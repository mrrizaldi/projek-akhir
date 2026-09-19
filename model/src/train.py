"""train — Fase 5: class weight + loop training. Walkthrough: docs/train-walkthrough.md"""
import numpy as np
from tensorflow.keras import callbacks, metrics

from config import BATCH_SIZE, EARLY_STOP_MONITOR, EARLY_STOP_PATIENCE, EPOCHS


def make_class_weights(y) -> dict:
    y = np.asarray(y).astype(int)
    counts = np.bincount(y, minlength=2)
    if (counts == 0).any():
        raise ValueError(f"satu kelas kosong: Normal={counts[0]}, Aritmia={counts[1]}")
    return {c: len(y) / (2.0 * counts[c]) for c in (0, 1)}


def compile_model(model):
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=[
            metrics.Recall(name="recall"),
            metrics.Precision(name="precision"),
            metrics.AUC(name="auc"),
        ],
    )
    return model


def train(model, train_data: dict, val_data: dict,
          epochs: int = EPOCHS, batch_size: int = BATCH_SIZE,
          pakai_class_weight: bool = True):
    """pakai_class_weight=False untuk ablasi K1/T1 (docs/2026-09-19-fitur-design.md).

    Bawaan True = nilai terkunci, tidak berubah. P1 Tabel 4 mengukur trade-off-nya
    di varian yang HANYA beda ini: recall -7 poin, precision +31 poin.
    """
    compile_model(model)
    stop = callbacks.EarlyStopping(
        monitor=EARLY_STOP_MONITOR, mode="max",
        patience=EARLY_STOP_PATIENCE, restore_best_weights=True,
    )
    return model.fit(
        [train_data["X_morph"], train_data["X_rr"]], train_data["y"],
        validation_data=([val_data["X_morph"], val_data["X_rr"]], val_data["y"]),
        class_weight=make_class_weights(train_data["y"]) if pakai_class_weight else None,
        epochs=epochs, batch_size=batch_size, callbacks=[stop], verbose=2,
    )
