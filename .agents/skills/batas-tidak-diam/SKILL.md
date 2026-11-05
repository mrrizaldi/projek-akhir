---
name: batas-tidak-diam
description: Wajib dipakai saat menulis atau menyunting firmware yang punya batas (buffer/array penuh, durasi maksimum, antrean, kapasitas LittleFS/PSRAM, nomor berkas) atau operasi lambat di loop() (tulis berkas, jaringan). Batas tidak boleh membuang data diam-diam, dan aksi di batas tidak boleh memblok jalur real-time.
---

# Batas tidak diam

Kegagalan yang ditangkap user (14 Okt 2026): user merekam ±45 menit, hanya 5
menit tersimpan. `rekam_sampel()` berisi `if (n >= REKAM_N) return;`: setelah
300 detik sampel dibuang tanpa tanda, sesi tetap aktif, layar `REC05:00` merah
membeku. Saat diperbaiki, menyimpan 540 KB sekaligus memblok `loop()` ±4 detik
dan membuang 1.450 sampel. Tidak ada uji yang pernah mencapai batasnya.

## Aturan

1. **Pilah dulu setiap batas** (`grep -nE "(>=|==) *[A-Z_]*(MAKS|_N)" src/*.cpp`):
   - membuang DATA (sampel, rekaman, hasil ukur) → aturan 2–7 wajib;
   - membuang isyarat UI (bip, redraw) → boleh, catat di `firmware/README.md`
     §Batasan yang disengaja;
   - tak tercapai menurut rancangan → biarkan; buktinya dua angka dari kode
     (entri terpakai termasuk akar vs indeks terbesar yang diizinkan guard).

