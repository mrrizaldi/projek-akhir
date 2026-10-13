import numpy as np

from scripts.analyze_recording import analisis_segmen, gabung, muat

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
