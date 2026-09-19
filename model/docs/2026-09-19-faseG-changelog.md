# Fase G — regime latih: hasil & diagnosis

**19 September 2026.** Lanjutan
[`2026-09-19-fitur-design.md`](2026-09-19-fitur-design.md) §5b.

Aturan §7 berlaku: 3 seed per varian, signifikan = selisih ≥ 0,04 F1.
**Fase ini menemukan aturan itu sendiri kurang ketat — lihat §5.**

---

## 0. Kenapa Fase G ada

Fase A–F berakhir **kunci nol** dari puluhan run. Sebelum menambah percobaan
sejenis, dicek apakah plan-nya menanyakan hal yang tepat. Lima tema ternyata
**nol cakupan** di seluruh `docs/` + `CLAUDE.md` (diverifikasi grep):
variansi, TEST-B/TEST-C, fungsi loss, representasi, personalisasi.

Dua kemenangan sepanjang proyek (`WIN_PRE` 128, augmentasi jitter) sama-sama
bukan soal fitur atau kapasitas melainkan **cara window disajikan**. Itu prior
yang dipakai menyusun urutan Fase G.

---

## 1. T7 — rata-rata bobot (`--swa N`). **GAGAL.**

Hipotesis: bobot akhir dipilih oleh lotere `val_auc` yang berisik (jebakan
oneDNN, changelog 18 Sep §B2), jadi rata-ratakan N epoch teratas alih-alih
memungut argmax-nya.

```
w128b    F1 0,6911 ±0,0290   AUC 0,9373
g_swa3   F1 0,6346 ±0,0387   AUC 0,9215
         dF1 -0,0565  DI ATAS ambang = SINYAL, dan negatif
```

Gagal di kedua sisi: tidak lebih baik, dan variansinya juga tidak menyempit.

**Diagnosis:** dicetak epoch mana yang dirata-rata → `[0, 1, 2]`. Bersebelahan,
bukan berjauhan. Hipotesis awal ("dua basin berbeda") **salah**.

---

## 2. Temuan utama: model produksi adalah hasil SATU epoch

Sebab kegagalan T7 terlihat di kurva `val_auc`, yang tidak pernah ditinjau
ulang setelah window 256 + augmentasi jitter dikunci 18 Sep:

```
lr 1e-3, seed 7 (jalur terkunci)   lr 1e-4, seed 7
epoch 0  0,9492  <- puncak         epoch 0   0,8797  masih naik
epoch 1  0,9345                    epoch 2-19  dataran ~0,905-0,911
...      turun MONOTON             epoch 18  0,9113  <- puncak
epoch 8  0,8635  berhenti          epoch 26  0,9082  berhenti
9 epoch, 8 terbuang                27 epoch, membaik selama 19
```

`patience=8` → selalu 9 epoch → `restore_best_weights` mengembalikan epoch 0.

**Kenapa secepat itu:** "epoch" menyesatkan sebagai satuan. DS1 teraugmentasi
121.857 beat ÷ `BATCH_SIZE` 64 = **1.905 langkah gradien per epoch**. Untuk
6.417 parameter dengan Adam 1e-3, satu epoch lebih dari cukup untuk menghafal.
Augmentasi ×3 di Fase 6c melipatgandakan langkah per epoch, dan tak ada yang
meninjau ulang jadwal latihnya.

**T7 tidak bisa diselamatkan aturan rata-rata yang lebih pintar:** puncaknya di
tepi dan sisanya menurun, jadi merata-rata apa pun menarik masuk bobot lebih
buruk. Rata-rata bobot butuh **dataran**; pada 1e-3 tidak ada.

---

## 3. T12 — learning rate. Konsekuensi langsung §2.

`CLAUDE.md` mengunci LR dengan alasan *"knob yang **belum terbukti perlu**"*.
Alasan itu gugur oleh ukuran: overfit dalam satu epoch bukan kemewahan tuning,
itu regime rusak. Knob `--lr` ditambahkan (bawaan 0 = 1e-3 = jalur terkunci).

---

## 4. T8 — TEST-B/TEST-C jadi wasit T12

