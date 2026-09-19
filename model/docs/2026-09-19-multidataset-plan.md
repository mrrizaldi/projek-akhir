# Fase A — gabungkan mitdb + svdb + incartdb

**19 September 2026. Rencana EKSEKUSI, branch `feat/multidataset`.**
Eksperimental: tidak di `main` sampai Fase B memberi angka.

Lanjutan dari [`2026-09-19-fitur-design.md`](2026-09-19-fitur-design.md).
Aturan metodologis §7 dokumen itu berlaku penuh (3 seed minimum, selisih
< 0,04 F1 bukan sinyal, DS2 tak pernah memilih apa pun).

---

## 0. Kenapa ada fase ini

Permintaan pembimbing dari awal: perluas data latih. Setelah diukur, permintaan
itu ternyata menjawab dua kelemahan yang tersisa dari Fase 6c:

```
recall S  0,422 +- 0,156   rapuh & tak stabil   -> svdb
recall F  0,152 +- 0,067   n=1 pasien efektif   -> incartdb
recall V  0,944 +- 0,007   sudah selesai
```

### Diagnosis F yang baru — bukan dari paper, dari data sendiri

```
DS1: 372 dari 414 beat F  ->  record 208   (90%)
DS2: 362 dari 388 beat F  ->  record 213   (93%)
```

Split inter-patient kita, **untuk kelas F**, sebenarnya berbunyi: latih morfologi
fusi satu orang, uji di morfologi fusi satu orang lain. recall 0,152 bukan
kegagalan implementasi — itu angka yang benar untuk generalisasi n=1 → n=1.

Ini argumen yang lebih kuat daripada mengutip P1/P3 juga gagal, dan bisa masuk
paragraf pembatasan laporan apa adanya.

---

## 1. Kandidat: kriteria, bukan selera

**Syarat mutlak: anotasi BEAT-LEVEL** (`.atr`, satu simbol per R-peak) dengan
alfabet WFDB yang sama. Kalau itu dipenuhi, `AAMI_MAP` di `config.py` sudah
menanganinya tanpa mapping baru, dan decision point *"simbol di luar AAMI_MAP →
KeyError"* justru jadi penjaga yang kita mau: simbol asing berisik, bukan lolos.

Yang **dibuang, dan bukan karena frekuensi**: PTB-XL, CPSC-2018, Chapman/Ningbo,
PhysioNet Challenge 2020/2021. Semuanya punya **diagnosis per-rekaman**, bukan
per-beat. Label per-beat tidak bisa diturunkan dari diagnosis per-rekaman —
informasinya tidak ada di sana, berapa pun laju cupliknya.

### Yang dipakai (header asli PhysioNet, diverifikasi 19 Sep)

| db | rec | fs | lead dipakai | peran |
|---|---|---|---|---|
| `mitdb` | 48 | 360 Hz | **MLII** | acuan; DS1/DS2 de Chazal |
| `svdb` | 78 | 128 Hz | ECG1 ⚠️ | **kelas S** |
| `incartdb` | 75 | 257 Hz | **II** | **sebaran F**, + V |

### Sebaran terukur (anotasi asli → `AAMI_MAP`, bukan angka paper)

| Kelas | DS1-latih | svdb | incartdb |
|---|---|---|---|
| N | 36.514 | 162.339 / 78 rec | 153.676 / 75 rec |
| S | **634** (~20 rec) | **12.198 / 73 rec** | 1.960 / 36 rec |
| V | 3.071 | 9.943 / 67 rec | 20.013 / 70 rec |
| F | 394 (**372 di rec 208**) | 23 / 6 rec ❌ | **219 / 22 rec** |
| Q | 6 | 79 / 20 rec | 6 / 5 rec |

Dibekukan di [`../tests/test_multidataset.py`](../tests/test_multidataset.py).

**S: selesai.** 634 → ~11.250 beat, ~20 → ~102 pasien, dan record terbesar svdb
cuma 15% dari total S-nya. Tidak ada satu pasien pun yang bisa mendominasi.

**F: cakupan naik, bobot tidak.** Jujurnya dua metrik bergerak berbeda arah:

| | sebelum | sesudah |
|---|---|---|
| pasien penyumbang F | 7 (efektif **1**) | ~31 ✓ |
| konsentrasi beat di 1 record | 94% | **64%** — masih rec 208 |

