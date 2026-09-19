"""dataset — Fase 3: rakit split inter-patient DS1/DS2. Walkthrough: docs/dataset-walkthrough.md"""
import os

import numpy as np

from config import (
    DATASETS, DS1, DS2, PACED_EXCLUDED, PER_RECORD_DIR, SPLIT_SETIAP_KE,
    VAL_RECORDS, WIN_LEN, raw_dir,
)


def assert_split_valid() -> None:
    ds1, ds2, paced = set(DS1), set(DS2), set(PACED_EXCLUDED)
    if ds1 & ds2:
        raise ValueError(f"DS1 ∩ DS2 tidak kosong: {sorted(ds1 & ds2)}")
    if (ds1 | ds2) & paced:
        raise ValueError(f"record paced ikut di split: {sorted((ds1 | ds2) & paced)}")
    total = len(ds1) + len(ds2) + len(paced)
    if total != 48:
        raise ValueError(f"total record {total}, harus 48")


def record_int_id(record_id, db: str = "mitdb") -> int:
    """Nama record -> int32 untuk kolom `records`. Tiga rentang tidak bertumpuk.

        mitdb     "100".."234"  -> 100..234    (offset 0)
        svdb      "800".."894"  -> 800..894    (offset 0)
        incartdb  "I01".."I75"  -> 1001..1075  (offset 1000)

    Kenapa perlu: `records` dipakai metrik per-record dan cek kebocoran lintas
    split, dan tipenya int32. int("I18") melempar ValueError — jadi tanpa peta
    ini incartdb menabrak stack_records, bukan gagal dengan pesan yang berguna.
    """
    rec = str(record_id)
    angka = rec[1:] if rec[:1].isalpha() else rec
    if not angka.isdigit():
        raise ValueError(f"record id tak bisa dipetakan ke int: {record_id!r} ({db})")
    return DATASETS[db]["id_offset"] + int(angka)


def bagi_train_test(records) -> tuple:
    """Held-out = setiap record ke-SPLIT_SETIAP_KE dalam urutan tersortir.

    Aturan, bukan seed: tidak ada seed yang bisa dipancing, dan siapa pun bisa
    memverifikasi hasilnya dengan sorted(records)[::4]. Dipakai HANYA untuk
    svdb & incartdb — DS1/DS2 mitdb tetap literal de Chazal di config.py.
    """
    r = sorted(str(x) for x in records)
    test = r[::SPLIT_SETIAP_KE]
    return [x for x in r if x not in set(test)], test


def records_tersedia(db: str) -> list:
    """Record LENGKAP (.hea+.dat+.atr) di data/raw/<db>/; mitdb tanpa PACED_EXCLUDED.

    Menuntut ketiganya, bukan cuma .hea: download yang masih jalan meninggalkan
    .hea tanpa .atr, dan itu jadi FileNotFoundError jauh di hilir (wfdb.rdann)
    bukan "belum lengkap" di sini.
    """
    d = raw_dir(db)
    if not os.path.isdir(d):
        return []
    ada = set(os.listdir(d))
    ids = sorted(f[:-4] for f in ada if f.endswith(".hea")
                 and f"{f[:-4]}.dat" in ada and f"{f[:-4]}.atr" in ada)
    if db == "mitdb":
        excluded = {str(x) for x in PACED_EXCLUDED}
        ids = [i for i in ids if i not in excluded]
    return ids


def stack_records(record_ids, per_record_dir: str = PER_RECORD_DIR,
                  db: str = "mitdb") -> dict:
    morph, rr, y, origin = [], [], [], []
    for rec in record_ids:
        path = os.path.join(per_record_dir, f"{rec}.npz")
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} — jalankan `make prep` dulu")
        with np.load(path) as z:
            morph.append(z["windows"])
            rr.append(z["rr"])
            y.append(z["labels"])
            origin.append(np.full(len(z["labels"]), record_int_id(rec, db), dtype=np.int32))

    return {
        "X_morph": np.concatenate(morph).reshape(-1, WIN_LEN, 1).astype(np.float32),
        "X_rr": np.concatenate(rr).astype(np.float32),
        "y": np.concatenate(y).astype(np.int8),
        "records": np.concatenate(origin),
    }


def build_split(per_record_dir: str = PER_RECORD_DIR):
    assert_split_valid()
    train = stack_records(DS1, per_record_dir)
    test = stack_records(DS2, per_record_dir)
    if set(np.unique(train["records"])) & set(np.unique(test["records"])):
        raise ValueError("record bocor lintas split")
    return train, test


def split_train_val(data: dict, val_records=VAL_RECORDS):
    if not set(val_records) <= set(DS1):
        raise ValueError(f"val record di luar DS1: {sorted(set(val_records) - set(DS1))}")
    is_val = np.isin(data["records"], val_records)
    take = lambda mask: {k: v[mask] for k, v in data.items()}
    return take(~is_val), take(is_val)
