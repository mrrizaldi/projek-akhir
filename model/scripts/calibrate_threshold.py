"""Fase 5/6 — kalibrasi threshold di VALIDATION (DS1). DS2 HARAM di sini.

    python scripts/calibrate_threshold.py

Kriteria terkunci: F1 maksimum, tie-break ke recall bila selisih F1 < 0,005.
Hasilnya jadi config.THRESHOLD. Penjelasan: docs/evaluate-walkthrough.md §2.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf  # noqa: E402

from config import ARTIFACT_DIR, METRICS_DIR, PROCESSED_DIR  # noqa: E402
from src.dataset import split_train_val  # noqa: E402
from src.evaluate import sweep_thresholds  # noqa: E402

F1_TIE_MARGIN = 0.005


def main() -> None:
    with np.load(os.path.join(PROCESSED_DIR, "train.npz")) as z:
        data = {k: z[k] for k in ("X_morph", "X_rr", "y", "records")}
    _, va = split_train_val(data)

    model = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))
    prob = model.predict([va["X_morph"], va["X_rr"]], verbose=0).ravel()

    rows = sweep_thresholds(va["y"], prob, np.arange(0.05, 0.96, 0.05))
    print(" thr  recall  prec     F1    spec    TP   FN   FP")
    for r in rows:
        print("%.2f  %.4f  %.4f  %.4f  %.4f %4d %4d %4d"
              % (r["threshold"], r["recall"], r["precision"], r["f1"],
                 r["specificity"], r["tp"], r["fn"], r["fp"]))

    f1_max = max(r["f1"] for r in rows)
    kandidat = [r for r in rows if f1_max - r["f1"] < F1_TIE_MARGIN]
    pilih = max(kandidat, key=lambda r: r["recall"])
    print(f"\nF1 maksimum {f1_max:.4f}; kandidat dalam margin {F1_TIE_MARGIN}: "
          f"{[round(r['threshold'], 2) for r in kandidat]}")
    print(f"→ THRESHOLD = {pilih['threshold']:.2f}  "
          f"(recall {pilih['recall']:.4f}, precision {pilih['precision']:.4f})")

    out = os.path.join(METRICS_DIR, "fase5_threshold_sweep.csv")
    os.makedirs(METRICS_DIR, exist_ok=True)
    with open(out, "w") as f:
        f.write("threshold,tp,fn,fp,tn,accuracy,precision,recall,specificity,f1\n")
        for r in rows:
            f.write("%.2f,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f\n" % (
                r["threshold"], r["tp"], r["fn"], r["fp"], r["tn"],
                r["accuracy"], r["precision"], r["recall"], r["specificity"], r["f1"]))
    print(out)


if __name__ == "__main__":
    main()
