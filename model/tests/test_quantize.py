import os

import numpy as np
import pytest

from config import ARTIFACT_DIR, MAX_MODEL_KB, WIN_LEN, N_RR_FEATURES
from src.quantize import representative_dataset_gen, stratified_indices

TFLITE = os.path.join(ARTIFACT_DIR, "model_int8.tflite")
butuh_artefak = pytest.mark.skipif(not os.path.exists(TFLITE), reason="jalankan `make quantize`")


def test_kalibrasi_wajib_memuat_kedua_kelas():
    """JEBAKAN #4: kalibrasi cuma kelas Normal → rentang aktivasi Aritmia ngawur."""
    y = np.array([0] * 900 + [1] * 100)
    idx = stratified_indices(y, n=300)
    assert (y[idx] == 0).sum() > 0 and (y[idx] == 1).sum() > 0
    assert len(idx) == len(set(idx.tolist()))


def test_proporsi_kelas_terjaga():
    y = np.array([0] * 900 + [1] * 100)
    idx = stratified_indices(y, n=300)
    assert np.isclose((y[idx] == 1).mean(), 0.1, atol=0.02)


def test_deterministik_karena_seed():
    y = np.array([0] * 900 + [1] * 100)
    assert np.array_equal(stratified_indices(y, 300), stratified_indices(y, 300))


def test_kelas_hilang_error_bukan_diam():
    with pytest.raises(ValueError):
        stratified_indices(np.zeros(100, dtype=int), n=50)


def test_generator_yield_dua_input_bernama():
    """JEBAKAN #3: model dua-input; list posisional bikin converter salah pasang."""
    n = 40
    y = np.array([0] * 36 + [1] * 4)
    gen = representative_dataset_gen(
        np.zeros((n, WIN_LEN, 1), np.float32), np.zeros((n, N_RR_FEATURES), np.float32),
        y, n=20)
    sampel = next(iter(gen()))
    assert set(sampel) == {"morphology", "rhythm"}
    assert sampel["morphology"].shape == (1, WIN_LEN, 1)
    assert sampel["rhythm"].shape == (1, N_RR_FEATURES)
    assert sampel["morphology"].dtype == np.float32


@butuh_artefak
def test_ukuran_model_di_bawah_batas():
    assert os.path.getsize(TFLITE) / 1024 < MAX_MODEL_KB


@butuh_artefak
def test_benar_benar_full_int8():
    """Tidak boleh ada tensor float32 tersisa — kalau ada, bukan full-INT8."""
    import tensorflow as tf
    interp = tf.lite.Interpreter(model_path=TFLITE)
    interp.allocate_tensors()
    dtypes = {t["dtype"].__name__ for t in interp.get_tensor_details()}
    assert "float32" not in dtypes, f"masih ada float32: {dtypes}"
    assert all(d["dtype"].__name__ == "int8" for d in interp.get_input_details())
    assert interp.get_output_details()[0]["dtype"].__name__ == "int8"
