"""Assert DoD Fase 0 (PRD hal. 7) — loader MIT-BIH.

    make test        (atau: pytest tests/ -q)

Butuh dataset di data/raw/mitdb/ (gitignored) — kalau tidak ada, semua di-skip.
"""
import os

import numpy as np
import pytest
import wfdb

import config
from src.io_mitdb import load_record

pytestmark = pytest.mark.skipif(
    not os.path.isdir(config.RAW_DIR), reason="dataset belum di-download (make data)"
)


@pytest.fixture(scope="module")
def rec100():
    """Record 30 menit; dimuat sekali dipakai beberapa test."""
    return load_record("100")


def test_dod_record_100(rec100):
    signal, r_locations, symbols, fs = rec100
    assert fs == config.FS
    assert len(signal) == 650_000, "30 menit x 360 Hz"
    assert 2_000 < len(r_locations) < 2_500, "MIT-BIH rec 100 ~2.200 R-peak"


def test_array_sejajar_dan_dalam_batas(rec100):
    signal, r_locations, symbols, _ = rec100
    assert len(r_locations) == len(symbols), "sample & symbol harus tetap sejajar"
    assert r_locations.min() >= 0 and r_locations.max() < len(signal)
    assert np.all(np.diff(r_locations) > 0), "R-peak harus urut menaik (RR > 0)"


def test_simbol_non_beat_terbuang(rec100):
    _, r_locations, symbols, _ = rec100
    assert set(symbols) <= config.BEAT_SYMBOLS

    raw = wfdb.rdann(os.path.join(config.RAW_DIR, "100"), "atr")
    assert len(r_locations) < len(raw.sample), \
        "rec 100 punya anotasi '+' — kalau jumlahnya sama, filter tidak jalan"


def test_kanal_mlii_dipilih_eksplisit():
    """Rec 114 kanalnya ['V5', 'MLII'] — index 0 BUKAN MLII."""
    signal, _, _, _ = load_record("114")
    record = wfdb.rdrecord(os.path.join(config.RAW_DIR, "114"))
    assert record.sig_name.index(config.CHANNEL) == 1, "asumsi test: MLII di index 1"
    assert np.allclose(signal, record.p_signal[:, 1])
    assert not np.allclose(signal, record.p_signal[:, 0]), "kebaca V5, bukan MLII"


@pytest.mark.parametrize("record_id", ["102", "104"])
def test_record_tanpa_mlii_ditolak(record_id):
    """Menolak lebih aman daripada fallback diam-diam ke kanal lain."""
    with pytest.raises(ValueError, match=config.CHANNEL):
        load_record(record_id)
