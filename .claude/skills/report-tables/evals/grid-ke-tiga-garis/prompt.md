---
tags: [report-tables]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

Repo `/home/mrrizaldi/dev/projek-akhir`, buku `laporan/buku-pa`, lebar teks A4. User mengizinkan menyunting tabel yang disebut.

Ubah tabel grid lama berikut ke gaya buku-pa. Sumbernya: `\begin{tabular}{|p{3cm}|p{3cm}|p{5cm}|}` `\hline` `\rowcolor{headgray}` `\textbf{Komponen} & \textbf{Sinyal} & \textbf{GPIO} \\` `\hline` `\multirow{2}{*}{AD8232} & OUT & GPIO 1 \\` `\cline{2-3}` `& LO+ / LO$-$ & GPIO 42 / 2 \\` `\hline` `Tombol & B1 / B2 / B3 & GPIO 4 / 5 / 6 \\` `\hline` `\multicolumn{3}{|l|}{\textit{Keluaran}} \\` `\hline` `\textit{Buzzer} & I/O & GPIO 13 \\` `\hline` `\end{tabular}`. Tulis LaTeX hasilnya, lalu sebutkan apa yang dilakukan bila tabel ini berupa `longtable` dengan `\endfoot`.

Kamu tidak bisa menjalankan perintah atau menyunting repo. Tulis LaTeX hasilnya, paragraf yang berubah, dan pesan akhir ke user; bila butuh keluaran perintah yang belum kamu lihat, tulis [N].
