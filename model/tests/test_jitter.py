import numpy as np
import pytest

from src.preprocessing import jitter_r


def regular_r(n=200, rr=300):
    return np.arange(n, dtype=np.int64) * rr + 1000


def test_uniform_zero_delta_does_not_shift():
    r = regular_r()
    assert np.array_equal(jitter_r(r, 0, np.random.default_rng(0), "seragam"), r)


def test_uniform_bounded_by_delta():
    r = regular_r()
    d = jitter_r(r, 5, np.random.default_rng(1), "seragam") - r
    assert np.abs(d).max() <= 5
    assert np.abs(d).max() > 0


@pytest.mark.parametrize("model,delta", [("seragam", 18), ("normal", 6), ("empiris", 0)])
def test_order_stays_ascending(model, delta):
    j = jitter_r(regular_r(), delta, np.random.default_rng(2), model)
    assert (np.diff(j) >= 0).all(), "RR negatif — pasangan beat bertukar tempat"


def test_empirical_mimics_measured_distribution():
    r = regular_r(20000)
    d = jitter_r(r, 0, np.random.default_rng(3), "empiris") - r
    assert 4.0 < d.std() < 8.0
    assert np.abs(np.median(d)) <= 1


def test_unknown_model_rejected():
    with pytest.raises(ValueError):
        jitter_r(regular_r(), 3, np.random.default_rng(4), "gauss-kaleng")
