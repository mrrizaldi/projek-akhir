"""train — Fase 5: class weight + loop training. Walkthrough: docs/train-walkthrough.md"""
import numpy as np
from tensorflow.keras import callbacks, metrics, optimizers

from config import BATCH_SIZE, EARLY_STOP_MONITOR, EARLY_STOP_PATIENCE, EPOCHS


def make_class_weights(y) -> dict:
    y = np.asarray(y).astype(int)
    counts = np.bincount(y, minlength=2)
    if (counts == 0).any():
        raise ValueError(f"satu kelas kosong: Normal={counts[0]}, Aritmia={counts[1]}")
    return {c: len(y) / (2.0 * counts[c]) for c in (0, 1)}


def compile_model(model, lr: float = 0.0):
    """lr > 0 untuk ablasi T12. 0 = bawaan Adam (1e-3) = jalur terkunci."""
    model.compile(
        optimizer=optimizers.Adam(learning_rate=lr) if lr else "adam",
        loss="binary_crossentropy",
        metrics=[
            metrics.Recall(name="recall"),
            metrics.Precision(name="precision"),
            metrics.AUC(name="auc"),
        ],
    )
    return model


class RataBobotTerbaik(callbacks.Callback):
    """Rata-rata bobot N epoch ber-`monitor` tertinggi (ablasi T7).

    Dipasang SESUDAH EarlyStopping supaya menimpa hasil restore_best_weights.
    Aman tanpa penghitungan ulang statistik: model ini tidak punya BatchNorm.
    """

    def __init__(self, monitor: str, n: int):
        super().__init__()
        self.monitor, self.n = monitor, n
        self.riwayat = []

    def on_epoch_end(self, epoch, logs=None):
        self.riwayat.append((float((logs or {})[self.monitor]), epoch,
                             [w.copy() for w in self.model.get_weights()]))

    def on_train_end(self, logs=None):
        teratas = sorted(self.riwayat, key=lambda t: -t[0])[:self.n]
        self.epoch_terpakai = sorted(e for _, e, _ in teratas)
        print(f"[swa] epoch dirata-rata: {self.epoch_terpakai} "
              f"dari {len(self.riwayat)} epoch")
        self.model.set_weights([np.mean(w, axis=0)
                                for w in zip(*[b for _, _, b in teratas])])


def train(model, train_data: dict, val_data: dict,
          epochs: int = EPOCHS, batch_size: int = BATCH_SIZE,
          pakai_class_weight: bool = True, swa_n: int = 0, lr: float = 0.0):
    """pakai_class_weight=False untuk ablasi K1/T1 (docs/2026-09-19-fitur-design.md).

    Bawaan True = nilai terkunci, tidak berubah. P1 Tabel 4 mengukur trade-off-nya
    di varian yang HANYA beda ini: recall -7 poin, precision +31 poin.

    swa_n > 0 untuk ablasi T7: alih-alih memungut argmax `val_auc` (lotere epoch
    oneDNN), rata-ratakan bobot swa_n epoch terbaik. 0 = jalur terkunci.
    """
    compile_model(model, lr)
    cb = [callbacks.EarlyStopping(
        monitor=EARLY_STOP_MONITOR, mode="max",
        patience=EARLY_STOP_PATIENCE, restore_best_weights=True,
    )]
    if swa_n > 0:
        cb.append(RataBobotTerbaik(EARLY_STOP_MONITOR, swa_n))
    return model.fit(
        [train_data["X_morph"], train_data["X_rr"]], train_data["y"],
        validation_data=([val_data["X_morph"], val_data["X_rr"]], val_data["y"]),
        class_weight=make_class_weights(train_data["y"]) if pakai_class_weight else None,
        epochs=epochs, batch_size=batch_size, callbacks=cb, verbose=2,
    )
