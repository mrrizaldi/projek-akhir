import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DATASETS, DS1, JITTER_MODEL, JITTER_COPIES, PER_RECORD_DIR,
    SEED, USE_RR_RATIO, WIN_PRE, WIN_POST,
)
from src.dataset import split_train_test, available_records
from src.io_mitdb import load_record
from src.preprocessing import (
    design_bandpass_sos, apply_bandpass, jitter_r, segment_beats, align_r,
    zscore_per_window,
)
from src.features_rr import (
    to_aami_class, to_binary_label, assemble_rhythm_features,
)


def valid_beat_indices(signal_len: int, r_locations: np.ndarray) -> np.ndarray:
    r = np.asarray(r_locations)
    i = np.arange(len(r))
    fits = (r - WIN_PRE >= 0) & (r + WIN_POST <= signal_len)
    ok = fits & (i >= 2)
    if USE_RR_RATIO:
        ok &= i < len(r) - 1
    return i[ok]


def process_record(record_id: str, sos, jitter=None, db: str = "mitdb") -> dict:
    signal, r, sym, _ = load_record(record_id, db=db)
    filtered = apply_bandpass(signal, sos)
    if DATASETS[db]["selaraskan"]:
        r = align_r(r, filtered)
    if jitter is not None:
        r = jitter(r)

    idx = valid_beat_indices(len(signal), r)
    windows = zscore_per_window(segment_beats(filtered, r[idx]))
    rr = assemble_rhythm_features(r, windows, idx)
    labels = np.array([to_binary_label(to_aami_class(sym[i])) for i in idx], dtype=np.int8)
    symbols = np.array([sym[i] for i in idx], dtype="<U2")

    assert len(windows) == len(rr) == len(labels) == len(symbols) == len(idx)
    assert not np.isnan(rr).any(), f"record {record_id}: NaN leaked into rr"

    return {
        "windows": windows,
        "rr": rr,
        "labels": labels,
        "symbols": symbols,
        "n_dropped": np.int32(len(r) - len(idx)),
    }


def combine(parts: list) -> dict:
    if len(parts) == 1:
        return parts[0]
    return {
        "windows": np.concatenate([b["windows"] for b in parts]),
        "rr": np.concatenate([b["rr"] for b in parts]),
        "labels": np.concatenate([b["labels"] for b in parts]),
        "symbols": np.concatenate([b["symbols"] for b in parts]),
        "n_dropped": np.int32(sum(int(b["n_dropped"]) for b in parts)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jitter", default=JITTER_MODEL,
                    choices=["none", "empiris", "seragam", "normal"])
    ap.add_argument("--copies", type=int, default=JITTER_COPIES,
                    help="jittered copies per DS1 record, ON TOP of the clean copy")
    ap.add_argument("--delta", type=int, default=0, help="for seragam/normal")
    ap.add_argument("--db", nargs="+", default=list(DATASETS),
                    choices=list(DATASETS),
                    help="databases to process; those not downloaded are skipped")
    args = ap.parse_args()

    os.makedirs(PER_RECORD_DIR, exist_ok=True)
    sos = design_bandpass_sos()
    rng = np.random.default_rng(SEED)
    ds1 = {str(r) for r in DS1}

    print(f"augmentation: {args.jitter} x{args.copies}: DS1 mitdb only")
    total_n = total_arr = total_drop = total_rec = 0
    for db in args.db:
        records = available_records(db)
        if not records:
            print(f"\n[{db}] not downloaded: skipped (make data DB={db})")
            continue
        role = "" if db == "mitdb" else (
            f"  train {len(split_train_test(records)[0])} / held-out "
            f"{len(split_train_test(records)[1])}")
        print(f"\n[{db}] {len(records)} records, {DATASETS[db]['fs']} Hz -> 360 Hz{role}")
        print(f"{'rec':>5} {'beat':>7} {'normal':>7} {'arrhythmia':>10} {'%arr':>6} {'dropped':>7}")
        for rec in records:
            n_copies = (args.copies
                         if (db == "mitdb" and rec in ds1 and args.jitter != "none")
                         else 0)
            out = combine([process_record(rec, sos, db=db)] + [
                process_record(rec, sos, db=db,
                               jitter=lambda r: jitter_r(r, args.delta, rng, args.jitter))
                for _ in range(n_copies)])
            labels = out["labels"]
            n, n_arr, n_drop = len(labels), int(labels.sum()), int(out["n_dropped"])
            np.savez_compressed(os.path.join(PER_RECORD_DIR, f"{rec}.npz"), **out)

            print(f"{rec:>5} {n:>7} {n - n_arr:>7} {n_arr:>10} "
                  f"{100 * n_arr / n:>5.1f}% {n_drop:>7}")
            total_n += n
            total_arr += n_arr
            total_drop += n_drop
            total_rec += 1

    print("-" * 44)
    print(f"{total_rec} records  {total_n} beats  "
          f"Normal {total_n - total_arr} ({100 * (total_n - total_arr) / total_n:.1f}%)  "
          f"Arrhythmia {total_arr} ({100 * total_arr / total_n:.1f}%)  dropped {total_drop}")


if __name__ == "__main__":
    main()
