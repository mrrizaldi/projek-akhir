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
- [x] **Fase 2** — sejak 18 Sep 2026 `make prep` mengaugmentasi DS1 (jitter
  empiris ×2 salinan; DS2 tetap bersih) → **202.560 beat** (Normal 89,7% /
  Aritmia 10,3%, buang 215). Angka di bawah ini dari versi TANPA augmentasi dan
  window 250, disimpan sebagai rujukan sejarah: 44 record, **100.619 beat**, Normal 90.018 (89,5%)
  / Aritmia 10.601 (10,5%), **114 beat dibuang** (2 per record tanpa RR/dRR +
  26 beat tepi). Ekstrem per record: 212 → 0% aritmia, 232 → 77,7%. Rec 100:
  RR_ratio median Normal 1,0003 vs Aritmia 0,7664 (fitur memisah). Alignment
  di-assert mekanis (`labels == (symbols != "N")`). `make test` → 20 passed.
- [x] **Fase 3** — `make split` → **DS1 152.904 beat (10,1% aritmia, 3 salinan)
  / DS2 49.656 (11,0%, bersih)**; `X_morph` (N,256,1). Angka lama (sebelum
  augmentasi + window 256): DS1 50.965 / DS2 49.654; 50.965+49.654 = 100.619 = total Fase 2, nol beat hilang.
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
- [x] **Fase 6 (ANGKA BERLAKU, 18 Sep 2026)** — window 256 + augmentasi jitter,
  threshold 0,80 dari VAL: **TP=3813 FN=1637 FP=2302 TN=41904 → recall 0,6996,
  precision 0,6235, F1 0,6594, specificity 0,9479, AUC 0,9334** (49.656 beat).
  Median recall per pasien 0,9167; terburuk tetap rec 232 (0,3541) dan 213
  (0,2246). INT8: recall 0,7105 F1 0,6604 AUC 0,9344, **22,94 KB**, delta recall
  **+0,0108**. Angka lama (window 250, tanpa augmentasi, threshold 0,35) di
  bawah ini sebagai pembanding sejarah.
- [x] **Fase 6 (lama)** — DS2 dibuka SEKALI di threshold 0,35 (dikalibrasi di val).
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
| 6c | `scripts/ukur_jitter.py`, `sweep_jitter.py`, `ablasi.py` | [`docs/jitter-walkthrough.md`](docs/jitter-walkthrough.md) |
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
- [x] **Fase 6c** (di luar PRD) — ketahanan terhadap error segmentasi, adaptasi
  Dias 2021. Jitter detektor DIUKUR, bukan dipinjam: DS1 50.601 pasangan, median
  0, std 6,07, tapi **inti tajam (80% ≤1 sampel, 90% ≤2) dengan ekor berat**
  (|p95| 18, |p99| 26, maks 54) yang beralamat di record berisik 108/203/207.
  Model Fase 5 di bawah jitter empiris: F1 0,5659 → **0,4534**, tapi AUC cuma
  0,8866 → 0,8586 — yang rusak titik operasi, bukan urutan. **Latih ulang dengan
  jitter (3 seed): F1 DS2 0,5660 → 0,6354; ganti window ke 128/127 → 0,6775,
  AUC 0,9394.** HOS tidak terbukti membayar, ditolak.
  `docs/jitter-walkthrough.md`. **DIKUNCI 18 Sep 2026** atas persetujuan user:
  `WIN_PRE/WIN_POST = 128/128`, `JITTER_MODEL = "empiris"`, `JITTER_SALINAN = 2`,
  `THRESHOLD = 0,80`. Follow-up ikut diuji: 128/128 (256 tepat) ≈ 128/127, dan
  `--salinan 3` lebih buruk dari 2. Rantai penuh dijalankan ulang (prep → split →
  train → kalibrasi → eval → quantize → golden → export); `pio test -e native`
  17/17, `make poc` 8/8, pytest 56.
