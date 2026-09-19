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
