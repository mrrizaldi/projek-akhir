import numpy as np
import pytest

from config import JITTER_COPIES, N_RR_FEATURES, DS1, DS2, PACED_EXCLUDED, VAL_RECORDS, WIN_LEN
from src.dataset import assert_split_valid, stack_records, build_split, split_train_val


def test_split_disjoint_and_48():
    assert_split_valid()
    assert len(set(DS1) & set(DS2)) == 0
    assert len(set(DS1) | set(DS2) | set(PACED_EXCLUDED)) == 48


def test_missing_record_errors_not_silent():
    with pytest.raises(FileNotFoundError):
        stack_records([101], per_record_dir="/tmp/tidak-ada")


def test_build_split_no_cross_patient_leak():
    train, test = build_split()
    r_train, r_test = set(np.unique(train["records"])), set(np.unique(test["records"]))
    assert r_train & r_test == set()
    assert r_train == set(DS1) and r_test == set(DS2)


def test_shape_and_count_conservation():
    train, test = build_split()
    for d in (train, test):
        n = len(d["y"])
        assert d["X_morph"].shape == (n, WIN_LEN, 1)
        assert d["X_rr"].shape == (n, N_RR_FEATURES)
        assert d["records"].shape == (n,)
        assert not np.isnan(d["X_rr"]).any()
        assert set(np.unique(d["y"])) <= {0, 1}
    assert len(test["y"]) == 49656
    multiplier = JITTER_COPIES + 1
    assert abs(len(train["y"]) - multiplier * 50968) < 0.01 * multiplier * 50968


def test_val_taken_per_patient_not_per_beat():
    train_full, _ = build_split()
    tr, va = split_train_val(train_full)
    assert set(np.unique(va["records"])) == set(VAL_RECORDS)
    assert set(np.unique(tr["records"])) & set(VAL_RECORDS) == set()
    assert len(tr["y"]) + len(va["y"]) == len(train_full["y"])


def test_val_not_from_ds2():
    with pytest.raises(ValueError):
        split_train_val({"records": np.array([100]), "y": np.array([0])}, val_records=[100])
