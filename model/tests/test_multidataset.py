"""Assert DoD Fase A (19 Sep 2026) — penggabungan mitdb + svdb + incartdb.

    make test        (atau: pytest tests/test_multidataset.py -q)

Angka di file ini BUKAN dari paper. Semuanya diukur pada 19 Sep 2026 dari
anotasi asli PhysioNet yang dipetakan lewat config.AAMI_MAP, dan dibekukan di
sini supaya perubahan senyap ketahuan. Kalau salah satu gagal, urutan
tersangkanya: (1) daftar record berubah, (2) AAMI_MAP/BEAT_SYMBOLS diedit,
(3) DATASETS salah isi — BUKAN "angkanya kebetulan beda".

Test yang butuh database di data/raw/<db>/ otomatis di-skip.
"""
import collections
import os

import numpy as np
import pytest

import config
from src.dataset import bagi_train_test, record_int_id, records_tersedia

# ── Sebaran terukur 19 Sep 2026 (anotasi mentah, sebelum prep_beats buang tepi) ──
SEBARAN = {
    "svdb":     {"N": 162339, "S": 12198, "V":  9943, "F":  23, "Q": 79},
    "incartdb": {"N": 153676, "S":  1960, "V": 20013, "F": 219, "Q":  6},
}
# Di berapa record tiap kelas muncul. Ini yang sebenarnya jadi alasan Fase A:
# F kita 372 dari 394 beat ada di record 208 SAJA (1 pasien efektif), sedangkan
# incartdb menyebar 219 beat di 22 record. Yang diobati cakupan, bukan jumlah.
N_RECORD_BERKELAS = {
    "svdb":     {"N": 78, "S": 73, "V": 67, "F":  6, "Q": 20},
    "incartdb": {"N": 75, "S": 36, "V": 70, "F": 22, "Q":  5},
}
JUMLAH_RECORD = {"svdb": 78, "incartdb": 75}

# Daftar lengkap, dibekukan supaya aturan split bisa diuji tanpa download.
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
    return len(records_tersedia(db)) > 0


# ── 1. Tabel DATASETS ────────────────────────────────────────────────────────

def test_datasets_lengkap_dan_konsisten():
    assert set(config.DATASETS) == {"mitdb", "svdb", "incartdb"}
    for db, spec in config.DATASETS.items():
        assert set(spec) == {"fs", "leads", "id_offset"}
        assert spec["fs"] > 0 and len(spec["leads"]) >= 1
    assert config.DATASETS["mitdb"]["fs"] == config.FS, "mitdb = acuan, tak di-resample"
    assert config.DATASETS["mitdb"]["leads"] == (config.CHANNEL,), \
        "jalur mitdb harus identik dengan sebelum Fase A"


def test_rentang_id_tidak_bertumpuk():
    """records bertipe int32; tiga rentang harus disjoint atau metrik per-record bohong."""
    rentang = {
        "mitdb": {record_int_id(r) for r in config.DS1 + config.DS2 + config.PACED_EXCLUDED},
        "svdb": {record_int_id(r, "svdb") for r in SVDB_SEMUA},
        "incartdb": {record_int_id(r, "incartdb") for r in INCART_SEMUA},
    }
    for a in rentang:
        for b in rentang:
            if a < b:
                assert not (rentang[a] & rentang[b]), f"id bertumpuk: {a} vs {b}"


def test_record_int_id_memetakan_nama_alfanumerik():
    assert record_int_id("100") == 100
    assert record_int_id("800", "svdb") == 800
    assert record_int_id("I01", "incartdb") == 1001
    assert record_int_id("I75", "incartdb") == 1075
    with pytest.raises(ValueError):
        record_int_id("bukan-record", "mitdb")


# ── 2. Aturan split (tanpa perlu download) ───────────────────────────────────

def test_split_setiap_ke_4_deterministik():
    for semua, heldout in [(SVDB_SEMUA, HELDOUT_SVDB), (INCART_SEMUA, HELDOUT_INCART)]:
        train, test = bagi_train_test(semua)
        assert test == heldout, "aturan sorted()[::4] berubah — split tidak lagi sama"
        assert set(train) & set(test) == set(), "pasien bocor lintas split"
        assert sorted(train + test) == sorted(semua), "ada record hilang/dobel"
        assert 0.2 < len(test) / len(semua) < 0.3, "held-out harus ~25%"


def test_split_dua_kali_hasil_sama():
    """Tak ada RNG di dalamnya — dipanggil dua kali harus identik."""
    assert bagi_train_test(INCART_SEMUA) == bagi_train_test(INCART_SEMUA)


