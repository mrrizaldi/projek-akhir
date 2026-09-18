# Changelog Fase 6c — 18 September 2026

Catatan perubahan **rencana → pelaksanaan** untuk
[`2026-09-18-robustness-plan.md`](2026-09-18-robustness-plan.md).
Isi konseptualnya ada di [`jitter-walkthrough.md`](jitter-walkthrough.md); di
sini yang dicatat cuma **apa yang berbeda dari rencana, kenapa, dan bagaimana
mengulanginya**.

Ditulis supaya pengujian lanjutan tidak perlu menebak-nebak kenapa suatu jalan
diambil — dan supaya keputusan yang diambil dari kursi Claude bisa dibatalkan
user tanpa arkeologi.

---

## A. Yang berubah dari rencana

| # | Rencana | Yang dikerjakan | Alasan |
|---|---|---|---|
| A1 | Task 0: kerjakan `daya-plan` Task 4 | ✅ sama, tanpa perubahan | — |
| A2 | Task 1: skrip baru yang menjalankan rantai penyelarasan | `ukur_jitter.py` **mengimpor** `haluskan()` dari `eval_detected_segmentation.py` | rantai yang sama sudah ada sejak Fase 6b; menyalinnya = dua sumber kebenaran yang bisa berbeda diam-diam |
| A3 | Task 2: `--jitter/--seed/--out` di `prep_beats.py` **dan** `build_split.py`, npz per varian | `process_record(jitter=callable)` saja; `sweep_jitter.py` & `ablasi.py` merakit **di memori** | npz per (δ, seed) = 50+ set file untuk data yang dipakai sekali. Cache sinyal+bandpass sekali, ulang cuma pemotongan — sweep 51 konfigurasi jadi hitungan menit |
| A4 | Task 3: "ulangi kurva Task 2 untuk model baru" (kurva δ=0..18 per varian) | dua titik ukur per varian: DS2 anotasi + DS2 jitter empiris | kurva penuh × 5 varian × 3 seed = 765 evaluasi untuk informasi yang sama. Titik empiris adalah kondisi deploy; sisa kurva sudah dijawab §4 walkthrough |
| A5 | Task 3: kriteria adopsi "recall di δ=p95 naik tanpa recall δ=0 turun >2 poin" | dinilai dari **F1 + AUC**, bukan recall telanjang | tiap varian dapat threshold sendiri dari kalibrasi VAL (0,40–0,85). Membandingkan recall antar-titik-operasi yang berbeda itu membandingkan dua hal berbeda |
| A6 | Task 4-5: ablasi 1 run per varian | **3 seed per varian**, dilaporkan rerata ± setengah-rentang | ketahuan di tengah jalan: seed yang dikunci **tidak** mengunci hasil (lihat B2) |
| A7 | Task 6 tidak masuk ruang lingkup ("gas sampai Task 5") | **dieksekusi 18 Sep 2026** atas persetujuan eksplisit user atas hasil ablasi | gate point `config.py` dibuka user |

## B. Yang tidak ada di rencana sama sekali

**B1 — Model jitter "empiris".** Rencana mengasumsikan pilihan seragam/normal
ala paper. Pengukuran Task 1 menunjukkan residu kita **inti tajam + ekor berat**
(80% ≤1 sampel, tapi maks 54) — tidak cocok kedua bentuk itu. Ditambahkan model
ketiga: ambil ulang langsung dari kolam residu terukur, tanpa asumsi bentuk.
`residu_ds1.npy` jadi artefak baru yang dibutuhkan `jitter_r`.

**B2 — Nondeterminisme oneDNN.** `np.random.seed` + `tf.random.set_seed`, kode
identik, dua kali jalan → F1 DS2 0,6209 vs 0,5882 (varian jitter). Penjadwalan
thread mengubah urutan penjumlahan float; EarlyStopping lalu memilih epoch
berbeda. Konsekuensi permanen: **ablasi 1 run tidak sah di repo ini**, dan
selisih < ~0,04 F1 bukan sinyal. Ditambahkan `--seed` ke `ablasi.py`.

**B3 — Knob environment di `config.py`.** `PA_WIN_PRE`, `PA_WIN_POST`, `PA_HOS`.
Tanpa env nilainya persis seperti semula, jadi ablasi berjalan tanpa menyentuh
gate point. Rencana tidak menyebut bagaimana varian window dijalankan.