Gradien tetap didominasi morfologi F record 208 (372 dari 577 beat latih). Obat
yang mungkin: subsample F rec 208. **Tidak dilakukan** — F cuma 1,2% positif,
dan itu knob yang harus dipertanggungjawabkan untuk plafon yang rendah. Biarkan
Fase B yang bicara.

**Q: mati, final.** 8 + 79 + 6 = **93 beat** di tiga database beranotasi-beat
terbesar yang kompatibel, digabung. Q bukan kelas yang bisa dilaporkan, dan
sekarang ada tiga database sebagai bukti. Q permanen masuk keranjang
"Aritmia — tipe tak pasti", **tanpa nama**.

### Trade-off yang tidak menyenangkan

Database yang menyelesaikan kelas terburuk punya frekuensi terburuk:

```
resolusi lebar QRS:  mitdb 360 Hz -> 2,8 ms/sampel
                     incartdb 257 -> 3,9 ms
                     svdb     128 -> 7,8 ms      <- sumber S terbaik
ambang V vs S: 120 ms
```

QRSw adalah fitur **rank 1–2** (K4) untuk memisahkan S dari V, dan beat S baru
datang dalam resolusi paling kasar untuk fitur yang paling penting bagi mereka.
**Konsekuensi wajib: metrik dilaporkan PER-SUMBER.** Kalau T2 (QRSw) gagal,
tersangka pertamanya ini, bukan fiturnya.

---

## 2. Frekuensi: satu jebakan, satu arah, tiga keputusan

**Window terdefinisi dalam SAMPEL, bukan waktu.**

```
128 sampel @ 360 Hz =  355 ms   <- yang diablasi & dikunci 18 Sep
128 sampel @ 128 Hz = 1000 ms   <- fisiologi lain sama sekali
```

Decision point 18 Sep: yang membayar itu *"konteks 128 sampel SEBELUM R"*, dan
mekanismenya gelombang P & interval PR di ~150–200 ms sebelum R. Itu durasi
**fisiologis**. Memakai 128 sampel di 128 Hz bukan menyalin keputusan itu — itu
melanggarnya sambil terlihat konsisten.

**Arahnya 360 Hz**, tidak menurunkan mitdb ke 128. Konsekuensinya: `WIN_PRE`/
`WIN_POST`, koefisien `ecg_sos`, `ECG_FS` di firmware, dan `golden_ref.h`
**semuanya tidak berubah**. Firmware nol sentuhan di seluruh Fase A.

### Dua keputusan terkunci yang kebetulan sudah membayar

| Sudah ada | Kenapa gratis di sini |
|---|---|
| `d = np.diff(r) / fs` → RR dalam **detik** | fitur RR otomatis fs-independen |
| z-score **per window** | gain/kalibrasi mV antar-database mati sendiri |

Keduanya dipilih untuk alasan lain. Keputusan yang **general** lebih berharga
dari yang optimal.

### Tiga keputusan di `resample_to_fs()`

1. **`resample_poly` (polyphase FIR), bukan `resample` (FFT).** `resample`
   mengasumsikan sinyal periodik; EKG tidak periodik dan punya baseline wander,
   jadi tepi rekaman berdenyut. `resample_poly` linear-phase dan scipy sudah
   mengompensasi group delay-nya. Rasio direduksi lewat `gcd`: 128→360 = 45/16,
   257→360 = 360/257. scipy sudah di `requirements.txt` — nol dependency baru.

2. **Posisi R = pembulatan saja, tanpa cari-ulang puncak.** Bukan kemalasan —
   anggarannya cukup. Pembulatan meleset ≤0,5 sampel, sisa group delay
   sub-sampel, total <1 sampel. Ambang bahaya repo ini **4 sampel** (meleset 4
   menjatuhkan precision 0,48 → 0,12), dan jitter empiris memang dilatih untuk
   residu ±1–2 sampel. Cari-ulang puncak punya risiko sendiri: `argmax` bisa
   pindah ke ekstremum yang salah pada beat V/F bermorfologi aneh.
   Terverifikasi: sinyal sintetis → pergeseran **0,00 sampel**; svdb asli →
   `test_resample_kontrak[svdb]` hijau.

3. **Dipanggil SEBELUM `apply_bandpass`.** Semua database lewat `sos` yang sama
   di 360 Hz. Kalau dibalik, tiap database dapat respons filter sedikit berbeda —
   dan golden reference cuma menjamin satu: `sos` di 360 Hz.

