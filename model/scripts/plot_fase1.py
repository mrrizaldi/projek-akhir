"""Fase 1 — verifikasi preprocessing (yang butuh mata manusia).

    python scripts/plot_fase1.py 100

DoD visual (PRD Fase 1):
  1. raw vs bandpass 5 detik  → baseline wander hilang, bentuk QRS tetap.
  2. R-peak Pan-Tompkins vs anotasi 10 detik → cocok dalam +-150 ms.
  3. 5 window Normal ditumpuk → mirip; 5 window V → jelas beda (lebar, tanpa P).

TODO (manual): implementasi plotting. Panggil fungsi dari src/preprocessing.py.
"""
