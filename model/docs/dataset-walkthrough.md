# Walkthrough `src/dataset.py` — Fase 3

> **Ruang lingkup:** perakitan split inter-patient DS1/DS2 (de Chazal 2004) dari `.npz` per record, beserta penjaga kebocoran lintas pasien.
> **Kode terkait:** `src/dataset.py`, `scripts/build_split.py`, `config.py` (`DS1`, `DS2`, `PACED_EXCLUDED`, `VAL_RECORDS`, `DB_LATIH`), `tests/test_dataset.py`
> **Prasyarat:** [`prep-beats-walkthrough.md`](prep-beats-walkthrough.md)

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 11. Lanjutan dari
[`features-rr-walkthrough.md`](features-rr-walkthrough.md) (Fase 2).

Angka di sini hasil `make split` atas 44 record. Reproduksi:

```
cd model
make prep && make split
```

---

## 0. Peta besar — di sini data berhenti jadi "per pasien"

```
per_record/100.npz  101.npz  ...  (44 file, satu per pasien)
        │
        │  build_split()  ← memilih file berdasar DS1/DS2, BUKAN mengacak beat
        ▼
train.npz (DS1, 22 pasien)        test.npz (DS2, 22 pasien)
        │                                  │
        ▼                                  ▼
   Fase 4-5 latih                    Fase 6 evaluasi (baru boleh disentuh)
```

Fase 3 **tidak menghitung apa pun**. Tidak ada filter, tidak ada fitur baru,
tidak ada normalisasi. Dia cuma menumpuk array dan menjaga satu janji: **tidak
ada satu pun detak dari pasien yang sama muncul di kedua sisi.**

---

## 1. Kenapa split per pasien, bukan acak per beat

Ini keputusan tunggal yang paling menentukan apakah angka akhirmu bermakna
atau bohong.

### Yang terjadi kalau beat diacak (*intra-patient*)

MIT-BIH itu 30 menit per pasien. Detak seorang pasien saling mirip — morfologi
QRS-nya khas orang itu (bentuk elektroda, anatomi, posisi lead). Kalau 100.624
beat diacak lalu dibelah 80:20, maka untuk hampir tiap beat di test set, ada
beat **dari pasien yang sama, menit yang sama** di training set.

Model tidak perlu belajar "seperti apa PVC itu". Cukup belajar "seperti apa PVC
milik pasien 208". Akurasinya bisa 99% — dan **nol gunanya di klinik**, karena
pasien yang datang besok tidak ada di training set.

Ini bentuk *data leakage*: bukan bocor lewat label, tapi lewat **identitas**.

### Yang kita pakai (*inter-patient*, de Chazal 2004)

22 pasien untuk latih, 22 pasien lain untuk uji. Model harus menggeneralisasi
ke jantung yang belum pernah dilihatnya — sama seperti kondisi deploy di ESP32.

Harganya: **akurasi turun drastis**, dan itu wajar. Literatur intra-patient
melaporkan 99%; inter-patient yang jujur biasanya jauh di bawah itu. Kalau
angkamu terlihat terlalu bagus, kecurigaan pertama adalah split-nya bocor.

```python
if set(np.unique(train["records"])) & set(np.unique(test["records"])):
    raise ValueError("record bocor lintas split")
```

Cek itu jalan tiap `make split`. Murah, dan menutup satu-satunya cara kebocoran
ini bisa masuk diam-diam.

---

## 2. `assert_split_valid()` — tiga syarat sebelum apa pun dibaca

```python
ds1, ds2, paced = set(DS1), set(DS2), set(PACED_EXCLUDED)
if ds1 & ds2:                    raise ...   # 1. tidak beririsan
if (ds1 | ds2) & paced:          raise ...   # 2. paced tidak ikut
if len(ds1)+len(ds2)+len(paced) != 48: raise ...   # 3. 22+22+4 = 48
```

Dijalankan **sebelum** file apa pun dibuka — kalau daftarnya salah, gagal dalam
milidetik, bukan setelah membaca 44 file.

Syarat 3 (`= 48`) itu penjaga salah-ketik. MIT-BIH punya persis 48 record; kalau
satu nomor terhapus atau terduplikasi saat mengedit `config.py`,
jumlahnya meleset dan test menangkapnya.

### Kenapa 4 record dibuang, dua alasan berbeda