Yang **tidak** dilakukan: menyaring `r` yang keluar batas. `symbols` sejajar
dengan `r` lewat indeks, jadi membuang satu `r` memutus kesejajaran tanpa suara.
Batas window tetap urusan `prep_beats.valid_beat_indices()` — satu tempat,
senada decision point *"prep_beats yang menyaring (opsi C)"*.

Ongkos terukur: 30 menit sinyal, kedua rasio, **0,01 s**.

### Yang resample TIDAK lakukan

Menciptakan informasi. svdb 128 Hz tetap punya detail lebih sedikit setelah
di-upsample — bentuknya cocok, detailnya tidak muncul. Format seragam
menyembunyikan kualitas yang tidak seragam; itu sebabnya §1 menuntut metrik
per-sumber.

---

## 3. Gate point yang menunggu keputusan

| # | Pertanyaan | Kalau "ya" |
|---|---|---|
| **A3** | Subsample F record 208 supaya ragam F tidak tenggelam? | **DITOLAK** — alasan terukur di §3c |
| **A4** | `2026-09-19-fitur-design.md` masih untracked di `main` | commit sendiri — bukan milik Fase A |

**A1 (siapa mengisi `resample_to_fs`) sudah tertutup**: aturan "USER yang
menulis logika algoritma" dihapus dari `CLAUDE.md` pada 19 Sep, dan fungsinya
diimplementasikan — keputusannya di §2 di bawah, semuanya bisa diubah.

**A2 (polaritas lead svdb) sudah tertutup** — diukur, bukan diasumsikan; hasil &
temuan tak terduga di §3b.

Sisa gate: **A3** (subsample F rec 208) dan **A4** (`fitur-design.md` untracked).
Keduanya tidak memblokir.

---

## 3b. Gate A2 — dua temuan, satu dicari satu tidak

`scripts/cek_lead.py`. Yang diukur: nilai window ter-z-score **di indeks R = 132**
(`WIN_PRE` + group delay), dirata-rata atas beat **normal saja** (beat V/F memang
bermorfologi aneh dan bisa negatif di lead yang benar). Itu persis angka yang
dilihat model.

### Temuan 1 — lead: ECG1 benar

| lead | mean (mentah) | record positif | vonis |
|---|---|---|---|
| `mitdb/MLII` | +4,053 | 88% (rec 108 memang berisik) | acuan |
| `svdb/ECG1` | +1,673 | **100%** | **sebanding** ✓ |
| `svdb/ECG2` | −0,390 | 50% | **terbalik** ✗ |
| `incartdb/II` | +3,146 | 100% (n=1, sementara) | sebanding |

`DATASETS["svdb"]["leads"]` dipersempit ke `("ECG1",)`.

### Temuan 2 — yang TIDAK dicari: konvensi anotasi antar-database beda

Posisi puncak relatif anotasi, sinyal ter-bandpass, beat normal:

```
mitdb  median  +3   p5..p95  +1..+5     <- anotasi DI puncak; +3/+4 = group delay
svdb   median +10   p5..p95  -2..+15    <- ~6 sampel lebih awal, sebaran 3x lebar
```

Bias **+6 sampel** itu di atas ambang bahaya repo ini (meleset 4 → precision
0,48 ke 0,12) **dan sistematis**, bukan jitter zero-mean. Tanpa koreksi tiap beat
svdb tergeser searah, dan model membacanya sebagai morfologi lain — persis
"belajar identitas dataset" yang dilawan split inter-patient. Gejalanya di Fase B
bukan error, cuma *"dataset baru tidak menolong"*.

**Perbaikan pakai mekanisme yang sudah ada** (`haluskan()` di
`eval_detected_segmentation.py`, `ecg_align_r()` di firmware): geser ke puncak,
lalu kembalikan group delay. `ALIGN_WIN = 16` (±44 ms) menutup p1..p99 svdb
(−9..+15) tanpa menjangkau gelombang T (~200–300 ms = 72–108 sampel).
**Bukan** `PT_REFINE_WIN = 25` — itu untuk sebaran detektor Pan-Tompkins.

Hasilnya:

| | sebelum | sesudah |
|---|---|---|
| `svdb/ECG1` mean di R | +1,673 | **+4,533** (mitdb: +4,487) |
| puncak mendarat di | 135–141 | **132** (7/8 record) |
| record dengan 100% beat positif | 3/8 | **8/8** |

Record 802 menunjuk 147 karena gelombang S-nya dalam — metrik `puncak_di`
mengukur amplitudo **absolut**, jadi bisa menunjuk S alih-alih R. Dibaca bareng
`mean` (802 = +3,656, 100% positif) posisinya benar.

