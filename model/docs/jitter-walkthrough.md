# Walkthrough jitter — ketahanan terhadap error segmentasi

Fase 6c, di luar PRD. Adaptasi Dias et al. 2021 (*Arrhythmia classification from
single-lead ECG signals using the inter-patient paradigm*, CMPB 202:105948,
doi:10.1016/j.cmpb.2021.105948), bagian yang dia ablasi sendiri.

Lanjutan dari [`segmentasi-deteksi-walkthrough.md`](segmentasi-deteksi-walkthrough.md),
yang menemukan masalahnya. Dokumen ini mengukur dan memperbaikinya.

---

## 0. Peta satu layar

```
                    anotasi kardiolog          Pan-Tompkins di alat
                           │                          │
                           └──── selisihnya? ─────────┘
                                      │
                         scripts/ukur_jitter.py        ← Task 1: UKUR
                                      │
                       residu_ds1.npy (kolam 50.601 selisih)
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
        src/preprocessing.jitter_r()            scripts/sweep_jitter.py
        (dipakai melatih)                       (dipakai mengukur)  ← Task 2
                    │                                   │
                    ▼                                   ▼
        scripts/ablasi.py  ← Task 3-5            kurva metrik vs δ
        (latih varian, bandingkan)
```

Satu kalimat: **semua angka Fase 6 dipotong dari R-peak anotasi yang sempurna,
sedangkan alat memotong dari deteksi yang meleset — dokumen ini mengukur harga
selisih itu, lalu melatih model supaya tahan.**

---

## 1. Masalahnya, dinyatakan pelan-pelan

Fase 2 memotong window dari `r` **anotasi kardiolog**. Itu keputusan yang benar
dan tetap benar: jalur training harus bersih dari error detektor, kalau tidak
kita tidak pernah tahu yang rusak itu modelnya atau detektornya.

Tapi keputusan itu punya konsekuensi yang belum pernah dibayar. Di alat, tidak
ada kardiolog. Yang ada `ecg_detect_r` → `ecg_align_r`, dan hasilnya meleset.
`segmentasi-deteksi-walkthrough.md` §2 sudah mencatat betapa pekanya model ini:
**geser 4 sampel (11 ms) saja, precision jatuh 0,479 → 0,124.**

Jadi metrik Fase 6 itu batas atas, bukan ramalan. Yang belum ada: berapa jauh
kenyataan dari batas atas itu.

Dias 2021 mengalami persoalan yang sama dan menyelesaikannya dengan satu ide
sederhana: **kalau posisi R di alat meleset, rusak saja posisi R di data latih,
lalu ukur.** Mereka menyebutnya *jitter*.

---

## 2. `scripts/ukur_jitter.py` — jangan pinjam angka orang

Paper memakai jitter seragam ±δ dengan δ ≤ 18 sampel (50 ms), diambil dari
literatur QRS detection. Mereka **tidak punya detektor**, jadi angka pinjaman
itu satu-satunya pilihan.

Kita punya detektornya. Maka langkah pertama bukan meniru δ=18, tapi mengukur.

Rantai yang diukur persis rantai yang dijalankan firmware:

```python
r_kasar  = pan_tompkins_detect(filtered)        # punya delay ~38 sampel
r_pakai  = haluskan(r_kasar - PT_DETECTOR_OFFSET, filtered)
#          haluskan = cari puncak dalam ±PT_REFINE_WIN, lalu - GROUP_DELAY
pasangan = pair_detected(r_pakai, r_anotasi, toleransi 150 ms)
residu   = r_pakai[cocok] - r_anotasi[pasangan[cocok]]
```

`haluskan()` dan `pair_detected()` **tidak ditulis ulang** — keduanya sudah ada
dari Fase 6b (`scripts/eval_detected_segmentation.py`, `src/evaluate.py`). Yang
baru cuma pengumpulan statistiknya.

DS1 saja. δ hasil skrip ini dipakai melatih, dan apa pun yang dipakai melatih
tidak boleh menengok DS2.

### Hasilnya — sebarannya tidak seperti dugaan siapa pun

```
DS1: 51.021 beat anotasi, 50.601 terpasangkan, 420 terlewat (0,82%),
     2.605 deteksi palsu
residu : median 0,0   mean 0,14   std 6,07   p5 −3   p95 +2
|residu|: p95 18   p99 26   maks 54 sampel  (50 / 72 ms)
```

