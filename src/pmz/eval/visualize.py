"""自己改善の時系列可視化（要件 §6.1「デモの目玉」/ §9.1）.

依存ゼロで **SVG を自前生成** する（matplotlib 等を足さない＝軽量・CI で安定）。
オンライン推移（ルールブックが育つ実運用さながらの系列）の **累積 誤承認率／誤ブロック率** を
折れ線で描き、trap（見逃し→学習）と catch（検知）の位置を注記する。

ストーリー: 誤承認率は trap で跳ね上がり、学習後は catch で再発を止めるため**下がっていく**。
誤ブロック率は **0% のまま不変**（健全性）。＝「賢くなっている様子」を一枚で見せる。
"""

from __future__ import annotations

import sys
from pathlib import Path

from pmz.eval.backtest import SelfImprovementResult, run_self_improvement
from pmz.models import Act, ReleaseRecord, Verdict

# 既定の出力先（リポジトリ同梱のデモ資産）。
DEFAULT_OUT = Path("docs/assets/self_improvement.svg")

_W, _H = 880, 460
_M = {"left": 64, "right": 28, "top": 72, "bottom": 76}


def _cumulative_rates(
    timeline: list[tuple[ReleaseRecord, object]],
) -> tuple[list[float], list[float]]:
    """オンライン推移から累積 (誤承認率, 誤ブロック率) を作る。

    - 誤承認率 = (見逃した No-Go 件数) / (これまでの正解 No-Go 件数)
    - 誤ブロック率 = (誤って止めた Go 件数) / (これまでの正解 Go 件数)
    """
    fa: list[float] = []
    fb: list[float] = []
    fp = tn = fn = tp = 0
    for rec, dec in timeline:
        pred_go = dec.effective_verdict is Verdict.GO  # type: ignore[attr-defined]
        true_go = rec.labels.correct_verdict is Verdict.GO
        if pred_go and true_go:
            tp += 1
        elif pred_go and not true_go:
            fp += 1
        elif not pred_go and true_go:
            fn += 1
        else:
            tn += 1
        fa.append(fp / (fp + tn) if (fp + tn) else 0.0)
        fb.append(fn / (fn + tp) if (fn + tp) else 0.0)
    return fa, fb


def _polyline(points: list[tuple[float, float]], color: str, width: float = 2.5) -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (
        f'<polyline fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linejoin="round" points="{pts}"/>'
    )


def render_self_improvement_svg(result: SelfImprovementResult | None = None) -> str:
    """自己改善の時系列 SVG 文字列を返す（依存ゼロ）。"""
    result = result or run_self_improvement()
    timeline = result.online_timeline
    n = len(timeline)
    fa, fb = _cumulative_rates(timeline)

    plot_w = _W - _M["left"] - _M["right"]
    plot_h = _H - _M["top"] - _M["bottom"]

    def px(i: int) -> float:
        return _M["left"] + (plot_w * i / (n - 1) if n > 1 else 0)

    def py(v: float) -> float:
        return _M["top"] + plot_h * (1 - v)

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_W}" height="{_H}" '
        f'viewBox="0 0 {_W} {_H}" font-family="sans-serif">'
    )
    parts.append(f'<rect width="{_W}" height="{_H}" fill="#ffffff"/>')
    parts.append(
        f'<text x="{_W / 2:.0f}" y="32" text-anchor="middle" font-size="20" '
        f'font-weight="bold" fill="#111">pmz 自己改善の時系列（見逃す→学習→検知）</text>'
    )

    # Y 軸グリッド + ラベル（0〜100%）。
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        gy = py(frac)
        parts.append(
            f'<line x1="{_M["left"]}" y1="{gy:.1f}" x2="{_W - _M["right"]}" y2="{gy:.1f}" '
            f'stroke="#e5e7eb" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{_M["left"] - 8}" y="{gy + 4:.1f}" text-anchor="end" '
            f'font-size="11" fill="#6b7280">{frac * 100:.0f}%</text>'
        )

    # trap / catch の縦線・注記。
    for i, (rec, _dec) in enumerate(timeline):
        act = rec.arc.act
        if act not in (Act.TRAP, Act.CATCH):
            continue
        x = px(i)
        is_trap = act is Act.TRAP
        color = "#f59e0b" if is_trap else "#10b981"
        label = "見逃し→学習" if is_trap else "検知"
        parts.append(
            f'<line x1="{x:.1f}" y1="{_M["top"]}" x2="{x:.1f}" y2="{_M["top"] + plot_h:.1f}" '
            f'stroke="{color}" stroke-width="1" stroke-dasharray="4 3" opacity="0.7"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{_M["top"] - 6:.1f}" text-anchor="middle" '
            f'font-size="10" fill="{color}">{rec.id} {label}</text>'
        )

    # 折れ線（誤承認率＝赤、誤ブロック率＝青）。
    fa_pts = [(px(i), py(v)) for i, v in enumerate(fa)]
    fb_pts = [(px(i), py(v)) for i, v in enumerate(fb)]
    parts.append(_polyline(fb_pts, "#3b82f6"))
    parts.append(_polyline(fa_pts, "#ef4444"))
    # データ点（誤承認率）。
    for x, y in fa_pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#ef4444"/>')

    # X 軸ラベル（最初・最後）。
    parts.append(
        f'<text x="{px(0):.1f}" y="{_M["top"] + plot_h + 18:.1f}" text-anchor="middle" '
        f'font-size="11" fill="#6b7280">{timeline[0][0].id}</text>'
    )
    parts.append(
        f'<text x="{px(n - 1):.1f}" y="{_M["top"] + plot_h + 18:.1f}" text-anchor="middle" '
        f'font-size="11" fill="#6b7280">{timeline[n - 1][0].id}</text>'
    )

    # 凡例。
    ly = _M["top"] + plot_h + 44
    lx = _M["left"]

    def _legend(x: float, color: str, text: str) -> None:
        parts.append(f'<rect x="{x:.0f}" y="{ly - 9}" width="14" height="4" fill="{color}"/>')
        parts.append(
            f'<text x="{x + 20:.0f}" y="{ly - 2}" font-size="12" fill="#374151">{text}</text>'
        )

    _legend(lx, "#ef4444", "累積 誤承認率")
    _legend(lx + 130, "#3b82f6", "累積 誤ブロック率")

    # before/after サマリ（右上）。
    summary = (
        f"誤承認率 {result.before.false_approve_rate * 100:.0f}% → "
        f"{result.after.false_approve_rate * 100:.0f}%   |   "
        f"再発検知率 {result.recurrence_detection_rate * 100:.0f}%   |   "
        f"誤ブロック率 {result.after.false_block_rate * 100:.0f}%（不変）"
    )
    parts.append(
        f'<text x="{_W - _M["right"]}" y="52" text-anchor="end" font-size="12" '
        f'fill="#111">{summary}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    """`python -m pmz.eval.visualize [出力パス]` で SVG を書き出す。"""
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_self_improvement_svg(), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
