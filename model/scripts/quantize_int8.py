"""Fase 7 — PTQ INT8 + evaluasi ulang di DS2 identik + tabel delta.

    make quantize    (atau: python scripts/quantize_int8.py)

Threshold & prosedur evaluasi SAMA PERSIS dengan Fase 6 — kalau tidak, delta
yang terukur bukan efek kuantisasi melainkan efek beda cara ukur.

Keluaran:
    artifacts/model_int8.tflite
    artifacts/metrics/fase7_delta.csv
    artifacts/metrics/fase7_confusion_int8.png

Penjelasan alur & alasan: docs/quantize-walkthrough.md
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (  # noqa: E402
    ARTIFACT_DIR, INT8_IO, MAX_MODEL_KB, METRICS_DIR, PROCESSED_DIR,
    REP_SAMPLES, THRESHOLD,
)
from src.evaluate import evaluate_probabilities, roc_auc  # noqa: E402
from src.quantize import (  # noqa: E402
    predict_tflite, quantize_int8, representative_dataset_gen, stratified_indices,
)
from scripts.eval_fp32 import plot_confusion  # noqa: E402

METRIK = ("accuracy", "precision", "recall", "f1", "specificity")


def _muat(nama: str) -> dict:
    path = os.path.join(PROCESSED_DIR, nama)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} — jalankan `make split` dulu")
    with np.load(path) as z:
        return {k: z[k] for k in ("X_morph", "X_rr", "y", "records")}


def main() -> None:
    ds1, ds2 = _muat("train.npz"), _muat("test.npz")
    keras_path = os.path.join(ARTIFACT_DIR, "model_fp32.keras")
    tflite_path = os.path.join(ARTIFACT_DIR, "model_int8.tflite")

    idx = stratified_indices(ds1["y"], REP_SAMPLES)
    print(f"kalibrasi {len(idx)} sampel dari DS1  "
          f"(Normal {int((ds1['y'][idx] == 0).sum())}, "
          f"Aritmia {int((ds1['y'][idx] == 1).sum())})   int8_io={INT8_IO}")

    blob = quantize_int8(keras_path, representative_dataset_gen(
        ds1["X_morph"], ds1["X_rr"], ds1["y"], REP_SAMPLES))
    with open(tflite_path, "wb") as f:
        f.write(blob)
    ukuran_kb = len(blob) / 1024
    print(f"{tflite_path}  {len(blob):,} byte = {ukuran_kb:.2f} KB "
          f"({'OK' if ukuran_kb < MAX_MODEL_KB else 'MELEBIHI'} batas {MAX_MODEL_KB} KB)")

    print(f"inferensi INT8 atas {len(ds2['y']):,} beat DS2 ...")
    prob = predict_tflite(tflite_path, ds2["X_morph"], ds2["X_rr"])
    int8 = evaluate_probabilities(ds2["y"], prob, THRESHOLD)
    int8["auc"] = roc_auc(ds2["y"], prob)

    fp32 = {}
    with open(os.path.join(METRICS_DIR, "fase6_metrics_fp32.csv")) as f:
        kolom = f.readline().strip().split(",")
        nilai = f.readline().strip().split(",")
    for k, v in zip(kolom, nilai):
        if k not in ("model",):
            fp32[k] = float(v)

    print(f"\n{'Metrik':<14} {'Float32':>10} {'INT8':>10} {'Delta':>10}")
    baris = []
    for k in METRIK + ("auc",):
        d = int8[k] - fp32[k]
        print(f"{k:<14} {fp32[k]:>10.4f} {int8[k]:>10.4f} {d:>+10.4f}")
        baris.append((k, fp32[k], int8[k], d))
    print(f"{'TP/FN/FP/TN':<14} "
          f"{int(fp32['tp'])}/{int(fp32['fn'])}/{int(fp32['fp'])}/{int(fp32['tn'])}"
          f"   {int8['tp']}/{int8['fn']}/{int8['fp']}/{int8['tn']}")
    print(f"{'ukuran model':<14} {'(n/a)':>10} {ukuran_kb:>9.2f}K")

    with open(os.path.join(METRICS_DIR, "fase7_delta.csv"), "w") as f:
        f.write("metrik,float32,int8,delta\n")
        for k, a, b, d in baris:
            f.write(f"{k},{a:.6f},{b:.6f},{d:+.6f}\n")
        f.write(f"ukuran_kb,,{ukuran_kb:.2f},\n")
        f.write(f"threshold,{THRESHOLD},{THRESHOLD},0\n")

    plot_confusion(int8, os.path.join(METRICS_DIR, "fase7_confusion_int8.png"),
                   f"DS2 INT8 @ threshold {THRESHOLD}")
    print(f"\n{os.path.join(METRICS_DIR, 'fase7_delta.csv')}")


if __name__ == "__main__":
    main()
