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

## ⚠️ VONIS — dibaca SEBELUM isi dokumen (ditambahkan 19 Sep 2026, sore)

Dokumen ini ditulis **sebelum** Fase A–F dijalankan. Isinya masih berbunyi
seperti usul terbuka; sebagian besar sudah **diukur dan ditutup**. Hasil
pengukuran ada di [`2026-09-19-faseB-changelog.md`](2026-09-19-faseB-changelog.md);
keputusan final ada di tabel decision point [`../CLAUDE.md`](../CLAUDE.md).

**Teks asli sengaja TIDAK dihapus** — alasan yang menghasilkan usul yang kalah
sama berharganya dengan yang menang, dan §A changelog 18 Sep memang menuntut
divergensi rencana↔hasil dicatat, bukan dirapikan.

### Tesis utama dokumen ini TIDAK terbukti

§0 menyatakan *"fitur kita kurang, bukan model kita kecil"*. Setengah pertama
kalimat itu salah:

```
F1              fitur LAMA (3)    fitur BARU (6)
mitdb saja      0,6911 +-0,029    0,6882 +-0,023     <- yang TERPASANG
mitdb+svdb      0,6262 +-0,063    0,6960 +-0,049
```

Fitur peringkat 1–4 menurut mutual information dipasang, dan di mitdb **tidak
menggerakkan apa pun** (−0,003, ambang sinyal 0,04). Kenaikannya cuma muncul
saat ada kerusakan svdb untuk ditambal — interaksi murni, bukan perbaikan.

Setengah kedua (*"bukan model kita kecil"*, §2.3) masih berdiri. Jadi kedua
hipotesis besar sudah tertutup, dan yang tersisa justru yang paling kutunda:
**representasi** (K6 pooling, K7 input turunan).

### Status per temuan

| # | Usul | Vonis | Bukti |
|---|---|---|---|
| **K1** | matikan `class_weight` | ❌ **DIBANTAH** | P1 prediksi precision +31 poin; terukur **+0,3**. Kalibrasi threshold hilir menyerapnya (0,40 → 0,15). G1 DITUTUP |
| **K2** | `RR+1`, tunda 1 beat | ⚪ **G2 disetujui, TIDAK dikunci** | Diimplementasikan sampai firmware (`#if ECG_RR_RATIO`, `ecg_live.cpp` menilai `idx_hist-1`). Dorman karena K3 tidak menang |
| **K3** | fitur RR jadi rasio | ❌ **tidak menang** | Bagian dari "fitur BARU" di tabel atas |
| **K4** | lebar QRS (rank 1–2 MI) | ❌ **menang di MI, kalah di sini** | mitdb: recall V 0,944 → 0,898, recall F 0,152 → **0,029**. Knob `PA_QRSW=1` ditinggal |
| **K5** | jendela lokal 10 → 32 | ⬜ **BELUM DIUJI** | G3 masih terbuka |
| **K6** | pooling berbobot | ⬜ **BELUM DIUJI** | Ditunda dgn alasan "kapasitas bukan penyebabnya" — masih benar, tapi kini fitur juga bukan |
| **K7** | input turunan pertama | ⬜ **BELUM DIUJI** | Satu-satunya usul yang mengganti **representasi**, jadi tidak tercakup tabel 2×2 |
| **K8** | kelas F & Q tetap | ✅ **dikonfirmasi + diperkuat** | Sensitivitas: F sempurna pun cuma **+0,037 F1**. Izin berhenti memikirkan F/Q |
| **K9** | jangan tambah sklearn | ✅ **dihormati** | Ranking P3 dipakai sebagai hipotesis, divalidasi `ablasi.py` |
| **K10** | tetap PTQ | ✅ **tetap** — plus ranjau baru ketemu | `MAX_RHYTHM_SCALE` 0,05: satu beat RR ekstrem (rec 207, RR_prev 100 s) bisa mematikan cabang ritme, 1,8%/seed, **tanpa error**. Satu-satunya hal dari Fase A–F yang masuk produksi |
| **S3** | QRSw wajib ternormalisasi (resampling multi-DB) | ⭕ **GUGUR** | `DB_LATIH` kembali ke mitdb saja. Alasan bentuk ternormalisasi kembali ke bukti P3, bukan FS-invariance |

### Yang tetap benar dari dokumen ini

