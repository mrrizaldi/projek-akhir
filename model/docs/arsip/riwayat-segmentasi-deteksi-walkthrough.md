# Riwayat: Walkthrough Fase 6b — biaya segmentasi on-device

**Dokumen sumber:** [`segmentasi-deteksi-walkthrough.md`](../segmentasi-deteksi-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Indeks R 94 → 132
- **Perubahan:** dokumen ditulis saat window 90/160 (R di indeks 94). Sejak window
  128/128 dikunci 18 Sep 2026, R mendarat di indeks 132. Dokumen sempat membiarkan
  angka 94 dengan catatan "merekam pengukuran pada window lama"; dokumen aktif kini
  menyatakan rumus `WIN_PRE + 4` dan memberi label kondisi ukur pada tabel yang memang
  diukur di baseline.
- **Alasan / bukti:** `config.py` (`WIN_PRE`, `R_IN_WINDOW`), `firmware/include/ecg_preproc.h`.

## Saran augmentasi geseran → Fase 6c
- **Perubahan:** §2 semula menutup dengan saran "melatih ulang dengan augmentasi geseran
  acak ±4 sampel" sebagai pekerjaan lanjutan. Saran itu dikerjakan sebagai augmentasi
  jitter empiris (Fase 6c) dan kini dirujuk ke `jitter-walkthrough.md`.

## Pengukuran ulang dengan model berlaku (13 Okt 2026)
- **Perubahan:** `scripts/eval_detected_segmentation.py` dijalankan ulang (keluaran ke
  direktori sementara, artefak repo tidak ditimpa) dengan model berlaku. Hasil
  ditambahkan sebagai kolom "berlaku": deteksi recall 0,7279, precision 0,5869, F1
  0,6499; recall sistem 0,6035; 50,4% deteksi palsu → 1.106 alarm palsu tambahan.
  Angka baseline dipertahankan sebagai pembanding.
- **Catatan:** `artifacts/metrics/fase6b_segmentasi_deteksi.csv` di repo masih hasil
  run baseline (12 Sep 2026), dan baris "D. Pembanding Fase 6" di skrip mencetak angka
  baseline yang ditulis tetap (0,6661/0,4919/0,5659), bukan dibaca dari
  `fase6_metrics_fp32.csv`.