Perhatikan dua baris terakhir bertengkar: p95 residu bertanda cuma +2, tapi p95
dari **nilai mutlaknya** 18. Itu bukan salah hitung — itu tanda sebaran berekor.
ECDF-nya menjelaskan:

| |residu| ≤ | proporsi beat |
|---|---|
| 1 sampel | 79,85% |
| 2 sampel | 90,22% |
| 3 sampel | 92,27% |
| 5 sampel | 93,15% |
| 10 sampel | 93,57% |
| 18 sampel | 95,00% |
| 26 sampel | 99,00% |

Bacanya: **93% beat praktis terkunci tepat** (≤5 sampel), lalu ada ~7% yang
meleset jauh, sampai 54 sampel. Bukan seragam, bukan normal — campuran
"terkunci" dan "kehilangan jejak".

Ekornya punya alamat. Per record, `|p95|`:

| record | std | \|p95\| | catatan |
|---|---|---|---|
| 112, 115, 220, 230 | 0,4–0,7 | 1 | detektor nyaris sempurna |
| 108 | 14,8 | 26 | 829 deteksi palsu |
| 203 | 10,8 | 30 | 126 beat terlewat |
| 207 | 17,4 | 28 | ventricular flutter |

Jadi ekor itu bukan sifat merata detektor, melainkan **beberapa record berisik**.
Itu penting untuk menafsirkan hasil: model yang tahan jitter sebenarnya sedang
dilatih tahan terhadap *record buruk*, bukan tahan terhadap ketidaktelitian
sehari-hari.

Satu lagi yang ikut terukur, dan ini tidak bisa diobati jitter sama sekali:

```
beat terlewat per kelas AAMI: N 0,4%   F 1,7%   V 3,7%   S 6,8%
```

Beat yang tidak pernah terdeteksi tidak pernah sampai ke model. Augmentasi
apa pun tidak menolong beat yang hilang — itu urusan detektor (refraktori
200 ms memblokir beat prematur, lihat jebakan di `../CLAUDE.md`).

---

## 3. `src/preprocessing.jitter_r()` — tiga model, satu default

```python
def jitter_r(r_locations, delta=0, rng=None, model="empiris"):
    if model == "empiris":
        kolam = np.load(RESIDU_DS1)
        geser = rng.choice(kolam, size=len(r))       # ambil ulang residu asli
    elif model == "seragam":
        geser = rng.integers(-delta, delta + 1, size=len(r))   # protokol paper
    elif model == "normal":
        geser = np.rint(rng.normal(0.0, float(delta), size=len(r)))
    return np.maximum.accumulate(r + geser)
```

Tiga keputusan di sembilan baris itu:

**(a) Default `empiris`, bukan `seragam`.** Sebaran aslinya inti-tajam-ekor-berat;
seragam ±18 akan menggeser 80% beat yang sebetulnya terkunci. Mengambil ulang
dari kolam residu asli tidak memakai asumsi bentuk sama sekali — dan uji
`test_empiris_meniru_sebaran_terukur` menjaga ragamnya tetap ~6 sampel.
`seragam` tetap disediakan supaya sweep δ=0..18 bisa dibandingkan lurus dengan
Tabel 3 paper.

**(b) Jitter per beat INDEPENDEN, walau kenyataannya berkorelasi.** Record 108
berisik sepanjang record — errornya menggerombol, bukan acak per beat. Korelasi
itu sebagian **saling meniadakan** di fitur RR, karena RR itu selisih dua posisi:
kalau dua beat bertetangga sama-sama bergeser +20, RR-nya tidak berubah sama
sekali. Independen berarti ragam RR **dilebihkan**. Itu arah yang pesimistis,
jadi aman: model dilatih menghadapi kerusakan RR yang lebih parah dari kenyataan.

**(c) `np.maximum.accumulate` menjaga urutan.** Ekor 54 sampel bisa membuat dua
beat bertukar tempat kalau RR-nya pendek, dan itu menghasilkan RR negatif —
mode kegagalan yang **tidak mungkin** dihasilkan detektor sungguhan (refraktori
200 ms = 72 sampel mencegahnya). Menjaga urutan lebih jujur daripada
membiarkannya.

### Yang bergeser cuma pisau, bukan diagnosis

