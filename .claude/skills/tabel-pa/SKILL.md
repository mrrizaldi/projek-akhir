---
name: tabel-pa
description: Membuat, merombak, atau meninjau tabel LaTeX di laporan PA (laporan/buku-pa, progres-pa-1), termasuk tabel hasil Bab 4, spesifikasi, ablasi, ketercapaian tujuan, dan pembanding penelitian terkait. Pakai setiap kali user bilang "rapikan tabel", "tabelnya jelek", "ubah ke tiga garis", "booktabs", "buat tabel hasil", "tabel pembanding", "tabel terlalu penuh", "sel terlalu panjang", atau "fix this table"; juga saat menulis paragraf pengantar dan penjelas di sekitar tabel. Mengatur gaya tiga garis tanpa garis vertikal, satu tabel satu pertanyaan, sel pendek, angka dan satuan rapi, kosakata status tetap, keterangan di bawah tabel, dan pemeriksaan dengan cek_tabel.py.
---

# Tabel PA

Tabel yang benar secara format masih bisa buruk bila dipakai sebagai wadah paragraf atau bila barisnya tidak menjawab pertanyaan yang sama. Skill ini mengatur isi dan susunan tabel, bukan hanya garisnya.

## Keputusan gaya

- Tabel buku-pa memakai gaya tiga garis (`booktabs`), bukan grid penuh. Alasannya, tabel riset jarang berborder lengkap dan buku AFIB (pembimbing sama) memakai tiga garis.
- Tabel Perbandingan Penelitian Terkait (`tab:perbandingan-penelitian`) satu-satunya pengecualian: grid tertutup polos. Daftar pengecualian ada di `TABEL_GRID_PENUH` pada `scripts/cek_tabel.py`.
- `laporan/proposal-pa` dibekukan dan tetap grid; jangan disunting.
- Saran dari skill penulisan berbahasa Inggris yang tidak dipakai: menebalkan nilai terbaik di setiap kolom (Bab 4 menilai terhadap target, bukan lomba; tebal hanya untuk varian terpilih di tabel ablasi), baris "Ours" (diganti baris terakhir "Penelitian ini"), `table*` dua kolom (laporan satu kolom), dan `threeparttable` (diganti baris Keterangan tanpa paket baru).

## Aturan

1. **Pakai tiga garis.** `\toprule` di atas header, `\midrule` di bawah header, `\bottomrule` di akhir. Tanpa `|`, `\hline`, `\cline`, dan `\rowcolor`. Header tebal. Alasannya satu bentuk di seluruh buku.
   - Garis tambahan di badan hanya `\midrule` pemisah kelompok: tepat sebelum baris `\multicolumn` nama kelompok (tanpa garis sesudahnya), dan pada tabel ber-`\multirow` setiap `\hline` penuh menjadi `\midrule` sementara `\cline` dihapus. `\hline` lain di badan dihapus tanpa pengganti.
   - Di `longtable`, header berulang memakai `\toprule`/`\midrule` dan `\endfoot` memakai `\bottomrule`.
   - `tab:perbandingan-penelitian` memakai `|` di spesifikasi kolom dan `\hline` sesudah header (di `\endfirsthead` dan `\endhead`) serta sesudah setiap baris, tanpa booktabs, `\rowcolor`, atau warna.

2. **Tata letak.** Caption di atas tabel (tebal, rata tengah, otomatis dari `preamble.tex`), `\begin{table}[!ht]` bukan `[H]`, dan "Sumber: ..." 10pt rata tengah di bawah tabel pinjaman. Satu tabel tidak melewati satu halaman, kecuali tabel pembanding panjang berupa `longtable` (`laporan/CLAUDE.md` §Konvensi Tabel & Gambar). Bab 1 dan Bab 5 tanpa tabel, karena keduanya naratif.

3. **Putuskan dulu apakah perlu tabel.** Tabel hanya untuk dua sumbu yang dibandingkan pembaca, yaitu baris sejenis dan atribut sejenis.
   - Dua sampai tiga angka: tulis dalam kalimat.
   - Tren atas banyak titik (kurva *loss*, sebaran residu): gambar plot dari pipeline repo (placeholder diatur skill `struktur-pa` aturan 9).
   - Alasan, argumen, dan riwayat keputusan: paragraf, karena sel bukan tempat paragraf.

4. **Satu tabel menjawab satu pertanyaan, dan setiap baris adalah objek sejenis.** Tulis pertanyaannya dalam satu kalimat sebelum menyusun kolom, mis. "Apakah setiap target *pipeline* terpenuhi?". Baris yang menjawab pertanyaan lain pindah ke tabel lain atau ke kalimat. Contoh pelanggaran: TP/FN/FP/TN dijajarkan dengan Recall/Precision (pecah jadi *confusion matrix* 2×2 dan tabel metrik, templat C dan B di `referensi/templat.md`), atau baris "Ukuran model (KB)" di tabel selisih metrik (pindah ke tabel sumber daya atau kalimat).

