"""Assert DoD yang berupa angka — bagian config & split (PRD Fase 0-3).

    make test        (atau: pytest tests/ -q)

Test yang butuh konstanta belum ada otomatis di-skip, jadi file ini tetap hijau
selama pengisian config.py bertahap.
"""
import pytest

import config


def test_sampling_dan_window():
    assert config.FS == 360
    assert config.WIN_LEN == config.WIN_PRE + config.WIN_POST
    assert config.WIN_LEN == 250, "jebakan PRD: 250 total, bukan +-250 (=500)"


def test_bandpass_masuk_akal():
    assert 0 < config.BANDPASS_LOW < config.BANDPASS_HIGH < config.FS / 2
    assert config.BANDPASS_ORDER in (2, 4), "kunci satu nilai, konsisten Python<->C"


def test_label_biner_tidak_tumpang_tindih():
    assert config.NORMAL_SYMBOLS & config.ARRHYTHMIA_SYMBOLS == set()


@pytest.mark.skipif(not hasattr(config, "DS1"), reason="DS1/DS2 belum diisi (Fase 3)")
def test_split_inter_patient_disjoint():
    ds1, ds2 = set(config.DS1), set(config.DS2)
    paced = set(config.PACED_EXCLUDED)
    assert ds1 & ds2 == set(), "kebocoran antar-pasien: record muncul di DS1 dan DS2"
    assert (ds1 | ds2) & paced == set(), "record paced tidak boleh ikut latih/uji"
    assert len(ds1) == len(config.DS1) and len(ds2) == len(config.DS2), "ada duplikat"
    assert len(ds1 | ds2 | paced) == 48, "total record MIT-BIH harus 48"


@pytest.mark.skipif(not hasattr(config, "AAMI_MAP"), reason="AAMI_MAP belum diisi (Fase 2)")
def test_aami_map_lengkap():
    assert set(config.AAMI_MAP.values()) <= {"N", "S", "V", "F", "Q"}
    assert config.AAMI_MAP["L"] == "N" and config.AAMI_MAP["R"] == "N", \
        "LBBB/RBBB masuk N (konvensi AAMI) — keputusan sadar, catat di CLAUDE.md"
