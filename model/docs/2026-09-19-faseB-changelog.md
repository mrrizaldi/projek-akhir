# Fase B — baseline multi-database: hasil & diagnosis

**19 September 2026. Branch `feat/multidataset`.** Lanjutan
[`2026-09-19-multidataset-plan.md`](2026-09-19-multidataset-plan.md).

Aturan §7 berlaku: 3 seed per varian, signifikan = rentang `[rerata ±
setengah-rentang]` **tidak bertumpuk**.

---

## 1. Hasil, 4 varian × 3 seed

Semua: config terkunci (window 128/128, jitter empiris ×2), VAL murni mitdb,
DS2 tak tersentuh. Yang berbeda hanya database LATIH.

| metrik | mitdb saja | +svdb | +incartdb | +keduanya |
|---|---|---|---|---|
| n_train | 121.857 | 261.547 | 256.454 | 396.144 |
| **AUC** | **0,9373 ±0,009** | 0,9314 ±0,017 | **0,8881 ±0,034** | 0,9092 ±0,011 |
| F1 | **0,6911 ±0,029** | 0,6242 ±0,052 | 0,6239 ±0,021 | 0,6419 ±0,027 |
| **precision** | **0,6728 ±0,024** | 0,5367 ±0,092 | 0,5634 ±0,036 | 0,5785 ±0,052 |
| recall | 0,7112 ±0,046 | 0,7602 ±0,036 | 0,7003 ±0,011 | 0,7239 ±0,012 |
| **recall S** | 0,4221 ±0,156 | **0,4980 ±0,075** | **0,3312 ±0,024** | 0,4050 ±0,025 |
| recall V | 0,9437 ±0,007 | 0,9775 ±0,015 | 0,9731 ±0,005 | 0,9737 ±0,021 |
| recall F | 0,1521 ±0,067 | 0,1959 ±0,157 | 0,1838 ±0,031 | 0,1581 ±0,107 |
| threshold | 0,63 | 0,40 | 0,48 | 0,33 |

### Vonis vs baseline (rentang tidak bertumpuk)

```
AUC        +svdb —      +incartdb TURUN   +keduanya TURUN
F1         +svdb —      +incartdb TURUN   +keduanya —
precision  +svdb TURUN  +incartdb TURUN   +keduanya TURUN
recall     +svdb —      +incartdb —       +keduanya —
```

---

## 2. Temuan utama: efek keduanya BERLAWANAN dan saling meniadakan

`recall S`, dibandingkan **antar-varian baru** (bukan lewat baseline, karena
variansi baseline ±0,156 membuat semuanya bertumpuk dengannya):

```
+svdb      [0,423 , 0,573]
+incartdb  [0,307 , 0,355]     TERPISAH
```

| varian | recall S | delta dari baseline |
|---|---|---|
| mitdb saja | 0,422 ±0,156 | — |
| **+svdb** | **0,498 ±0,075** | **+0,076**, variansi separuh |
| **+incartdb** | **0,331 ±0,024** | **−0,091** |
| +keduanya | 0,405 ±0,025 | −0,017 ← **hampir persis saling meniadakan** |

**svdb mengerjakan tepat apa yang dia dipilih untuk kerjakan.** Kenaikan S itu
ADA; di `fb_multi` dia tertutup karena incartdb menariknya turun sebanyak yang
svdb menaikkannya. Tanpa ablasi pengisolasi ini, kesimpulannya akan jadi
"dataset tambahan tidak menolong S" — dan itu salah.

### incartdb: merugikan

AUC terendah (0,8881), F1 terendah, dan **recall S turun** meski menyumbang
256.454 beat latih. Tersangka mekanismenya bukan lead (II ≈ MLII, sudah
diverifikasi gate A2) dan bukan resolusi (257 Hz > svdb 128 Hz), tapi
**komposisi**: incartdb menyumbang 15.592 beat V ke latih (V naik 10,7×) dari
populasi berbeda (rekaman klinis 12-lead St Petersburg). Model bergeser ke arah
morfologi V dan kehilangan ketajaman N-vs-S.

