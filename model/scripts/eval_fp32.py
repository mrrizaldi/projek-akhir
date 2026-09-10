"""Fase 6 — evaluasi float32 di DS2 (inter-patient, belum pernah dilihat).

    make eval        (atau: python scripts/eval_fp32.py)

Threshold TIDAK dituning di sini — dipakai apa adanya dari config.THRESHOLD
yang sudah dikalibrasi di DS1/val (JEBAKAN PRD Fase 6).

Keluaran:
    artifacts/metrics/fase6_confusion_fp32.png
    artifacts/metrics/fase6_metrics_fp32.csv        (baris "float32" tabel delta Fase 7)
    artifacts/metrics/fase6_per_record_fp32.csv

Penjelasan alur & alasan: docs/evaluate-walkthrough.md
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import tensorflow as tf  # noqa: E402

from config import ARTIFACT_DIR, METRICS_DIR, PROCESSED_DIR, THRESHOLD  # noqa: E402
from src.evaluate import evaluate_probabilities, per_record_metrics, roc_auc  # noqa: E402


def plot_confusion(counts: dict, out_path: str, judul: str) -> None:
    cm = np.array([[counts["tn"], counts["fp"]], [counts["fn"], counts["tp"]]])
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.imshow(cm, cmap="Blues")
    label = [["TN", "FP"], ["FN", "TP"]]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{label[i][j]}\n{cm[i, j]:,}", ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=13)
    ax.set_xticks([0, 1], ["pred Normal", "pred Aritmia"])
    ax.set_yticks([0, 1], ["asli Normal", "asli Aritmia"])
    ax.set_title(judul)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def main() -> None:
    path = os.path.join(PROCESSED_DIR, "test.npz")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} — jalankan `make split` dulu")
    with np.load(path) as z:
        ds2 = {k: z[k] for k in ("X_morph", "X_rr", "y", "records")}

    model = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))
    prob = model.predict([ds2["X_morph"], ds2["X_rr"]], verbose=0).ravel()

    hasil = evaluate_probabilities(ds2["y"], prob, THRESHOLD)
    auc = roc_auc(ds2["y"], prob)

    print(f"DS2  {len(ds2['y'])} beat dari {len(np.unique(ds2['records']))} pasien  "
          f"({int(ds2['y'].sum())} aritmia)   threshold {THRESHOLD} (dari DS1/val)")
    print(f"  TP={hasil['tp']}  FN={hasil['fn']}  FP={hasil['fp']}  TN={hasil['tn']}")
    for k in ("recall", "precision", "f1", "specificity", "accuracy"):
        print(f"  {k:<12} {hasil[k]:.4f}")
    print(f"  {'auc':<12} {auc:.4f}")

    os.makedirs(METRICS_DIR, exist_ok=True)
    plot_confusion(hasil, os.path.join(METRICS_DIR, "fase6_confusion_fp32.png"),
                   f"DS2 float32 @ threshold {THRESHOLD}")

    with open(os.path.join(METRICS_DIR, "fase6_metrics_fp32.csv"), "w") as f:
        f.write("model,threshold,tp,fn,fp,tn,accuracy,precision,recall,specificity,f1,auc\n")
        f.write("float32,%.2f,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n" % (
            THRESHOLD, hasil["tp"], hasil["fn"], hasil["fp"], hasil["tn"],
            hasil["accuracy"], hasil["precision"], hasil["recall"],
            hasil["specificity"], hasil["f1"], auc))

    rows = per_record_metrics(ds2["y"], prob, ds2["records"], THRESHOLD)
    with open(os.path.join(METRICS_DIR, "fase6_per_record_fp32.csv"), "w") as f:
        f.write("record,n_beat,n_aritmia,tp,fn,fp,tn,recall,precision,specificity\n")
        for r in rows:
            f.write("%d,%d,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f\n" % (
                r["record"], r["n_beat"], r["n_aritmia"], r["tp"], r["fn"], r["fp"],
                r["tn"], r["recall"], r["precision"], r["specificity"]))

    ada = [r for r in rows if r["n_aritmia"] > 0]
    terburuk = sorted(ada, key=lambda r: r["recall"])[:4]
    print("\nrecall per pasien (4 terburuk yang punya aritmia):")
    for r in terburuk:
        print(f"  rec {r['record']}  {r['n_aritmia']:>5} aritmia  recall {r['recall']:.4f}")
    print(f"  median recall {np.median([r['recall'] for r in ada]):.4f} "
          f"atas {len(ada)} pasien beraritmia")


if __name__ == "__main__":
    main()