5. **Sel pendek.** Paling banyak 20 kata per sel, idealnya di bawah 12, karena sel panjang berarti ada alasan atau syarat yang menumpang. Pindahkan ke paragraf penjelas atau baris Keterangan, jangan dibuang. Kolom "Alasan" atau "Justifikasi" hanya dipertahankan bila semua selnya muat satu frasa.

6. **Angka.**
   - Tulis satuan sekali: di header kolom bila satu kolom satu besaran (`\textbf{Latensi (ms)}`), atau di label baris bila besaran tiap baris berbeda. Jangan tulis `939~ms` di tiap sel.
   - Nilai boleh dikonversi agar satu baris satu satuan (target "2 detik" menjadi `2.000` pada baris ms). Sebut ke user bahwa itu perubahan tampilan, bukan perubahan angka.
   - Desimal seragam per kolom: metrik klasifikasi 4 desimal, persen 1 desimal, latensi bilangan bulat ms. Desimal koma, ribuan titik (`3.813`, `0,6996`, `99,2`).
   - Kolom angka rata kanan: `>{\raggedleft\arraybackslash}p{2cm}`. Rata tengah hanya untuk status atau label pendek.
   - Rentang dan ambang memakai simbol matematika (`$\leq$ 2`, `$<$ 0{,}02`); selisih bertanda eksplisit (`$+$0,0108`, `$-$0,0067`).

7. **Isian kosong dan berulang.**
   - Tidak ada nilai: tulis `--`, lalu jelaskan alasannya satu kalimat di Keterangan ("-- : skenario putus koneksi dijalankan sekali").
   - Jangan tulis "Sama", "idem", "Konfigurasi sama", "Tidak diulang", "dst", karena pembaca tak tahu apakah itu terukur atau tidak dijalankan. Ulangan yang memang dijalankan dan hasilnya sama ditulis nilainya (mis. `0`); yang tidak dijalankan ditulis `--` plus Keterangan.
   - Nilai sama berturut-turut di kolom pertama: pakai `\multirow` (paket sudah dimuat), atau baris kelompok `\midrule` lalu `\multicolumn{k}{l}{\textit{Nama kelompok}}`.
   - Kolom yang isinya sama di semua baris dihapus; nilainya masuk caption atau Keterangan (mis. "model *window* 250").

8. **Kosakata status tetap.**
   - Tabel target: Terpenuhi / Tidak terpenuhi / Belum diukur.
   - Tabel ketercapaian tujuan: Tercapai / Sebagian tercapai / Belum tercapai.
   - Tabel ablasi: Dipilih / Ditolak / Acuan. Setiap Ditolak yang F1-nya lebih tinggi dari Dipilih dijelaskan alasannya di Keterangan atau paragraf.
   - Metrik tanpa target di rencana pengujian: "Dilaporkan", lalu dibahas di paragraf.
   - Angka acuan yang bukan target (mis. acuan 2 detik untuk p95) tetap ditulis di kolom Target sebagai `acuan $\leq$ 2.000`.

9. **Hitung lebar, jangan menebak.** Lebar teks A4 = 14 cm, A5 = 9,8 cm.
   - Tabel float baru: `tabularx` dengan `\linewidth`, kolom teks `>{\RaggedRight\arraybackslash}X`, kolom angka `p{..}` rata kanan, supaya total pas.
   - `longtable` (tak bisa `tabularx`): jumlah lebar `p{}` + 2 × `\tabcolsep` × jumlah kolom ≤ lebar teks; `cek_tabel.py` memeriksanya (`T-LEBAR`).
   - Turunkan huruf (`\small`, lalu `\footnotesize`) hanya setelah sel dipendekkan. `\scriptsize` hanya untuk tabel pembanding padat.

10. **Caption berupa frasa benda.** Tanpa titik dan kata kerja, paling banyak 15 kata, memuat objek dan kondisi pembeda (mis. "pada DS2", "*threshold* 0,80"); penjelasan dalam kurung pindah ke Keterangan. Pola:
    - hasil: "Hasil Pengujian {Objek} terhadap {Acuan/Target}"
    - dua kondisi: "Perbandingan {Metrik} {Kondisi A} dan {Kondisi B}"
    - spesifikasi: "Spesifikasi {Perangkat Keras/Lunak} Ujicoba"
    - rencana: "Rencana Pengujian {Objek}"
    - struktur: "Struktur {Payload/Tabel} {Nama}"
    - ketercapaian: "Ketercapaian Tujuan Penelitian"
    - pembanding: "Perbandingan Penelitian Terkait"

