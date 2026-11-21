---
name: buku-ikut-proposal
description: Menyunting laporan/buku-pa, terutama Bab 1 (Latar Belakang, Permasalahan, Tujuan, Manfaat, Sistematika), dan menyusun pertanyaan atau laporan akhir ke user tentang isi buku. Dipakai saat user bilang "rapikan Bab 1", "samakan buku dengan proposal", "tambah batasan masalah", "ikuti format AFIB", "proposal sesuaikan sama buku", "tabel perubahan dari proposal", atau saat Claude hendak bertanya ke user soal rakitan uji, jumlah subjek, PCB final, atau warna sampul. Kerangka Bab 1 mengikuti proposal, proposal dibekukan, rujukan ke subbab tidak dipakai, dan pertanyaan ke user hanya untuk keputusan yang mengubah isi buku sekarang. Berlaku juga saat menulis ulang Bab 1 buku progres atau menyusun laporan akhir sesi pengerjaan buku. Edit and write buku-pa chapter one, follow the proposal outline.
---

# Buku ikut proposal

Bab 1 buku mengikuti proposal karena proposal sudah disetujui dan dibekukan; buku hanya menambah rancangan akhir dan hasil.

## Kerangka Bab 1

1. Samakan kerangka `laporan/buku-pa/bab/bab1.tex` dengan `laporan/proposal-pa/bab/bab1.tex`: Latar Belakang, Permasalahan (3 butir "Bagaimana ...?"), Tujuan (3 butir), Manfaat (3 butir), Sistematika Penulisan. Jumlah butir Permasalahan dan Tujuan tetap 3, supaya benang merah ke hasil dan kesimpulan tidak bergeser.
2. Akhiri subbab Tujuan pada daftar tujuan, tanpa kalimat sesudahnya, karena proposal tidak memilikinya.
3. Jangan menambah subbab Bab 1 yang tidak ada di proposal (Batasan Masalah, Ruang Lingkup, Kontribusi, dan sejenisnya), walau laporan acuan AFIB memilikinya. Keputusan user: Bab 1 buku mengikuti proposal.
4. Perbarui isi subbab Bab 1 (angka, sitasi, istilah) bila faktanya berubah. Yang diikuti dari proposal adalah garis besar, bukan kalimat: tiga hal yang dipermasalahkan, tiga tujuan, dan apa yang diuji (Rencana Pengujian di Bab 3). Tulis kalimat buku dengan skill `tulis-tanpa-slop`; kalimatnya tidak harus identik dengan proposal.
5. Saat mengoreksi fakta di Bab 1, pakai fakta yang sudah dibuktikan di Bab 2 beserta sumbernya, bukan klaim baru, karena Bab 1 tidak boleh membawa klaim yang tidak dibuktikan di bab sesudahnya (koreksi Bab 1 yang disetujui user).

## Proposal tidak disunting

1. Jangan menyunting `laporan/proposal-pa`, termasuk `.bib`-nya, walau buku sudah bergeser (target berangka, uji tambahan, sitasi baru). Proposal sudah diserahkan; menyuntingnya mengubah dokumen yang sudah dinilai.
2. Jangan menulis rencana suntingan proposal. Bila user meminta "sesuaikan proposal dengan buku", tolak dengan alasan itu dan tawarkan alternatifnya: buku memuat rancangan akhir di Bab 3 dan hasilnya di Bab 4.
3. Jangan membuat tabel "perubahan dari proposal" di buku; keputusan user, mengikuti buku AFIB.

## Lingkup tanpa subbab Batasan

Tulis lingkup di subbab tetap berikut, tanpa `\ref` ke subbab Bab 1 yang tidak ada:

- subjek sehat anonim, non-klinis, data primer: Bab 4 `\section{Karakteristik Data}` dan `\section{Tempat Ujicoba}`;
- klasifikasi biner, bukan alat diagnosis, daya tidak dioptimasi: Bab 4 `\subsection{Keterbatasan dan Status Proof of Concept}`;
- data latih mitdb inter-patient DS1/DS2: Bab 3 `\subsubsection{\textit{Dataset} dan Pelabelan}`.