| Record | Alasan | Jenis |
|---|---|---|
| 102, 104 | tidak punya kanal MLII → `load_record` melempar `ValueError` | **teknis** |
| 107, 217 | pasien ber-*pacemaker* | **metodologis** |

107 itu 97% simbol `/` (paced). Kalau ikut, satu record menyumbang 2.078 beat
"Aritmia" — model akan belajar mengenali *pacemaker*, bukan aritmia. Keempatnya
tinggal di satu daftar `PACED_EXCLUDED` di `config.py`, dipakai Fase 2 **dan**
Fase 3. Satu sumber kebenaran, jangan digandakan.

---

## 3. `stack_records()` — menumpuk, plus satu kolom yang gampang dilupakan

```python
with np.load(path) as z:
    morph.append(z["windows"])
    rr.append(z["rr"])
    y.append(z["labels"])
    origin.append(np.full(len(z["labels"]), record_int_id(rec, db), dtype=np.int32))
```

`record_int_id` memetakan nama record ke `int32`: mitdb dan svdb sudah numerik
(offset 0), incartdb `"I01".."I75"` menjadi 1001..1075. Tiga rentang itu tidak
bertumpuk, jadi `records` tetap unik lintas database.

Tiga array pertama jelas. Yang keempat — `records` — adalah **jejak asal tiap
beat**, dan dia satu-satunya alasan Fase 6 bisa menjawab pertanyaan yang benar.

Metrik global ("recall 0,78") menyembunyikan hal penting: apakah 0,78 itu rata,
atau 0,95 di 20 pasien dan 0,10 di 2 pasien? Yang kedua jauh lebih berbahaya di
alat medis. Dengan `records`, metrik per-pasien tinggal `y[records == r]`.

Tanpa kolom itu, informasinya **hilang permanen** begitu array disatukan — dan
tidak bisa direkonstruksi, karena urutan beat sudah menyatu.

### `FileNotFoundError`, bukan `continue`

```python
if not os.path.exists(path):
    raise FileNotFoundError(f"{path} — jalankan `make prep` dulu")
```

Melewati record yang hilang akan menghasilkan split yang **valid secara bentuk
tapi lebih kecil diam-diam** — dan kamu baru sadar saat membandingkan jumlah
beat dengan Bab 4 yang sudah dicetak.

### `reshape(-1, WIN_LEN, 1)`

```python
"X_morph": np.concatenate(morph).reshape(-1, WIN_LEN, 1)
```

`Conv1D` di Keras menuntut bentuk `(batch, langkah_waktu, kanal)`. Kita punya
satu kanal (MLII), jadi dimensi terakhir = 1. Ditambahkan di sini, sekali,
bukan di dalam loop training — supaya `train.npz` sudah berbentuk persis seperti
yang dimakan model.

---

## 4. Angka hasil `make split`

```
DS1     22 record   152904 beat   Normal 137451 (89,9%)   Aritmia 15453 (10,1%)
DS2     22 record    49656 beat   Normal  44206 (89,0%)   Aritmia  5450 (11,0%)
X_morph (152904, 256, 1) / (49656, 256, 1)      X_rr (152904, 3) / (49656, 3)
```

DS1 berisi tiga salinan tiap beat (satu bersih + dua ber-jitter, lihat
[`prep-beats-walkthrough.md`](prep-beats-walkthrough.md) §4): $152904 = 3 \times
50968$. Tanpa augmentasi, $50968 + 49656 = 100624$ — sama persis dengan total
Fase 2 data bersih. Tidak ada beat yang hilang atau terhitung dua kali.

### Rasio kelasnya mirip, sebaran pasiennya tidak

| | DS1 (latih) | DS2 (uji) |
|---|---|---|
| aritmia terbanyak | 208 (46,3%), 106 (25,7%), 119 (22,3%) | **232 (77,7%)**, 200 (33,0%), 233 (27,6%) |
| aritmia ~nol | 230, 115, 122 (0,0%) | **212 (0,0%)**, 111 (0,0%), 103 (0,1%) |
| beat per record (bersih) | 1.616 (rec 124) – 3.360 (rec 215) | 1.516 (rec 123) – 3.248 (rec 213) |

Rasio agregat nyaris sama (10,1% vs 11,0%) — itu kebetulan yang menguntungkan,
bukan hasil penyeimbangan. **Jangan tergoda "memperbaiki" split supaya lebih
seimbang**: daftarnya milik de Chazal 2004 dan gunanya justru supaya angkamu
sebanding dengan literatur.