def test_ds2_mitdb_tidak_tersentuh_fase_a():
    """Satu-satunya angka yang sebanding literatur. Fase A TIDAK boleh mengubahnya."""
    assert config.DS2 == [100, 103, 105, 111, 113, 117, 121, 123, 200, 202, 210,
                          212, 213, 214, 219, 221, 222, 228, 231, 232, 233, 234]
    assert len(config.DS1) == 22 and len(config.DS2) == 22
    assert config.VAL_RECORDS == [101, 114, 201, 220, 223]
    assert set(config.VAL_RECORDS) <= set(config.DS1)


# ── 3. Sebaran kelas (butuh database di data/raw/) ───────────────────────────

@pytest.mark.parametrize("db", ["svdb", "incartdb"])
def test_sebaran_kelas_sesuai_yang_diukur(db):
    n_ada = len(records_tersedia(db))
    if n_ada == 0:
        pytest.skip(f"{db} belum di-download (python scripts/download_data.py {db})")
    if n_ada < JUMLAH_RECORD[db]:
        pytest.skip(f"{db} baru {n_ada}/{JUMLAH_RECORD[db]} record — download belum selesai")
    import wfdb

    per_kelas = collections.Counter()
    per_kelas_record = collections.defaultdict(set)
    for rec in records_tersedia(db):
        ann = wfdb.rdann(os.path.join(config.raw_dir(db), rec), "atr")
        for sym in ann.symbol:
            if sym in config.BEAT_SYMBOLS:
                kelas = config.AAMI_MAP[sym]
                per_kelas[kelas] += 1
                per_kelas_record[kelas].add(rec)

    assert len(records_tersedia(db)) == JUMLAH_RECORD[db]
    for kelas, n in SEBARAN[db].items():
        assert per_kelas[kelas] == n, f"{db} kelas {kelas}: {per_kelas[kelas]} != {n}"
        assert len(per_kelas_record[kelas]) == N_RECORD_BERKELAS[db][kelas], \
            f"{db} kelas {kelas} tersebar di {len(per_kelas_record[kelas])} record"


def test_q_tetap_bukan_kelas_yang_bisa_dilaporkan():
    """Tiga database digabung memberi ~93 beat Q. Dijaga supaya tidak ada yang
    tergoda menambahkan cabang Q di tahap 2 berdasarkan angka yang tidak ada."""
    q_baru = SEBARAN["svdb"]["Q"] + SEBARAN["incartdb"]["Q"]
    assert q_baru + 8 < 200, "kalau ini gagal, Q mungkin sudah layak — cek ulang"


# ── 4. Kontrak resample (stub sampai user mengisinya) ────────────────────────

def test_resample_mitdb_dilewati():
    """fs == FS harus lewat tanpa menyentuh resample — jalur mitdb wajib utuh."""
    if not os.path.isdir(config.RAW_DIR):
        pytest.skip("mitdb belum di-download")
    from src.io_mitdb import load_record
    signal, r, sym, fs = load_record("100")
    assert fs == config.FS and len(signal) == 650_000
    assert len(r) == len(sym) and np.all(np.diff(r) > 0)


@pytest.mark.parametrize("db", ["svdb", "incartdb"])
def test_resample_kontrak(db):
    """Sebelum diisi: NotImplementedError. Sesudah: fs & posisi R harus benar."""
    if not _ada(db):
        pytest.skip(f"{db} belum di-download")
    from src.io_mitdb import load_record
    rec = records_tersedia(db)[0]
    fs_asal = config.DATASETS[db]["fs"]
    signal, r, sym, fs = load_record(rec, db=db)

    assert fs == config.FS, "load_record wajib mengembalikan FS, bukan fs asal"
    assert len(r) == len(sym), "R-peak & simbol harus tetap sejajar"
    assert np.all(np.diff(r) > 0), "R-peak harus urut menaik (RR > 0)"
    assert r.max() < len(signal), "indeks R keluar dari sinyal hasil resample"
    # Durasi harus kekal: meleset >1% berarti rasio resample-nya salah.
    durasi_asal = wfdb_sig_len(db, rec) / fs_asal
    assert abs(len(signal) / config.FS - durasi_asal) / durasi_asal < 0.01, \
        f"durasi berubah: {len(signal)/config.FS:.1f}s vs {durasi_asal:.1f}s"


def wfdb_sig_len(db: str, rec: str) -> int:
    import wfdb
    return wfdb.rdheader(os.path.join(config.raw_dir(db), rec)).sig_len
