# Walkthrough `firmware/` — port ke ESP32-S3

Dokumen belajar, bukan spesifikasi. Lanjutan dari
[`quantize-walkthrough.md`](quantize-walkthrough.md) (Fase 7). Ini jalur
"menunggu hardware" di Lampiran C PRD.

Reproduksi:

```
cd firmware
pio test -e native      # preprocessing di PC, tanpa board
pio test -e esp32-s3    # preprocessing + inferensi di board sungguhan
pio run                 # build firmware
```

---

## 0. Peta besar

```
model/src/preprocessing.py  ─┐  golden reference (Python)
model/src/features_rr.py    ─┤
                             ▼
              scripts/export_golden.py
                             │
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
firmware/include/ecg_preproc.h          firmware/test/golden_ref.h
  koefisien SOS, konstanta                sinyal + hasil tiap tahap
        │                                         │
        ▼                                         ▼
firmware/src/ecg_pipeline.cpp  ──── diuji oleh ──── test_preproc/
        │                                          test_inference/
        ▼                                              ▲
firmware/include/model_int8.h ─────────────────────────┘
  (dari model/scripts/export_model_h.py)
```

Aturan tunggalnya: **Python adalah kebenaran.** Kalau C dan Python berbeda,
C yang salah — sampai terbukti sebaliknya dengan angka.

---

## 1. Kenapa harus ada golden reference

Risiko terbesar jalur hardware bukan kode yang crash, tapi **train/deploy
mismatch**: filter di C sedikit berbeda dari yang dipakai saat training, window
yang masuk model jadi bergeser distribusinya, dan akurasi runtuh **tanpa satu
pun error**. Alat tetap menyala, LED tetap berkedip, angka tetap keluar.

Karena itu vektor uji ditulis **sebelum** kode C. Dibuat sesudah, godaannya
adalah menyetel toleransi sampai kode yang terlanjur ditulis lolos — itu
pembenaran, bukan verifikasi.

`golden_ref.h` berisi record 208 (DS1), 2.400 sampel pertama:
`golden_raw` → `golden_filtered` → `golden_window` → `golden_rr` →
`golden_prob_int8`. Delapan beat: N, F, V, N, V, V, N, V.

---

## 2. Tiga fungsi di `ecg_pipeline.cpp`

### `ecg_bandpass` — kaskade 4 biquad, transposed direct-form II

```c
float y = c[0]*x + s[0];          // b0*x + state0
s[0] = c[1]*x - c[4]*y + s[1];    // b1*x - a1*y + state1
s[1] = c[2]*x - c[5]*y;           // b2*x - a2*y
x = y;                            // masuk ke section berikutnya
```

`ecg_sos` disimpan `{b0,b1,b2,a0,a1,a2}` per baris; `a0` selalu 1 (scipy sudah
menormalisasi), jadi indeksnya dilewati — `a1` ada di kolom 4, bukan 3.

**`state` milik pemanggil, bukan fungsi.** Itu yang membuat filter bisa dipanggil
per potongan sampel tanpa mengubah hasil — kondisi kerja sebenarnya, karena ADC
mengirim sampel mengalir, tidak pernah 2.400 sekaligus.

### `ecg_window_zscore` — pembagi N, bukan N−1

```c
const double std_pop = sqrt(kuadrat / ECG_WIN_LEN_);
```

numpy `std()` default memakai pembagi $N$ (populasi). Memakai $N-1$ (sampel)
menghasilkan selisih ~0,2% — lolos mata, tertangkap toleransi.

### `ecg_rr_features` — jendela kausal yang menyusut

```c
const size_t start = (j >= ECG_RR_LOCAL_WINDOW - 1) ? j - (ECG_RR_LOCAL_WINDOW - 1) : 0;
```

`ECG_RR_LOCAL_WINDOW` di-*generate* dari `config.py`, tidak ditulis `10` di sini.
Kalau suatu saat angkanya diubah di Python dan C masih 10, tidak ada yang crash —
Python dan C cuma diam-diam menghitung ritme berbeda.

### `ecg_detect_r` — Pan-Tompkins, lima tahap

