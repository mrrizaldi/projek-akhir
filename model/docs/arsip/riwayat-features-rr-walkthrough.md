# Riwayat: Walkthrough `src/features_rr.py` — Fase 2

**Dokumen sumber:** [`features-rr-walkthrough.md`](../features-rr-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Angka dataset pada window 90/160 (250 sampel)
- **Perubahan:** §4 semula memuat `44 record 100.619 beat, Normal 90.018 (89,5%),
  Aritmia 10.601 (10,5%), dibuang 114 = 88 + 26 beat tepi`. Pada window 128/128 angka
  data bersih menjadi 100.624 / 90.023 / 10.601, dibuang 109 = 88 + 21.
- **Alasan / bukti:** window dikunci 128/128 pada 18 Sep 2026 (lihat
  [`riwayat-preprocessing-walkthrough.md`](riwayat-preprocessing-walkthrough.md)).
  Angka baru dihitung ulang dari `valid_beat_indices` atas 44 record (Okt 2026).

## Implementasi MCU
- **Perubahan:** dokumen semula merencanakan "di MCU nanti: ring buffer 10 float +
  running_sum, O(1) per beat". Port C yang berlaku (`ecg_rr_features`) menjumlahkan
  ulang ≤10 interval dari riwayat indeks R tiap beat.
- **Alasan / bukti:** `firmware/src/ecg_pipeline.cpp`.

## Jumlah test
- **Perubahan:** tabel skrip pendukung semula menulis "16 test — 7 di antaranya";
  diganti rujukan ke `tests/test_features_rr.py` karena jumlah test terus bertambah.