**B4 — Varian `w112` (112/144).** Tidak ada di rencana; ditambahkan sebagai
**isolator**. Tanpa dia, kemenangan `w128` bisa dikira soal panjang 256 atau
kelipatan 8. `w112` punya keduanya dan tidak menang → yang membayar konteks
pre-R. Satu varian tambahan mengubah kesimpulan dari "256 lebih baik" jadi
"128 sampel sebelum R lebih baik", dan cuma yang kedua yang bisa dipertahankan.

**B5 — `R_IDX` di test firmware.** `test_preproc.cpp` menghafal angka 94.
Diganti rumus `ECG_WIN_PRE + ECG_GROUP_DELAY`. Tanpa ini, pindah window bikin
test gagal karena alasan yang salah (angka hafalan, bukan sifat yang rusak).

## C. Keputusan yang diambil Claude, yang rencananya milik user

Rencana menandai dua tempat `[kamu yang tulis]`. Atas permintaan eksplisit
("gas ... sekalian sampai task 5"), keduanya dikerjakan Claude. Isi
keputusannya dicatat di sini supaya gampang dibatalkan:

| Keputusan | Diambil | Alternatif yang ditolak |
|---|---|---|
| Bentuk sebaran jitter | empiris (resample kolam residu) | seragam ±18 (paper) — melatih error yang bukan milik kita; normal(0,σ) — std cocok, bentuk tidak |
| Korelasi jitter antar-beat | independen per beat | berkorelasi per record (lebih setia), tapi independen melebihkan ragam RR = pesimistis = aman |
| Urutan R setelah jitter | `np.maximum.accumulate` | membiarkan bertukar → RR negatif, mode kegagalan yang mustahil di detektor nyata |
| Momen HOS | pembagi N (bias), kurtosis mentah | `ddof=1` & excess kurtosis — selisih konstan 0,4% di window 250 sampel, diserap bobot |
| Salinan bersih saat augmentasi | selalu ikut | hanya salinan ber-jitter — membuang kasus mayoritas (80% beat meleset ≤1 sampel) |

Semua ada tesnya (`tests/test_jitter.py`) yang menjaga **sifat**, bukan pilihan —
mengganti bentuk sebaran tidak akan membuat test merah.

## D. Cara mengulang

```bash
cd model
# 1. ukur jitter detektor sendiri (wajib duluan: menghasilkan residu_ds1.npy)
python scripts/ukur_jitter.py

# 2. metrik vs delta untuk model yang sudah ada (protokol Tabel 3 Dias 2021)
python scripts/sweep_jitter.py --model model_fp32.keras --tag dasar

# 3. ablasi — SATU varian per proses, 3 seed masing-masing
for S in 42 7 13; do
  python scripts/ablasi.py --tag bersih --seed $S
  python scripts/ablasi.py --tag jitter --jitter empiris --salinan 2 --seed $S
  PA_WIN_PRE=128 PA_WIN_POST=127 python scripts/ablasi.py --tag w128   --jitter empiris --salinan 2 --seed $S
  PA_WIN_PRE=112 PA_WIN_POST=144 python scripts/ablasi.py --tag w112   --jitter empiris --salinan 2 --seed $S
  PA_WIN_PRE=128 PA_WIN_POST=128 python scripts/ablasi.py --tag w128b  --jitter empiris --salinan 2 --seed $S
  PA_HOS=1                       python scripts/ablasi.py --tag hos    --jitter empiris --salinan 2 --seed $S
done
```

Hasil menumpuk sebagai baris di `artifacts/metrics/ablasi/ablasi.csv`
(satu baris = satu run, kolom `tag` + `seed`). Hapus file itu untuk mulai
bersih; `ablasi_seed42.csv` adalah arsip batch pertama (sebelum kolom `seed`
ada) dan sengaja tidak digabung.

Ongkos: ~4 menit per varian tanpa augmentasi, ~7 menit dengan `--salinan 2`
(12 core CPU, tanpa GPU).

## E. Artefak yang dihasilkan

| Berkas | Isi |
|---|---|
| `artifacts/metrics/jitter/jitter_residu.csv` / `.png` | residu per record + histogram/ECDF |
| `artifacts/metrics/jitter/residu_ds1.npy` | **kolam residu — dipakai `jitter_r` saat runtime** |
| `artifacts/metrics/jitter/sweep_jitter_dasar.csv` / `.png` | metrik vs δ |
| `artifacts/metrics/ablasi/ablasi.csv` | satu baris per run ablasi |
| `artifacts/model_fp32_<tag>.keras` | model tiap varian (seed utama saja) |

