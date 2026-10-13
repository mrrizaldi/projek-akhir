# Riwayat: komentar & docstring kode

**Dokumen sumber:** komentar/docstring di `firmware/`, `model/`, `dashboard/`
(bukan satu berkas .md)
**Isi:** catatan perubahan, koreksi, dan konteks historis yang dikeluarkan dari
komentar kode saat formalisasi dokumentasi (Okt 2026). Perilaku kode tidak
berubah; yang dipindah hanya narasinya.

## Ukuran window 90/160 -> 128/128 (18 Sep 2026)
- **Perubahan:** `WIN_PRE/WIN_POST` dikunci 128/128 (256 sampel), menggantikan
  90/160 (250 sampel). R pindah dari indeks 94 ke 132; rantai pooling dari
  250->125->62->31 menjadi 256->128->64->32 tanpa pemotongan. Varian sementara
  128/127 sempat diuji sebelum 128/128.
- **Alasan / bukti:** ablasi 3 seed, F1 DS2 0,5660 -> 0,6911 (Fase 6c,
  `docs/jitter-walkthrough.md`).
- **Bekas di kode:** `model/config.py` (blok WIN_PRE), `tests/test_config.py`,
  `tests/test_dataset.py` (DS2 49.656 beat, sebelumnya 49.654 di window 250),
  `firmware/test/test_preproc/test_preproc.cpp` (uji posisi R ditulis sebagai
  rumus karena alasan ini). Komentar yang masih menyebut 250/94 di
  `scripts/build_split.py`, `scripts/prep_beats.py`,
  `scripts/eval_detected_segmentation.py`, `src/features_rr.py`,
  `test_inference.cpp`, dan `config.py` (blok PT_DETECTOR_OFFSET) diselaraskan
  ke 256/132.

## Threshold 0,35 -> 0,80 (18 Sep 2026)
- **Perubahan:** `THRESHOLD` naik dari 0,35 ke 0,80 setelah window 128/128 +
  augmentasi jitter.
- **Alasan / bukti:** kriteria kalibrasi tidak berubah; VAL ikut ber-jitter,
  sebaran probabilitas bergeser. Angka lama (val F1 0,8124 @ 0,35) diukur di
  VAL bersih, tidak sebanding dengan angka sekarang.

## Augmentasi jitter di prep_beats (18 Sep 2026)
- **Perubahan:** sejak tanggal itu `make prep` menumpuk DS1 dengan salinan
  ber-jitter. "Data Fase 2 yang asli" = keluaran `--jitter none`.

## Batas ukuran model 20 KB -> 25 KB
- **Perubahan:** DoD PRD semula < 20 KB; dinaikkan ke 25 KB (`MAX_MODEL_KB`).
- **Alasan / bukti:** varian deploy yang benar di TFLM (tanpa MEAN & tanpa
  shape dinamis) memakan 20,8 KB.

## Polaritas lead svdb (gate A2, 19 Sep 2026)
- **Perubahan:** komentar `config.py` masih menulis "POLARITASNYA BELUM
  DIVERIFIKASI". Gate A2 sudah tertutup: ECG1 benar, 8/8 record positif di R
  (`docs/arsip/2026-09-19-multidataset-plan.md` §3b). Komentar diperbarui.

## Tahap 2: percobaan pertama memakai F1 (Fase E)
- **Perubahan:** percobaan pertama kalibrasi ambang nama "V" memaksimalkan F1;
  ambang mendarat di dasar grid, 4.387 dinamai V, cuma 1.664 benar (presisi
  37,9%). Kriteria diganti presisi minimum (`MIN_PRESISI_NAMA = 0,90`).

## Fase A: resample_to_fs semula stub
- **Perubahan:** `resample_to_fs` awalnya stub yang melempar
  `NotImplementedError`; sudah diimplementasikan. Docstring `load_record` dan
  `test_resample_kontrak` tidak lagi menyebut NotImplementedError.
- **Perubahan terkait:** `load_record(db="mitdb")` dijaga berperilaku persis
  seperti sebelum Fase A (44/44 record byte-identik, cek manual 19 Sep 2026).

## MQTT: pembacaan PUBACK versi pertama (19 Sep 2026)
- **Perubahan:** versi pertama `pungut_masuk()` membaca 4 byte begitu
  `available() >= 4` dan menganggapnya PUBACK. PINGRESP yang tidak dibaca
  membuat aliran desync. Diganti pembacaan per header paket.
- **Alasan / bukti:** `PUBACK timeout` acak tiap ~30 detik, p95 latensi
  10,4 detik, maks 19,5 detik.

## MQTT: batch 8 -> 50
- **Perubahan:** `ECG_MQTT_BATCH_N` sempat diturunkan ke 8 karena paket besar
  tidak habis ditulis sekali jalan (paket terpotong tidak pernah di-PUBACK).
  Setelah `kirim_sampai_habis()` menulis bertahap, batas dinaikkan ke 50.

## MQTT: buffer paket dua -> satu
- **Perubahan:** versi dua-buffer (payload + paket) memakan 32 KB RAM internal
  untuk batch 50; diganti satu buffer dengan header ditempel mundur.

## Replay: float di ISR (18 Sep 2026)
- **Perubahan:** versi pertama replay mengalikan float di dalam `on_timer()`;
  board panic "Coprocessor exception" setelah ~18 detik dan sempat lolos uji
  20 detik. Konversi dipindah ke `setup()` (tabel integer `sim_counts[]`).

## LED: pola kedip clipping dicabut
- **Perubahan:** clipping dulu punya pola merah kedip sendiri; dicabut karena
  menumpuk arti di satu warna. Clipping tetap dilaporkan lewat serial.

## Pin LO: INPUT -> INPUT_PULLUP
- **Perubahan:** pin LO mengambang (tanpa pull-up) yang kebetulan terbaca LOW
  pernah melaporkan "elektroda menempel" untuk kabel yang tidak tersambung;
  karena itu dipakai `INPUT_PULLUP`.

## WiFi power save: pengukuran daya
- **Perubahan:** saat `WiFi.setSleep(false)` dipasang, pengukuran daya mode
  WiFi (HW-7) belum dijalankan. Komentar kini hanya menyatakan syaratnya
  (ukur DENGAN setelan ini).

## hwtest: ECG_LIVE_TIAP=90 (11 Okt 2026)
- **Perubahan:** env `hwtest` memakai deteksi tiap 250 ms
  (`-D ECG_LIVE_TIAP=90`); firmware utama tetap bawaan 1 detik.
- **Alasan / bukti:** DS1 Se 0,9867 -> 0,9881, PPV 0,9880 -> 0,9870 (setara);
  burst deteksi 7,2 ms per putaran = 2,9% CPU.

## ukur_pipeline.py: selisih jam
- **Perubahan:** docstring semula menganggap selisih jam board-laptop puluhan ms
  dan hanya dilaporkan. Skrip sekarang mengukur offset dari `epoch_ms` lalu
  mengoreksinya; docstring diselaraskan.