### Cacat di skrip cek sendiri, diperbaiki

`selaraskan_r` memakai **signed argmax**, jadi dia **memaksa** nilai di R jadi
positif — lead terbalik pun tampak sebanding sesudahnya (`ECG2` melompat dari
−0,390 ke +1,099). Vonis polaritas **hanya sah dari kolom mentah**.
`cek_lead.py` sekarang mencetak dua kolom dan dua vonis terpisah.

### mitdb: dibuktikan tak bergeser

`selaraskan=False` untuk mitdb, dan bukan cuma dideklarasikan: **44/44 record
byte-identik** setelah Fase A, termasuk undian jitter (urutan `rng` bersama
seperti `main()`). Semua ablasi terkunci tetap reproducible. Dijaga
`test_jalur_mitdb_byte_identik_setelah_fase_a` untuk rec 100 & 232.

---

## 3c. Gate A3 ditolak — analisis sensitivitas

Pertanyaannya: subsample beat F record 208 (372 dari 577 beat F latih) supaya
ragam F dari 22 pasien incartdb tidak tenggelam?

**Jawaban: jangan**, dan alasan pertama menutup pembahasan sendiri.

### 1. Bahkan F yang SEMPURNA pun di bawah ambang sinyal

Sensitivitas F1 biner kalau recall satu kelas dinaikkan ke 1,0 (FP tetap — kita
cuma menangkap positif yang terlewat). DS2 terukur, recall biner 0,710
diturunkan dari F1 0,691 & precision 0,673 (ablasi w128b, 3 seed):

| kelas | % positif DS2 | recall kini | TP tambahan kalau sempurna | ΔF1 |
|---|---|---|---|---|
| **S** | 33,7% | 0,422 | 1.061 | **+0,113** |
| V | 59,1% | 0,944 | 180 | +0,021 |
| **F** | 7,1% | 0,152 | 329 | **+0,037** |
| Q | 0,1% | 0,000 | 7 | +0,001 |

Ambang sinyal repo (changelog 18 Sep §B2): **selisih < 0,04 F1 bukan sinyal.**

Jadi F recall 1,0 — sempurna, mustahil — memberi **+0,037, masih di bawah
ambang**. Subsample memberi sebagian kecil dari itu. Eksperimennya **tidak bisa
dinilai**: naik pun tak bisa dibedakan dari noise. Menjalankan ablasi yang
hasilnya mustahil ditafsirkan = 3 seed dibakar untuk nol informasi.

### 2. Premis "dominasi gradien" itu salah untuk tugas biner

```
train total        292.594
  semua kelas F        577  = 0,20% training
  F dari rec 208       372  = 0,13% training
  N                 262.006 = 89,5% training
```

0,13% tidak mendominasi 89,5%. "Dominasi" relevan kalau kita mengklasifikasi F
**sebagai kelas**; kita tidak — F cuma salah satu bentuk positif. Sebab recall F
rendah bukan bobot gradien, tapi **cakupan pasien**: F di DS2 datang dari pasien
213 yang morfologinya tak pernah dilihat model. Obatnya pasien baru, dan itu
sudah dikerjakan incartdb.

### 3. Subsample menambah nol informasi

```
subsample 208 ke 100  ->  buang 272 beat POSITIF (0,9% positif train)
                      ->  NOL pasien F baru
```

Sisi kreditnya kosong.

### 4. Beban pembelaan

"Kenapa ke 100, bukan 150?" — konstanta pilihan tanpa ablasi, dan ablasinya
tidak bisa dijalankan (alasan 1). Itu akan jadi satu-satunya angka di repo ini
tanpa justifikasi terukur; bandingkan window 128/128, jitter x2, threshold 0,80.

### Yang dipakai sebagai ganti (nol ongkos)

Tabel sensitivitas di atas masuk **paragraf pembatasan laporan**. Dia mengubah
*"recall F kami 0,15"* jadi *"recall F secara struktural tidak bisa memperbaiki
angka utama, dan ini hitungannya"* — pembelaan, bukan permintaan maaf.

Konsekuensi yang lebih luas: hanya **S** yang layak dikerjakan untuk metrik yang
dilaporkan (+0,113, hampir 3x ambang). V sudah habis (0,944), F dan Q struktural.
Itu memvalidasi ke belakang bahwa memprioritaskan svdb benar, dan memberi izin
berhenti memikirkan F/Q sebagai target perbaikan.

---

## 4. Split: satu aturan mengunci semuanya

