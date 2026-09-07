"""Fase 0 — verifikasi loader: overlay R-peak anotasi di atas sinyal.

    python scripts/plot_fase0.py 100

DoD Fase 0 (PRD): garis R-peak mendarat PAS di puncak R. Kalau meleset →
loader/anotasi salah baca (cek kanal MLII bukan selalu index 0).
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ponytail: shim 1 baris supaya `import config` jalan saat dipanggil sebagai
# script (sys.path[0] = scripts/, bukan model/). Kalau sudah 3 script butuh ini,
# baru ekstrak ke modul bootstrap bersama.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FS, NORMAL_SYMBOLS  # noqa: E402
from src.io_mitdb import load_record  # noqa: E402

PLOT_SECONDS = 10
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "artifacts", "metrics")


def main(record_id: str) -> None:
    signal, r_locations, symbols, fs = load_record(record_id)

    print(f"record {record_id}")
    print(f"  panjang sinyal : {len(signal)} sampel "
          f"({len(signal) / fs / 60:.1f} menit)")
    print(f"  R-peak (beat)  : {len(r_locations)}")
    print(f"  fs             : {fs} Hz")
    print(f"  simbol unik    : {sorted(set(symbols))}")

    n = PLOT_SECONDS * fs
    time = np.arange(n) / fs
    in_window = r_locations < n

    plt.figure(figsize=(14, 4))
    plt.plot(time, signal[:n], color="#2563eb", linewidth=0.8,
             label=f"ECG (MLII) — record {record_id}")
    for r, sym in zip(r_locations[in_window], np.asarray(symbols)[in_window]):
        color = "#22c55e" if sym in NORMAL_SYMBOLS else "#ef4444"
        plt.axvline(x=r / fs, color=color, alpha=0.4, linewidth=0.8)
        plt.text(r / fs, signal[r] + 0.05, sym, fontsize=6, color=color,
                 ha="center", va="bottom")

    plt.xlabel("Waktu (detik)")
    plt.ylabel("Amplitudo (mV)")
    plt.title(f"Fase 0 — record {record_id}, {PLOT_SECONDS} detik pertama\n"
              f"Hijau = N, Merah = non-N (anotasi non-beat sudah dibuang)")
    plt.legend()
    plt.tight_layout()

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"fase0_{record_id}.png")
    plt.savefig(out_path, dpi=120)
    print(f"\nPlot: {os.path.relpath(out_path)}")
    print("Cek mata: garis vertikal harus mendarat pas di puncak R.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "100")
