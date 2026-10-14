import numpy as np

from scripts.analyze_recording import analisis_segmen
from scripts.plot_rekaman import pilih_jendela

FS = 360
DETIK = 150
JENDELA_S = 60
DERAU_DARI_S, DERAU_SAMPAI_S = 20, 90
AMPLITUDO_R, LEBAR_R_S, DASAR = 1500, 0.012, 1600
AMPLITUDO_DERAU = 400
SEED = 0


def _ekg_dengan_derau_otot():
    t = np.arange(DETIK * FS) / FS
    x = np.full_like(t, DASAR)
    for tb in np.arange(0.5, DETIK, 0.8):
        x += AMPLITUDO_R * np.exp(-0.5 * ((t - tb) / LEBAR_R_S) ** 2)
    rng = np.random.default_rng(SEED)
    derau = (t >= DERAU_DARI_S) & (t < DERAU_SAMPAI_S)
    x[derau] += AMPLITUDO_DERAU * rng.standard_normal(derau.sum())
    return x.astype(int)


def test_jendela_terbaik_menghindari_derau_otot():
    hasil = [analisis_segmen(_ekg_dengan_derau_otot().astype(np.float32), FS)]
    aneh, _, _, mulai, _ = pilih_jendela(hasil, FS, JENDELA_S * FS, None)
    assert mulai >= DERAU_SAMPAI_S * FS
    assert aneh == 0


def test_mulai_eksplisit_dipakai_apa_adanya():
    hasil = [analisis_segmen(_ekg_dengan_derau_otot().astype(np.float32), FS)]
    _, _, _, mulai, _ = pilih_jendela(hasil, FS, JENDELA_S * FS, DERAU_DARI_S)
    assert mulai == DERAU_DARI_S * FS