Yang tidak boleh diabaikan: **rec 212 menyumbang 2.745 beat uji tanpa satu pun
aritmia**, sementara **rec 232 didominasi aritmia (77,7%)**. Rata-rata global
akan meratakan dua kutub ini. Itulah kenapa kolom `records` disimpan.

### Split lintas database (`make split-multi`)

`build_split_multi` merakit split untuk ablasi lintas database dan menulis
`train_multi.npz`, `test_ds2.npz`, serta `test_<db>.npz`:

- **train:** DS1 mitdb + porsi latih database yang ada di `DB_LATIH`.
- **ds2:** DS2 mitdb apa adanya — angka utama yang sebanding literatur.
- **`<db>_test`:** held-out tiap database tambahan, dipilih dengan aturan
  `sorted(records)[::4]` (`bagi_train_test`), bukan seed.

Database yang belum di-prep dilewati, tetapi database yang baru sebagian ter-prep
ditolak `ValueError`, karena aturan `[::4]` atas daftar yang tidak lengkap
memberi split yang berbeda tanpa tanda. Cek kebocoran yang sama berlaku antara
`train` dan setiap set uji. Model produksi tetap dilatih dari `train.npz`
(mitdb saja).

### Konstanta multi-database di `config.py`

Tujuan Fase A (permintaan pembimbing): memperluas data latih. Sebaran berikut
terukur 19 Sep 2026 dari anotasi asli PhysioNet yang dipetakan lewat `AAMI_MAP`,
bukan disalin dari paper (angka yang sama dibekukan di
`tests/test_multidataset.py`):

```
svdb      78 rec, 128 Hz | S 12.198/73rec  V  9.943/67rec  F  23/6rec   Q 79/20rec
incartdb  75 rec, 257 Hz | S  1.960/36rec  V 20.013/70rec  F 219/22rec  Q  6/5rec
```

**Kenapa dua database ini.** Keduanya punya anotasi beat-level (`.atr`, satu
simbol per R-peak) dengan alfabet WFDB yang sama, jadi `AAMI_MAP` menanganinya
tanpa mapping baru. PTB-XL, CPSC, dan Chapman ditolak bukan karena frekuensi
cuplik, tetapi karena diagnosisnya per-rekaman: label per-beat tidak bisa
diturunkan dari sana. Syarat yang sama berlaku untuk database berikutnya yang
ditambahkan ke `download_data.py`.

**Peran yang diharapkan.** svdb untuk recall S (0,422 ± 0,156; dari 634 beat S
di ~20 pasien ke ~11.250 di ~102). incartdb untuk konsentrasi F: 372 dari 394
beat F mitdb ada di record 208 saja (satu pasien efektif), sedangkan incartdb
menyebar 219 beat di 22 record; yang diperbaiki cakupan pasien, bukan jumlah
beat. Q tidak tertolong: 100 beat di tiga database (mitdb 8 + 7, svdb 79,
incartdb 6), sehingga Q tetap bukan kelas yang bisa dilaporkan.

**DS2 mitdb tidak berubah satu byte.** Dia satu-satunya set yang sebanding
literatur, dan aturan "DS2 tidak memilih apa pun" hanya bisa ditegakkan kalau
komposisinya bukan variabel. Data baru masuk train; sisanya menjadi test
terpisah untuk generalisasi antar-database. `load_record(db="mitdb")` dijaga
44/44 record byte-identik dengan sebelum Fase A.

**`leads`.** Dipilih lead pertama yang tersedia. mitdb MLII = acuan alat
(AD8232 lead II). incartdb `II` paling dekat dengannya. svdb (Holter) tidak
menamai lead, jadi `ECG1` dipakai; polaritasnya diverifikasi `scripts/cek_lead.py`
(gate A2: 8/8 record svdb positif di R).

**`selaraskan` dan `ALIGN_WIN = 16`.** Konvensi anotasi antar-database berbeda.
Terukur atas beat normal, posisi puncak relatif anotasi di sinyal ter-bandpass:

```
mitdb  median  +3   p5..p95  +1..+5     anotasi DI puncak; +3/+4 = group delay
svdb   median +10   p5..p95  -2..+15    ~6 sampel lebih awal, sebaran 3x lebih lebar
```

