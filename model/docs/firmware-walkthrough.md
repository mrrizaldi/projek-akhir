# Walkthrough `firmware/` — port ke ESP32-S3

> **Ruang lingkup:** port preprocessing, deteksi R, dan inferensi INT8 ke ESP32-S3, beserta harness golden yang menjaga kesetaraan C↔Python.
> **Kode terkait:** `firmware/src/ecg_pipeline.cpp`, `firmware/src/ecg_live.cpp`, `firmware/src/main.cpp`, `firmware/src/akuisisi.cpp`, `firmware/src/tombol.cpp`, `firmware/src/menu.cpp`, `firmware/src/daya.cpp`, `firmware/src/perangkat.cpp`, `firmware/include/perangkat.h`, `firmware/include/ecg_preproc.h`, `firmware/include/model_int8.h`, `firmware/test/golden_ref.h`, `firmware/platformio.ini`
> **Prasyarat:** [`quantize-walkthrough.md`](quantize-walkthrough.md) (Fase 7)

Dokumen belajar, bukan spesifikasi. Ini jalur hardware di Lampiran C PRD.

Reproduksi:

```
cd firmware
pio test -e native      # preprocessing, INA219, payload & ring MQTT di PC, tanpa board
pio test -e esp32-s3    # preprocessing, inferensi, dan perangkat PCB di board sungguhan
pio run                 # build firmware utama (env esp32-s3)
```

`platformio.ini` memuat dua env:

| Env | Isi | Dipakai untuk |
|---|---|---|
| `esp32-s3` | `main.cpp` + seluruh pipeline + MQTT + perangkat PCB (TFT, buzzer, tombol, INA219) | firmware utama (bawaan `pio run`) dan test di board |
| `native` | modul murni tanpa Arduino | `pio test -e native` di PC |

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
`golden_prob_int8`. Sembilan beat: N, F, V, N, V, V, N, V, V.

Header GENERATED tidak memuat komentar; isinya dibaca dari sini:

| Simbol | Arti |
|---|---|
| `ECG_N_RR` | Didefinisikan di `model_int8.h` dan `ecg_preproc.h`, keduanya di balik `#ifndef` supaya tidak bentrok |
| `ECG_N_RR_DASAR`, `ECG_RR_RATIO`, `ECG_QRSW` | Bentuk fitur ritme (Fase D): jumlah kolom RR saja (tanpa QRSw/HOS) dan knob `PA_RR_RATIO`/`PA_QRSW` |
| `ECG_R_IN_WINDOW`, `ECG_QRSW_CARI` | Posisi R di window (`WIN_PRE` + group delay) dan toleransi cari puncak ±4 untuk `ecg_qrs_lebar()` |
| `ECG_PT_OFFSET`, `ECG_PT_REFINE`, `ECG_GROUP_DELAY` | Penyelarasan R-peak, urutan wajib `r - ECG_PT_OFFSET` → puncak dalam ±`ECG_PT_REFINE` → `- ECG_GROUP_DELAY` (§2 `ecg_align_r`) |
| `ecg_sos`, `ECG_N_SOS` | Butterworth 0,5-40 Hz orde 4, `{b0, b1, b2, a0, a1, a2}` per baris; kausal, group delay +4 sampel dibiarkan |
| `ECG_IN_*_SCALE/ZERO`, `ECG_OUT_*` | Kuantisasi affine: `q = round(x / scale) + zero_point`, `x = (q - zero_point) * scale` |
| `GOLDEN_RR_FIRST` | Beat 0 & 1 tak punya RR_prev/dRR: baris `golden_rr` dan probabilitasnya 0, jangan diuji. RR dihitung dari R-peak potongan ini saja, bukan record utuh, karena C hanya punya beat yang ada di potongan |
| `GOLDEN_RR_LAST` | 1 bila `PA_RR_RATIO` aktif: beat terakhir butuh beat ke depan yang tidak ada di potongan |
| `GOLDEN_TOL_*` | Toleransi float32 vs float64 (§3) |
| `golden_rr` | Per beat: RR_prev, RR_ratio, dRR |
| `golden_r_deteksi` | R-peak Pan-Tompkins atas `golden_filtered`, indeks MENTAH (belum dikompensasi/diselaraskan) |

