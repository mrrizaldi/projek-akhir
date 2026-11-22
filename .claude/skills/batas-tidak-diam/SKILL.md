---
name: batas-tidak-diam
description: Lapisan repo PA untuk firmware yang punya batas atau operasi lambat di loop(). Pakai setiap kali menulis, menyunting, atau meninjau firmware/src (recorder.cpp, acquisition.cpp, display.cpp, serial_cmd.cpp) yang menyentuh buffer atau array penuh, RECORDER_SECONDS/RECORDER_N, antrean ISR, kapasitas LittleFS atau PSRAM, nomor berkas rekaman, atau tulis berkas, jaringan di loop(). Juga untuk keluhan "rekaman terpotong", "sampel hilang", "buffer penuh", "loop macet", "simpan memblok", "data hilang", "rekam berhenti sendiri", dan saat merencanakan uji batas rekam. Memuat skill umum firmware-bounded-limits lalu menambahkan nilai, nama, dan berkas khusus PA.
---

# Batas tidak diam (lapisan PA)

Muat skill user `firmware-bounded-limits` lebih dulu; skill ini hanya menambah hal khusus repo PA.

## Nilai dan nama di firmware PA

Pakai nama ini persis di kode, pesan, dan rencana uji, karena skill umum memakai nama generik.

- Antrean ISR: `QUEUE_N = 256` (`firmware/include/acquisition.h`) pada `ECG_FS = 360` Hz, jadi 256 / 360 = 711 ms. `loop()` mengambil satu sampel per iterasi. Bandingkan setiap konstanta waktu simpan, coba ulang, dan batas tunggu dengan 711 ms.
- Isi antrean dibaca lewat `acquisition_fill()`; potongan simpan hanya jalan saat `acquisition_fill() == 0`.
- Sampel hilang dihitung `acquisition_missed()` (sama dengan `n_lewat + n_tick_lost`). Uji jalur gagal mencocokkan angka yang dilaporkan dengan selisih `acquisition_missed()`.
- Batas rekam di `firmware/include/recorder.h`: `RECORDER_SECONDS` (bawaan 300), `RECORDER_PART` (bawaan 6), `RECORDER_NUMBER` (bawaan 999). `RECORDER_N` di `firmware/src/recorder.cpp` turunan `ECG_FS * RECORDER_SECONDS`, jadi build flag-nya `RECORDER_SECONDS`, bukan `RECORDER_N`.
- Desain rekam yang berlaku (`recorder.cpp`): seluruh sesi ditahan di PSRAM dengan `SESSION_N = RECORDER_N * RECORDER_PART_MAX`, baru ditulis ke LittleFS sesudah berhenti, dari `recorder_service()` saat `acquisition_fill() == 0`. Kapasitas per bagian `FULL_FILE_SPACE`, dan `part_max` dihitung saat mulai dari ruang bebas dan `RECORDER_NUMBER_MAX`. Perubahan dimulai dari desain ini, bukan dari rancangan baru, karena skema ini sudah ada di repo.
- Penghitung nama PA: sampel dilewati antrean = `lewat` (`acquisition_missed()`, juga `lewat=` di header CSV); data yang belum tersimpan = `belum` (belum ada di firmware, ditambahkan ke baris `s` bila uji membutuhkannya). Jangan pakai `lewati`: nama itu sudah dipakai di baris `s` untuk gerbang kalibrasi bench.
- Penulis wadah di `recorder.cpp` memeriksa batasnya sendiri; fungsi dari jalur sampel (`recorder_sample`) hanya menulis `aktif = false` dan menandai kejadian.
- Variabel penanda sesi di `recorder.cpp` bernama `aktif`; setiap jalur berhenti menulis `aktif = false` sebelum `Serial`, `display_message`, atau `display_sound`.

## Teks layar dan serial

Teks layar berbahasa Indonesia, untuk manusia: `RUANG PENUH`, `BATAS SESI`, `TUNGGU`, `TOLAK`, `PENUH`, `GAGAL SIMPAN`. Baris REC (`REC05:00`, di `display.cpp`) tampil hanya saat sampel benar-benar masuk wadah; saat `acquisition_missed()` di atas nol diganti `HILANG` (merah), dan saat menyimpan tampil `SIMPAN..` lalu `SIMPAN`. Pesan baru mengikuti gaya itu lewat `display_message(besar, kecil)`.

Perintah serial 115200 untuk uji: `r` mulai atau stop rekam, `j` jeda, `s` status (memuat `rekam=<0|1> n=<n>`, `antrean <n>`, `sampel hilang <n> (tick <n>)`), `l` daftar berkas, `d<n>` cetak berkas, `h<n>` hapus, `y` ganti sumber sinyal (replay tanpa sensor; `r` menolak bila sumber bukan ADC: serial `REKAM hanya dari sensor`, layar `TOLAK`, jadi uji batas rekam memakai sensor, bukan replay). Penghitung yang dibutuhkan uji tetapi belum ada di baris `s` ditambahkan ke baris status pada perubahan yang sama.

## Uji di board PA

Batas kecil lewat build flag dari `firmware/`, satu perintah literal per uji:

```bash
PLATFORMIO_BUILD_FLAGS="-DRECORDER_SECONDS=10" pio run -t upload
```

Daftar batas di berkas PA dicari dengan `grep -nE "(>=|==|>) *[A-Z_]*(MAKS|_N)" firmware/src/*.cpp`, karena konstanta batas PA bersufiks `_MAKS` atau `_N`. Uji jeda membaca jumlah sampel pasti dari penghitung (`n=` di baris `s`) sebelum dan sesudah jeda, dan baris harapan memakai selisihnya.

Batas asli (300 detik) dilewati sekali di board. Board tercolok berarti Claude yang menjalankan uji dan membaca serialnya; hasil yang belum dijalankan ditulis harapan dan butir daftar periksa tetap `[ ]` (aturan keras C di `CLAUDE.md`).

## Dokumentasi dan pemeriksa

- Blok opsi untuk user memuat satu rekomendasi beserta alasannya, karena keputusan tetap milik user.
- Batas yang hanya membuang isyarat UI dicatat di `firmware/README.md` §Batasan yang disengaja.
- Prosedur masuk bagian fitur di `firmware/README.md`; jebakan beserta angka ukurnya masuk §Jebakan subsistem yang tepat; flag uji ikut didokumentasikan di sana.
- Kode tanpa komentar (skill `tanpa-komentar-kode`); `python3 scripts/check_comments.py` harus keluar 0.