Bias +6 sampel itu di atas ambang bahaya repo ini (meleset 4 sampel menjatuhkan
precision 0,48 → 0,12) dan sistematis, bukan jitter berpusat nol: tanpa koreksi
tiap beat svdb tergeser searah dan model membacanya sebagai morfologi lain, alias
belajar identitas dataset. Maka svdb dan incartdb diselaraskan
(`selaraskan_r`: geser anotasi ke puncak, lalu kembalikan group delay; sepadan
dengan penyelarasan Pan-Tompkins di firmware, jendela lebih sempit). mitdb wajib
`False`: dia acuan `golden_ref.h` dan semua ablasi terkunci, dan median +3 vs +4
berarti menyelaraskannya menggeser R ~1 sampel dan membatalkan semuanya.
Setengah-lebar jendela cari-puncak 16 sampel (±44 ms) menutup p1..p99 svdb
(−9..+15) tanpa menjangkau gelombang T (~200-300 ms = 72-108 sampel); 25
(`PT_REFINE_WIN`, ±70 ms) dibuat untuk sebaran detektor (std 13 sampel) dan di
sini terlalu lebar. `cek_lead.py` membaca polaritas dari kolom "mentah" dan
alignment dari kolom "selaras"; kolom "selaras" tidak boleh memvonis polaritas
karena `selaraskan_r` memakai argmax bertanda yang memaksa nilai di R positif.

**Laju cuplik diseragamkan ke 360 Hz.** `WIN_PRE` terdefinisi dalam sampel,
bukan waktu: 128 sampel @ 360 Hz = 355 ms (yang diablasi dan dikunci), sedangkan
128 sampel @ 128 Hz = 1.000 ms, fisiologi lain sama sekali. Yang membayar di
ablasi window adalah konteks gelombang P dan interval PR ~150-200 ms sebelum R,
jadi durasinya yang harus dijaga. Dengan target 360 Hz, `WIN_PRE/WIN_POST`,
koefisien bandpass, `ECG_FS` firmware, dan `golden_ref.h` tidak berubah.
`resample_to_fs` memakai `resample_poly` (polyphase, linear-phase), dan posisi R
cukup dibulatkan selama arahnya upsample (indeks makin menyebar, tak mungkin
bertabrakan); bila suatu hari `fs_target < fs_asal`, dua R bisa jatuh ke indeks
yang sama (RR = 0), dan itu harus berisik. `fs` setiap record dicek terhadap
janji `DATASETS[db]["fs"]` sebelum resample, supaya tabel config yang salah tidak
tertutupi resample.

**`id_offset`.** Lihat `record_int_id` di §3. Tanpa peta itu `int("I18")`
melempar `ValueError` di `stack_records`, bukan gagal dengan pesan berguna.

**`SPLIT_SETIAP_KE = 4`.** Held-out tiap database tambahan = setiap record ke-4
dalam urutan tersortir (~25%). Aturan, bukan seed: tidak ada yang bisa
dipancing, dan siapa pun dapat memverifikasinya dengan `sorted(records)[::4]`.
Konsekuensi yang sudah diperiksa: held-out incartdb hanya mendapat ~13-20 beat F
(I05 = 9, I65 = 4, plus sisa kecil) karena record F terbesar (I18 = 56,
I74 = 48) jatuh ke train. Itu disengaja; F di test dilaporkan sebagai hitungan
TP/FN mentah, bukan recall berkoma.

**`n_record`.** Jumlah record lengkap yang diharapkan (mitdb 48 − 4
`PACED_EXCLUDED` = 44). Aturan held-out dihitung dari daftar yang ADA, jadi
database yang baru separuh terunduh menghasilkan held-out yang berbeda tanpa
tanda. Terukur 19 Sep pada 65/75 record incartdb: I68 masuk held-out padahal
seharusnya tidak, dan I65/I69/I73 hilang (I65 memegang 4 beat F). Karena itu
`build_split_multi` menolak database yang jumlah recordnya tidak pas; split yang
salah lebih buruk daripada error. `available_records` juga menuntut `.hea`,
`.dat`, dan `.atr` sekaligus, karena unduhan yang masih berjalan meninggalkan
`.hea` tanpa `.atr`.

