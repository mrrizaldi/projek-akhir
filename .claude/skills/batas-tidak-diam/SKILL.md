---
name: batas-tidak-diam
description: Wajib dipakai saat menulis atau menyunting firmware yang punya batas (buffer/array penuh, durasi maksimum, antrean, kapasitas LittleFS/PSRAM, nomor berkas) atau operasi lambat di loop() (tulis berkas, jaringan). Batas tidak boleh membuang data diam-diam, dan aksi di batas tidak boleh memblok jalur real-time.
---

# Batas tidak diam

Kegagalan yang ditangkap user (14 Okt 2026): user merekam ±45 menit, tetapi
hanya 5 menit tersimpan. `rekam_sampel()` berisi
`if (n >= REKAM_N) return;`: setelah 300 detik sampel dibuang tanpa tanda,
sesi tetap aktif, dan layar menampilkan `REC05:00` merah yang membeku. Saat
diperbaiki, aksi di batas (menyimpan 540 KB sekaligus) ternyata memblok
`loop()` ±4 detik dan membuang 1.450 sampel. Kedua masalah lolos semua uji
karena tidak ada uji yang pernah mencapai batasnya.

## Aturan

1. **Setiap batas punya perilaku yang dipilih, bukan `return`.** Untuk setiap
   `if (x >= MAKS) return;` / `break` / indeks penuh, tentukan satu dari:
   - lanjut (simpan lalu mulai wadah baru, mis. berkas lanjutan),
   - berhenti dan tutup dengan benar: wadah yang sudah penuh DISIMPAN lewat
     jalur simpan yang sama, baru sesi ditutup (urutan: simpan, tutup sesi,
     serial, layar, bip); data yang sudah terkumpul tidak pernah dibuang,
   - tolak di depan (sebelum mulai, mis. ruang LittleFS tidak cukup).
   Syarat "tolak" diperiksa ulang setiap kali wadah baru dibuka (tiap berkas
   lanjutan), bukan sekali di awal sesi; kegagalan di tengah sesi (ruang habis,
   tulis gagal, alokasi gagal) diperlakukan sebagai batas: wadah yang terkumpul
   disimpan, lalu serial + layar + bip. Kegagalan alokasi juga harus terlihat
   setiap kali fitur dipakai, bukan hanya sekali saat boot.
   Data terkumpul tidak dibuang, baik diam-diam maupun dengan pesan. Satu-satunya
   pengecualian: sisa byte yang ditolak panggilan tulis karena ruang habis,
   dihitung dan dilaporkan sebagai `belum tersimpan`, dan ujinya menyuntik
   kegagalan itu. Kegagalan `open`, `close`, `usedBytes()`, atau cek ruang
   BUKAN pengecualian: coba simpan wadah lewat jalur simpan yang sama (atau
   tunda dan coba lagi), dan hanya sisa yang benar-benar tidak tertulis yang
   dihitung. `close()` tidak mengembalikan status, jadi sesudah menutup bandingkan
   ukuran berkas dengan byte yang ditulis; selisihnya dihitung `belum tersimpan`
   (atau ditulis ulang). Baris CSV yang terpotong di akhir berkas dipangkas atau
   disebut di dokumen supaya alat analisis tidak salah baca. Keadaan "simpan sebelumnya belum selesai saat wadah baru penuh"
   dibuktikan tak tercapai dengan hitungan terukur (lama simpan vs lama mengisi
   wadah). Bila tetap terjadi, jalur sampel TIDAK menunggu simpan (aturan 4):
   sampel yang tidak tertampung dihitung sebagai `hilang`, dicetak di serial
   dan tampil di layar, dan jumlahnya sama dengan `akuisisi_lewat()` / selisih
   penghitung. Tidak boleh ada kehilangan yang tak dilaporkan.
   Pilihan yang mengubah pengalaman user (lanjut vs berhenti, kapasitas)
   ditanyakan ke user, dan teks pertanyaannya ditulis lengkap di jawaban: satu
   baris per opsi beserta akibatnya, lalu rekomendasi dan alasannya. Menulis
   "sudah ditanyakan" tanpa teks opsi tidak memenuhi aturan ini. Ini berlaku
   juga untuk perilaku "tolak" (mis. nomor berkas habis) dan untuk setiap batas
   data baru yang dirancang sendiri (log, buffer), walau user tidak menyebutnya;
   bila pilihannya tidak mengubah pengalaman user, tulis alasannya. "Saya usulkan
   X, kabari bila mau lain" bukan blok opsi; tulis minimal dua opsi. Opsi tidak
   pernah menghapus data; bila ruang harus dikosongkan, sebut "tarik data lalu
   hapus" sebagai tindakan user. Angka kapasitas di
   opsi (berapa berkas / menit muat) dihitung sesudah cadangan yang dipakai
   desain itu sendiri dan overhead sistem berkas, dengan rumusnya ditulis, dan
   satuannya konsisten (KB = 1024 B bila membandingkan dengan `totalBytes()`).
   Jumlah berkas dihitung dengan tabel "cek ke-k → sisa → lanjut/berhenti →
   berkas tersimpan" agar tidak meleset satu.
   Fungsi yang menulis ke wadah tetap menjaga batasnya sendiri (cek sebelum
   menulis), tidak bergantung pada pemanggil untuk mengosongkan wadah tepat
   waktu.
