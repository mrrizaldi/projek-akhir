# Fitur, imbalance, dan ketahanan — sintesis riset & usul adaptasi

**19 September 2026. Dokumen KEPUTUSAN, bukan rencana eksekusi.**
Belum ada baris kode atau nilai `config.py` yang berubah. Isinya: paper apa yang
dipakai, temuan mana yang **bertabrakan dengan decision point yang sudah
dikunci**, dan urutan kerja yang diusulkan. Rencana bertahap (`-plan.md`) ditulis
setelah dokumen ini disetujui.

Lanjutan dari [`2026-09-18-robustness-plan.md`](2026-09-18-robustness-plan.md) /
[`-changelog.md`](2026-09-18-robustness-changelog.md). Aturan metodologis dari
changelog itu (§B2: **ablasi 1 run tidak sah**) berlaku penuh di sini.

---

## 0. Ringkasan satu layar

Fase 6c menutup satu celah: posisi R yang meleset. Angka DS2 naik dari F1 0,566
ke 0,659. Tapi kelemahan yang tersisa **bukan** soal ketahanan sinyal:

```
recall V  0,92-0,97   sudah selesai
recall S  0,33-0,67   rapuh, variansi besar
recall F  0,12-0,34   nyaris gagal total
precision 0,6235      2.302 FP dari 44.206 beat normal (FPR 5,2%)
```

Tujuh sumber dibaca. Kesimpulannya konsisten dan tidak menyenangkan: **fitur
kita kurang, bukan model kita kecil.** Model pembanding terbaik yang memenuhi
kriteria persis proyek ini memakai **1.267 parameter** (kita 6.417) dan
mendapat SVEB F1 82,1% (kita recall S ~0,40).

Empat usul utama, semuanya menyentuh `features_rr.py` dan `train.py` — **nol
perubahan arsitektur, nol perubahan firmware** sampai tahap re-export:

1. Hapus `class_weight` (kontra decision point terkunci)
2. Tambah lebar QRS (QRSw2, QRSw4) — peringkat 1 & 2 dari 85 fitur
3. Fitur RR jadi **rasio** semua, tambah `RR+1/RR0` (butuh 1 beat ke depan)
4. Uji input turunan pertama

---

## 1. Paper yang dipakai

| # | Sumber | Peran di proyek ini |
|---|---|---|
| **P1** | Farag, M.M. *A Tiny Matched Filter-Based CNN for Inter-Patient ECG Classification and Arrhythmia Detection at the Edge.* **Sensors 23(3):1365 (2023).** DOI 10.3390/s23031365 | **Pembanding utama.** Satu-satunya SOTA yang memenuhi AAMI + inter-patient + embedded. Tabel ablasinya variabel-tunggal — itu yang paling berharga |
| **P2** | *A Systematic Review of ECG Arrhythmia Classification: Adherence to Standards, Fair Evaluation, and Embedded Feasibility.* **arXiv:2503.07276 (2025)** | Kerangka **E3C**. Hanya **5 dari 122** studi memenuhi ketiganya. Pembelaan orisinalitas + pedoman pelaporan |
| **P3** | Saenz-Cogollo, J.F.; Agelli, M. *Investigating Feature Selection and Random Forests for Inter-Patient Heartbeat Classification.* **Algorithms 13(4):75 (2020).** DOI 10.3390/a13040075 | **Ranking fitur formal** (mutual information atas 85 fitur). Sumber usul lebar QRS & bentuk rasio RR |
| **P4** | Zhu, H.; Zhao, Y.; Pan, Y. *Robust Heartbeat Classification for Wearable Single-Lead ECG via Extreme Gradient Boosting.* **Sensors 21(16):5290 (2021).** | Konfirmasi RRpre/**RRpos**/HRVloc. Diuji di DB wearable nyata, bukan cuma MITDB |
| **P5** | Huang, H.; Liu, J.; Zhu, Q. *A new hierarchical method for inter-patient heartbeat classification using random projections and RR intervals.* **BioMed Eng OnLine 13:90 (2014).** | Argumen pemisahan tahap: V lewat morfologi, S lewat ritme |
| **P6** | Khosravi Khaliran, M.U. dkk. *Improving deep learning in arrhythmia Detection: modular quality and quantity controllers in data augmentation.* **Biomed Signal Process Control 91:105940 (2024).** | Tiga teknik augmentasi + rumus volume per kelas. **Hasilnya tidak dipakai** (lihat §1.1) |
| **P7** | *False arrhythmia alarm reduction in the ICU* (arXiv:1709.03562); Tanatorn dkk. (2014) DOI 10.3233/bme-130823 | Post-processing & gating kualitas sinyal untuk menekan FP |

