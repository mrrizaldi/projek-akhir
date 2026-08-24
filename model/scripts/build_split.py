"""Fase 3 — rakit split inter-patient DS1/DS2 dari per_record/*.npz.

    make split       (atau: python scripts/build_split.py)

Keluaran: data/processed/train.npz (DS1) & test.npz (DS2), key
    X_morph float32 [N,250,1]   (channel dim untuk Conv1D)
    X_rr    float32 [N,3]
    y       int8    [N]
    records int32   [N]         asal record tiap beat (untuk metrik per-record)

DoD (PRD Fase 3): set(DS1), set(DS2), set(PACED_EXCLUDED) disjoint, total 48.
JANGAN shuffle lalu split ulang — split sudah ditentukan per record.

TODO (manual): panggil src.dataset.build_split(). Daftar record dari config.py
(cross-check ke de Chazal 2004 dulu — gated decision).
"""
