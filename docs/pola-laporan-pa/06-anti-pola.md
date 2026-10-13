# 06 — Anti-pola: kesalahan nyata di korpus

Dokumen-dokumen ini sudah lolos sidang dan direvisi berkali-kali, tetapi masih
memuat kesalahan berikut. Daftar ini dipakai sebagai daftar periksa sebelum
laporan kita dikumpulkan. Banyak di antaranya otomatis tercegah oleh LaTeX
(penomoran, daftar isi, rujukan) asal semua gambar/tabel/persamaan memakai
`\label` dan `\ref`.

## A. Sisa versi lama

| # | Kesalahan | Lokasi | Pencegahan |
|---|---|---|---|
| A1 | Buku full masih menulis "proposal ini bertujuan untuk" | AFIB 1.4 p.25 | grep "proposal" sebelum kumpul |
| A2 | Sistematika menyebut "tiga bab utama" tetapi menjabarkan lima bab | OFFLINE p.15; CODACY p.13 | Sistematika ditulis ulang setiap ganti fase |
| A3 | Kalimat sistematika/penelitian terkait masih menyebut "proposal" di buku full | ISYARAT p.14, p.24 | sama dengan A1 |
| A4 | Tabel Jadwal dihapus, rujukannya tertinggal di 4.4 | AFIB p.102 (+ "Error! Bookmark" di daftar isi p.15) | hapus elemen bersama semua `\ref`-nya, kompilasi ulang, cek "??" |
| A5 | Teknologi lama (Firebase) masih disebut di teori, padahal sistem memakai ThingsBoard + PostgreSQL | AFIB p.41, p.42, p.47 | setiap perubahan arsitektur, grep nama teknologi lama |
| A6 | Teori dataset menjelaskan basis data aritmia umum dan kelas PVC, padahal model biner AF/Non-AF dari AFDB | AFIB 2.2.14 p.47–48 | teori dataset = dataset yang benar-benar dipakai |
| A7 | Frasa progres ("akan disempurnakan pada sprint berikutnya") tertinggal di buku full | AFIB 4.6.4 p.116 | grep "sprint berikutnya", "tahap progres", "fase berikutnya" saat transformasi ke buku |
| A8 | Kalimat Bab 3 "kolaborasi belum dilakukan secara resmi" tetap ada meski Bab 4 melaporkan validasi lapangan | ISYARAT p.40 vs p.85–87 | sinkronkan status antara Bab 3 dan Bab 4 |

## B. Navigasi dan penomoran

| # | Kesalahan | Lokasi | Pencegahan |
|---|---|---|---|
| B1 | "Error! Bookmark not defined." di Daftar Isi, Daftar Gambar, Daftar Tabel | AFIB p.15–19 | LaTeX: kompilasi penuh, tidak ada warning "undefined reference" |
| B2 | Nomor tabel ganda (dua Tabel 4.1, dua Tabel 4.2) | AFIB p.100–103 | caption otomatis |
| B3 | Nomor tabel ganda (dua Tabel 4.4) | GDD p.53, p.74 | caption otomatis |
| B4 | Nomor persamaan ganda ((4.1) dan (4.2) dua kali) | AFIB p.110, p.112, p.117 | `equation` + `\label` |
| B5 | Penomoran gambar melompat (3.1 → 3.3) | CODACY p.7, p.33–34 | caption otomatis |
| B6 | Daftar isi berantakan: 2.1.x di bawah 2.2, subbab Bab 4 tanpa nomor, 4.6.4 tanpa 4.6.3 | CODACY p.5–6 | `\section`/`\subsection` bernomor, jangan ketik manual |
| B7 | Judul subbab salah: 3.1 berjudul "Deskripsi Permasalahan" padahal isinya solusi | GDD p.35 | cocokkan dengan kerangka 02 |
| B8 | Judul subbab salah: 4.7.5 "Tahap Framework" berisi rekomendasi | GDD p.81–82 | baca ulang setiap judul vs isi |
| B9 | Caption salah: tabel "sesudah refactoring" diberi judul "Sebelum Refactoring" | CODACY Tabel 4.2 p.51 | caption ditulis setelah isi tabel final |
| B10 | Tabel spesifikasi HW berisi komponen perangkat lunak dan sebaliknya | GDD Tabel 4.1–4.2 p.47–48 | satu tabel = satu kategori |
| B11 | Teks merujuk nomor gambar yang salah | ISYARAT p.66 ("gambar 4.1" untuk 4.7); BYOM p.47 ("Gambar 4.4" untuk Swagger yang 4.3) | selalu `\ref`, tidak mengetik nomor |
| B12 | "Tabel 4.8 diatas" padahal tabel muncul sesudahnya | AFIB p.121 | pengantar sebelum, penjelas sesudah (pola sandwich) |
| B13 | Salah ketik judul baku: "KARATERISTIK", "EKSPERMEN" | AFIB, CODACY, BYOM daftar isi | salin judul dari kerangka 02 |
| B14 | Jumlah yang disebut tidak cocok dengan daftar ("tiga halaman utama" lalu empat disebut) | ISYARAT p.51 | hitung ulang setiap kali menulis "dua/tiga/empat ..." |

