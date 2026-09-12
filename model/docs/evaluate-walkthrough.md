# Walkthrough `src/evaluate.py` — Fase 6

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 15. Lanjutan dari
[`train-walkthrough.md`](train-walkthrough.md) (Fase 5).

Reproduksi:

```
cd model
python scripts/calibrate_threshold.py   # kalibrasi di VAL (DS1)
make eval                               # evaluasi di DS2
```

> **Ini fase paling menentukan di seluruh PA.** Angka di sini adalah klaim
> ilmiah primer-mu. Semua yang dilakukan di fase 0–5 adalah persiapan supaya
> angka ini jujur.

---

## 0. Urutan yang tidak boleh dibalik

```
Fase 5 selesai → model_fp32.keras beku
        │
        ▼
calibrate_threshold.py   ← pakai VAL (5 record DS1). Threshold ditetapkan DI SINI.
        │
        ▼  config.THRESHOLD = 0.35   (dikunci)
        │
        ▼
    make eval            ← DS2 dibuka. SEKALI. Dilapor apa adanya.
```

**JEBAKAN PRD Fase 6:** kalau threshold disetel dengan melihat hasil DS2, DS2
berhenti jadi test set. Yang kamu laporkan bukan lagi "performa pada pasien
baru", tapi "performa terbaik yang bisa saya cari-cari pada pasien uji" — dan
penguji yang paham akan langsung menyerang itu.

Makanya kalibrasi punya skripnya sendiri (`calibrate_threshold.py`) yang secara
struktural **tidak bisa** menyentuh DS2: dia cuma memuat `train.npz`.

---

## 1. Kenapa metrik ditulis sendiri, bukan `sklearn.metrics`

PRD mencontohkan `confusion_matrix`, `classification_report`. Semuanya adalah
aritmetika empat angka:

$$\text{recall} = \frac{TP}{TP+FN}, \quad
\text{precision} = \frac{TP}{TP+FP}, \quad
\text{specificity} = \frac{TN}{TN+FP}$$

$$F_1 = \frac{2 \cdot \text{precision} \cdot \text{recall}}{\text{precision}+\text{recall}}$$

Sama seperti `class_weight` di Fase 5: gate point `CLAUDE.md` melarang menambah
dependency untuk yang beberapa baris sudah selesai. Bonus yang tidak sepele —
menulis sendiri memaksa kamu memutuskan apa yang terjadi saat penyebutnya nol.

```python
div = lambda a, b: a / b if b else 0.0
```

Model yang tidak pernah menebak positif punya `TP+FP = 0`. sklearn mengeluarkan
warning dan mengembalikan 0; di sini eksplisit: **0,0, bukan NaN**. NaN akan
menjalar ke tabel delta Fase 7 dan merusak perbandingan float32 vs INT8.

---

## 2. Kalibrasi threshold — kriteria yang ditulis SEBELUM melihat hasil

Kriteria terkunci: **F1 maksimum, tie-break ke recall bila selisih F1 < 0,005.**

Kenapa kriterianya perlu ditulis dulu: kalau kamu melihat tabel sweep dulu baru
memilih "yang paling enak dilihat", itu tuning yang tidak bisa
dipertanggungjawabkan. Dengan kriteria eksplisit, `calibrate_threshold.py`
menghasilkan angka yang sama tiap kali dijalankan siapa pun.

Sweep di VAL (10.348 beat DS1 yang disisihkan):

| thr | recall | precision | F1 | specificity |
|---|---|---|---|---|
| 0,20 | 0,8881 | 0,5038 | 0,6429 | 0,9016 |
| 0,30 | 0,8375 | 0,7436 | 0,7878 | 0,9675 |
| **0,35** ✓ | **0,8117** | **0,8132** | **0,8124** | **0,9790** |
| 0,40 | 0,7725 | 0,8596 | **0,8137** | 0,9858 |
| 0,50 | 0,6960 | 0,9157 | 0,7909 | 0,9928 |
| 0,70 | 0,5010 | 0,9632 | 0,6591 | 0,9978 |

F1 maksimum ada di 0,40 (0,8137), tapi 0,35 hanya berbeda 0,0013 — di dalam
margin — dan memberi recall **+3,9 poin**. Tie-break memilih 0,35.

Perhatikan bentuk trade-off-nya: menaikkan threshold selalu menaikkan precision
dan menurunkan recall. Tidak ada threshold "benar" secara universal; yang ada
adalah threshold yang sesuai dengan biaya kesalahan di domainmu.

---

## 3. `roc_auc()` — kenapa ditulis manual dan kenapa penting

AUC = probabilitas bahwa satu beat aritmia acak diberi skor lebih tinggi
daripada satu beat normal acak. Dihitung lewat statistik **Mann–Whitney U**,
bukan dengan menggambar kurva:

$$\text{AUC} = \frac{\sum_{i \in \text{pos}} r_i - \frac{n_{+}(n_{+}+1)}{2}}{n_{+} \cdot n_{-}}$$

dengan $r_i$ = peringkat probabilitas. Penanganan **nilai seri** (`ties`) diberi
peringkat rata-rata — kalau tidak, model yang mengeluarkan probabilitas identik
untuk semua sampel akan terlihat AUC 1,0 padahal seharusnya 0,5. Itu di-assert
di `test_auc_sempurna_acak_dan_seri`.

Kenapa AUC dilaporkan bersama recall: **AUC tidak tergantung threshold**. Kalau
suatu saat threshold berubah, recall dan precision ikut berubah tapi AUC tidak —
jadi dialah yang bisa membandingkan *kualitas model* lintas konfigurasi.

---

## 4. Hasil DS2 — angka jujur