### 1.1 Sumber yang DIBUANG, dan kenapa

| Sumber | Kenapa dibuang |
|---|---|
| *Baseline normalization choices inflate performance* (Frontiers Digit Health 2026) | **Salah sasaran.** Domainnya affective computing; mekanisme bocornya = jendela baseline tumpang tindih dengan test set. Z-score kita dihitung dari window itu sendiri — mekanisme itu tidak ada di sini. Usul awal "ganti normalisasi" **ditarik** |
| *BeatRhythm-TTA* (arXiv:2608.23347) | 12-lead PTB-XL→CPSC, butuh backprop saat inferensi. Untung +2,7% Macro-F1. Tidak deployable di ESP32-S3 |
| **Angka** P6 (akurasi 98,9%) | Protokol 17 kelas per-fragmen, split acak, dan 10-fold CV dijalankan **di dataset yang sudah diaugmentasi**. Dua kebocoran bertumpuk. **Jangan pernah** disandingkan dengan F1 0,659 kita |
| Segmentasi per-RR + resample 480 titik (P6) | Menormalkan panjang beat → informasi "beat ini datang kepagian" terhapus dari window. Merusak justru untuk deteksi S |

---

## 2. Diagnosis: ke mana angka kita bocor

### 2.1 Per kelas (ablasi 3 seed, varian w128 yang sudah dikunci)

| Kelas | recall (seed 42 / 7 / 13) | Baca |
|---|---|---|
| V | 0,923 / 0,936 / 0,967 | selesai |
| S | 0,326 / 0,669 / 0,466 | rapuh **dan** tak stabil |
| F | 0,116 / 0,134 / 0,338 | gagal |

S dibedakan dari N terutama oleh **waktu kedatangan**, bukan bentuk (P5
menyatakannya eksplisit: "the waveform of SVEB is similar to that of class N").
Recall S rendah = cabang ritme kurang informasi. Menambah filter Conv tidak akan
menolong.

### 2.2 Beban alarm palsu

```
FPR = 2.302 / (2.302 + 41.904) = 5,21%
60 bpm → 86.400 beat/hari, ~89% normal → ~76.900 beat normal
       → ~4.000 alarm palsu per hari
```

Angka yang membuat alat tidak terpakai, terlepas dari F1.

### 2.3 Kita lebih BESAR dan lebih buruk

| | P1 (Farag, model ID 6) | Kita |
|---|---|---|
| Parameter | **1.267** (1.245 trainable) | 6.417 |
| Ukuran INT8 | 15–18 KB | 22,94 KB |
| Input | 64 sampel @128 Hz (0,5 s) | 256 sampel @360 Hz (0,71 s) |
| Fitur RR | 4 (ternormalisasi) | 3 (2 di antaranya absolut) |
| SVEB | Se 81,6 / +P 82,7 / **F1 82,1** | recall S ~0,40 |
| Protokol | inter-patient DS1/DS2 | sama |

5× lebih banyak parameter untuk hasil lebih buruk. **Kapasitas bukan
penyebabnya.** Rencana "perbesar model karena RAM longgar" dicoret.

> Catatan sebanding: F1 82,1% milik P1 adalah F1 kelas SVEB pada tugas 3 kelas;
> F1 0,659 kita adalah kelas biner "Aritmia" yang menggabung S+V+F+Q. Bukan
> perbandingan lurus. Yang lurus dibandingkan: **recall per simbol**, dan di situ
> S kita (0,33–0,67) memang jauh di bawah Se 81,6% mereka.

---

## 3. Temuan yang KONTRA dengan decision point terkunci

Ini bagian terpenting dokumen. Setiap baris di bawah menabrak sesuatu yang sudah
ditulis di [`../CLAUDE.md`](../CLAUDE.md) §"Decision point yang sudah di-lock".
Tidak ada satu pun yang boleh diubah tanpa persetujuan eksplisit.