`export_golden.py` meng-assert bahwa memfilter potongan 2.400 sampel identik
dengan memfilter sinyal utuh lalu memotongnya (filter kausal), jadi vektor uji
berdiri sendiri.

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

Prinsipnya: **test yang menjaga sifat harus menuliskan sifatnya, bukan hasil
hitungannya.** Indeks R yang ditulis sebagai angka lurus di lebih dari satu
tempat akan tertinggal saat window berubah, dan test-nya gagal dengan pesan yang
menuduh firmware.

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
yang diambil demi kekebalan antar-pasien sekaligus memberi toleransi presisi di
device.

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

Ini jebakan terbesar jalur hardware, dan hampir seluruhnya tak terlihat tanpa
harness.

### Gejala

Model, bobot, input, dan parameter kuantisasi identik. Hasilnya tidak:

```
beat 2 (V):  PC 0,9727   device 0,3359
beat 3 (N):  PC 0,0039   device 0,0391
```

Semua tertekan ke tengah — model masih mengurutkan benar, tapi keyakinannya
runtuh. Di threshold 0,35, beat aritmia berubah jadi "normal".

### Penelusuran

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

### Empat cara menulis rata-rata, dan kenapa tiga ditolak

| Rata-rata ditulis sebagai | Ukuran | Di PC | Di device |
|---|---|---|---|
| `MEAN` (model latih) | 17,8 KB | 0,973 | **0,336** (salah) |
| `AVERAGE_POOL_2D` | 20,8 KB | 0,945 | 0,945 (cocok), tapi **recall DS2 0,528** |
| `AVERAGE_POOL_2D` + `Flatten` | 19,4 KB | 0,945 | **0,418** (salah) |
| **`DEPTHWISE_CONV_2D` bobot 1/31** | 22,9 KB | 0,973 | **0,973** (dipakai) |

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

Mode putar-ulang ini bukan alat sementara. Dengan elektroda terpasang pun, dia
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
   adc1_get_raw()                             ├─ ecg_live_push + nilai_kualitas
   (atau rp_data[] saat replay)               ├─ nilai_fase (gerbang kalibrasi)
                                              ├─ inferensi tiap beat (fase pemantauan)
                                              ├─ publikasi → ring backlog MQTT
                                              ├─ ecg_mqtt_layani (non-blocking)
                                              ├─ LED kualitas sinyal (biru/oranye/hijau)
                                              ├─ TFT: HR, INA219 ⇄ jam, REC/JEDA/replay, gelombang
                                              ├─ buzzer: bip per detak (terjadwal, senyap saat kalibrasi)
                                              ├─ tombol B1/B2/B3: monitor (bisu, beku, rekam/jeda; tahan B3 simpan) / menu
                                              └─ menu di layar (bila terbuka)
