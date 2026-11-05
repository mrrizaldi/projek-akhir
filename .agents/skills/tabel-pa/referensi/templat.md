# Templat tabel PA (gaya tiga garis)

Semua templat memakai blok dasar yang sama dengan tabel yang sudah ada di
`laporan/buku-pa/bab/bab4.tex`. Contoh angka diambil dari buku-pa per 15 Okt
2026 hanya sebagai ilustrasi bentuk. Saat dipakai, salin angkanya ulang dari
artefak (`% sumber:`), bukan dari berkas ini.

## Blok dasar

```latex
Pengantar yang merujuk Tabel~\ref{tab:slug} sebelum tabel muncul.

\begin{table}[!ht]
  \centering
  \caption{Frasa benda tanpa titik}
  \label{tab:slug}
  \setstretch{1.0}
  \setlength{\tabcolsep}{4pt}
  \renewcommand{\arraystretch}{1.15}
  \small
  \begin{tabularx}{\linewidth}{>{\RaggedRight\arraybackslash}X>{\raggedleft\arraybackslash}p{2.2cm}>{\centering\arraybackslash}p{2.4cm}}
    \toprule
    \textbf{Kolom teks} & \textbf{Angka (satuan)} & \textbf{Status} \\
    \midrule
    ... & ... & ... \\
    \bottomrule
  \end{tabularx}
  \par\vspace{2pt}{\footnotesize\raggedright Keterangan: singkatan, arti --, kondisi uji.\par}
\end{table}
% sumber: path artefak (nilai mentah)

Paragraf penjelas (skill narasi-pa): temuan dulu, lalu makna terhadap target.
```

Catatan:
- Kolom teks `X` mengambil sisa lebar sehingga total pas `\linewidth`. Bila
  ada dua kolom `X`, keduanya mendapat lebar sama.
- Kolom angka `p{..}` rata kanan. Lebar secukupnya untuk angka terpanjang +
  header.
- `longtable` tidak bisa memakai `X`. Hitung lebar `p{}` manual (aturan 8),
  ulangi header dengan `\endfirsthead`/`\endhead`, dan `\endfoot` cukup
  `\bottomrule`.

---

## A. Target vs hasil

Pertanyaan: "Apakah setiap target terpenuhi?" Satu baris = satu metrik.
Satuan ada di label baris karena besarannya berbeda per baris.

Sebelum (`tab:target-pipeline`): satuan di tiap sel, isian "Sama"/"Tidak
diulang", status "Tidak stabil" untuk metrik tanpa target, dan kolom Aspek
yang mengulang "Latensi *end-to-end*" dua kali.

Sesudah:

```latex
  \begin{tabularx}{\linewidth}{>{\RaggedRight\arraybackslash}X>{\RaggedRight\arraybackslash}p{2.6cm}>{\raggedleft\arraybackslash}p{1.7cm}>{\raggedleft\arraybackslash}p{1.7cm}>{\centering\arraybackslash}p{1.9cm}}
    \toprule
    \textbf{Metrik} & \textbf{Target} & \textbf{Ulangan 1} & \textbf{Ulangan 2} & \textbf{Status} \\
    \midrule
    PDSR (\%) & $\geq$ 95 & 100,0 & 99,2 & Terpenuhi \\
    Latensi median (ms) & $\leq$ 2.000 & 939 & 1.108 & Terpenuhi \\
    Latensi p95 (ms) & acuan $\leq$ 2.000 & 1.404 & 3.304 & Dilaporkan \\
    Kapasitas \textit{ring buffer} (entri) & 27.000 tanpa \textit{overflow} & 27.000 & -- & Terpenuhi \\
    Detak hilang saat putus koneksi & 0 & 0 & -- & Terpenuhi \\
    Durasi \textit{flush} (detik) & $\leq$ 60 & $\leq$ 24,6 & -- & Terpenuhi \\
    \textit{Timestamp} ganda di ThingsBoard & 0 & 0 & 0 & Terpenuhi \\
    \bottomrule
  \end{tabularx}
  \par\vspace{2pt}{\footnotesize\raggedright Keterangan: PDSR dihitung per paket (292 dan 255 paket). Tanda -- berarti skenario kapasitas dan putus koneksi dijalankan sekali pada konfigurasi yang sama. Perilaku antrean penuh diverifikasi pada uji unit.\par}
```

Yang berubah: satuan pindah ke label baris (target "2 detik" dikonversi
menjadi 2.000 ms dan disebut ke user), isian samar menjadi `--` dengan satu
kalimat di Keterangan, p95 diberi status "Dilaporkan" dengan acuannya tetap
tertulis, dan jumlah paket pindah ke Keterangan sehingga sel angka hanya
berisi angka.

## B. Dua kondisi dan selisihnya

Pertanyaan: "Seberapa besar perubahan metrik dari kondisi X ke Y?" Hanya
metrik sejenis (rasio 0–1, 4 desimal). Besaran lain seperti ukuran model
pindah ke tabel sumber daya.

```latex
    \toprule
    \textbf{Metrik} & \textbf{\textit{Float32}} & \textbf{INT8} & \textbf{Selisih} \\
    \midrule
    \textit{Recall} & 0,6996 & 0,7105 & $+$0,0108 \\
    \textit{Precision} & 0,6235 & 0,6169 & $-$0,0067 \\
    \bottomrule
```

Urutkan baris dari metrik acuan utama (Recall, F1) ke metrik pelengkap
(Accuracy terakhir, ditandai "bukan acuan" di Keterangan, bukan di sel).

## C. *Confusion matrix* 2×2

Pertanyaan: "Bagaimana sebaran prediksi terhadap label?" Baris = aktual,
kolom = prediksi, dengan kolom jumlah untuk memeriksa total.