### K1 — `class_weight` balanced ⚠️ KONTRA

**Terkunci:** *"Strategi imbalance: `class_weight` balanced, dihitung sendiri
`w_c = N/(2·n_c)` → Normal 0,556 / Aritmia 4,947"*

**Bukti tandingan (P1, Tabel 4).** Model 2 vs Model 6 berbeda **hanya** di
parameter class weight; trainable=TRUE, NK=32, input=turunan, semuanya identik:

| | SVEB Se | SVEB +P | **SVEB F1** | avg F1 |
|---|---|---|---|---|
| class weight **SET** | 88,51 | 51,49 | 65,11 | 84,79 |
| class weight **NOT SET** | 81,60 | 82,68 | **82,14** | **92,17** |

Recall turun 7 poin, precision naik **31 poin**. Persis pola penyakit kita:
recall 0,70 / precision 0,62. Penulis P1 menyatakannya sebagai trade-off sadar —
*"enhances the classifier's performance for the minority classes at the expense
of the majority class"* — dan memilih mematikannya.

**Argumen mengapa ini masuk akal di repo kita:** kita **sudah** menangani
imbalance lewat kalibrasi threshold di VAL (0,80). Class weight menumpuk
mekanisme kedua untuk tujuan yang sama, lalu threshold harus menebusnya lagi.
Dua knob saling menarik.

**Usul:** uji `class_weight=None`, 3 seed, threshold tetap dikalibrasi ulang di
VAL. Biaya: satu argumen di `train.py:39`. **Ini eksperimen termurah di seluruh
dokumen.**

### K2 — `RR+1` butuh beat masa depan ⚠️ KONTRA LANGSUNG

**Terkunci:** *"Jendela `RR_local_avg`: kausal, menyusut di tepi (10 RR
terakhir). Alasan: simetris butuh beat masa depan → **firmware harus tunda 5
beat**; kausal konsisten dgn `sosfilt` Fase 1"*

Alasan penolakan itu **persis** yang dilanggar usul `RR+1/RR0`.

**Yang berbeda: besaran penundaannya.** Keputusan lama menolak tunda **5 beat**.
`RR+1` butuh tunda **1 beat**. P3 menyatakannya eksplisit:

> Since only the features related to RR+1 need a future value, the classification
> of each heartbeat can be done **once the following beat is detected**.

Pada 60 bpm itu ≈ 1 detik. Untuk monitoring kontinu (bukan defibrilator), itu
murah.

**Bukti kekuatan fiturnya — empat sumber independen:**

| Sumber | Bentuk | Bukti |
|---|---|---|
| P3 | `RR+1/RR0` | **peringkat 4** dari 85 fitur (mutual information) |
| P1 | post-RR / rerata lokal & global | 1 dari 4 fitur RR-nya |
| P4 | `RRpos`, `HRVloc = RRpos − RRpre` | fitur morfologi inti; SVEB Se 87,1% |
| P5 | rasio RR (tahap 2 khusus S) | SVEB Se 91,1% |

**Fisiologinya:** beat SVEB = RR pendek **lalu jeda kompensasi panjang**. Tanpa
`RR+1`, S dan beat normal yang kebetulan cepat tidak terbedakan. Ini penjelasan
paling langsung untuk recall S kita yang mentok.

**Status: GATE POINT.** Menembus alasan yang tertulis di decision point.
Butuh persetujuan, dan kalau disetujui **alasan di CLAUDE.md harus direvisi**
menjadi "tunda 1 beat diterima, tunda 5 beat tidak".

### K3 — bentuk fitur RR: absolut vs rasio ⚠️ KONTRA (ringan)

`compute_rr_features()` mengembalikan 3 kolom:

| Kolom kita | Bentuk | Padanan di P3 | Rank MI |
|---|---|---|---|
| `RR_prev` | **detik, absolut** | `RR−1/RR0` | 10 |
| `RR_ratio` (RR0/local_avg) | rasio ✅ | `RR0/avgRR` | **3** |
| `dRR` | **detik, absolut** | — (tak masuk 10 besar) | — |

P3 menguji keduanya dan menyimpulkan:

> those newly introduced normalizations for R–R intervals give more information
> and are more discriminative for heartbeat classification than **values of the
> R–R intervals alone**