Di `prep_beats.process_record`, posisi ber-jitter dipakai **seluruhnya**:

```python
if jitter is not None:
    r = jitter(r)
idx     = valid_beat_indices(len(signal), r)
windows = zscore_per_window(segment_beats(filtered, r[idx]))
rr      = compute_rr_features(r)[idx]       # ikut rusak — memang harus
labels  = [to_binary_label(to_aami_class(sym[i])) for i in idx]   # TIDAK ikut
```

Kalau hanya window yang dijitter sementara RR tetap dihitung dari anotasi,
fitur RR jadi bocoran informasi sempurna dan ketahanan yang terukur palsu.
Detektor yang meleset merusak dua-duanya sekaligus.

Label tetap dari anotasi asli: yang berubah adalah **tempat kita memotong**,
bukan penyakit pasiennya.

---

## 4. `scripts/sweep_jitter.py` — metrik sebagai kurva, bukan satu angka

Protokol Tabel 3 paper, dijalankan atas model yang **tidak** dilatih ulang:
δ = 0, 2, …, 18, lima seed per δ, plus satu baris `empiris`.

Yang mahal (baca record + bandpass 650.000 sampel × 22 record) dilakukan
**sekali** dan di-cache; yang diulang per δ cuma pemotongan window. Tanpa itu
satu sweep memakan puluhan menit.

### Hasil: model kita jauh lebih rapuh dari model paper

Model Fase 5, threshold terkunci 0,35, DS2:

| jitter | recall | precision | F1 | AUC | recall S | recall V |
|---|---|---|---|---|---|---|
| anotasi (δ=0) | 0,6661 | 0,4919 | **0,5659** | 0,8866 | 0,303 | 0,933 |
| seragam δ=2 | 0,7371 | 0,2813 | 0,4072 | 0,8520 | 0,471 | 0,942 |
| seragam δ=4 | 0,8288 | 0,1960 | 0,3170 | 0,8165 | 0,686 | 0,951 |
| seragam δ=18 | 0,7920 | 0,2113 | 0,3336 | 0,8191 | 0,624 | 0,935 |
| **empiris** | 0,7080 | 0,3335 | **0,4534** | 0,8586 | 0,410 | 0,935 |

Bandingkan dengan paper (Tabel 3): sensitivitas N mereka 94,5 → 93,7 dari δ=0
ke δ=18. **Nyaris tidak bergerak.** Kita: F1 0,566 → 0,317 hanya di δ=4.

Kenapa bedanya sejauh itu? Karena yang dibandingkan bukan hal yang sama.
Klasifikasi mereka bersandar pada **statistik ringkasan** window (maks, min,
varians, RMS, kurtosis, skewness) — semua itu **kebal geseran**: menggeser
jendela sedikit tidak mengubah varians isinya. Kita memakai **Conv1D** yang
membaca bentuk gelombang pada posisi tertentu, dan tiga `MaxPooling1D(2)`
membuat geseran 4 sampel = setengah bin pooling.

Itu juga menjelaskan Tabel 6-8 paper: kelompok RR dan HOS mereka datar terhadap
jitter, kelompok morfologi yang rontok (SeS 79,1 → ~70). Cabang morfologi kita
adalah keseluruhan modelnya.

### Satu jebakan penafsiran: sebagian besar kerusakan itu soal threshold

Perhatikan kolom AUC: 0,8866 → 0,8586 di jitter empiris. Turun 3%. Sementara
F1 turun 20%. **Urutan probabilitas nyaris utuh; yang rusak titik operasinya.**
Jitter menggeser seluruh distribusi probabilitas ke atas (window yang bergeser
terlihat "tidak normal"), jadi threshold 0,35 yang dikalibrasi pada data bersih
tiba-tiba terlalu longgar dan FP meledak.

Konsekuensinya penting untuk membaca semua tabel di bawah: **model yang
dilatih ulang WAJIB dikalibrasi ulang threshold-nya**, dan perbandingan pada
threshold tetap 0,35 akan menyesatkan.

---

## 5. `scripts/ablasi.py` — satu varian, satu proses, rantai yang sama

```
rakit DS1 (+salinan ber-jitter) → pisah val per pasien → latih →
kalibrasi threshold di VAL → ukur DS2 (anotasi DAN jitter empiris)
```