- §2.2 beban alarm palsu (**2.302 FP, precision 0,6235**) — masalahnya nyata dan
  belum terpecahkan. Tapi **obat yang diusulkan (T5 k-dari-n) sudah diukur dan
  GUGUR**, lihat di bawah.

### T5 (k-dari-n) ❌ GUGUR sebelum ditulis — `scripts/cek_fp.py`

Aturan "k beat berturut-turut" hanya menolong kalau FP lebih **tunggal**
daripada TP. Di DS2 justru **terbalik**:

```
TP (pred=1,y=1)   3813 beat  tunggal 87,0%  run>=3  3,7%
FP (pred=1,y=0)   2302 beat  tunggal 60,8%  run>=3 22,3%
  FP rec 222       781 beat  tunggal 33,7%  run>=3 43,8%
```

Menuntut k≥2 beat berturut-turut membuang **87% true positive** dan menyimpan
FP yang bergerombol — di rec 222 (penyumbang FP terbesar) 43,8% FP-nya selamat.
Aturan itu bukan cuma tidak menolong, ia **menyeleksi arah yang salah**.

Sebabnya struktural: 65,3% beat aritmia DS2 adalah kejadian **tunggal** (run
panjang 1). Label kita per-beat; k-dari-n itu alat untuk deteksi **episode**.
Salah alat, bukan salah parameter.

### Ke mana FP sebenarnya pergi (temuan pengganti)

**Menumpuk, bukan tersebar:** 2 record = 56,6% dari seluruh FP, 8 record = 92,4%
(dari 22). Ini kegagalan per-pasien.

| simbol | FP | %FP | n negatif | FPR simbol |
|---|---|---|---|---|
| N | 1568 | 68,1% | 36.401 | 0,043 |
| **L** (LBBB) | 536 | 23,3% | 4.121 | **0,130** |
| R (RBBB) | 187 | 8,1% | 3.471 | 0,054 |
| j (nodal escape) | 11 | 0,5% | 213 | 0,052 |

**L+R = 723 FP = 31,4%**, dan FPR beat LBBB **3× lipat** beat N biasa. Ini
tagihan terukur dari decision point yang sudah diambil sadar — *"L & R → N: ikut
AAMI... beda dari intuisi klinis"*. Beat LBBB memang QRS-nya lebar dan mirip
ventrikular; cabang morfologi menyalakannya, lalu label AAMI menyebutnya salah.

Rec 222 (FPR 0,344) beda lagi: isinya 83% N + 9% j (nodal escape) + 8% A —
ritme tak teratur, jadi cabang ritme yang menyala. Dua penyumbang terbesar,
dua mekanisme berbeda, **dua-duanya bukan derau yang bisa disaring waktu**.
- §2.3 perbandingan parameter (kita 6.417 vs P1 1.267).
- §7 aturan metodologis — dipakai terus, dan justru aturan inilah yang
  menyelamatkan Fase A–F dari menyimpulkan kenaikan palsu.

### Temuan BARU yang tidak ada di dokumen ini

1. **Fitur baru membuat recall S ANDAL, bukan lebih tinggi** — variansi
   ±0,156 → ±0,058. Sinyalnya ada, penyalurannya yang tidak.
2. **Pelajaran transferabilitas**: ablasi paper yang sah pun tidak berpindah
   kalau pipeline kita punya langkah adaptif yang mereka tidak punya (K1).
3. **Tabel 2×2 wajib**, bukan dua ablasi terpisah. Tanpa sel keempat
   (mitdb + fitur baru), kesimpulannya salah dua kali.

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
| **T0** ✅ | Baseline ulang 3 seed pada config terkunci | Tanpa ini tidak ada pembanding yang sah. Sudah ada di `ablasi.csv` (`w128b`), verifikasi masih reproduksi |
| **T1** ✅ | `class_weight=None` | 1 baris, nol risiko, potensi terbesar terhadap precision. Kalibrasi threshold **wajib** diulang — *hasil: K1 dibantah, +0,3 poin* |
| **T2** ✅ | QRSw2 + QRSw4 (K4) | Rank 1–2. Tidak butuh beat masa depan → tidak tersandera gate K2 — *hasil: Fase D, tidak dikunci* |
| **T3** ✅ | RR jadi rasio + `RR+1/RR0` (K2, K3) | ~~Menunggu persetujuan gate K2~~ — *G2 disetujui, diimplementasi s/d firmware, tidak dikunci* |
| **T4** ⬜ | Input turunan + uji noise (K7) | Setelah fitur benar, supaya efeknya tidak tercampur — **belum dikerjakan** |
| **T5a** ❌ | k-dari-n | ~~Nol retraining~~ — **GUGUR**, diukur `scripts/cek_fp.py`: FP lebih bergerombol daripada TP, aturan ini membuang 87% TP. Lihat blok VONIS |
| **T5b** ⬜ | gating SQI | Belum dikerjakan. Butuh rekaman badan, bukan MIT-BIH — MIT-BIH terlalu bersih untuk mengalibrasi ambang kualitas. Tempatnya firmware + HW-5 |
| **T6** ⬜ | Augmentasi P6 + Pers. 16 | Paling jauh dari akar masalah — **belum dikerjakan** |

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

