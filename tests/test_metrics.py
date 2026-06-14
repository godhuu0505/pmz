"""評価指標のテスト（要件 §6.1）。陽性クラス = Go の混同行列。"""

from __future__ import annotations

from gatekeeper.eval.metrics import confusion_matrix
from gatekeeper.models import Verdict

GO = Verdict.GO
NO = Verdict.NO_GO


def test_confusion_matrix_maps_false_approve_to_fp() -> None:
    # 予測 Go・正解 No-Go = 誤承認（FP）。これが最重要指標。
    cm = confusion_matrix([(GO, NO)])
    assert (cm.tp, cm.fp, cm.fn, cm.tn) == (0, 1, 0, 0)
    assert cm.false_approve_rate == 1.0


def test_confusion_matrix_maps_false_block_to_fn() -> None:
    # 予測 No-Go・正解 Go = 誤ブロック（FN）。
    cm = confusion_matrix([(NO, GO)])
    assert (cm.tp, cm.fp, cm.fn, cm.tn) == (0, 0, 1, 0)
    assert cm.false_block_rate == 1.0


def test_perfect_classifier() -> None:
    cm = confusion_matrix([(GO, GO), (NO, NO)])
    assert cm.accuracy == 1.0
    assert cm.false_approve_rate == 0.0
    assert cm.false_block_rate == 0.0
    assert cm.f_beta() == 1.0


def test_fbeta_penalizes_false_approve_more_than_false_block() -> None:
    # beta<1（precision寄り）なので、同数なら誤承認(FP)が混じる方が F-beta は低い（§6.1）。
    base = [(GO, GO)] * 4
    with_fp = confusion_matrix([*base, (GO, NO)])  # 誤承認1件
    with_fn = confusion_matrix([*base, (NO, GO)])  # 誤ブロック1件
    assert with_fp.f_beta(0.5) < with_fn.f_beta(0.5)