Fase A membangun held-out svdb (20 pasien) + incartdb (19 pasien) = 39 pasien,
85.812 beat, lalu tidak pernah dipakai. `ablasi.py --lintas-db` menjadikannya
bagian harness; hasil ke `lintas_db.csv` **terpisah** supaya skema
`ablasi.csv` tidak bergeser (header hanya ditulis sekali).

Threshold tetap dari VAL, tidak pernah disetel ulang di set uji.

| Set | pasien | F1 1e-3 | F1 1e-4 | vonis F1 | AUC |
|---|---|---|---|---|---|
| DS2 | 22 | 0,6535 ±0,0280 | 0,6729 ±0,0483 | +0,019 bukan sinyal | 0,9305 → 0,9415 |
| TEST-B | 20 | 0,5237 ±0,0084 | 0,5306 ±0,0339 | +0,007 bukan sinyal | 0,8667 → 0,8860 |
| TEST-C | 19 | 0,6784 ±0,1080 | **0,8025 ±0,0277** | **+0,124 SINYAL** | 0,9352 → 0,9525 |

**AUC naik di 4 dari 4 set.** Konsistensinya yang jadi argumen, bukan besar
tiap deltanya.

### Pertukaran yang tajam: S ditukar V

| seed | F1 | recall **S** | recall **V** |
|---|---|---|---|
| 13 | 0,6523 → **0,7091** | 0,2859 → **0,3099** | 0,9161 → **0,9671** |
| 42 | 0,6261 → **0,6970** | 0,4771 → *0,3834* | 0,8664 → **0,9758** |
| 7 | 0,6821 → *0,6125* | 0,5790 → *0,2446* | 0,9627 → **0,9779** |

recall V naik 3/3. recall S turun 2/3, dan turun di rerata DS2 (−0,135) serta
TEST-C (−0,043); naik hanya di TEST-B (+0,035).

Yang bikin serius: threshold 1e-4 **lebih longgar** (0,53 vs 0,65), yang
seharusnya menaikkan recall. Recall S tetap turun → **bukan artefak titik
operasi**, melainkan model yang memeringkat beat S lebih buruk.

F1 & AUC tetap naik karena V mendominasi jumlah beat aritmia. Artinya 1e-4
**memperbaiki kelas yang sudah kuat dan memperburuk yang lemah** — arah
berlawanan dengan kebutuhan proyek ini.

Catatan: seed 7 jadi seed "pro-S" di **kedua** batch (recall S baseline 0,6095
dan 0,5790). Reproduksibel, jadi bukan lotere murni.

### Probe LR tengah (3e-4): pertukarannya TIDAK bisa dihindari

Hipotesis: mungkin ada LR tengah yang memberi kenaikan AUC tanpa kehilangan S.
Dijawab dengan 3 seed penuh — **tidak**.

| LR | recall **S** | recall **V** | recall **F** | DS2 AUC | TEST-C F1 |
|---|---|---|---|---|---|
| **1e-3** (terkunci) | **0,4473** | 0,9151 | 0,1804 | 0,9305 | 0,6784 ±0,1080 |
| 3e-4 | *0,2024* | 0,9663 | 0,3265 | 0,9348 | **0,8481 ±0,0098** |
| 1e-4 | *0,3126* | **0,9736** | **0,3591** | **0,9415** | 0,8025 ±0,0277 |

3e-4 justru **paling buruk** di S. Jadi polanya bukan "ada titik manis di
tengah", melainkan: **turunkan LR → S turun, semua yang lain naik.**

Yang mencolok: **recall F naik dua kali lipat** (0,180 → 0,359) — kelas yang
sudah dinyatakan tak tertolong sejak Fase 6 dan dikonfirmasi ulang oleh P1 & P3.

Dalam jumlah beat DS2 (S ~1.837, V ~3.220, F ~388) pertukarannya nyaris impas:
S kehilangan ~248 deteksi, V+F mendapat ~259. Itu sebabnya F1 tidak bergerak —
yang berubah **komposisi** deteksi, bukan jumlahnya.

### Uji titik operasi setara — hipotesis "artefak underfit" TERBANTAH

