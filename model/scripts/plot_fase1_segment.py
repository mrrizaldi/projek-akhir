"""Fase 1 (segmentasi + z-score) — verifikasi segment_beats() & zscore_per_window().

    python scripts/plot_fase1_segment.py 100

DoD: tiap window WIN_LEN sampel persis, R-peak di posisi WIN_PRE (garis tengah
merah). Sebelum z-score amplitudo antar-beat beda-beda; sesudah, semua window
berada di skala sebanding (mean~0, std~1) — itu yang mau dicek mata.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WIN_PRE, WIN_LEN  # noqa: E402
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import (  # noqa: E402
    design_bandpass_sos, apply_bandpass, segment_beats, zscore_per_window,
)

N_SHOW = 8
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "artifacts", "metrics")


def main(record_id: str) -> None:
    signal, r_locations, symbols, fs = load_record(record_id)
    filtered = apply_bandpass(signal, design_bandpass_sos())

    windows = segment_beats(filtered, r_locations)
    n_dropped = len(r_locations) - len(windows)
    z_windows = zscore_per_window(windows)

    print(f"record {record_id} — anotasi={len(r_locations)}, window valid={len(windows)}, "
          f"dibuang={n_dropped}")
    print(f"  shape windows={windows.shape}, shape z-score={z_windows.shape}")
    print(f"  cek panjang: semua == WIN_LEN({WIN_LEN})? "
          f"{bool(np.all(np.array([len(w) for w in windows]) == WIN_LEN))}")

    time = (np.arange(WIN_LEN) - WIN_PRE) / fs
    n_show = min(N_SHOW, len(windows))

    fig, (ax_raw, ax_z) = plt.subplots(1, 2, figsize=(14, 4.5))

    for w in windows[:n_show]:
        ax_raw.plot(time, w, linewidth=0.8, alpha=0.7)
    ax_raw.axvline(0, color="#ef4444", linestyle="--", linewidth=1, label="R-peak")
    ax_raw.set_title(f"Sebelum z-score ({n_show} window pertama)")
    ax_raw.set_xlabel("Waktu relatif R-peak (detik)")
    ax_raw.set_ylabel("Amplitudo (mV)")
    ax_raw.legend()

    for w in z_windows[:n_show]:
        ax_z.plot(time, w, linewidth=0.8, alpha=0.7)
    ax_z.axvline(0, color="#ef4444", linestyle="--", linewidth=1, label="R-peak")
    ax_z.set_title(f"Sesudah z-score per-window ({n_show} window pertama)")
    ax_z.set_xlabel("Waktu relatif R-peak (detik)")
    ax_z.set_ylabel("Amplitudo ternormalisasi")
    ax_z.legend()

    fig.suptitle(f"Fase 1 segmentasi — record {record_id}, WIN_PRE={WIN_PRE}, WIN_LEN={WIN_LEN}")
    fig.tight_layout()

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"fase1_segment_{record_id}.png")
    fig.savefig(out_path, dpi=120)
    print(f"\nPlot: {os.path.relpath(out_path)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "100")
