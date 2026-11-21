---
name: tulis-tanpa-slop
description: Lapisan repo PA untuk menyunting atau menulis paragraf laporan PA (laporan/progres-pa-1, laporan/buku-pa) supaya tidak terbaca sebagai tulisan AI. Pakai saat user mengetik "rapikan biar tidak AI slop", "humanize", "bersihkan gaya tulis", "sunting bab 3", "rapikan narasi", "perbaiki paragraf penjelas tabel", "review bab", "polish this chapter", atau meminta paragraf pengantar dan penjelas tabel hasil Bab 4. Memuat skill user indonesian-antislop-writing lebih dulu, lalu menambahkan aturan rumah laporan/CLAUDE.md, bentuk paragraf penjelas tabel (temuan, bukti, makna), klaim sebanding bukti, prosedur dari folder buku dengan make pdf-bersih, dan pembungkus scripts/cek_slop.py.
---

# Tulis tanpa slop (lapisan PA)

Muat skill user `indonesian-antislop-writing` lebih dulu; skill ini hanya menambah hal khusus repo PA. Pola, prinsip, daftar "yang bukan slop", dan syarat invarian (angka, `\cite`, `\ref`, `\label`, klaim, tabel) ada di skill itu dan tidak diulang di sini.

## Lingkup suntingan

1. Sunting hanya bab yang diminta user. Gaya ini baru diuji di `laporan/progres-pa-1/bab/bab2.tex` sampai `bab4.tex`; memperluasnya ke Bab 1, Bab 5, bagian depan (abstrak dan lain-lain), atau `laporan/buku-pa` menunggu keputusan user, dan permintaan eksplisit user untuk salah satunya adalah keputusan itu. Temuan di bab lain dilaporkan, tidak disunting.
2. `laporan/proposal-pa` dibekukan dan tidak disentuh.
3. Kalimat yang butuh fakta pengganti tetapi faktanya tidak ada di naskah dibiarkan dan dilaporkan ke user, karena angka tidak boleh dikarang.

## Aturan rumah yang menang atas saran sumber

Sumber di skill user boleh menyarankan hal yang bertentangan dengan `laporan/CLAUDE.md`; di PA aturan berikut berlaku.

1. Paragraf tanpa titik dua, titik koma, dan em dash, serta tanpa numbering inline. Ganti dengan konjungsi, koma, kurung, atau kalimat baru, karena `laporan/CLAUDE.md` melarangnya; `cek_tabel.py` N-GAYA menandai titik koma dan em dash, sedangkan titik dua dicek manual.
2. Istilah teknis Inggris dimiringkan (`\textit{board}`), daftar kata adopsi tetap tegak, dan padanan Indonesia tidak dipakai.
3. Desimal koma (0,6594), ribuan titik (85.812), `~\cite{}`, dan judul Title Case.
4. Tanpa "kami", "kita", "saya": `S-PERSONA` diperlakukan sebagai galat di laporan PA, bukan sekadar tinjau.
5. Tanpa koma sebelum "sehingga" (EYD V; galat `S-KOMA-SEHINGGA`), karena induk kalimat di depan anak kalimat tidak berkoma.
6. Label internal repo tidak tercetak di teks laporan: HW-n, Fase n, Task n, T-n/K-n, rev1/rev2, path berkas, nama skrip, nama env (`PA_*`), dan kata "walkthrough". Sebut isinya dengan istilah umum. Komentar `% sumber:` tidak tercetak sehingga boleh memuat path.
7. Tanpa pembuka meta ("Subbab ini membahas ...") dan tanpa label bernomor "Tujuan N" di judul atau kalimat; kerangka bab ada di skill `struktur-pa`.

## Paragraf dan benang merah

Berlaku untuk semua paragraf, bukan hanya penjelas tabel.