## 5b. Fase G — lanjutan plan (ditambahkan 19 Sep 2026, sore)

Fase A–F berakhir **kunci nol**. Sebelum menambah percobaan sejenis, dicek dulu
apakah plan-nya menanyakan hal yang tepat. Lima tema di bawah **nol cakupan** di
seluruh `docs/` + `CLAUDE.md` — diverifikasi dengan grep, bukan kesan.

Dua kemenangan sepanjang proyek (`WIN_PRE` 128, augmentasi jitter) sama-sama
bukan soal fitur atau kapasitas, melainkan **cara window disajikan ke CNN**.
Itu prior untuk Fase G.

| # | Celah | Status di repo |
|---|---|---|
| **T7** | Variansi tidak pernah diserang | "ensemble", "rerata bobot" → **0 dokumen** |
| **T8** | TEST-B/TEST-C menganggur | dibangun Fase A, tidak pernah dilaporkan |
| **T9** | Fungsi loss tidak pernah diablasi | "focal" → **0 dokumen**; yang diablasi baru *bobot*-nya (K1) |
| **T10** | Representasi: pooling (K6) & input turunan (K7) | sudah di plan lama, belum dikerjakan |
| **T11** | Personalisasi / adaptasi per pasien | "personalisasi", "patient-specific" → **0 dokumen** |

### T7 — turunkan variansi (PENGGANDA, kerjakan duluan)

Dokumen ini sendiri sudah menyebut *"masalah yang sebenarnya adalah variansi
threshold antar-seed"* — tapi variansi hanya **diamati**, tidak pernah jadi
target.

Akibatnya lantai derau 0,04 F1 membuat perbaikan nyata **tidak terdeteksi**.
Sebagian vonis "bukan sinyal" di Fase A–F mungkin salah, dan tidak ada cara
tahu tanpa menurunkan variansinya dulu.

Mekanismenya sudah terdiagnosis di daftar jebakan `CLAUDE.md`: oneDNN mengubah
urutan penjumlahan float → `val_auc` bergoyang → EarlyStopping memilih epoch
berbeda → `restore_best_weights` mengembalikan bobot yang lain. **Lotere epoch.**

| Cara | Biaya deploy | Menyerang |
|---|---|---|
| **Rata-rata bobot N epoch ber-`val_auc` terbaik** | **nol** — tetap 1 model, 23 KB, arena & firmware tak berubah | lotere epoch, langsung di sumbernya |
| Ensemble 3 seed | 3×23 KB flash (dari 16 MB), 3×26,6 ms = 80 ms/detak (anggaran ~1 dtk) | variansi antar-seed |

Dipilih yang pertama: nol perubahan hilir, dan menyerang mekanisme yang sudah
terbukti ada. Alih-alih memungut argmax dari beberapa epoch yang nyaris seri,
**rata-ratakan yang nyaris seri itu.**

Gratisnya di sini bukan kebetulan: model kita **tidak punya BatchNorm**
(Conv1D → MaxPool → GAP → Dense), jadi tidak ada statistik BN yang harus
dihitung ulang setelah bobot dirata-rata — jebakan baku SWA yang tidak berlaku
buat kita.

Knob: `ablasi.py --swa N` (bawaan 0 = jalur terkunci, byte-identik). Pola sama
dengan `--tanpa-class-weight`: flag ablasi, bukan mengubah nilai final.

Kriteria: dinilai dari **rerata DAN setengah-rentang** 3 seed. Menang kalau
rentangnya menyempit — kenaikan rerata bonus, bukan syarat.

### T8 — laporkan TEST-B / TEST-C