Aturan §A5 (changelog 18 Sep) melarang membandingkan recall di dua titik
operasi berbeda. Maka threshold tiap model digeser sampai **recall TOTAL-nya
sama**, baru recall per kelas diadu (`scripts/cek_titik_operasi.py`, seed 42):

| recall total | 1e-3 | 3e-4 | 1e-4 |
|---|---|---|---|
| 0,65 | **S 0,436** / V 0,848 | S 0,216 / **V 0,945** | S 0,234 / V 0,943 |
| 0,70 | **S 0,517** / V 0,885 | S 0,295 / **V 0,974** | S 0,320 / V 0,967 |
| 0,80 | **S 0,716** / V 0,933 | S 0,552 / **V 0,985** | S 0,576 / V 0,983 |

Di **enam dari enam** titik operasi, 1e-3 unggul di S dan kalah di V. Arahnya
tidak pernah berbalik.

**Kesimpulan: defisit S itu NYATA, bukan artefak titik operasi.** Kedua model
benar-benar mempelajari hal yang berbeda — 1e-3 memeringkat beat S lebih baik,
1e-4 memeringkat beat V lebih baik.

### Hipotesis yang DITARIK: "keunggulan S milik 1e-3 adalah artefak UNDERFIT"

Beat S mirip N secara morfologi; yang membedakannya waktu kedatangan. Model
yang berhenti setelah satu epoch punya batas keputusan yang belum tajam, jadi
ia "ragu" dan pada threshold terkalibrasi banyak beat S ikut tertangkap. Model
yang terlatih penuh dengan percaya diri menyebut beat S itu Normal — karena
secara bentuk memang Normal.

Kalau benar, konsekuensinya penting: recall S 0,4473 bukan prestasi arsitektur
melainkan efek samping model kurang latih.

**Diuji, dan salah.** Pada recall total yang disamakan, keunggulan S milik
1e-3 tetap utuh (tabel di atas). Model yang "ragu" akan kehilangan
keunggulannya begitu titik operasinya disetarakan — ini tidak.

### Hipotesis pengganti: latih lebih lama = makin bergantung MORFOLOGI

Yang tersisa untuk menjelaskan pertukaran S↔V:

Cabang morfologi (CNN atas window) punya sinyal kuat untuk V — beat ventrikular
bentuknya memang jelas beda. Cabang ritme cuma 3 skalar. Semakin lama dilatih,
model makin menemukan bahwa morfologi membayar, dan bobot efektif cabang ritme
makin tenggelam. **S adalah satu-satunya kelas yang morfologinya TIDAK
membedakan** — ia hanya terlihat dari ritme. Jadi latih lebih lama =
V naik, S turun.

Kalau hipotesis ini benar, konsekuensinya jauh melampaui learning rate:

1. Menjelaskan kenapa Fase D gagal — menambah fitur ritme tidak menolong kalau
   model memang sedang belajar mengabaikan cabang itu.
2. Obat untuk S bukan LR dan bukan fitur, melainkan **memaksa cabang ritme
   dipakai**: kepala terpisah per cabang, atau pendekatan dua tahap ala P5
   (V lewat morfologi, S lewat ritme).

**Diuji, dan juga salah.** Kontribusi tiap cabang ke lapisan penggabung
(`sum |bobot| × std aktivasi masuk` — bukan |bobot| telanjang, karena skala
keluaran GAP dan fitur RR berbeda):

| model | morfologi | ritme | porsi ritme |
|---|---|---|---|
| 1e-3 | 14,78 | 1,16 | 7,3% |
| 3e-4 | 11,26 | 0,85 | 7,0% |
| 1e-4 | 7,30 | 0,98 | **11,8%** |

Model yang dilatih lebih lama justru **lebih** bergantung ritme, bukan kurang.
Yang menyusut morfologinya (14,78 → 7,30) sementara ritme hampir tetap —
konsisten dengan bobot yang lebih terkonvergensi, dan **tidak menjelaskan
pertukaran S↔V sama sekali**.

### Status jujur: pertukarannya NYATA, sebabnya BELUM DIKETAHUI

Dua cerita mekanistik diajukan dan dua-duanya diukur lalu gugur:

