import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import GROUP_DELAY_SAMPLES, METRICS_DIR, PT_DETECTOR_OFFSET, PT_REFINE_WIN
from src.preprocessing import align_r
from scripts.analyze_recording import analyze_segment, muat, band_energy

PLOT_WINDOW_S = 60
SEARCH_STEP_S = 5
SECONDS_PER_ROW = 10
BPM_PLAUSIBLE_MIN, BPM_PLAUSIBLE_MAX = 30, 200
ECG_BAND_HZ = (0.5, 40)
MUSCLE_BAND_MIN_HZ = 60
ROW_HEIGHT_IN, WIDTH_IN, DPI = 1.6, 16, 110


def r_peaks(h):
    r = h["r"] - PT_DETECTOR_OFFSET
    r = r[r >= 0]
    return align_r(r, h["filtered"], PT_REFINE_WIN) + GROUP_DELAY_SAMPLES


def window_scores(x, r, fs, mulai, n):
    inside = r[(r >= mulai) & (r < mulai + n)]
    bpm = 60.0 * fs / np.diff(inside) if len(inside) > 2 else np.array([])
    odd_rr = int(((bpm < BPM_PLAUSIBLE_MIN) | (bpm > BPM_PLAUSIBLE_MAX)).sum()) if len(bpm) else n
    potong = x[mulai:mulai + n]
    muscle = band_energy(potong, fs, MUSCLE_BAND_MIN_HZ, fs / 2) / band_energy(potong, fs, *ECG_BAND_HZ)
    return odd_rr, muscle


def select_window(hasil, fs, n, start_s):
    calon = []
    for k, h in enumerate(hasil):
        if h["n"] < n:
            continue
        r = r_peaks(h)
        awal = [int(start_s * fs)] if start_s is not None else range(0, h["n"] - n + 1, SEARCH_STEP_S * fs)
        for mulai in awal:
            if mulai + n <= h["n"]:
                calon.append((*window_scores(h["x"], r, fs, mulai, n), k, mulai, r))
    if not calon:
        sys.exit(f"No segment of {n / fs:.0f} seconds.")
    return min(calon, key=lambda c: (c[0], c[1]))


def draw_rows(h, r, fs, mulai, n, judul, tujuan):
    baris = n // (SECONDS_PER_ROW * fs)
    fig, ax = plt.subplots(baris + 1, 1, figsize=(WIDTH_IN, ROW_HEIGHT_IN * (baris + 1)))
    y = h["filtered"]
    lim = np.percentile(np.abs(y[mulai:mulai + n]), 99.9) * 1.1
    lebar = SECONDS_PER_ROW * fs
    for i in range(baris):
        a, b = mulai + i * lebar, mulai + (i + 1) * lebar
        t = np.arange(a, b) / fs
        ax[i].plot(t, y[a:b], lw=0.6, color="tab:blue")
        rr = r[(r >= a) & (r < b)]
        ax[i].plot(rr / fs, y[rr], "v", ms=3, color="tab:red")
        ax[i].set_xlim(a / fs, b / fs)
        ax[i].set_ylim(-lim, lim)
        ax[i].set_yticks([])
        ax[i].grid(True, which="both", alpha=0.3)
    ax[baris - 1].set_xlabel("detik sejak mulai rekam")
    rw = r[(r >= mulai) & (r < mulai + n)]
    bpm = 60.0 * fs / np.diff(rw)
    ax[-1].plot(rw[1:] / fs, bpm, ".-", lw=0.8)
    ax[-1].set_ylabel("HR (bpm)")
    ax[-1].set_xlim(mulai / fs, (mulai + n) / fs)
    ax[-1].grid(True, alpha=0.3)
    fig.suptitle(judul)
    fig.tight_layout()
    fig.savefig(tujuan, dpi=DPI)
    return bpm


def main() -> None:
    p = argparse.ArgumentParser(description="ECG plot of one window (default: best 60 seconds) from a board recording.")
    p.add_argument("file", help="data/recordings/<name>.csv")
    p.add_argument("--start", type=float, help="window start in seconds; without it the best window is chosen")
    p.add_argument("--duration", type=int, default=PLOT_WINDOW_S, help="window length in seconds")
    arg = p.parse_args()

    segmen, fs, _ = muat(arg.file)
    hasil = [analyze_segment(m, fs) for m in segmen]
    n = arg.duration * fs
    odd_rr, muscle, k, mulai, r = select_window(hasil, fs, n, arg.start)

    nama = os.path.splitext(os.path.basename(arg.file))[0]
    folder = os.path.join(METRICS_DIR, "akuisisi")
    os.makedirs(folder, exist_ok=True)
    tujuan = os.path.join(folder, f"rekaman_{nama}_detik-{mulai // fs:03d}.png")
    segment_text = f", segmen {k + 1}" if len(segmen) > 1 else ""
    judul = (f"{nama}{segment_text}: detik {mulai // fs}-{(mulai + n) // fs} "
             f"(bandpass 0,5-40 Hz, ▼ = R terdeteksi)")
    bpm = draw_rows(hasil[k], r, fs, mulai, n, judul, tujuan)
    print(f"window seconds {mulai // fs}-{(mulai + n) // fs}{segment_text}: "
          f"odd RR {odd_rr}, noise >{MUSCLE_BAND_MIN_HZ} Hz {100 * muscle:.1f}% of ECG band, "
          f"HR median {np.median(bpm):.0f} bpm ({bpm.min():.0f}-{bpm.max():.0f}), {len(bpm) + 1} R")
    print(tujuan)


if __name__ == "__main__":
    main()
