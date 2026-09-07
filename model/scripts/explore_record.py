"""Eksplorasi awal Fase 0 — ARSIP, bukan jalur produksi.

Kode asli tulisan sendiri (dulu di src/io_mitdb.py), dipindah utuh ke sini
supaya src/ tetap modul murni. Bebas diulik lagi; tidak dipanggil fase mana pun.
Jalur produksi Fase 0: src/io_mitdb.load_record() + scripts/plot_fase0.py.

    python scripts/explore_record.py
"""
## Download MIT-BIH Arrhythmia Database
# import wfdb
# wfdb.dl_database('mitdb', dl_dir='data/raw/mitdb')

import os

import numpy as np
import wfdb
import matplotlib.pyplot as plt

# tes = os.path.dirname(__file__)
# print(tes)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "mitdb")
print(DATA_DIR)

# tes = os.path.join(DATA_DIR, "101.atr")
tes = os.path.join(DATA_DIR, "100")
record = wfdb.rdrecord(tes)
annotation = wfdb.rdann(tes, "atr")

# print(record)
print(f"   Nama           : {record.record_name}")
print(f"   Jumlah kanal   : {record.n_sig}  → {record.sig_name}")
print(f"   Sampling rate  : {record.fs} Hz")
print(f"   Durasi         : {record.sig_len / record.fs:.1f} detik "
      f"({record.sig_len / record.fs / 60:.1f} menit)")
print(f"   Shape sinyal   : {record.p_signal.shape}")
print(f"   Jumlah anotasi : {len(annotation.symbol)}")

## plotting
fs = record.fs
plot_duration = 10
n_sampel = fs * plot_duration

signal = record.p_signal[:n_sampel, 0]  # kanal MLII
time = np.arange(n_sampel) / fs

# Ambil anotasi dalam window 30 detik
ann_mask = annotation.sample < n_sampel
ann_samples = annotation.sample[ann_mask]
ann_symbols = np.array(annotation.symbol)[ann_mask]

plt.figure(figsize=(14, 4))
plt.plot(time, signal, color="#2563eb", linewidth=0.8, label="ECG (MLII)")

# Tandai setiap R-peak dengan simbol anotasinya
for s, sym in zip(ann_samples, ann_symbols):
    color = "#ef4444" if sym != "N" else "#22c55e"
    plt.axvline(x=s / fs, color=color, alpha=0.4, linewidth=0.8)
    plt.text(s / fs, signal[s] + 0.05, sym, fontsize=6, color=color,
             ha="center", va="bottom")

plt.xlabel("Waktu (detik)")
plt.ylabel("Amplitudo (mV)")
plt.title(f"ECG Rekaman '100' — 30 detik pertama\n"
          f"Hijau = Normal (N), Merah = Aritmia")
plt.legend()
plt.tight_layout()

out_path = os.path.join(os.path.dirname(__file__), "ecg_sample.png")
plt.savefig(out_path, dpi=120)
print(f"\n✅ Plot disimpan ke: scripts/ecg_sample.png")
print("\n🎉 Dataset OK! Siap diproses.\n")