2. **Batas yang tercapai selalu terlihat:** baris serial yang bisa di-grep,
   pesan di layar (`tampilan_pesan`), dan bila sesi berakhir, bip. Keadaan
   yang ditampilkan harus jujur: tidak boleh ada `REC` merah atau penghitung
   waktu yang terus tampil sementara data tidak lagi disimpan; saat ada sampel
   yang hilang, indikator REC diganti indikator hilang (mis. `HILANG` merah),
   jadi fungsi penentu tampilan REC ikut memeriksa jalur hilang. Setiap fungsi
   yang menghentikan sesi (berhenti normal, batas, gagal) menulis
   `aktif = false` sebelum serial, layar, dan bip, dan nilai kembali pemanggil
   (mis. `rekam_sampel` gagal) ditangani tertulis.
3. **Pilah batas menurut akibatnya** sebelum memutuskan:
   - membuang DATA (sampel, rekaman, beat, hasil ukur) → aturan 1 dan 2 wajib;
   - membuang isyarat UI (bip, redraw) → boleh dibuang, tetapi dicatat di
     `firmware/README.md` §Batasan yang disengaja;
   - tidak dapat tercapai menurut rancangan (array seukuran jumlah jendela
     tetap, kedalaman menu statis) → biarkan, sebut alasannya bila ditanya.
   Bukti "tidak dapat tercapai" berasal dari kode: tulis kedua angka yang
   dibandingkan dan cara menghitungnya: jumlah entri yang benar-benar dipakai
   (termasuk entri akar/awal) dan indeks terbesar yang diizinkan pemeriksaan
   batasnya (mis. `if (dalam + 1 >= DALAM_MAKS) return;` mengizinkan indeks
   sampai `DALAM_MAKS - 1`), bukan perkiraan.
