import numpy as np

from config import FS, RR_LOCAL_WINDOW_BEATS
from src.features_rr import to_aami_class, to_binary_label, compute_rr_features


def test_label_mapping():
    assert to_binary_label(to_aami_class("N")) == 0
    assert to_binary_label(to_aami_class("L")) == 0   # LBBB → N (keputusan sadar)
    assert to_binary_label(to_aami_class("V")) == 1
    assert to_binary_label(to_aami_class("/")) == 1   # paced → Q → aritmia


def test_rr_ritme_konstan():
    """Ritme sempurna 1 detik: RR_prev=1, RR_ratio=1, dRR=0 (bukan NaN)."""
    r = np.arange(20) * FS
    f = compute_rr_features(r)
    assert f.shape == (20, 3)
    assert np.isnan(f[0]).all() and np.isnan(f[1, 2])
    assert np.allclose(f[2:], [1.0, 1.0, 0.0], atol=1e-5)


def test_rr_panjang_dan_kausalitas():
    """Panjang == len(r) utuh; beat masa depan tidak mempengaruhi beat sekarang."""
    rng = np.random.default_rng(0)
    r = np.cumsum(rng.integers(250, 450, size=60)).astype(np.int64)
    f = compute_rr_features(r)
    assert len(f) == len(r)
    k = 30
    assert np.allclose(compute_rr_features(r[:k])[2:k], f[2:k], equal_nan=True)


def test_rr_local_avg_menyusut_di_tepi():
    """Jendela lokal beat awal memakai interval yang ada saja, bukan pad."""
    r = np.array([0, 360, 1080])          # RR = 1.0 s, lalu 2.0 s
    f = compute_rr_features(r)
    assert np.isclose(f[1, 1], 1.0)                    # avg = 1.0 → ratio 1.0
    assert np.isclose(f[2, 1], 2.0 / 1.5)              # avg (1+2)/2 = 1.5
    assert np.isclose(f[2, 2], 1.0)                    # dRR = 2.0 - 1.0


def test_rr_record_pendek_tidak_crash():
    assert np.isnan(compute_rr_features(np.array([5]))).all()
    assert compute_rr_features(np.array([], dtype=int)).shape == (0, 3)
