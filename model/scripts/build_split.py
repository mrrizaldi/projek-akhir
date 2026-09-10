"""Fase 3 — rakit split inter-patient DS1/DS2 dari per_record/*.npz.

    make split       (atau: python scripts/build_split.py)

Keluaran: data/processed/train.npz (DS1) & test.npz (DS2), key
    X_morph float32 [N,250,1]   (channel dim untuk Conv1D)
    X_rr    float32 [N,3]
    y       int8    [N]
    records int32   [N]         asal record tiap beat (untuk metrik per-record)

DoD (PRD Fase 3): set(DS1), set(DS2), set(PACED_EXCLUDED) disjoint, total 48.
JANGAN shuffle lalu split ulang — split sudah ditentukan per record.

Penjelasan alur & alasan: docs/dataset-walkthrough.md
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROCESSED_DIR  # noqa: E402
from src.dataset import build_split  # noqa: E402


def _ringkas(nama: str, d: dict) -> None:
    y = d["y"]
    n, n_arr = len(y), int(y.sum())
    print(f"{nama:<6} {len(np.unique(d['records'])):>3} record  {n:>7} beat  "
          f"Normal {n - n_arr:>6} ({100 * (n - n_arr) / n:.1f}%)  "
          f"Aritmia {n_arr:>6} ({100 * n_arr / n:.1f}%)")


def main() -> None:
    train, test = build_split()
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    np.savez_compressed(os.path.join(PROCESSED_DIR, "train.npz"), **train)
    np.savez_compressed(os.path.join(PROCESSED_DIR, "test.npz"), **test)

    _ringkas("DS1", train)
    _ringkas("DS2", test)
    print(f"X_morph {train['X_morph'].shape} / {test['X_morph'].shape}   "
          f"X_rr {train['X_rr'].shape} / {test['X_rr'].shape}")


if __name__ == "__main__":
    main()