```
TRAIN    mitdb DS1 (17 rec)  +  svdb 58 rec  +  incartdb 56 rec
VAL      mitdb 101,114,201,220,223         <- MURNI mitdb
TEST-A   mitdb DS2 (22 rec)                <- ANGKA UTAMA, sebanding literatur
TEST-B   svdb 20 rec held-out              <- generalisasi antar-database
TEST-C   incartdb 19 rec held-out          <- generalisasi antar-database
```

**DS2 tidak berubah satu byte.** Dua alasan: (1) de Chazal DS1/DS2 satu-satunya
yang bikin F1 kita sebanding dengan P1/P3 — ganti test set, tabel §2.3 tidak bisa
dibaca lagi; (2) §7 aturan 4 cuma bisa ditegakkan kalau komposisi DS2 bukan
variabel. Dijaga oleh `test_ds2_mitdb_tidak_tersentuh_fase_a`.

**VAL tetap murni mitdb**, dan alasannya sekarang lebih kuat:

```
VAL    aritmia 10,11%
DS2    aritmia 10,98%   <- VAL cermin DS2 ✓
TRAIN  aritmia 12,10%   <- beda, dan itu TIDAK masalah
```

Threshold dikalibrasi di VAL lalu dipakai di DS2, jadi VAL harus mirip **DS2**,
bukan mirip train.

**Aturan held-out: `sorted(records)[::4]`.** Aturan, bukan seed — tidak ada seed
yang bisa dipancing, dan siapa pun bisa memverifikasinya. ~25% disisihkan.

Konsekuensi yang sudah diperiksa: held-out incartdb cuma dapat ~13–20 beat F
(I05=9, I65=4 + sisa kecil), karena F terbesar (I18=56, I74=48) jatuh ke train.
**Itu disengaja** — yang kekurangan F adalah train, bukan test. F di TEST-C
dilaporkan sebagai hitungan **TP/FN mentah**, jangan sebagai recall berkoma.

### Bonus yang tidak diminta

TEST-B/TEST-C = uji generalisasi antar-database. Itu persis yang kerangka E3C
(P2) hargai, dan untuk sidang lebih kuat daripada F1 naik 0,05: *"model diuji di
pasien dari database dengan alat rekam berbeda"* > *"F1 saya 0,74"*.

---

## 5. Urutan fase

| Fase | Isi | DoD |
|---|---|---|
| **A** | infrastruktur multi-dataset | `make prep` jalan utk 3 db; sebaran cocok tabel §1 |
| **B** | **baseline ulang 3 seed, config terkunci, TANPA fitur baru** | pembanding sah. **Jangan dilewati** |
| **C** | T1 `class_weight=None` ulang | 3 seed |
| **D** | T2/T3 fitur: QRSw + RR rasio (gate K2) | 3 seed, lapor per-sumber |
| **E** | tahap 2 penamaan V/S — offline | nol retraining |
| **F** | re-export `.h` + `golden_ref` + `pio test -e native` | **sekali, di akhir** |

**Fase B punya sanity check bawaan yang gratis: recall S harus naik paling
banyak.** Kalau tidak bergerak setelah 634 → ~11.250 beat dan ~20 → ~102 pasien,
yang salah merge-nya (lead terbalik? resample rusak? label ketukar?), bukan
modelnya. Tes yang menunjuk tersangkanya sendiri.

Fase F sekali di akhir: tiap perubahan `N_RR_FEATURES` memaksa regen
`model_int8.h` **dan** `golden_ref.h` bersama. Regen 4× = 4× kesempatan salah
sinkron.

---

## 6. Ongkos — lebih murah dari dugaan

```
sekarang (mitdb DS1 x3 jitter)         = 121.857 window
nanti (mitdb x3 + svdb x1 + incart x1) ≈ 392.200 window   -> 3,2x
train.npz ~400 MB (muat di RAM, tidak perlu generator)
```

Bukan 10×: training sudah 3× dari jitter, dan database baru **tidak** dijitter.
3,2× × 3 seed masih masuk akal — aturan 3-seed tetap bisa ditegakkan.

### Kenapa database baru tidak dijitter

Bukan soal RAM. Kolam residu (`artifacts/metrics/jitter/residu_ds1.npy`) diukur
dari detektor di **mitdb 360 Hz**. Menerapkannya ke beat 128/257 Hz yang sudah
di-resample = menumpuk dua sumber error posisi, dan yang kedua belum pernah
diukur. Kalau nanti mau: **ukur dulu residunya di sana** (`ukur_jitter.py` sudah
ada) — jangan pakai ulang residu mitdb. Itu semangat aturan repo: jangan menyalin
konstanta empiris kalau kita bisa mengukur sendiri.

