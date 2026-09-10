"""Fase 5 — latih model hybrid di DS1, simpan model_fp32.keras + kurva.

    make train       (atau: python scripts/train_model.py)

DS2 HARAM di sini — validation diambil dari DS1 (config.VAL_RECORDS).
Pantau recall Aritmia + AUC, bukan accuracy (data timpang).

Penjelasan alur & alasan: docs/train-walkthrough.md
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import tensorflow as tf  # noqa: E402

from config import ARTIFACT_DIR, METRICS_DIR, PROCESSED_DIR, SEED, THRESHOLD  # noqa: E402
from src.dataset import split_train_val  # noqa: E402
from src.model import build_hybrid_model  # noqa: E402
from src.train import make_class_weights, train  # noqa: E402


def load_ds1() -> dict:
    path = os.path.join(PROCESSED_DIR, "train.npz")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} — jalankan `make split` dulu")
    with np.load(path) as z:
        return {k: z[k] for k in ("X_morph", "X_rr", "y", "records")}


def plot_history(history, out_path: str) -> None:
    h = history.history
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, key, judul in zip(axes, ("loss", "recall", "auc"),
                              ("Loss", "Recall Aritmia", "AUC")):
        ax.plot(h[key], label="train")
        ax.plot(h[f"val_{key}"], label="val")
        ax.set_title(judul)
        ax.set_xlabel("epoch")
        ax.grid(alpha=0.3)
        ax.legend()
    fig.suptitle("Fase 5 — training di DS1 (val = record DS1 yang disisihkan)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def main() -> None:
    np.random.seed(SEED)
    tf.random.set_seed(SEED)
    os.makedirs(METRICS_DIR, exist_ok=True)

    tr, va = split_train_val(load_ds1())
    bobot = make_class_weights(tr["y"])
    print(f"train {len(tr['y'])} beat ({int(tr['y'].sum())} aritmia)  "
          f"val {len(va['y'])} beat ({int(va['y'].sum())} aritmia)")
    print(f"class_weight  Normal {bobot[0]:.3f}  Aritmia {bobot[1]:.3f}")

    model = build_hybrid_model()
    history = train(model, tr, va)

    model_path = os.path.join(ARTIFACT_DIR, "model_fp32.keras")
    model.save(model_path)
    plot_path = os.path.join(METRICS_DIR, "fase5_training.png")
    plot_history(history, plot_path)

    p = model.predict([va["X_morph"], va["X_rr"]], verbose=0).ravel()
    pred = (p >= THRESHOLD).astype(int)
    y = va["y"].astype(int)
    tp = int(((pred == 1) & (y == 1)).sum()); fn = int(((pred == 0) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
    print(f"\nVAL @ threshold {THRESHOLD}   TP={tp} FN={fn} FP={fp} TN={tn}")
    print(f"  recall(sensitivity) {tp / (tp + fn):.4f}   precision {tp / (tp + fp):.4f}   "
          f"specificity {tn / (tn + fp):.4f}")
    print(f"\n{model_path}\n{plot_path}")


if __name__ == "__main__":
    main()
