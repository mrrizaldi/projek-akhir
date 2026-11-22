import collections
import os

import numpy as np
import pytest

import config
from src.dataset import split_train_test, record_int_id, available_records

SEBARAN = {
    "svdb":     {"N": 162339, "S": 12198, "V":  9943, "F":  23, "Q": 79},
    "incartdb": {"N": 153676, "S":  1960, "V": 20013, "F": 219, "Q":  6},
}
N_RECORD_BERKELAS = {
    "svdb":     {"N": 78, "S": 73, "V": 67, "F":  6, "Q": 20},
    "incartdb": {"N": 75, "S": 36, "V": 70, "F": 22, "Q":  5},
}
JUMLAH_RECORD = {"svdb": 78, "incartdb": 75}

SVDB_SEMUA = (
    [str(x) for x in range(800, 813)] + [str(x) for x in range(820, 830)]
    + [str(x) for x in range(840, 895)])
INCART_SEMUA = [f"I{i:02d}" for i in range(1, 76)]

HELDOUT_SVDB = ["800", "804", "808", "812", "823", "827", "841", "845", "849",
                "853", "857", "861", "865", "869", "873", "877", "881", "885",
                "889", "893"]
HELDOUT_INCART = ["I01", "I05", "I09", "I13", "I17", "I21", "I25", "I29", "I33",
                  "I37", "I41", "I45", "I49", "I53", "I57", "I61", "I65", "I69",
                  "I73"]


def _ada(db: str) -> bool:
    return len(available_records(db)) > 0


def _skip_if_half_built():
    if not os.path.exists(os.path.join(config.PER_RECORD_DIR, "100.npz")):
        pytest.skip("per_record belum dibangun (make prep)")
    for db, spec in config.DATASETS.items():
        ter_prep = [r for r in available_records(db)
                    if os.path.exists(os.path.join(config.PER_RECORD_DIR, f"{r}.npz"))]
        if ter_prep and len(ter_prep) != spec["n_record"]:
            pytest.skip(f"{db} baru {len(ter_prep)}/{spec['n_record']} ter-prep")


def test_datasets_complete_and_consistent():
    assert set(config.DATASETS) == {"mitdb", "svdb", "incartdb"}
    for db, spec in config.DATASETS.items():
        assert set(spec) == {"fs", "leads", "id_offset", "selaraskan", "n_record"}
        assert spec["fs"] > 0 and len(spec["leads"]) >= 1 and spec["n_record"] > 0
    assert config.DATASETS["mitdb"]["fs"] == config.FS, "mitdb = acuan, tak di-resample"
    assert config.DATASETS["mitdb"]["leads"] == (config.CHANNEL,), \
        "jalur mitdb harus identik dengan sebelum Fase A"


def test_id_ranges_do_not_overlap():
    rentang = {
        "mitdb": {record_int_id(r) for r in config.DS1 + config.DS2 + config.PACED_EXCLUDED},
        "svdb": {record_int_id(r, "svdb") for r in SVDB_SEMUA},
        "incartdb": {record_int_id(r, "incartdb") for r in INCART_SEMUA},
    }
    for a in rentang:
        for b in rentang:
            if a < b:
                assert not (rentang[a] & rentang[b]), f"id bertumpuk: {a} vs {b}"


def test_record_int_id_maps_alphanumeric_names():
    assert record_int_id("100") == 100
    assert record_int_id("800", "svdb") == 800
    assert record_int_id("I01", "incartdb") == 1001
    assert record_int_id("I75", "incartdb") == 1075
    with pytest.raises(ValueError):
        record_int_id("bukan-record", "mitdb")


def test_split_every_4th_deterministic():
    for semua, heldout in [(SVDB_SEMUA, HELDOUT_SVDB), (INCART_SEMUA, HELDOUT_INCART)]:
        train, test = split_train_test(semua)
        assert test == heldout, "aturan sorted()[::4] berubah — split tidak lagi sama"
        assert set(train) & set(test) == set(), "pasien bocor lintas split"
        assert sorted(train + test) == sorted(semua), "ada record hilang/dobel"
        assert 0.2 < len(test) / len(semua) < 0.3, "held-out harus ~25%"


def test_split_twice_same_result():
    assert split_train_test(INCART_SEMUA) == split_train_test(INCART_SEMUA)


def test_ds2_mitdb_untouched_by_phase_a():
    assert config.DS2 == [100, 103, 105, 111, 113, 117, 121, 123, 200, 202, 210,
                          212, 213, 214, 219, 221, 222, 228, 231, 232, 233, 234]
    assert len(config.DS1) == 22 and len(config.DS2) == 22
    assert config.VAL_RECORDS == [101, 114, 201, 220, 223]
    assert set(config.VAL_RECORDS) <= set(config.DS1)


@pytest.mark.parametrize("db", ["svdb", "incartdb"])
def test_class_distribution_matches_measured(db):
    n_ada = len(available_records(db))
    if n_ada == 0:
        pytest.skip(f"{db} belum di-download (python scripts/download_data.py {db})")
    if n_ada < JUMLAH_RECORD[db]:
        pytest.skip(f"{db} baru {n_ada}/{JUMLAH_RECORD[db]} record — download belum selesai")
    import wfdb

    per_kelas = collections.Counter()
    per_kelas_record = collections.defaultdict(set)
    for rec in available_records(db):
        ann = wfdb.rdann(os.path.join(config.raw_dir(db), rec), "atr")
        for sym in ann.symbol:
            if sym in config.BEAT_SYMBOLS:
                kelas = config.AAMI_MAP[sym]
                per_kelas[kelas] += 1
                per_kelas_record[kelas].add(rec)

    assert len(available_records(db)) == JUMLAH_RECORD[db]
    for kelas, n in SEBARAN[db].items():
        assert per_kelas[kelas] == n, f"{db} kelas {kelas}: {per_kelas[kelas]} != {n}"
        assert len(per_kelas_record[kelas]) == N_RECORD_BERKELAS[db][kelas], \
            f"{db} kelas {kelas} tersebar di {len(per_kelas_record[kelas])} record"


