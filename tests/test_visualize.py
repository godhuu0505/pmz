"""時系列可視化（SVG 生成）のテスト（要件 §6.1）。"""

from __future__ import annotations

from pmz.eval.backtest import run_self_improvement
from pmz.eval.visualize import render_self_improvement_svg


def test_svg_has_expected_structure() -> None:
    svg = render_self_improvement_svg()
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    # オンライン推移の24点が誤承認率の折れ線上に描かれる。
    assert svg.count("<circle") == 24
    assert "誤承認率" in svg
    assert "誤ブロック率" in svg


def test_svg_annotates_trap_and_catch() -> None:
    svg = render_self_improvement_svg()
    # trap（見逃し→学習）と catch（検知）が注記される。
    assert "rel-07" in svg and "見逃し→学習" in svg  # db_migration trap
    assert "rel-19" in svg and "検知" in svg  # db_migration catch


def test_svg_is_deterministic() -> None:
    result = run_self_improvement()
    assert render_self_improvement_svg(result) == render_self_improvement_svg(result)