```

Pin map PCB rev1 dan urutan pemasangan perangkat berada di
`firmware/include/perangkat.h` dan `firmware/src/perangkat.cpp`, dipakai
bersama oleh `main.cpp` dan test device `test_hw_*`. Tabel pin, peta tombol,
dan pohon menu ada di [`firmware/README.md`](../../firmware/README.md) bagian
Pemakaian di perangkat.

Arti LED dan prosedur rekam ada di
[`akuisisi-walkthrough.md`](akuisisi-walkthrough.md) §2–3; gerbang kalibrasi dan
publikasi ada di [`mqtt-walkthrough.md`](mqtt-walkthrough.md) §3.

**ADC dibaca DI DALAM ISR, bukan di loop.** Ini konsekuensi langsung dari
temuan §5b: beban menggumpal sampai 33 ms. Kalau ISR cuma menaikkan penanda dan
loop yang membaca ADC, sampel tetap terbaca — tapi **terlambat**, karena ADC
mengambil nilai saat dibaca, bukan saat seharusnya. Jitter waktu sebesar burst
itu masuk langsung ke interval RR.

`adc1_get_raw()` dipakai, bukan `analogRead()`: yang kedua membawa penguncian
dan tidak aman dipanggil dari ISR.

Antrean 256 sampel (0,7 detik) — jauh di atas 13 yang dibutuhkan, tapi murah
(512 byte) dan memberi ruang bagi WiFi/MQTT yang ikut memakai waktu loop. Batas
711 ms inilah yang membatasi setiap operasi jaringan di `ecg_mqtt.cpp`
([`mqtt-walkthrough.md`](mqtt-walkthrough.md) §7b).
`n_lewat` menghitung sampel yang hilang saat antrean penuh; angkanya **harus
tetap 0**, dan ikut disimpan ke berkas rekaman.

### Tombol dan menu: layar berganti, pemrosesan tidak

`tombol.cpp` hanya menghasilkan event per tombol: `TEKAN`, `PENDEK` (dilepas
sebelum 800 ms), `LAMA` (masih ditahan saat 800 ms tercapai, tanpa menunggu
dilepas), dan `LEPAS`. Arti event dirangkai pemanggil: `main.cpp` untuk mode
monitor (B1 pendek bisu, B2 pendek beku, B3 pendek rekam, B2 lama buka menu),
dan `menu.cpp` selama menu terbuka (B3/B1 pendek naik/turun, B2 lama pilih,
B2 pendek kembali, B1/B3 lama langsung ke monitor). Aksi pendek terjadi saat
dilepas karena tekanan yang sama bisa berlanjut menjadi tekan lama.

Menu bukan mode terpisah. `loop()` tetap menguras antrean, menjalankan
`ecg_live`, inferensi, rekam, dan MQTT di setiap iterasi; yang berubah hanya
siapa yang memakai layar (`tampilan_set_monitor(false)`) dan siapa yang
menerima event tombol. Gelombang tidak digambar selama menu terbuka, tetapi
bip detak tetap dijadwalkan dan NeoPixel tetap mengikuti fase.

Konsekuensinya, setiap penggambaran menu berjalan di `loop()` yang sama dengan
pengurasan antrean dan memblokirnya selama menggambar. Batasnya adalah
kedalaman antrean ISR, 256 sampel = **711 ms**. Pohon menu berupa array struct
statis; `tampilan_menu_baris()` mengingat isi tiap baris dan hanya menggambar
ulang baris yang berubah, sehingga menggeser sorotan menyentuh dua baris saja.

Terukur di board (13 Okt 2026):

| Operasi | Waktu |
|---|---|
| Bingkai menu penuh (judul, enam baris, petunjuk) | ±200 ms |
| Geser sorotan (dua baris) | ±36 ms |
| Kedalaman antrean ISR | 711 ms |
| Sampel hilang selama navigasi | 0 |

Halaman teks (Status, Info) dihitung ulang sekali per detik dengan aturan yang
sama: baris yang isinya tidak berubah tidak digambar. Pengecualian yang memblok
lebih lama dari 711 ms adalah menu Tes perangkat (bunyi, pola layar ±2 detik,
tunggu tombol sampai 10 detik); selama tes, timer akuisisi dihentikan sehingga
tidak ada sampel yang dihitung hilang, dan antrean tidak meluap.

Navigasi dapat diuji tanpa jari: serial `t1`–`t3` menyuntik tekan pendek dan
`T1`–`T3` tekan lama, dan setiap gerakan menu mencetak
`menu: <judul> [i/n] <baris>`.

### Terukur di board (tanpa elektroda, ADC membaca derau)

Kondisi uji: build inti tanpa modul MQTT dan tanpa tabel replay.

```
RAM   21,2% (69.404 B)    Flash 6,4% (419.209 B)
antrean saat burst: 12 sampel      sampel hilang: 0
```

Antrean 12 saat diperiksa di tengah burst — cocok dengan 13 yang dihitung dari
pengukuran §5b.

### Tiga sumber sinyal (menu Sumber sinyal)

Sumber dipilih dari menu **Sumber sinyal** dan disimpan di NVS, sehingga tetap
berlaku setelah boot:

| Sumber | Isi antrean ISR | Kegunaan |
|---|---|---|
| Sensor (ADC) | `adc1_get_raw()` dari AD8232 | operasi dan perekaman sinyal tubuh |
| REPLAY 208 | `golden_raw` record 208 (2400 sampel, 9 beat), diputar berulang | beban identik untuk ukur daya, uji MQTT tanpa elektroda |
| Replay rekaman | berkas `/rekam/NNN.csv` dimuat ke PSRAM (maks. 300 detik), diputar berulang | memutar ulang sinyal tubuh yang pernah direkam lewat jalur produksi; baris `#` (header, `# jeda`) dilewati sehingga segmen diputar bersambung |

