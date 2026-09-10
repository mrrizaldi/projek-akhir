import numpy as np

from config import WIN_PRE, WIN_LEN
from scripts.prep_beats import valid_beat_indices, process_record
from src.preprocessing import design_bandpass_sos


def test_valid_beat_indices_tiga_syarat():
    """Beat tepi (window tak muat) dan beat 0/1 (tanpa RR/dRR) sama-sama gugur."""
    r = np.array([10, 100, 200, 300, 950, 995])   # signal_len = 1000
    idx = valid_beat_indices(1000, r)
    assert idx.tolist() == [2, 3]                 # 0,1 → i<2; 10 → kiri; 950,995 → kanan
    assert np.all(np.diff(idx) > 0)


def test_valid_beat_indices_kosong_tidak_crash():
    assert valid_beat_indices(1000, np.array([], dtype=int)).tolist() == []
    assert valid_beat_indices(1000, np.array([500])).tolist() == []


def test_process_record_alignment_rec100():
    """Kontrak alignment: 4 array sejajar, tanpa NaN, label cocok simbolnya."""
    out = process_record("100", design_bandpass_sos())
    n = len(out["labels"])
    assert len(out["windows"]) == len(out["rr"]) == len(out["symbols"]) == n
    assert out["windows"].shape[1] == WIN_LEN
    assert not np.isnan(out["rr"]).any()

    # label 1 HARUS tepat pada simbol non-N — ini yang pecah kalau baris tergeser.
    non_n = out["symbols"] != "N"
    assert np.array_equal(out["labels"].astype(bool), non_n)
    assert int(out["labels"].sum()) == 34          # 33 "A" + 1 "V" di rec 100


def test_process_record_r_peak_pada_posisi_tetap():
    """R-peak mendarat di WIN_PRE + group delay filter kausal (~4 sampel)."""
    out = process_record("100", design_bandpass_sos())
    puncak = np.median(np.argmax(out["windows"], axis=1))
    assert WIN_PRE <= puncak <= WIN_PRE + 8
