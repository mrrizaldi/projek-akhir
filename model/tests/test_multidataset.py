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
        assert set(spec) == {"fs", "leads", "id_offset", "selaraskan"}
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


# ── 5. Penyelarasan anotasi antar-database (gate A2) ─────────────────────────

def test_selaraskan_menaruh_puncak_di_win_pre():
    """Puncak buatan digeser 9 sampel dari anotasi -> harus balik ke WIN_PRE+delay."""
    from src.preprocessing import selaraskan_r
    n = 4000
    x = np.zeros(n, dtype=np.float32)
    anot = np.arange(400, n - 400, 400)
    puncak = anot + 9                      # persis pola svdb: anotasi lebih awal
    x[puncak] = 1.0
    r = selaraskan_r(anot, x)
    assert np.all(r == puncak - config.GROUP_DELAY_SAMPLES)
    # window dipotong di r -> puncak mendarat di WIN_PRE + GROUP_DELAY = 132
    assert np.all(puncak - (r - config.WIN_PRE)
                  == config.WIN_PRE + config.GROUP_DELAY_SAMPLES)


def test_selaraskan_tidak_melompat_ke_gelombang_t():
    """T lebih tinggi tapi 250 ms dari R: di luar ALIGN_WIN, jangan diambil."""
    from src.preprocessing import selaraskan_r
    x = np.zeros(2000, dtype=np.float32)
    anot = np.array([500])
    x[504] = 1.0                            # R (group delay +4)
    x[504 + 90] = 3.0                       # T, 250 ms = 90 sampel, lebih tinggi
    assert selaraskan_r(anot, x)[0] == 504 - config.GROUP_DELAY_SAMPLES


def test_mitdb_tidak_pernah_diselaraskan():
    """mitdb acuan golden_ref.h & semua ablasi terkunci. Median +3 vs +4 berarti
    menyelaraskannya menggeser r ~1 sampel dan membatalkan semuanya."""
    assert config.DATASETS["mitdb"]["selaraskan"] is False
    assert config.DATASETS["svdb"]["selaraskan"] is True
    assert config.DATASETS["incartdb"]["selaraskan"] is True
    assert 0 < config.ALIGN_WIN < 25, "PT_REFINE_WIN=25 terlalu lebar untuk ini"


@pytest.mark.parametrize("rec", ["100", "232"])
def test_jalur_mitdb_byte_identik_setelah_fase_a(rec):
    """Fase A tidak boleh mengubah SATU angka pun di mitdb.

    Dipilih record DS2 (tak pernah dijitter) supaya deterministik tanpa harus
    memutar ulang urutan rng. Cek penuh 44/44 record sudah dijalankan manual
    19 Sep — hasilnya 44 identik, 0 berubah (plan §3).
    """
    npz = os.path.join(config.PER_RECORD_DIR, f"{rec}.npz")
    if not os.path.exists(npz):
        pytest.skip("per_record belum dibangun (make prep)")
    from scripts.prep_beats import process_record
    from src.preprocessing import design_bandpass_sos

    baru = process_record(rec, design_bandpass_sos(), db="mitdb")
    with np.load(npz, allow_pickle=True) as lama:
        for k in ("windows", "rr", "labels", "symbols", "n_dropped"):
            assert np.array_equal(lama[k], baru[k]), f"rec {rec}: {k} berubah"


# ── 6. Split gabungan Fase A ─────────────────────────────────────────────────

def test_build_split_multi_tidak_bocor_dan_ds2_utuh():
    if not os.path.exists(os.path.join(config.PER_RECORD_DIR, "100.npz")):
        pytest.skip("per_record belum dibangun (make prep)")
    from src.dataset import build_split_multi, build_split

    h = build_split_multi()
    assert "train" in h and "ds2" in h

    # DS2 di split gabungan HARUS identik dengan test.npz jalur lama.
    _, test_lama = build_split()
    for k in ("X_morph", "X_rr", "y", "records"):
        assert np.array_equal(h["ds2"][k], test_lama[k]), f"ds2 {k} bergeser"

    r_train = set(np.unique(h["train"]["records"]))
    for nama, d in h.items():
        if nama == "train":
            continue
        assert not (set(np.unique(d["records"])) & r_train), f"bocor train <-> {nama}"
        n = len(d["y"])
        assert d["X_morph"].shape == (n, config.WIN_LEN, 1)
        assert not np.isnan(d["X_rr"]).any()


def test_val_tetap_cermin_ds2_bukan_cermin_train():
    """Threshold dikalibrasi di VAL lalu dipakai di DS2, jadi VAL harus mirip DS2.
    Train boleh bergeser (svdb kaya S) — itu justru yang diinginkan."""
    if not os.path.exists(os.path.join(config.PER_RECORD_DIR, "100.npz")):
        pytest.skip("per_record belum dibangun (make prep)")
    from src.dataset import build_split_multi, split_train_val

    h = build_split_multi()
    _, val = split_train_val(h["train"])
    rasio_val = float(val["y"].mean())
    rasio_ds2 = float(h["ds2"]["y"].mean())
    assert abs(rasio_val - rasio_ds2) < 0.03, \
        f"VAL {rasio_val:.4f} vs DS2 {rasio_ds2:.4f} — kalibrasi threshold jadi bias"
    assert set(np.unique(val["records"])) == set(config.VAL_RECORDS)


def wfdb_sig_len(db: str, rec: str) -> int:
    import wfdb
    return wfdb.rdheader(os.path.join(config.raw_dir(db), rec)).sig_len