- [x] **HW-7 Task 4** — sumber sinyal replay (toggle serial `y`), **TERVERIFIKASI
  DI BOARD 18 Sep 2026**. ISR menyalin `sim_counts[]` (golden_raw → counts,
  dikonversi sekali di `setup()`) menggantikan `adc1_get_raw`; jalur hilir nol
  perubahan. Terukur: **11 beat per putaran 6,67 detik (1,58 beat/detik), pola p
  identik tiap putaran, sampel hilang 0, antrean puncak 21/256**, ayun 2720
  counts. Golden punya 9 beat beranotasi — 2 selisihnya artefak sambungan
  putaran (satu keluar `p = 0,500` persis). **Untuk akuntansi MQTT pakai 11**,
  bukan 9: yang dihitung apa yang dikirim alat. RAM 22,7% (+4.800 B tabel).
- [x] **HW-1 (angka diperbarui 18 Sep 2026, window 256)** — `pio test -e esp32-s3`
  **16/16**, probabilitas device cocok PC (satu beat beda 1 kuantum INT8:
  0,0820 vs 0,0859 — 1/256, lolos toleransi). **26,6 ms per detak** (dari 26,0),
  tensor arena 12.948 B, heap bebas 312.396 B. Detail lama di bawah.
- [x] **HW-1 (lama, window 250)** — port preprocessing ke C + inferensi di ESP32-S3 sungguhan.
  `pio test -e native` 7/7, `pio test -e esp32-s3` PASSED — probabilitas device
  **cocok PC digit demi digit** (0,9727 / 0,0039 / 0,9883 / 0,9805 / 0,0117 /
  0,9609). **26,0 ms per detak** (3,3% duty cycle), tensor arena 12.756 B,
  RAM 54.468 B (16,6%), Flash 356.025 B (5,4%). Board id
  `4d_systems_esp32s3_gen4_r8n16`, port `/dev/ttyACM0`.
- [x] **HW-2** — Pan-Tompkins diport ke C (`ecg_detect_r`, `ecg_align_r`).
  Deteksi cocok Python **11/11 puncak** di golden; penyelarasan menaruh R di
  indeks 94 (diuji sebagai sifat, bukan angka). `pio test -e native` 9/9,
  `pio run -e esp32-s3` RAM 6,8% Flash 4,9%. Firmware akuisisi (timer 360 Hz,
  2 tombol, LittleFS, LED kualitas sinyal) sudah jalan; 7 rekaman percobaan
  tersimpan di `data/recordings/`.
- [x] **HW-3** — alur hidup dirangkai (`src/ecg_live.cpp`): sampel masuk satu per
  satu → bandpass streaming → deteksi tiap 1 detik atas ring 4 detik →
  penyelarasan → window + RR → beat keluar. Inferensi di pemanggil, jadi modul
  bisa diuji di native tanpa TFLM. Diuji dgn memutar ulang `golden_raw` (tanpa
  elektroda): **6 beat keluar, 6 cocok anotasi, 6 prediksi BENAR**.
  **Beban rata-rata 82 us/sampel dari anggaran 2778 us = 3,0%**, tapi puncak
  burst **33,4 ms** (deteksi + inferensi bersamaan) → ADC WAJIB diumpankan ISR
  ke antrean min 13 sampel, kalau tidak sampel bolong dan RR rusak.
  `pio test -e native` 11/11, device 5/5.
- [x] **HW-4** — firmware produksi: timer ISR 360 Hz baca `adc1_get_raw` →
  antrean 256 → loop kuras → `ecg_live` → inferensi → LED + serial per detak.
  ADC dibaca DI ISR (bukan loop) supaya jitter burst 33 ms tidak masuk ke RR.
  Terukur di board: **RAM 21,2%, Flash 6,4%, antrean 12 saat burst, sampel
  hilang 0**. REC tetap menyimpan sinyal mentah ke LittleFS untuk analisis
  offline. `pio test -e native` 11/11.
