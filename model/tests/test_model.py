import numpy as np

from config import WIN_LEN, N_RR_FEATURES
from src.model import build_hybrid_model


def test_param_budget():
    """~6.000 param (PRD). Jauh lebih besar = tak sengaja pakai Flatten."""
    n = build_hybrid_model().count_params()
    assert 5000 <= n <= 7000, f"count_params()={n}, cek Flatten/Dense kegedean"


def test_dua_input_satu_output():
    m = build_hybrid_model()
    assert len(m.inputs) == 2
    assert tuple(m.inputs[0].shape) == (None, WIN_LEN, 1)
    assert tuple(m.inputs[1].shape) == (None, N_RR_FEATURES)
    assert tuple(m.output.shape) == (None, 1)


def test_predict_dummy_di_rentang_probabilitas():
    m = build_hybrid_model()
    y = m.predict([np.zeros((4, WIN_LEN, 1)), np.zeros((4, N_RR_FEATURES))], verbose=0)
    assert y.shape == (4, 1)
    assert np.all((y >= 0) & (y <= 1))


def test_cabang_ritme_benar_benar_terpakai():
    """Ubah HANYA fitur RR → output harus berubah. Kalau tidak, concat salah sambung."""
    m = build_hybrid_model()
    morph = np.zeros((1, WIN_LEN, 1))
    a = m.predict([morph, np.zeros((1, N_RR_FEATURES))], verbose=0)
    b = m.predict([morph, np.full((1, N_RR_FEATURES), 5.0)], verbose=0)
    assert not np.isclose(a, b), "cabang RR tidak mempengaruhi output"