Selama replay, pojok kanan atas layar monitor menampilkan `RP 208` (acuan) atau
`RP#NNN` (rekaman) berwarna kuning. Serial `y` tetap ada sebagai jalur
cadangan: ADC ⇄ replay acuan. Kedua replay
memakai satu cabang di ISR yang membaca array apa pun yang ditunjuk `rp_data`:

```cpp
if (rp_data) {
    antre[tulis] = rp_data[replay_i];      // integer saja: golden dikonversi sekali di akuisisi_mulai()
    if (++replay_i >= rp_n) replay_i = 0;
} else {
    antre[tulis] = (uint16_t)adc1_get_raw(KANAL_EKG);
}
```

Memuat berkas rekaman memblok `loop()` (membaca LittleFS); selama itu timer
dihentikan agar tidak tercatat sampel hilang. PSRAM aman dibaca di ISR ini
karena ISR tidak dipasang dengan `ESP_INTR_FLAG_IRAM`, sehingga ia ikut
ditahan saat flash ditulis.

Satu cabang di ISR, dan **seluruh jalur di hilirnya tidak berubah** — bandpass,
deteksi, penyelarasan, inferensi, LED, REC, dan MQTT semuanya berjalan seperti
biasa. Kalau simulasi punya jalur sendiri, yang tervalidasi bukan jalur
produksi.

Skalanya bebas (bandpass membuang DC, z-score membuang skala); yang haram cuma
terpotong di rail. 1000 counts/mV menaruh puncak R (~1,5 mV) di ~3550.

Dua kegunaan, dan yang kedua justru yang lebih penting:

1. **Beban kerja identik tiap ulangan** — syarat mengukur daya per mode (HW-7).
   Tanpa sinyal, tidak ada beat, dan mode inferensi mengukur nol pekerjaan.
2. **Jumlah beat yang SEHARUSNYA keluar jadi diketahui persis.** Itu yang
   membuat kehilangan data di jalur MQTT bisa diukur, bukan cuma dirasakan:
   beat hilang = beat seharusnya − beat yang sampai di broker. Setiap ganti
   sumber (menu atau `y`) me-reset `ecg_live` dan pencacah beat supaya
   hitungannya mulai dari nol. Selama replay (acuan maupun rekaman), syarat
   pemanasan dan RR-tenang gerbang kalibrasi dilewati; bypass itu diturunkan
   dari sumber sinyal sehingga berhenti bersama replay
   ([`mqtt-walkthrough.md`](mqtt-walkthrough.md) §3.1b).

Konsekuensinya: uji resiliensi pipeline tidak perlu menunggu elektroda.

#### JEBAKAN: float di dalam ISR membunuh board, pelan-pelan

Mengalikan langsung di `on_timer()` tampak wajar:

```cpp
float v = golden_raw[replay_i] * SKALA_REPLAY + OFFSET_REPLAY;   // SALAH
```

Kode itu ter-build bersih dan berjalan sekitar 20 detik, lalu:

```
Guru Meditation Error: Core 1 panic'ed (Coprocessor exception).
EXCCAUSE: 0x00000004
Rebooting...
```

