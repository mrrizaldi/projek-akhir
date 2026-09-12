"""Eksperimen: berapa biaya segmentasi on-device (Pan-Tompkins) vs anotasi?

    python scripts/eval_detected_segmentation.py

Semua metrik Fase 6 diukur dengan window yang dipotong dari R-peak ANOTASI
kardiolog. Di alat, window dipotong dari R-peak hasil DETEKSI — setiap deteksi
yang meleset menggeser window, dan setiap beat yang tak terdeteksi tidak pernah
sampai ke model. Selisih dua angka itu belum pernah diukur.

DISIPLIN:
- Offset detektor dikalibrasi di DS1. DS2 tidak menyetel apa pun.
- Model float32 (bukan INT8) supaya yang berubah cuma segmentasi.
- DS2 dilihat kedua kalinya di sini, MURNI untuk mengukur; tidak ada parameter
  yang diambil darinya. Dicatat jujur di ../CLAUDE.md.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf  # noqa: E402

from config import (  # noqa: E402
    ARTIFACT_DIR, DS1, DS2, FS, GROUP_DELAY_SAMPLES, METRICS_DIR,
    PT_REFINE_WIN, THRESHOLD, WIN_LEN, WIN_POST, WIN_PRE,
)
from src.evaluate import binary_metrics, confusion_counts, pair_detected  # noqa: E402
from src.features_rr import compute_rr_features, to_aami_class, to_binary_label  # noqa: E402
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import (  # noqa: E402
    apply_bandpass, design_bandpass_sos, pan_tompkins_detect, segment_beats,
    zscore_per_window,
)

TOLERANSI_MS = 150


def haluskan(r_kasar, filtered):
    """Geser tiap deteksi ke puncak R sebenarnya, lalu kembalikan group delay.

    Tanpa ini R mendarat di indeks acak sekitar 94 (std delay detektor 13 sampel).
    Tanpa `- GROUP_DELAY` R mendarat di 90, bukan 94 — dan geseran 4 sampel saja
    (11 ms) menjatuhkan precision dari 0,48 ke 0,12. Lihat docs.
    """
    hasil = []
    for lo in r_kasar:
        a = max(0, lo - PT_REFINE_WIN)
        b = lo + PT_REFINE_WIN + 1
        hasil.append(a + int(np.argmax(filtered[a:b])))
    return np.asarray(hasil) - GROUP_DELAY_SAMPLES


def deteksi(record_id: str, sos):
    signal, r_anotasi, simbol, _ = load_record(record_id)
    filtered = apply_bandpass(signal, sos)
    return signal, filtered, r_anotasi, simbol, pan_tompkins_detect(filtered, FS)


def kalibrasi_offset(sos, toleransi: int) -> int:
    """Median (deteksi - anotasi) atas DS1. Inilah yang firmware harus kompensasi."""
    selisih = []
    for rec in DS1:
        try:
            _, _, r_anot, _, r_det = deteksi(str(rec), sos)
        except ValueError:
            continue
        pasangan = pair_detected(r_det, r_anot, toleransi)
        cocok = pasangan >= 0
        selisih.extend((r_det[cocok] - r_anot[pasangan[cocok]]).tolist())
    return int(np.median(selisih)), len(selisih)


def main() -> None:
    sos = design_bandpass_sos()
    toleransi = round(TOLERANSI_MS / 1000 * FS)

    offset, n_pasangan = kalibrasi_offset(sos, toleransi)
    print(f"Offset detektor dikalibrasi di DS1: median {offset} sampel "
          f"({1000 * offset / FS:.1f} ms) atas {n_pasangan:,} pasangan\n")

    model = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))

    W, R, Y, palsu_prob = [], [], [], []
    n_aritmia_total = n_terdeteksi = n_palsu = 0
    det_tp = det_fn = 0
    kena = {}
    tot = {}

    for rec in DS2:
        signal, filtered, r_anot, simbol, r_det = deteksi(str(rec), sos)
        label_anot = np.array([to_binary_label(to_aami_class(s)) for s in simbol])
        n_aritmia_total += int(label_anot.sum())

        r_pakai = haluskan(r_det - offset, filtered)  # kompensasi + penyelarasan
        pasangan = pair_detected(r_det, r_anot, toleransi)

        det_tp += int((pasangan >= 0).sum())
        det_fn += len(r_anot) - int((pasangan >= 0).sum())

        terdeteksi = np.zeros(len(r_anot), dtype=bool)
        terdeteksi[pasangan[pasangan >= 0]] = True
        for sim, ok in zip(simbol, terdeteksi):
            kelas = to_aami_class(sim)
            tot[kelas] = tot.get(kelas, 0) + 1
            kena[kelas] = kena.get(kelas, 0) + int(ok)

        # Syarat sama dengan prep_beats, tapi atas deret DETEKSI.
        i = np.arange(len(r_pakai))
        muat = (r_pakai - WIN_PRE >= 0) & (r_pakai + WIN_POST <= len(signal))
        idx = i[muat & (i >= 2)]
        if len(idx) == 0:
            continue

        windows = zscore_per_window(segment_beats(filtered, r_pakai[idx]))
        rr = compute_rr_features(r_pakai)[idx]       # dari deret deteksi UTUH
        pas = pasangan[idx]

        cocok = pas >= 0
        n_terdeteksi += int(cocok.sum())
        n_palsu += int((~cocok).sum())

        W.append(windows[cocok])
        R.append(rr[cocok])
        Y.append(label_anot[pas[cocok]])
        if (~cocok).any():                            # deteksi palsu: tetap diklasifikasi
            palsu_prob.append(model.predict(
                [windows[~cocok].reshape(-1, WIN_LEN, 1), rr[~cocok]], verbose=0).ravel())

    X_morph = np.concatenate(W).reshape(-1, WIN_LEN, 1)
    X_rr = np.concatenate(R)
    y = np.concatenate(Y)
    prob = model.predict([X_morph, X_rr], verbose=0).ravel()
    pred = (prob >= THRESHOLD).astype(int)

    c = confusion_counts(y, pred)
    m = binary_metrics(c)

    print(f"Detektor di DS2: {det_tp:,} beat terdeteksi, {det_fn:,} terlewat "
          f"(sensitivity {det_tp / (det_tp + det_fn):.4f}), {n_palsu:,} deteksi palsu")
    print("   per kelas AAMI: " + "  ".join(
        f"{k} {kena[k] / tot[k]:.3f}" for k in ("N", "S", "V", "F") if tot.get(k)))
    ar_t = sum(tot.get(k, 0) for k in "SVFQ")
    ar_k = sum(kena.get(k, 0) for k in "SVFQ")
    print(f"   Normal {kena['N'] / tot['N']:.4f} vs Aritmia {ar_k / ar_t:.4f} — "
          f"beat prematur terblokir refraktori 200 ms detektor\n")

    print("A. Klasifikasi pada beat yang BERHASIL terdeteksi")
    print(f"   n={len(y):,}  TP={c['tp']} FN={c['fn']} FP={c['fp']} TN={c['tn']}")
    print(f"   recall {m['recall']:.4f}  precision {m['precision']:.4f}  F1 {m['f1']:.4f}")

    # Recall tingkat SISTEM: penyebutnya semua aritmia asli, termasuk yang
    # tak pernah sampai ke model karena detektor melewatkannya.
    sistem_tp = int(((pred == 1) & (y == 1)).sum())
    print("\nB. Tingkat SISTEM (penyebut = semua aritmia asli di DS2)")
    print(f"   aritmia asli {n_aritmia_total:,}  tertangkap {sistem_tp:,}"
          f"  → recall sistem {sistem_tp / n_aritmia_total:.4f}")

    if palsu_prob:
        pp = np.concatenate(palsu_prob)
        print(f"\nC. Deteksi palsu: {len(pp):,} window tanpa beat asli, "
              f"{int((pp >= THRESHOLD).sum()):,} diklasifikasi Aritmia "
              f"({100 * (pp >= THRESHOLD).mean():.1f}%) → alarm palsu tambahan")

    print("\nD. Pembanding Fase 6 (segmentasi anotasi, float32, threshold sama)")
    print("   recall 0.6661  precision 0.4919  F1 0.5659")

    os.makedirs(METRICS_DIR, exist_ok=True)
    out = os.path.join(METRICS_DIR, "fase6b_segmentasi_deteksi.csv")
    with open(out, "w") as f:
        f.write("segmentasi,tp,fn,fp,tn,recall,precision,f1,recall_sistem,offset_sampel\n")
        f.write("anotasi,3630,1820,3750,40454,0.666055,0.491870,0.565903,0.666055,0\n")
        f.write("deteksi,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%d\n" % (
            c["tp"], c["fn"], c["fp"], c["tn"], m["recall"], m["precision"], m["f1"],
            sistem_tp / n_aritmia_total, offset))
    print(f"\n{out}")


if __name__ == "__main__":
    main()