---

## 7. Yang berubah di kode (Fase A)

Semua **additive**. `FS`, `CHANNEL`, `RAW_DIR`, `DS1`, `DS2`, `VAL_RECORDS`,
`AAMI_MAP` — **tidak disentuh** (gate point CLAUDE.md). `make test` hijau: **74 passed, 1 skipped** (sisa skip menunggu incartdb).

### Lubang yang ketemu: `build_split()` mitdb-only

`make split` akan menghasilkan `train.npz` **tanpa svdb sama sekali, tanpa
bersuara** — persis jebakan yang membuat Fase B melaporkan "data baru tidak
menolong". Ditambal dengan `build_split_multi()` + `make split-multi`, dan
**nama file sengaja dibedakan**: `train.npz`/`test.npz` (mitdb-only) tidak
ditimpa karena keduanya masih dipakai mereproduksi ablasi terkunci.

Terverifikasi: `test_ds2.npz` dan `test.npz` sama-sama 47.513.784 byte dan
array-nya identik (`test_build_split_multi_tidak_bocor_dan_ds2_utuh`).

### Komposisi setelah svdb (incartdb belum)

```
train       80 record  292.594 beat  aritmia 10,45%
  setelah split_train_val -> train 261.547 / val 31.047 (aritmia 10,11%)
ds2         22 record   49.656 beat  aritmia 10,98%   <- VAL cermin DS2 ✓
svdb_test   20 record   44.704 beat  aritmia 15,88%

kelas di train:  S 634 -> 7.663 (12,1x)   V 3.071 -> 11.143 (3,6x)
                 F 394 -> 399 (svdb F memang tak berguna)   Q 6 -> 35
w_Aritmia        4,948 -> 4,686
```

| File | Perubahan |
|---|---|
| `config.py` | + `DATASETS`, `SPLIT_SETIAP_KE`, `raw_dir(db)` |
| `src/preprocessing.py` | + `resample_to_fs()` (resample_poly, 3 keputusan di §2) |
| `src/io_mitdb.py` | + `pilih_lead()`, `load_record(..., db=)`; `db="mitdb"` identik dgn sebelumnya |
| `src/dataset.py` | + `record_int_id()`, `bagi_train_test()`, `records_tersedia()` (menuntut .hea+.dat+.atr) |
| `scripts/prep_beats.py` | loop per-db, `--db`; jitter tetap mitdb-DS1 saja |
| `scripts/download_data.py` | multi-db, `--semua` |
| `src/dataset.py` (lagi) | + `build_split_multi()` — train gabungan + test per-db |
| `scripts/cek_lead.py` | **baru** — gate A2: polaritas & alignment, dua kolom |
| `scripts/build_split.py` | + `--gabungan` → `train_multi.npz`, `test_ds2.npz`, `test_<db>.npz` |
| `tests/test_multidataset.py` | **baru** — membekukan sebaran, aturan split, alignment, non-regresi mitdb |
| `Makefile` | + `data-semua`, `make data DB=svdb`; `help` kini lihat target ber-tanda-hubung |

### Blocker yang ditemukan sambil jalan

`stack_records()` memanggil `int(rec)` untuk kolom `records` (int32). Record
incartdb bernama `I01`..`I75` → `int("I18")` melempar `ValueError`. Dipetakan
lewat `record_int_id()`: mitdb 100–234, svdb 800–894, incartdb **1001–1075**.
Tiga rentang disjoint, dijaga `test_rentang_id_tidak_bertumpuk`.

---

## 8. Langkah berikut

1. ~~Gate A1 — isi `resample_to_fs()`~~ **selesai**
2. `make data-semua` (~1 GB) — sedang jalan
3. `make test` → dua `test_sebaran_kelas_sesuai_yang_diukur` harus hijau, bukan skip
4. `make prep` → `make split`
5. **Gate A2** — verifikasi polaritas lead svdb sebelum Fase B dianggap sah
6. Fase B: baseline 3 seed

### Sisa yang menggantung

`docs/2026-09-16-daya-plan.md:28` masih mengutip *"Aturan 1 `model/CLAUDE.md` —
USER yang menulis logika algoritma"*. Aturan itu sudah tidak ada. Dokumen itu
milik user; tidak diubah dari sini.