ESP32 **tidak menyimpan register FPU saat masuk ISR**. Operasi float di sana
merusak state FPU task yang sedang diinterupsi, dan panic-nya baru muncul saat
task itu dijadwalkan lagi — jadi **bukan crash seketika**, yang membuatnya lolos
uji pendek. Terukur: panic di detik 18,49.

Obatnya konversi sekali di `akuisisi_mulai()` (dipanggil `setup()`) ke
`static uint16_t sim_counts[GOLDEN_N]` (4.800 byte), ISR tinggal menyalin
integer. Ongkosnya RAM 21,2% → 22,7%.

Gejala turunannya lebih berbahaya daripada crash-nya: board reboot diam-diam,
`replay` kembali `false`, dan pengukuran berikutnya melaporkan **angka yang
masuk akal tapi salah objek** — 2 beat/detik dari derau ADC, bukan dari replay.

#### Terukur di board

Kondisi uji: board N16R8, 18 Sep 2026, tanpa elektroda, replay ON.

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

Dengan input ADC mengambang (tanpa elektroda, replay OFF), firmware
mengeluarkan **~2 beat/detik, 57% diklasifikasi ARITMIA**. Derau
kecil (ayun 15 counts) tetap punya puncak, dan Pan-Tompkins berambang adaptif
selalu menemukan sesuatu — ambangnya relatif terhadap sinyal yang ada, jadi
"tidak ada sinyal" bukan kondisi yang ia kenali.

Karena itu publikasi MQTT digerbangi penilai kualitas sinyal (`AMBANG_AYUN`)
dan fase kalibrasi, bukan ada-tidaknya beat
([`mqtt-walkthrough.md`](mqtt-walkthrough.md) §3.1). Tanpa gerbang itu,
elektroda lepas = banjir alarm palsu ke broker.

### Jebakan kecil: BPM dari `millis()`

Menghitung BPM dari selisih waktu antar-cetak menghasilkan "2000 bpm", karena beat keluar **bergerombol** — deteksi berjalan sekali per
detik lalu mengeluarkan beberapa beat sekaligus. Jarak waktu antar-cetak bukan
jarak antar-detak. BPM harus dihitung dari `beat.rr[0]`, satu-satunya sumber
yang benar-benar mengukur interval jantung.

---

## 5d. Tangga ukur daya

Rancangan: [`arsip/2026-09-16-daya-design.md`](arsip/2026-09-16-daya-design.md).
Konsumsi dipisahkan per tahap lewat isolasi mode: tiap anak tangga menambah satu
beban, dan ongkos satu tahap adalah selisih dua anak tangga. Satu anak tangga
dipilih lewat serial `p0`–`p5`; `p` diikuti huruf lain (mis. `px`) kembali ke
operasi normal. Seluruh tangga dijalankan dengan dua cara: dari laptop
(`measure_power.py`, di bawah) atau oleh board sendiri (tangga mandiri, menu
**Ukur daya** atau serial `V`).

| Mode | Yang berjalan | Ongkos yang diisolasi |
|---|---|---|
| `p0` | timer ISR mati, radio WiFi mati, LED padam | dasar: ESP32-S3 + AD8232 + TFT (lampu latar) + regulator |
| `p1` | + ISR 360 Hz dan pengurasan antrean | akuisisi |
| `p2` | + `ecg_live_push()` dan penilai kualitas | DSP: bandpass, deteksi R, segmentasi |
| `p3` | + inferensi CNN per detak | TinyML |
| `p4` | + gelombang TFT, bip, LED | antarmuka |
| `p5` | + radio WiFi (`setSleep(false)`) dan publikasi MQTT | radio = operasi normal |

Teks TFT 1 Hz, tombol, dan pembacaan INA219 berjalan di semua mode, sehingga
ongkosnya hilang pada selisih. Sumber sinyal wajib replay: tanpa sinyal tidak
ada beat, dan `p3` akan mengukur nol inferensi. Radio dimatikan dengan
`esp_wifi_stop()`, bukan `WiFi.mode(WIFI_OFF)`; yang terakhir ikut men-deinit
driver dan berebut dengan task WiFi, gejalanya panic `LoadProhibited` di core 0.