1. **Satu paragraf satu fungsi, 60 sampai 150 kata.** Hasil (4.6), mekanisme (4.7 atau Bab 3), keputusan rancangan, dan keterbatasan tidak dicampur; paragraf di atas 180 kata dipecah per fungsi. Kalimat pertama setiap paragraf menyatakan klaim utama sesuai fungsinya (temuan untuk hasil, pernyataan mekanisme untuk mekanisme, keputusan untuk keputusan), bukan rincian atau pengantar. Uji cepat: paragraf harus bisa diberi judul tiga sampai lima kata tanpa "dan".
2. **Benang merah.** Butir hasil 4.6 ditutup kalimat bahwa target rencana Bab 3 terpenuhi atau tidak; 4.7 menjawab mengapa dan apa artinya tanpa mengulang angka 4.6 kecuali sebagai rujukan; Bab 5 tanpa angka baru (`struktur-pa` aturan 3 dan 6).

Contoh pemecahan kalimat 50 kata (rantai sebab-akibat) tanpa kehilangan hubungannya:

```latex
Deteksi berjalan tiap 1 detik atas \textit{ring} 4 detik, dan detak yang
ditemukan baru boleh keluar 128 sampel atau 356~ms sesudah puncak R.
Akibatnya, penundaan di sisi perangkat berada di antara 356 dan 1.356~ms.
```

## Paragraf penjelas tabel dan gambar

Bentuk paragraf ini khusus laporan PA dan tidak ditangkap pola generik.

1. **Temuan, bukti, makna.** Kalimat pertama adalah temuan utama dengan rujukan `Tabel~\ref{}` di dalam kalimat atau di kurung akhir. Bukti memuat paling banyak lima angka seluruh paragraf, dan setiap angka di paragraf ikut dihitung, termasuk target, ambang, selisih, dan angka kondisi uji (jumlah ulangan, jumlah sampel). Metrik tanpa target (mis. p95) tetap di tabel, tidak masuk paragraf. Pilih angka tabel yang paling menentukan, dan tiap angka dibandingkan dengan target, acuan, atau kondisi lain, atau dijelaskan sebabnya; angka tanpa pembanding adalah transkripsi ("F1 naik 0,0010" saja salah, "F1 naik 0,0010, jauh di bawah ambang 0,02" benar), dan angka yang tidak bisa diberi pembanding dibuang. Hitung angkanya sebelum menyerahkan dan tulis jumlahnya dengan benar. Kalimat penutup mengaitkan temuan ke target atau keputusan rancangan. Boleh ditambah satu sampai dua kalimat anomali atau keterbatasan; bila lebih panjang, jadikan paragraf sendiri.
2. **Jangan membaca ulang tabel.** Paragraf mengulang paling banyak setengah angka tabel. Bila paragraf harus menyusuri tiap baris agar bermakna, desain tabelnya yang diperbaiki lewat skill `tabel-pa`.
3. **Pembuka bervariasi.** "Berdasarkan Tabel" dan "Tabel~\ref{..} memperlihatkan/menunjukkan" dihitung bersama, paling banyak tiga kali per bab dan tidak pada dua penjelas berurutan. Pilih pembuka dari isi: temuan langsung ("Seluruh target pengiriman terpenuhi pada kedua ulangan (Tabel~\ref{..})."), perbandingan ("Dibandingkan {acuan}, {objek} naik {besaran}"), pengecualian ("Seluruh selisih berada di bawah ambang kecuali {metrik}"), atau lanjutan paragraf sebelumnya.
4. **Baris `% sumber:`** dipindah bersama kalimatnya saat kalimat dipindah atau dipecah.

## Klaim sebanding bukti

Skill user menandai kata mutlak dan "signifikan"; di PA kekuatan klaim juga mengikuti desain ujinya.

