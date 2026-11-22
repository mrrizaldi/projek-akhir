import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf

from config import (
    ARTIFACT_DIR, DS1, DS2, FS, GROUP_DELAY_SAMPLES, METRICS_DIR,
    PT_REFINE_WIN, THRESHOLD, WIN_LEN, WIN_POST, WIN_PRE,
)
from src.evaluate import binary_metrics, confusion_counts, pair_detected
from src.features_rr import compute_rr_features, to_aami_class, to_binary_label
from src.io_mitdb import load_record
from src.preprocessing import (
    apply_bandpass, design_bandpass_sos, pan_tompkins_detect, segment_beats,
    zscore_per_window,
)

TOLERANCE_WINDOW_MS = 150


def refine_peaks(r_coarse, filtered):
    refined = []
    for lo in r_coarse:
        a = max(0, lo - PT_REFINE_WIN)
        b = lo + PT_REFINE_WIN + 1
        refined.append(a + int(np.argmax(filtered[a:b])))
    return np.asarray(refined) - GROUP_DELAY_SAMPLES


def deteksi(record_id: str, sos):
    signal, r_annotated, symbols, _ = load_record(record_id)
    filtered = apply_bandpass(signal, sos)
    return signal, filtered, r_annotated, symbols, pan_tompkins_detect(filtered, FS)


def calibrate_offset(sos, tolerance: int) -> int:
    offsets = []
    for rec in DS1:
        try:
            _, _, r_ref, _, r_det = deteksi(str(rec), sos)
        except ValueError:
            continue
        pairing = pair_detected(r_det, r_ref, tolerance)
        matched = pairing >= 0
        offsets.extend((r_det[matched] - r_ref[pairing[matched]]).tolist())
    return int(np.median(offsets)), len(offsets)


def main() -> None:
    sos = design_bandpass_sos()
    tolerance = round(TOLERANCE_WINDOW_MS / 1000 * FS)

    offset, n_pairs = calibrate_offset(sos, tolerance)
    print(f"Detector offset calibrated on DS1: median {offset} samples "
          f"({1000 * offset / FS:.1f} ms) over {n_pairs:,} pairs\n")

    model = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))

    W, R, Y, false_prob = [], [], [], []
    n_arrhythmia_total = n_detected = n_palsu = 0
    det_tp = det_fn = 0
    hit = {}
    tot = {}

    for rec in DS2:
        signal, filtered, r_ref, symbols, r_det = deteksi(str(rec), sos)
        annotated_labels = np.array([to_binary_label(to_aami_class(s)) for s in symbols])
        n_arrhythmia_total += int(annotated_labels.sum())

        r_used = refine_peaks(r_det - offset, filtered)
        pairing = pair_detected(r_det, r_ref, tolerance)

        det_tp += int((pairing >= 0).sum())
        det_fn += len(r_ref) - int((pairing >= 0).sum())

        detected = np.zeros(len(r_ref), dtype=bool)
        detected[pairing[pairing >= 0]] = True
        for symbol_short, ok in zip(symbols, detected):
            aami_class = to_aami_class(symbol_short)
            tot[aami_class] = tot.get(aami_class, 0) + 1
            hit[aami_class] = hit.get(aami_class, 0) + int(ok)

        i = np.arange(len(r_used))
        fits = (r_used - WIN_PRE >= 0) & (r_used + WIN_POST <= len(signal))
        idx = i[fits & (i >= 2)]
        if len(idx) == 0:
            continue

        windows = zscore_per_window(segment_beats(filtered, r_used[idx]))
        rr = compute_rr_features(r_used)[idx]
        pas = pairing[idx]

        matched = pas >= 0
        n_detected += int(matched.sum())
        n_palsu += int((~matched).sum())

        W.append(windows[matched])
        R.append(rr[matched])
        Y.append(annotated_labels[pas[matched]])
        if (~matched).any():
            false_prob.append(model.predict(
                [windows[~matched].reshape(-1, WIN_LEN, 1), rr[~matched]], verbose=0).ravel())

    X_morph = np.concatenate(W).reshape(-1, WIN_LEN, 1)
    X_rr = np.concatenate(R)
    y = np.concatenate(Y)
    prob = model.predict([X_morph, X_rr], verbose=0).ravel()
    pred = (prob >= THRESHOLD).astype(int)

    c = confusion_counts(y, pred)
    m = binary_metrics(c)

    print(f"Detector on DS2: {det_tp:,} beats detected, {det_fn:,} missed "
          f"(sensitivity {det_tp / (det_tp + det_fn):.4f}), {n_palsu:,} false detections")
    print("   per AAMI class: " + "  ".join(
        f"{k} {hit[k] / tot[k]:.3f}" for k in ("N", "S", "V", "F") if tot.get(k)))
    ar_t = sum(tot.get(k, 0) for k in "SVFQ")
    ar_k = sum(hit.get(k, 0) for k in "SVFQ")
    print(f"   Normal {hit['N'] / tot['N']:.4f} vs Arrhythmia {ar_k / ar_t:.4f}: "
          f"premature beats blocked by the detector 200 ms refractory period\n")

    print("A. Classification on beats that WERE detected")
    print(f"   n={len(y):,}  TP={c['tp']} FN={c['fn']} FP={c['fp']} TN={c['tn']}")
    print(f"   recall {m['recall']:.4f}  precision {m['precision']:.4f}  F1 {m['f1']:.4f}")

    system_tp = int(((pred == 1) & (y == 1)).sum())
    print("\nB. SYSTEM level (denominator = all true arrhythmias in DS2)")
    print(f"   true arrhythmias {n_arrhythmia_total:,}  caught {system_tp:,}"
          f"  → system recall {system_tp / n_arrhythmia_total:.4f}")

    if false_prob:
        pp = np.concatenate(false_prob)
        print(f"\nC. False detections: {len(pp):,} windows without a true beat, "
              f"{int((pp >= THRESHOLD).sum()):,} classified Arrhythmia "
              f"({100 * (pp >= THRESHOLD).mean():.1f}%) → extra false alarms")

    with open(os.path.join(METRICS_DIR, "fase6_metrics_fp32.csv")) as f:
        a = next(csv.DictReader(f))
    print("\nD. Phase 6 comparison (annotation segmentation, float32, threshold "
          f"{a['threshold']}; fase6_metrics_fp32.csv)")
    print(f"   recall {float(a['recall']):.4f}  precision {float(a['precision']):.4f}  "
          f"F1 {float(a['f1']):.4f}")

    os.makedirs(METRICS_DIR, exist_ok=True)
    out = os.path.join(METRICS_DIR, "fase6b_segmentasi_deteksi.csv")
    with open(out, "w") as f:
        f.write("segmentasi,tp,fn,fp,tn,recall,precision,f1,recall_sistem,offset_sampel\n")
        f.write("anotasi,%s,%s,%s,%s,%s,%s,%s,%s,0\n" % (
            a["tp"], a["fn"], a["fp"], a["tn"], a["recall"], a["precision"], a["f1"],
            a["recall"]))
        f.write("deteksi,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%d\n" % (
            c["tp"], c["fn"], c["fp"], c["tn"], m["recall"], m["precision"], m["f1"],
            system_tp / n_arrhythmia_total, offset))
    print(f"\n{out}")


if __name__ == "__main__":
    main()
