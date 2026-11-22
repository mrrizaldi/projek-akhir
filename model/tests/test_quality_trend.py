import numpy as np

from scripts.tren_kualitas import FREK_JALA_HZ, nilai_per_detik, tenang_per_detik

FS = 360


def _ekg(detik, waktu_beat, dasar=2000):
    t = np.arange(int(detik * FS)) / FS
    x = np.full_like(t, dasar)
    for tb in waktu_beat:
        x += 1500 * np.exp(-0.5 * ((t - tb) / 0.012) ** 2)
    return x


def test_hum_50hz_measured_peak_to_peak():
    t = np.arange(5 * FS) / FS
    _, hum50, _, clipping = nilai_per_detik(2000 + 100 * np.sin(2 * np.pi * FREK_JALA_HZ * t))
    assert np.allclose(hum50, 200, rtol=0.01)
    assert not clipping.any()


def test_quiet_rr_grows_and_resets_on_premature_beat():
    teratur = _ekg(60, np.arange(0.5, 60, 1.0))
    *_, tenang = tenang_per_detik(teratur, 60)
    assert tenang.max() >= 55

    prematur = np.sort(np.r_[np.arange(0.5, 60, 1.0), 30.85])
    *_, tenang = tenang_per_detik(_ekg(60, prematur), 60)
    assert tenang[30] == 0 and tenang[31] == 0
    assert tenang[59] >= 25
