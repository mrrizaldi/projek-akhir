import config


def test_sampling_dan_window():
    assert config.FS == 360
    assert config.WIN_LEN == config.WIN_PRE + config.WIN_POST
    assert config.WIN_LEN == 256, "jebakan PRD: 256 total, bukan +-256 (=512)"
    assert config.WIN_PRE == 128 and config.WIN_POST == 128


def test_bandpass_masuk_akal():
    assert 0 < config.BANDPASS_LOW < config.BANDPASS_HIGH < config.FS / 2
    assert config.BANDPASS_ORDER in (2, 4), "kunci satu nilai, konsisten Python<->C"


def test_label_biner_tidak_tumpang_tindih():
    assert config.NORMAL_SYMBOLS & config.ARRHYTHMIA_SYMBOLS == set()


def test_aami_map_lengkap():
    assert set(config.AAMI_MAP.values()) <= {"N", "S", "V", "F", "Q"}
    assert config.AAMI_MAP["L"] == "N" and config.AAMI_MAP["R"] == "N", \
        "LBBB/RBBB masuk N (konvensi AAMI) — keputusan sadar, catat di CLAUDE.md"