Dua dari tiga fitur RR kita dalam bentuk yang kalah. Ini **inti masalah
inter-patient**: nilai absolut (detik, milivolt, milidetik) berbeda antar-orang,
jadi model belajar identitas pasien. Window kita sudah ter-z-score (amplitudo
ternormalisasi ✅) tapi fitur RR-nya dalam detik absolut (❌) — tidak konsisten.

**Usul bentuk baru (tetap 4–5 kolom, bukan menambah beban):**

| Kolom | Rumus | Rank MI (P3) |
|---|---|---|
| `RR0/avgRR` | sudah ada | 3 |
| `RR+1/RR0` | **baru** (lihat K2) | 4 |
| `RR−1/RR0` | ganti `RR_prev` absolut | 10 |
| `tRR0` | (RR0 − avgRR) / std(N beat terakhir) | masuk 10 besar |

### K4 — lebar QRS: fitur peringkat 1, belum kita punya

Bukan kontra — murni kekosongan. Tapi besar.

**P3, Tabel 2 — 10 besar dari 85 fitur menurut mutual information:**

| Rank | Fitur | Punya? |
|---|---|---|
| **1** | **QRSw2** (lebar QRS di ½ puncak, dinormalisasi) | ❌ |
| **2** | **QRSw4** (lebar QRS di ¼ puncak, dinormalisasi) | ❌ |
| 3 | RR0/avgRR | ✅ |
| **4** | **RR+1/RR0** | ❌ |
| 5 | QRSw2 (mentah) | ❌ |
| 6, 7, 9 | koefisien Hermite basis function | ~ (CNN melihat window mentah) |
| 8 | QRSw4 (mentah) | ❌ |
| 10 | RR−1/RR0 | ❌ |

**Empat dari sepuluh besar adalah lebar QRS, dan ia memegang dua peringkat
teratas — di atas semua fitur RR.** Hasil P3: 6 fitur saja sudah plateau →
Acc 96,14%, SVEB F1 73,06%, VEB F1 90,85%, dengan Random Forest, tanpa deep
learning.

**Fisiologi:** satu skalar yang memisahkan V (QRS lebar >120 ms, depolarisasi
lewat miokardium) dari S (QRS sempit, datang kepagian) dari N — sumbu yang
tidak diberikan fitur RR mana pun.

**Biaya di MCU: nol buffer tambahan.** Window sudah ter-z-score, R sudah mendarat
di indeks 132. Dari puncak, jalan kiri-kanan sampai amplitudo turun di bawah ½
dan ¼ nilai puncak. Menempel di cabang ritme seperti HOS, bukan cabang
morfologi.

Catatan: normalisasi P3 memakai **rerata 32 beat terakhir**, sama seperti fitur
RR-nya — bukan nilai mentah.

### K5 — jendela rerata lokal: 10 vs 32 vs 80 ⚠️ GATE POINT