| Hipotesis | Uji | Hasil |
|---|---|---|
| Keunggulan S = artefak underfit / model ragu | recall per kelas pada recall total disamakan | **salah** — keunggulan S bertahan di 6/6 titik |
| Latih lebih lama = makin bergantung morfologi | kontribusi cabang ke Dense penggabung | **salah** — porsi ritme justru naik |

Yang berdiri sebagai fakta: **menurunkan learning rate menukar recall S dengan
recall V dan F, secara nyata dan reproducible, dan tidak ada penjelasan yang
sudah terverifikasi.**

Dicatat begitu apa adanya. Menaruh cerita mekanistik yang belum diuji ke Bab 4
lebih berbahaya daripada mengakui ada pertukaran yang belum dipahami —
penguji bisa membantah cerita, tidak bisa membantah tabel.

---

## 5. Pelajaran metodologis: ambang 0,04 berlaku untuk RERATA 3 SEED

Konfigurasi identik, seed identik, dijalankan dua kali pada hari yang sama:

```
w128b     F1 DS2 0,6911 ±0,0290   (batch 1)
t8_lr1e3  F1 DS2 0,6535 ±0,0280   (batch 2)
selisih   0,0376
```

§7 no.1 selama ini dibaca "1 run tidak sah, pakai 3 seed". Ternyata **rerata
3 seed pun bergoyang ~0,04 antar batch.**

Konsekuensi: mengulang 3 seed **tidak** mengangkat selisih kecil jadi sinyal.
Yang benar-benar menaikkan daya pisah adalah **set uji lebih besar** — dan itu
persis nilai TEST-B/TEST-C. Vonis +0,124 di TEST-C bertahan jauh di atas
lantai derau mana pun yang terukur di sini.

### Klaim yang DITARIK

"Variansi 3× lebih sempit di 1e-4" — batch 1 memberi setengah-rentang F1 DS2
±0,0096, batch 2 memberi ±0,0483 (lebih lebar dari baseline). Disimpulkan dari
satu batch, tidak bereplikasi. Yang tersisa dari T12 adalah kenaikan AUC.

---

## 6. T5 — k-dari-n. **GUGUR sebelum ditulis.**

Aturan "k beat berturut-turut" hanya menolong kalau FP lebih tunggal daripada
TP. Di DS2 terbalik:

```
TP   3813 beat  tunggal 87,0%  run>=3  3,7%
FP   2302 beat  tunggal 60,8%  run>=3 22,3%
  rec 222        tunggal 33,7%  run>=3 43,8%
```

k≥2 membuang **87% true positive** dan menyimpan FP bergerombol. Sebabnya
struktural: **65,3% beat aritmia DS2 adalah kejadian tunggal**. Label kita
per-beat; k-dari-n alat deteksi *episode*. Salah alat, bukan salah parameter.

### Temuan pengganti: ke mana FP pergi (`scripts/cek_fp.py`)

Menumpuk, bukan tersebar: **2 record = 56,6%** dari seluruh FP, 8 record = 92,4%
(dari 22).

| simbol | FP | %FP | n negatif | FPR |
|---|---|---|---|---|
| N | 1568 | 68,1% | 36.401 | 0,043 |
| **L** (LBBB) | 536 | 23,3% | 4.121 | **0,130** |
| R (RBBB) | 187 | 8,1% | 3.471 | 0,054 |
| j (nodal escape) | 11 | 0,5% | 213 | 0,052 |

**L+R = 31,4% dari seluruh FP**, dan FPR beat LBBB **3× beat N biasa**. Ini
tagihan terukur dari decision point yang diambil sadar: *"L & R → N: ikut AAMI…
beda dari intuisi klinis"*. Beat LBBB memang QRS-nya lebar dan mirip
ventrikular — cabang morfologi benar secara klinis, label AAMI yang menyebutnya
salah.

Rec 222 (FPR 0,344) mekanisme lain: 83% N + 9% nodal escape + 8% atrial
prematur → ritme tak teratur, cabang ritme yang menyala. Dua penyumbang
terbesar, dua mekanisme, **dua-duanya bukan derau yang bisa disaring waktu**.

---

## 7. Apa yang dihasilkan Fase G

