# Riwayat: Walkthrough `src/train.py` — Fase 5

**Dokumen sumber:** [`train-walkthrough.md`](../train-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Angka latih pada window 90/160, tanpa augmentasi
- **Perubahan:** §0–§2 dan §5 semula memakai DS1 50.965 beat → train 40.617
  (4.105 aritmia) / val 10.348 (1.046 aritmia); class weight
  $w_0 = 40617/(2·36512) = 0{,}556$, $w_1 = 40617/(2·4105) = 4{,}947$; hasil
  `VAL @ threshold 0.5: TP=728 FN=318 FP=67 TN=9235`. Angka VAL itu dan tabel kurva
  epoch 4/12 tetap ada di dokumen sumber dengan label kondisi ukur.
- **Alasan / bukti:** window 128/128 + augmentasi jitter ×3 (18 Sep 2026). Angka
  berlaku dihitung ulang dari `train.npz` dan `artifacts/model_fp32.keras` (Okt 2026):
  train 121.857 / val 31.047, VAL @0,80 TP=2052 FN=1086 FP=743 TN=27166.

## Kurva yang tidak ditinjau ulang setelah augmentasi (Fase G, 19 Sep 2026)
- **Perubahan:** §6b semula berjudul "Fase G — kurva yang tidak pernah benar-benar
  dilihat" dan menceritakan bahwa setelah window 256 + augmentasi dikunci (18 Sep),
  kurva tidak dilihat ulang sampai diagnosis Fase G/T7 menemukan `val_auc`
  memuncak di epoch 0.
- **Alasan / bukti:** [`2026-09-19-faseG-changelog.md`](2026-09-19-faseG-changelog.md) §2.

## Alasan learning rate 1e-3 diganti (19 Sep 2026)
- **Perubahan:** §7 semula beralasan "tidak menyetel learning rate: menambah knob yang
  belum terbukti perlu = ruang tuning yang harus dipertanggungjawabkan", lalu diberi
  catatan "⚠️ Alasan ini gugur 19 Sep 2026": dengan konfigurasi terkunci, model
  produksi adalah hasil satu epoch. Nilai tetap 1e-3, dengan dasar baru: ablasi
  3 LR × 3 seed + 39 pasien held-out menunjukkan LR lebih rendah menukar recall S
  dengan recall V dan F.
- **Alasan / bukti:** [`2026-09-19-faseG-changelog.md`](2026-09-19-faseG-changelog.md).

## Ambang 0,04 untuk rerata 3 seed
- **Perubahan:** dokumen semula menulis "Selama ini '3 seed' dianggap cukup ...
  Ternyata rerata 3 seed pun bergoyang ~0,04". Dokumen aktif menyatakan faktanya
  langsung (batch 1 F1 0,6911 vs batch 2 0,6535, konfigurasi dan seed identik).

## Threshold di `make train`
- **Perubahan:** §7 semula menulis threshold "tetap 0,5" di fase ini.
  `scripts/train_model.py` kini mencetak ringkasan VAL pada `THRESHOLD` (0,80).