85.812 beat, 39 pasien held-out svdb + incartdb, sudah dibangun Fase A dan
tidak pernah dipakai. Klaim generalisasi lintas-database kelas E3C yang **sudah
dibayar** — Farag (P1) divalidasi di INCART/QT/PTB dan review P2 menghargainya.
Nol eksperimen baru, murni evaluasi.

### T9 — ablasi fungsi loss

Objektifnya selalu `binary_crossentropy`; yang pernah diablasi cuma bobotnya.
Focal loss adalah jawaban baku untuk imbalance + contoh sulit. Satu baris di
`compile_model`, harness ablasi sudah ada. **Catatan K1 berlaku**: kalibrasi
threshold di hilir bisa menyerap efeknya juga — nilai dari F1 + rentang, bukan
dari recall telanjang.

### T11 — personalisasi (SCOPING dulu, jangan langsung implementasi)

Lever terbesar yang belum disentuh, dan satu-satunya yang menjelaskan
konsentrasi FP (2 pasien = 57%).

- `CLAUDE.md`: *"Overfit di sini akar masalahnya variasi antar-pasien"*
- Mao dkk. (via P2): on-chip learning 93,67% → 97,36%, specificity 55,54% → 82,30%

Versi murah = **titik operasi per pasien**, bukan belajar bobot. Tapi kalibrasi
tanpa label butuh jangkar tak-terawasi, dan itu belum jelas. **Jangan asumsikan
gampang** — keluarkan dokumen scoping dulu.

### T7 ❌ KALAH — dan kekalahannya menemukan yang lebih besar

Dijalankan `--swa 3`, 3 seed, konfigurasi identik `w128b` (n_train 121.857):

```
w128b    F1 0,6911 +-0,0290   AUC 0,9373
g_swa3   F1 0,6346 +-0,0387   AUC 0,9215
         dF1 -0,0565 (DI ATAS ambang 0,04 = SINYAL)   rentang MELEBAR
```

Gagal di kedua sisi: bukan cuma tidak lebih baik, variansinya juga tidak
menyempit.

**Diagnosis mencetak epoch mana yang dirata-rata: `[0, 1, 2]`** — tiga epoch
PERTAMA, dan bersebelahan. Hipotesis awalku (epoch terpilih berjauhan, basin
beda) **salah**. Sebab sebenarnya terlihat di kurvanya:

```
seed 42 (+swa)          seed 7 (jalur terkunci)
epoch 0  val_auc 0,8847     epoch 0  val_auc 0,9492   <- puncak
epoch 1          0,8347     epoch 1          0,9345
epoch 2          0,7985     epoch 2          0,9279
...                         ...
epoch 8          0,6702     epoch 8          0,8635
train auc        0,9968
```

`val_auc` memuncak di **epoch 0** lalu turun **monoton**, di kedua seed, dengan
dan tanpa SWA. Dengan `patience=8`, training selalu jalan 9 epoch lalu
`restore_best_weights` mengembalikan epoch 0.

> **Model produksi kita adalah model setelah SATU epoch. Delapan epoch sisanya
> murni overfitting.**

T7 tidak bisa diperbaiki dengan aturan rata-rata yang lebih pintar: **tidak ada
"nyaris seri" untuk dirata-rata.** Puncaknya di tepi dan kurvanya menurun, jadi
merata-rata apa pun berarti menarik masuk bobot yang lebih buruk.

### T12 — learning rate (BARU, lahir dari diagnosis T7)

`CLAUDE.md` mengunci: *"Learning rate: default adam (1e-3), tidak disetel —
knob yang **belum terbukti perlu** = ruang tuning yang harus dipertanggungjawabkan
di sidang."*

Alasan itu kini **gugur oleh bukti**: dengan 1e-3 model overfit dalam satu
epoch. Itu bukan kemewahan tuning, itu regime latih yang rusak.

Dan ini kemungkinan besar **sumber variansi yang dicari T7**: kalau model
terbaik selalu epoch 0, maka yang menentukan hasil adalah inisialisasi + urutan
batch satu epoch pertama — persis besaran acak yang bikin rentang F1 ±0,029.
Masalah variansi dan masalah learning rate mungkin **satu masalah yang sama**.

Knob: `ablasi.py --lr 1e-4` (bawaan 0 = 1e-3 bawaan Adam = jalur terkunci).