```c
pt_bandpass(filtered, scratch, n);        // 5-15 Hz, 2 biquad, kausal
pt_derivative(scratch, n);                // (x[i] + 2x[i-1] - 2x[i-3] - x[i-4]) * fs/8
for (...) scratch[i] *= scratch[i];       // kuadrat
pt_mwi(scratch, n);                       // rata-rata bergerak 54 sampel (150 ms)
// lalu ambang adaptif + refraktori 200 ms
```

`scratch` disediakan pemanggil (n float) — **tanpa alokasi dinamis**, syarat wajar
di MCU dan sekaligus membuat pemakaian memorinya terlihat di tempat pemanggilan.

Dua detail yang gampang meleset saat porting:

- **Akumulator MWI pakai `double`.** Rata-rata bergerak menjumlahkan dan
  mengurangi ratusan ribu kali; dengan `float` galatnya menumpuk sampai ambang
  adaptif ikut bergeser.
- **Kernel turunan sudah digeser 2 sampel** agar kausal (bentuk aslinya butuh
  `x[i+1]`, `x[i+2]`). Geseran itu bagian dari kontrak, bukan koreksi.

Deteksi C cocok dengan Python pada 11 dari 11 puncak di `golden_raw`.

### `ecg_align_r` — tiga koreksi yang tidak boleh terlewat

```c
int lo = r_kasar - ECG_PT_OFFSET;                    // 38: median delay (kalibrasi DS1)
int puncak = argmax(filtered, lo - 25 .. lo + 25);   // puncak R sebenarnya
return puncak - ECG_GROUP_DELAY;                     // 4: geseran bandpass kausal
```

Hasilnya menaruh R di indeks **94** dalam window, sama seperti window training.
Meleset 4 sampel ke arah mana pun dan precision jatuh dari 0,479 ke 0,124 —
angkanya diukur di [Fase 6b](segmentasi-deteksi-walkthrough.md) §2.

Test `test_align_r_menaruh_puncak_di_r_idx` menjaganya sebagai sifat, bukan
sebagai angka: dia memotong window dari hasil `ecg_align_r` lalu memastikan
puncaknya mendarat di `R_IDX = ECG_WIN_PRE + ECG_GROUP_DELAY`. Pencariannya
dibatasi ±20 di sekitar `R_IDX` — `argmax` global tidak bisa dipakai karena
record 208 punya detak berdekatan (697 → 853) sehingga window selebar ini sering
memuat R tetangga yang lebih tinggi.

Namanya dulu `..._di_94` dan angkanya ditulis lurus di dua tempat. Saat window
pindah ke 128/128 (18 Sep 2026), yang satu terlewat dan test merah dengan pesan
yang menuduh firmware. Pelajarannya: **test yang menjaga sifat harus menuliskan
sifatnya, bukan hasil hitungannya.**

---

## 3. Toleransi: float32 vs float64, dan kenapa itu tidak menular

Golden dihitung scipy dengan float64; device float32 (FPU ESP32-S3 hanya
single-precision, `double` di-emulasi software dan lambat). Di filter **IIR yang
rekursif**, selisih presisi itu menumpuk:

```
selisih terukur pada tahap bandpass: 2,09e-4  (amplitudo ~0,4)
```

Bukan bug — yang haram adalah beda **sistematis**: geseran indeks, koefisien
tertukar, `a0` ikut terbaca. Karena itu toleransi tidak sekadar dilonggarkan;
`test_pipeline_utuh` menjalankan mentah → bandpass → z-score seluruhnya di C
lalu membandingkan ke window golden — dan lolos.

Alasannya elegan: **z-score membagi dengan simpangan baku**, jadi pergeseran
yang dialami bersama oleh seluruh window ikut ternormalisasi. Keputusan Fase 1
yang diambil demi kekebalan antar-pasien ternyata sekaligus membeli toleransi
presisi di device.

---

## 4. `test_bandpass_streaming` — test yang tidak punya padanan di Python

```c
for (size_t i = 0; i < GOLDEN_N; i += 64) {
    ecg_bandpass(golden_raw + i, buf_filtered + i, n, state);
}
```

Dipanggil per blok 64 sampel, hasilnya wajib sama dengan sekali jalan 2.400
sampel. Kalau `state` biquad tidak bertahan antar-panggilan, test tunggal tetap
hijau dan yang ini merah. Bug ini mustahil ketahuan dari sisi Python, karena di
Python sinyal selalu tersedia utuh.

