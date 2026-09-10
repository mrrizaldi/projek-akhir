import numpy as np
import pytest

from src.evaluate import (
    confusion_counts, binary_metrics, evaluate_probabilities,
    per_record_metrics, roc_auc,
)


def test_confusion_counts_semua_kuadran():
    y = np.array([1, 1, 0, 0, 1])
    p = np.array([1, 0, 1, 0, 1])
    assert confusion_counts(y, p) == {"tp": 2, "fn": 1, "fp": 1, "tn": 1}


def test_bentuk_beda_error_bukan_broadcast():
    with pytest.raises(ValueError):
        confusion_counts(np.zeros(5), np.zeros(4))


def test_metrik_dari_hitungan_tangan():
    m = binary_metrics({"tp": 2, "fn": 1, "fp": 1, "tn": 1})
    assert np.isclose(m["recall"], 2 / 3)
    assert np.isclose(m["precision"], 2 / 3)
    assert np.isclose(m["f1"], 2 / 3)
    assert np.isclose(m["specificity"], 0.5)
    assert np.isclose(m["accuracy"], 0.6)


def test_pembagian_nol_jadi_nol_bukan_nan():
    """Model yang tak pernah menebak positif: precision 0, bukan NaN."""
    m = binary_metrics({"tp": 0, "fn": 5, "fp": 0, "tn": 5})
    assert m["precision"] == 0.0 and m["recall"] == 0.0 and m["f1"] == 0.0


def test_threshold_menggeser_recall_dan_precision():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.4, 0.45, 0.9])
    ketat = evaluate_probabilities(y, p, 0.5)
    longgar = evaluate_probabilities(y, p, 0.3)
    assert ketat["recall"] == 0.5 and ketat["precision"] == 1.0
    assert longgar["recall"] == 1.0 and longgar["precision"] < 1.0


def test_auc_sempurna_acak_dan_seri():
    assert roc_auc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == 1.0
    assert roc_auc([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]) == 0.0
    assert roc_auc([0, 1], [0.5, 0.5]) == 0.5          # seri → 0,5, bukan 1,0
    with pytest.raises(ValueError):
        roc_auc([0, 0, 0], [0.1, 0.2, 0.3])


def test_auc_bebas_threshold():
    """Skala probabilitas berubah monoton → AUC tidak berubah."""
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.3, 0.6, 0.7])
    assert np.isclose(roc_auc(y, p), roc_auc(y, p / 10))


def test_per_record_memisah_pasien():
    y = np.array([1, 0, 1, 0])
    p = np.array([0.9, 0.1, 0.1, 0.1])
    rows = per_record_metrics(y, p, np.array([100, 100, 200, 200]), 0.5)
    assert [r["record"] for r in rows] == [100, 200]
    assert rows[0]["recall"] == 1.0 and rows[1]["recall"] == 0.0