⚠️ **Gate point** kalau menang: mengubah `Learning rate` di tabel decision point.
Sampai itu terjadi, `--lr` adalah flag ablasi, bukan nilai final.

#### Hasil T12 (`--lr 1e-4`, 3 seed, konfigurasi `w128b`)

```
tag        n           F1        recall S            AUC          thr
w128b      3  0,6911 +-0,0290  0,4221 +-0,1555  0,9373 +-0,0087  0,633
g_lr1e4    3  0,6827 +-0,0096  0,3019 +-0,0806  0,9461 +-0,0065  0,467

dF1 -0,0083 (bukan sinyal)   rentang F1 MENYEMPIT 0,0290 -> 0,0096  (3x)
dAUC +0,0089                 rentang AUC menyempit 0,0087 -> 0,0065
```

**Inilah yang T7 seharusnya berikan, dan T12 yang memberikannya.** F1 tidak
bergerak, tapi dua hal berubah ke arah benar sekaligus:

1. **Lantai derau turun 3×.** Setengah-rentang 0,0290 → 0,0096. Ambang "bukan
   sinyal" 0,04 selama ini ditetapkan oleh variansi ini; kalau rentangnya
   sepertiga, perbaikan sebesar 0,015 yang selama ini tak terlihat jadi bisa
   disimpulkan. Ini efek **pengganda** yang dicari §5b.
2. **AUC naik dan ikut menyempit.** AUC bebas threshold, jadi ia mengukur mutu
   pengurutan model — bukan titik operasi. Naik 0,0089 berarti modelnya memang
   memeringkat lebih baik, bukan sekadar bergeser.

**Yang harus dibaca hati-hati:** recall S turun 0,120. Tapi thresholdnya BEDA
(0,633 → 0,467), dan §A5 changelog 18 Sep melarang membandingkan recall di dua
titik operasi berbeda — itu membandingkan dua hal berbeda. AUC yang naik
menunjukkan pengurutan membaik; penurunan recall S kemungkinan besar artefak
titik operasi, **tapi itu hipotesis, belum diukur.**

**Batas kejujuran:** setengah-rentang dari n=3 itu sendiri estimasi kasar.
Klaim "variansi turun 3×" perlu lebih banyak seed sebelum dikunci. Yang sudah
kuat: arahnya konsisten di F1 DAN AUC sekaligus.

#### Mekanisme terkonfirmasi — kurva `val_auc` berubah bentuk

Seed 7, konfigurasi identik, hanya learning rate yang beda:

```
lr 1e-3 (terkunci)            lr 1e-4
epoch 0  0,9492  <- puncak    epoch 0   0,8797   naik
epoch 1  0,9345               epoch 2   0,9067
epoch 2  0,9279               epoch 2-19  dataran ~0,905-0,911
...  turun monoton            epoch 18  0,9113  <- puncak
epoch 8  0,8635  BERHENTI     epoch 26  0,9082  BERHENTI
9 epoch, 8 terbuang           27 epoch, membaik selama 19
```

Regime-nya benar-benar berubah: dari "overfit sejak epoch pertama" jadi
"membaik perlahan lalu mendatar".

#### Per seed — dan kenapa baseline terlihat lebih baik dari yang sebenarnya

| seed | F1 w128b → lr1e-4 | AUC w128b → lr1e-4 |
|---|---|---|
| 42 | 0,6691 → **0,6718** | 0,9375 → **0,9473** |
| 13 | 0,6770 → **0,6910** | 0,9285 → **0,9521** |
| 7 | **0,7271** → 0,6854 | **0,9458** → 0,9391 |

**Dua dari tiga seed membaik di F1 DAN AUC.** Yang memburuk cuma seed 7 — dan
seed 7 adalah **seed hoki baseline**: F1 0,7271 jauh di atas saudaranya
(0,669 / 0,677), recall S 0,6095 vs 0,358 / 0,299.

Jadi rerata baseline yang 0,6911 itu sebagian ditopang satu lotere yang menang.
Menutup loterenya membuat rerata nyaris tak bergerak tapi outlier-nya hilang —
dan lotere yang sama bisa saja menghasilkan outlier ke arah sebaliknya.

Revisi atas catatan recall S di atas: penurunannya **tidak konsisten antar
seed** (13 naik, 42 turun, 7 turun jauh), dan didominasi hilangnya outlier
seed 7. Bukan "recall S memburuk", tapi "recall S berhenti mengayun".

