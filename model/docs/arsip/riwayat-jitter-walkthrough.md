# Riwayat: Walkthrough jitter — ketahanan terhadap error segmentasi

**Dokumen sumber:** [`jitter-walkthrough.md`](../jitter-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Hipotesis "250 sudah cukup"
- **Perubahan:** §6 semula ditulis sebelum ablasi window, dengan dugaan bahwa
  `WIN_PRE = 90` sudah memuat gelombang P dan 128 milik paper hanya membeli garis
  dasar. Setelah ablasi 3 seed, dokumen menandai hipotesis itu "salah". Dokumen aktif
  kini menyajikannya sebagai argumen tandingan yang dibantah ablasi.
- **Alasan / bukti:** `w128` 0,6775 vs `bersih` 0,5660; `w112` (256 sampel, T lebih
  panjang) setara baseline. `artifacts/metrics/ablasi/ablasi.csv`.

## Batch satu seed
- **Perubahan:** batch ablasi pertama dijalankan satu kali per varian. Pengulangan
  dengan seed dan kode identik memberi angka berbeda (jitter 0,6209 vs 0,5882), sehingga
  semua varian diulang 3 seed (42, 7, 13). Run pertama varian HOS sempat terbaca
  "HOS merugikan"; dengan tiga seed klaim itu tidak bertahan.

## Penguncian konfigurasi (18 Sep 2026)
- **Perubahan:** §5 semula mencatat kandidat pemenang tanpa menguncinya ke `config.py`.
  Atas persetujuan user, bawaan dikunci: `WIN_PRE/WIN_POST = 128/128`,
  `JITTER_MODEL = "empiris"`, `JITTER_SALINAN = 2`, `THRESHOLD = 0,80`. Follow-up ikut
  diuji: `w128b` (128/128) ≈ `w128` (128/127), dan `w128s3` (3 salinan) lebih buruk.
  Baris kedua varian itu ditambahkan ke tabel hasil dokumen aktif.
- **Perubahan:** contoh perintah ablasi semula mengandalkan bawaan 90/160 untuk varian
  `bersih`, `jitter`, dan `hos`. Karena bawaan kini 128/128, perintah di dokumen aktif
  menyebut `PA_WIN_PRE=90 PA_WIN_POST=160` secara eksplisit.
- **Alasan / bukti:** `config.py`, `model/CLAUDE.md` tabel decision point,
  `artifacts/metrics/ablasi/ablasi.csv` (tag `w128b`, `w128s3`).
