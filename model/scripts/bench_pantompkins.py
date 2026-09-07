"""Benchmark Pan-Tompkins: overlay R-peak anotasi vs hasil detektor + sensitivity/precision.

    python scripts/bench_pantompkins.py 100

Fungsi ini TIDAK dipakai buat segmentasi training (lihat catatan di
src/preprocessing.py) — murni ukur seberapa akurat detektor on-device sendiri,
toleransi ±150ms (PRD hal 7-9).
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FS  # noqa: E402
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import design_bandpass_sos, apply_bandpass, pan_tompkins_detect  # noqa: E402

TOLERANCE_MS = 150
PLOT_SECONDS = 10
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "artifacts", "metrics")


def match_peaks(detected: np.ndarray, reference: np.ndarray, tolerance_samples: int):
    """Pasangkan tiap anotasi ke detected terdekat dalam toleransi (greedy, 1-ke-1).

    Returns:
        tp (int), fn (int), fp (int)
    """
    used = np.zeros(len(detected), dtype=bool)
    tp = 0
    for r in reference:
        if len(detected) == 0:
            break
        diffs = np.abs(detected - r)
        diffs[used] = np.iinfo(np.int64).max
        idx = np.argmin(diffs)
        if diffs[idx] <= tolerance_samples:
            used[idx] = True
            tp += 1
    fn = len(reference) - tp
    fp = len(detected) - int(used.sum())
    return tp, fn, fp


def main(record_id: str) -> None:
    signal, r_locations, symbols, fs = load_record(record_id)
    filtered = apply_bandpass(signal, design_bandpass_sos())
    detected = pan_tompkins_detect(filtered, fs)

    tolerance_samples = round(TOLERANCE_MS / 1000 * fs)
    tp, fn, fp = match_peaks(detected, r_locations, tolerance_samples)
    sensitivity = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0

    print(f"record {record_id} — anotasi={len(r_locations)}, terdeteksi={len(detected)}")
    print(f"  TP={tp}  FN={fn}  FP={fp}")
    print(f"  sensitivity={sensitivity:.3f}  precision={precision:.3f}  "
          f"(toleransi ±{TOLERANCE_MS}ms = ±{tolerance_samples} sampel)")

    n = PLOT_SECONDS * fs
    time = np.arange(n) / fs
    ann_in = r_locations[r_locations < n]
    det_in = detected[detected < n]

    plt.figure(figsize=(14, 4))
    plt.plot(time, filtered[:n], color="#94a3b8", linewidth=0.8, label="ECG (bandpass)")
    plt.scatter(ann_in / fs, filtered[ann_in], color="#22c55e", marker="o",
                s=40, zorder=3, label="Anotasi (ground truth)")
    plt.scatter(det_in / fs, filtered[det_in], color="#ef4444", marker="x",
                s=40, zorder=3, label="Pan-Tompkins (deteksi)")

    plt.xlabel("Waktu (detik)")
    plt.ylabel("Amplitudo (mV)")
    plt.title(f"Pan-Tompkins vs anotasi — record {record_id}, {PLOT_SECONDS} detik pertama\n"
              f"Bulat hijau overlap silang merah = TP. Bulat sendiri = FN (missed). "
              f"Silang sendiri = FP (deteksi salah).")
    plt.legend()
    plt.tight_layout()

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"pantompkins_{record_id}.png")
    plt.savefig(out_path, dpi=120)
    print(f"\nPlot: {os.path.relpath(out_path)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "100")
