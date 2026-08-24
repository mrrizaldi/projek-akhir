"""Fase 7 — PTQ INT8, evaluasi ulang di DS2 identik, tabel delta.

    make quantize    (atau: python scripts/quantize_int8.py)

DoD (PRD Fase 7): model_int8.tflite < 20 KB; metrik dihitung dengan cara
IDENTIK Fase 6; tabel delta float32 vs INT8 lengkap.

Jebakan: representative dataset harus yield DUA input (window + RR) dan
mencakup KEDUA kelas secara stratified — kalau cuma Normal, rentang aktivasi
kelas Aritmia tidak terkalibrasi.

TODO (manual): panggil src.quantize.representative_dataset_gen /
quantize_int8 / evaluate_int8, simpan artifacts/model_int8.tflite +
artifacts/metrics/tabel_delta.csv.
"""