1. Satu pengukuran pada satu kondisi memakai "menunjukkan" atau "terukur"; "konsisten" butuh minimal dua ulangan atau tiga *seed*; "terbukti" atau "setara" butuh seluruh lingkup klaim diuji; hal yang hanya disimpulkan dari mekanisme memakai "diperkirakan" atau "diduga".
2. "Signifikan" tanpa uji statistik diganti "bermakna di atas ambang {nilai}" atau "selisih {nilai}".
3. Sebab-akibat hanya dari ablasi terkendali (satu pengaturan diubah, minimal tiga *seed*); pengamatan bersamaan ditulis "bertepatan dengan" atau "diikuti", bukan "menyebabkan".
4. Kondisi uji menempel pada klaim: sumber sinyal *replay* atau sinyal tubuh, jumlah ulangan, dan data uji (DS2). Klaim tentang sinyal tubuh tidak boleh berdasar uji *replay*.
5. Metrik tanpa target (misalnya p95) tidak diposisikan terhadap ambang metrik lain; bila ada angka acuan, sebut sebagai acuan, bukan target. Di dalam paragraf penjelas tabel, metrik tanpa target tetap di tabel dan tidak dilaporkan di paragraf (butir 1 bagian Paragraf penjelas).
6. Hal yang belum diukur ditulis "belum diukur" atau `\PlaceholderData{...}`, tidak pernah dalam bentuk lampau, karena klaim lampau atas hal yang belum terjadi adalah klaim palsu. Register rancangan (Bab 3) dan capaian (Bab 4 dan 5) ada di `struktur-pa` aturan 4.

## Istilah dan singkatan

Satu konsep satu istilah di seluruh buku. Sebelum memperkenalkan istilah, cek `grep -rn "istilah" laporan/buku-pa/bab`. Singkatan didefinisikan saat pertama muncul di tiap bab (PDSR, AUC, p95, ISR).

## Prosedur

Jalankan dari folder buku yang disunting. Pembungkus `scripts/cek_slop.py` meneruskan ke pemeriksa skill user (`--ringkas` = `--summary`, `--banding` = `--compare`, `--uji` = `--self-test`) dan memberi pesan jelas bila skill user tidak terpasang.

```bash
cd laporan/progres-pa-1
cp bab/bab3.tex /tmp/bab3.lama.tex
python3 ../../scripts/cek_slop.py --ringkas bab/bab3.tex
python3 ../../scripts/cek_slop.py bab/bab3.tex
python3 ../../scripts/cek_slop.py --banding /tmp/bab3.lama.tex bab/bab3.tex
python3 ../../scripts/cek_tabel.py bab/*.tex
python3 ../../scripts/cek_slop.py --ringkas bab/bab3.tex
make pdf-bersih
grep -cE "undefined|Overfull" output/main.log
```

Hasil yang diharapkan: pemeriksa mencetak `errors` dan `review`; `errors` 0 dan `S-PERSONA` di keluaran 0 walau levelnya `review`, tinjau turun dan sisanya disengaja, `invarian aman`, `cek_tabel` 0 galat, log 0. `make pdf-bersih` dipakai untuk bukti karena `make rebuild` menghapus DOCX di `output/`. Satu bab per commit, dan pesan commit memuat metrik `--ringkas` sebelum dan sesudah. Untuk `laporan/buku-pa`, ganti folder kerja; prosedurnya sama.

## Daftar periksa tambahan

- [ ] Penjelas tabel yang disentuh: dibuka temuan, paling banyak lima angka yang dibandingkan atau dijelaskan, ditutup makna.
- [ ] `cek_tabel.py`: `N-PEMBUKA`, `N-ULANG`, `N-PANJANG` untuk paragraf yang disentuh 0; `N-KALIMAT` dan `N-SEHINGGA` per bab turun, dengan angka dari keluaran yang dijalankan.
- [ ] Tanpa persona, titik dua, titik koma, em dash, dan label internal di paragraf.
- [ ] Kondisi uji menempel pada setiap klaim hasil.
- [ ] Hanya bab yang diminta yang berubah; `git diff --stat` dicek.
