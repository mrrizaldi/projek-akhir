# Riwayat: CLAUDE.md — model/ (status fase & decision point)

**Dokumen sumber:** [`CLAUDE.md`](../../CLAUDE.md)
**Isi:** log status per fase (Fase 0–8, 6b, 6c, HW-1 s.d. HW-7) dan konteks historis
tabel decision point yang dikeluarkan dari dokumen sumber saat formalisasi
dokumentasi (Okt 2026). Isi disalin utuh, termasuk
angka dari konfigurasi lama (window 250, threshold 0,35) sebagai rujukan sejarah.
Dokumen sumber kini hanya memuat tabel status ringkas kondisi saat ini.

## Status fase Fase 0–8 (log asli)
- **Perubahan:** bagian "Status fase" dipindah utuh dari `model/CLAUDE.md`.
- **Alasan / bukti:** dokumen aktif hanya memuat kondisi saat ini; log per fase,
  angka lama, dan tanggal perubahan disimpan di sini.

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

## Status fase di luar PRD: 6b, 6c, HW-1 s.d. HW-7 (log asli)
- **Perubahan:** entri status yang semula terselip di bagian "Walkthrough per fase"
  `model/CLAUDE.md` dipindah utuh ke sini.
- **Alasan / bukti:** sama dengan di atas; bagian walkthrough di dokumen sumber kini
  hanya merujuk ke [`docs/README.md`](../README.md).

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
- [x] **HW-6 — MQTT + ThingsBoard, TERVERIFIKASI DI BOARD 19 Sep 2026.**
  Klien MQTT 4 paket di atas `WiFiClient`, tanpa library. **Dua gerbang sesuai
  bab3.tex §Pengujian Pipeline:** fase `calibrating` (stabilisasi 10 menit + RR
  300–1500 ms & |dRR| ≤ 200 ms tenang 30 dtk, **CNN tidak jalan**) lalu gerbang
  ayunan per detak. Kriteria RR itu gerbang MASUK saja — menegakkannya terus akan
  membungkam aritmia. Beat karangan tanpa elektroda gagal di dua gerbang sekaligus
  (ayun 27 < 60 DAN RR 0,208 s < 0,300 s). Replay = record 208 yang aritmik, jadi
  tidak bisa lulus gerbang RR: toggle `y`/`k` melewatinya dengan pengumuman.
  Backlog **27.000 beat di PSRAM** (1.054 KB, 40 B/entri ≈ 4–7 jam, target bab3),
  batch 50, `ts` = waktu kejadian dari `r_abs` + `gettimeofday`. **6 dari 6 target
  Tabel Rencana Pengukuran terukur, 2 ulangan:** PDSR **100% / 99,2%** (≥95 ✅),
  latensi median **939 / 1.108 ms** (≤2000 ✅), p95 **1.404 / 3.304 ms**
  (⚠️ tidak stabil), `hilang 0` ✅, flush ~24 dtk ✅, 0 ts duplikat ✅.
  Latensi dipecah: **sisi alat 869 ms** = 89%, kadens deteksi 1 dtk + 356 ms
  post-window (arsitektural); jaringan+cloud cuma ~130 ms. Ekor p95 = **retransmisi
  TCP** (RTO 1-2-4 dtk) karena kontensi WiFi, bukan broker — broker diukur 1,1 ms
  median dari laptop. Porsi paket lambat turun 11,1% → 1–9% lewat `setNoDelay` +
  `WiFi.setSleep(false)`; sisanya berayun per kanal, **tidak dikejar**. `pio test
  -e native` **23/23**, `esp32-s3` **16/16**, RAM **36,9%** Flash **13,5%**.
  Sisa: daya mode WiFi (ambil DENGAN `setSleep(false)`), gerbang penuh dgn sinyal
  tubuh (HW-5). `docs/mqtt-walkthrough.md`

## Decision point & jebakan: konteks historis
- **Perubahan:** penanda tanggal dan nilai lama dikeluarkan dari tabel "Decision point
  yang sudah di-lock" dan bagian "Jebakan" di `model/CLAUDE.md`; dokumen sumber kini
  hanya menyatakan nilai yang berlaku.
- **Alasan / bukti:** konteks di bawah disalin dari versi sebelum formalisasi.

- **Ukuran window:** 128/128 = 256 sampel dikunci 18 Sep 2026, menggantikan 90/160 =
  250. R pindah dari indeks 94 ke 132.
- **Threshold:** 0,80 dikunci 18 Sep 2026, menggantikan 0,35. Kriteria kalibrasi tidak
  berubah; yang berubah datanya (VAL ikut ber-jitter). Angka lama val F1 0,8124 @ 0,35
  diukur di val bersih, tidak sebanding dengan angka sekarang.
- **Learning rate:** diuji 19 Sep 2026 (Fase G), tetap 1e-3. Alasan awal mempertahankan
  default ("knob yang belum terbukti perlu") gugur karena kurva `val_auc` memuncak di
  epoch 0. Ongkos pindah dinilai terlalu besar karena jatuh tepat saat HW-5 buntu.
- **Dropout:** diuji ulang sesudah Fase 5, tetap 0.0.
- **QAT:** alasan semula mengutip PTQ dari model lama (delta recall 1,21%, 17,84 KB).
  Angka model berlaku: delta recall +1,08%, 22,94 KB.
- **Batas ukuran model:** dinaikkan dari 20 KB ke 25 KB saat varian deploy memakan
  22,91 KB (window 250). Model berlaku 22,94 KB.
- **Board PlatformIO:** id board diambil dari projek uji yang ter-flash Jul 2026.
- **Jebakan "Model runtuh kalau R-peak meleset 4 sampel":** perbaikan (augmentasi
  jitter, Fase 6c) dikerjakan 18 Sep 2026.
- **Jebakan "Telemetri akuisisi bisa berbohong":** ketiga kasus ditemukan 15 Sep 2026
  saat memburu sinyal yang hilang.
- **Jebakan "`time()` beresolusi 1 detik":** galat jam sempat menghasilkan kesimpulan
  "sisa ~1 detik milik broker" yang sudah ditulis dan di-commit; pengukuran langsung
  (`dashboard/probe_rtt.py`) membantahnya (RTT broker 1,1 ms median).