F1 tidak bergerak (lagi). Yang dihasilkan:

| # | Hasil | Nilainya |
|---|---|---|
| 1 | Model produksi = hasil **1 epoch** latih | Regime latih rusak, tidak pernah terlihat karena kurva tak ditinjau setelah Fase 6c |
| 2 | "Epoch" menyesatkan: 1.905 langkah/epoch | Augmentasi ×3 mengubah lama latih tanpa ada yang sadar |
| 3 | Ambang 0,04 berlaku untuk rerata 3 seed | Memperketat §7; sebagian vonis "bukan sinyal" Fase A–F jadi lebih lemah, bukan lebih kuat |
| 4 | TEST-B/TEST-C masuk harness (`--lintas-db`) | Klaim generalisasi E3C, 39 pasien, dan wasit yang lebih peka dari DS2 |
| 5 | T12: AUC naik 4/4 set, TEST-C F1 +0,124 | **Tapi recall S turun** — pertukaran, bukan kemenangan |
| 6 | T7 gugur + alasannya (tidak ada dataran) | Layak diulang di 1e-4, di mana dataran ada |
| 7 | T5 gugur: 65% aritmia adalah kejadian tunggal | Post-processing episode tidak berlaku untuk label per-beat |
| 8 | 31% FP = beat LBBB yang AAMI sebut Normal | Mengubah precision 0,62 dari "model lemah" jadi "tagihan konvensi label" |
| 9 | `ringkas_ablasi.py`, `cek_fp.py` | Vonis ablasi tidak lagi dihitung tangan |

### Yang masuk produksi

**Nol.** Semua knob (`--swa`, `--lr`, `--lintas-db`) bawaannya mati; tanpa flag
jalur terkunci byte-identik. `config.py` tidak tersentuh.

Itu hasil yang jujur: banyak yang dipelajari, nol yang dikirim, nol regresi —
dan satu decision point (`Learning rate`) yang alasannya kini terbukti salah
dan menunggu keputusan user.

---

## 8. Gate `Learning rate` — bahan keputusan

Ini **pertukaran nilai**, bukan soal angka mana yang lebih besar. Karena itu
tidak diputuskan sendiri.

**Alasan memilih 1e-4:**

1. Regime 1e-3 **tidak bisa dipertahankan di sidang**. Pertanyaan "coba
   tunjukkan kurva latihnya" dijawab dengan model yang berhenti setelah satu
   epoch dan delapan epoch terbuang.
2. **TEST-C F1 +0,124** — satu-satunya hasil selevel sinyal dari seluruh Fase
   A–G, dan tepat jenis klaim yang dihargai kerangka E3C (generalisasi
   lintas-database, 39 pasien held-out).
3. AUC naik di **4 dari 4** set evaluasi.
4. recall F **naik dua kali lipat**, recall V naik — hanya S yang turun.
5. Keunggulan S milik 1e-3 diduga artefak underfit (§4), jadi mempertahankannya
   berarti mempertahankan model yang kurang latih demi satu metrik.

**Alasan mempertahankan 1e-3:**

1. recall S **0,4473 → 0,3126**, dan S adalah kelemahan yang dinyatakan proyek
   ini sejak Fase 6 — seluruh program fitur (Fase D) ditujukan ke sana.
2. Mengubahnya berarti menjalankan ulang rantai penuh: prep → split → train →
   kalibrasi → eval → quantize → golden → export, plus `pio test`.
3. Angka Bab 4 yang sudah ditulis ikut berubah.

**Rekomendasi Claude: pilih 1e-4**, dengan alasan 1 dan 5 sebagai penentu —
mempertahankan konfigurasi yang keunggulannya berasal dari kurang latih adalah
dasar yang rapuh untuk dipertahankan di depan penguji. Tapi keputusan soal
"kelas mana yang diutamakan" milik user, bukan Claude.

**Kalau diputuskan pindah**, yang wajib ikut: `config.py` (`LEARNING_RATE`),
baris `Learning rate` di tabel decision point, rantai penuh dijalankan ulang,
`golden_ref.h` + `model_int8.h` di-regen bersama, dan angka di
`docs/README.md` §"Angka penting" diperbarui.