Selama mode ukur aktif, INA219 dibaca tiap 100 ms (lebih lama dari konversi
rata-rata 128 sampel, ~68 ms) dan dirata-ratakan per jendela 10 detik. Satu
baris per jendela:

```
DAYA p3 n=101 I=<mA> sd=<mA> mA V=<V> P=<mW> mW beat=17 lewat=0 replay=1
```

`sd` adalah simpangan baku bacaan 100 ms di dalam jendela, `beat` jumlah beat
yang keluar dari `ecg_live` di jendela itu (bukti beban DSP berjalan), dan
`lewat` sampel yang hilang (wajib 0). INA219 memakai PGA ÷8 (`0x3FFF`,
±320 mV = ±3,2 A pada 0,1 ohm) karena burst TX WiFi melewati ±400 mA milik
PGA ÷1; LSB register shunt tetap 10 µV.

`model/scripts/measure_power.py` menjalankan tangga: membaca status `s`,
menyalakan replay bila belum, mengirim tiap mode, membuang jendela pertama
(transien ganti mode), mengambil 6 jendela (60 detik) per mode, menulis CSV ke
`model/artifacts/metrics/daya/<ts>.csv`, lalu mencetak rata-rata ± std per mode
dan selisih antar-mode. Cek mekanis: arus monoton naik `p0 ≤ … ≤ p5`, tiap
selisih > 2 × std, `lewat = 0`, dan `beat > 0` mulai `p2`. Skrip berhenti tanpa
menulis CSV bila tegangan bus < 1 V, yaitu bila INA219 tidak berada di jalur
arus alat.

Catatan tafsir: `loop()` tidak pernah tidur, jadi CPU 240 MHz aktif penuh di
semua mode. Selisih `p1`–`p3` adalah ongkos instruksi tambahan pada CPU yang
sudah aktif, dan dapat tenggelam di bawah 2 × std; cek skrip melaporkannya
sebagai tahap yang belum terukur, bukan sebagai angka.

### Kondisi jalur ukur saat ini

Register mentah INA219 (`pio test -e esp32-s3 -f test_hw_ina219 -v`, 13 Okt
2026, board dicatu USB laptop):

```
mentah: shunt 0x3400 (13312 x 10 uV) | bus 0x000A -> 1 x 4 mV, CNVR 1 OVF 0
mentah: shunt 0x55FF (22015 x 10 uV) | bus 0x000A -> 1 x 4 mV, CNVR 1 OVF 0
mentah: shunt 0x4FFF (20479 x 10 uV) | bus 0x0002 -> 0 x 4 mV, CNVR 1 OVF 0
```

Tegangan bus (VIN− terhadap GND) 0–4 mV, sedangkan tegangan shunt melompat
133–220 mV antar-bacaan. Arus 1,3–2,2 A pada bus 0 V tidak mungkin berasal dari
beban; kedua pin VIN mengambang. INA219 belum berada di jalur arus alat, dan
board menerima daya langsung dari konektor USB. Angka arus di layar dan di baris
status pada kondisi ini bukan konsumsi alat. Jalur ukur (firmware + skrip) sudah diuji
ujung ke ujung dengan `--paksa`: keenam mode terkonfirmasi, `lewat = 0` di semua
mode, dan radio kembali tersambung di `p5`.

### Prosedur ukur daya

INA219 dipasang di sisi baterai: TP4056 `OUT+` → `VIN+` → `VIN−` → masukan
konverter DC-DC, yang keluarannya mencatu pin 5V board. Rangkaian, tabel pin,
bacaan pemeriksaan, dan hal yang perlu dicek pada regulator board:
[`firmware/README.md`](../../firmware/README.md) bagian Catu daya dan
pengukuran arus. Karena arus diukur di sel, hasilnya sudah memuat rugi
konverter dan langsung dipakai untuk umur baterai (kapasitas mAh dibagi arus
mA), tanpa konversi efisiensi.

