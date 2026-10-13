# Walkthrough Fase 6b — biaya segmentasi on-device

> **Ruang lingkup:** mengukur berapa yang hilang ketika window dipotong dari deteksi Pan-Tompkins, bukan dari R-peak anotasi, dan menetapkan urutan penyelarasan R-peak yang wajib diikuti firmware.
> **Kode terkait:** `scripts/eval_detected_segmentation.py`, `src/evaluate.py` (`pair_detected`), `config.py` (`PT_DETECTOR_OFFSET`, `PT_REFINE_WIN`, `GROUP_DELAY_SAMPLES`, `PT_REFRACTORY_MS`), `firmware/include/ecg_preproc.h`
> **Prasyarat:** [`evaluate-walkthrough.md`](evaluate-walkthrough.md) (Fase 6)

Dokumen belajar, bukan spesifikasi. Eksperimen tambahan di luar PRD, menjawab
pertanyaan yang tidak terjawab oleh Fase 6.

Reproduksi:

```
cd model
python scripts/eval_detected_segmentation.py
```

---

## 0. Pertanyaannya

Semua angka Fase 6 diukur dengan window yang dipotong dari **R-peak anotasi
kardiolog** — posisi yang sempurna. Di alat, window dipotong dari **hasil
deteksi Pan-Tompkins**. Dua hal berubah sekaligus:

1. Beat yang **tidak terdeteksi** tidak pernah sampai ke model
2. Beat yang terdeteksi punya posisi R yang **sedikit meleset**

Berapa biayanya? Tanpa angka ini, recall Fase 6 berlaku untuk laboratorium,
bukan untuk alat.

**Disiplin:** offset detektor dikalibrasi di **DS1**; DS2 tidak menyetel apa
pun. Model float32 (bukan INT8) supaya yang berubah hanya segmentasi. DS2
dilihat kedua kalinya di sini — murni mengukur, tidak ada parameter diambil
darinya.

---

## 1. Tiga koreksi yang harus dilakukan firmware

### a. Offset detektor (~38 sampel)

Pan-Tompkins bekerja atas sinyal yang sudah difilter, punya bandpass sendiri,
turunan, dan integrasi 150 ms — semuanya menambah delay. Terukur di DS1 atas
47.848 pasangan:

```
median 38 sampel (105,6 ms), std 13,0, p10 21, p90 52
```

Median-nya dikompensasi; std 13 sampel adalah jitter yang tersisa.

### b. Penyelarasan ke puncak sebenarnya

Kompensasi median saja menyisakan jitter ±13 sampel. Obatnya murah: setelah
detektor menunjuk lokasi kasar, cari **puncak maksimum** di ±25 sampel (±70 ms)
sekitarnya.

### c. Mengembalikan group delay filter (+4 sampel)

Ini yang paling halus, dan paling merusak kalau terlewat.

Window training dipotong di `r_anotasi - WIN_PRE`, sedangkan sinyal yang
difilter menggeser puncak R **+4 sampel** (JEBAKAN Fase 1). Jadi saat training,
R selalu mendarat di **`WIN_PRE + 4`** — indeks **132** pada window 128/128
yang berlaku (94 pada window baseline 90/160).

Penyelarasan di (b) menemukan puncak di sinyal terfilter, yaitu `r + 4`. Kalau
langsung dipakai, window mulai di `r + 4 - WIN_PRE` dan R mendarat di
`WIN_PRE` (128), bukan 132. Karena itu hasil penyelarasan dikurangi 4
(`GROUP_DELAY_SAMPLES`).

---

## 2. Model SANGAT peka pada posisi R

Geser 4 sampel — 11 milidetik — ke arah mana pun. Diukur pada model baseline
(window 90/160, tanpa augmentasi, threshold 0,35), sehingga posisi yang benar
adalah indeks 94:

| Posisi R di window | recall | precision | F1 |
|---|---|---|---|
| 90 | 0,8952 | **0,1243** | 0,2182 |
| **94** (seperti training) | 0,6821 | **0,4794** | **0,5631** |
| 98 | 0,9007 | **0,1249** | 0,2194 |

Precision jatuh **hampir 4×** untuk geseran 11 ms, dan simetris ke dua arah.

### Kenapa sepeka itu, padahal ada GlobalAveragePooling?

GAP memang membuang informasi *posisi absolut*, tapi lapisan sebelum GAP punya tiga
`MaxPooling1D(2)` — stride total **8**. Geseran 4 sampel = **setengah bin
pooling**. Sampel yang tadinya jatuh di bin A pindah ke bin B, jadi representasi
yang masuk GAP benar-benar berubah fase. Model tidak pernah melihat variasi ini
saat training karena semua window disegmentasi dari anotasi yang presisi.

Konsekuensi praktis: **firmware wajib menaruh R di indeks `WIN_PRE + 4`**
(132), dan itu bukan detail kosmetik. Kepekaan ini juga menjadi dasar Fase 6c:
model yang berlaku dilatih dengan posisi R yang digeser sesuai residu detektor
terukur, supaya tidak bergantung pada fase window yang persis. Lihat
[`jitter-walkthrough.md`](jitter-walkthrough.md).

---

## 3. Hasil