---

## 3. Yang memburuk di SEMUA varian: precision

```
mitdb saja   FP 1.885   FPR 4,26%   ~3.279 alarm palsu/hari
+svdb        FP 3.577   FPR 8,09%   ~6.222
+incartdb    FP 2.958   FPR 6,69%   ~5.146
+keduanya    FP 2.875   FPR 6,50%   ~5.001
```

Bukan sifat salah satu database — **harga menambah data luar-domain sama sekali.**
recall naik (S dan V), precision bayar. Dan §2.2 dokumen fitur-design menyebut
angka alarm palsu sebagai "angka yang membuat alat tidak terpakai".

`+svdb` justru beban alarm TERBERAT (6.222/hari) walau recall S-nya terbaik:
recall 0,760 dengan precision 0,537.

Threshold VAL ambruk di semua varian (0,63 → 0,33–0,48), konsisten dengan
sebaran probabilitas yang bergeser karena latih tak lagi didominasi mitdb.

---

## 4. Konsekuensi: precision jadi leher botol, dan obatnya sudah tertulis

Sebelum Fase B, leher botolnya recall S. Sekarang **precision**, di keempat
varian. Dan K1 di [`2026-09-19-fitur-design.md`](2026-09-19-fitur-design.md)
adalah eksperimen yang dirancang persis untuk itu:

> P1 Tabel 4, Model 2 vs 6, berbeda HANYA di class weight:
> class weight SET → SVEB Se 88,51 / +P 51,49
> class weight NOT SET → SVEB Se 81,60 / **+P 82,68**
> Recall turun 7 poin, **precision naik 31 poin.**

Argumen dokumen itu sekarang lebih kuat, bukan lebih lemah: kita **sudah**
menangani imbalance lewat kalibrasi threshold di VAL, dan `class_weight`
menumpuk mekanisme kedua untuk tujuan sama. Dengan train 3,3× lebih besar dan
threshold yang ambruk ke 0,33, dua knob itu jelas saling menarik.

`make_class_weights` menghitung dari `y` yang masuk, jadi nilainya sudah
bergeser sendiri: **4,948 → 4,455**.

---

## 5. Usul

| # | Usul | Dasar |
|---|---|---|
| 1 | **incartdb keluar dari LATIH**, tetap jadi TEST-C | recall S terpisah-dan-lebih-buruk dari +svdb; AUC & F1 terendah. Sebagai test antar-database dia tetap berharga (41.108 beat, 19 pasien) |
| 2 | **svdb tetap di LATIH** | +0,076 recall S, variansi separuh, AUC tak terganggu |
| 3 | **T1 `class_weight=None`, 3 seed, di mitdb+svdb** | precision leher botol di semua varian; K1 memprediksi +31 poin precision |

Yang TIDAK diusulkan: membuang svdb karena beban alarmnya. Beban itu gejala
precision, dan usul 3 menyerang penyebabnya — bukan membuang data yang terbukti
memperbaiki S.

---

## 6. Pelajaran metodologis

**Fase B yang berdiri sendiri membayar hari ini.** Kalau fitur baru (QRSw, RR
rasio) digabung sekaligus dengan dataset baru, angkanya akan bergerak sedikit dan
kesimpulannya akan menyalahkan fitur — padahal dua efek berlawanan (svdb naik,
incartdb turun) saling menutupi di rata-rata.

Dan **ablasi pengisolasi wajib, bukan opsional.** `fb_multi` sendirian bilang
"dataset tambahan gagal". Memecahnya per-database membalik kesimpulannya jadi
"satu berhasil, satu merugikan".

Catatan kejujuran: dua kali dalam sesi ini kesimpulan sempat diambil dari n=1
seed (`fb_svdb` seed 42 AUC 0,9379 dibaca sebagai "svdb aman" — dengan 3 seed
precision-nya justru paling liar, ±0,092). Ambang deteksi yang dihitung sendiri
tetap harus dipatuhi sendiri.

