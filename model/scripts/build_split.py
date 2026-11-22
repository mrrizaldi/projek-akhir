import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROCESSED_DIR
from src.dataset import build_split, build_split_multi


def _summarize(name: str, d: dict) -> None:
    y = d["y"]
    n, n_arr = len(y), int(y.sum())
    print(f"{name:<6} {len(np.unique(d['records'])):>3} records  {n:>7} beats  "
          f"Normal {n - n_arr:>6} ({100 * (n - n_arr) / n:.1f}%)  "
          f"Arrhythmia {n_arr:>6} ({100 * n_arr / n:.1f}%)")


def main_multi() -> None:
    hasil = build_split_multi()
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    file_label = {"train": "train_multi.npz", "ds2": "test_ds2.npz"}
    for name, d in sorted(hasil.items()):
        f = file_label.get(name, f"test_{name.replace('_test','')}.npz")
        np.savez_compressed(os.path.join(PROCESSED_DIR, f), **d)
        _summarize(name, d)
        print(f"        -> {f}")


def main() -> None:
    train, test = build_split()
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    np.savez_compressed(os.path.join(PROCESSED_DIR, "train.npz"), **train)
    np.savez_compressed(os.path.join(PROCESSED_DIR, "test.npz"), **test)

    _summarize("DS1", train)
    _summarize("DS2", test)
    print(f"X_morph {train['X_morph'].shape} / {test['X_morph'].shape}   "
          f"X_rr {train['X_rr'].shape} / {test['X_rr'].shape}")


if __name__ == "__main__":
    if "--combined" in sys.argv:
        main_multi()
    else:
        main()
