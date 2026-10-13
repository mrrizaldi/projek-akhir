# Riwayat: Walkthrough `src/quantize.py` — Fase 7

**Dokumen sumber:** [`quantize-walkthrough.md`](../quantize-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Angka model baseline (window 250, threshold 0,35)
- **Perubahan:** dokumen semula memuat hasil kuantisasi model baseline. Dokumen aktif
  kini memuat model berlaku (window 256 + jitter, threshold 0,80; 22,94 KB).
- **Angka lama:** ukuran 23.456 byte = 22,91 KB. Skala/zero point: morfologi
  0,042865/−24, ritme 0,042874/−109, output 1/256/−128. Tabel delta:

  | Metrik | Float32 | INT8 | Delta |
  |---|---|---|---|
  | accuracy | 0,8878 | 0,8984 | +0,0106 |
  | precision | 0,4919 | 0,5302 | +0,0383 |
  | recall | 0,6661 | 0,6549 | −0,0112 |
  | F1 | 0,5659 | 0,5859 | +0,0201 |
  | specificity | 0,9152 | 0,9284 | +0,0133 |
  | AUC | 0,8866 | 0,8862 | −0,0004 |
  | TP/FN/FP/TN | 3630/1820/3750/40454 | 3569/1881/3163/41041 | — |

- **Alasan / bukti:** `artifacts/metrics/fase7_delta.csv`, `firmware/include/model_int8.h`.

## Klaim yang diperbaiki
- **Tensor int32:** dokumen menyebut `{'int8': 30, 'int32': 12}` dan menyebut semua
  int32 sebagai bias. Pada model berlaku `{'int8': 39, 'int32': 16}`, terdiri atas bias
  dan konstanta bentuk untuk op `Squeeze`/reshape.
- **Urutan input `predict_tflite`:** dokumen menunjukkan pengurutan menurut jumlah
  dimensi. Kode kini mengurutkan menurut jumlah elemen, karena di model deploy input
  ritme `(1,1,3)` dan morfologi `(1,256,1)` sama-sama 3-D.
- **Lupa dequantize:** klaim "semua terprediksi 1" tidak tepat; yang terjadi q ≥ 1
  (p ≳ 0,5) jadi Aritmia.
- **QAT:** kalimat lama "(<1,21% delta recall, 17,84 KB)" tidak cocok dengan angka mana
  pun di dokumen; diganti angka model berlaku.
- **`AveragePooling1D`:** dulu dicoba sebagai pengganti GAP lalu ditolak (recall DS2
  0,655 → 0,528 pada model baseline); dokumen aktif menyatakannya sebagai alternatif
  yang tidak dipakai.
- **Jumlah test:** "49 test — 7 di antaranya" (jumlah suite saat Fase 7) diganti
  rujukan ke `tests/test_quantize.py` (9 test).
