"""Jalankan pipeline LENGKAP atas rekaman dari device, persis seperti di alat.

    make klasifikasi FILE=data/recordings/xxx.csv

Alur sama dengan ecg_live.cpp: bandpass kausal -> Pan-Tompkins -> penyelarasan
R (offset + puncak + group delay) -> window + z-score -> fitur RR -> INT8.
Sudah dibuktikan cocok digit demi digit antara PC dan ESP32-S3, jadi hasil di
sini setara dengan yang dicetak alat ke serial — bedanya ini tersimpan dan bisa
dilaporkan.

Tanpa ground truth: rekaman dari badan tidak punya anotasi kardiolog. Keluaran
ini menunjukkan APA yang diputuskan alat, bukan apakah keputusannya benar.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (  # noqa: E402
    ARTIFACT_DIR, FS, GROUP_DELAY_SAMPLES, METRICS_DIR, PT_DETECTOR_OFFSET,
    PT_REFINE_WIN, THRESHOLD, WIN_LEN, WIN_POST, WIN_PRE,
)
from src.features_rr import compute_rr_features  # noqa: E402
from src.preprocessing import (  # noqa: E402
    apply_bandpass, design_bandpass_sos, pan_tompkins_detect, segment_beats,
    zscore_per_window,
)
from src.quantize import predict_tflite  # noqa: E402
from scripts.analyze_recording import muat  # noqa: E402


def selaraskan(r_kasar, filtered):
    """Sama dengan ecg_align_r di firmware: kompensasi → puncak → group delay."""
    hasil = []
    for lo in r_kasar - PT_DETECTOR_OFFSET:
        a = max(0, lo - PT_REFINE_WIN)
        b = lo + PT_REFINE_WIN + 1
        hasil.append(a + int(np.argmax(filtered[a:b])))
    return np.asarray(hasil) - GROUP_DELAY_SAMPLES


def main() -> None:
    path = sys.argv[1]
    nama = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(path)[:-4]
    mentah, fs, lewat = muat(path)

    x = (mentah - mentah.mean()) / 1000.0
    filtered = apply_bandpass(x, design_bandpass_sos())
    r = selaraskan(pan_tompkins_detect(filtered, fs), filtered)

    i = np.arange(len(r))
    muat_win = (r - WIN_PRE >= 0) & (r + WIN_POST <= len(filtered))
    idx = i[muat_win & (i >= 2)]          # i>=2: butuh RR_prev & dRR
    if len(idx) == 0:
        sys.exit(f"Cuma {len(r)} R-peak terdeteksi di {len(mentah) / fs:.1f} detik — "
                 f"butuh minimal 3 (beat 0 & 1 tak punya RR_prev/dRR).\n"
                 f"Sinyalnya kemungkinan terlalu kotor; jalankan `make analisis "
                 f"FILE={path}` dulu.")

    windows = zscore_per_window(segment_beats(filtered, r[idx]))
    rr = compute_rr_features(r)[idx]
    prob = predict_tflite(os.path.join(ARTIFACT_DIR, "model_int8.tflite"),
                          windows.reshape(-1, WIN_LEN, 1), rr)
    pred = (prob >= THRESHOLD).astype(int)

    durasi = len(mentah) / fs
    bpm = 60.0 / rr[:, 0]
    masuk_akal = ((bpm >= 30) & (bpm <= 200)).mean()

    print(f"{nama}: {len(mentah)} sampel = {durasi:.1f} detik @ {fs} Hz"
          + (f", {lewat} terlewat" if lewat is not None else ""))
    print(f"  R-peak terdeteksi  {len(r)}  → {len(idx)} beat diklasifikasi")
    print(f"  BPM dari RR_prev   median {np.median(bpm):.0f}  "
          f"min {bpm.min():.0f}  max {bpm.max():.0f}  "
          f"masuk akal {100 * masuk_akal:.0f}%")
    print(f"  Klasifikasi @{THRESHOLD}  Normal {int((pred == 0).sum())}  "
          f"Aritmia {int(pred.sum())} ({100 * pred.mean():.1f}%)")
    print(f"  Probabilitas       median {np.median(prob):.3f}  "
          f"p10 {np.percentile(prob, 10):.3f}  p90 {np.percentile(prob, 90):.3f}")

    print(f"\n  {'#':>3} {'detik':>7} {'RR':>6} {'bpm':>5} {'p':>7}  hasil")
    for n, (k, p) in enumerate(zip(idx, prob)):
        if n >= 25:
            print(f"  ... {len(idx) - 25} beat lagi")
            break
        print(f"  {n:>3} {r[k] / fs:>7.2f} {rr[n, 0]:>6.3f} {60 / rr[n, 0]:>5.0f} "
              f"{p:>7.4f}  {'ARITMIA' if p >= THRESHOLD else 'normal'}")

    os.makedirs(METRICS_DIR, exist_ok=True)
    out = os.path.join(METRICS_DIR, f"klasifikasi_{nama}.csv")
    with open(out, "w") as f:
        f.write("beat,sampel,detik,rr_prev,rr_ratio,drr,prob,prediksi\n")
        for n, (k, p) in enumerate(zip(idx, prob)):
            f.write("%d,%d,%.3f,%.4f,%.4f,%.4f,%.6f,%d\n" % (
                n, r[k], r[k] / fs, rr[n, 0], rr[n, 1], rr[n, 2], p, int(p >= THRESHOLD)))
    print(f"\n{out}")
    print("\nCatatan: rekaman badan tidak punya anotasi kardiolog. Ini menunjukkan\n"
          "APA yang diputuskan alat, bukan apakah keputusannya benar.")


if __name__ == "__main__":
    main()