---

## 5. Jebakan TFLite Micro: op yang sama, hasil berbeda

Ini temuan terbesar jalur hardware, dan hampir seluruhnya tak terlihat tanpa
harness.

### Gejala

Model, bobot, input, dan parameter kuantisasi identik. Hasilnya tidak:

```
beat 2 (V):  PC 0,9727   device 0,3359
beat 3 (N):  PC 0,0039   device 0,0391
```

Semua tertekan ke tengah — model masih mengurutkan benar, tapi keyakinannya
runtuh. Di threshold 0,35, beat aritmia berubah jadi "normal".

### Pengejaran

| Langkah | Hasil | Kesimpulan |
|---|---|---|
| Suapi window & RR **golden** langsung | tetap meleset | bukan port C-nya |
| Bandingkan parameter kuantisasi device vs header | identik | bukan salah scale/zero |
| PC dengan kernel referensi (bukan XNNPACK) | 0,969 | PC konsisten, device yang menyimpang |
| **Ganti library TFLM** (Chirale → tanakamasayuki) | **angka salah yang identik** | bukan bug satu library — sifat TFLM |

Dua implementasi independen sepakat di angka yang salah. Itu yang mematikan
hipotesis "bug library" dan mengarahkan ke **op**.

### Sebab

`GlobalAveragePooling1D` menjadi op `MEAN`, dan TFLM menghitungnya berbeda dari
TFLite biasa. Solusinya mengganti cara rata-rata itu **dituliskan**, bukan
mengubah modelnya.

### Empat percobaan, dan kenapa tiga gagal

| Rata-rata ditulis sebagai | Ukuran | Di PC | Di device |
|---|---|---|---|
| `MEAN` (asli) | 17,8 KB | 0,973 | **0,336** ✗ |
| `AVERAGE_POOL_2D` | 20,8 KB | 0,945 | 0,945 ✓ tapi **recall DS2 0,528** ✗ |
| `AVERAGE_POOL_2D` + `Flatten` | 19,4 KB | 0,945 | **0,418** ✗ |
| **`DEPTHWISE_CONV_2D` bobot 1/31** | 22,9 KB | 0,973 | **0,973** ✓ |

**Kenapa pooling gagal walau hasilnya "benar":** op pooling **mewarisi skala
kuantisasi input-nya** (0,332 di sini), sedangkan op konvolusi mendapat skala
**output sendiri** (0,0429 — persis yang dipilih `MEAN`). Rata-rata 31 nilai
jauh lebih kecil dari rentang input, jadi pooling membuang ~3 bit resolusi.
Di 6 beat uji hampir tak terlihat; di 49.654 beat DS2, recall jatuh dari 0,655
ke 0,528.

**Kenapa `Flatten` gagal:** dia memunculkan `SHAPE`, `PACK`, `STRIDED_SLICE` —
op shape-dinamis, dan TFLM tidak punya alokasi dinamis.

**Kenapa DepthwiseConv1D berhasil:** konvolusi dengan kernel $[\frac{1}{31},
\dots]$ secara matematika *adalah* rata-rata (identik sampai 1,19e-07 di
float32), tapi dia op konvolusi — dapat skala output sendiri, dan
`DEPTHWISE_CONV_2D` termasuk kernel paling matang di TFLM.

Ini hidup sebagai `build_deploy_model()` di `model/src/model.py`: masuk model
latih, keluar varian dengan bobot disalin apa adanya. **Tidak ada latih ulang.**

---

## 5b. Alur hidup (`ecg_live.cpp`)

Menggabungkan semua yang sudah terverifikasi jadi satu jalur: sampel ADC masuk
satu per satu, beat siap-klasifikasi keluar.

```c
int ecg_live_push(float sampel_mentah, ecg_beat_t *beat);
```

Di dalamnya:

```
sampel mentah
   → ecg_bandpass (state bertahan)  → ring 4 detik
   → tiap 1 detik: ecg_detect_r atas seluruh ring
   → ecg_align_r  (R mendarat di ECG_WIN_PRE + ECG_GROUP_DELAY = 132)
   → ecg_window_zscore + ecg_rr_features
   → beat keluar
```

