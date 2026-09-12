# CLAUDE.md — model/ (jalur TinyML)

Spesifikasi lengkap: `PRD_Model_Aritmia_TinyML.pdf` (19 hal, Fase 0–8).
Baca fase terkait sebelum menyentuh file apa pun. Jangan vibe-coding.
Desain workflow: `docs/2026-08-18-workflow-model-design.md`.

## Aturan

1. **USER yang menulis logika algoritma.** Claude: scaffolding, review, debug,
   docs, build glue. Jangan isi `src/*.py` kecuali diminta eksplisit.
2. **`src/` = modul MURNI** (fungsi in→out, tanpa kode top-level, import-safe).
   **`scripts/` = eksekusi** (cetak, plot, tulis file). Jangan campur.
3. **Semua konstanta di `config.py`.** Jangan hardcode angka di `src/`.
4. **DS2 haram disentuh sebelum Fase 6.** Bukan validation, bukan tuning
   threshold. Sekali sentuh di Fase 6–7, itu saja.
5. **`sosfilt`, BUKAN `filtfilt`** (kausal — JEBAKAN #1 PRD). `filtfilt` mustahil
   real-time di MCU → train/deploy mismatch.
6. **Segmentasi training pakai R-peak dari ANOTASI**, bukan Pan-Tompkins
   (keputusan terkunci, PRD Fase 2).
7. **Tiap fase selesai → tulis walkthrough.** Satu file per modul di `docs/`,
   pola nama `<modul>-walkthrough.md`. Lihat "Walkthrough per fase" di bawah.
8. **Penjelasan tinggal di `docs/`, bukan di `src/`.** File `src/` ditulis
   sependek mungkin (nyaris tanpa komentar) supaya terbaca sebagai persamaan
   dan gampang diterjemahkan ke C. Kalau butuh menjelaskan "kenapa", tempatnya
   walkthrough — bukan docstring 40 baris.

## Perintah

```
make data      # download MIT-BIH (sekali)      make train     # Fase 5
make check     # cek kelengkapan dataset        make eval      # Fase 6
make plot0     # verifikasi Fase 0 (R-peak)     make quantize  # Fase 7
make plot1     # verifikasi Fase 1a (filter)    make export    # .h ke firmware
make plot1seg  # verifikasi Fase 1b (segmentasi)
make prep      # Fase 2 → per_record/*.npz      make test      # pytest
make split     # Fase 3 → train/test.npz         make poc       # Fase 8 checklist
```

## Status fase

Maksimal ~5 baris per fase: angka DoD, keputusan di-lock, jebakan ketemu.
Naratif panjang → langsung ke Bab 4 laporan, jangan di sini.

- [x] **Fase 0** — 48 record lengkap. Rec 100 → 650.000 sampel, 2.273 beat,
  `fs == 360`, simbol tersisa `{A, N, V}`. Rec 114 (MLII index 1): garis mendarat
  pas di puncak R (`make plot0 REC=114`) + di-assert mekanis vs `p_signal[:, 1]`.
  Rec 102/104 (tanpa MLII) ditolak `ValueError`. `make test` → 9 passed.
- [x] **Fase 1** — bandpass 0.5–40 Hz orde 4 kausal (`sosfilt`). Rec 100: mean
  −0,3063 → +0,0000, std 0,1932 → 0,1840 (turun ~5% saja = filter pembersih,
  bukan pemangkas morfologi); rec 114 std 0,3755 → 0,3480. Segmentasi rec 100:
  2.273 anotasi → 2.271 window (2 dibuang, beat tepi), semua == `WIN_LEN` 250.
  **Group delay +4 sampel (+11,2 ms)** — puncak R di indeks ~94, bukan 90.
  Verifikasi: `make plot1 REC=n` (filter) + `make plot1seg REC=n` (segmentasi).
- [x] **Fase 2** — `make prep` → 44 record, **100.619 beat**, Normal 90.018 (89,5%)
  / Aritmia 10.601 (10,5%), **114 beat dibuang** (2 per record tanpa RR/dRR +
  26 beat tepi). Ekstrem per record: 212 → 0% aritmia, 232 → 77,7%. Rec 100:
  RR_ratio median Normal 1,0003 vs Aritmia 0,7664 (fitur memisah). Alignment
  di-assert mekanis (`labels == (symbols != "N")`). `make test` → 20 passed.
- [x] **Fase 3** — `make split` → DS1 50.965 beat (10,1% aritmia) / DS2 49.654
  beat (11,0%); 50.965+49.654 = 100.619 = total Fase 2, nol beat hilang.
  `X_morph` (N,250,1) siap Conv1D, kolom `records` disimpan untuk metrik
  per-pasien Fase 6. Kebocoran lintas pasien di-`raise` mekanis. Sebaran ekstrem:
  DS1 208 → 46,3%, DS2 232 → 77,7% vs 212 → 0,0%. `make test` → 24 passed.
- [x] **Fase 4** — Functional API dua input → **6.417 param** (128+2.592+3.104+
  576+17), float32 25,07 KB. Bentuk: 250→125→62→31 lalu GAP→32, concat RR→35.
  **Tanpa dropout** (rasio 50.965 sampel : 6.417 param ≈ 8, lebih rawan
  underfit); `build_hybrid_model(dropout_rate=0.3)` siap kalau kurva Fase 5
  bicara lain. `make test` → 28 passed.
- [x] **Fase 5** — `make train` → `artifacts/model_fp32.keras`. class_weight
  Normal 0,556 / Aritmia 4,947. EarlyStopping(`val_auc`) berhenti epoch 12,
  bobot dikembalikan ke epoch 4. **VAL @0,5: TP=728 FN=318 FP=67 TN=9235 →
  recall 0,696, precision 0,916, specificity 0,993.** Overfit nyata (val AUC
  puncak epoch 4 lalu turun) tapi dropout TIDAK menolong (lihat tabel di bawah).
  Recall masih kurang → knob threshold, urusan Fase 6. `make test` → 34 passed.
- [x] **Fase 6** — DS2 dibuka SEKALI di threshold 0,35 (dikalibrasi di val).
  49.654 beat / 22 pasien: **TP=3630 FN=1820 FP=3750 TN=40454 → recall 0,6661,
  precision 0,4919, F1 0,5659, specificity 0,9152, AUC 0,8866** (accuracy 0,8878
  — LEBIH RENDAH dari tebak-Normal 0,8903, jangan dipakai). Per kelas AAMI:
  **V 0,9332 / S 0,3034 / F 0,1675**. Median recall per pasien 0,8933 tapi rec 232
  (1.381 aritmia S, 25% total DS2) cuma 0,2042 → menyeret agregat beat-level.
  `make test` → 42 passed.
- [x] **Fase 7** — PTQ INT8 full end-to-end (int8 in/out, 0 tensor float32).
  **22,91 KB < 25 KB** (batas dinaikkan dari 20, lihat decision point). Yang
  dikuantisasi adalah **varian deploy** (`build_deploy_model`), bukan model latih
  — TFLM salah hitung op `MEAN`. Kalibrasi 300 sampel DS1 stratified, seed
  dikunci. **Delta DS2 @0,35: recall −0,0112, AUC −0,0004, precision +0,0383**.
  `make test` → 49 passed.
- [x] **Fase 8** — `make poc` → **8/8 item DoD terverifikasi mekanis**
  (`scripts/check_poc.py`, exit code != 0 kalau ada yang gagal — bukan centang
  manual). `make export` → `firmware/include/model_int8.h` 110,7 KB (array C
  18.264 byte + scale/zero_point tiap tensor + `ECG_THRESHOLD`). Langkah figure
  → `laporan/` sengaja opt-in (`--laporan`), default DILEWATI karena `laporan/`
  read-only tanpa konfirmasi.

## Walkthrough per fase

Dokumen belajar, bukan spesifikasi (spesifikasi = PRD). Isinya: alur kode
langkah demi langkah, matematika di baliknya, alasan tiap keputusan, angka
nyata dari record 100, dan soal cek pemahaman.

**Tulis begitu fase ditandai `[x]`, jangan tunda** — alasan yang tidak dicatat
saat masih hangat akan hilang, dan Bab 4 laporan mengambil bahannya dari sini.

Peta masuk + urutan baca: [`docs/README.md`](docs/README.md).

| Fase | Modul | Dokumen |
|---|---|---|
| 0 | `src/io_mitdb.py` | [`docs/io-mitdb-walkthrough.md`](docs/io-mitdb-walkthrough.md) |
| 1 | `src/preprocessing.py` | [`docs/preprocessing-walkthrough.md`](docs/preprocessing-walkthrough.md) |
| 2 | `src/features_rr.py` | [`docs/features-rr-walkthrough.md`](docs/features-rr-walkthrough.md) |
| 2 | `scripts/prep_beats.py` (eksekusi) | [`docs/prep-beats-walkthrough.md`](docs/prep-beats-walkthrough.md) |
| 3 | `src/dataset.py` | [`docs/dataset-walkthrough.md`](docs/dataset-walkthrough.md) |
| 4 | `src/model.py` | [`docs/model-walkthrough.md`](docs/model-walkthrough.md) |
| 5 | `src/train.py` | [`docs/train-walkthrough.md`](docs/train-walkthrough.md) |
| 6 | `src/evaluate.py` | [`docs/evaluate-walkthrough.md`](docs/evaluate-walkthrough.md) |
| 6b | `scripts/eval_detected_segmentation.py` | [`docs/segmentasi-deteksi-walkthrough.md`](docs/segmentasi-deteksi-walkthrough.md) |
| 7 | `src/quantize.py` | [`docs/quantize-walkthrough.md`](docs/quantize-walkthrough.md) |
| HW | `firmware/src/ecg_pipeline.cpp` | [`docs/firmware-walkthrough.md`](docs/firmware-walkthrough.md) |

Kerangka yang dipakai (ikuti, jangan bikin format baru tiap fase):
peta besar (diagram alur) → fungsi per fungsi dengan kode + rumus → keputusan
yang diambil beserta alternatif yang ditolak → yang sengaja TIDAK dilakukan →
angka nyata → cek pemahaman → skrip pendukung.

- [x] **Fase 6b** (di luar PRD) — biaya segmentasi on-device diukur. Offset
  detektor dikalibrasi di DS1 (median **38 sampel**, std 13). Dengan koreksi
  lengkap (kompensasi + penyelarasan puncak + kembalikan group delay 4 →
  R di indeks **94**): klasifikasi **recall 0,6821 precision 0,4794 F1 0,5631**
  ≈ Fase 6 (0,6661/0,4919/0,5659) — segmentasi TIDAK merusak klasifikasi.
  **Recall sistem 0,5656** (turun 10 poin, semuanya dari beat tak terdeteksi).
  Sensitivity detektor **Normal 0,9614 vs Aritmia 0,8296; kelas S cuma 0,6494**.
  DS2 dilihat kedua kalinya di sini — murni mengukur, nol parameter diambil.
- [x] **HW-1** — port preprocessing ke C + inferensi di ESP32-S3 sungguhan.
  `pio test -e native` 7/7, `pio test -e esp32-s3` PASSED — probabilitas device
  **cocok PC digit demi digit** (0,9727 / 0,0039 / 0,9883 / 0,9805 / 0,0117 /
  0,9609). **26,0 ms per detak** (3,3% duty cycle), tensor arena 12.756 B,
  RAM 54.468 B (16,6%), Flash 356.025 B (5,4%). Board id
  `4d_systems_esp32s3_gen4_r8n16`, port `/dev/ttyACM0`.
- [ ] **HW-2** — akuisisi AD8232 + MQTT + ring buffer PSRAM

## Decision point yang sudah di-lock

Tabel ini = LAMPIRAN B PRD versi hidup. Isi begitu ketok palu, jangan tunda.

| Keputusan | Nilai | Alasan singkat |
|---|---|---|
| Klasifikasi | biner (Normal/Aritmia) | inter-patient bikin F & Q recall ~0 |
| Split | inter-patient de Chazal | intra-patient = akurasi palsu |
| Filter | kausal `sosfilt` | `filtfilt` mustahil di MCU |
| Segmentasi | R-peak anotasi | jaga jalur model murni dari error detektor |
| Normalisasi | z-score per window | kebal beda amplitudo, nol kebocoran statistik |
| Pooling | GlobalAveragePooling1D | param jauh lebih kecil dari Flatten |
| Threshold | **0,35** (dari 0,5) | dikalibrasi di VAL sebelum DS2 dibuka. Kriteria ditulis DULU: F1 maksimum, tie-break ke recall bila ΔF1 < 0,005 → 0,35 (F1 0,8124) menang atas 0,40 (0,8137) karena recall +3,9 poin. Reproduksi: `scripts/calibrate_threshold.py` |
| Agregasi metrik Fase 6 | **level beat** (per-record disimpan terpisah) | standar & sebanding literatur (PRD); `fase6_per_record_fp32.csv` untuk cerita sebarannya |
| `sklearn.metrics` | **tidak dipakai** — numpy | rumus TP/FN/FP/TN + AUC Mann-Whitney beberapa baris; sekalian memaksa memutuskan pembagian-nol → 0,0 bukan NaN (NaN akan merusak tabel delta Fase 7) |
| Orde Butterworth | **4** (2 biquad) | roll-off tajam; std cuma turun 5% = morfologi utuh |
| Beat tanpa `dRR` | **buang** (beat 0 & 1 tiap record) | `dRR=0` nilai SAH (ritme stabil) — sentinel bentrok data asli; biaya 88 dari ~100k beat |
| Alignment window↔label | **`prep_beats` yang menyaring** (opsi C) | semua kebijakan buang-beat di satu file; `src/` tetap murni utk port ke C |
| Jendela `RR_local_avg` | **kausal, menyusut di tepi** (10 RR terakhir, termasuk RR_prev beat ini) | simetris butuh beat masa depan → firmware harus tunda 5 beat; kausal konsisten dgn `sosfilt` Fase 1 |
| Sentinel beat tepi di `features_rr` | **NaN**, bukan 0 | senada baris `dRR`; `prep_beats` buang lewat indeks, sentinel tak pernah sampai model |
| Simbol di luar `AAMI_MAP` | **`KeyError`** (tidak di-default ke Q) | whitelist `BEAT_SYMBOLS` sudah saring di hulu; simbol asing = bocor, harus berisik |
| Record dibuang | `PACED_EXCLUDED` di `config.py` | 102/104 teknis (tanpa MLII), 107/217 metodologis (paced) |
| Strategi imbalance | **`class_weight` balanced**, dihitung sendiri: `w_c = N/(2·n_c)` → Normal 0,556 / Aritmia 4,947 | tidak menyentuh data & tidak menggandakan beat pasien yang sama (oversampling = model hafal individu, lawan semangat inter-patient); PRD melarang dipakai bareng oversampling |
| `pyserial` | **dipakai** (disetujui) — di `requirements.txt` | menarik rekaman dari board lewat serial; tidak ada padanan stdlib, dan semua alat jadi satu venv |
| `sklearn` untuk class weight | **tidak dipakai** — 3 baris numpy | rumus `balanced` cuma `N/(2·n_c)`; gate point CLAUDE.md: jangan tambah dependency (apalagi sebesar sklearn) untuk yang beberapa baris sudah selesai |
| Monitor EarlyStopping | **`val_auc`** (mode max, patience 8, `restore_best_weights`) | `val_recall` bisa dicurangi (tebak Aritmia semua → recall 1,0); `val_loss` sudah terdistorsi `class_weight` jadi tak lagi bisa ditafsir; AUC bebas threshold & tak bisa dipalsukan satu kelas |
| Metrik yang dipantau | **recall, precision, AUC** — accuracy TIDAK | accuracy 89,9% bisa dicapai dengan menebak Normal terus; menampilkannya cuma mengundang salah baca |
| Learning rate | **default adam (1e-3)**, tidak disetel | knob yang belum terbukti perlu = ruang tuning yang harus dipertanggungjawabkan di sidang |
| Dropout Dense 16 | **0.0 (tanpa dropout)** — DIUJI ULANG, tetap 0.0 | val recall: 0.0→**0,700**, 0.2→0,274, 0.3→0,359, 0.5→0,651 (AUC nyaris sama semua). Dropout cuma bikin model makin konservatif — precision naik, recall turun, padahal recall yang kurang. Overfit di sini akar masalahnya variasi antar-pasien, bukan model kegedean |
| Tipe I/O INT8 | **int8 in / int8 out** (`INT8_IO=True`) | full-INT8 end-to-end: nol kernel float, tensor arena terkecil. Firmware yang mengubah float↔int8 pakai scale/zero_point dari `model_int8.h` (jangan hardcode) |
| Sampel kalibrasi PTQ | **300, stratified dari DS1**, seed dikunci | PRD 100-500; 300 → 30 beat Aritmia, cukup mencakup ekor distribusi, konversi tetap detikan. Stratified supaya JEBAKAN #4 (kelas minoritas tak terkalibrasi) mustahil terjadi |
| QAT | **tidak dipakai** | PTQ sudah lolos target (delta recall 1,21% < 2%, 17,84 KB); QAT = latih ulang + sumber variasi baru untuk keuntungan yang belum tentu ada |
| Validation set | **DS1 record 101, 114, 201, 220, 223** (`VAL_RECORDS`; 10.348 beat = 20,3% DS1, aritmia 10,11% ≈ rasio DS1, S=310 V=714) | val jadi simulasi jujur "pasien baru" → angkanya layak dipakai pilih epoch & kalibrasi threshold; DS2 tetap haram sampai Fase 6 |
| Rec 208 wajib di train | **ya** — jangan pernah masuk val/exclude | 372 dari 414 beat kelas F di DS1 ada di record ini; tanpa dia kelas F nyaris hilang dari training |
| Model yang dikuantisasi | **varian deploy** (`build_deploy_model`), bukan model latih | TFLM menghitung op `MEAN` beda dari TFLite: PC 0,973 vs device 0,336, tanpa error. Bobot disalin apa adanya (identik 1,19e-07), nol latih ulang |
| Pengganti GlobalAveragePooling | **`DepthwiseConv1D(31)` bobot 1/31**, bukan `AveragePooling1D` | op pooling MEWARISI skala kuantisasi input (0,332); rata-rata 31 nilai jauh lebih kecil → ~3 bit resolusi hilang, recall DS2 0,655→0,528. Op konvolusi dapat skala output sendiri (0,0429, sama dgn `MEAN`) |
| `Flatten`/`Reshape` di model deploy | **dihindari** — kepala klasifikasi tetap 3-D, `Dense`→`Conv1D` kernel 1 | keduanya memunculkan `SHAPE`/`PACK`/`STRIDED_SLICE` (shape dinamis); TFLM tak punya alokasi dinamis → device memberi 0,418 vs 0,945 |
| Batas ukuran model | **25 KB** (dari 20 KB) | varian deploy yang benar memakan 22,91 KB; flash ESP32-S3 16 MB, batas ini soal disiplin bukan kapasitas. Disetujui eksplisit |
| Library TFLM | **`spaziochirale/Chirale_TensorFLowLite`** 2.0.0 | rilis terbaru di registry PlatformIO, jalan dgn framework Arduino. Kernel referensi (belum ESP-NN) → 26 ms/detak jadi baseline; pindah `esp-tflite-micro` kalau daya jadi kendala |
| Board PlatformIO | **`4d_systems_esp32s3_gen4_r8n16`** | bukan tebakan — id dari projek uji yang sudah pernah ter-flash & jalan di hardware ini (Jul 2026) |
| Segmentasi on-device | **kompensasi 38 + penyelarasan puncak ±25 + kurangi group delay 4** | tanpa salah satunya R tidak mendarat di indeks 94 dan precision jatuh 4× (0,479→0,124); offset dikalibrasi di DS1 |
| Record kanal anomali | 114 (MLII idx 1); 102 & 104 tanpa MLII → `raise` | 102/104 paced, dibuang di Fase 3 juga |
| Filter non-beat | whitelist `BEAT_SYMBOLS` di `config.py` | simbol tak dikenal ikut kebuang, bukan lolos |

## Jebakan yang sudah ketemu

- **`wfdb.io.annotation.is_qrs` tidak bisa dipakai buat filter non-beat.**
  Gejala: `[`, `]`, `x`, `)` lolos sebagai "beat". Sebab: tabel wfdb menandai
  penanda awal/akhir ventricular flutter & non-conducted P-wave sebagai QRS.
  Hindari: whitelist eksplisit `config.BEAT_SYMBOLS` (15 simbol AAMI).
- **Menyamakan PANJANG array ≠ menyejajarkan beat.** Gejala: tidak ada.
  `assert len(windows)==len(labels)` LOLOS, loss turun mulus, baru ketahuan di
  Fase 6 saat recall ~0. Sebab: `segment_beats` buang beat tepi (rec 100: beat
  0 & 2272), `compute_rr_features` buang beat tanpa RR_prev (beat 0) — himpunan
  beda, panjang bisa kebetulan sama. Rec 100 disimulasikan: 100% baris tergeser
  1 beat, 68 label salah simbol padahal aritmia asli cuma 34 (tiap 1 aritmia
  merusak 2 baris). Hindari: `prep_beats` hitung `valid_beat_indices` DULU,
  semua array diambil dari indeks yang sama. RR dihitung dari `r` UTUH baru
  di-slice — potong `r` duluan bikin beat tepi kehilangan tetangga.
- **Group delay filter kausal menggeser R-peak +4 sampel.** Gejala: garis
  R-peak anotasi meleset ~11 ms di kiri puncak pada window HASIL FILTER
  (`make plot1seg`). Sebab: `sosfilt` cuma lihat masa lalu → output tertinggal.
  **Bukan bug, jangan dikoreksi.** Geserannya konsisten (median 94, mean 94,03),
  jadi model belajar posisi itu dan firmware menghasilkan hal sama selama
  koefisien SOS identik. Mengoreksi di Python tanpa koreksi di C = mismatch.
- **TFLite Micro menghitung op `MEAN` beda dari TFLite biasa.** Gejala: model,
  bobot, input, dan parameter kuantisasi identik, tapi PC 0,9727 vs device
  0,3359 — semua probabilitas tertekan ke tengah, **tanpa error apa pun**.
  Sebab: `GlobalAveragePooling1D` → op `MEAN`; dua library TFLM berbeda memberi
  angka salah yang IDENTIK, jadi ini sifat TFLM, bukan bug library. Hindari:
  `build_deploy_model` menukar ke `DepthwiseConv1D` berbobot 1/31 (rata-rata yang
  sama, op konvolusi). Ketahuan cuma karena ada golden reference PC↔device.
- **Op pooling mewarisi skala kuantisasi input; op konvolusi punya skala sendiri.**
  Gejala: `AveragePooling1D` cocok di 6 beat uji golden, tapi recall DS2 jatuh
  0,655 → 0,528. Sebab: skala input 0,332 dipakai juga untuk output, padahal
  rata-rata 31 nilai jauh lebih kecil → ~3 bit resolusi terbuang. Hindari: pakai
  op konvolusi untuk rata-rata. Pelajaran umum: **cocok di segelintir sampel uji
  ≠ benar**; verifikasi ukuran-penuh tetap perlu.
- **Serial monitor merebut `/dev/ttyACM0`.** Gejala: `esptool` gagal dengan
  `Errno 11: Could not exclusively lock port` — pesannya tidak pernah menyebut
  "monitor". Sebab: tombol *Upload and Monitor* VS Code masih hidup. Hindari:
  `lsof /dev/ttyACM0` untuk menemukan PID-nya.
- **Model runtuh kalau R-peak meleset 4 sampel (11 ms).** Gejala: precision
  0,479 → 0,124, simetris ke dua arah (R di indeks 90 atau 98, bukan 94).
  Sebab: tiga `MaxPooling1D(2)` = stride total 8, jadi geseran 4 sampel itu
  SETENGAH bin pooling — fase representasi yang masuk GAP berubah. Model tak
  pernah melihat variasi ini karena training memakai anotasi yang presisi.
  Hindari: firmware wajib menaruh R di indeks 94 (lihat decision point).
  Perbaikan jangka panjang: latih ulang dengan augmentasi geseran ±4 sampel.
- **Refraktori 200 ms Pan-Tompkins memblokir beat prematur.** Gejala:
  sensitivity detektor kelas S cuma 0,6494 vs Normal 0,9614. Sebab: beat
  supraventrikular datang terlalu cepat setelah detak sebelumnya, tepat di
  jendela refraktori. Efeknya berlipat dengan recall klasifikasi S yang sudah
  0,3034. Trade-off menurunkan refraktori bisa diukur dgn
  `scripts/eval_detected_segmentation.py`.
- **`.venv` tidak kepakai walau ada.** Gejala: `make plot1` →
  `ModuleNotFoundError: No module named 'numpy'`. Sebab: `PY := python` ambil
  pyenv shim, bukan `.venv/bin/python`. Hindari: `PY` di Makefile sekarang
  auto-pilih `.venv/bin/python` kalau ada (tak perlu `source activate`).
- **`import config` gagal dari `scripts/`.** Gejala: `ModuleNotFoundError` walau
  dijalankan dari `model/`. Sebab: `python scripts/x.py` menaruh `scripts/` di
  `sys.path[0]`, bukan cwd. Hindari: shim 1 baris `sys.path.insert` (lihat
  `scripts/plot_fase0.py`); `conftest.py` sudah menangani sisi pytest.

## Kanal knowledge

Sesi Claude Code di folder ini **tidak** mewarisi riwayat sesi lain (riwayat
tersimpan per direktori kerja). File ini satu-satunya yang selalu termuat —
tulis keputusan ke sini, bukan cuma ke chat.