#### ⚠️ Temuan metodologis: `val_auc` TIDAK bisa memilih antar regime

Puncak `val_auc` di 1e-3 (**0,9492**) lebih TINGGI daripada di 1e-4 (**0,9113**)
untuk seed yang sama — padahal 1e-4 lebih baik di DS2 pada 2 dari 3 seed.

**Memakai VAL untuk memilih learning rate akan memilih yang kalah.**

Tugas VAL adalah memilih *epoch di dalam satu run* — itu sah dan tetap.
Memilih *antar regime hyperparameter* adalah tugas lain, dan 5 pasien tidak
cukup untuk itu. Ini bukti kedua yang independen: Fase E sudah menemukan hal
yang sama (presisi nama V 91,7% di DS2 vs maksimum 43,9% di VAL).

**Akibatnya T8 naik prioritas:** TEST-B/TEST-C (39 pasien held-out, 85.812
beat) adalah wasit yang tepat untuk gate T12 — bukan VAL yang terlalu kecil,
bukan DS2 yang haram memilih.

#### Hasil T8 — wasit lintas-database untuk gate T12

3 seed × 2 regime, tag baru (`t8_lr1e3` / `t8_lr1e4`) supaya baris lama tak
terkontaminasi. Threshold tetap dari VAL, tidak pernah disetel di set uji.

| Set | n pasien | F1 lr 1e-3 | F1 lr 1e-4 | vonis F1 | AUC |
|---|---|---|---|---|---|
| DS2 (mitdb) | 22 | 0,6535 ±0,0280 | 0,6729 ±0,0483 | +0,019 bukan sinyal | 0,9305 → **0,9415** |
| **TEST-B** (svdb) | 20 | 0,5237 ±0,0084 | 0,5306 ±0,0339 | +0,007 bukan sinyal | 0,8667 → **0,8860** |
| **TEST-C** (incartdb) | 19 | 0,6784 ±0,1080 | **0,8025 ±0,0277** | **+0,124 SINYAL** | 0,9352 → **0,9525** |

**AUC naik di 4 dari 4 set evaluasi** (+0,009 sampai +0,019). AUC bebas
threshold, jadi ia mengukur mutu pengurutan — dan konsistensi 4/4 itu
argumennya, bukan besar tiap deltanya.

#### ⚠️ Tapi ada pertukaran yang tajam: S ditukar V

Per seed di DS2 (batch t8):

| seed | F1 | AUC | recall **S** | recall **V** |
|---|---|---|---|---|
| 13 | 0,6523 → **0,7091** | 0,9258 → **0,9507** | 0,2859 → **0,3099** | 0,9161 → **0,9671** |
| 42 | 0,6261 → **0,6970** | 0,9233 → **0,9517** | 0,4771 → *0,3834* | 0,8664 → **0,9758** |
| 7 | 0,6821 → *0,6125* | 0,9424 → *0,9219* | 0,5790 → *0,2446* | 0,9627 → **0,9779** |

**recall V naik di 3 dari 3 seed. recall S turun di 2 dari 3**, dan turun juga
di rerata DS2 (−0,135) dan TEST-C (−0,043); naik hanya di TEST-B (+0,035).

Yang bikin ini serius: threshold lr 1e-4 **lebih longgar** (0,53 vs 0,65).
Threshold lebih rendah seharusnya MENAIKKAN recall. Recall S tetap turun —
jadi ini bukan artefak titik operasi seperti dugaanku sebelumnya, melainkan
**model yang memang memeringkat beat S lebih buruk**.

F1 dan AUC tetap naik karena V mendominasi jumlah beat aritmia. Artinya
lr 1e-4 **memperbaiki kelas yang sudah kuat dan memperburuk kelas yang lemah** —
arah yang berlawanan dengan kebutuhan proyek ini.

Catatan: seed 7 jadi seed "pro-S" di kedua batch (baseline recall S 0,6095 dan
0,5790). Reproduksibel, jadi bukan lotere murni — ada sesuatu di lintasan
seed 7 pada 1e-3 yang menemukan solusi pendeteksi S.

#### ❌ KOREKSI: klaim "variansi 3× lebih sempit" TIDAK bereplikasi

Batch pertama memberi `g_lr1e4` setengah-rentang F1 DS2 **±0,0096**. Batch
kedua, konfigurasi identik, memberi `t8_lr1e4` **±0,0483** — lebih lebar dari
baseline. Klaim itu **ditarik**: dengan n=3, setengah-rentang itu sendiri
estimasi yang sangat berisik, dan aku menyimpulkannya dari satu batch.

