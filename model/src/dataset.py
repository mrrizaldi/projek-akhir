"""dataset — Fase 3: rakit split inter-patient DS1/DS2. Walkthrough: docs/dataset-walkthrough.md"""
import os

import numpy as np

from config import DS1, DS2, PACED_EXCLUDED, PER_RECORD_DIR, VAL_RECORDS, WIN_LEN


def assert_split_valid() -> None:
    ds1, ds2, paced = set(DS1), set(DS2), set(PACED_EXCLUDED)
    if ds1 & ds2:
        raise ValueError(f"DS1 ∩ DS2 tidak kosong: {sorted(ds1 & ds2)}")
    if (ds1 | ds2) & paced:
        raise ValueError(f"record paced ikut di split: {sorted((ds1 | ds2) & paced)}")
    total = len(ds1) + len(ds2) + len(paced)
    if total != 48:
        raise ValueError(f"total record {total}, harus 48")


def stack_records(record_ids, per_record_dir: str = PER_RECORD_DIR) -> dict:
    morph, rr, y, origin = [], [], [], []
    for rec in record_ids:
        path = os.path.join(per_record_dir, f"{rec}.npz")
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} — jalankan `make prep` dulu")
        with np.load(path) as z:
            morph.append(z["windows"])
            rr.append(z["rr"])
            y.append(z["labels"])
            origin.append(np.full(len(z["labels"]), int(rec), dtype=np.int32))

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