Semua varian melewati rantai identik; yang berbeda cuma satu knob. Hasil
menumpuk sebagai baris di `artifacts/metrics/ablasi/ablasi.csv`.

Knob ukuran window dan HOS dibaca `config.py` **saat import**, jadi tidak bisa
diganti di tengah proses. Karena itu lewat environment, dan tiap varian jalan
di proses sendiri:

```bash
python scripts/ablasi.py --tag bersih
python scripts/ablasi.py --tag jitter --jitter empiris --salinan 2
PA_WIN_PRE=128 PA_WIN_POST=127 python scripts/ablasi.py --tag w128 --jitter empiris --salinan 2
PA_WIN_PRE=112 PA_WIN_POST=144 python scripts/ablasi.py --tag w112 --jitter empiris --salinan 2
PA_HOS=1                       python scripts/ablasi.py --tag hos  --jitter empiris --salinan 2
```

Tanpa env, `config.py` memberi nilai yang persis sama seperti sebelumnya —
ablasi tidak menyentuh gate point. Yang menang baru dikunci dengan mengubah
bawaannya, dan itu keputusan user.

**Salinan bersih selalu ikut** (`--salinan N` = N tiruan ber-jitter DI ATAS satu
salinan bersih). Alasannya ada di angka §2: 80% beat di alat meleset ≤1 sampel,
jadi kasus "tepat" bukan kasus langka yang boleh dikorbankan.

### Sebelum membaca hasil: satu seed tidak cukup, dan ini bukan basa-basi

Batch pertama dijalankan sekali per varian. Saat diulang dengan **seed yang
sama dan kode yang sama**, angkanya berbeda:

| varian | run-1 (seed 42) | run-2 (seed 42) |
|---|---|---|
| bersih | 0,5669 | 0,5642 |
| jitter | 0,6209 | **0,5882** |
| w128 | 0,6676 | 0,6657 |

`np.random.seed` + `tf.random.set_seed` **tidak** mengunci hasil di CPU:
penjadwalan thread oneDNN mengubah urutan penjumlahan float, dan di model yang
berhenti lewat EarlyStopping selisih kecil itu memilih epoch yang berbeda.

Karena itu tiap varian dijalankan **3 kali** dan yang dilaporkan rerata ±
setengah-rentang. Selisih di bawah ~0,04 F1 di sini **bukan sinyal**.

### Hasil: tiga seed per varian, DS2

| varian | window | F1 anotasi | AUC anotasi | F1 jitter | threshold |
|---|---|---|---|---|---|
| `bersih` (baseline) | 90/160 | 0,5660 ± 0,0202 | 0,8870 ± 0,0191 | 0,5423 ± 0,0359 | 0,40–0,50 |
| `jitter` | 90/160 | **0,6354** ± 0,0428 | 0,9084 ± 0,0163 | 0,6154 ± 0,0353 | 0,60–0,80 |
| `w128` | 128/127 | **0,6775** ± 0,0112 | **0,9394** ± 0,0047 | **0,6670** ± 0,0194 | 0,55–0,85 |
| `w112` | 112/144 | 0,5786 ± 0,0311 | 0,9069 ± 0,0113 | 0,5607 ± 0,0337 | 0,55–0,85 |
| `hos` | 90/160 + HOS | 0,6150 ± 0,0509 | 0,8882 ± 0,0363 | 0,6099 ± 0,0501 | 0,55–0,70 |

**1. Augmentasi jitter menang, dan menang DUA KALI.** Rentang `jitter`
[0,593–0,678] tidak bertumpang tindih dengan `bersih` [0,546–0,587]. Yang tidak
diduga: perbaikannya juga muncul di **DS2 anotasi** — data yang bersih, tanpa
jitter sama sekali. Jadi jitter di sini bukan cuma "melatih kondisi deploy",
tapi bekerja sebagai **regularisasi**: model dipaksa berhenti bergantung pada
fase yang persis dan belajar bentuk yang lebih umum. Efek yang sama persis
dengan random crop di penglihatan komputer.

**2. Window paper menang, dan alasannya bukan yang diduga.** `w128` unggul di
semua kolom, dengan rentang paling sempit dari semua varian (±0,0112 F1,
±0,0047 AUC). Hipotesis awal dokumen ini — "250 sudah cukup, yang dibeli paper
cuma garis dasar" — **salah**.

