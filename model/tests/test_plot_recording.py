import numpy as np

from scripts.analyze_recording import analyze_segment
from scripts.plot_recording import select_window

FS = 360
SIGNAL_S = 150
WINDOW_S = 60
NOISE_FROM_S, NOISE_UNTIL_S = 20, 90
R_AMPLITUDE, R_WIDTH_S, BASELINE = 1500, 0.012, 1600
NOISE_AMPLITUDE = 400
SEED = 0


def _ecg_with_muscle_noise():
    t = np.arange(SIGNAL_S * FS) / FS
    x = np.full_like(t, BASELINE)
    for tb in np.arange(0.5, SIGNAL_S, 0.8):
        x += R_AMPLITUDE * np.exp(-0.5 * ((t - tb) / R_WIDTH_S) ** 2)
    rng = np.random.default_rng(SEED)
    noisy = (t >= NOISE_FROM_S) & (t < NOISE_UNTIL_S)
    x[noisy] += NOISE_AMPLITUDE * rng.standard_normal(noisy.sum())
    return x.astype(int)


def test_best_window_avoids_muscle_noise():
    analyses = [analyze_segment(_ecg_with_muscle_noise().astype(np.float32), FS)]
    odd_rr, _, _, start, _ = select_window(analyses, FS, WINDOW_S * FS, None)
    assert start >= NOISE_UNTIL_S * FS
    assert odd_rr == 0


def test_explicit_start_used_as_is():
    analyses = [analyze_segment(_ecg_with_muscle_noise().astype(np.float32), FS)]
    _, _, _, start, _ = select_window(analyses, FS, WINDOW_S * FS, NOISE_FROM_S)
    assert start == NOISE_FROM_S * FS
