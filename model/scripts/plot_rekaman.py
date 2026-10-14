import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import GROUP_DELAY_SAMPLES, METRICS_DIR, PT_DETECTOR_OFFSET, PT_REFINE_WIN
from src.preprocessing import selaraskan_r
from scripts.analyze_recording import analisis_segmen, muat, pita_energi

DURASI_S = 60
LANGKAH_CARI_S = 5
DETIK_PER_BARIS = 10
BPM_WAJAR_MIN, BPM_WAJAR_MAKS = 30, 200
PITA_EKG_HZ = (0.5, 40)
PITA_OTOT_MIN_HZ = 60
TINGGI_BARIS_IN, LEBAR_IN, DPI = 1.6, 16, 110


def puncak_r(h):
    r = h["r"] - PT_DETECTOR_OFFSET
    r = r[r >= 0]
    return selaraskan_r(r, h["filtered"], PT_REFINE_WIN) + GROUP_DELAY_SAMPLES


def nilai_jendela(x, r, fs, mulai, n):
    di_dalam = r[(r >= mulai) & (r < mulai + n)]
    bpm = 60.0 * fs / np.diff(di_dalam) if len(di_dalam) > 2 else np.array([])
    aneh = int(((bpm < BPM_WAJAR_MIN) | (bpm > BPM_WAJAR_MAKS)).sum()) if len(bpm) else n
    potong = x[mulai:mulai + n]
    otot = pita_energi(potong, fs, PITA_OTOT_MIN_HZ, fs / 2) / pita_energi(potong, fs, *PITA_EKG_HZ)
    return aneh, otot


def pilih_jendela(hasil, fs, n, mulai_s):
    calon = []
    for k, h in enumerate(hasil):
        if h["n"] < n:
            continue
        r = puncak_r(h)
        awal = [int(mulai_s * fs)] if mulai_s is not None else range(0, h["n"] - n + 1, LANGKAH_CARI_S * fs)
        for mulai in awal:
            if mulai + n <= h["n"]:
                calon.append((*nilai_jendela(h["x"], r, fs, mulai, n), k, mulai, r))
    if not calon:
        sys.exit(f"Tidak ada segmen sepanjang {n / fs:.0f} detik.")
    return min(calon, key=lambda c: (c[0], c[1]))


def gambar(h, r, fs, mulai, n, judul, tujuan):
    baris = n // (DETIK_PER_BARIS * fs)
    fig, ax = plt.subplots(baris + 1, 1, figsize=(LEBAR_IN, TINGGI_BARIS_IN * (baris + 1)))
    y = h["filtered"]
    lim = np.percentile(np.abs(y[mulai:mulai + n]), 99.9) * 1.1
    lebar = DETIK_PER_BARIS * fs
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
    p = argparse.ArgumentParser(description="Grafik EKG satu jendela (bawaan: 60 detik terbaik) dari rekaman board.")
    p.add_argument("berkas", help="data/recordings/<nama>.csv")
    p.add_argument("--mulai", type=float, help="detik awal jendela; tanpa ini dipilih jendela terbaik")
    p.add_argument("--durasi", type=int, default=DURASI_S, help="panjang jendela dalam detik")
    arg = p.parse_args()

    segmen, fs, _ = muat(arg.berkas)
    hasil = [analisis_segmen(m, fs) for m in segmen]
    n = arg.durasi * fs
    aneh, otot, k, mulai, r = pilih_jendela(hasil, fs, n, arg.mulai)

    nama = os.path.splitext(os.path.basename(arg.berkas))[0]
    folder = os.path.join(METRICS_DIR, "akuisisi")
    os.makedirs(folder, exist_ok=True)
    tujuan = os.path.join(folder, f"rekaman_{nama}_detik-{mulai // fs:03d}.png")
    segmen_teks = f", segmen {k + 1}" if len(segmen) > 1 else ""
    judul = (f"{nama}{segmen_teks}: detik {mulai // fs}-{(mulai + n) // fs} "
             f"(bandpass 0,5-40 Hz, ▼ = R terdeteksi)")
    bpm = gambar(hasil[k], r, fs, mulai, n, judul, tujuan)
    print(f"jendela detik {mulai // fs}-{(mulai + n) // fs}{segmen_teks}: "
          f"RR tak wajar {aneh}, derau >{PITA_OTOT_MIN_HZ} Hz {100 * otot:.1f}% pita EKG, "
          f"HR median {np.median(bpm):.0f} bpm ({bpm.min():.0f}-{bpm.max():.0f}), {len(bpm) + 1} R")
    print(tujuan)


if __name__ == "__main__":
    main()