`residu_ds1.npy` itu **dependensi runtime**, bukan sekadar laporan: menghapusnya
membuat `jitter_r(model="empiris")` gagal. Jalankan ulang `ukur_jitter.py`.

---

## F. Follow-up yang dieksekusi hari ini (18 Sep 2026)

Dua pertanyaan yang muncul dari hasil ablasi, dijawab sebelum mengunci:

**F1 — `w128` itu 255 sampel, bukan 256.** Paper: 128 sebelum R + R + 127
sesudah = 256. Parametrisasi kita `signal[r-WIN_PRE : r+WIN_POST]`, jadi
128/127 = **255**, dan 255 tidak habis dibagi 8 (pooling memotong:
255→127→63→31). Varian `w128b` (128/128 = 256 tepat) dijalankan 3 seed.

| varian | F1 anotasi | AUC | F1 jitter |
|---|---|---|---|
| `w128` (255) | 0,6775 ± 0,0112 | 0,9394 ± 0,0047 | 0,6670 |
| `w128b` (256) | 0,6911 ± 0,0290 | 0,9373 ± 0,0087 | 0,6750 |

Rentangnya tumpang tindih → **tidak terbedakan**. Dipilih 128/128 karena: sama
persis dengan paper (bisa dibandingkan lurus di laporan), rerata F1 tertinggi,
dan 256 habis dibagi 8 sehingga rantai pooling tidak memotong (256→128→64→32).

**F2 — apakah 3 salinan lebih baik dari 2?** Tidak: `w128s3` 0,6099 ± 0,0254,
**lebih buruk** dari `w128` 2 salinan. Menambah salinan menambah data ber-jitter
tanpa menambah pasien; rasio salinan bersih : ber-jitter makin timpang dan model
mulai belajar kondisi rusak sebagai hal normal. `JITTER_SALINAN = 2`.

## G. Task 6 — penguncian (gate point dibuka user 18 Sep 2026)

Nilai yang dikunci di `config.py`:

| Konstanta | Lama | Baru |
|---|---|---|
| `WIN_PRE` / `WIN_POST` | 90 / 160 (250) | **128 / 128 (256)** |
| `THRESHOLD` | 0,35 | **0,80** |
| `JITTER_MODEL` / `JITTER_SALINAN` | — | **`empiris` / 2** |

Rantai yang dijalankan ulang, berurutan:

```
make prep     202.560 beat (DS1 ×3 salinan, DS2 bersih)     ~10 detik
make split    DS1 152.904 | DS2 49.656
make train    EarlyStopping, model_fp32.keras               ~83 detik
scripts/calibrate_threshold.py   VAL F1 maks 0,6917 @ 0,80
make eval     DS2: recall 0,6996 prec 0,6235 F1 0,6594 AUC 0,9334
make quantize INT8 22,94 KB, delta recall +0,0108
scripts/export_golden.py         ecg_preproc.h + golden_ref.h (9 beat golden)
pio test -e native               17/17
make export   firmware/include/model_int8.h (ECG_WIN_LEN 256, ECG_THRESHOLD 0.8f)
pio run -e esp32-s3              SUCCESS, RAM 21,2% Flash 6,6%
make poc      8/8
pytest        56 passed
```

### Efek berantai yang harus diketahui

- **R tidak lagi mendarat di indeks 94, tapi 132** (`WIN_PRE` + group delay 4).
  Semua dokumen lama yang menyebut 94 merujuk window 90/160.
- `test_preproc.cpp` dulu menghafal 94 di **dua** tempat (batas pencarian puncak
  DAN batas penerimaan `puncak >= 92 && puncak <= 96`). Yang kedua sempat
  terlewat saat diparametrisasi dan bikin test merah dengan pesan yang
  menyesatkan ("6 beat keluar, 0 puncak di R_IDX") — bukan regresi firmware.
  Sekarang keduanya memakai `R_IDX = ECG_WIN_PRE + ECG_GROUP_DELAY`.
- **Jumlah beat DS2 berubah 49.654 → 49.656**: window yang lebih panjang di
  kiri dan lebih pendek di kanan membuang beat tepi yang berbeda.
- `tests/test_config.py` dan `tests/test_dataset.py` menghafal 250 dan 49.654 —
  keduanya diperbarui beserta alasan perubahannya, bukan dihapus.