2. **Batas data punya perilaku yang dipilih, bukan `return`:** lanjut (simpan,
   wadah baru), berhenti (simpan wadah terkumpul DULU, baru tutup sesi), atau
   tolak di depan. Syarat tolak dicek ulang tiap wadah baru. Fungsi penulis
   wadah menjaga batasnya sendiri (cek sebelum tulis).
   Pilihan yang mengubah pengalaman user ditulis sebagai blok opsi lengkap di
   jawaban: ≥ 2 opsi, akibat tiap opsi, rekomendasi + alasan. Berlaku juga untuk
   perilaku tolak dan batas data rancangan sendiri. "Saya usulkan X" bukan blok
   opsi. Opsi tidak pernah menghapus data (mengosongkan ruang = user "tarik data
   lalu hapus"). Angka kapasitas di opsi dihitung sesudah cadangan dan overhead,
   rumus ditulis, dengan tabel "cek ke-k → sisa → lanjut/berhenti → berkas".

3. **Data terkumpul tidak pernah dibuang**, diam-diam maupun dengan pesan.
   Satu-satunya pengecualian: byte yang ditolak panggilan tulis karena ruang
   habis, dihitung `belum tersimpan`. Gagal `open`/`close`/cek ruang, coba ulang
   yang habis, atau simpan tertunda BUKAN pengecualian: wadah tetap utuh di
   PSRAM, sesi berhenti, coba lagi nanti. `close()` tak berstatus: bandingkan
   ukuran berkas dengan byte tertulis. Baris CSV terpotong dipangkas atau
   didokumentasikan. Bila jalur sampel tidak bisa menampung (wadah berikutnya
   penuh sebelum simpan selesai, dibuktikan tak tercapai dengan hitungan),
   sampel dihitung `hilang`, bukan ditunggu.

4. **Terlihat dan jujur.** Setiap kejadian batas, `hilang`, atau `belum`:
   baris serial yang bisa di-grep + `tampilan_pesan` + bip bila sesi berakhir.
   Setiap jalur berhenti menulis `aktif = false` sebelum serial/layar/bip.
   Pesan layar ditulis untuk manusia (`RUANG PENUH, TERSIMPAN`), bukan label
   internal (`ruang`, `wadah_tertahan`).
   Tampilan REC hanya saat sampel benar-benar masuk wadah; saat `hilang > 0` atau
   `belum > 0` diganti indikator (mis. `HILANG` merah); saat menyimpan sesudah
   berhenti tampil `SIMPAN`. Nilai kembali ke pemanggil ditangani tertulis.

5. **Tidak memblok jalur real-time.** Antrean ISR 256 sampel / 360 Hz = 711 ms,
   dan `loop()` mengambil satu sampel per iterasi. Jalur sampel hanya menukar
   pointer wadah (buffer kedua PSRAM, tanpa salin): tanpa `open`/`close`/tulis/
   `usedBytes()`/`while` menunggu/tulis "paksa"/Serial/tampilan/bip. Fungsi yang
   dipanggil dari jalur sampel (termasuk penanganan batas dan berhenti) hanya
   menulis `aktif = false` dan menandai kejadian; serial, layar, dan bip
   dijalankan dari `loop()`. Simpan dipecah per potongan di
   `loop()` dan hanya jalan saat `akuisisi_isi() == 0`. Setiap konstanta waktu
   (potongan, coba ulang, batas tunggu) diberi nilai + rumus dan dibandingkan
   dengan 711 ms. Durasi `open`/`close`/`usedBytes()`/pindai direktori diukur
   (`micros()` di salinan sementara, bukan di repo), termasuk isi antrean
   maksimum; "iterasi > 200 ms" saja tidak cukup karena masalahnya bisa laju.

6. **Uji batasnya, dengan angka pasti.**
   - Batas kecil lewat build flag (`#ifndef X / #define X <bawaan>`) melewati
     batas beberapa kali; batas asli sekali di board.
   - Tiap uji berdiri sendiri: perintah build literal sendiri (bukan "sama
     dengan Uji n"; mis. `PLATFORMIO_BUILD_FLAGS="-DREKAM_DETIK=10"
     pio run -t upload`, lalu perintah serial), kondisi awal dipastikan lewat
     baris pasti (bukan klausa "bila berbeda"), baris `s` sebelum/selama/sesudah
     dengan `sampel hilang 0`, dan satu baris harapan tetap berisi semua
     penghitung bernilai pasti termasuk nol (`berkas=3 total=2160 hilang=0
     belum=0 lewat=0`) plus string serial lengkap.
   - Baris harapan tanpa `≈`, "sekitar", "parsial", `<`/`>`, atau placeholder
     (`k`, `<p>`, `NNN`); uji jeda memakai jumlah sampel pasti.
   - Uji yang memicu jalur gagal (injeksi tulis/open gagal) mencocokkan angka
     yang dilaporkan dengan selisih penghitung dan `akuisisi_lewat()`.
   - Setiap angka menyebut sumber (fakta / terukur di sesi ini / estimasi);
     konversi satuan sekali (KiB = 1024 B bila dibanding `totalBytes()`).
   - Hasil hanya ditulis teramati bila dijalankan; selain itu "harapan" dan
     didaftar belum dijalankan (aturan keras C); butir daftar periksa yang
     butuh eksekusi tetap `[ ]` sampai dijalankan.

7. **Dokumentasi** di `firmware/README.md`: prosedur (bagian fitur), jebakan +
   angka ukur (§Jebakan, subsistem yang tepat), flag uji. Jawaban memuat teks
   README lengkap (bagian, kalimat, angka); angka belum terukur ditulis "belum
   diverifikasi di board". Kode tanpa komentar (skill `tanpa-komentar-kode`).

## Daftar periksa akhir

- [ ] Semua batas di berkas yang disentuh dipilah (data / UI / tak tercapai).
- [ ] Batas data: perilaku dipilih; blok opsi tertulis (≥ 2 opsi, akibat,
      rekomendasi, kapasitas dengan rumus + tabel), tanpa opsi menghapus data.
- [ ] Tidak ada data terkumpul dibuang; pengecualian hanya byte ditolak tulis;
      ukuran diverifikasi sesudah `close()`.
- [ ] Serial + layar + bip; `aktif = false` lebih dulu; REC diganti indikator
      saat `hilang` atau `belum` > 0.
- [ ] Jalur sampel hanya tukar pointer dan menandai kejadian (tanpa Serial/
      tampilan/bip); simpan per potongan saat antrean kosong;
      konstanta waktu bernilai vs 711 ms; durasi I/O diukur.
- [ ] Tiap uji berdiri sendiri: perintah literal, kondisi awal pasti,
      `sampel hilang 0` sebelum/selama/sesudah,
      baris harapan tetap tanpa `≈`/`<`/placeholder; sumber angka disebut;
      tidak ada hasil teramati tanpa dijalankan.
- [ ] Teks README lengkap; pemeriksa komentar keluar 0.
