# Riwayat: Walkthrough `scripts/prep_beats.py` — Fase 2 (eksekusi)

**Dokumen sumber:** [`prep-beats-walkthrough.md`](../prep-beats-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Angka pada window 90/160, tanpa augmentasi
- **Perubahan:** §5 semula: `44 record 100.619 beat, Normal 90.018, Aritmia 10.601,
  buang 114`; sebaran buang `{3 beat: 26 record, 2 beat: 18 record}`; batas akhir
  `r <= 649.840` (jendela +160), contoh rec 223 `r[-1] = 649.849` dibuang karena lewat
  9 sampel; syarat awal `r >= 90`. Soal cek pemahaman no. 3 memakai rec 223 dan
  `WIN_POST` 160 → 150.
- **Alasan / bukti:** window dikunci 128/128 (18 Sep 2026). Angka baru dihitung ulang
  dari `valid_beat_indices` (Okt 2026): 100.624 beat, buang 109 = 88 + 21.

## Kode yang berkembang sejak dokumen ditulis
- **Perubahan:** dokumen semula menampilkan `process_record` tanpa `db`,
  `selaraskan_r`, dan `jitter`, serta `rr = compute_rr_features(r)[idx]` langsung
  (kini lewat `rakit_fitur_ritme`). `available_records` semula membaca `.hea` saja
  dari `raw_dir`; kini alias `records_tersedia(db)` yang menuntut `.hea/.dat/.atr`.
  `valid_beat_indices` kini punya syarat opsional `PA_RR_RATIO`.
- **Alasan / bukti:** augmentasi jitter Fase 6c (18 Sep 2026) dan dataset tambahan
  svdb/incartdb Fase A (19 Sep 2026); lihat
  [`2026-09-19-multidataset-plan.md`](2026-09-19-multidataset-plan.md).

## Per-kelas AAMI pada konfigurasi lama
- **Perubahan:** §3 semula mengutip recall per kelas "V 0,9332 / S 0,3034 / F 0,1675"
  (Fase 6 pada window 250, threshold 0,35). Diganti rujukan ke
  `evaluate-walkthrough.md` §5 karena angka itu bukan milik model terkunci.
