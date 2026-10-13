# Walkthrough `src/evaluate.py` — Fase 6

> **Ruang lingkup:** kalibrasi threshold di VAL lalu evaluasi model float32 di DS2 (inter-patient), termasuk bedah kegagalan per kelas dan per pasien.
> **Kode terkait:** `src/evaluate.py`, `scripts/calibrate_threshold.py`, `scripts/eval_fp32.py`, `config.py` (`THRESHOLD`)
> **Prasyarat:** [`train-walkthrough.md`](train-walkthrough.md) (Fase 5)

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 15.

Konfigurasi yang diukur di dokumen ini: window 128/128 (256 sampel), DS1
diaugmentasi jitter empiris (1 salinan bersih + 2 salinan ber-jitter), threshold
0,80. Kondisi ukur: artefak `model_fp32.keras` dan `fase6_*.csv` hasil rantai
penuh 18 Sep 2026.

Reproduksi:

```
cd model
python scripts/calibrate_threshold.py   # kalibrasi di VAL (DS1)
make eval                               # evaluasi di DS2
```

> **Ini fase paling menentukan di seluruh PA.** Angka di sini adalah klaim
> ilmiah primer. Semua yang dilakukan di fase 0–5 adalah persiapan supaya
> angka ini jujur.

---

## 0. Urutan yang tidak boleh dibalik

```
Fase 5 selesai → model_fp32.keras beku
        │
        ▼
calibrate_threshold.py   ← pakai VAL (5 record DS1). Threshold ditetapkan DI SINI.
        │
        ▼  config.THRESHOLD = 0.80   (dikunci)
        │
        ▼
    make eval            ← DS2 dibuka. SEKALI. Dilapor apa adanya.
```

**JEBAKAN PRD Fase 6:** kalau threshold disetel dengan melihat hasil DS2, DS2
berhenti jadi test set. Yang kamu laporkan bukan lagi "performa pada pasien
baru", tapi "performa terbaik yang bisa saya cari-cari pada pasien uji" — dan
penguji yang paham akan langsung menyerang itu.

Makanya kalibrasi punya skripnya sendiri (`calibrate_threshold.py`) yang secara
struktural **tidak bisa** menyentuh DS2: dia cuma memuat `train.npz` lalu
mengambil record VAL lewat `split_train_val`.

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

Kriteria terkunci: **F1 maksimum, tie-break ke recall bila selisih F1 < 0,005**
(`F1_TIE_MARGIN` di `calibrate_threshold.py`).

Kriteria perlu ditetapkan lebih dulu: memilih threshold "yang paling enak
dilihat" sesudah membaca tabel sweep adalah tuning yang tidak bisa
dipertanggungjawabkan. Dengan kriteria eksplisit, `calibrate_threshold.py`
menghasilkan angka yang sama tiap kali dijalankan siapa pun.

Sweep di VAL (5 record DS1, 31.047 beat termasuk salinan ber-jitter; sebagian
baris dari `fase5_threshold_sweep.csv`):

| thr | recall | precision | F1 | specificity |
|---|---|---|---|---|
| 0,20 | 0,9446 | 0,1480 | 0,2559 | 0,3888 |
| 0,50 | 0,8445 | 0,3193 | 0,4634 | 0,7976 |
| 0,70 | 0,7240 | 0,6085 | 0,6612 | 0,9476 |
| 0,75 | 0,6909 | 0,6704 | 0,6805 | 0,9618 |
| **0,80** (terpilih) | **0,6539** | **0,7342** | **0,6917** | **0,9734** |
| 0,85 | 0,6141 | 0,7837 | 0,6886 | 0,9809 |
| 0,90 | 0,5542 | 0,8504 | 0,6710 | 0,9890 |

F1 maksimum ada di 0,80 (0,6917). Kandidat lain di dalam margin hanya 0,85
(selisih 0,0031); tie-break memilih recall yang lebih tinggi, jadi 0,80.

Threshold 0,80 tampak tinggi, tetapi itu bukan tanda model konservatif. VAL
dirakit dari DS1 teraugmentasi, sehingga ikut berisi salinan ber-jitter, dan
window yang bergeser cenderung diberi probabilitas Aritmia lebih tinggi.
Sebaran probabilitas bergeser ke atas, dan titik operasi yang benar ikut
bergeser. Pada threshold 0,35 model ini hanya mencapai precision 0,19 di VAL.
Konsekuensinya: **threshold milik satu model terlatih, bukan konstanta
pipeline** — setiap latih ulang wajib diikuti `calibrate_threshold.py`.

Bentuk trade-off-nya: menaikkan threshold selalu menaikkan precision dan
menurunkan recall. Tidak ada threshold "benar" secara universal; yang ada
adalah threshold yang sesuai dengan biaya kesalahan di domainnya.

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
threshold berubah, recall dan precision ikut berubah tapi AUC tidak —
jadi dialah yang bisa membandingkan *kualitas model* lintas konfigurasi.
Perbandingan antar-varian di [`jitter-walkthrough.md`](jitter-walkthrough.md)
bersandar pada sifat ini.

---

## 4. Hasil DS2

