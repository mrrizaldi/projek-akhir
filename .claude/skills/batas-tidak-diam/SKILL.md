---
name: batas-tidak-diam
description: Lapisan repo PA untuk firmware yang punya batas atau operasi lambat di loop(). Pakai setiap kali menulis, menyunting, atau meninjau firmware/src (rekam.cpp, akuisisi.cpp, tampilan.cpp, serial_cmd.cpp) yang menyentuh buffer atau array penuh, REKAM_DETIK/REKAM_N, antrean ISR, kapasitas LittleFS atau PSRAM, nomor berkas rekaman, atau tulis berkas, jaringan di loop(). Juga untuk keluhan "rekaman terpotong", "sampel hilang", "buffer penuh", "loop macet", "simpan memblok", "data hilang", "rekam berhenti sendiri", dan saat merencanakan uji batas rekam. Memuat skill umum firmware-bounded-limits lalu menambahkan nilai, nama, dan berkas khusus PA.
---

# Batas tidak diam (lapisan PA)

Muat skill user `firmware-bounded-limits` lebih dulu; skill ini hanya menambah hal khusus repo PA.

## Nilai dan nama di firmware PA

Pakai nama ini persis di kode, pesan, dan rencana uji, karena skill umum memakai nama generik.

- Antrean ISR: `ANTRE_N = 256` (`firmware/include/akuisisi.h`) pada `ECG_FS = 360` Hz, jadi 256 / 360 = 711 ms. `loop()` mengambil satu sampel per iterasi. Bandingkan setiap konstanta waktu simpan, coba ulang, dan batas tunggu dengan 711 ms.
- Isi antrean dibaca lewat `akuisisi_isi()`; potongan simpan hanya jalan saat `akuisisi_isi() == 0`.
- Sampel hilang dihitung `akuisisi_lewat()` (sama dengan `n_lewat + n_tick_hilang`). Uji jalur gagal mencocokkan angka yang dilaporkan dengan selisih `akuisisi_lewat()`.
- Batas rekam di `firmware/include/rekam.h`: `REKAM_DETIK` (bawaan 300), `REKAM_BAGIAN` (bawaan 6), `REKAM_NOMOR` (bawaan 999). `REKAM_N` di `firmware/src/rekam.cpp` turunan `ECG_FS * REKAM_DETIK`, jadi build flag-nya `REKAM_DETIK`, bukan `REKAM_N`.
- Penulis wadah di `rekam.cpp` memeriksa batasnya sendiri; fungsi dari jalur sampel (`rekam_sampel`) hanya menulis `aktif = false` dan menandai kejadian.
- Variabel penanda sesi di `rekam.cpp` bernama `aktif`; setiap jalur berhenti menulis `aktif = false` sebelum `Serial`, `tampilan_pesan`, atau `tampilan_bunyi`.

## Teks layar dan serial

Teks layar berbahasa Indonesia, untuk manusia: `RUANG PENUH`, `BATAS SESI`, `TUNGGU`, `TOLAK`, `PENUH`, `GAGAL SIMPAN`. Baris REC (`REC05:00`, di `tampilan.cpp`) tampil hanya saat sampel benar-benar masuk wadah; saat `akuisisi_lewat()` di atas nol diganti `HILANG` (merah), dan saat menyimpan tampil `SIMPAN..` lalu `SIMPAN`. Pesan baru mengikuti gaya itu lewat `tampilan_pesan(besar, kecil)`.

Perintah serial 115200 untuk uji: `r` mulai atau stop rekam, `j` jeda, `s` status (memuat `rekam=<0|1> n=<n>`, `antrean <n>`, `sampel hilang <n> (tick <n>)`), `l` daftar berkas, `d<n>` cetak berkas, `h<n>` hapus, `y` ganti sumber sinyal (replay tanpa sensor). Penghitung yang dibutuhkan uji tetapi belum ada di baris `s` ditambahkan ke baris status pada perubahan yang sama.

## Uji di board PA

Batas kecil lewat build flag dari `firmware/`, satu perintah literal per uji:

```bash
PLATFORMIO_BUILD_FLAGS="-DREKAM_DETIK=10" pio run -t upload
```

Batas asli (300 detik) dilewati sekali di board. Board tercolok berarti Claude yang menjalankan uji dan membaca serialnya; hasil yang belum dijalankan ditulis harapan dan butir daftar periksa tetap `[ ]` (aturan keras C di `CLAUDE.md`).

## Dokumentasi dan pemeriksa

- Batas yang hanya membuang isyarat UI dicatat di `firmware/README.md` §Batasan yang disengaja.
- Prosedur masuk bagian fitur di `firmware/README.md`; jebakan beserta angka ukurnya masuk §Jebakan subsistem yang tepat; flag uji ikut didokumentasikan di sana.
- Kode tanpa komentar (skill `tanpa-komentar-kode`); `python3 scripts/cek_komentar.py` harus keluar 0.
