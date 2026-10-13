# Riwayat: Walkthrough `src/evaluate.py` — Fase 6

**Dokumen sumber:** [`evaluate-walkthrough.md`](../evaluate-walkthrough.md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari dokumen
sumber saat formalisasi dokumentasi (Okt 2026).

## Fase 6 pertama — window 90/160, tanpa augmentasi, threshold 0,35
- **Perubahan:** dokumen semula ditulis untuk model baseline. Sejak 18 Sep 2026 model
  yang berlaku memakai window 128/128 + augmentasi jitter, dan threshold dikalibrasi
  ulang menjadi 0,80. Dokumen aktif kini memuat angka model berlaku; ringkasan baseline
  tetap ada sebagai "Model pembanding".
- **Alasan / bukti:** ablasi Fase 6c (`jitter-walkthrough.md` §5), `config.py`
  (`WIN_PRE`, `WIN_POST`, `THRESHOLD`), `artifacts/metrics/fase6_metrics_fp32.csv`.
- **Sweep VAL lama** (VAL bersih, 10.348 beat), kriteria sama:

  | thr | recall | precision | F1 | specificity |
  |---|---|---|---|---|
  | 0,20 | 0,8881 | 0,5038 | 0,6429 | 0,9016 |
  | 0,30 | 0,8375 | 0,7436 | 0,7878 | 0,9675 |
  | **0,35** (terpilih) | 0,8117 | 0,8132 | 0,8124 | 0,9790 |
  | 0,40 | 0,7725 | 0,8596 | 0,8137 | 0,9858 |
  | 0,50 | 0,6960 | 0,9157 | 0,7909 | 0,9928 |
  | 0,70 | 0,5010 | 0,9632 | 0,6591 | 0,9978 |

  F1 maksimum di 0,40 (0,8137); 0,35 berselisih 0,0013 dan recall +3,9 poin → tie-break
  memilih 0,35.
- **Hasil DS2 lama** (49.654 beat, 5.450 aritmia): TP=3630 FN=1820 FP=3750 TN=40454;
  recall 0,6661, precision 0,4919, F1 0,5659, specificity 0,9152, accuracy 0,8878,
  AUC 0,8866. Accuracy model berada di bawah tebak-Normal.
- **Per kelas lama:** V 0,9332 / S 0,3034 / F 0,1675 / Q 0,5714; FP rate N 0,0848.
- **Per pasien lama:** median recall 0,8933 (21 pasien); rec 232 0,2042 (recall S di
  232 0,2042 vs 0,6044 di pasien lain), rec 100 0,2353, rec 234 0,3019.
- **Narasi lama VAL→DS2:** recall 0,8117 → 0,6661 dan precision 0,8132 → 0,4919
  ditafsirkan sebagai penurunan inter-patient yang wajar. Pada model berlaku recall DS2
  justru di atas VAL, jadi narasi itu tidak dipakai lagi.

## Ralat kecil
- **Perubahan:** accuracy tebak-Normal ditulis 0,8903; nilai yang benar 0,8902
  (44.204/49.654 pada baseline, 44.206/49.656 pada model berlaku).
- **Perubahan:** baris skrip pendukung menyebut "42 test" (jumlah suite saat Fase 6);
  diganti rujukan ke `tests/test_evaluate.py` (8 test).
