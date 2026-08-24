"""Fase 2 — ekstrak beat + label biner + fitur RR, simpan per record.

    make prep        (atau: python scripts/prep_beats.py)

Keluaran: data/processed/per_record/<rec>.npz dengan key
    windows   float32 [K,250]   window ter-z-score
    rr        float32 [K,3]     RR_prev, RR_ratio, dRR
    labels    int8    [K]       0=Normal, 1=Aritmia
    symbols   <U2     [K]       simbol MIT-BIH asli (audit error)
    n_dropped int32   skalar    beat dibuang (out-of-bound / tanpa RR_prev)

DoD (PRD Fase 2): len(windows)==len(rr)==len(labels); distribusi label dicetak
per record; mapping AAMI terdokumentasi (LBBB/RBBB→N adalah keputusan sadar).

TODO (manual): loop record, panggil src.io_mitdb + src.preprocessing +
src.features_rr, simpan .npz. Segmentasi pakai R-peak ANOTASI, bukan Pan-Tompkins.
"""
