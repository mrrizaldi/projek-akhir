import numpy as np

from scripts.window_quality import (
    AMBANG_KORELASI_TEMPLATE, JEDA_RR_MAKS_S, JENDELA_SQI_S, window_scores,
)

FS = 360
INTERVAL_DETAK_S = 0.8
LEBAR_QRS_SAMPEL = 8
JEDA_PANJANG_S = JEDA_RR_MAKS_S + 1


def _sinyal_detak(r):
    x = np.zeros(JENDELA_SQI_S * FS)
    t = np.arange(len(x))
    for i in r:
        x += np.exp(-((t - i) / LEBAR_QRS_SAMPEL) ** 2)
    return x


def _r_teratur():
    return np.arange(FS // 2, JENDELA_SQI_S * FS - FS // 2, int(INTERVAL_DETAK_S * FS))


def test_regular_beats_pass_all_rules():
    r = _r_teratur()
    hasil = window_scores(_sinyal_detak(r), r, FS)
    assert hasil["lolos_aturan"] and hasil["lolos"]
    assert hasil["korelasi"] > AMBANG_KORELASI_TEMPLATE


def test_pause_over_three_seconds_rejected():
    r = _r_teratur()
    r = np.r_[r[:3], r[3:] + int(JEDA_PANJANG_S * FS)]
    r = r[r < JENDELA_SQI_S * FS]
    assert not window_scores(_sinyal_detak(r), r, FS)["lolos_aturan"]


def test_noise_without_repeating_shape_fails_template():
    rng = np.random.default_rng(0)
    r = _r_teratur()
    hasil = window_scores(rng.standard_normal(JENDELA_SQI_S * FS), r, FS)
    assert hasil["lolos_aturan"] and not hasil["lolos"]


def test_no_beats_does_not_pass():
    assert not window_scores(np.zeros(JENDELA_SQI_S * FS), np.array([], dtype=int), FS)["lolos"]