Yang tersisa dari T12 adalah kenaikan AUC yang konsisten, bukan variansi.

#### 🔴 Temuan baru: ambang 0,04 berlaku untuk RERATA 3 SEED, bukan cuma 1 run

Konfigurasi identik, seed identik, dijalankan dua kali:

```
w128b     F1 DS2 0,6911 +-0,0290     (batch 1)
t8_lr1e3  F1 DS2 0,6535 +-0,0280     (batch 2, konfigurasi SAMA PERSIS)
selisih   0,0376  — nyaris menyentuh ambang 0,04
```

Selama ini §7 no.1 dibaca sebagai "1 run tidak sah, pakai 3 seed". Ternyata
**rerata 3 seed pun bergoyang ~0,04 antar batch.** Konsekuensinya: selisih
di bawah 0,04 tidak jadi sinyal hanya karena diulang 3 seed — ia butuh
pengulangan batch, atau set uji yang jauh lebih besar (justru itu gunanya
TEST-B/TEST-C).

Ini memperkuat, bukan melemahkan, vonis TEST-C: +0,124 bertahan jauh di atas
lantai derau mana pun yang terukur di sini.

#### T7 layak ditinjau ulang SETELAH T12

Di 1e-4 sekarang **ada dataran** (epoch 15–20 semua ~0,910). Dataran itu
justru prasyarat yang dibutuhkan rata-rata bobot, dan yang tidak ada di 1e-3.
T7 mungkin tidak salah secara prinsip — ia diterapkan pada regime yang tidak
punya dataran untuk dirata-rata.

### Urutan Fase G (diperbarui 2×, setelah hasil T12)

**T12 → T8 → T9 → T10 → T7' → T11.**

| Tahap | Status |
|---|---|
| **T12** learning rate | ✅ dijalankan. AUC naik 4/4 set, TEST-C F1 +0,124 (SINYAL) — **tapi recall S turun**. Klaim variansi ditarik. **Menunggu gate, dan ini pertukaran, bukan kemenangan bersih** |
| **T8** TEST-B/TEST-C | ✅ dijalankan sebagai wasit T12. `--lintas-db` kini bagian harness; tiap ablasi bisa melapor 39 pasien held-out |
| **T9** fungsi loss | ⬜ sekarang lebih layak: lantai derau lebih rendah = efek kecil bisa terlihat |
| **T10** representasi (K6/K7) | ⬜ idem |
| **T7'** rata-rata bobot, ULANG di 1e-4 | ⬜ dataran sudah ada, prasyaratnya baru terpenuhi |
| **T11** personalisasi | ⬜ scoping |

T7 (versi 1e-3) gugur. **T12 naik ke puncak** — kalau benar seluruh proyek
melatih model satu epoch, tiap ablasi sebelumnya membandingkan model yang
nyaris belum belajar, dan itu menjelaskan kenapa hampir semuanya berakhir
"bukan sinyal".

---

## 6. Gate point yang menunggu keputusanmu

| # | Pertanyaan | Kalau "ya" |
|---|---|---|
| **G1** ✅ **DITUTUP** | Boleh uji `class_weight=None`? Menabrak decision point K1 | Diuji → **K1 dibantah**. `class_weight` TETAP, dan sekarang alasannya bukan lagi asumsi melainkan ablasi sendiri |
| **G2** ✅ **DISETUJUI** | Boleh tunda **1 beat** demi `RR+1`? Alasan penolakan lama menyebut tunda 5 beat | Disetujui & diimplementasi sampai C (`ecg_live.cpp` menilai `idx_hist-1`, `r_hist[16]` sudah memuat RR+1, `ECG_LIVE_TIMEOUT` 3 dtk utk asistol). **Dorman** — `PA_RR_RATIO` tidak dikunci |
| **G3** ⬜ **MASIH TERBUKA** | `RR_LOCAL_WINDOW_BEATS` 10 → 32 boleh diuji? Nilai ini dari PRD | Uji sebagai varian ablasi, bukan diganti langsung |
| **G4** ✅ **DIHORMATI** | Setuju **tidak** menambah sklearn untuk replikasi ranking MI? | Pakai ranking P3 sebagai hipotesis, validasi lewat `ablasi.py` — dijalankan persis begitu |

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
