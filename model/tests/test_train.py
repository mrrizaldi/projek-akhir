import numpy as np
import pytest
from tensorflow import keras

from src.train import RataBobotTerbaik, make_class_weights


def _model_satu_bobot():
    return keras.Sequential([keras.layers.Input(shape=(1,)),
                             keras.layers.Dense(1, use_bias=False)])


def _jalankan(cb, riwayat):
    m = _model_satu_bobot()
    cb.set_model(m)
    for auc, w in riwayat:
        m.set_weights([np.array([[w]], dtype=np.float32)])
        cb.on_epoch_end(0, {"val_auc": auc})
    cb.on_train_end()
    return float(m.get_weights()[0][0, 0])


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


def test_rata_bobot_merata_ratakan_n_terbaik_bukan_memungut_argmax():
    """Inti T7: epoch yang nyaris seri dirata-rata, bukan dipilih satu.

    top-3 val_auc = 0,92/0,91/0,90 -> bobot 3, 5, 4 -> rerata 4,0.
    Kalau yang jalan cuma argmax, hasilnya 3,0 (bobot epoch ber-auc tertinggi).
    """
    hasil = _jalankan(RataBobotTerbaik("val_auc", 3),
                      [(0.90, 4.0), (0.80, 50.0), (0.92, 3.0),
                       (0.50, 99.0), (0.91, 5.0)])
    assert np.isclose(hasil, 4.0)


def test_epoch_buruk_tidak_ikut_rata_rata():
    """Epoch ber-val_auc rendah harus terbuang, bukan menyeret rerata."""
    hasil = _jalankan(RataBobotTerbaik("val_auc", 2),
                      [(0.9, 1.0), (0.1, 1000.0), (0.8, 3.0)])
    assert np.isclose(hasil, 2.0)


def test_n_lebih_besar_dari_jumlah_epoch_pakai_semua():
    hasil = _jalankan(RataBobotTerbaik("val_auc", 10), [(0.9, 2.0), (0.8, 4.0)])
    assert np.isclose(hasil, 3.0)