Prosedur di bawah memerintah tangga dari laptop lewat serial. Kabel USB biasa
tidak dapat dipakai selama pengukuran, karena VBUS-nya ikut mencatu board dan
membagi arus dengan baterai. Jalur serial memakai kabel USB data tanpa VBUS:
kawat merah (VBUS) diputus dan ujungnya diisolasi, sedangkan D+, D−, dan GND
tetap tersambung.

1. Rakit rangkaian catu dan sambungkan pin logika INA219 dengan semua catu
   terlepas.
2. Cabut masukan pengisi TP4056, lalu nyalakan alat dari baterai.
3. Sambungkan kabel data tanpa VBUS ke port USB board yang dipakai serial.
   Pastikan port muncul (`pio device list`).
4. Ketik `s` di `pio device monitor`. Baris `INA219` harus menunjukkan `V`
   3,0–4,2 V dan `I` positif dan stabil. Bila tidak, ikuti tabel bacaan di
   README.
5. Tutup monitor serial (port tidak boleh dipakai dua program), lalu jalankan
   dari folder `model/`:

   ```
   .venv/bin/python scripts/measure_power.py
   ```

   Durasi sekitar 7,5 menit (6 mode × 70 detik). Agar `p5` mewakili operasi
   normal, broker aktif harus terjangkau; periksa dengan `make broker-info`
   (port 1883 `terbuka`) sebelum mulai. Pemeriksaan tegangan bus < 1 V di skrip
   tetap berlaku untuk baterai: tegangan sel minimum 3,0 V, sehingga bacaan di
   bawah 1 V hanya muncul bila INA219 tidak berada di jalur arus.
6. Cek silang sekali dengan multimeter mode arus yang disisipkan di titik yang
   sama (antara TP4056 `OUT+` dan masukan konverter) pada satu mode; selisih
   dikoreksi lewat `R_SHUNT` di `perangkat.h`
   (`R_baru = R_lama × I_ina219 / I_multimeter`).
7. Ulangi pada beberapa tegangan sel (mis. sel penuh dan sel sekitar 3,5 V):
   arus di sisi baterai naik saat tegangan sel turun, karena konverter
   menjaga daya keluaran.

### Tangga mandiri dan `make pull-daya`

Tangga mandiri menghilangkan kebutuhan kabel data tanpa VBUS: board
menjalankan `p0`–`p5` sendiri dari baterai, menyimpan hasilnya, lalu laptop
menariknya setelah pengukuran selesai. Prosedur langkah demi langkah:
[`firmware/README.md`](../../firmware/README.md) bagian Ukur daya tanpa laptop.

Isinya sama dengan `measure_power.py`, dipindah ke `daya.cpp`:

- Tiap langkah: buang 1 jendela transien, ambil 6 jendela 10 detik
  (`DAYA_BLOK`, `DAYA_JENDELA_MS`), total ±7 menit. Jendela dicatat oleh
  `daya_layani()` yang sama dengan baris `DAYA`; `daya_tangga_tick()` hanya
  memindah langkah, sehingga `loop()` tidak tertahan selain saat menulis CSV
  di akhir.
- Sumber ADC dipindah ke replay acuan selama tangga dan dikembalikan sesudahnya,
  agar beban identik antar-ulangan.
- Menu ditutup selama tangga, sehingga `p4` mengukur layar monitor yang
  sebenarnya, bukan layar menu yang nyaris diam. Halaman hasil terbuka sendiri
  di akhir.
- Kriteria sah per langkah sama dengan skrip: V bus ≥ 1 V, `lewat = 0` (mulai
  `p1`), `beat > 0` (mulai `p2`), dan arus naik lebih dari 2 × sd dari langkah
  sebelumnya. Langkah yang gagal tampil `pN!` di layar dan `sah = 0` di CSV.
  Tangga yang batal di tengah (mode diubah dari luar, INA219 berhenti menjawab)
  membuat semua langkah tidak sah.
