---
name: tabel-pa
description: Wajib dipakai saat membuat, merombak, atau meninjau tabel LaTeX di laporan PA (laporan/buku-pa, progres, proposal), termasuk tabel hasil Bab 4, spesifikasi, ablasi, ketercapaian, dan pembanding penelitian terkait. Gaya tiga garis (booktabs, tanpa garis vertikal), satu tabel satu pertanyaan, angka rapi, dan paragraf pengapitnya.
---

# Tabel PA

Kegagalan yang ditangkap user (15 Okt 2026): "tabelku masih busuk". Hasil
`python3 scripts/cek_tabel.py` pada buku-pa saat itu: 0 galat format, tetapi
34 sel berisi lebih dari 20 kata (terpanjang 47 kata di kolom "Alasan dan
Acuan"), satuan `ms` diulang di setiap sel pada 7 kolom, isian samar "Sama",
"Konfigurasi sama", "Tidak diulang" di `tab:target-pipeline`, kolom INT8
bercampur 2 dan 4 desimal karena baris ukuran model ikut masuk tabel metrik,
dan `tab:hasil-ds2` menjajarkan sel *confusion matrix* (TP, FN, FP, TN) dengan
metrik (Recall, Precision) di baris yang sama padahal keduanya tidak
berhubungan. Format sudah benar. Yang busuk adalah **isi dan susunan**:
tabel dipakai sebagai wadah paragraf, dan tiap baris tidak menjawab pertanyaan
yang sama.

Keputusan gaya (user, 19 Okt 2026): tabel buku-pa memakai **gaya tiga garis**,
bukan grid penuh. Alasan user: tabel riset jarang berborder lengkap, dan buku
AFIB (Mulyawan 2026, pembimbing sama) memakai tiga garis pada Tabel 2.1 dan
4.1. Proposal yang sudah diserahkan tetap grid dan tidak disunting.

Asal aturan: diadaptasi dari skill berbahasa Inggris `table-generation`
(lingzhi227/claude-skills), `academic-writing` (David-Saeteros/claude-skills),
dan `evaluate`/`paper-validator` (minhuw/claude-writer), lalu disesuaikan
dengan Panduan Proposal PA D4TI (`laporan/proposal-pa/Panduan_Proposal_PA_D4TI/D. Bab 3.docx`)
dan `laporan/CLAUDE.md`. Yang **tidak** diambil, beserta alasannya:

| Saran skill Inggris | Keputusan | Alasan |
|---|---|---|
| `booktabs` tanpa garis vertikal | diambil (19 Okt 2026) | Keputusan user mengikuti gaya tabel riset dan buku AFIB. Panduan PENS (grid `TableGrid`, header D9D9D9) hanya dipakai proposal yang sudah dibekukan |
| tebalkan nilai terbaik di setiap kolom | dibatasi | Bab 4 menilai hasil terhadap **target**, bukan lomba. Pakai kolom Status. Tebal hanya untuk baris varian terpilih di tabel ablasi |
| baris "Ours" | diganti | baris terakhir "Penelitian ini" pada tabel pembanding (6/6 korpus) |
| `table*`, dua kolom | tidak relevan | laporan satu kolom |
| `threeparttable` untuk catatan | diganti | baris "Keterangan:" 10pt di bawah tabel, setara baris "Sumber:" di panduan, tanpa paket baru |

## Aturan

1. **Gaya tiga garis.** `\toprule` di atas header, `\midrule` di bawah
   header, `\bottomrule` di akhir tabel. Tanpa garis vertikal `|`, tanpa
   `\hline`/`\cline`, tanpa `\rowcolor`. Header tetap teks tebal. Garis
   tambahan di badan hanya `\midrule` pemisah kelompok: (a) tepat sebelum
   baris `\multicolumn` nama kelompok, tanpa garis sesudah baris itu, dan
   (b) pada tabel yang memuat `\multirow`, setiap `\hline` penuh di badan
   menjadi `\midrule` agar batas kelompok terlihat, sedangkan `\cline`
   dihapus. Selain itu `\hline` di badan dihapus tanpa pengganti. Di `longtable`,
   header berulang memakai `\toprule`/`\midrule` dan `\endfoot` memakai
   `\bottomrule`. Caption di ATAS tabel (tebal, rata
   tengah, otomatis dari `preamble.tex`), `\begin{table}[!ht]` (bukan `[H]`),
   dan "Sumber: ..." 10pt rata tengah di bawah tabel pinjaman. Bab 1 dan Bab 5
   tanpa tabel. Satu tabel tidak lebih dari satu halaman. Pengecualiannya
   tabel pembanding panjang yang memakai `longtable`
   (`laporan/CLAUDE.md` §Konvensi Tabel & Gambar).

2. **Putuskan dulu apakah perlu tabel.** Tabel hanya untuk data dengan dua
   sumbu yang dibandingkan pembaca: baris sejenis × atribut sejenis.
   - Dua sampai tiga angka saja → tulis dalam kalimat, bukan tabel.
   - Tren atas banyak titik (kurva *loss*, sebaran residu) → gambar plot dari
     pipeline repo (aturan placeholder di skill `struktur-pa` aturan 9).
   - Alasan, argumen, dan riwayat keputusan → paragraf. Sel bukan tempat
     paragraf.

3. **Satu tabel menjawab satu pertanyaan, dan setiap baris adalah objek
   sejenis.** Tulis pertanyaannya dalam satu kalimat sebelum menyusun kolom,
   mis. "Apakah setiap target *pipeline* terpenuhi?". Baris yang menjawab
   pertanyaan lain dipindah ke tabel lain atau ke kalimat. Contoh pelanggaran:
   - TP|FN|FP|TN dijajarkan dengan Recall|Precision → pecah jadi *confusion
     matrix* 2×2 dan tabel metrik (templat C dan B di `referensi/templat.md`).
   - Baris "Ukuran model (KB)" di tabel selisih metrik → pindah ke tabel
     sumber daya atau ke kalimat.

4. **Sel pendek.** Paling banyak 20 kata per sel, idealnya di bawah 12. Sel
   yang lebih panjang berarti ada alasan atau syarat yang menumpang. Pindahkan
   ke paragraf penjelas atau ke baris Keterangan. Kolom "Alasan"/"Justifikasi"
   hanya dipertahankan bila semua selnya muat dalam satu frasa.

5. **Angka.**
   - Satuan ditulis sekali: di header kolom bila satu kolom satu besaran
     (`\textbf{Latensi (ms)}`), atau di label baris bila tiap baris besaran
     berbeda (`Latensi median (ms)`). Jangan tulis `939~ms` di tiap sel.
     Nilai boleh dikonversi agar satu baris satu satuan (target "2 detik"
     menjadi `2.000` pada baris bersatuan ms), dan konversi itu disebut ke
     user sebagai perubahan tampilan, bukan perubahan angka.
   - Jumlah desimal seragam per kolom: metrik klasifikasi 4 desimal, persen 1
     desimal, latensi bilangan bulat ms. Desimal koma, ribuan titik
     (`3.813`, `0,6996`, `99,2`).
   - Kolom angka rata kanan: `>{\raggedleft\arraybackslash}p{2cm}`. Rata
     tengah hanya untuk sel status atau label pendek.
   - Rentang dan ambang memakai simbol matematika: `$\leq$ 2`, `$<$ 0{,}02`.
   - Selisih diberi tanda eksplisit: `$+$0,0108`, `$-$0,0067`.

6. **Isian kosong dan berulang punya aturan.**
   - Tidak ada nilai → `--`, lalu satu kalimat di Keterangan yang menjelaskan
     alasannya ("-- : skenario putus koneksi dijalankan sekali").
   - Dilarang "Sama", "idem", "Konfigurasi sama", "Tidak diulang", "dst".
     "Sama" yang berarti ulangan kedua memang dijalankan dan hasilnya sama
     diganti nilainya (mis. `0`). "Sama"/"Tidak diulang" yang berarti tidak
     dijalankan diganti `--` + Keterangan.
   - Nilai sama di beberapa baris berturut-turut pada kolom pertama →
     `\multirow` (paket sudah dimuat), atau baris kelompok
     `\midrule` lalu `\multicolumn{k}{l}{\textit{Nama kelompok}}`.
   - Kolom yang isinya sama di semua baris dihapus, lalu nilainya ditulis di
     caption atau Keterangan (mis. "model *window* 250").

7. **Kosakata status tetap.** Tabel target memakai Terpenuhi / Tidak
   terpenuhi / Belum diukur. Tabel ketercapaian tujuan memakai Tercapai /
   Sebagian tercapai / Belum tercapai. Tabel ablasi memakai Dipilih /
   Ditolak / Acuan, dan setiap Ditolak yang F1-nya lebih tinggi dari yang
   Dipilih wajib dijelaskan alasannya di Keterangan atau paragraf. Metrik yang
   tidak punya target di rencana pengujian diberi status "Dilaporkan", bukan
   Terpenuhi/Tidak terpenuhi, lalu dibahas di paragraf. Bila ada angka acuan
   yang bukan target (mis. "acuan 2 detik" untuk p95), tulis di kolom Target
   sebagai `acuan $\leq$ 2.000`, jangan dihapus.

8. **Lebar dihitung, bukan ditebak.** Lebar teks A4 = 14 cm, A5 = 9,8 cm.
   - Tabel float baru → `tabularx` dengan `\linewidth`, kolom teks
     `>{\RaggedRight\arraybackslash}X`, kolom angka `p{..}` rata kanan. Lebar
     total otomatis pas.
   - `longtable` (tidak bisa `tabularx`) → jumlah lebar `p{}` + 2 ×
     `\tabcolsep` × jumlah kolom ≤ lebar teks. Skrip memeriksanya (`T-LEBAR`).
   - Turunkan ukuran huruf (`\small`, lalu `\footnotesize`) hanya setelah sel
     dipendekkan. `\scriptsize` hanya untuk tabel pembanding padat.

9. **Caption.** Frasa benda tanpa titik dan tanpa kata kerja, paling banyak
   15 kata, memuat objek dan kondisi pembeda (mis. "pada DS2", "*threshold*
   0,80"). Penjelasan dalam kurung dipindah ke Keterangan. Pola per jenis:
   hasil "Hasil Pengujian {Objek} terhadap {Acuan/Target}", dua kondisi
   "Perbandingan {Metrik} {Kondisi A} dan {Kondisi B}", spesifikasi
   "Spesifikasi {Perangkat Keras/Lunak} Ujicoba", rencana "Rencana
   Pengujian {Objek}", struktur "Struktur {Payload/Tabel} {Nama}",
   ketercapaian "Ketercapaian Tujuan Penelitian", pembanding "Perbandingan
   Penelitian Terkait".

10. **Keterangan di bawah tabel**, di dalam lingkungan `table` sesudah
    `\end{tabular}`, 10pt rata kiri:
    `\par\vspace{2pt}{\footnotesize\raggedright Keterangan: ...\par}`. Isinya
    singkatan (TP, PDSR, p95, HOS), arti `--`, dan satu kalimat kondisi uji.
    Baris `\multicolumn` selebar tabel yang berisi catatan dipindah ke sini.
    Untuk tabel pinjaman, "Sumber: ..." diletakkan sesudah Keterangan.

11. **Setiap angka tertelusur.** Pertahankan praktik komentar
    `% sumber: path (nilai mentah)` sesudah tabel atau per baris. Angka hanya
    dari artefak repo (`model/artifacts/metrics/*`, walkthrough aktif, kode).
    Angka yang belum ada ditulis `\PlaceholderData{...}`, tidak pernah
    ditebak. Label kerja internal (`HW-n`, `Fase n`, tag ablasi, nama berkas)
    tidak boleh muncul di sel (`laporan/CLAUDE.md` §Larangan Label Kerja).

12. **Tabel tidak berdiri sendiri.** Paragraf pengantar merujuk tabel
    sebelum tabel muncul. Paragraf penjelas sesudahnya mengikuti skill
    `narasi-pa` aturan 1–3, yaitu temuan dulu dan tidak membaca ulang isi
    tabel. Mengganti `\label` dilarang bila sudah dirujuk di bab lain. Cek
    dengan `grep -rn "ref{tab:" laporan/buku-pa/bab`.

13. **Batas wewenang.** `laporan/` read-only tanpa konfirmasi (`CLAUDE.md`
    root). Saat diminta "rapikan tabel", tampilkan dulu rencana per tabel
    berupa pertanyaan yang dijawab, kolom baru, dan baris yang dipindah.
    Suntingan `.tex` dikerjakan sesudah user setuju, atau langsung bila user
    sudah menyebut tabel dan bab yang boleh diubah.

## Alur kerja

1. Jalankan `python3 scripts/cek_tabel.py --tanpa-prosa` (atau beri path bab).
   Catat galat dan saran per tabel.
2. Untuk tiap tabel yang disentuh, tulis pertanyaannya (aturan 3), lalu
   pilih templat dari `referensi/templat.md`:
   A target vs hasil, B pembanding dua kondisi, C *confusion matrix*,
   D ablasi, E spesifikasi, F ketercapaian tujuan, G pembanding penelitian
   terkait.
3. Susun ulang dengan aturan 4–10. Pindahkan isi yang keluar dari sel ke
   paragraf penjelas atau Keterangan, jangan dibuang.
4. Tulis atau perbarui paragraf pengantar dan penjelas (skill `narasi-pa`).
5. Kompilasi: `cd laporan/buku-pa && make pdf`, lalu
   `grep -ciE "undefined|overfull .hbox" output/main.log`. Buka halaman
   tabel di PDF dan lihat langsung.
6. Jalankan ulang `cek_tabel.py`. Laporkan ke user angka sebelum dan
   sesudah dari keluaran yang benar-benar dijalankan. Yang belum dijalankan
   ditulis "belum dijalankan".

## Daftar periksa akhir

- [ ] Setiap tabel yang disentuh punya pertanyaan satu kalimat, dan semua
      barisnya menjawab pertanyaan itu.
- [ ] `cek_tabel.py`: 0 galat. Saran `T-SEL`, `T-SATUAN`, `T-DESIMAL`,
      `T-ISIAN`, dan `T-CATATAN` untuk tabel yang disentuh sudah 0, atau ada
      alasan tertulis untuk tiap saran yang dibiarkan.
- [ ] Tiga garis (`\toprule`, `\midrule`, `\bottomrule`), tanpa `|`,
      `\hline`, dan `\rowcolor`. Caption di atas, `[!ht]`.
- [ ] Satuan di header, desimal seragam, kolom angka rata kanan.
- [ ] Tidak ada "Sama"/"idem"/"Tidak diulang". Ada `--` + Keterangan.
- [ ] Status memakai kosakata aturan 7.
- [ ] Komentar `% sumber:` ada untuk setiap angka. Tidak ada label kerja
      internal di sel.
- [ ] `make pdf` sukses, `undefined` dan `Overfull \hbox` untuk tabel yang
      disentuh 0, dari keluaran yang dijalankan.
- [ ] Label tabel lama tidak berubah, atau semua `\ref`-nya ikut diganti.
