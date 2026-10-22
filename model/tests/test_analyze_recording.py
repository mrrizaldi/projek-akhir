import numpy as np

from scripts.analyze_recording import (
    AMBANG_CLIPPING_PERSEN, JENDELA_AUTOKORELASI_S, analisis_segmen, hitung_clipping, denyut_autokorelasi, denyut_per_jendela, gabung, muat,
)

FS = 360


def _ekg(detik, fase, dasar):
    t = np.arange(int(detik * FS)) / FS
    x = np.full_like(t, dasar)
    for tb in np.arange(fase, detik, 1.0):
        x += 1500 * np.exp(-0.5 * ((t - tb) / 0.012) ** 2)
    return x.astype(int)


def test_rr_tidak_melintasi_jeda(tmp_path):
    s1, s2 = _ekg(20, 0.5, 2000), _ekg(20, 0.3, 2600)
    berkas = tmp_path / "rekam.csv"
    berkas.write_text(f"# fs={FS} n={len(s1) + len(s2)}\n"
                      + "\n".join(map(str, s1)) + "\n# jeda\n"
                      + "\n".join(map(str, s2)) + "\n")

    segmen, fs, _ = muat(str(berkas))
    assert fs == FS and [len(s) for s in segmen] == [len(s1), len(s2)]

    hasil = [analisis_segmen(s, fs) for s in segmen]
    r, rr, *_ = gabung(hasil, fs)
    assert all(len(h["r"]) > 10 for h in hasil)
    assert len(rr) == len(r) - 2
    assert np.all(np.abs(rr - 1.0) < 0.05)


def test_autokorelasi_pendek_tetap_seluruh_segmen():
    x = (_ekg(50, 0.5, 2000) - 2000) / 1000.0
    assert denyut_per_jendela(x, FS) == denyut_autokorelasi(x, FS)


def test_autokorelasi_panjang_median_per_jendela():
    x = (_ekg(95, 0.5, 2000) - 2000) / 1000.0
    n = JENDELA_AUTOKORELASI_S * FS
    tiap = [denyut_autokorelasi(x[i:i + n], FS) for i in range(0, len(x) - n + 1, n)]
    kuat, bpm, _ = denyut_per_jendela(x, FS)
    assert len(tiap) == 3
    assert kuat == float(np.median([k for k, _, _ in tiap]))
    assert bpm == float(np.median([b for _, b, _ in tiap]))


def test_clipping_dinilai_dari_fraksi_sampel_di_rail_firmware():
    x = np.full(100000, 2000.0)
    x[:5] = 4093
    n, persen, ok = hitung_clipping(x)
    assert (n, ok) == (5, True)
    x[:200] = 4090
    x[200:201] = 5
    n, persen, ok = hitung_clipping(x)
    assert n == 201 and persen > AMBANG_CLIPPING_PERSEN and not ok