Aturan penulisan rujukan:

1. Ganti rujukan ke subbab yang dihapus dengan kalimat utuh yang berdiri sendiri (hapus klausa "sesuai ..."), karena penunjuk ke subbab dilarang.
2. Jangan memakai penunjuk `\ref` ke bab atau subbab sama sekali; ikuti `struktur-pa` aturan 11.
3. Jangan memakai penunjuk tanpa target seperti "pada subbab ini" atau "seperti di atas", karena pembaca tidak tahu menunjuk ke mana.

## Bukti build

Setelah menyunting, jalankan dan baca keluarannya:

```bash
cd /home/mrrizaldi/dev/projek-akhir/laporan/buku-pa && make pdf-bersih
grep -cE "undefined|Overfull" output/main.log
```

Hitungan harus 0. Pakai `pdf-bersih`, bukan `make rebuild`, karena `rebuild` menghapus DOCX di `output/`.

## Pertanyaan ke user

Bertanya hanya untuk keputusan yang mengubah isi buku sekarang dan tidak bisa dijawab dari repo, karena pertanyaan yang jawabannya sudah tertulis membuang waktu user. Cari dulu di `model/CLAUDE.md`, `model/docs/` (baris "Kondisi uji" di walkthrough), `model/data/arsip/rekaman-uji-coba/README.md` (rangkaian dan pin per tanggal rekaman uji coba), dan isi buku sendiri. Pilah begini:

1. Riwayat yang sudah tercatat di repo (rakitan lama, tanggal uji, pin lama): pakai apa adanya, jangan ditanyakan.
2. Angka yang menunggu data resmi: tulis `\PlaceholderData{...}`, jangan ditanyakan.
3. Hal yang menunggu peristiwa (PCB final dicetak, rekaman resmi): catat sebagai butir `model/CLAUDE.md` §Pekerjaan terbuka, jangan ditanyakan. Di teks dan tabel buku jangan menulisnya seolah sudah terjadi: bukan "PCB final" tetapi `\PlaceholderData{rakitan final}`.
4. Keputusan milik user yang belum pernah diambil dan tidak ada jawabannya di repo (warna sampul, templat kampus, rumusan baru): tanyakan sekali dengan opsi dan rekomendasi. Keputusan ini memblok penyelesaian buku walau bab lain masih bisa ditulis; jangan memutuskannya diam-diam dengan "pakai bawaan".

## Laporan akhir ke user

1. Sebut apa yang diubah dan bukti build yang benar-benar dijalankan di sesi itu: jumlah halaman dan hasil `grep -cE "undefined|Overfull"` dari `output/main.log`.
2. Tulis "belum dijalankan" untuk perintah yang tidak dijalankan, bukan "sukses" atau "0", karena angka yang tidak diamati menyesatkan.
3. Tutup dengan hanya pertanyaan dari butir 4 bagian Pertanyaan ke user, beralasan dari fakta repo, bukan "biasanya". Tanpa pertanyaan pun boleh.

## Daftar periksa akhir

- `diff` kerangka `\section` Bab 1 buku dan proposal: sama.
- Permasalahan 3 butir, Tujuan 3 butir.
- `grep -rn "batasan-masalah" laporan/buku-pa/bab` kosong (atau label lain yang subbabnya dihapus).
- `make pdf-bersih` sukses dan hitungan `undefined|Overfull` 0, dari keluaran yang dijalankan.
- Tidak ada sel atau kalimat yang menyebut keadaan yang belum terjadi sebagai fakta; pakai `\PlaceholderData`.
- Teks pengganti rujukan: kalimat utuh, tanpa `\ref` ke bab atau subbab, tanpa "pada subbab ini".
- Setiap pertanyaan ke user lolos pemilahan di atas.