**Inferensi sengaja TIDAK di dalam modul ini.** Pemanggil yang menjalankannya,
sehingga `ecg_live` bisa diuji di `pio test -e native` tanpa TFLite Micro sama
sekali — dan itu memisahkan bug logika alur dari bug inferensi.

Dua beat pertama tiap sesi tidak pernah keluar: belum punya `RR_prev`/`dRR`,
aturan yang sama persis dengan `valid_beat_indices` di `prep_beats.py`.

### Diuji tanpa elektroda

`golden_raw` diputar ulang sampel demi sampel seolah datang dari ADC 360 Hz.
Karena jawabannya sudah diketahui, seluruh rantai bisa diverifikasi:

```
beat keluar   : 6 (6 cocok anotasi, 6 prediksi benar)
  r= 697 (F) p=0.9961 -> 1   r=1378 (V) p=0.9922 -> 1
  r= 853 (V) p=0.9805 -> 1   r=1579 (V) p=0.9805 -> 1
  r=1181 (N) p=0.0039 -> 0   r=1860 (N) p=0.0117 -> 0
```

Mode putar-ulang ini bukan alat sementara. Setelah elektroda ada pun, dia
satu-satunya cara menguji firmware secara **deterministik** — sinyal tubuh tidak
pernah sama dua kali, jadi perubahan hasil tidak bisa dibedakan antara "kode
berubah" dan "jantung berbeda". Dia juga memisahkan dua jenis kegagalan: kalau
putar-ulang benar tapi sinyal nyata kacau, masalahnya di akuisisi/analog.

### Bebannya bursty — dan itu menentukan arsitektur firmware

```
rata-rata    :     82 us/sampel dari anggaran 2778 us  → beban 3,0%
puncak burst : 33.428 us (deteksi 4 detik + inferensi bersamaan)
antrean min  : 13 sampel
```

Rata-ratanya sangat longgar, tapi **puncaknya 12× anggaran satu sampel**. Kalau
akuisisi dan pemrosesan berjalan di satu alur berurutan, 12 sampel akan hilang
tiap kali deteksi berjalan — dan sampel yang hilang merusak interval RR, fitur
yang paling menentukan kelas S.

Konsekuensinya untuk firmware produksi: **ADC harus diumpankan timer ISR ke
antrean**, dan `ecg_live_push` menguras antrean itu di loop utama. Burst cuma
menumpuk ~13 sampel sementara, lalu terkuras karena beban rata-rata 3%.

Yang di-assert test bukan puncaknya, melainkan rata-rata — puncaknya dilaporkan
supaya antreannya bisa disizing dengan angka, bukan tebakan.

---

## 5c. Firmware produksi (`main.cpp`)

```
timer ISR 360 Hz ──► antrean 256 sampel ──► loop utama
   adc1_get_raw()                             ├─ ecg_live_push
                                              ├─ inferensi tiap beat
                                              ├─ LED kedip (merah = aritmia)
                                              └─ REC: simpan mentah ke LittleFS
```

**ADC dibaca DI DALAM ISR, bukan di loop.** Ini konsekuensi langsung dari
temuan §5b: beban menggumpal sampai 33 ms. Kalau ISR cuma menaikkan penanda dan
loop yang membaca ADC, sampel tetap terbaca — tapi **terlambat**, karena ADC
mengambil nilai saat dibaca, bukan saat seharusnya. Jitter waktu sebesar burst
itu masuk langsung ke interval RR.

`adc1_get_raw()` dipakai, bukan `analogRead()`: yang kedua membawa penguncian
dan tidak aman dipanggil dari ISR.

Antrean 256 sampel (0,7 detik) — jauh di atas 13 yang dibutuhkan, tapi murah
(512 byte) dan memberi ruang kalau nanti WiFi/MQTT ikut mencuri waktu loop.
`n_lewat` menghitung sampel yang hilang saat antrean penuh; angkanya **harus
tetap 0**, dan ikut disimpan ke berkas rekaman.

### Terukur di board (tanpa elektroda, ADC membaca derau)

```
RAM   21,2% (69.404 B)    Flash 6,4% (419.209 B)
antrean saat burst: 12 sampel      sampel hilang: 0
```