## C. Sitasi dan pustaka

| # | Kesalahan | Lokasi | Pencegahan |
|---|---|---|---|
| C1 | Nomor sitasi di teks bergeser dari daftar pustaka (mis. Mayo [7] di teks = [8] di daftar; [17] dipakai untuk dua sumber berbeda; teks sampai [26], daftar hanya 23) | AFIB p.29–65 vs p.131–133 | BibTeX + `~\cite{key}`, tidak menomori manual |
| C2 | Satu nomor dipakai untuk dua paper berbeda | CODACY [17] p.25–26 | sama dengan C1 |
| C3 | Gaya sitasi campur (penulis-tahun di teks, daftar bernomor) | ISYARAT | satu gaya: IEEE numerik |
| C4 | Sumber lemah (blog, tutorial, situs berita populer) untuk klaim teori | AFIB p.131–132; ISYARAT p.93–94 | utamakan jurnal/prosiding/datasheet/dokumentasi resmi |
| C5 | Angka akurasi metode alternatif tanpa sitasi | AFIB 2.2.15 p.48–50 | setiap angka dari literatur wajib `\cite` |
| C6 | NIP dua pembimbing identik di sampul | GDD p.1 | cek data identitas dari sumber resmi |

## D. Isi dan logika

| # | Kesalahan | Lokasi | Pencegahan |
|---|---|---|---|
| D1 | Klaim "seluruh tujuan tercapai" padahal dua target tidak diukur dengan metrik yang dijanjikan (MAE RR, sensitivitas/spesifisitas) | AFIB 5.1 p.128 vs 1.4 p.25 | tabel ketercapaian per tujuan (lihat 02 §8) |
| D2 | Manfaat mengklaim "telah divalidasi oleh ahli medis" padahal Batasan menyatakan tanpa supervisi tenaga medis | AFIB 1.5.1 p.26 vs 1.3 f p.25 | Manfaat tidak boleh melampaui Batasan |
| D3 | Angka tidak konsisten di satu subbab (tabel 19 paket, teks 10 paket) | AFIB p.118 | angka teks diambil dari tabel, bukan diketik ulang |
| D4 | Data contoh tidak masuk akal secara fisiologis (Mean RR 2,86 ms) dan label sumber data berubah antartabel (ID sama: "IoT" di Tabel 4.2, "MIT-BIH" di Tabel 4.8) | AFIB p.101 vs p.121 | cek kewajaran angka (rentang fisik) dan konsistensi ID |
| D5 | Deskripsi confusion matrix kabur ("kurang lebih 4.000") | AFIB p.120 | tulis angka TP/TN/FP/FN persis + metrik turunannya |
| D6 | Definisi metrik keliru (Reliability diberi definisi efisiensi, Testability diberi definisi fleksibilitas, pengantar Product Operation memakai kalimat Product Transition) | GDD 2.2.5 p.26–27 | definisi teori dicek ke sumber primer |
| D7 | Klaim kesimpulan tidak cocok dengan analisis ("7 dari 10 heuristik" vs 4 kategori di 4.7.3) | GDD p.83 vs p.79–80 | kesimpulan hanya mengutip angka yang ada di Bab 4 |
| D8 | Label kolom salah satuan ("Average Engine Time (s)" berisi total runtime) | BYOM Tabel 4.1 p.52 | nama kolom = definisi metrik di 4.1 |
| D9 | Metrik klasifikasi dipakai pada skenario yang membuat recall pasti 100% (semua kata selalu menghasilkan gesture), sehingga metrik kehilangan makna | ISYARAT p.62–84 | pilih metrik yang bisa gagal; jelaskan definisi TP/FP untuk kasusnya |
| D10 | Uji yang direncanakan di Bab 3 tidak dilaporkan di Bab 4 (uji beban 9 aliran video) | BYOM 3.2.8 p.38 | setiap rencana uji muncul di 4.6 atau disebut eksplisit belum dilakukan + alasan |
| D11 | Kata kerja terbalik ("penurunan Grade dari E menjadi A") | CODACY p.59 | baca ulang kalimat angka |
| D12 | Halaman pengesahan masih templat ("Nama Mahasiswa", "tgl bln 20xx") | AFIB p.3, p.6 | front matter final diisi terakhir, dicek terpisah |

