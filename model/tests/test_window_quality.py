import numpy as np

from scripts.window_quality import (
    TEMPLATE_CORRELATION_THRESHOLD, RR_PAUSE_MAX_S, SQI_WINDOW_S, window_scores,
)

FS = 360
BEAT_INTERVAL_S = 0.8
QRS_WIDTH_SAMPLES = 8
LONG_PAUSE_S = RR_PAUSE_MAX_S + 1


def _beat_signal(r):
    x = np.zeros(SQI_WINDOW_S * FS)
    t = np.arange(len(x))
    for i in r:
        x += np.exp(-((t - i) / QRS_WIDTH_SAMPLES) ** 2)
    return x


def _regular_r():
    return np.arange(FS // 2, SQI_WINDOW_S * FS - FS // 2, int(BEAT_INTERVAL_S * FS))


def test_regular_beats_pass_all_rules():
    r = _regular_r()
    scores = window_scores(_beat_signal(r), r, FS)
    assert scores["lolos_aturan"] and scores["lolos"]
    assert scores["korelasi"] > TEMPLATE_CORRELATION_THRESHOLD


def test_pause_over_three_seconds_rejected():
    r = _regular_r()
    r = np.r_[r[:3], r[3:] + int(LONG_PAUSE_S * FS)]
    r = r[r < SQI_WINDOW_S * FS]
    assert not window_scores(_beat_signal(r), r, FS)["lolos_aturan"]


def test_noise_without_repeating_shape_fails_template():
    rng = np.random.default_rng(0)
    r = _regular_r()
    scores = window_scores(rng.standard_normal(SQI_WINDOW_S * FS), r, FS)
    assert scores["lolos_aturan"] and not scores["lolos"]


def test_no_beats_does_not_pass():
    assert not window_scores(np.zeros(SQI_WINDOW_S * FS), np.array([], dtype=int), FS)["lolos"]