```latex
  \begin{tabular}{>{\RaggedRight\arraybackslash}p{3.0cm}>{\raggedleft\arraybackslash}p{2.6cm}>{\raggedleft\arraybackslash}p{2.6cm}>{\raggedleft\arraybackslash}p{2.0cm}}
    \toprule
    & \textbf{Prediksi Aritmia} & \textbf{Prediksi Normal} & \textbf{Jumlah} \\
    \midrule
    \textbf{Aktual Aritmia} & 3.813 (TP) & 1.637 (FN) & 5.450 \\
    \textbf{Aktual Normal} & 2.302 (FP) & 41.904 (TN) & 44.206 \\
    \bottomrule
  \end{tabular}
```

Bila *confusion matrix* sudah tampil sebagai gambar (mis. `fig:cm-ds2`),
jangan ulangi sebagai tabel. Tabelnya cukup berisi metrik (templat B, satu
kolom nilai), dan jumlah TP/FN/FP/TN disebut di paragraf bila perlu.
Pelanggaran yang dihindari: menjajarkan TP|FN|FP|TN dengan
Recall|Precision di baris yang sama.

## D. Ablasi

Pertanyaan: "Pengaturan mana yang dipilih, dan atas bukti apa?" Baris
dikelompokkan per **pertanyaan ablasi**, bukan per urutan waktu. Baris yang
dipilih ditebalkan.

```latex
    \toprule
    \textbf{ID} & \textbf{Perubahan terhadap acuan} & \textbf{\textit{Seed}} & \textbf{F1} & \textbf{\textit{Recall} S} & \textbf{AUC} & \textbf{Keputusan} \\
    \midrule
    \multicolumn{7}{l}{\textit{Posisi R dalam window, jitter $\times$2}} \\
    A2 & 90/160 & 3 & 0,6354 $\pm$ 0,0428 & 0,2712 & 0,9084 & Acuan \\
    A4 & 112/144 & 3 & 0,5786 $\pm$ 0,0311 & 0,3691 & 0,9069 & Ditolak \\
    \textbf{A6} & \textbf{128/128} & \textbf{3} & \textbf{0,6911 $\pm$ 0,0290} & \textbf{0,4221} & \textbf{0,9373} & \textbf{Dipilih} \\
    \midrule
    \multicolumn{7}{l}{\textit{Data latih tambahan pada A6}} \\
    A8 & $+$ SVDB & 6 & ... & ... & ... & Ditolak \\
    \bottomrule
```

- Keputusan memakai Acuan / Dipilih / Ditolak. Bila sebuah varian Ditolak
  padahal F1-nya lebih tinggi dari yang Dipilih (mis. selisih di bawah ambang
  0,04), alasannya ditulis di Keterangan atau paragraf. Pembaca tidak boleh
  menebak.
- Keterangan memuat arti a/b, ×2, ±, singkatan (HOS, QRS, LR), dan ambang
  bermakna. Notasi ini tidak ditaruh di baris `\multicolumn` di dalam tabel.
- Tag ablasi internal (`w128b`, `fb_svdb`) hanya di komentar `%`.

## E. Spesifikasi perangkat

Pertanyaan: "Perangkat apa yang dipakai dan untuk apa?" Satu baris = satu
komponen. Perangkat keras dan perangkat lunak dipisah ke dua tabel (anti-pola
anti-pola korpus di skill `struktur-pa`).

```latex
    \toprule
    \textbf{Komponen} & \textbf{Spesifikasi} & \textbf{Kegunaan} \\
    \midrule
    ESP32-S3 N16R8 & 512 KB SRAM, 8 MB PSRAM, 16 MB \textit{flash} & Akuisisi, preprocessing, inferensi \\
    \bottomrule
```

Spesifikasi berupa frasa angka, bukan kalimat. Riwayat rakitan (breadboard ke
PCB) dan alasan pemilihan dibahas di paragraf.

## F. Ketercapaian tujuan

Pertanyaan: "Tujuan mana yang tercapai?" Satu baris = satu tujuan. Kolom
Justifikasi diganti paragraf per tujuan di subbab berikutnya, sehingga sel
tetap pendek.

```latex
    \toprule
    \textbf{Tujuan} & \textbf{Target utama} & \textbf{Hasil kunci} & \textbf{Status} \\
    \midrule
    Tujuan 2, model INT8 \textit{on-device} & $|\Delta \textit{recall}| < 0{,}02$, model $<$ 25 KB, daya per mode & $+$0,0108, 22,94 KB, daya belum diukur & Sebagian tercapai \\
    \bottomrule
```

Status memakai Tercapai / Sebagian tercapai / Belum tercapai, dan kriteria
statusnya ditulis satu kalimat di paragraf pengantar.

## G. Pembanding penelitian terkait (Bab 2) dan pembanding protokol (Bab 4)

Pertanyaan: "Di mana posisi penelitian ini terhadap penelitian lain?" Satu
baris = satu penelitian, dan baris terakhir adalah **Penelitian ini**
(ditebalkan).

- Kolom sama untuk semua baris: Penelitian, Masalah, Metode/Model, Data dan
  pembagian, Lokasi inferensi, Hasil yang dilaporkan.
- Kolom "Perbedaan" dengan 20–40 kata per sel diganti kolom atribut pendek
  yang membuat perbedaan terlihat langsung, mis. kolom Pembagian data dengan
  isi "per detak" vs "*inter-patient*". Uraian perbedaan pindah ke paragraf
  pemosisian (arketipe "Pemosisian" di skill `narasi-pa`).
- Panjang lebih dari satu halaman → `longtable` + `\scriptsize` + kolom `L{}`
  (`laporan/CLAUDE.md`).