Tapi perhatikan `w112`: panjangnya **sama** 256 sampel, habis dibagi 8, dan
cakupan T-nya lebih panjang dari `w128`. Hasilnya setara baseline, jauh di bawah
`w128`. Jadi yang membayar **bukan** panjang window dan **bukan** kelipatan 8 —
melainkan **konteks 128 sampel sebelum R**. Segmen PR dan garis dasar sebelum P
ternyata memuat informasi, bukan ruang kosong.

**3. HOS tidak terbukti membayar.** Reratanya di bawah `jitter` (0,6150 vs
0,6354) tapi rentangnya paling lebar dari semua varian (±0,0509) dan bertumpang
tindih penuh. Kesimpulan jujurnya bukan "HOS merusak", melainkan **"tidak ada
bukti HOS menolong"** — dan fitur tanpa bukti tetap harus diimplementasikan
ulang di C, diuji, dan dijaga. Ditolak karena ongkos, bukan karena terbukti
buruk. (Satu run pertama sempat terbaca "HOS merugikan"; dengan tiga seed,
klaim itu tidak bertahan.)

---

## 6. Ukuran window — kenapa 256 tidak langsung diambil

Paper memakai 256 sampel: 128 sebelum R, 127 sesudah. Kita 250: 90 sebelum,
160 sesudah. Panjang totalnya nyaris sama (711 vs 694 ms); yang beda **letak R**.

| | pre-R | post-R |
|---|---|---|
| kita | 90 sampel = 250 ms | 160 sampel = 444 ms |
| paper | 128 sampel = 355 ms | 127 sampel = 353 ms |

Interval PR normal 120–200 ms = 43–72 sampel, jadi `WIN_PRE = 90` **sudah**
memuat gelombang P dengan sisa. Tambahan 38 sampel milik paper membeli garis
dasar sebelum P, bukan informasi P yang kita belum punya. Sebaliknya di kanan:
pada denyut lambat, gelombang T bisa melewati 353 ms — window paper memotongnya,
window kita tidak, dan T yang lebar itu justru penanda beat ventrikular.

Satu hal yang memang lebih rapi di 256: stride total CNN = 8 (tiga pooling), dan
256 habis dibagi 8 sedangkan 250 tidak (250 → 125 → 62 → 31, ada pembulatan).

Karena ada argumen fisiologis untuk 90/160 dan argumen aritmetika untuk 128/127,
diputuskan eksperimen. Kandidat ketiga **112/144 = 256** mengambil kelipatan 8
tanpa memotong T.

**Hasilnya (§5) mematahkan argumen fisiologis di atas.** `w128` menang,
`w112` tidak — padahal `w112` punya panjang yang sama dan cakupan T yang lebih
panjang. Satu-satunya yang membedakan `w128` adalah 128 sampel sebelum R.

Pelajaran metodologisnya lebih besar dari angkanya: penalaran "gelombang P
sudah muat di 90 sampel, jadi 128 cuma membeli garis dasar" itu **masuk akal
dan salah**. Yang memutuskan eksperimen, bukan argumen yang enak dibaca.

---

## 7. HOS — dua skalar yang nyaris gratis

Paper memakai kurtosis dan skewness (Pers. 12-13). Sendirian fitur ini **payah**:
sensitivitas kelas S cuma 2,2% (Tabel 8). Yang menarik bukan kekuatannya,
melainkan bahwa ia **datar terhadap jitter** — 2,2 → 13 dari δ=0 ke δ=18, naik,
bukan turun. Momen statistik tidak peduli jendela bergeser sedikit.

Di kita ongkosnya hampir nol, karena window yang masuk **sudah ter-z-score**:

```
mean = 0, std = 1  →  penyebut Pers. 12-13 tinggal 1
kurtosis = mean(s⁴)      skewness = mean(s³)
```

Dua pass atas 250 float yang sudah ada di RAM. Di MCU itu tidak terasa.

Ditempelkan ke **cabang ritme**, bukan cabang morfologi: dua skalar bukan deret
waktu, dan cabang RR memang tempat fitur ringkasan berkumpul. `N_RR_FEATURES`
jadi 5 dan model menyesuaikan sendiri — satu sumber kebenaran, tidak ada angka
kembar di dua tempat.

