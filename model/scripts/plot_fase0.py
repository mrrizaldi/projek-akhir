"""Fase 0 — verifikasi loader: overlay R-peak anotasi di atas sinyal.

    python scripts/plot_fase0.py 100

DoD Fase 0 (PRD): garis R-peak mendarat PAS di puncak R. Kalau meleset →
loader/anotasi salah baca (cek kanal MLII bukan selalu index 0).

TODO (manual): pindahkan kode eksplorasi dari src/io_mitdb.py ke sini, lalu
panggil src.io_mitdb.load_record() — jangan baca wfdb langsung dari sini.
"""