**Terkunci:** `RR_LOCAL_WINDOW_BEATS = 10`, sumbernya PRD hal. 10 ("~10 beat
sekitarnya"), ditandai DECISION POINT.

| Sumber | Jendela |
|---|---|
| Kita | 10 beat |
| P3 | **32 beat** |
| P1 | **80 lokal + 400 global** (≈1 menit + 5 menit) |

Dua sumber independen memakai jendela 3–8× lebih panjang. Jendela pendek =
estimasi baseline berisik = rasio yang dibaginya ikut berisik. **Tidak diubah
tanpa persetujuan** — ini milik PRD.

### K6 — GlobalAveragePooling1D: ditunda, tidak dibatalkan

**Terkunci:** *"Pooling: GlobalAveragePooling1D — param jauh lebih kecil dari
Flatten"*

GAP merata-ratakan 32 langkah jadi 1 angka per kanal: model tahu "ada aktivitas
frekuensi-X", tidak tahu **di mana** relatif R. Gelombang P (penanda S) ada di
~150–200 ms sebelum R — informasi posisi itu yang dibuang.

Jalur murah yang sudah tersedia: `build_deploy_model()` **sudah** mengganti GAP
dengan `DepthwiseConv1D(32)` berbobot tetap 1/32. Menjadikan bobot itu
**belajar** = pooling temporal berbobot, nol op baru di TFLM, +1.024 bobot
(~1 KB INT8).

**Keputusan: TUNDA.** Alasan §2.3 — kapasitas bukan penyebabnya. Kerjakan
K1/K3/K4 dulu; kalau S masih macet setelah fiturnya benar, baru sentuh ini.

### K7 — input turunan pertama: menang, tapi ada harganya

**P1, Tabel 4.** Model 5 (sinyal) vs Model 2 (turunan), sisanya identik:
akurasi 92,90 → 95,58, **SVEB F1 54,26 → 65,11**.

**Tapi P1 juga mengukur harganya** (uji AWGN 0–50%, noise hanya di test):
F1 model turunan jatuh ke 35%, model sinyal mentah bertahan di 60%.
*"The model with the derivative input is more susceptible to noise."*

Turunan pertama = high-pass: menguatkan lereng QRS, menekan P/T/baseline
wander — sekaligus menguatkan noise EMG yang hidup di pita yang sama. Satu knob,
dua metrik ke arah berlawanan.

**Untuk AD8232 + elektroda kering, ini harus diukur sendiri, bukan diterima.**
Uji dua-duanya, dan uji di rekaman badan, bukan cuma MIT-BIH.

### K8 — kelas F & Q: tetap, dengan catatan jujur

**Terkunci:** *"Klasifikasi: biner (Normal/Aritmia) — inter-patient bikin F & Q
recall ~0"*. `ARRHYTHMIA_SYMBOLS = {V, S, F, Q}`.

P1 menguji 3 / 4 / 5 kelas dan membuang F & Q. **Tapi angkanya harus dibaca
hati-hati** — membuang F/Q hampir tidak mengubah skor N/S/V:

| | N F1 | SVEB F1 | VEB F1 |
|---|---|---|---|
| 3 kelas (ID 6) | 99,05 | 82,14 | 95,31 |
| 4 kelas (ID 8) | 98,43 | 81,78 | 92,50 |
| 5 kelas (ID 9) | 98,40 | 81,85 | 94,25 |

Jadi jatuhnya rerata makro sebagian besar **efek mekanis** menambah kelas yang
tak terpelajari, bukan bukti bahwa F/Q merusak kelas lain.

P3 mengonfirmasi ketidakterpelajarannya: dari 342 beat F di DS2, **277 diprediksi
NB, 65 VEB, nol SVEB**.

**Di setup biner kita efeknya berbeda**: beat F/Q jadi positif yang hampir
selalu meleset → langsung menekan recall kelas positif. Tapi membuangnya
mengubah definisi masalah.

**Keputusan: TIDAK DIUBAH.** Ini sudah terkunci dan alasannya masih berlaku.
Yang bertambah cuma bukti pendukung untuk paragraf pembatasan di laporan:
recall F 0,12–0,34 kita **bukan** kegagalan implementasi — P1 dan P3 menabrak
dinding yang sama.

### K9 — mutual information butuh sklearn ⚠️ GATE POINT (dependency)

**Terkunci:** *"`sklearn` untuk class weight: tidak dipakai — 3 baris numpy"* +
aturan repo *"Menambah dependency baru → tanya dulu"*.

P3 memakai `sklearn.metrics.mutual_info_classif`. Kalau kita mau **mereplikasi
ranking MI-nya di data kita sendiri**, itu butuh sklearn.

**Usul: jangan.** Ranking P3 sudah dihitung di MIT-BIH DS1 — dataset yang sama
dengan kita. Pakai hasilnya sebagai hipotesis, lalu validasi lewat **ablasi 3
seed** yang alatnya sudah ada (`ablasi.py`). Tidak perlu dependency baru.

### K10 — PTQ vs QAT: tidak berubah

**Terkunci:** *"QAT: tidak dipakai — PTQ sudah lolos target"*

P1 melaporkan *"PTQ int8 lost >10% accuracy; QAT int8 retained accuracy"*.
Kedengarannya mengancam, **tapi tidak berlaku untuk kita**: delta PTQ kita
+0,001 F1 (Fase 7), bukan −10%. Perbedaan kemungkinan dari varian deploy kita
yang sudah membuang op bermasalah.

**Keputusan: tetap PTQ.** Dicatat sebagai risiko yang sudah dipantau, bukan
tindakan.

---

## 4. Tabel adopsi

| # | Usul | Sumber | Keputusan | Menyentuh |
|---|---|---|---|---|
| 1 | Matikan `class_weight` | P1 Tabel 4 | **Uji (3 seed)** — ⚠️ kontra K1 | `train.py` 1 baris |
| 2 | Tambah QRSw2 + QRSw4 ternormalisasi | P3 rank 1–2 | **Uji (3 seed)** | `features_rr.py`, `N_RR_FEATURES` |
| 3 | Fitur RR jadi rasio + `RR+1/RR0` | P3 rank 4,10; P1; P4; P5 | **Uji** — ⚠️ gate K2 (tunda 1 beat) | `features_rr.py`, firmware nanti |
| 4 | Jendela lokal 10 → 32 | P3, P1 | **Gate point K5** — milik PRD | `config.py` |
| 5 | Input turunan pertama | P1 Tabel 4 | **Uji, dengan uji noise** — K7 | `preprocessing.py` |
| 6 | k-dari-n + gating SQI | P7 | **Adopsi, offline dulu** | post-processing, `firmware` |
| 7 | Inisialisasi kernel = template rata-rata kelas | P1 | **Uji, prioritas rendah** | `model.py` |
| 8 | Augmentasi scaling / magnitude warp / time warp | P6 §3.4 | **Uji, prioritas rendah** | `prep_beats.py` |
| 9 | Volume augmentasi per kelas `αc = 1 + α(1−accc)` | P6 Pers. 16 | **Uji bersama #8** | `ablasi.py` |
| — | Pooling berbobot (ganti GAP) | analisis sendiri | **Tunda** — K6 | — |
| — | Dua tahap V/S | P5, Yan (via P2) | **Tunda** — arsitektur + firmware + `.h` sekaligus | — |
| — | Volume per teknik `∝(acci−acc0)^β` | P6 Pers. 17 | **TOLAK** | — |
| — | GAN / BiLSTM augmentasi | P6 teknik 6–7 | **TOLAK** | — |
| — | Ganti normalisasi window | — | **DITARIK** (§1.1) | — |
| — | Test-time adaptation | BeatRhythm-TTA | **TOLAK** | — |

### Kenapa Pers. 17 (P6) ditolak

Rumusnya mengalokasikan volume augmentasi menurut `(acc_i − acc_0)^β` per
teknik. Selisih antar-teknik itu hampir pasti di bawah ambang noise kita
(changelog 18 Sep §B2: **selisih < ~0,04 F1 bukan sinyal**), dan pangkat β=2
justru **memperbesar** noise itu. Menjalankannya jujur butuh 3 seed × 7 teknik ×
tiap kelas. Tidak sepadan.

---

## 5. Urutan eksekusi yang diusulkan

Disusun agar tiap langkah bisa dinilai sendiri, dan yang termurah duluan.

| Tahap | Isi | Kenapa urutannya begini |
|---|---|---|
| **T0** | Baseline ulang 3 seed pada config terkunci | Tanpa ini tidak ada pembanding yang sah. Sudah ada di `ablasi.csv` (`w128b`), verifikasi masih reproduksi |
| **T1** | `class_weight=None` | 1 baris, nol risiko, potensi terbesar terhadap precision. Kalibrasi threshold **wajib** diulang |
| **T2** | QRSw2 + QRSw4 (K4) | Rank 1–2. Tidak butuh beat masa depan → tidak tersandera gate K2 |
| **T3** | RR jadi rasio + `RR+1/RR0` (K2, K3) | **Menunggu persetujuan gate K2** |
| **T4** | Input turunan + uji noise (K7) | Setelah fitur benar, supaya efeknya tidak tercampur |
| **T5** | k-dari-n + SQI, offline dari `fase6_per_record_fp32.csv` | Nol retraining. Bisa jalan paralel kapan saja |
| **T6** | Augmentasi P6 + Pers. 16 | Paling jauh dari akar masalah |

T2 dan T3 menyentuh file yang sama (`features_rr.py`) — kalau gate K2 disetujui
di muka, keduanya digabung jadi satu perubahan dan satu ablasi.

### Konsekuensi yang tidak boleh lupa

- Setiap perubahan `features_rr.py` mengubah `N_RR_FEATURES` → **bentuk input
  model berubah** → `model_int8.h` **dan** `golden_ref.h` wajib di-regen bersama
  (`golden_ref.h` = regression test, bukan pagar desain — lihat robustness-plan).
- `RR+1` menambah **tunda 1 beat** di firmware: keputusan tidak boleh keluar
  sebelum R berikutnya terdeteksi. Ring buffer dan urutan di `ecg_pipeline.cpp`
  ikut berubah.
- Threshold **wajib** dikalibrasi ulang di VAL setiap kali distribusi probabilitas
  bergeser (pelajaran 18 Sep: 0,35 → 0,80).

---

## 6. Gate point yang menunggu keputusanmu

| # | Pertanyaan | Kalau "ya" |
|---|---|---|
| **G1** | Boleh uji `class_weight=None`? Menabrak decision point K1 | Revisi baris "Strategi imbalance" di `CLAUDE.md` setelah ablasi |
| **G2** | Boleh tunda **1 beat** demi `RR+1`? Alasan penolakan lama menyebut tunda 5 beat | Revisi baris "Jendela `RR_local_avg`" jadi eksplisit soal besaran tunda |
| **G3** | `RR_LOCAL_WINDOW_BEATS` 10 → 32 boleh diuji? Nilai ini dari PRD | Uji sebagai varian ablasi, bukan diganti langsung |
| **G4** | Setuju **tidak** menambah sklearn untuk replikasi ranking MI? | Pakai ranking P3 sebagai hipotesis, validasi lewat `ablasi.py` |

G1 tidak tergantung apa pun — bisa jalan hari ini. G2 memblokir T3 saja.

---

## 7. Aturan metodologis yang berlaku

Diwarisi dari changelog 18 Sep §B2, **tidak bisa ditawar**:

1. **3 seed minimum** per varian. Ablasi 1 run tidak sah di repo ini.
2. Selisih **< ~0,04 F1 bukan sinyal** — oneDNN nondeterministik.
3. Dilaporkan sebagai **rerata ± setengah-rentang**, bukan angka tunggal.
4. DS2 **tidak pernah** dipakai memilih apa pun. Threshold dari VAL.
5. Dinilai dari **F1 + AUC**, bukan recall telanjang — tiap varian punya
   threshold sendiri.

---

## 8. Daftar pustaka

1. Farag, M.M. (2023). *A Tiny Matched Filter-Based CNN for Inter-Patient ECG
   Classification and Arrhythmia Detection at the Edge.* Sensors, 23(3), 1365.
   DOI 10.3390/s23031365
2. *A Systematic Review of ECG Arrhythmia Classification: Adherence to Standards,
   Fair Evaluation, and Embedded Feasibility.* arXiv:2503.07276 (2025).
3. Saenz-Cogollo, J.F.; Agelli, M. (2020). *Investigating Feature Selection and
   Random Forests for Inter-Patient Heartbeat Classification.* Algorithms, 13(4),
   75. DOI 10.3390/a13040075
4. Zhu, H.; Zhao, Y.; Pan, Y. (2021). *Robust Heartbeat Classification for
   Wearable Single-Lead ECG via Extreme Gradient Boosting.* Sensors, 21(16), 5290.
5. Huang, H.; Liu, J.; Zhu, Q. (2014). *A new hierarchical method for
   inter-patient heartbeat classification using random projections and RR
   intervals.* BioMedical Engineering OnLine, 13, 90.
   DOI 10.1186/1475-925X-13-90
6. Khosravi Khaliran, M.U.; Zabbah, I.; Faraji, M.; Ebrahimpour, R. (2024).
   *Improving deep learning in arrhythmia Detection: The application of modular
   quality and quantity controllers in data augmentation.* Biomedical Signal
   Processing and Control, 91, 105940. DOI 10.1016/j.bspc.2023.105940
7. de Chazal, P.; O'Dwyer, M.; Reilly, R.B. (2004). *Automatic Classification of
   Heartbeats Using ECG Morphology and Heartbeat Interval Features.* IEEE TBME,
   51(7), 1196–1206. *(sudah dipakai: split DS1/DS2)*
8. *False arrhythmia alarm reduction in the intensive care unit.*
   arXiv:1709.03562.
9. Tanatorn, T.; Nantajeewarawat, E.; Thiemjarus, S. (2014). *Toward continuous
   ambulatory monitoring using a wearable and wireless ECG-recording system.*
   DOI 10.3233/bme-130823
