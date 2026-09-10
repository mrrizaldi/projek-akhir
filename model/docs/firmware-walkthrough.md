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

## 6. Angka device

```
inferensi     : 26,0 ms per detak (240 MHz, kernel referensi tanpa ESP-NN)
tensor arena  : 12.756 byte dari 24.576 dialokasikan
model         : 22,91 KB
RAM firmware  : 54.468 byte (16,6% dari 320 KB)   baseline kosong 18.220
Flash firmware: 356.025 byte (5,4% dari 6,25 MB)  baseline kosong 236.745
```

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
| `pio test -e native` | 7 test preprocessing di PC |
| `pio test -e esp32-s3` | preprocessing + inferensi di board |
| `pio test -e esp32-s3 -v` | plus keluaran `Serial.printf` (benchmark, DIAG) |
| `pio run` | build firmware, lihat RAM/Flash |
| `cd model && make export` | regenerasi `model_int8.h` setelah model berubah |

---

**[← Fase 7 — quantize](quantize-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[akuisisi sinyal →](akuisisi-walkthrough.md)**
