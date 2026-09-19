import os

import numpy as np
import pytest

from config import ARTIFACT_DIR, MAX_MODEL_KB, WIN_LEN, N_RR_FEATURES
from src.quantize import (assert_skala_ritme_wajar, representative_dataset_gen,
                          stratified_indices)

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


@butuh_artefak
def test_skala_ritme_artefak_wajar():
    """Ranjau senyap: skala INT8 input ritme diturunkan dari min/max REP_SAMPLES
    sampel kalibrasi. Satu beat ber-RR ekstrem di sana (record 207: RR_prev =
    100 s) melebarkan skala ~30x, cabang ritme mati, dan yang TERLIHAT cuma
    recall S buruk — bukan error. Terukur 19 Sep: sehat 0,0129; outlier disuntik
    0,3952. Peluang kena per seed 1,8% (tiga database).
    """
    from config import MAX_RHYTHM_SCALE
    with open(TFLITE, "rb") as f:
        skala = assert_skala_ritme_wajar(f.read())
    assert skala == pytest.approx(0.0129, abs=5e-3), f"skala bergeser: {skala}"
    assert skala < MAX_RHYTHM_SCALE


@butuh_artefak
def test_assert_skala_ritme_benar_benar_menyalak():
    """Ambang diperketat di bawah nilai sehat -> harus raise, bukan lolos diam."""
    with open(TFLITE, "rb") as f:
        blob = f.read()
    with pytest.raises(ValueError, match="skala kuantisasi input ritme"):
        assert_skala_ritme_wajar(blob, ambang=0.001)