- Hasil ke `/daya/NNN.csv`, kolom `waktu,mode,n,I_mA,sd_mA,V,P_mW,beat,lewat,replay,sah`;
  `waktu` UTC ISO bila jam NTP sudah tersinkron, selain itu `+<detik uptime>s`.

`make pull-daya` (`scripts/pull_daya.py`) mengirim `v` untuk daftar berkas,
lalu `v<n>` (bawaan: berkas terakhir; `N=<n>` untuk yang lain), menyimpan ke
`model/artifacts/metrics/daya/<YYYYmmdd-HHMM>-board-NNN.csv`, dan mengulang
validasi dengan kriteria `measure_power.py` sehingga penilaian board dan laptop
dapat dibandingkan. Skrip keluar dengan kode 1 bila ada langkah TIDAK SAH.

## 6. Angka device

Kondisi uji: board N16R8, 18 Sep 2026, window 256, `pio test -e esp32-s3`.

```
inferensi     : 26,6 ms per detak (240 MHz, kernel referensi tanpa ESP-NN)
tensor arena  : 12.948 byte dari 24.576 dialokasikan
model         : 22,94 KB
heap bebas    : 312.396 byte
RAM firmware  : 74.284 byte (22,7% dari 320 KB)   build inti + 4.800 B tabel replay
Flash firmware: 430.569 byte (6,6% dari 6,25 MB)  build inti
```

Build firmware utama lengkap (dengan modul MQTT dan `wifi_secrets.h` terisi),
`pio run`: **RAM 37,0% (121.336 B), Flash 13,5% (887.873 B)**. Selisihnya
dari build inti adalah tumpukan WiFi, buffer paket MQTT, dan ring cadangan;
rinciannya di [`mqtt-walkthrough.md`](mqtt-walkthrough.md) §7.

Biaya window 256 dibanding window 250 yang diuji sebagai pembanding: inferensi
26,0 → 26,6 ms (+0,6 ms), arena 12.756 → 12.948 B, model 22,91 → 22,94 KB.
Sepadan dengan F1 +0,09.

Satu detak ~0,8 detik, jadi 26 ms = **3,3% duty cycle** — cukup longgar untuk
kontinu. Bila daya menjadi kendala, `esp-tflite-micro` dengan kernel ESP-NN
(SIMD khusus S3) dapat memangkasnya beberapa kali lipat; selisihnya bahan
pembahasan yang baik di laporan.

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
| `pio test -e native` | 23 test di PC: `test_preproc` 11 (preprocessing, deteksi R, alur hidup), `test_ina219` 6, `test_mqtt` 6 |
| `pio test -e esp32-s3` | 29 test di board: `test_preproc` 11, `test_inference` 5, `test_hw_integrasi` 5, `test_hw_tft` 2, `test_hw_adc` 2, `test_hw_tombol` 2, `test_hw_buzzer` 1, `test_hw_ina219` 1 |
| `pio test -e esp32-s3 -f test_hw_buzzer` | satu suite saja |
| `pio test -e esp32-s3 -v` | plus keluaran `Serial.printf` (benchmark, DIAG, bacaan perangkat) |
| `pio run` | build firmware utama (env `esp32-s3`), lihat RAM/Flash |
| `pio run -t upload` | flash firmware utama |
| `cd model && make export` | regenerasi `model_int8.h` setelah model berubah |
| `cd model && .venv/bin/python scripts/measure_power.py` | tangga ukur daya `p0`–`p5` dari laptop → `artifacts/metrics/daya/<ts>.csv` (§5d) |
| `cd model && make pull-daya [N=<n>]` | tarik hasil tangga mandiri `/daya/NNN.csv` → `artifacts/metrics/daya/<YYYYmmdd-HHMM>-board-NNN.csv` (§5d) |

---

**[← Fase 7 — quantize](quantize-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[akuisisi sinyal →](akuisisi-walkthrough.md)**