- **Golden reference sekarang 9 beat** (dulu 8): window baru meloloskan satu
  beat tepi tambahan di potongan record 208.
- Ukuran model **tidak berubah** (6.417 param): Conv1D tidak bergantung panjang
  window, dan GlobalAveragePooling meratakan panjang berapa pun jadi 32 kanal.
  Yang berubah cuma panjang rantai pooling (31 → 32 langkah), dan
  `build_deploy_model` mengambilnya dari `x.shape`, bukan angka tetap.

### Perbandingan sebelum/sesudah, DS2 (49.6 ribu beat, 22 pasien)

| | recall | precision | F1 | AUC | INT8 |
|---|---|---|---|---|---|
| sebelum (window 250, thr 0,35) | 0,6661 | 0,4919 | 0,5659 | 0,8866 | 22,91 KB |
| **sesudah (window 256 + jitter, thr 0,80)** | **0,6996** | **0,6235** | **0,6594** | **0,9334** | 22,94 KB |

Precision +0,13 dengan recall ikut naik — bukan pertukaran, melainkan model yang
memang lebih baik. AUC +0,047 memastikan itu bukan efek threshold.

## H. Verifikasi di board (18 Sep 2026, sesi yang sama)

Board dicolok, `/dev/ttyACM0` (Espressif USB JTAG). Catatan: `pio device list`
TIDAK menampilkannya walau node-nya ada — jangan pakai itu sebagai penentu.

| Uji | Hasil |
|---|---|
| `pio test -e esp32-s3` | **16/16 PASSED** (preprocessing + inferensi, golden window 256) |
| probabilitas device vs PC | cocok; satu beat beda **1 kuantum INT8** (0,0820 vs 0,0859 = 1/256) |
| latensi inferensi | **26,6 ms**/detak (dari 26,0 — window +2,4%) |
| tensor arena | 12.948 B dari 24.576 |
| replay `y` tanpa elektroda | **11 beat / putaran 6,67 dtk**, pola identik, `sampel hilang 0` |
| `pio run` produksi | SUCCESS, RAM 22,7%, Flash 6,6% |

### Bug yang ditemukan DI SINI (bukan di rencana, bukan dari paper)

**Float di dalam ISR.** Kode replay versi pertama — yang ditulis persis seperti
sketsa di `2026-09-16-daya-plan.md` Task 4 Step 3 — mengalikan float di
`on_timer()`. Board panic `Coprocessor exception` (EXCCAUSE 4) di **detik 18,49**
lalu reboot. ESP32 tidak menyimpan register FPU di konteks interrupt.

Kenapa lolos sejauh ini: ter-build bersih, dan **tidak crash seketika** — panic
baru meledak saat task ber-FPU dijadwalkan lagi. Uji 20 detik pertama lolos tipis.

Perbaikan: konversi sekali di `setup()` → `static uint16_t sim_counts[GOLDEN_N]`
(4.800 B, RAM 21,2% → 22,7%), ISR tinggal menyalin integer. Sketsa di daya-plan
sudah dikoreksi beserta peringatannya.

**Dua jebakan pengukuran yang ikut ketemu**, keduanya menghasilkan angka yang
kelihatan benar:
1. Membuka port serial dengan pyserial menegaskan DTR/RTS → **board reset**.
   Toggle `y` yang dikira aktif ternyata tidak, dan yang terukur derau ADC.
   Obat: `s.dtr = s.rts = False` sebelum `open()`, lalu **verifikasi** state dari
   balasan `replay ON` dan dari ayunan sinyal (replay ~2700 counts vs derau ~15).
2. Tanpa elektroda, firmware mengeluarkan **~2 beat/detik dengan 57% "ARITMIA"**.
   Ambang Pan-Tompkins adaptif relatif terhadap sinyal yang ada, jadi "tidak ada
   sinyal" bukan kondisi yang ia kenali. **Konsekuensi untuk HW-6: publikasi MQTT
   wajib digerbangi kualitas sinyal, bukan oleh ada-tidaknya beat.**

## I. Yang masih belum dikerjakan

- Fitur RR versi paper (`ln`, median ±15 beat) belum diuji sama sekali.
- `model_fp32_<tag>.keras` (7 berkas, ~900 KB) belum masuk `.gitignore` dan
  bukan artefak final.
- Tabel di `laporan/` belum disentuh (read-only tanpa konfirmasi).
- Belum ada commit — seluruh pekerjaan hari ini masih di working tree.