---

## 7. T1 (`class_weight=None`) — K1 TERBANTAH

`fb_svdb_nocw`, 3 seed, latih mitdb+svdb, semua yang lain identik.

| metrik | cw balanced | cw OFF | delta | vonis |
|---|---|---|---|---|
| AUC | 0,9314 ±0,017 | 0,9309 ±0,005 | −0,0005 | tumpuk |
| F1 | 0,6242 ±0,052 | 0,6223 ±0,020 | −0,0019 | tumpuk |
| precision | 0,5367 ±0,092 | 0,5398 ±0,033 | **+0,0032** | tumpuk |
| recall | 0,7602 ±0,036 | 0,7360 ±0,006 | −0,0242 | tumpuk |
| recall S | 0,4980 ±0,075 | 0,4223 ±0,029 | −0,0757 | tumpuk |
| threshold | 0,40 | **0,15** | −0,25 | — |

```
prediksi K1 (P1 Tabel 4) : precision +31 poin, recall -7 poin
terukur                  : precision  +0,3 poin, recall -2,4 poin
```

**Mekanismenya ada di baris threshold.** Tanpa `class_weight` probabilitas model
bergeser turun, dan kalibrasi VAL cuma memilih threshold lebih rendah —
mendarat di titik operasi yang sama. Kalibrasi **menyerap** seluruh efeknya.

