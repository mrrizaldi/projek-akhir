# Walkthrough `src/dataset.py` — Fase 3

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
QRS-nya khas orang itu (bentuk elektroda, anatomi, posisi lead). Kalau 100.619
beat diacak lalu dibelah 80:20, maka untuk hampir tiap beat di test set, ada
beat **dari pasien yang sama, menit yang sama** di training set.

Model tidak perlu belajar "seperti apa PVC itu". Cukup belajar "seperti apa PVC
milik pasien 208". Akurasinya bisa 99% — dan **nol gunanya di klinik**, karena
pasien yang datang besok tidak ada di training set.

Ini bentuk *data leakage*: bukan bocor lewat label, tapi lewat **identitas**.

### Yang kita pakai (*inter-patient*, de Chazal 2004)

22 pasien untuk latih, 22 pasien lain untuk uji. Model harus menggeneralisasi
ke jantung yang belum pernah dilihatnya — sama seperti kondisi deploy sungguhan
di ESP32.

Harganya: **akurasi turun drastis**, dan itu wajar. Literatur intra-patient
melaporkan 99%; inter-patient yang jujur biasanya jauh di bawah itu. Kalau
nanti angkamu terlihat terlalu bagus, kecurigaan pertama adalah split-nya bocor.

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
suatu saat satu nomor terhapus atau terduplikasi saat mengedit `config.py`,
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
    origin.append(np.full(len(z["labels"]), int(rec), dtype=np.int32))
```

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
DS1     22 record    50965 beat   Normal 45814 (89,9%)   Aritmia 5151 (10,1%)
DS2     22 record    49654 beat   Normal 44204 (89,0%)   Aritmia 5450 (11,0%)
X_morph (50965, 250, 1) / (49654, 250, 1)      X_rr (50965, 3) / (49654, 3)
```

$50965 + 49654 = 100619$ — sama persis dengan total Fase 2. Tidak ada beat yang
hilang atau terhitung dua kali.

### Rasio kelasnya mirip, sebaran pasiennya tidak

| | DS1 (latih) | DS2 (uji) |
|---|---|---|
| aritmia terbanyak | 208 (46,3%), 106 (25,7%), 119 (22,3%) | **232 (77,7%)**, 200 (33,0%), 233 (27,6%) |
| aritmia ~nol | 230, 115, 122 (0,0%) | **212 (0,0%)**, 111 (0,0%), 117 (0,1%) |
| beat per record | 1.616 (rec 124) – 3.360 (rec 215) | 1.516 (rec 123) – 3.248 (rec 213) |

Rasio agregat nyaris sama (10,1% vs 11,0%) — itu kebetulan yang menguntungkan,
bukan hasil penyeimbangan. **Jangan tergoda "memperbaiki" split supaya lebih
seimbang**: daftarnya milik de Chazal 2004 dan gunanya justru supaya angkamu
sebanding dengan literatur.

Yang tidak boleh diabaikan: **rec 212 menyumbang 2.745 beat uji tanpa satu pun
aritmia**, sementara **rec 232 didominasi aritmia (77,7%)**. Rata-rata global
akan meratakan dua kutub ini. Itulah kenapa kolom `records` disimpan.

---

## 5. Yang sengaja TIDAK dilakukan

**Tidak ada `shuffle`.** Urutan di dalam file mengikuti urutan record. Pengacakan
adalah urusan `model.fit(shuffle=True)` saat training — dilakukan di memori, per
epoch, dan tidak pernah menyeberangi batas train/test.

**Tidak ada validation split di sini.** DS1 nanti dibelah lagi jadi
train/validation di Fase 5 — dan pembelahannya juga **per pasien**, dengan
alasan yang persis sama. DS2 tidak ikut campur.

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
3. Model dilatih dengan `X_morph` ber-`shape (N, 250)` bukan `(N, 250, 1)`.
   Error-nya muncul di mana, dan kenapa lebih baik bentuknya dibereskan di
   Fase 3 daripada di skrip training?
4. Seseorang mengganti `build_split` jadi mengacak 100.619 beat lalu membelah
   80:20. Akurasi Fase 6 naik dari 0,80 jadi 0,99. Apa nama kesalahannya, dan
   cek satu baris mana di `src/dataset.py` yang seharusnya mencegahnya?

## 7. Skrip pendukung

| Perintah | Melihat apa |
|---|---|
| `make split` | Rakit train/test + ringkasan distribusi per split |
| `make test` | 24 test — 4 di antaranya mengunci kontrak split Fase 3 |

---

**[← Fase 2b — prep_beats](prep-beats-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 4 — model →](model-walkthrough.md)**
