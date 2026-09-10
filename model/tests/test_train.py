import numpy as np
import pytest

from src.train import make_class_weights


def test_bobot_inversely_proportional():
    """w_c = N / (2 * n_c). Kelas minoritas dapat bobot lebih besar."""
    y = np.array([0] * 90 + [1] * 10)
    w = make_class_weights(y)
    assert np.isclose(w[0], 100 / (2 * 90))
    assert np.isclose(w[1], 100 / (2 * 10))
    assert w[1] > w[0]


def test_kontribusi_dua_kelas_jadi_setara():
    """Inti class_weight: n_c * w_c sama untuk kedua kelas."""
    y = np.array([0] * 90 + [1] * 10)
    w = make_class_weights(y)
    assert np.isclose(90 * w[0], 10 * w[1])


def test_seimbang_berarti_bobot_satu():
    w = make_class_weights(np.array([0, 0, 1, 1]))
    assert np.isclose(w[0], 1.0) and np.isclose(w[1], 1.0)


def test_kelas_kosong_error_bukan_pembagian_nol():
    with pytest.raises(ValueError):
        make_class_weights(np.zeros(10, dtype=int))