- [ ] **HW-5** — validasi dengan elektroda baru (sinyal tubuh nyata).
  **15 Sep 2026: satu rekaman tubuh BERHASIL** — `20260915-1130.csv`, ayunan
  **3128 counts**, dengung 3,3%, autokorelasi 0,27 @ 87 bpm, 64 R-peak / 47,2 dtk,
  BPM masuk akal 100% (20 sampel clipping di rail atas). Sesudah itu **enam
  rekaman beruntun mati di 40–55 counts** (~38 uV input-referred = lantai derau).
  Dicoret lewat ukur, satu variabel per percobaan: elektroda, jack, kabel LO,
  modul+kabel (RA–LA ribuan ohm; lintasan tubuh diukur di steker = ratusan kOhm),
  penempatan LA. Sisa satu variabel: **header modul AD8232 belum disolder** —
  sambungan tekan yang intermiten cocok dgn pola "kadang 3128, kadang 48".
  Keputusan: **solder dulu, baru ulangi rekam**. Analisis offline jalan terus
  pakai rekaman 11:30 — HW-5 tidak terkunci total.
- [ ] **HW-6** *(opsional, di luar PoC)* — MQTT + ThingsBoard

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
| Ukuran window | **128/128 = 256 sampel** (dari 90/160 = 250), dikunci 18 Sep 2026 | ablasi 3 seed (Fase 6c): F1 DS2 0,5660 → 0,6911. Varian PENENTU justru yang kalah: 112/144 juga 256 sampel, juga kelipatan 8, cakupan T lebih panjang → setara baseline. Jadi yang membayar **konteks 128 sampel sebelum R**, bukan panjang window. R sekarang di indeks **132** (128+4), bukan 94 |
| Augmentasi jitter | **`empiris` × 2 salinan di DS1**, DS2 tidak pernah dijitter | F1 DS2 0,5660 → 0,6354 bahkan pada data BERSIH — jitter bekerja sebagai regularisasi, bukan cuma latihan kondisi deploy. `--salinan 3` lebih buruk (0,6099), jadi 2 |
| Threshold | **0,80** (18 Sep 2026, dari 0,35) | kriteria TIDAK berubah (F1 maksimum, tie-break recall bila ΔF1 < 0,005); yang berubah datanya — VAL sekarang ikut ber-jitter, jadi sebaran probabilitas bergeser dan titik operasi yang benar ikut bergeser. Kandidat {0,80; 0,85} → recall menang → 0,80. Memakai 0,35 di model ini memberi precision 0,19. Angka lama (val F1 0,8124 @ 0,35) diukur di val bersih, tidak sebanding. Reproduksi: `scripts/calibrate_threshold.py` |
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
| Segmentasi on-device | **kompensasi 38 + penyelarasan puncak ±25 + kurangi group delay 4** | tanpa salah satunya R tidak mendarat di `WIN_PRE+4` (94 dulu, **132** sejak window 256) dan precision jatuh 4× (0,479→0,124); offset dikalibrasi di DS1 |
| Model jitter | **empiris** (ambil ulang dari `residu_ds1.npy`), bukan seragam ±18 paper | residu terukur inti-tajam-ekor-berat; seragam ±18 menggeser 80% beat yang sebetulnya terkunci. `seragam` tetap ada supaya sweep δ=0..18 sebanding Tabel 3 Dias 2021 |
| Jitter per beat | **independen**, walau kenyataannya berkorelasi per record | korelasi sebagian saling meniadakan di RR (RR = selisih dua posisi); independen melebihkan ragam RR = arah pesimistis, aman |
| Salinan bersih saat augmentasi | **selalu ikut** (`--salinan N` = N tiruan DI ATAS 1 salinan bersih) | 80% beat di alat meleset ≤1 sampel; kasus "tepat" itu mayoritas, bukan kasus pinggir |
| Knob ablasi | **environment** (`PA_WIN_PRE`, `PA_WIN_POST`, `PA_HOS`), bukan edit nilai final | tanpa env, `config.py` memberi nilai yang persis sama → ablasi tidak menyentuh gate point. Yang menang baru dikunci lewat bawaannya (tetap gate point) |
| Fitur HOS (kurtosis+skewness) | **ditolak** | 3 seed: 0,6150±0,0509 vs 0,6354±0,0428 tanpa HOS — tumpang tindih penuh. Bukan "merusak", tapi "tidak ada bukti menolong"; fitur tanpa bukti tetap harus diport ke C & dijaga. Kode + knob `PA_HOS` ditinggal untuk ablasi ulang |
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
  Hindari: firmware wajib menaruh R di indeks `ECG_WIN_PRE + ECG_GROUP_DELAY`
  (94 saat window 90/160, **132** sejak window 128/128 — jangan hafal angkanya,
  `test_preproc.cpp` memakai rumusnya). **Perbaikan ini SUDAH dikerjakan**
  18 Sep 2026: augmentasi jitter, Fase 6c.
