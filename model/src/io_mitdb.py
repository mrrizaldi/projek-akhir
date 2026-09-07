"""Fase 0 — loader MIT-BIH. Modul MURNI: masuk record_id, keluar array.

Tanpa kode top-level, tanpa plot, tanpa print — supaya import-safe dan bisa
di-assert tanpa menyeret pemuatan record 30 menit. Eksekusi/plot ada di
scripts/plot_fase0.py.
"""
import os

import numpy as np
import wfdb

from config import CHANNEL, FS, RAW_DIR, BEAT_SYMBOLS


def load_record(record_id: str, raw_dir: str = RAW_DIR):
    """Baca satu record MIT-BIH.

    Returns:
        signal (np.ndarray, [N] float32): sinyal kanal MLII.
        r_locations (np.ndarray, [M] int64): indeks sampel R-peak (anotasi).
        symbols (list[str], len M): simbol anotasi per beat.
        fs (int): sampling frequency (dijamin == FS).

    Raises:
        ValueError: record tidak punya kanal CHANNEL, atau fs != FS.
    """
    path = os.path.join(raw_dir, str(record_id))
    record = wfdb.rdrecord(path)
    annotation = wfdb.rdann(path, "atr")

    if record.fs != FS:
        raise ValueError(f"record {record_id}: fs={record.fs}, harus {FS}")

    if CHANNEL not in record.sig_name:
        raise ValueError(
            f"record {record_id}: kanal {CHANNEL} tidak ada, hanya {record.sig_name}"
        )

    channel = record.sig_name.index(CHANNEL)
    signal = record.p_signal[:, channel].astype(np.float32)

    symbols = np.asarray(annotation.symbol)
    is_beat = np.isin(symbols, list(BEAT_SYMBOLS))

    return signal, annotation.sample[is_beat], symbols[is_beat].tolist(), record.fs