Ini mengonfirmasi **premis** K1 (*"kita sudah menangani imbalance lewat
kalibrasi; class_weight menumpuk mekanisme kedua"*) sekaligus membantah
**prediksinya**: karena mekanisme kedua di HILIR dan ADAPTIF, dia menyerap apa
pun yang dilakukan yang pertama. Keduanya redundan, bukan saling menarik — dan
redundan berarti mencabut satu = netral. P1 tidak punya langkah kalibrasi (argmax
3 kelas), jadi di sana efeknya besar.

**Pelajaran untuk aturan repo.** *"Adopsi hanya kalau papernya mengablasi"* tidak
cukup — P1 MEMANG mengablasi class weight, variabel-tunggal, Tabel 4, dan
klaimnya sah. Yang tidak transfer adalah **konteks pipeline**. Perlu klausa
tambahan: ablasi paper transfer hanya kalau tidak ada **langkah adaptif di antara
knob dan metrik** yang kita punya tapi mereka tidak.

**Vonis G1: `class_weight` balanced TETAP.** Netral pada metrik, 2,5–6,5× lebih
reproducible, tapi recall S turun 0,076 — dan S kelas targetnya. Nilai terkunci
menang, sekarang atas dasar ablasi sendiri, bukan preseden paper.

---

## 8. Titik operasi: svdb sebenarnya MENANG, kalibrasinya yang meleset

### Pada precision yang dicocokkan (seed 42, kedua model)

| target precision | w128b recall / recall S | **fb_svdb** recall / recall S |
|---|---|---|
| 0,60 | 0,711 / 0,385 | **0,745 / 0,452** |
| 0,67 | 0,686 / 0,345 | **0,715 / 0,384** |
| 0,75 | 0,641 / 0,288 | **0,680 / 0,334** |
| 0,85 | 0,578 / 0,230 | **0,621 / 0,294** |

Di setiap precision ≥ 0,60, `+svdb` memberi recall DAN recall S lebih tinggi.
Kesimpulan §3 (*"svdb kerugian bersih"*) adalah **artefak titik operasi**, bukan
sifat datanya.

### Berapa yang hilang ke kalibrasi (seed 42)

| model | thr VAL → F1 DS2 | thr optimal DS2 → F1 | rugi |
|---|---|---|---|
| w128b | 0,75 → 0,6691 | 0,87 → 0,7031 | 0,034 |
| fb_svdb | 0,50 → 0,6780 | 0,95 → 0,7259 | 0,048 |
| fb_multi | 0,35 → 0,6506 | 0,89 → 0,7191 | 0,068 |

DS2 dipakai **mendiagnosis**, bukan memilih. F1 potensial `fb_svdb` 0,7259 —
tertinggi dari semua varian, termasuk mitdb-saja.

### Set kalibrasi yang lebih besar menutup sebagian besar celah

Ketiganya SAH (bukan train, bukan DS2). `scripts/cek_kalibrasi.py`.

| model | VAL (5 pasien) | +svdb (25) | **+svdb+incart (44)** | sisa celah |
|---|---|---|---|---|
| w128b | 0,6691 | 0,6541 | **0,6893** | 0,034 → 0,014 |
| fb_svdb | 0,6780 | 0,7005 | **0,7059** | 0,048 → 0,020 |
| fb_multi | 0,6506 | 0,5639 | **0,6997** | 0,068 → 0,019 |

Tidak monoton pada jumlah pasien: set 25-pasien lebih buruk untuk dua model.
Jadi yang menolong bukan "lebih banyak" saja — kemungkinan keragamannya.

### Dua hipotesis yang DITOLAK sepanjang analisis ini

1. **"Jitter di VAL yang menggeser threshold."** Diuji dengan VAL bersih
   (10.349 baris, tanpa salinan): threshold jadi SAMA atau LEBIH RENDAH, F1 sama
   atau lebih buruk. Terbantah.
2. **"Kalibrasi merugikan 0,10 F1."** Itu membandingkan rerata 3-seed F1@VAL
   dengan optimum satu-seed. Apel vs jeruk. Per-seed yang benar: 0,034–0,068.

### Batas yang harus disebut

Seluruh §8 ini **satu seed**, karena `ablasi.py` hanya menyimpan model seed utama.
Dan masalah yang sebenarnya adalah **variansi threshold antar-seed** (w128b
0,50–0,75; fb_svdb 0,30–0,50) di atas plateau F1 yang datar. Membuktikan bahwa
set kalibrasi lebih besar **mengurangi variansi** butuh tiga seed, bukan satu.

### Ongkos yang belum dibayar

Set kalibrasi adalah bagian dari PELATIHAN. Kalau svdb/incartdb held-out dipakai
kalibrasi, mereka berhenti jadi test antar-database — dan itu kontribusi E3C yang
dipilih sejak plan §4. Perlu keputusan: pecah tiap held-out (separuh kalibrasi,
separuh test), atau korbankan salah satu peran.

---

## 9. Fase D — tabel 2x2 dataset × fitur. **VONIS: kunci nol.**

Sel "mitdb + fitur baru" (`fd_mitdb_only`) adalah yang membuka seluruh
interpretasinya, dan itu sel yang nyaris terlewat.

| F1 | fitur LAMA (3) | fitur BARU (6) |
|---|---|---|
| **mitdb saja** | **0,6911 ±0,029** | 0,6882 ±0,023 |
| **mitdb+svdb** | 0,6262 ±0,063 | **0,6960 ±0,049** |

Efek utama, ambang §7 no.2 (< 0,04 bukan sinyal):

```
fitur baru di mitdb saja    -0,003   bukan sinyal
fitur baru di mitdb+svdb    +0,070   SINYAL
svdb dgn fitur lama         -0,065   SINYAL, MERUGIKAN
svdb dgn fitur baru         +0,008   bukan sinyal
```

**Ini interaksi murni, bukan dua perbaikan yang bertumpuk.** svdb merusak,
fitur baru menambal kerusakannya, dan hasil akhirnya kembali ke titik awal:

```
w128b (terkunci)  F1 0,6911    fd_both  F1 0,6960    selisih +0,005
```

Tanpa sel `fd_mitdb_only`, kesimpulan yang diambil akan **salah dua kali**: dari
kolom kanan saja tampak "fitur baru memberi +0,070", dan dari baris bawah saja
tampak "dataset + fitur menang". Keduanya artefak konfounding.

### Metrik sekunder — kenapa "mitdb + fitur baru" juga bukan pemenang

| | w128b | fd_mitdb_only | fd_both |
|---|---|---|---|
| precision | 0,6728 | **0,7038** | 0,6894 |
| AUC | **0,9373** | 0,9228 | 0,9352 |
| recall V | **0,9437** | **0,8983** ✗ | 0,9359 |
| recall F | 0,1521 | **0,0290** ✗ | 0,1057 |
| recall S (± ) | 0,4221 ±0,156 | 0,4203 ±0,069 | 0,4436 **±0,058** |

`fd_mitdb_only` menukar recall V dan F untuk precision. V kelas paling penting
secara klinis, jadi pertukaran itu ditolak.

### Vonis

**Kunci nol. `config.py` tidak berubah.** Jalur produksi tetap mitdb + 3 fitur,
`train_model.py` tetap memakai `train.npz`, dan mesin multi-dataset TIDAK masuk
produksi. `USE_QRSW` / `USE_RR_RATIO` tetap 0 secara bawaan — tersedia sebagai
knob, bukan sebagai nilai terkunci.

G2 tidak perlu dijawab lagi: `RR+1` tidak dikunci, jadi firmware tidak menunda
beat. Kode C-nya tetap ada di balik `#if ECG_RR_RATIO` — sudah ditulis, sudah
dikompilasi, sudah terbukti tidak mengganggu jalur lama (17/17). Kalau nanti ada
alasan mengaktifkannya, tidak ada pekerjaan tersisa.

---

## 10. Apa yang SEBENARNYA dihasilkan Fase A-F

F1 tidak bergerak. Yang dihasilkan bukan angka, tapi **hal-hal yang bisa
dipertahankan**:

| # | Hasil | Nilainya |
|---|---|---|
| 1 | Tabel 2×2 dataset × fitur | Menunjukkan perluasan dataset **merugikan** (pergeseran domain) dan fitur cuma menambalnya. Ini temuan, bukan kegagalan |
| 2 | incartdb merugikan di latih, svdb menolong recall S — efek berlawanan yang saling meniadakan | 4 varian × 3 seed. Tanpa ablasi pengisolasi, kesimpulannya terbalik |
| 3 | K1 (`class_weight`) terbantah + pelajaran konteks pipeline | Ablasi paper yang sah pun tidak transfer kalau ada langkah adaptif di hilir yang mereka tidak punya |
| 4 | recall S variansi ±0,156 → ±0,058 (fd_both) | Deteksi S jadi ANDAL, bukan lebih tinggi. Nyata, walau tidak dikunci |
| 5 | Ranjau PTQ ditemukan + assert `MAX_RHYTHM_SCALE` | Kegagalan senyap 1,8%/seed jadi berisik. Ini masuk produksi |
| 6 | Aturan tahap 2 + temuan VAL tak bisa mensertifikasi | Presisi nama V 91,7% di DS2 vs 43,9% maksimum di VAL. 5 pasien tidak cukup |
| 7 | Konvensi anotasi svdb bergeser +6 sampel | Di atas ambang bahaya 4 sampel, sistematis. Kalau lolos, gejalanya "svdb tidak menolong" |
| 8 | Tiga bug diam di pipeline | Semua menghasilkan angka salah tanpa error |
| 9 | TEST-B/TEST-C tersedia | Uji generalisasi antar-database (E3C), 85.812 beat / 39 pasien |
| 10 | Sensitivitas per kelas | Bahkan F sempurna cuma +0,037 F1 — izin berhenti memikirkan F/Q |

### Yang masuk produksi dari seluruh ini

Cuma satu: **assert `MAX_RHYTHM_SCALE`** (#5). Sisanya temuan, alat, dan data uji.

Itu hasil yang jujur: banyak yang dipelajari, satu yang dikirim, dan nol regresi.