- **Refraktori 200 ms Pan-Tompkins memblokir beat prematur.** Gejala:
  sensitivity detektor kelas S cuma 0,6494 vs Normal 0,9614. Sebab: beat
  supraventrikular datang terlalu cepat setelah detak sebelumnya, tepat di
  jendela refraktori. Efeknya berlipat dengan recall klasifikasi S yang sudah
  0,3034. Trade-off menurunkan refraktori bisa diukur dgn
  `scripts/eval_detected_segmentation.py`.
- **Beban alur hidup bursty, bukan merata.** Gejala: rata-rata cuma 82 us/sampel
  (3% anggaran) tapi satu sampel bisa memakan 33,4 ms — 12x anggaran. Sebab:
  deteksi berjalan sekaligus atas ring 4 detik, dan kebetulan bersamaan dengan
  inferensi beat yang baru ditemukan. Hindari: akuisisi ADC di timer ISR menaruh
  ke antrean (min 13 sampel), pemrosesan menguras di loop utama. Kalau berurutan
  di satu alur, ~12 sampel hilang tiap detik dan interval RR rusak.
- **`.venv` tidak kepakai walau ada.** Gejala: `make plot1` →
  `ModuleNotFoundError: No module named 'numpy'`. Sebab: `PY := python` ambil
  pyenv shim, bukan `.venv/bin/python`. Hindari: `PY` di Makefile sekarang
  auto-pilih `.venv/bin/python` kalau ada (tak perlu `source activate`).
- **Telemetri akuisisi bisa berbohong, dan hari itu tiga sekaligus.** Ketemu
  15 Sep 2026 saat memburu sinyal yang hilang. (1) **`lepas 0%` dari LO AD8232
  BUKAN jaminan ada sinyal** — LO cuma butuh satu jalur impedansi rendah, dan
  elektroda RL sendirian sudah memuaskannya; enam rekaman kosong semuanya
  melapor `lepas 0%`. (2) **Nama file `make pull` = waktu TARIK, bukan waktu
  rekam** (`pull_recording.py:77` pakai `datetime.now()`) — rekaman basi
  terlihat baru kalau lupa menekan REC. (3) **Ohmmeter di rangkaian bertegangan
  memberi angka salah tanpa tanda apa pun** — RA–LA terbaca ~0 Ohm (disimpulkan
  korslet), diulang dengan daya mati jadi ribuan ohm. Hindari: jadikan **ayunan
  ADC absolut** wasitnya, bukan flag. Konversi: 12-bit + atten 11 dB =
  0,757 mV/count, gain AD8232 ~1100 → EKG sehat ~2 mV (~3000 counts);
  **di bawah ~0,1 mV (~150 counts) berarti tidak ada biopotensial sama sekali**,
  dan itu bukan masalah penempatan lead (penempatan buruk memangkas 3–5x,
  bukan 50x).
- **Seed dikunci, hasil tetap berubah.** Gejala: `np.random.seed(42)` +
  `tf.random.set_seed(42)`, kode identik, dijalankan dua kali → F1 DS2 0,6209 vs
  0,5882 (varian jitter). Sebab: penjadwalan thread oneDNN di CPU mengubah urutan
  penjumlahan float; selisih kecil itu memilih epoch berhenti yang berbeda lewat
  EarlyStopping, dan `restore_best_weights` mengembalikan bobot yang lain.
  Hindari: **jangan pernah menyimpulkan ablasi dari satu run.** Minimal 3, lapor
  rerata ± rentang. Di repo ini selisih < ~0,04 F1 bukan sinyal.
