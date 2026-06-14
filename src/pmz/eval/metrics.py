"""判定精度の指標（要件 §6.1）.

判定を 2値分類とみなす。**陽性クラス = Go（承認）** と定義することで:

- **FP = 誤承認**（No-Go であるべきものを Go にした＝最重要・低いほど良い）
- **FN = 誤ブロック**（Go であるべきものを No-Go にした）

となり、F-beta（beta<1）が precision を重く見る＝誤承認を主に罰する形になる。
誤ブロック（FN）も recall 経由で罰するため「全ブロックでFPゼロ」は高評価にならない（§6.1）。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pmz.models import Verdict

# 誤承認（FP）を主役にしつつ誤ブロック（FN）も罰する重み（precision 寄り・§6.1）。
DEFAULT_BETA = 0.5


@dataclass(frozen=True)
class ConfusionMatrix:
    """陽性クラス = Go の混同行列（§6.1）。"""

    tp: int = 0  # 正しく承認（Go / 正解 Go）
    fp: int = 0  # 誤承認（Go / 正解 No-Go）★最重要
    fn: int = 0  # 誤ブロック（No-Go / 正解 Go）
    tn: int = 0  # 正しくブロック（No-Go / 正解 No-Go）

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def accuracy(self) -> float:
        return _safe_div(self.tp + self.tn, self.total)

    @property
    def precision(self) -> float:
        """承認したもののうち正しかった割合（FP=誤承認に反応）。"""
        return _safe_div(self.tp, self.tp + self.fp)

    @property
    def recall(self) -> float:
        """承認すべきもののうち承認できた割合（FN=誤ブロックに反応）。"""
        return _safe_div(self.tp, self.tp + self.fn)

    @property
    def false_approve_rate(self) -> float:
        """誤承認率: No-Go であるべきリリースを通した割合（§6 最重要）。"""
        return _safe_div(self.fp, self.fp + self.tn)

    @property
    def false_block_rate(self) -> float:
        """誤ブロック率: Go であるべきリリースを止めた割合（§6）。"""
        return _safe_div(self.fn, self.fn + self.tp)

    def f_beta(self, beta: float = DEFAULT_BETA) -> float:
        """F-beta（beta<1 で precision=誤承認抑止を重視・§6.1）。"""
        p, r = self.precision, self.recall
        b2 = beta * beta
        return _safe_div((1 + b2) * p * r, b2 * p + r)


def confusion_matrix(pairs: Iterable[tuple[Verdict, Verdict]]) -> ConfusionMatrix:
    """``(予測 verdict, 正解 verdict)`` の列から混同行列を作る（陽性 = Go）。"""
    tp = fp = fn = tn = 0
    for predicted, correct in pairs:
        pred_go = predicted is Verdict.GO
        true_go = correct is Verdict.GO
        if pred_go and true_go:
            tp += 1
        elif pred_go and not true_go:
            fp += 1
        elif not pred_go and true_go:
            fn += 1
        else:
            tn += 1
    return ConfusionMatrix(tp=tp, fp=fp, fn=fn, tn=tn)


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0