11. **Keterangan di bawah tabel**, di dalam `table` sesudah `\end{tabular}`, 10pt rata kiri: `\par\vspace{2pt}{\footnotesize\raggedright Keterangan: ...\par}`. Isinya singkatan (TP, PDSR, p95, HOS), arti `--`, dan satu kalimat kondisi uji. Baris `\multicolumn` selebar tabel berisi catatan pindah ke sini. "Sumber: ..." untuk tabel pinjaman diletakkan sesudah Keterangan.

12. **Setiap angka tertelusur.** Beri komentar LaTeX `% sumber: path (nilai mentah)` sesudah tabel atau per baris (komentar `.tex` tidak dicetak). Angka hanya dari artefak repo (`model/artifacts/metrics/*`, walkthrough aktif, kode). Angka yang belum ada ditulis `\PlaceholderData{...}`, tidak pernah ditebak. Label kerja internal (`HW-n`, `Fase n`, tag ablasi, nama berkas) tidak boleh muncul di sel (`laporan/CLAUDE.md` §Larangan Label Kerja).

13. **Tabel tidak berdiri sendiri.** Paragraf pengantar merujuk tabel sebelum tabel muncul. Paragraf penjelas sesudahnya mengikuti bagian "Paragraf penjelas" di skill `tulis-tanpa-slop` (temuan dulu, tidak membaca ulang isi tabel). Jangan ganti `\label` yang sudah dirujuk di bab lain; cek dengan `grep -rn "ref{tab:" laporan/buku-pa/bab`.

14. **Batas wewenang.** `laporan/` read-only tanpa konfirmasi (`CLAUDE.md` root). Untuk permintaan umum seperti "rapikan tabel Bab 4", tampilkan dulu rencana per tabel (pertanyaan yang dijawab, kolom baru, baris yang dipindah) dan sunting `.tex` sesudah user setuju. Bila user sudah menyebut tabel dan bab yang boleh diubah, langsung kerjakan.

## Alur kerja

1. Jalankan `cd laporan/buku-pa && python3 ../../scripts/cek_tabel.py bab/*.tex` dan catat galat dan saran per tabel. Atau dari root repo: `python3 scripts/cek_tabel.py --tanpa-prosa`.
2. Untuk tiap tabel yang disentuh, tulis pertanyaannya (aturan 4), lalu pilih templat dari `referensi/templat.md`: A target vs hasil, B pembanding dua kondisi, C *confusion matrix*, D ablasi, E spesifikasi, F ketercapaian tujuan, G pembanding penelitian terkait.
3. Susun ulang dengan aturan 5–11. Isi yang keluar dari sel dipindah ke paragraf penjelas atau Keterangan.
4. Tulis atau perbarui paragraf pengantar dan penjelas dengan skill `tulis-tanpa-slop`.
5. Bangun dan periksa:
   ```bash
   cd laporan/buku-pa && make pdf-bersih
   grep -cE "undefined|Overfull" output/main.log
   ```
   Hasil yang diharapkan: 0 untuk tabel yang disentuh. Buka halaman tabel di PDF dan lihat langsung. Jangan pakai `make rebuild`, karena menghapus DOCX di `output/`.
6. Jalankan ulang `cek_tabel.py`. Laporkan angka sebelum dan sesudah dari keluaran yang benar-benar dijalankan; yang belum dijalankan ditulis "belum dijalankan".

## Daftar periksa akhir

- Setiap tabel yang disentuh punya pertanyaan satu kalimat, dan semua barisnya menjawabnya.
- `cek_tabel.py` 0 galat; saran `T-SEL`, `T-SATUAN`, `T-DESIMAL`, `T-ISIAN`, `T-CATATAN` untuk tabel yang disentuh 0, atau tiap saran yang dibiarkan punya alasan tertulis.
- Tiga garis tanpa `|`, `\hline`, `\rowcolor` (kecuali `tab:perbandingan-penelitian`); caption di atas, `[!ht]`.
- Satuan di header, desimal seragam, kolom angka rata kanan.
- Tidak ada "Sama"/"idem"/"Tidak diulang"; ada `--` plus Keterangan.
- Status memakai kosakata aturan 8.
- `% sumber:` ada untuk setiap angka; tanpa label kerja internal di sel.
- `make pdf-bersih` sukses dan `grep -cE "undefined|Overfull" output/main.log` untuk tabel yang disentuh 0, dari keluaran yang dijalankan.
- Label tabel lama tidak berubah, atau semua `\ref`-nya ikut diganti.
