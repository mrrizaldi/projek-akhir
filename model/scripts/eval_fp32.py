"""Fase 6 — evaluasi float32 di DS2 (angka klaim ilmiah primer).

    make eval        (atau: python scripts/eval_fp32.py)

Threshold dipakai apa adanya dari Fase 5 — JANGAN di-tuning pakai DS2.
Kelas positif = Aritmia. Laporkan recall Aritmia, bukan cuma accuracy.

TODO (manual): muat test.npz + model_fp32.keras, panggil
src.evaluate.evaluate_fp32(), simpan confusion matrix (PNG + angka) dan tabel
metrik CSV ke artifacts/metrics/. Angka ini jadi baris "float32" tabel delta.
"""
