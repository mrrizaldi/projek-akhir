"""Fase 2 — jalankan Fase 0+1+2 untuk tiap record, simpan .npz per record.

    make prep        (atau: python scripts/prep_beats.py)

Keluaran: data/processed/per_record/<rec>.npz dengan key
    windows   float32 [K,250]   window ter-z-score
    rr        float32 [K,3]     RR_prev, RR_ratio, dRR
    labels    int8    [K]       0=Normal, 1=Aritmia
    symbols   <U2     [K]       simbol MIT-BIH asli (audit error Fase 6)
    n_dropped int32   skalar    beat dibuang (tepi rekaman / tanpa RR_prev-dRR)

Penjelasan alur & alasan: docs/features-rr-walkthrough.md §3.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PACED_EXCLUDED, PER_RECORD_DIR, RAW_DIR, WIN_PRE, WIN_POST  # noqa: E402
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import (  # noqa: E402
    design_bandpass_sos, apply_bandpass, segment_beats, zscore_per_window,
)
from src.features_rr import (  # noqa: E402
    to_aami_class, to_binary_label, compute_rr_features,
)


def valid_beat_indices(signal_len: int, r_locations: np.ndarray) -> np.ndarray:
    """Indeks beat yang lolos SEMUA syarat — satu-satunya sumber kebenaran alignment.

    Irisan tiga syarat: window muat di sinyal, punya RR_prev (i>=1),
    punya dRR (i>=2). Sejajarkan lewat indeks, jangan lewat panjang array.
    """
    r = np.asarray(r_locations)
    i = np.arange(len(r))
    fits = (r - WIN_PRE >= 0) & (r + WIN_POST <= signal_len)
    return i[fits & (i >= 2)]


def process_record(record_id: str, sos) -> dict:
    """Satu record → dict siap disimpan. Murni, tidak menulis file."""
    signal, r, sym, _ = load_record(record_id)
    filtered = apply_bandpass(signal, sos)

    idx = valid_beat_indices(len(signal), r)
    windows = zscore_per_window(segment_beats(filtered, r[idx]))
    rr = compute_rr_features(r)[idx]
    labels = np.array([to_binary_label(to_aami_class(sym[i])) for i in idx], dtype=np.int8)
    symbols = np.array([sym[i] for i in idx], dtype="<U2")

    assert len(windows) == len(rr) == len(labels) == len(symbols) == len(idx)
    assert not np.isnan(rr).any(), f"record {record_id}: NaN lolos ke rr"

    return {
        "windows": windows,
        "rr": rr,
        "labels": labels,
        "symbols": symbols,
        "n_dropped": np.int32(len(r) - len(idx)),
    }


def available_records(raw_dir: str = RAW_DIR) -> list:
    """Record id dari file .hea di raw_dir, tanpa yang di PACED_EXCLUDED."""
    excluded = {str(x) for x in PACED_EXCLUDED}
    ids = sorted(f[:-4] for f in os.listdir(raw_dir) if f.endswith(".hea"))
    return [i for i in ids if i not in excluded]


def main() -> None:
    os.makedirs(PER_RECORD_DIR, exist_ok=True)
    sos = design_bandpass_sos()
    records = available_records()

    total_n = total_arr = total_drop = 0
    print(f"{'rec':>5} {'beat':>7} {'normal':>7} {'aritmia':>8} {'%arit':>6} {'buang':>6}")
    for rec in records:
        out = process_record(rec, sos)
        labels = out["labels"]
        n, n_arr, n_drop = len(labels), int(labels.sum()), int(out["n_dropped"])
        np.savez_compressed(os.path.join(PER_RECORD_DIR, f"{rec}.npz"), **out)

        print(f"{rec:>5} {n:>7} {n - n_arr:>7} {n_arr:>8} {100 * n_arr / n:>5.1f}% {n_drop:>6}")
        total_n += n
        total_arr += n_arr
        total_drop += n_drop

    print("-" * 44)
    print(f"{len(records)} record  {total_n} beat  "
          f"Normal {total_n - total_arr} ({100 * (total_n - total_arr) / total_n:.1f}%)  "
          f"Aritmia {total_arr} ({100 * total_arr / total_n:.1f}%)  buang {total_drop}")


if __name__ == "__main__":
    main()
