import os

import numpy as np
import wfdb

from config import CHANNEL, DATASETS, FS, RAW_DIR, BEAT_SYMBOLS, raw_dir as _raw_dir
from src.preprocessing import resample_to_fs


def pilih_lead(record_id: str, sig_name: list, leads) -> int:
    for lead in leads:
        if lead in sig_name:
            return sig_name.index(lead)
    raise ValueError(
        f"record {record_id}: tidak ada kanal {list(leads)}, hanya {sig_name}"
    )


def load_record(record_id: str, raw_dir: str = None, db: str = "mitdb"):
    spec = DATASETS[db]
    path = os.path.join(_raw_dir(db) if raw_dir is None else raw_dir, str(record_id))
    record = wfdb.rdrecord(path)
    annotation = wfdb.rdann(path, "atr")

    if record.fs != spec["fs"]:
        raise ValueError(
            f"record {record_id} ({db}): fs={record.fs}, DATASETS menjanjikan {spec['fs']}"
        )

    channel = pilih_lead(record_id, record.sig_name, spec["leads"])
    signal = record.p_signal[:, channel].astype(np.float32)

    symbols = np.asarray(annotation.symbol)
    is_beat = np.isin(symbols, list(BEAT_SYMBOLS))
    r = annotation.sample[is_beat]

    if record.fs != FS:
        signal, r = resample_to_fs(signal, r, record.fs, FS)

    return signal, np.asarray(r, dtype=np.int64), symbols[is_beat].tolist(), FS
