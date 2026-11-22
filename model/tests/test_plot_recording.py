import numpy as np

from scripts.analyze_recording import analyze_segment
from scripts.plot_recording import select_window

FS = 360
DETIK = 150
WINDOW_S = 60
DERAU_DARI_S, DERAU_SAMPAI_S = 20, 90
AMPLITUDO_R, R_WIDTH_S, BASELINE = 1500, 0.012, 1600
AMPLITUDO_DERAU = 400
SEED = 0


def _ecg_with_muscle_noise():
    t = np.arange(DETIK * FS) / FS
    x = np.full_like(t, BASELINE)
    for tb in np.arange(0.5, DETIK, 0.8):
        x += AMPLITUDO_R * np.exp(-0.5 * ((t - tb) / R_WIDTH_S) ** 2)
    rng = np.random.default_rng(SEED)
    derau = (t >= DERAU_DARI_S) & (t < DERAU_SAMPAI_S)
    x[derau] += AMPLITUDO_DERAU * rng.standard_normal(derau.sum())
    return x.astype(int)


def test_best_window_avoids_muscle_noise():
    hasil = [analyze_segment(_ecg_with_muscle_noise().astype(np.float32), FS)]
    odd_rr, _, _, mulai, _ = select_window(hasil, FS, WINDOW_S * FS, None)
    assert mulai >= DERAU_SAMPAI_S * FS
    assert odd_rr == 0


def test_explicit_start_used_as_is():
    hasil = [analyze_segment(_ecg_with_muscle_noise().astype(np.float32), FS)]
    _, _, _, mulai, _ = select_window(hasil, FS, WINDOW_S * FS, DERAU_DARI_S)
    assert mulai == DERAU_DARI_S * FS