```
DS2  49.656 beat dari 22 pasien  (5.450 aritmia)   threshold 0,80 (dari DS1/val)
  TP=3813  FN=1637  FP=2302  TN=41904
  recall 0,6996   precision 0,6235   F1 0,6594
  specificity 0,9479   accuracy 0,9207   AUC 0,9334
```

Bandingkan dengan VAL @0,80: recall 0,6539 → **0,6996**, precision 0,7342 →
**0,6235**, F1 0,6917 → **0,6594**. Jarak VAL→DS2 muncul terutama di
precision: pada pasien yang benar-benar baru, lebih banyak beat Normal yang
morfologinya tidak dikenal dan ikut ditandai Aritmia. Perbandingan ini
perkiraan kasar, karena VAL berisi salinan ber-jitter sedangkan DS2 bersih.

**Accuracy 0,9207 sengaja tidak dijadikan judul.** Menebak Normal untuk semua
beat sudah memberi 0,8902 (44.206 dari 49.656 beat). Selisih 3 poin itu
menyembunyikan perbedaan yang sesungguhnya: tebak-Normal punya recall 0,
model ini 0,70. Itu sebabnya accuracy tidak dipakai sebagai metrik utama di data
timpang.

### Model pembanding

Konfigurasi pembanding yang dipakai di Fase 6b dan 6c adalah model baseline:
window 90/160 (250 sampel), tanpa augmentasi, threshold 0,35 (dikalibrasi di
VAL bersih), DS2 49.654 beat.

| | baseline (90/160, 0,35) | berlaku (128/128 + jitter, 0,80) |
|---|---|---|
| recall | 0,6661 | **0,6996** |
| precision | 0,4919 | **0,6235** |
| F1 | 0,5659 | **0,6594** |
| specificity | 0,9152 | **0,9479** |
| AUC | 0,8866 | **0,9334** |
| accuracy | 0,8878 (di bawah tebak-Normal 0,8902) | 0,9207 |

Penjelasan selisihnya (window dan augmentasi) ada di
[`jitter-walkthrough.md`](jitter-walkthrough.md) §5.

---

## 5. Bedah kegagalan — kelas mana yang jatuh

Di sinilah kolom `symbols` (Fase 2) dan `records` (Fase 3) membayar dirinya.

### Per kelas AAMI

| Kelas | n di DS2 | recall | tafsir |
|---|---|---|---|
| **V** (ventricular) | 3.219 | **0,9248** | morfologi jelas beda → CNN menangkapnya |
| **S** (supraventricular) | 1.836 | **0,4390** | bentuk mirip normal, beda di gelombang P dan timing |
| **F** (fusion) | 388 | **0,0670** | gagal hampir total |
| Q | 7 | 0,5714 | terlalu sedikit untuk disimpulkan |
| N (normal) | 44.206 | FP rate 0,0521 | 2.302 alarm palsu |

Tiga temuan yang layak masuk Bab 4–5:

**1. V baik, S dan F jatuh — ini pola inter-patient klasik**, bukan bug. PRD
sendiri sudah memperkirakannya (alasan klasifikasi dibikin biner). Window
128/128 menaikkan recall S dan menurunkan recall F terhadap baseline (S 0,3034
→ 0,4390, F 0,1675 → 0,0670); pertukaran ini disengaja dan dijelaskan di
[`jitter-walkthrough.md`](jitter-walkthrough.md) §5.

**2. Kegagalan F bisa diramalkan dari komposisi dataset.** Dari 414 beat kelas F
di DS1, **372 ada di record 208 sendirian**. Model tidak pernah melihat fusion
dari pasien yang beragam, jadi yang dipelajarinya adalah "fusion pada jantung
pasien 208". Di sisi uji polanya sama: **362 dari 388 beat F di DS2 ada di
record 213**, dan recall F di sana 0,0387. Kelas F diuji praktis oleh satu
pasien yang berbeda dari satu pasien yang mengajarkannya — konsekuensi langsung
komposisi dataset, bukan kesalahan arsitektur.

**3. Satu pasien menyeret metrik global.** Recall per pasien:

```
median recall  0,9167  (atas 21 pasien beraritmia)
rec 232        0,3541  ← 1.381 aritmia, semuanya kelas S
rec 213        0,2246  ← 610 aritmia, 362 di antaranya kelas F
rec 100        0,2059  ← cuma 34 aritmia
```

Median 0,92 vs agregat 0,70 — jaraknya jauh. Sebab utamanya rec 232: 1.381 dari
1.836 beat S di seluruh DS2 ada di pasien ini, dan recall S di sana cuma 0,3541
sementara di pasien DS2 lainnya 0,6967. Satu pasien memegang 25% seluruh
aritmia DS2, jadi kegagalannya mendominasi angka beat-level.

Agregasi tetap di **level beat** (keputusan PRD, standar & sebanding dengan
literatur), tapi tabel per-record disimpan di
`artifacts/metrics/fase6_per_record_fp32.csv` supaya cerita di baliknya bisa
diceritakan.

### Tahap 2: menamai aritmia (dieksperimenkan, tidak dikirim)