4. **Aksi di batas tidak boleh memblok jalur real-time.** Antrean ISR 256
   sampel pada 360 Hz = 711 ms. Operasi > beberapa puluh ms (tulis berkas,
   `usedBytes()`, jaringan) dipecah per potongan lintas iterasi `loop()`, dan
   potongan berikutnya hanya jalan saat antrean kosong (`akuisisi_isi() == 0`),
   karena `loop()` mengambil satu sampel per iterasi: kerja sedikit di setiap
   iterasi pun menurunkan laju konsumsi di bawah 360 Hz. Data yang sedang
   ditulis tidak boleh ditimpa: pakai buffer kedua (PSRAM), bukan menyalin.
   `open`, `close`, `usedBytes()`, dan pemindaian direktori termasuk kerja sisi
   tulis: ukur durasinya dan tunjukkan totalnya di bawah anggaran antrean bila
   harus terjadi di jalur sampel (mis. saat wadah ditukar). Jalur sampel
   (fungsi yang dipanggil per sampel) tidak pernah memanggil penyelesaian
   simpan, `while` menunggu, atau tulis dengan bendera "paksa"; semua kerja
   simpan hanya di `loop()` saat `akuisisi_isi() == 0`. Setiap konstanta waktu
   di desain (batas tunggu, periode coba ulang) diberi nilai dan dibandingkan
   dengan anggaran antrean 711 ms secara angka (mis. "coba ulang tiap 1000 ms;
   satu percobaan = satu `open` terukur X ms < 711 ms"), juga bila ia berjalan
   di luar jalur sampel. Setiap angka turunan ditulis rumusnya.
5. **Uji batasnya, dua kali:**
   - batas kecil lewat build flag (`#ifndef X / #define X <bawaan>`, lalu
     `PLATFORMIO_BUILD_FLAGS="-DX=<kecil>" pio run -t upload`) untuk melewati
     batas beberapa kali dengan cepat;
   - batas sebenarnya sekali di board, karena biaya aksi (ukuran berkas, lama
     tulis) baru terlihat di ukuran asli.
   SETIAP uji ditulis dengan perintah lengkap (mis.
   `PLATFORMIO_BUILD_FLAGS="-DREKAM_DETIK=10" pio run -t upload`, lalu perintah
   serial yang dikirim) dan diakhiri satu baris harapan tetap yang memuat semua
   penghitung dengan nilai pasti, termasuk nol (mis.
   `berkas=2 total=1440 hilang=0 belum=0 lewat=0`) serta string serial yang
   diharapkan ditulis lengkap. SETIAP uji (bukan hanya uji flag) menyebut angka harapan yang pasti, bukan
   kesan atau "≈": pencacah sampel hilang (`akuisisi_lewat()`, baris `s`) = 0
   sebelum, selama, dan sesudah aksi; jumlah tersimpan = penghitung/header,
   tepat; pesan batas muncul di serial. Uji yang sengaja memicu jalur memblok
   atau gagal (simpan tertunda, injeksi tulis gagal) memeriksa bahwa jumlah
   yang dilaporkan hilang/belum tersimpan sama persis dengan
   `akuisisi_lewat()` dan selisih penghitung. Durasi uji yang memakai jeda
   dihitung dari jumlah sampel, bukan dari jam dinding.
   Baris harapan tidak memakai `≈`, "sekitar", "perkiraan", "parsial", atau
   ketidaksamaan (`<`, `>`): tulis angka pasti hasil rumus, termasuk untuk uji
   pendukung (isi berkas terakhir = sisa sampel). Estimasi ditulis terpisah dan
   diberi label. Setiap angka menyebut sumbernya: fakta (dari user/repo),
   terukur (dijalankan di sesi ini), atau estimasi. Setiap besaran dikonversi sekali (B ke
   KiB dengan pembulatan yang ditulis) lalu angka yang sama dipakai di semua
   tempat.
   Hasil uji hanya ditulis sebagai teramati bila perintahnya benar-benar
   dijalankan di sesi itu; selain itu ditulis "harapan" dan didaftar sebagai
   belum dijalankan (aturan keras C di CLAUDE.md).
6. **Kalau angka meleset, ukur sebelum menebak.** Pasang pengukur di salinan
   sementara (bukan di repo): `micros()` di sekitar tiap operasi, iterasi
   `loop()` terlama, isi antrean maksimum. Pengukur "iterasi > 200 ms" yang
   kosong tidak membuktikan apa-apa bila masalahnya laju, bukan satu jeda
   panjang; ukur juga isi antrean.
7. **Dokumentasikan** perilaku batas di `firmware/README.md`: prosedur pakai
   (bagian Merekam atau bagian fitur terkait), jebakan + angka ukur di
   §Jebakan sesuai subsistem, dan flag uji batas kecil. Tanpa komentar kode
   (skill `tanpa-komentar-kode`). Jawaban memuat teks README yang ditambahkan
   secara lengkap (nama bagian, kalimat, angka), bukan hanya "README perlu
   diperbarui"; angka yang belum terukur di board ditulis "belum diverifikasi
   di board".

## Daftar periksa akhir

- [ ] Grep batas di berkas yang disentuh (`grep -nE "(>=|==) *[A-Z_]*(MAKS|_N)" src/*.cpp`)
      dan semua batas sudah dipilah (data / UI / tak tercapai).
- [ ] Batas data: perilaku dipilih (lanjut / berhenti / tolak), terlihat di
      serial + layar, keadaan layar jujur.
- [ ] Opsi berhenti menyimpan wadah penuh sebelum menutup sesi; syarat tolak
      dicek ulang tiap wadah baru; kegagalan di tengah sesi terlihat.
- [ ] Pertanyaan ke user ditulis lengkap (opsi + akibat + rekomendasi), termasuk
      perilaku tolak; angka kapasitas sesudah cadangan + overhead, rumus ditulis.
- [ ] Tidak ada data terkumpul yang dibuang di jalur gagal; yang tak bisa ditulis
      dihitung `belum tersimpan`; simpan tertunda diselesaikan, bukan dibuang.
- [ ] Setiap jalur berhenti menulis `aktif = false` (`grep -n "aktif *= *false"`);
      layar tidak menampilkan REC saat tidak aktif.
- [ ] `open`/`close`/`usedBytes()` di jalur sampel diukur dan di bawah anggaran.
- [ ] Jalur sampel tanpa penyelesaian simpan, `while` menunggu, atau tulis
      "paksa"; konstanta waktu bernilai dan dibandingkan dengan 711 ms.
- [ ] Baris harapan angka pasti (tanpa `≈`, "sekitar", "parsial", `<`); sumber
      angka disebut (fakta / terukur / estimasi); konversi satuan sekali.
- [ ] Setiap batas data baru punya blok opsi tertulis (atau alasan tidak perlu);
      tidak ada opsi yang menghapus data.
- [ ] Tampilan REC diganti indikator hilang saat sampel hilang.
- [ ] Perilaku tolak berbentuk blok opsi (≥ 2 opsi + rekomendasi).
- [ ] Ukuran berkas diverifikasi sesudah `close()`; baris terpotong ditangani.
- [ ] Tiap uji: perintah lengkap + baris harapan tetap
      (`berkas= total= hilang= belum= lewat=`) + string serial lengkap.
- [ ] Teks README ditulis lengkap di jawaban.
- [ ] Cabang gagal open/close/usedBytes/cek ruang tetap mencoba menyimpan wadah;
      pengecualian hanya sisa byte yang ditolak tulis karena ruang.
- [ ] Setiap uji punya angka harapan pasti; uji jalur memblok/gagal mencocokkan
      jumlah yang dilaporkan dengan `akuisisi_lewat()`.
- [ ] Tidak ada hasil yang ditulis teramati tanpa dijalankan; yang belum
      dijalankan didaftar.
- [ ] Fungsi penulis wadah menjaga batasnya sendiri (cek sebelum tulis).
- [ ] Aksi di batas tidak memblok: dipecah, jalan saat antrean kosong, buffer
      kedua bila data masih ditulis.
- [ ] Uji batas kecil (build flag) + batas asli di board; sampel hilang 0
      selama dan sesudah; jumlah tersimpan cocok.
- [ ] README diperbarui; flag uji disebut; pemeriksa komentar keluar 0.