Antrean 12 saat diperiksa di tengah burst — cocok dengan 13 yang dihitung dari
pengukuran §5b.

### Sumber sinyal replay (toggle serial `y`)

Tekan `y` dan ISR berhenti membaca ADC; gantinya `golden_raw` (record 208, 2400
sampel, 8 beat, ~72 bpm) diputar berulang sebagai counts ADC:

```cpp
if (replay) {
    float v = golden_raw[replay_i] * SKALA_REPLAY + OFFSET_REPLAY;  // 1000 c/mV, +2048
    ...
    replay_i = (replay_i + 1) % GOLDEN_N;
} else {
    antre[tulis] = (uint16_t)adc1_get_raw(KANAL_EKG);
}
```

Satu cabang di ISR, dan **seluruh jalur di hilirnya tidak berubah** — bandpass,
deteksi, penyelarasan, inferensi, LED, REC, dan nanti MQTT semuanya berjalan
seperti biasa. Kalau simulasi punya jalur sendiri, yang tervalidasi bukan jalur
produksi.

Skalanya bebas (bandpass membuang DC, z-score membuang skala); yang haram cuma
terpotong di rail. 1000 counts/mV menaruh puncak R (~1,5 mV) di ~3550.

Dua kegunaan, dan yang kedua justru yang lebih penting:

1. **Beban kerja identik tiap ulangan** — syarat mengukur daya per mode (HW-7).
   Tanpa sinyal, tidak ada beat, dan mode inferensi mengukur nol pekerjaan.
2. **Jumlah beat yang SEHARUSNYA keluar jadi diketahui persis.** Itu yang
   membuat kehilangan data di jalur MQTT bisa diukur, bukan cuma dirasakan:
   beat hilang = beat seharusnya − beat yang sampai di broker. `y` juga
   me-reset `ecg_live` dan pencacah beat supaya hitungannya mulai dari nol.

Konsekuensinya: uji resiliensi pipeline tidak perlu menunggu elektroda.

#### JEBAKAN: float di dalam ISR membunuh board, pelan-pelan

Versi pertama mengalikan langsung di `on_timer()`:

```cpp
float v = golden_raw[replay_i] * SKALA_REPLAY + OFFSET_REPLAY;   // SALAH
```

Ter-build bersih, jalan 20 detik, lalu:

```
Guru Meditation Error: Core 1 panic'ed (Coprocessor exception).
EXCCAUSE: 0x00000004
Rebooting...
```

ESP32 **tidak menyimpan register FPU saat masuk ISR**. Operasi float di sana
merusak state FPU task yang sedang diinterupsi, dan panic-nya baru muncul saat
task itu dijadwalkan lagi — jadi **bukan crash seketika**, yang membuatnya lolos
uji pendek. Terukur: panic di detik 18,49.

Obatnya konversi sekali di `setup()` ke `static uint16_t sim_counts[GOLDEN_N]`
(4.800 byte), ISR tinggal menyalin integer. RAM 21,2% → 22,7%.

Gejala turunannya lebih berbahaya daripada crash-nya: board reboot diam-diam,
`replay` kembali `false`, dan pengukuran berikutnya melaporkan **angka yang
masuk akal tapi salah objek** — 2 beat/detik dari derau ADC, bukan dari replay.

#### Terukur di board (18 Sep 2026, tanpa elektroda)

```
periode putaran : 11 beat / 6,67 detik golden  (1,58 beat/detik)
p per putaran   : 0,984 0,996 0,019 0,996 0,988 0,078 0,992 0,996 0,500 0,988 0,078
                  → 7 ARITMIA + 4 normal, sama persis tiap putaran
sampel hilang   : 0        antrean puncak: 21 dari 256
mentah          : 1168..3618 counts (ayun 2720) — sesuai 1000 c/mV + 2048
```

Golden punya **9 beat beranotasi**, device mengeluarkan **11**. Dua selisihnya
artefak **sambungan putaran**: sampel terakhir menyambung ke sampel pertama, dan
diskontinuitas itu terlihat seperti QRS bagi detektor. Salah satunya keluar
dengan `p = 0,500` persis — model pun tidak bisa memutuskan. Untuk akuntansi
MQTT, yang dipakai **11 beat per putaran**, bukan 9: yang dihitung apa yang
dikirim alat, bukan apa yang ada di anotasi.