`scripts/tahap2.py` menguji aturan penamaan di atas keputusan biner. Tahap 2
tidak dilatih dan tidak masuk `model_int8.h`; dia aturan skalar atas beat yang
sudah ditandai tahap 1, jadi tidak bisa mengubah F1, hanya mengganti nama TP/FP
yang sudah ada. Plafonnya recall tahap 1. Dua sumbu saja:

```
                  QRS sempit            QRS lebar
prematur+jeda     S                     V (PVC prematur)
tepat waktu       N / tak dinamai       V atau F
```

- **F tidak punya cabang.** Fusion beat adalah tabrakan depolarisasi normal dan
  ventrikular, jadi morfologinya di antara N dan V; tidak ada fitur yang
  memisahkan sesuatu dari komponennya sendiri. P3 mengukurnya: 65 F → VEB,
  0 F → SVEB.
- **Q tidak punya cabang.** 100 beat di tiga database, dan keranjang sisa akan
  didominasi FP (~2.300 : 1 di DS2): menamainya "Q" berarti melabeli alarm palsu
  dengan nama kelas klinis.
- **S belum dinamai.** Cabang S menunggu gate G2: tanpa RR+1/RR0 tidak ada sumbu
  jeda kompensasi, dan S tidak terpisah dari beat normal yang kebetulan cepat.
  Menamai S dari rasio RR saja memberi +P 42% (P5).
- **Lebar QRS mentah, bukan ternormalisasi.** Fitur model ternormalisasi relatif
  baseline pasien (bagus untuk N vs abnormal), tetapi "V = QRS lebar" adalah
  ambang fisiologis absolut. Keduanya dari window yang sama, nol buffer tambahan.
- **Kriteria ambang = presisi minimum (`MIN_PRESISI_NAMA = 0,90`), bukan F1.**
  Memaksimalkan F1 kelas V di antara beat yang ditandai memberi hadiah untuk
  "namai semuanya V" (V ~50% dari yang ditandai): percobaan pertama mendarat di
  dasar grid, 4.387 dinamai V, hanya 1.664 benar (presisi 37,9%). Ambang terkecil
  yang presisinya ≥ 0,90 dipilih (cakupan terbesar pada presisi yang dijanjikan);
  bila tak ada, nama V tidak ditampilkan. Alat boleh diam ("tipe tak pasti"),
  tidak boleh bilang "V" kalau salah 6 dari 10. Di DS2 ambang 40 ms memberi
  presisi 91,7% dengan cakupan 40,4% (30 ms: 51,7%), tetapi ambang dikalibrasi
  di VAL, dan VAL maksimum hanya 43,9%; DS2 tidak boleh mensertifikasi, jadi
  tahap 2 tidak dikirim (`model/CLAUDE.md`, baris Tahap 2).

---

## 6. Yang sengaja TIDAK dilakukan

**Tidak mengulang training sebagai reaksi atas hasil DS2.** Sekali model
diperbaiki berdasarkan DS2, DS2 jadi validation dan klaim inter-patient gugur.
Jalur perbaikan yang sah: kembali ke DS1/VAL, ubah sesuatu, evaluasi ulang di
VAL, **lalu** DS2 dibuka lagi — dan jumlah pembukaan DS2 dicatat terbuka di
laporan.

**Tidak menggeser threshold setelah melihat DS2.** Sama alasannya.

**Tidak membuang rec 232 dari laporan.** Menyingkirkan pasien tersulit supaya
angka terlihat bagus adalah bentuk manipulasi. Yang benar: laporkan agregat,
lalu jelaskan sebarannya.

---

## 7. Cek pemahaman

1. Menebak "Normal" untuk semua beat DS2 memberi accuracy 0,8902, hanya 3 poin
   di bawah model (0,9207). Metrik mana yang menunjukkan model jauh lebih
   berguna, dan kenapa?
2. Recall kelas F 0,0670. Kembali ke Fase 3: keputusan mana yang membuat hasil
   ini praktis tidak terhindarkan, dan apa yang harus berubah untuk
   memperbaikinya?
3. Threshold dinaikkan 0,80 → 0,90 di DS2 dan precision membaik. Kenapa angka
   itu tetap tidak boleh dilaporkan sebagai hasil?
4. AUC DS2 0,9334 padahal F1 cuma 0,6594. Bagaimana model bisa "mengurutkan"
   dengan baik tapi berkinerja sedang saat dipaksa memilih 0/1?
5. Kenapa threshold 0,35 yang benar untuk model baseline memberi precision 0,19
   pada model yang berlaku?

## 8. Skrip pendukung

| Perintah | Keluaran |
|---|---|
| `python scripts/calibrate_threshold.py` | Tabel sweep val + `fase5_threshold_sweep.csv` |
| `make eval` | `fase6_confusion_fp32.png`, `fase6_metrics_fp32.csv`, `fase6_per_record_fp32.csv` |
| `make test` | seluruh suite pytest; 8 test di `tests/test_evaluate.py` mengunci rumus metrik & AUC |

---

**[← Fase 5 — train](train-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 6b — segmentasi deteksi →](segmentasi-deteksi-walkthrough.md)**
