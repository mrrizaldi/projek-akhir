# Riwayat: Walkthrough `src/model.py` — Fase 4

**Dokumen sumber:** [`model-walkthrough.md`](../model-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Bentuk tensor pada window 250
- **Perubahan:** tabel bentuk semula 250 → 125 → 62 → 31 (pembulatan ke bawah),
  tensor akhir `(31, 32)` = 992 angka, `Flatten` → Dense 992×16 + 16 = 15.888,
  total ~21.700. R-peak disebut di indeks ~94.
- **Alasan / bukti:** window 128/128 (18 Sep 2026) → 256 → 128 → 64 → 32, R di 132.
  Jumlah parameter tetap 6.417.

## Batas ukuran model 20 KB → 25 KB
- **Perubahan:** dokumen semula menulis target INT8 "< 20 KB" (DoD PRD) dan
  memperkirakan "INT8 nanti ≈ 6,4 KB bobot + overhead".
- **Alasan / bukti:** varian deploy yang benar di TFLM (tanpa `MEAN` dan tanpa shape
  dinamis) melampaui 20 KB; batas dinaikkan ke 25 KB atas persetujuan user
  (`MAX_MODEL_KB = 25`). Ukuran terukur 22,94 KB (`artifacts/metrics/fase7_delta.csv`).

## Threshold dan dropout
- **Perubahan:** dokumen semula menyebut threshold 0,5 sebagai default yang
  "nanti" dikalibrasi, dan dropout "siap dipakai kalau kurva Fase 5 bicara lain".
  Kondisi berlaku: threshold 0,80 dikalibrasi di VAL; dropout sudah diuji di Fase 5
  dan tetap 0,0. Rasio data latih semula ditulis 50.965 : 6.417 ≈ 8.
