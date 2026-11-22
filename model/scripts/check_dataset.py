import os
import sys
import wfdb
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "mitdb")
SAMPLE_RECORD = "100"

print("=" * 55)
print("  MIT-BIH ARRHYTHMIA DATASET CHECK")
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

print(f"\n✅ Complete records (.hea + .dat + .atr): {len(records_found)}")
print(f"   {records_found}\n")

if len(records_found) == 0:
    print("❌ No records found! Check the DATA_DIR path.")
    sys.exit(1)

if len(records_found) < 48:
    print(f"⚠️  MIT-BIH should have 48 records, but only {len(records_found)} found.")
else:
    print("✅ Record count matches (48 records).")

print(f"\n── Reading sample record: {SAMPLE_RECORD} ──")
record_path = os.path.join(DATA_DIR, SAMPLE_RECORD)

record = wfdb.rdrecord(record_path)
annotation = wfdb.rdann(record_path, "atr")

print(f"   Name           : {record.record_name}")
print(f"   Channel count  : {record.n_sig}  → {record.sig_name}")
print(f"   Sampling rate  : {record.fs} Hz")
print(f"   Duration       : {record.sig_len / record.fs:.1f} seconds "
      f"({record.sig_len / record.fs / 60:.1f} min)")
print(f"   Signal shape   : {record.p_signal.shape}")
print(f"   Annotation count: {len(annotation.symbol)}")

label_counts = Counter(annotation.symbol)
print(f"\n── Label distribution in record {SAMPLE_RECORD} ──")
for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
    print(f"   '{label}' : {count}")

fs = record.fs
plot_duration = 30
n_samples = plot_duration * fs

signal = record.p_signal[:n_samples, 0]
time = np.arange(n_samples) / fs

ann_mask = annotation.sample < n_samples
ann_samples = annotation.sample[ann_mask]
ann_symbols = np.array(annotation.symbol)[ann_mask]

plt.figure(figsize=(14, 4))
plt.plot(time, signal, color="#2563eb", linewidth=0.8, label="ECG (MLII)")

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
print(f"\n✅ Plot saved to: scripts/ecg_sample.png")
print("\n🎉 Dataset OK! Ready to process.\n")