@pytest.mark.parametrize("db", ["svdb", "incartdb"])
def test_resample_contract(db):
    if not _ada(db):
        pytest.skip(f"{db} belum di-download")
    from src.io_mitdb import load_record
    rec = available_records(db)[0]
    fs_source = config.DATASETS[db]["fs"]
    signal, r, sym, fs = load_record(rec, db=db)

    assert fs == config.FS, "load_record wajib mengembalikan FS, bukan fs asal"
    assert len(r) == len(sym), "R-peak & simbol harus tetap sejajar"
    assert np.all(np.diff(r) > 0), "R-peak harus urut menaik (RR > 0)"
    assert r.max() < len(signal), "indeks R keluar dari sinyal hasil resample"
    durasi_asal = wfdb_sig_len(db, rec) / fs_source
    assert abs(len(signal) / config.FS - durasi_asal) / durasi_asal < 0.01, \
        f"durasi berubah: {len(signal)/config.FS:.1f}s vs {durasi_asal:.1f}s"


def test_align_puts_peak_at_win_pre():
    from src.preprocessing import align_r
    n = 4000
    x = np.zeros(n, dtype=np.float32)
    anot = np.arange(400, n - 400, 400)
    puncak = anot + 9
    x[puncak] = 1.0
    r = align_r(anot, x)
    assert np.all(r == puncak - config.GROUP_DELAY_SAMPLES)
    assert np.all(puncak - (r - config.WIN_PRE)
                  == config.WIN_PRE + config.GROUP_DELAY_SAMPLES)


def test_align_does_not_jump_to_t_wave():
    from src.preprocessing import align_r
    x = np.zeros(2000, dtype=np.float32)
    anot = np.array([500])
    x[504] = 1.0
    x[504 + 90] = 3.0
    assert align_r(anot, x)[0] == 504 - config.GROUP_DELAY_SAMPLES


def test_mitdb_never_aligned():
    assert config.DATASETS["mitdb"]["selaraskan"] is False
    assert config.DATASETS["svdb"]["selaraskan"] is True
    assert config.DATASETS["incartdb"]["selaraskan"] is True
    assert 0 < config.ALIGN_WIN < 25, "PT_REFINE_WIN=25 terlalu lebar untuk ini"


def test_build_split_multi_no_leak_and_ds2_intact():
    _skip_if_half_built()
    from src.dataset import build_split_multi, build_split

    h = build_split_multi()
    assert "train" in h and "ds2" in h

    _, test_old = build_split()
    for k in ("X_morph", "X_rr", "y", "records"):
        assert np.array_equal(h["ds2"][k], test_old[k]), f"ds2 {k} bergeser"

    r_train = set(np.unique(h["train"]["records"]))
    for nama, d in h.items():
        if nama == "train":
            continue
        assert not (set(np.unique(d["records"])) & r_train), f"bocor train <-> {nama}"
        n = len(d["y"])
        assert d["X_morph"].shape == (n, config.WIN_LEN, 1)
        assert not np.isnan(d["X_rr"]).any()


def test_val_stays_ds2_mirror_not_train_mirror():
    _skip_if_half_built()
    from src.dataset import build_split_multi, split_train_val

    h = build_split_multi()
    _, val = split_train_val(h["train"])
    rasio_val = float(val["y"].mean())
    rasio_ds2 = float(h["ds2"]["y"].mean())
    assert abs(rasio_val - rasio_ds2) < 0.03, \
        f"VAL {rasio_val:.4f} vs DS2 {rasio_ds2:.4f} — kalibrasi threshold jadi bias"
    assert set(np.unique(val["records"])) == set(config.VAL_RECORDS)


def test_incartdb_test_only_not_train():
    assert config.TRAIN_DATABASES == ("mitdb", "svdb")
    assert "incartdb" in config.DATASETS, "tetap terdaftar — dia masih jadi TEST-C"
    _skip_if_half_built()
    from src.dataset import build_split_multi, split_train_test

    h = build_split_multi()
    assert "incartdb_test" in h, "TEST-C hilang — itu pemakaian terbaik incartdb"
    latih_incart = {record_int_id(r, "incartdb")
                    for r in split_train_test(available_records("incartdb"))[0]}
    assert not (latih_incart & set(np.unique(h["train"]["records"]).tolist())), \
        "porsi train incartdb bocor ke train"


def test_split_multi_rejects_half_built_database(monkeypatch):
    _skip_if_half_built()
    from src.dataset import build_split_multi

    db = next((d for d in ("svdb", "incartdb")
               if _ada(d) and os.path.exists(
                   os.path.join(config.PER_RECORD_DIR, f"{available_records(d)[0]}.npz"))), None)
    if db is None:
        pytest.skip("belum ada database tambahan yang ter-prep")

    monkeypatch.setitem(config.DATASETS[db], "n_record",
                        config.DATASETS[db]["n_record"] + 1)
    with pytest.raises(ValueError, match=db):
        build_split_multi()


def wfdb_sig_len(db: str, rec: str) -> int:
    import wfdb
    return wfdb.rdheader(os.path.join(config.raw_dir(db), rec)).sig_len
