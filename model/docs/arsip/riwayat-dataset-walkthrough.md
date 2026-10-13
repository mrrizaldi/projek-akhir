# Riwayat: Walkthrough `src/dataset.py` — Fase 3

**Dokumen sumber:** [`dataset-walkthrough.md`](../dataset-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Angka `make split` pada window 90/160, tanpa augmentasi
- **Perubahan:** §4 semula:
  `DS1 22 record 50965 beat, Normal 45814 (89,9%), Aritmia 5151 (10,1%)`;
  `DS2 22 record 49654 beat, Normal 44204 (89,0%), Aritmia 5450 (11,0%)`;
  `X_morph (50965, 250, 1) / (49654, 250, 1)`; total 100.619. DS2 aritmia ~nol
  menyebut rec 117 (0,1%).
- **Alasan / bukti:** window 128/128 + augmentasi jitter DS1 ×3 (18 Sep 2026). Angka
  berlaku dibaca langsung dari `data/processed/train.npz` dan `test.npz` (Okt 2026):
  DS1 152.904, DS2 49.656.

## Validation split
- **Perubahan:** dokumen semula menulis DS1 "nanti" dibelah train/val di Fase 5.
  Kini fungsi itu ada di `src/dataset.py` (`split_train_val`, `VAL_RECORDS`), dan
  `build_split_multi` ditambahkan untuk split lintas database (Fase A, 19 Sep 2026).
