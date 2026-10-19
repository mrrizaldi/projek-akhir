---
name: buku-ikut-proposal
description: Wajib dipakai saat menyunting laporan/buku-pa (terutama Bab 1) atau saat menyusun pertanyaan/laporan akhir ke user tentang isi buku. Kerangka Bab 1 mengikuti proposal persis; pertanyaan ke user hanya untuk keputusan yang mengubah isi buku sekarang.
---

# Buku ikut proposal

Kegagalan yang ditangkap user (14 Okt 2026):
- Bab 1 buku-pa diberi subbab Batasan Masalah (6 butir) yang tidak ada di
  proposal. User: "rumusan masalahnya kok jadi 6 bejir, ngikut yang di
  proposal aja".
- User ditanya soal rakitan uji 18–19 Sep yang sudah tercatat di repo dan
  tidak mengubah isi buku. User: "napa ditanyain jir, gausah".

## Aturan

1. Kerangka Bab 1 `laporan/buku-pa/bab/bab1.tex` = kerangka
   `laporan/proposal-pa/bab/bab1.tex`: Latar Belakang, Permasalahan (3 butir
   "Bagaimana ...?"), Tujuan (3 butir), Manfaat (3 butir), Sistematika
   Penulisan. Jumlah butir Permasalahan dan Tujuan tetap 3.
2. Jangan menambah subbab Bab 1 yang tidak ada di proposal (Batasan Masalah,
   Ruang Lingkup, Kontribusi, dll.), walau laporan acuan (AFIB) memilikinya.
   Keputusan user 14 Okt 2026: Bab 1 buku mengikuti proposal. Isi subbab
   Bab 1 boleh diperbarui (angka, sitasi, istilah) bila faktanya berubah.
   Yang diikuti dari proposal adalah **garis besar**, bukan kalimat: tiga
   hal yang dipermasalahkan, tiga tujuan, dan apa yang diuji (Rencana
   Pengujian Bab 3). Kalimat buku ditulis dengan skill `narasi-pa` dan
   tidak harus identik dengan proposal.
   Arah sebaliknya tidak ada: `laporan/proposal-pa` sudah diserahkan dan
   dibekukan (keputusan user 15 Okt 2026). Proposal tidak disunting lagi,
   termasuk daftar pustakanya, walau buku sudah bergeser (target berangka,
   uji tambahan, sitasi baru). Buku cukup memuat rancangan akhir di Bab 3
   dan hasilnya di Bab 4, tanpa tabel "perubahan dari proposal" (keputusan
   user 19 Okt 2026, mengikuti buku AFIB), dan proposal tidak diubah.
3. Lingkup ditulis di subbab tetap berikut, tanpa `\ref` ke subbab Bab 1 yang
   tidak ada:
   - subjek sehat anonim, non-klinis, data primer → Bab 4 Karakteristik Data
     (`sec:karakteristik-data`) dan Tempat Ujicoba;
   - klasifikasi biner, bukan alat diagnosis, daya tidak dioptimasi → Bab 4
     Keterbatasan (`subsec:analisis-keterbatasan`);
   - data latih mitdb inter-patient DS1/DS2 → Bab 3 Dataset dan Pelabelan.
   Rujukan ke subbab yang dihapus diganti kalimat utuh yang berdiri sendiri
   (hapus klausa "sesuai ..."), atau `\ref` ke label yang ADA di daftar atas.
   Dilarang penunjuk tanpa target seperti "pada subbab ini" / "seperti di
   atas". Setelah menyunting, jalankan
   `cd /home/mrrizaldi/dev/projek-akhir/laporan/buku-pa && make pdf` dan
   pastikan `grep -i undefined output/main.log` kosong.
4. Pertanyaan ke user hanya untuk keputusan yang mengubah isi buku SEKARANG
   dan tidak bisa dijawab dari repo. Sebelum bertanya, cari dulu di repo
   (`model/CLAUDE.md`, `model/docs/`, `docs/arsip/`, `model/docs/arsip/`,
   isi buku sendiri). Pemilahan:
   - riwayat yang sudah tercatat di repo (rakitan lama, tanggal uji, pin
     lama) → pakai apa adanya, jangan ditanyakan;
   - angka yang menunggu data resmi → `\PlaceholderData{...}`, jangan ditanyakan;
   - hal yang menunggu peristiwa (PCB final dicetak, rekaman resmi) → butir
     `model/CLAUDE.md` §Pekerjaan terbuka, jangan ditanyakan;
     di teks/tabel buku jangan ditulis seolah sudah terjadi (bukan "PCB
     final", tapi `\PlaceholderData{rakitan final}`);
   - keputusan milik user yang belum pernah diambil dan tidak ada jawabannya
     di repo (mis. warna sampul, templat kampus, rumusan baru) → DITANYAKAN
     sekali, dengan opsi + rekomendasi. Hal ini dianggap memblok penyelesaian
     buku walau bab lain masih bisa ditulis. Jangan memutuskannya diam-diam
     dengan "pakai bawaan".
5. Laporan akhir ke user menyebut apa yang diubah dan bukti build yang BENAR-
   BENAR dijalankan di sesi itu (jumlah halaman dan jumlah `undefined` dari
   `output/main.log`). Perintah yang belum dijalankan ditulis "belum
   dijalankan", bukan "sukses"/"0". Lalu hanya pertanyaan dari butir terakhir
   aturan 4, dengan alasan rekomendasi dari fakta repo, bukan "biasanya".
   Tanpa pertanyaan pun boleh.

## Daftar periksa akhir

- [ ] `diff` kerangka `\section` Bab 1 buku vs proposal: sama.
- [ ] Permasalahan 3 butir, Tujuan 3 butir.
- [ ] `grep -rn "batasan-masalah" laporan/buku-pa/bab` kosong (atau label lain
      yang subbabnya dihapus).
- [ ] `make pdf` sukses, `undefined` 0, dan angkanya dari keluaran yang dijalankan;
      yang belum dijalankan ditulis "belum dijalankan".
- [ ] Tidak ada sel/kalimat yang menyebut keadaan yang belum terjadi (PCB final,
      rekaman resmi) sebagai fakta; pakai `\PlaceholderData`.
- [ ] Teks pengganti rujukan: kalimat utuh atau `\ref` ke label yang ada; tanpa
      "pada subbab ini".
- [ ] Setiap pertanyaan ke user lolos pemilahan aturan 4; yang tercatat di repo,
      menunggu data, atau menunggu peristiwa tidak ditanyakan; keputusan milik
      user yang belum pernah diambil ditanyakan dengan opsi + rekomendasi.