**`DB_LATIH = ("mitdb", "svdb")`, incartdb hanya test.** Held-out selalu menjadi
test, tetapi porsi train sebuah database hanya ikut bila dia ada di `DB_LATIH`.
Fase B mengukur incartdb merugikan di latih walau menyumbang 256.454 beat latih
(4 varian × 3 seed):

```
                mitdb      +svdb    +incartdb   +keduanya
AUC            0,9373     0,9314     0,8881      0,9092
recall S       0,4221     0,4980     0,3312      0,4050
```

Rentang recall S +svdb [0,423; 0,573] dan +incartdb [0,307; 0,355] terpisah:
efeknya berlawanan, dan di "+keduanya" hampir saling meniadakan (−0,017).
Penyebabnya bukan lead (II ≈ MLII, gate A2) atau resolusi (257 > 128 Hz),
melainkan komposisi: 15.592 beat V dari populasi lain menumpulkan pemisahan
N-vs-S. incartdb tetap dipakai sebagai test antar-database (41.108 beat,
19 pasien). Model produksi tetap mitdb saja (`model/CLAUDE.md`, baris Database
LATIH); `DB_LATIH` hanya dipakai jalur ablasi.

**Angka beku di `tests/test_multidataset.py`.** Semuanya diukur 19 Sep 2026 dan
dibekukan supaya perubahan senyap ketahuan. Bila salah satu gagal, urutan
tersangkanya: (1) daftar record berubah, (2) `AAMI_MAP`/`BEAT_SYMBOLS` diedit,
(3) `DATASETS` salah isi, bukan "angkanya kebetulan beda". VAL dijaga mirip DS2
(threshold dikalibrasi di VAL lalu dipakai di DS2), sedangkan train boleh
bergeser karena svdb kaya S.

---

## 5. Yang sengaja TIDAK dilakukan

**Tidak ada `shuffle`.** Urutan di dalam file mengikuti urutan record. Pengacakan
adalah urusan `model.fit(shuffle=True)` saat training — dilakukan di memori, per
epoch, dan tidak pernah menyeberangi batas train/test.

**Tidak ada validation split di `train.npz`.** DS1 dibelah jadi train/validation
di Fase 5 lewat `split_train_val`, yang juga **per pasien**: record di
`VAL_RECORDS` (101, 114, 201, 220, 223) menjadi validation, dan fungsi itu
menolak record val di luar DS1. DS2 tidak ikut campur.

**Tidak ada normalisasi tambahan.** `windows` sudah z-score per window sejak
Fase 1; `rr` sengaja dibiarkan mentah (JEBAKAN #2 PRD). Menghitung $\mu,\sigma$
di sini berarti menghitungnya dari DS1+DS2 sekaligus = kebocoran.

**DS2 tidak dibaca untuk apa pun selain disimpan.** Aturan #4 `CLAUDE.md`:
haram disentuh sampai Fase 6. Distribusi labelnya dicetak karena itu DoD Fase 3
— bukan untuk jadi dasar keputusan apa pun.

---

## 6. Cek pemahaman

1. Kalau rec 208 (46,3% aritmia, DS1) dipindah ke DS2, metrik mana yang berubah
   paling banyak — dan kenapa itu tetap bukan alasan sah untuk memindahkannya?
2. `records` tidak disimpan. Di Fase 6 kamu ingin tahu recall per pasien. Kenapa
   tidak bisa direkonstruksi dari `train.npz` saja?
3. Model dilatih dengan `X_morph` ber-`shape (N, 256)` bukan `(N, 256, 1)`.
   Error-nya muncul di mana, dan kenapa lebih baik bentuknya dibereskan di
   Fase 3 daripada di skrip training?
4. Seseorang mengganti `build_split` jadi mengacak 100.624 beat lalu membelah
   80:20. Akurasi Fase 6 naik dari 0,80 jadi 0,99. Apa nama kesalahannya, dan
   cek satu baris mana di `src/dataset.py` yang seharusnya mencegahnya?

## 7. Skrip pendukung

| Perintah | Melihat apa |
|---|---|
| `make split` | Rakit train/test + ringkasan distribusi per split |
| `make split-multi` | Rakit split lintas database (ablasi) |
| `make test` | Seluruh test; `tests/test_dataset.py` mengunci kontrak split Fase 3 |

---

**[← Fase 2b — prep_beats](prep-beats-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 4 — model →](model-walkthrough.md)**
