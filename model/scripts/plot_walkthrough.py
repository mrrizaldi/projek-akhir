"""Gambar pendamping docs/preprocessing-walkthrough.md — 5 detik record 100.

    python scripts/plot_walkthrough.py 100

Keluar 2 file di artifacts/metrics/:
    walkthrough_pipeline_<rec>.png  — raw -> bandpass -> segmentasi -> z-score
    walkthrough_pt_<rec>.png        — 5 tahap kaskade Pan-Tompkins + threshold
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (  # noqa: E402
    BANDPASS_LOW, BANDPASS_HIGH, PT_BAND_LOW, PT_BAND_HIGH,
    PT_MWI_WINDOW_MS, PT_REFRACTORY_MS, WIN_PRE, WIN_LEN,
)
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import (  # noqa: E402
    design_bandpass_sos, apply_bandpass, segment_beats, zscore_per_window,
    _pt_bandpass, _pt_derivative, _pt_square, _pt_moving_window_integration,
    _pt_adaptive_threshold_detect,
)

SECONDS = 5
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "artifacts", "metrics")


def main(record_id: str) -> None:
    signal, r_locations, symbols, fs = load_record(record_id)
    n = SECONDS * fs
    t = np.arange(n) / fs

    filtered = apply_bandpass(signal, design_bandpass_sos())

    # --- Gambar 1: jalur training (raw -> filter -> segmen -> z-score) ---
    windows = segment_beats(filtered, r_locations)
    z = zscore_per_window(windows)
    tw = (np.arange(WIN_LEN) - WIN_PRE) / fs
    r_in = r_locations[r_locations < n]

    fig, ax = plt.subplots(4, 1, figsize=(13, 11))

    ax[0].plot(t, signal[:n], color="#94a3b8", lw=0.9)
    ax[0].set_title(f"1. Raw MLII — record {record_id}, {SECONDS} detik "
                    f"(drift baseline + noise masih ada)")

    ax[1].plot(t, filtered[:n], color="#2563eb", lw=0.9)
    ax[1].scatter(r_in / fs, filtered[r_in], color="#22c55e", s=25, zorder=3,
                  label="R-peak anotasi")
    for r in r_in:
        ax[1].axvspan((r - WIN_PRE) / fs, (r + WIN_LEN - WIN_PRE) / fs,
                      color="#f59e0b", alpha=0.12)
    ax[1].set_title(f"2. Bandpass kausal {BANDPASS_LOW}-{BANDPASS_HIGH} Hz (sosfilt) "
                    f"+ jendela segmentasi [R-{WIN_PRE}, R+{WIN_LEN - WIN_PRE})")
    ax[1].legend(loc="upper right")

    n_show = min(6, len(windows))
    for w in windows[:n_show]:
        ax[2].plot(tw, w, lw=0.9, alpha=0.8)
    ax[2].axvline(0, color="#ef4444", ls="--", lw=1)
    ax[2].set_title(f"3. Hasil segment_beats() — {n_show} window pertama, "
                    f"amplitudo masih beda-beda")
    ax[2].set_xlabel("Waktu relatif R-peak (detik)")

    for w in z[:n_show]:
        ax[3].plot(tw, w, lw=0.9, alpha=0.8)
    ax[3].axvline(0, color="#ef4444", ls="--", lw=1)
    ax[3].set_title("4. Sesudah zscore_per_window() — mean~0, std~1 per window")
    ax[3].set_xlabel("Waktu relatif R-peak (detik)")

    for a in ax[:2]:
        a.set_xlim(0, SECONDS)
        a.set_xlabel("Waktu (detik)")
        a.set_ylabel("mV")
    ax[2].set_ylabel("mV")
    ax[3].set_ylabel("z")
    fig.tight_layout()
    p1 = os.path.join(OUT_DIR, f"walkthrough_pipeline_{record_id}.png")
    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(p1, dpi=120)

    # --- Gambar 2: kaskade Pan-Tompkins ---
    qrs = _pt_bandpass(filtered, fs)
    deriv = _pt_derivative(qrs, fs)
    sq = _pt_square(deriv)
    mwi = _pt_moving_window_integration(sq, fs)
    peaks = _pt_adaptive_threshold_detect(mwi, fs)
    peaks_in = peaks[peaks < n]

    stages = [
        (filtered, f"a. Input: bandpass {BANDPASS_LOW}-{BANDPASS_HIGH} Hz", "#2563eb"),
        (qrs, f"b. _pt_bandpass — {PT_BAND_LOW}-{PT_BAND_HIGH} Hz, tonjolkan QRS", "#0ea5e9"),
        (deriv, "c. _pt_derivative — kernel [1,2,0,-2,-1]/(8T), ukur kemiringan", "#8b5cf6"),
        (sq, "d. _pt_square — semua positif, lonjakan diperbesar", "#ec4899"),
        (mwi, f"e. _pt_moving_window_integration — rata-rata {PT_MWI_WINDOW_MS} ms", "#f59e0b"),
    ]

    fig2, ax2 = plt.subplots(len(stages) + 1, 1, figsize=(13, 13), sharex=True)
    for a, (x, title, c) in zip(ax2, stages):
        a.plot(t, x[:n], color=c, lw=0.9)
        a.set_title(title, fontsize=10)

    ax2[-1].plot(t, mwi[:n], color="#f59e0b", lw=0.9, label="MWI")
    ax2[-1].scatter(peaks_in / fs, mwi[peaks_in], color="#ef4444", marker="x", s=50,
                    zorder=3, label="R-peak terdeteksi")
    ax2[-1].scatter(r_in / fs, np.zeros(len(r_in)), color="#22c55e", marker="o", s=25,
                    zorder=3, label="R-peak anotasi")
    ax2[-1].set_title(f"f. _pt_adaptive_threshold_detect — threshold adaptif + "
                      f"refraktori {PT_REFRACTORY_MS} ms", fontsize=10)
    ax2[-1].set_xlabel("Waktu (detik)")
    ax2[-1].legend(loc="upper right", fontsize=8)
    ax2[0].set_xlim(0, SECONDS)

    fig2.suptitle(f"Kaskade Pan-Tompkins — record {record_id}, {SECONDS} detik pertama")
    fig2.tight_layout()
    p2 = os.path.join(OUT_DIR, f"walkthrough_pt_{record_id}.png")
    fig2.savefig(p2, dpi=120)

    print(f"anotasi={len(r_locations)} beat, window valid={len(windows)}, "
          f"dibuang={len(r_locations) - len(windows)}")
    print(f"5 detik pertama: anotasi={len(r_in)}, PT deteksi={len(peaks_in)}")
    print(f"raw     mean={signal.mean():+.4f} std={signal.std():.4f}")
    print(f"filter  mean={filtered.mean():+.4f} std={filtered.std():.4f}")
    print(f"zscore  mean={z.mean():+.4f} std={z.std():.4f}")
    print(f"\nPlot: {os.path.relpath(p1)}\n      {os.path.relpath(p2)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "100")