## E. Gaya

| # | Kesalahan | Lokasi | Pencegahan |
|---|---|---|---|
| E1 | Paragraf penjelas gambar hanya mengulang caption | AFIB 2.2.6–2.2.13 | P10 di 03: baca isi gambar |
| E2 | Paragraf dobel (paragraf yang sama ditempel dua kali) | OFFLINE 2.3.7 p.40–41 | baca ulang per subbab |
| E3 | Dua butir manfaat dengan judul sama | OFFLINE 1.4 p.15 | — |
| E4 | Kalimat > 40 kata dengan definisi aposisi bertumpuk | OFFLINE Bab 1 | definisi panjang jadi kalimat sendiri |
| E5 | Desimal titik dan koma bercampur | AFIB, BYOM | desimal koma |
| E6 | Subbab teori untuk alat bantu (IDE, editor kode) tanpa nilai argumen | AFIB 2.2.11, 2.2.13 | teori hanya yang menopang keputusan desain |
| E7 | "Uji coba" dan "ujicoba" bergantian | beberapa dokumen | ikuti judul baku Bab 4 ("Ujicoba") dan konsisten |

## F. Daftar periksa sebelum kumpul (ringkas)

1. `make pdf` bersih: tanpa "undefined reference", tanpa "??", tanpa
   "multiply defined labels".
2. `grep -rni "proposal\|tahap progres\|sprint berikutnya\|fase berikutnya" laporan/<projek>/bab`
   dan putuskan tiap kemunculan (wajar di progres, tidak wajar di buku full).
3. `grep -rn "PLACEHOLDER-GAMBAR" laporan/<projek>` untuk melihat gambar yang
   masih harus dibuat.
4. Setiap Tujuan punya angka di 4.6, vonis di 4.7, kalimat di 5.1 (02 §8).
5. Angka abstrak = angka Bab 4 = angka Bab 5.
6. Manfaat dan kesimpulan tidak melampaui Batasan.
7. Setiap angka literatur bersitasi, setiap sitasi lewat BibTeX.
8. Setiap gambar/tabel: dirujuk sebelum, dijelaskan sesudah.
9. Sistematika Penulisan cocok dengan isi bab yang benar-benar ada.
10. Data identitas (nama, NRP, NIP, tahun) dicek ke sumber resmi.
