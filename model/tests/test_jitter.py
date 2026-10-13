import numpy as np
import pytest

from src.preprocessing import jitter_r


def r_teratur(n=200, rr=300):
    return np.arange(n, dtype=np.int64) * rr + 1000


def test_seragam_delta_nol_tidak_menggeser():
    r = r_teratur()
    assert np.array_equal(jitter_r(r, 0, np.random.default_rng(0), "seragam"), r)


def test_seragam_dibatasi_delta():
    r = r_teratur()
    d = jitter_r(r, 5, np.random.default_rng(1), "seragam") - r
    assert np.abs(d).max() <= 5
    assert np.abs(d).max() > 0


@pytest.mark.parametrize("model,delta", [("seragam", 18), ("normal", 6), ("empiris", 0)])
def test_urutan_tetap_menaik(model, delta):
    j = jitter_r(r_teratur(), delta, np.random.default_rng(2), model)
    assert (np.diff(j) >= 0).all(), "RR negatif — pasangan beat bertukar tempat"


def test_empiris_meniru_sebaran_terukur():
    r = r_teratur(20000)
    d = jitter_r(r, 0, np.random.default_rng(3), "empiris") - r
    assert 4.0 < d.std() < 8.0
    assert np.abs(np.median(d)) <= 1


def test_model_tak_dikenal_ditolak():
    with pytest.raises(ValueError):
        jitter_r(r_teratur(), 3, np.random.default_rng(4), "gauss-kaleng")