**Hasilnya: tidak terbukti membayar** (§5, poin 3). Reratanya di bawah varian
tanpa HOS dan rentangnya paling lebar dari semua varian. Kemungkinan besar
karena Conv1D sudah membaca seluruh bentuk window — momen ke-3 dan ke-4 tidak
menambah apa-apa yang belum ia lihat, beda dengan classifier linier paper yang
memang cuma punya ringkasan.

Tidak diadopsi. Kode `hos_features` tetap ditinggal di `src/features_rr.py`
beserta knob `PA_HOS`: mengulang ablasinya nanti (misalnya setelah window
berubah) cukup satu perintah, dan yang mahal bukan 5 baris itu melainkan
menemukan kembali cara mengujinya.

---

## 8. Yang sengaja TIDAK dilakukan

- **Filter dua moving-average paper (200 ms & 600 ms) tidak diadopsi.** Lebih
  murah di MCU (tanpa IIR rekursif, tanpa group delay), tapi paper **tidak
  pernah mengablasinya** — tidak ada satu tabel pun yang membandingkan filternya
  dengan alternatif. Preseden, bukan bukti. Kandidat perbaikan preprocessing
  yang berbukti ada di paper denoising multi-tahap + deteksi artefak gerak, dan
  itu menjawab masalah nyata kita (rekaman tubuh berisik), bukan masalah MIT-BIH.
- **Kelas F & Q tidak dibuang** walau paper membuangnya. Definisi masalah kita
  biner (Normal vs Aritmia) dan F/Q masuk Aritmia. Ini beda metodologis yang
  **dicatat sebagai batas pembandingan**, bukan diubah: SeS 92,5 milik paper
  tidak sebanding lurus dengan recall kita.
- **Fitur RR versi paper (`ln`, median ±15 beat, rerata seluruh record) belum
  diuji.** `ln` menolong classifier linier (LDA) karena membuat sebaran lebih
  simetris; untuk NN dengan input yang sudah dinormalisasi manfaatnya belum
  jelas. Rerata seluruh record juga tidak kausal — di alat, "seluruh record"
  belum ada saat beat pertama datang.
- **Augmentasi tidak dijalankan per epoch.** Window dipotong di muka, jadi
  jitter bersifat statis: N salinan tetap, bukan undian baru tiap epoch.
  Per-epoch butuh generator yang memotong ulang dari sinyal mentah — itu
  perombakan jalur data untuk keuntungan yang belum terbukti perlu.
- **Beat yang tidak terdeteksi tidak disimulasikan.** Jitter memindahkan
  jendela; ia tidak bisa meniru beat yang hilang sama sekali (0,82% di DS1,
  6,8% untuk kelas S). Itu masalah detektor dan diukur terpisah di Fase 6b.

---

## 9. Cek pemahaman

1. Kenapa `jitter_r` mengembalikan `np.maximum.accumulate(r + geser)` dan bukan
   `r + geser` saja? Mode kegagalan apa yang dicegah, dan kenapa mode itu tidak
   mungkin ada pada detektor sungguhan?
2. Residu terukur punya p95 bertanda +2 tapi p95 mutlak 18. Bagaimana dua angka
   itu bisa hidup berdampingan, dan apa artinya untuk memilih model jitter?
3. Di sweep, AUC cuma turun 3% sementara F1 turun 20%. Apa yang rusak, dan
   perbaikan apa yang paling murah?
4. Kenapa fitur RR **harus** ikut dihitung dari posisi yang sudah dijitter?
   Apa yang akan terjadi pada angka ketahanan kalau ia dihitung dari anotasi?
5. Paper melaporkan jitter nyaris tidak menurunkan performanya, kita anjlok.
   Sebutkan satu perbedaan arsitektur yang menjelaskannya.
6. Kenapa salinan bersih tetap diikutkan saat melatih dengan augmentasi jitter?

## 10. Skrip pendukung

| Skrip | Isi |
|---|---|
| `scripts/ukur_jitter.py` | ukur residu penyelarasan di DS1 → CSV, PNG, `residu_ds1.npy` |
| `scripts/sweep_jitter.py` | metrik DS2 sebagai fungsi δ (protokol Tabel 3 paper) |
| `scripts/ablasi.py` | satu varian ujung-ke-ujung → baris di `ablasi.csv` |
| `tests/test_jitter.py` | sifat `jitter_r` yang kalau rusak bikin hasil bohong |