```
DS2  49.654 beat dari 22 pasien  (5.450 aritmia)   threshold 0,35 (dari DS1/val)
  TP=3630  FN=1820  FP=3750  TN=40454
  recall 0,6661   precision 0,4919   F1 0,5659
  specificity 0,9152   accuracy 0,8878   AUC 0,8866
```

Bandingkan dengan VAL: recall 0,8117 → **0,6661**, precision 0,8132 → **0,4919**.

Penurunan sebesar ini **normal dan diharapkan** untuk inter-patient. Val masih
berisi pasien DS1 — sekelompok orang yang sebagian karakteristiknya sudah
terwakili di data latih. DS2 benar-benar orang lain. Selisih inilah ukuran
sebenarnya dari "seberapa jauh model bisa menyeberang ke pasien baru".

**Accuracy 0,8878 sengaja tidak dijadikan judul.** Menebak Normal terus memberi
0,8903 — *lebih tinggi* dari model kita. Ini bukti hidup kenapa accuracy dilarang
jadi metrik utama di data timpang.

---

## 5. Bedah kegagalan — kelas mana yang jatuh

Di sinilah kolom `symbols` (Fase 2) dan `records` (Fase 3) membayar dirinya.

### Per kelas AAMI

| Kelas | n di DS2 | recall | tafsir |
|---|---|---|---|
| **V** (ventricular) | 3.219 | **0,9332** | morfologi jelas beda → CNN menangkapnya |
| **S** (supraventricular) | 1.836 | **0,3034** | bentuk mirip normal, cuma beda timing |
| **F** (fusion) | 388 | **0,1675** | hampir gagal total |
| Q | 7 | 0,5714 | terlalu sedikit untuk disimpulkan |
| N (normal) | 44.204 | FP rate 0,0848 | 3.750 alarm palsu |

Tiga temuan yang layak masuk Bab 4–5:

**1. V baik, S dan F jatuh — ini pola inter-patient klasik**, bukan bug. PRD
sendiri sudah memperkirakannya (alasan klasifikasi dibikin biner).

**2. Kegagalan F sudah bisa diramalkan sejak Fase 5.** Dari 414 beat kelas F di
DS1, **372 ada di record 208 sendirian**. Model tidak pernah melihat fusion dari
pasien yang beragam, jadi yang dipelajarinya adalah "fusion pada jantung pasien
208". Recall 0,17 di DS2 adalah konsekuensi langsung komposisi dataset — bukan
kesalahan arsitektur.

**3. Satu pasien menyeret metrik global.** Recall per pasien:

```
median recall  0,8933  (atas 21 pasien beraritmia)
rec 232        0,2042  ← 1.381 aritmia, semuanya kelas S
rec 100        0,2353  ← cuma 34 aritmia
rec 234        0,3019
```

Median 0,89 vs agregat 0,67 — jaraknya jauh. Sebabnya rec 232: 1.381 dari 1.836
beat S di seluruh DS2 ada di pasien ini, dan recall S di sana cuma 0,2042
sementara di pasien DS2 lainnya 0,6044. Satu pasien memegang 25% seluruh
aritmia DS2, jadi kegagalannya mendominasi angka beat-level.

Agregasi tetap di **level beat** (keputusan PRD, standar & sebanding dengan
literatur), tapi tabel per-record disimpan di
`artifacts/metrics/fase6_per_record_fp32.csv` supaya cerita di baliknya bisa
diceritakan.

---

## 6. Yang sengaja TIDAK dilakukan

**Tidak mengulang training setelah melihat DS2.** Godaan terbesar setelah melihat
recall 0,67. Sekali model diperbaiki berdasarkan DS2, DS2 jadi validation dan
klaim inter-patient gugur. Kalau memang mau memperbaiki, jalurnya: kembali ke
DS1/val, ubah sesuatu, evaluasi ulang di val, **lalu** DS2 dibuka lagi — dan
fakta bahwa DS2 sudah dilihat harus dicatat jujur di laporan.

**Tidak menggeser threshold setelah melihat DS2.** Sama alasannya.

**Tidak membuang rec 232 dari laporan.** Menyingkirkan pasien tersulit supaya
angka terlihat bagus adalah bentuk manipulasi. Yang benar: laporkan agregat,
lalu jelaskan sebarannya.

---

## 7. Cek pemahaman

1. Menebak "Normal" untuk semua beat DS2 memberi accuracy 0,8903 — lebih tinggi
   dari model (0,8878). Metrik mana yang menunjukkan model tetap jauh lebih
   berguna, dan kenapa?
2. Recall kelas F 0,1675. Kembali ke Fase 3: keputusan mana yang membuat hasil
   ini praktis tidak terhindarkan, dan apa yang harus berubah untuk
   memperbaikinya?
3. Threshold dinaikkan 0,35 → 0,50 di DS2 dan precision membaik. Kenapa angka
   itu tetap tidak boleh dilaporkan sebagai hasil?
4. AUC DS2 0,8866 padahal F1 cuma 0,5659. Bagaimana model bisa "mengurutkan"
   dengan baik tapi berkinerja sedang saat dipaksa memilih 0/1?

## 8. Skrip pendukung

| Perintah | Keluaran |
|---|---|
| `python scripts/calibrate_threshold.py` | Tabel sweep val + `fase5_threshold_sweep.csv` |
| `make eval` | `fase6_confusion_fp32.png`, `fase6_metrics_fp32.csv`, `fase6_per_record_fp32.csv` |
| `make test` | 42 test — 8 di antaranya mengunci rumus metrik & AUC |

---

**[← Fase 5 — train](train-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 6b — segmentasi deteksi →](segmentasi-deteksi-walkthrough.md)**
