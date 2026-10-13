# Riwayat: Walkthrough `src/preprocessing.py` — Fase 1

**Dokumen sumber:** [`preprocessing-walkthrough.md`](../preprocessing-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Window 90/160 → 128/128 (18 Sep 2026)
- **Perubahan:** §4 semula menjelaskan window $[R-90,\ R+160)$ = 250 sampel = 694 ms
  (R di indeks 90; tampak di indeks 94 setelah filter), dengan catatan sisipan
  "Diperbarui 18 Sep 2026: window sekarang 128/128". Tabel anatomi lama: P + PR
  "90 sampel = 250 ms", ST + T "160 sampel = 444 ms". Kontrak keluaran `(N, 250)`,
  $L = 250$ pada z-score, dan soal cek pemahaman "`WIN_POST` 160 → 200".
- **Alasan / bukti:** ablasi 3 seed (Fase 6c): F1 DS2 0,5660 (90/160) → 0,6911
  (128/128); varian 112/144 setara baseline. Detail di
  [`jitter-walkthrough.md`](../jitter-walkthrough.md) §5–6 dan
  [`2026-09-18-robustness-changelog.md`](2026-09-18-robustness-changelog.md).

## Pan-Tompkins dari rencana menjadi detektor on-device
- **Perubahan:** dokumen semula menulis Pan-Tompkins "nanti" jalan di ESP32 dan
  "kalau nanti dipakai untuk segmentasi on-device, delay harus dikompensasi".
  Kondisi berlaku: port C (`ecg_detect_r`) sudah berjalan, offset dikompensasi
  `PT_DETECTOR_OFFSET = 38` (median DS1, Fase 6b).
- **Alasan / bukti:** [`segmentasi-deteksi-walkthrough.md`](../segmentasi-deteksi-walkthrough.md).
