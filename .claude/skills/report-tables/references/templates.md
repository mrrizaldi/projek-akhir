# Report table templates (three-line style)

All templates use the same base block as the tables already in
`laporan/buku-pa/bab/bab4.tex`. Example numbers come from buku-pa only to
illustrate the shape. When using a template, copy the numbers again from the
artifacts (`% sumber:`), not from this file.

## Base block

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

Paragraf penjelas (skill `report-antislop`): temuan dulu, lalu makna terhadap target.
```

Notes:
- The text column `X` takes the remaining width so the total fits `\linewidth`.
  With two `X` columns, both get equal width.
- Number columns `p{..}` are right-aligned. Width just enough for the longest
  number plus the header.
- `longtable` cannot use `X`. Compute `p{}` widths by hand (rule 9), repeat the
  header with `\endfirsthead`/`\endhead`, and `\endfoot` is just
  `\bottomrule`.

---

## A. Target vs result

Question: "Apakah setiap target terpenuhi?" One row = one metric.
The unit is in the row label because the quantity differs per row.

Before (`tab:target-pipeline`): unit in every cell, entries "Sama"/"Tidak
diulang", status "Tidak stabil" for a metric without a target, and an Aspek
column repeating "Latensi *end-to-end*" twice.

After:

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

What changed: the unit moved to the row label (target "2 detik" converted to
2.000 ms and the user told), vague entries became `--` with one sentence in
Keterangan, p95 got the status "Dilaporkan" with its reference still written,
and the packet count moved to Keterangan so number cells hold only numbers.

## B. Two conditions and their difference

Question: "Seberapa besar perubahan metrik dari kondisi X ke Y?" Only metrics
of the same kind (ratio 0-1, 4 decimals). Other quantities such as model size
move to a resource table.

```latex
    \toprule
    \textbf{Metrik} & \textbf{\textit{Float32}} & \textbf{INT8} & \textbf{Selisih} \\
    \midrule
    \textit{Recall} & 0,6996 & 0,7105 & $+$0,0108 \\
    \textit{Precision} & 0,6235 & 0,6169 & $-$0,0067 \\
    \bottomrule
```

Order rows from the main reference metric (Recall, F1) to complementary
metrics (Accuracy last, marked "bukan acuan" in Keterangan, not in the cell).

## C. 2×2 *confusion matrix*

Question: "Bagaimana sebaran prediksi terhadap label?" Rows = actual,
columns = predicted, with a total column to check the sum.

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

When the *confusion matrix* already appears as a figure (for example
`fig:cm-ds2`), do not repeat it as a table. The table then holds metrics only
(template B, one value column), and the TP/FN/FP/TN counts are named in a
paragraph if needed. The violation to avoid: listing TP|FN|FP|TN beside
Recall|Precision in the same row.

## D. Ablation

Question: "Pengaturan mana yang dipilih, dan atas bukti apa?" Rows are
grouped by **ablation question**, not by time order. The chosen row is bold.

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

- The decision uses Acuan / Dipilih / Ditolak. When a variant is Ditolak even
  though its F1 is higher than the Dipilih one (for example the difference is
  below the 0,04 threshold), the reason is written in Keterangan or a
  paragraph. The reader must not guess.
- Keterangan holds the meaning of a/b, ×2, ±, abbreviations (HOS, QRS, LR), and
  meaningful thresholds. This notation is not placed in a `\multicolumn` row
  inside the table.
- Internal ablation tags (`w128b`, `fb_svdb`) appear only in `%` comments.

## E. Device specification

Question: "Perangkat apa yang dipakai dan untuk apa?" One row = one component.
Hardware and software go into two separate tables.

```latex
    \toprule
    \textbf{Komponen} & \textbf{Spesifikasi} & \textbf{Kegunaan} \\
    \midrule
    ESP32-S3 N16R8 & 512 KB SRAM, 8 MB PSRAM, 16 MB \textit{flash} & Akuisisi, preprocessing, inferensi \\
    \bottomrule
```

The specification is a numeric phrase, not a sentence. Assembly history
(breadboard to PCB) and the reason for the choice are discussed in a paragraph.

## F. Goal achievement

Question: "Tujuan mana yang tercapai?" One row = one goal. A Justifikasi
column is replaced by one paragraph per goal in the following section, so cells
stay short.

```latex
    \toprule
    \textbf{Tujuan} & \textbf{Target utama} & \textbf{Hasil kunci} & \textbf{Status} \\
    \midrule
    Model INT8 \textit{on-device} & $|\Delta \textit{recall}| < 0{,}02$, model $<$ 25 KB, daya per mode & $+$0,0108, 22,94 KB, daya belum diukur & Sebagian tercapai \\
    \bottomrule
```

Status uses Tercapai / Sebagian tercapai / Belum tercapai, and the status
criterion is written in one sentence in the intro paragraph.
The first column holds the goal name by its content, not a numbered label "Tujuan N" (skill `report-structure` rule 2).

## G. Related-work comparison (Bab 2) and protocol comparison (Bab 4)

Question: "Di mana posisi penelitian ini terhadap penelitian lain?" One row =
one study, and the last row is **Penelitian ini** (bold).

- The same columns for every row: Penelitian, Masalah, Metode/Model, Data dan
  pembagian, Lokasi inferensi, Hasil yang dilaporkan.
- A "Perbedaan" column with 20-40 words per cell is replaced by short
  attribute columns that make the difference visible directly, for example a
  Pembagian data column holding "per detak" vs "*inter-patient*". The
  explanation of differences moves to a positioning paragraph after the table,
  which names the gap in earlier research and then this PA's position against
  that gap.
- Longer than one page → `longtable` + `\scriptsize` + `L{}` columns
  (`laporan/CLAUDE.md`).
