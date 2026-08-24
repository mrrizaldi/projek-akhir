"""Fase 5 — latih model hybrid di DS1, simpan model_fp32.keras + kurva.

    make train       (atau: python scripts/train_model.py)

DS2 HARAM di sini — validation diambil dari DS1 saja.
Pantau recall Aritmia + AUC, bukan accuracy (data timpang).

TODO (manual): muat train.npz, panggil src.model.build_hybrid_model() dan
src.train.train(), simpan artifacts/model_fp32.keras +
artifacts/metrics/history.png. Lock np.random & tf.random ke SEED sebelum latih.
"""
