"""
Script verifikasi dataset MIT-BIH Arrhythmia.
Jalankan dari folder model/:
    python scripts/check_dataset.py
"""

import os
import sys
import wfdb
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# ── Konfigurasi ──────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "mitdb")
SAMPLE_RECORD = "100"  # rekaman pertama yang dicek

# ── 1. Cek keberadaan file ────────────────────────────────────────────────────
print("=" * 55)
print("  CEK DATASET MIT-BIH ARRHYTHMIA")
print("=" * 55)

required_extensions = [".hea", ".dat", ".atr"]
records_found = []

for f in sorted(os.listdir(DATA_DIR)):
    if f.endswith(".hea"):
        rec_id = f.replace(".hea", "")
        has_all = all(
            os.path.exists(os.path.join(DATA_DIR, rec_id + ext))
            for ext in required_extensions
        )
        if has_all:
            records_found.append(rec_id)

print(f"\n✅ Rekaman lengkap (.hea + .dat + .atr): {len(records_found)}")
print(f"   {records_found}\n")

if len(records_found) == 0:
    print("❌ Tidak ada rekaman yang ditemukan! Cek path DATA_DIR.")
    sys.exit(1)

if len(records_found) < 48:
    print(f"⚠️  MIT-BIH seharusnya punya 48 rekaman, tapi hanya ada {len(records_found)}.")
else:
    print("✅ Jumlah rekaman sesuai (48 rekaman).")

# ── 2. Baca satu rekaman sampel ───────────────────────────────────────────────
print(f"\n── Membaca rekaman sampel: {SAMPLE_RECORD} ──")
record_path = os.path.join(DATA_DIR, SAMPLE_RECORD)

record = wfdb.rdrecord(record_path)
annotation = wfdb.rdann(record_path, "atr")

print(f"   Nama           : {record.record_name}")
print(f"   Jumlah kanal   : {record.n_sig}  → {record.sig_name}")
print(f"   Sampling rate  : {record.fs} Hz")
print(f"   Durasi         : {record.sig_len / record.fs:.1f} detik "
      f"({record.sig_len / record.fs / 60:.1f} menit)")
print(f"   Shape sinyal   : {record.p_signal.shape}")
print(f"   Jumlah anotasi : {len(annotation.symbol)}")

# ── 3. Ringkasan label aritmia ────────────────────────────────────────────────
label_counts = Counter(annotation.symbol)
print(f"\n── Distribusi label di rekaman {SAMPLE_RECORD} ──")
for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
    print(f"   '{label}' : {count}")

# ── 4. Plot sinyal + anotasi (30 detik pertama) ───────────────────────────────
fs = record.fs
durasi_plot = 30  # detik
n_sampel = durasi_plot * fs

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
plt.title(f"ECG Rekaman {SAMPLE_RECORD} — 30 detik pertama\n"
          f"Hijau = Normal (N), Merah = Aritmia")
plt.legend()
plt.tight_layout()

out_path = os.path.join(os.path.dirname(__file__), "ecg_sample.png")
plt.savefig(out_path, dpi=120)
print(f"\n✅ Plot disimpan ke: scripts/ecg_sample.png")
print("\n🎉 Dataset OK! Siap diproses.\n")