Angka di bawah diukur untuk dua model: **baseline** (window 90/160, tanpa
augmentasi, threshold 0,35) dan **model berlaku** (window 128/128, augmentasi
jitter, threshold 0,80; kondisi ukur: skrip yang sama, 13 Okt 2026).
Statistik detektor tidak bergantung pada model, jadi sama untuk keduanya:

```
Detektor di DS2: 47.074 terdeteksi, 2.638 terlewat (sensitivity 0,9469),
                 2.194 deteksi palsu
```

### A. Klasifikasi pada beat yang berhasil terdeteksi

| | baseline: anotasi | baseline: deteksi | berlaku: anotasi | berlaku: deteksi |
|---|---|---|---|---|
| recall | 0,6661 | **0,6821** | 0,6996 | **0,7279** |
| precision | 0,4919 | **0,4794** | 0,6235 | **0,5869** |
| F1 | 0,5659 | **0,5631** | 0,6594 | **0,6499** |

Pada kedua model, F1 dengan segmentasi deteksi berselisih kurang dari 0,01 dari
F1 dengan anotasi. **Segmentasi on-device tidak merusak klasifikasi** — asalkan
ketiga koreksi di §1 dilakukan.

### B. Tingkat sistem

```
                aritmia asli   tertangkap   recall sistem
baseline           5.453         3.084         0,5656   (anotasi 0,6661)
berlaku            5.453         3.291         0,6035   (anotasi 0,6996)
```

Recall sistem turun sekitar 10 poin dari recall dengan anotasi. Seluruh
kerugian berasal dari beat yang tidak pernah terdeteksi, bukan dari window yang
bergeser: pada beat yang terdeteksi, recall justru sedikit lebih tinggi (A).

### C. Deteksi palsu

2.194 window tanpa beat asli. Pada baseline **43,9%** diklasifikasi Aritmia →
964 alarm palsu tambahan di luar 3.349 yang sudah ada. Pada model berlaku
**50,4%** → 1.106 alarm palsu tambahan di luar 2.316.

---

## 4. Temuan terpenting: detektor membuang aritmia lebih sering

Sensitivity Pan-Tompkins per kelas AAMI di DS2:

| Kelas | Sensitivity |
|---|---|
| N (normal) | 0,9614 |
| **S (supraventrikular)** | **0,6494** |
| V (ventrikular) | 0,9146 |
| F (fusi) | 0,9820 |
| **Normal vs Aritmia** | **0,9614 vs 0,8296** |

Sebabnya struktural: beat supraventrikular datang **prematur**, dan Pan-Tompkins
memblokir deteksi selama **periode refraktori 200 ms** setelah detak sebelumnya
(`PT_REFRACTORY_MS` di `config.py`). Beat yang datang terlalu cepat justru
terblokir — padahal "datang terlalu cepat" itulah definisi beat prematur.

Efeknya berlipat: recall klasifikasi kelas S sudah rendah (0,4390 pada model
berlaku, 0,3034 pada baseline), dan hanya 65% beat S yang bahkan sampai ke
model. Ini penjelasan
kuantitatif kenapa kelas S menjadi titik terlemah seluruh sistem — dan arah
perbaikan yang jelas: menurunkan refraktori menaikkan sensitivity S dengan biaya
lebih banyak deteksi palsu. Trade-off itu bisa diukur dengan skrip yang sama.

---

## 5. Yang ini berarti untuk firmware

```c
// urutan wajib di alur hidup on-device
r_kasar   = pan_tompkins(filtered)      // punya delay ~38 sampel
r_kompen  = r_kasar - 38                // kompensasi median (kalibrasi DS1)
r_halus   = argmax(filtered, r_kompen +- 25)   // puncak sebenarnya
r_pakai   = r_halus - 4                 // kembalikan group delay -> R di indeks 132
window    = filtered[r_pakai - 128 : r_pakai + 128]   // WIN_PRE / WIN_POST
```

Konstanta yang sama di firmware: `ECG_PT_OFFSET` 38, `ECG_GROUP_DELAY` 4,
`ECG_WIN_PRE`/`ECG_WIN_POST` 128 (`firmware/include/ecg_preproc.h`). Salah satu
langkah saja terlewat, precision jatuh hingga 4× (terukur pada baseline) tanpa
satu pun error.

---

## 6. Cek pemahaman

1. Kenapa geseran 4 sampel merusak model padahal GAP seharusnya membuat model
   tahan geser? (Petunjuk: hitung stride total tiga MaxPooling.)
2. Recall klasifikasi pada beat terdeteksi (0,7279) sedikit LEBIH TINGGI
   daripada dengan anotasi (0,6996). Kenapa itu bukan bukti deteksi lebih baik?
3. Refraktori diturunkan 200 → 150 ms. Metrik mana yang membaik, mana yang
   memburuk, dan bagaimana mengukurnya tanpa menyentuh DS2 lagi?
4. Kenapa eksperimen ini memakai model float32, bukan INT8 yang akan benar-benar
   dipakai di alat?

## 7. Skrip

| Perintah | Keluaran |
|---|---|
| `python scripts/eval_detected_segmentation.py` | Semua angka di atas + `fase6b_segmentasi_deteksi.csv` |
| `python scripts/bench_pantompkins.py 100` | Akurasi detektor per record + plot |

---

**[← Fase 6 — evaluate](evaluate-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[firmware — port ke ESP32-S3 →](firmware-walkthrough.md)**
