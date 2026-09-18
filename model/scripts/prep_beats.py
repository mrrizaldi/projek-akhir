"""Fase 2 — jalankan Fase 0+1+2 untuk tiap record, simpan .npz per record.

    make prep        (atau: python scripts/prep_beats.py)

Sejak 18 Sep 2026 record DS1 ditumpuk dengan SALINAN ber-jitter (augmentasi
ketahanan segmentasi, Fase 6c). DS2 tidak pernah dijitter — dia tolok ukur
jujur. Matikan dengan `--jitter none` kalau ingin data Fase 2 yang asli.

Keluaran: data/processed/per_record/<rec>.npz dengan key
    windows   float32 [K,250]   window ter-z-score
    rr        float32 [K,3]     RR_prev, RR_ratio, dRR
    labels    int8    [K]       0=Normal, 1=Aritmia
    symbols   <U2     [K]       simbol MIT-BIH asli (audit error Fase 6)
    n_dropped int32   skalar    beat dibuang (tepi rekaman / tanpa RR_prev-dRR)

Penjelasan alur & alasan: docs/features-rr-walkthrough.md §3.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (  # noqa: E402
    DS1, JITTER_MODEL, JITTER_SALINAN, PACED_EXCLUDED, PER_RECORD_DIR, RAW_DIR,
    SEED, WIN_PRE, WIN_POST,
)
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import (  # noqa: E402
    design_bandpass_sos, apply_bandpass, jitter_r, segment_beats, zscore_per_window,
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


def process_record(record_id: str, sos, jitter=None) -> dict:
    """Satu record → dict siap disimpan. Murni, tidak menulis file.

    jitter: callable r -> r_tergeser, atau None. Dipakai untuk eksperimen
    ketahanan terhadap error segmentasi (docs/2026-09-18-robustness-plan.md).
    Posisi yang sudah digeser dipakai SELURUHNYA — window dan fitur RR — karena
    detektor yang meleset merusak dua-duanya sekaligus. Label tetap dari indeks
    anotasi asli: yang bergeser cuma tempat kita memotong, bukan diagnosisnya.
    """
    signal, r, sym, _ = load_record(record_id)
    filtered = apply_bandpass(signal, sos)
    if jitter is not None:
        r = jitter(r)

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


def gabung(bagian: list) -> dict:
    """Tumpuk beberapa hasil process_record dari SATU record jadi satu npz."""
    if len(bagian) == 1:
        return bagian[0]
    return {
        "windows": np.concatenate([b["windows"] for b in bagian]),
        "rr": np.concatenate([b["rr"] for b in bagian]),
        "labels": np.concatenate([b["labels"] for b in bagian]),
        "symbols": np.concatenate([b["symbols"] for b in bagian]),
        "n_dropped": np.int32(sum(int(b["n_dropped"]) for b in bagian)),
    }


def available_records(raw_dir: str = RAW_DIR) -> list:
    """Record id dari file .hea di raw_dir, tanpa yang di PACED_EXCLUDED."""
    excluded = {str(x) for x in PACED_EXCLUDED}
    ids = sorted(f[:-4] for f in os.listdir(raw_dir) if f.endswith(".hea"))
    return [i for i in ids if i not in excluded]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jitter", default=JITTER_MODEL,
                    choices=["none", "empiris", "seragam", "normal"])
    ap.add_argument("--salinan", type=int, default=JITTER_SALINAN,
                    help="tiruan ber-jitter per record DS1, DI ATAS salinan bersih")
    ap.add_argument("--delta", type=int, default=0, help="untuk seragam/normal")
    args = ap.parse_args()

    os.makedirs(PER_RECORD_DIR, exist_ok=True)
    sos = design_bandpass_sos()
    records = available_records()
    rng = np.random.default_rng(SEED)
    ds1 = {str(r) for r in DS1}

    print(f"augmentasi: {args.jitter} x{args.salinan} — DS1 saja, DS2 tetap bersih")
    total_n = total_arr = total_drop = 0
    print(f"{'rec':>5} {'beat':>7} {'normal':>7} {'aritmia':>8} {'%arit':>6} {'buang':>6}")
    for rec in records:
        n_salinan = args.salinan if (rec in ds1 and args.jitter != "none") else 0
        out = gabung([process_record(rec, sos)] + [
            process_record(rec, sos,
                           jitter=lambda r: jitter_r(r, args.delta, rng, args.jitter))
            for _ in range(n_salinan)])
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
