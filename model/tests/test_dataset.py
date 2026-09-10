import numpy as np
import pytest

from config import DS1, DS2, PACED_EXCLUDED, VAL_RECORDS, WIN_LEN
from src.dataset import assert_split_valid, stack_records, build_split, split_train_val


def test_split_disjoint_dan_48():
    assert_split_valid()
    assert len(set(DS1) & set(DS2)) == 0
    assert len(set(DS1) | set(DS2) | set(PACED_EXCLUDED)) == 48


def test_record_hilang_bikin_error_bukan_diam():
    with pytest.raises(FileNotFoundError):
        stack_records([101], per_record_dir="/tmp/tidak-ada")


def test_build_split_tidak_bocor_lintas_pasien():
    train, test = build_split()
    r_train, r_test = set(np.unique(train["records"])), set(np.unique(test["records"]))
    assert r_train & r_test == set()
    assert r_train == set(DS1) and r_test == set(DS2)


def test_bentuk_dan_kekekalan_jumlah():
    train, test = build_split()
    for d in (train, test):
        n = len(d["y"])
        assert d["X_morph"].shape == (n, WIN_LEN, 1)
        assert d["X_rr"].shape == (n, 3)
        assert d["records"].shape == (n,)
        assert not np.isnan(d["X_rr"]).any()
        assert set(np.unique(d["y"])) <= {0, 1}
    assert len(train["y"]) + len(test["y"]) == 100619   # == total Fase 2


def test_val_diambil_per_pasien_bukan_per_beat():
    """Tidak boleh ada satu pasien pun muncul di train sekaligus val."""
    train_full, _ = build_split()
    tr, va = split_train_val(train_full)
    assert set(np.unique(va["records"])) == set(VAL_RECORDS)
    assert set(np.unique(tr["records"])) & set(VAL_RECORDS) == set()
    assert len(tr["y"]) + len(va["y"]) == len(train_full["y"])


def test_val_bukan_dari_ds2():
    with pytest.raises(ValueError):
        split_train_val({"records": np.array([100]), "y": np.array([0])}, val_records=[100])
