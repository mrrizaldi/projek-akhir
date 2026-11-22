import numpy as np

from scripts.window_quality import (
    TEMPLATE_CORRELATION_THRESHOLD, RR_PAUSE_MAX_S, SQI_WINDOW_S, window_scores,
)

FS = 360
INTERVAL_DETAK_S = 0.8
QRS_WIDTH_SAMPLES = 8
LONG_PAUSE_S = RR_PAUSE_MAX_S + 1


def _sinyal_detak(r):
    x = np.zeros(SQI_WINDOW_S * FS)
    t = np.arange(len(x))
    for i in r:
        x += np.exp(-((t - i) / QRS_WIDTH_SAMPLES) ** 2)
    return x


def _r_teratur():
    return np.arange(FS // 2, SQI_WINDOW_S * FS - FS // 2, int(INTERVAL_DETAK_S * FS))


def test_regular_beats_pass_all_rules():
    r = _r_teratur()
    hasil = window_scores(_sinyal_detak(r), r, FS)
    assert hasil["lolos_aturan"] and hasil["lolos"]
    assert hasil["korelasi"] > TEMPLATE_CORRELATION_THRESHOLD


def test_pause_over_three_seconds_rejected():
    r = _r_teratur()
    r = np.r_[r[:3], r[3:] + int(LONG_PAUSE_S * FS)]
    r = r[r < SQI_WINDOW_S * FS]
    assert not window_scores(_sinyal_detak(r), r, FS)["lolos_aturan"]


def test_noise_without_repeating_shape_fails_template():
    rng = np.random.default_rng(0)
    r = _r_teratur()
    hasil = window_scores(rng.standard_normal(SQI_WINDOW_S * FS), r, FS)
    assert hasil["lolos_aturan"] and not hasil["lolos"]


def test_no_beats_does_not_pass():
    assert not window_scores(np.zeros(SQI_WINDOW_S * FS), np.array([], dtype=int), FS)["lolos"]
