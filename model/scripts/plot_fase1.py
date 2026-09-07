"""Fase 1 — verifikasi filter: overlay sinyal mentah vs hasil bandpass kausal.

    python scripts/plot_fase1.py 100

DoD Fase 1: bandingkan mata (drift baseline hilang, noise tinggi teredam) dan
angka (mean/std sebelum vs sesudah) untuk paham efek `sosfilt` + koefisien
Butterworth dari config.py.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import welch, spectrogram

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BANDPASS_LOW, BANDPASS_HIGH, BANDPASS_ORDER  # noqa: E402
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import design_bandpass_sos, apply_bandpass  # noqa: E402

PLOT_SECONDS = 3
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "artifacts", "metrics")


def describe(label: str, x: np.ndarray) -> None:
    print(f"  {label:<10} mean={x.mean():+.4f}  std={x.std():.4f}  "
          f"min={x.min():+.4f}  max={x.max():+.4f}")


def main(record_id: str) -> None:
    signal, r_locations, symbols, fs = load_record(record_id)
    sos = design_bandpass_sos()
    filtered = apply_bandpass(signal, sos)

    print(f"record {record_id} — bandpass {BANDPASS_LOW}-{BANDPASS_HIGH} Hz, "
          f"orde {BANDPASS_ORDER}, fs {fs}")
    describe("raw", signal)
    describe("filtered", filtered)

    n = PLOT_SECONDS * fs
    time = np.arange(n) / fs

    # PSD pakai jendela sama (PLOT_SECONDS) dengan panel waktu & spectrogram —
    # supaya ketiga panel merujuk rentang waktu yang sama persis.
    freq_raw, psd_raw = welch(signal[:n], fs=fs, nperseg=min(256, n))
    freq_filt, psd_filt = welch(filtered[:n], fs=fs, nperseg=min(256, n))

    # Spectrogram (STFT) raw, jendela sama (3 detik) & sharex sama panel waktu —
    # supaya "ledakan" energi tinggi di bawah bisa dicocokkan langsung ke QRS di atas.
    freq_spec, t_spec, sxx = spectrogram(signal[:n], fs=fs, nperseg=64, noverlap=48)

    fig, (ax_time, ax_spec, ax_freq) = plt.subplots(
        3, 1, figsize=(14, 12), gridspec_kw={"height_ratios": [1, 1, 1]})

    ax_time.plot(time, signal[:n], color="#94a3b8", linewidth=0.8, label="Sebelum (raw)")
    ax_time.plot(time, filtered[:n], color="#2563eb", linewidth=0.9, label="Sesudah (bandpass)")
    ax_time.set_title(f"Domain waktu — record {record_id}")
    ax_time.set_xlabel("Waktu (detik)")
    ax_time.set_ylabel("Amplitudo (mV)")
    ax_time.set_xlim(0, PLOT_SECONDS)
    ax_time.legend()

    pcm = ax_spec.pcolormesh(t_spec, freq_spec, 10 * np.log10(sxx + 1e-12),
                              shading="gouraud", cmap="magma")
    ax_spec.set_ylim(0, 60)
    ax_spec.set_title("Spectrogram (raw) — waktu vs frekuensi, warna terang = energi tinggi")
    ax_spec.set_xlabel("Waktu (detik)")
    ax_spec.set_ylabel("Frekuensi (Hz)")
    fig.colorbar(pcm, ax=ax_spec, label="dB")

    ax_freq.semilogy(freq_raw, psd_raw, color="#94a3b8", linewidth=1, label="Sebelum (raw)")
    ax_freq.semilogy(freq_filt, psd_filt, color="#2563eb", linewidth=1, label="Sesudah (bandpass)")
    ax_freq.axvline(BANDPASS_LOW, color="#22c55e", linestyle="--", linewidth=1,
                     label=f"cutoff {BANDPASS_LOW}-{BANDPASS_HIGH} Hz")
    ax_freq.axvline(BANDPASS_HIGH, color="#22c55e", linestyle="--", linewidth=1)
    ax_freq.set_xlim(0, 60)
    ax_freq.set_title(f"Domain frekuensi (PSD, Welch, {PLOT_SECONDS} detik sama seperti "
                       f"panel di atas) — bandpass orde {BANDPASS_ORDER} meredam di luar garis hijau")
    ax_freq.set_xlabel("Frekuensi (Hz)")
    ax_freq.set_ylabel("PSD (mV²/Hz, log)")
    ax_freq.legend()

    fig.tight_layout()

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"fase1_{record_id}.png")
    fig.savefig(out_path, dpi=120)
    print(f"\nPlot: {os.path.relpath(out_path)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "100")