- **Melatih dengan data yang "dirusak" menaikkan angka di data BERSIH.** Gejala
  (yang menyenangkan): augmentasi jitter menaikkan F1 DS2 anotasi 0,5660 →
  0,6354, padahal DS2 anotasi tidak punya jitter sama sekali. Sebab: model lama
  bergantung pada fase window yang persis (tiga `MaxPooling1D(2)`, stride 8);
  jitter memaksanya belajar bentuk yang tak bergantung fase — regularisasi, sama
  seperti random crop di penglihatan komputer. Pelajaran: augmentasi yang meniru
  error deploy bukan cuma "menyiapkan kondisi buruk", ia memperbaiki modelnya.
- **Penalaran fisiologis yang masuk akal bisa salah, dan ablasi yang benar
  membuktikannya.** Gejala: argumen "`WIN_PRE=90` sudah memuat gelombang P
  (interval PR 43-72 sampel), jadi 128 milik paper cuma membeli garis dasar"
  terdengar kuat — dan kalah. `w128` (128/127) F1 0,6775 vs 0,5660 baseline.
  Kunci pembuktiannya varian ketiga: `w112` (112/144) punya panjang 256 yang
  SAMA, habis dibagi 8, cakupan T lebih panjang — hasilnya setara baseline. Jadi
  yang membayar bukan panjang window, bukan kelipatan 8, tapi **konteks pre-R**.
  Hindari: setiap klaim "X sudah cukup" butuh varian pembanding yang mengisolasi
  X, bukan sekadar varian yang lebih besar.
- **Float di dalam ISR membunuh ESP32 — pelan-pelan, bukan seketika.** Gejala:
  `Guru Meditation Error: Core 1 panic'ed (Coprocessor exception)`, `EXCCAUSE
  0x00000004`, lalu reboot. Muncul di **detik 18**, bukan detik 0, jadi lolos
  uji 20 detik dan lolos build. Sebab: ESP32 tidak menyimpan register FPU saat
  masuk ISR; operasi float di sana merusak state FPU task yang diinterupsi, dan
  panic baru meledak saat task itu dijadwalkan lagi. Hindari: konversi di
  `setup()` ke tabel integer, ISR cuma menyalin (`sim_counts[]` di `main.cpp`).
  **Gejala turunannya lebih menipu dari crash-nya**: board reboot diam-diam →
  `replay` kembali `false` → pengukuran berikutnya melaporkan angka yang masuk
  akal (2 beat/detik) tapi dari objek yang salah (derau ADC, bukan replay).
- **Membuka port serial me-reset board, dan itu merusak pengukuran.** Gejala:
  pencacah beat di board tidak cocok dengan jumlah baris yang diterima; toggle
  `y` yang "sudah ditekan" ternyata tidak aktif. Sebab: pyserial menegaskan
  DTR/RTS saat `Serial()` dibuka → ESP32-S3 reset. Hindari: `s.dtr = s.rts =
  False` SEBELUM `s.open()`, lalu **verifikasi state** dari balasan board
  (`replay ON`) dan dari ayunan sinyal di `s` (replay ~2700 counts vs derau ~15),
  jangan diasumsikan.
- **Tanpa elektroda, alat mengarang aritmia: ~2 beat/detik, 57% "ARITMIA".**
  Sebab: ambang Pan-Tompkins adaptif relatif terhadap sinyal yang ada, jadi
  "tidak ada sinyal" bukan kondisi yang ia kenali — derau 15 counts pun punya
  puncak. Konsekuensi untuk HW-6: **publikasi MQTT wajib digerbangi penilai
  kualitas sinyal (`AMBANG_AYUN`), bukan oleh ada-tidaknya beat.** Kalau tidak,
  elektroda lepas = banjir alarm palsu ke broker.
- **`import config` gagal dari `scripts/`.** Gejala: `ModuleNotFoundError` walau
  dijalankan dari `model/`. Sebab: `python scripts/x.py` menaruh `scripts/` di
  `sys.path[0]`, bukan cwd. Hindari: shim 1 baris `sys.path.insert` (lihat
  `scripts/plot_fase0.py`); `conftest.py` sudah menangani sisi pytest.

## Kanal knowledge

Sesi Claude Code di folder ini **tidak** mewarisi riwayat sesi lain (riwayat
tersimpan per direktori kerja). File ini satu-satunya yang selalu termuat —
tulis keputusan ke sini, bukan cuma ke chat.