#### Tanpa elektroda dan tanpa replay, alat ini mengarang aritmia

Diukur tidak sengaja saat memburu bug di atas: dengan input ADC mengambang,
firmware mengeluarkan **~2 beat/detik, 57% diklasifikasi ARITMIA**. Derau
kecil (ayun 15 counts) tetap punya puncak, dan Pan-Tompkins berambang adaptif
selalu menemukan sesuatu — ambangnya relatif terhadap sinyal yang ada, jadi
"tidak ada sinyal" bukan kondisi yang ia kenali.

Untuk jalur MQTT nanti ini **wajib** jadi gerbang: publikasi harus tunduk pada
penilai kualitas sinyal (`AMBANG_AYUN`), bukan pada ada-tidaknya beat. Kalau
tidak, elektroda lepas = banjir alarm palsu ke broker.

### Jebakan kecil yang sempat muncul: BPM dari `millis()`

Versi pertama menghitung BPM dari selisih waktu antar-cetak. Hasilnya
"2000 bpm", karena beat keluar **bergerombol** — deteksi berjalan sekali per
detik lalu mengeluarkan beberapa beat sekaligus. Jarak waktu antar-cetak bukan
jarak antar-detak. BPM harus dihitung dari `beat.rr[0]`, satu-satunya sumber
yang benar-benar mengukur interval jantung.

---

## 6. Angka device

```
inferensi     : 26,6 ms per detak (240 MHz, kernel referensi tanpa ESP-NN)
tensor arena  : 12.948 byte dari 24.576 dialokasikan
model         : 22,94 KB   (window 256, 18 Sep 2026)
heap bebas    : 312.396 byte
RAM firmware  : 74.284 byte (22,7% dari 320 KB)   +4.800 B tabel replay
Flash firmware: 430.569 byte (6,6% dari 6,25 MB)
```

Angka sebelum window 256 (rujukan): inferensi 26,0 ms, arena 12.756 B,
model 22,91 KB. Window +2,4% → latensi +0,6 ms. Sepadan dengan F1 +0,09.

Satu detak ~0,8 detik, jadi 26 ms = **3,3% duty cycle** — cukup longgar untuk
kontinu. Kalau nanti daya jadi kendala, `esp-tflite-micro` dengan kernel ESP-NN
(SIMD khusus S3) bisa memangkasnya beberapa kali lipat; selisihnya justru bahan
pembahasan yang bagus di laporan.

`+119 KB flash` itu library TFLM, bukan modelnya (22,9 KB). Karena itu
`MicroMutableOpResolver<8>` mendaftarkan persis 8 op yang dipakai — bukan
`AllOpsResolver` yang menarik seluruh kernel.

---

## 7. Cek pemahaman

1. `state` di `ecg_bandpass` dipindah jadi variabel `static` di dalam fungsi.
   Test mana yang tetap hijau, dan kapan bug-nya muncul di alat sungguhan?
2. Kenapa `AVERAGE_POOL_2D` lolos uji 6 beat golden tapi gagal di 49.654 beat
   DS2 — dan pelajaran apa soal ukuran himpunan uji?
3. Model dilatih ulang lalu di-`make quantize`, tapi `make export` lupa
   dijalankan. Apa yang terjadi di device, dan kenapa tidak ada error?
4. `resolver.AddMean()` dihapus padahal model deploy tidak memakai `MEAN` lagi.
   Apa efeknya pada ukuran flash, dan kenapa `AllOpsResolver` dihindari?

## 8. Perintah

| Perintah | Melihat apa |
|---|---|
| `pio test -e native` | 11 test di PC (preprocessing, deteksi R, alur hidup) |
| `pio test -e esp32-s3` | preprocessing + inferensi di board |
| `pio test -e esp32-s3 -v` | plus keluaran `Serial.printf` (benchmark, DIAG) |
| `pio run` | build firmware, lihat RAM/Flash |
| `cd model && make export` | regenerasi `model_int8.h` setelah model berubah |

---

**[← Fase 7 — quantize](quantize-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[akuisisi sinyal →](akuisisi-walkthrough.md)**
