"""Fase 0 — loader record PhysioNet. Modul MURNI: masuk record_id, keluar array.

Tanpa kode top-level, tanpa plot, tanpa print — supaya import-safe dan bisa
di-assert tanpa menyeret pemuatan record 30 menit. Eksekusi/plot ada di
scripts/plot_fase0.py.
"""
import os

import numpy as np
import wfdb

from config import CHANNEL, DATASETS, FS, RAW_DIR, BEAT_SYMBOLS, raw_dir as _raw_dir
from src.preprocessing import resample_to_fs


def pilih_lead(record_id: str, sig_name: list, leads) -> int:
    """Indeks kanal pertama dari `leads` yang ada di record. Menolak kalau nihil.

    Menolak, tidak fallback ke kanal 0: rec 114 punya ['V5','MLII'] — fallback
    diam-diam akan membaca V5 dan tidak ada yang tahu (test_io_mitdb menjaga ini).
    """
    for lead in leads:
        if lead in sig_name:
            return sig_name.index(lead)
    raise ValueError(
        f"record {record_id}: tidak ada kanal {list(leads)}, hanya {sig_name}"
    )


def load_record(record_id: str, raw_dir: str = None, db: str = "mitdb"):
    """Baca satu record PhysioNet beranotasi-beat, diseragamkan ke FS.

    db="mitdb" (default) berperilaku PERSIS seperti sebelum Fase A: fs sudah 360
    jadi resample_to_fs() melewatkannya, dan lead-nya tetap CHANNEL = "MLII".

    Returns:
        signal (np.ndarray, [N] float32): satu kanal, laju FS, belum difilter.
        r_locations (np.ndarray, [M] int64): indeks R-peak pada laju FS.
        symbols (list[str], len M): simbol anotasi per beat (BEAT_SYMBOLS saja).
        fs (int): dijamin == FS.

    Raises:
        KeyError: db tak ada di DATASETS.
        ValueError: record tidak punya satu pun lead yang diminta, atau fs-nya
            tidak sama dengan yang dijanjikan DATASETS[db]["fs"].
        NotImplementedError: db butuh resample tapi resample_to_fs masih stub.
    """
    spec = DATASETS[db]
    path = os.path.join(_raw_dir(db) if raw_dir is None else raw_dir, str(record_id))
    record = wfdb.rdrecord(path)
    annotation = wfdb.rdann(path, "atr")

    # fs dicek terhadap JANJI di DATASETS, bukan terhadap FS: yang salah kalau
    # tidak cocok adalah tabel config (atau record rusak), dan itu harus berisik
    # sebelum resample menutupinya.
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
