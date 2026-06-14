"""自己改善のバックテスト（要件 §6.1 / §9.1 / §3.3.1）── W2 の心臓.

合成リリース履歴に対して「**見逃す → 学習 → 検知**」を再現し、自己改善が効いている
ことを **学習前後の混同行列（before/after）** と **時系列** で裏付ける。

評価時の前提:
- 各リリースの申告受け入れ基準は **全件「満たす」確信度0.9** とみなす（``believed_assessment``）。
  これは判定時点でゲートが PR を信じている状況の再現で、trap が誤承認をすり抜ける条件。
  trap の「悪さ」は判定時には分からず、**確定した客観イベント** から後追いで学習する
  （振り返り・§3.3.1 (1)）。
- 学習は **客観ラベル（障害確定 / 要件未達確定）** からのみ起こす（インバリアント #6）。

> ``correct_verdict`` は合成データだから仕込める正解（実運用では成立しない・§9.1）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pmz.core.decision import GateDecision
from pmz.core.judge import judge_record
from pmz.data import load_synthetic_releases
from pmz.eval.metrics import ConfusionMatrix, confusion_matrix
from pmz.learning.memory import CaseMemory, MisjudgedCase
from pmz.learning.retrospective import is_confirmed_bad, learn_rule_from
from pmz.learning.rulebook import Rulebook
from pmz.models import Act, ReleaseRecord, Verdict
from pmz.signals import CriterionResult, CriterionStatus, RequirementAssessment

# 申告基準を信じる確信度（trap がすり抜ける＝ゲートが PR を信用している状況の再現）。
_BELIEVED_CONFIDENCE = 0.9


def believed_assessment(record: ReleaseRecord) -> RequirementAssessment:
    """申告受け入れ基準を全件「満たす」とみなす要件充足判定を作る。

    判定時点ではゲートは PR の申告を信じている（trap はここをすり抜ける）。
    """
    return RequirementAssessment(
        results=[
            CriterionResult(
                criterion=c,
                status=CriterionStatus.MET,
                confidence=_BELIEVED_CONFIDENCE,
                evidence="申告どおり充足とみなす（合成データのバックテスト前提・§9.1）。",
            )
            for c in record.requirement.acceptance_criteria
        ]
    )


def evaluate(
    records: list[ReleaseRecord],
    *,
    rulebook: Rulebook | None = None,
    memory: CaseMemory | None = None,
) -> list[tuple[ReleaseRecord, GateDecision]]:
    """固定のルールブックで全レコードを判定する（バッチ評価）。"""
    return [
        (rec, judge_record(rec, believed_assessment(rec), rulebook=rulebook, memory=memory))
        for rec in records
    ]


def train(
    records: list[ReleaseRecord],
) -> tuple[Rulebook, CaseMemory, list[tuple[Verdict, Verdict]]]:
    """時系列に1件ずつ判定しながら、確定した見逃しから学習する（オンライン自己改善）。

    返り値の3要素目は時系列順の ``(予測, 正解)`` ペア（実運用さながらの混同行列用）。
    trap は学習前なので見逃し、catch は学習後なので検知される。
    """
    rulebook = Rulebook()
    memory = CaseMemory()
    online: list[tuple[Verdict, Verdict]] = []

    for rec in records:
        dec = judge_record(rec, believed_assessment(rec), rulebook=rulebook, memory=memory)
        online.append((dec.verdict, rec.labels.correct_verdict))

        # 判定後に振り返り: 客観イベントで確定した「見逃し（誤承認）」だけを学習に回す。
        if dec.verdict is Verdict.GO and is_confirmed_bad(rec):
            rule = learn_rule_from(rec, version=rulebook.version + 1)
            if rule is not None and not rulebook.has(rule.archetype, rule.file_globs):
                rulebook.add(rule)
                memory.add(
                    MisjudgedCase(
                        release_id=rec.id,
                        archetype=rec.arc.archetype,
                        predicted_verdict=dec.verdict,
                        correct_verdict=rec.labels.correct_verdict,
                        changed_files=rec.code.changed_files,
                        summary=rec.code.diff_summary,
                    )
                )

    return rulebook, memory, online


@dataclass
class SelfImprovementResult:
    """学習前後の比較（§6.1 の計測構造）。"""

    before: ConfusionMatrix
    after: ConfusionMatrix
    online: ConfusionMatrix
    rulebook: Rulebook
    recurrence_detection_rate: float
    timeline: list[tuple[ReleaseRecord, GateDecision, GateDecision]] = field(default_factory=list)


def run_self_improvement(records: list[ReleaseRecord] | None = None) -> SelfImprovementResult:
    """合成データで自己改善の before/after を計測する（デモの目玉・§6.1）。"""
    records = records if records is not None else load_synthetic_releases()

    # before: 何も学習していない素のゲート。
    before_eval = evaluate(records)
    before_cm = confusion_matrix((d.verdict, r.labels.correct_verdict) for r, d in before_eval)

    # 時系列に学習してルールブックを育てる。
    rulebook, memory, online_pairs = train(records)
    online_cm = confusion_matrix(online_pairs)

    # after: 学習済みルールブックを最初から適用した場合。
    after_eval = evaluate(records, rulebook=rulebook, memory=memory)
    after_cm = confusion_matrix((d.verdict, r.labels.correct_verdict) for r, d in after_eval)

    # 再発アーキタイプの検知率（§6.1 唯一100%と言える強KPI）。
    after_by_id = {r.id: d for r, d in after_eval}
    catches = [r for r in records if r.arc.act is Act.CATCH]
    detected = sum(1 for r in catches if after_by_id[r.id].verdict is Verdict.NO_GO)
    recurrence_rate = detected / len(catches) if catches else 0.0

    before_by_id = {r.id: d for r, d in before_eval}
    timeline = [(r, before_by_id[r.id], after_by_id[r.id]) for r in records]

    return SelfImprovementResult(
        before=before_cm,
        after=after_cm,
        online=online_cm,
        rulebook=rulebook,
        recurrence_detection_rate=recurrence_rate,
        timeline=timeline,
    )


def _fmt_cm(label: str, cm: ConfusionMatrix) -> str:
    return (
        f"{label}: acc={cm.accuracy:.0%} "
        f"誤承認率={cm.false_approve_rate:.0%} 誤ブロック率={cm.false_block_rate:.0%} "
        f"F-beta={cm.f_beta():.3f}  [TP={cm.tp} FP={cm.fp} FN={cm.fn} TN={cm.tn}]"
    )


def main() -> None:
    """`python -m pmz.eval.backtest` で before/after を表示する。"""
    result = run_self_improvement()
    print("=== pmz 自己改善バックテスト（合成データ §9.1）===")
    print(_fmt_cm("before（学習前）", result.before))
    print(_fmt_cm("after （学習後）", result.after))
    print(_fmt_cm("online（時系列）", result.online))
    print(
        f"再発アーキタイプ検知率 = {result.recurrence_detection_rate:.0%} "
        f"（学習ルール {result.rulebook.version} 件）"
    )
    print("\n--- 学習したルール ---")
    for r in result.rulebook.rules:
        print(f"  [{r.id}] {r.file_globs} <- {r.created_from}")
    print("\n--- タイムライン（見逃す→学習→検知）---")
    for rec, before, after in result.timeline:
        arc = rec.arc.act.value if rec.arc.act else "-"
        flip = "  ← 学習で検知!" if before.verdict != after.verdict else ""
        print(
            f"  {rec.id} act={arc:8s} 正解={rec.labels.correct_verdict.value:5s} "
            f"before={before.verdict.value:5s} after={after.verdict.value:5s}{flip}"
        )


if __name__ == "__main__":
    main()
