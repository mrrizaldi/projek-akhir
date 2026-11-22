---
name: report-tables
description: Use when creating, reworking or reviewing LaTeX tables in the Indonesian PA thesis report (laporan/buku-pa, progres-pa-1), including Bab 4 result tables, specification, ablation, goal achievement and related-work comparison tables. Use whenever the user says "rapikan tabel", "tabelnya jelek", "ubah ke tiga garis", "booktabs", "buat tabel hasil", "tabel pembanding", "tabel terlalu penuh", "sel terlalu panjang", or "fix this table"; also when writing the intro and explanatory paragraphs around a table. Covers the three-line style without vertical rules, one table one question, short cells, tidy numbers and units, a fixed status vocabulary, notes under the table, and checking with cek_tabel.py.
---

# Report tables

A table that is correct in format can still be bad when used as a container for paragraphs or when its rows do not answer the same question. This skill governs the content and layout of tables, not only their rules.

Table content stays Indonesian (headers, status words, captions, decimal comma). Quoted strings below are literal.

## Style decisions

- Tables in buku-pa use the three-line style (`booktabs`), not a full grid, because research tables rarely have full borders and the AFIB book (same supervisor) uses three lines.
- The related-work comparison table (`tab:perbandingan-penelitian`) is the only exception: a plain closed grid. The exception list is `FULL_GRID_TABLES` in `scripts/cek_tabel.py`.
- `laporan/proposal-pa` is frozen and stays grid; do not edit it.
- Advice from English-language writing skills that is not adopted: bolding the best value in every column (Bab 4 judges against targets, not a contest; bold only for the chosen variant in an ablation table), an "Ours" row (replaced by the last row "Penelitian ini"), two-column `table*` (the report is single column), and `threeparttable` (replaced by a Keterangan line with no new package).

## Rules

1. **Use three lines.** `\toprule` above the header, `\midrule` below the header, `\bottomrule` at the end. No `|`, `\hline`, `\cline`, or `\rowcolor`. Bold header. The reason: one form across the whole book.
   - Extra rules in the body are only a group-separating `\midrule`: exactly before the `\multicolumn` group name row (no rule after it), and in `\multirow` tables every full `\hline` becomes `\midrule` while `\cline` is deleted. Any other body `\hline` is deleted with no replacement.
   - In `longtable`, the repeated header uses `\toprule`/`\midrule` and `\endfoot` uses `\bottomrule`.
   - `tab:perbandingan-penelitian` uses `|` in the column spec and `\hline` after the header (in `\endfirsthead` and `\endhead`) and after every row, with no booktabs, `\rowcolor`, or colour.

2. **Layout.** Caption above the table (bold, centred, automatic from `preamble.tex`), `\begin{table}[!ht]` not `[H]`, and "Sumber: ..." at 10pt centred under a borrowed table. One table does not span more than one page, except the long comparison table as a `longtable` (`laporan/CLAUDE.md` §Konvensi Tabel & Gambar). Bab 1 and Bab 5 have no tables, because both are narrative.

3. **Decide first whether a table is needed.** A table is only for two axes the reader compares: similar rows and similar attributes.
   - Two or three numbers: write them in a sentence.
   - A trend over many points (loss curve, residual spread): a plot figure from the repo pipeline (placeholders are governed by skill `report-structure` rule 9).
   - Reasons, arguments and decision history: a paragraph, because a cell is not a place for a paragraph.

4. **One table answers one question, and every row is an object of the same kind.** Write the question in one sentence before laying out columns, for example "Apakah setiap target *pipeline* terpenuhi?". A row that answers another question moves to another table or into a sentence. Violation examples: TP/FN/FP/TN listed beside Recall/Precision (split into a 2×2 *confusion matrix* and a metrics table, templates C and B in `references/templates.md`), or a row "Ukuran model (KB)" in a metric-difference table (move to a resource table or a sentence).

5. **Short cells.** At most 20 words per cell, ideally under 12, because a long cell means a reason or condition is riding along. Move it to the explanatory paragraph or the Keterangan line, do not drop it. A column "Alasan" or "Justifikasi" is kept only when every cell fits one phrase. A citation inside a cell or a paragraph is written `teks~\cite{key}` with a tie, never a plain space, so the citation never starts a new line on its own.

6. **Numbers.**
   - Write the unit once: in the column header when one column is one quantity (`\textbf{Latensi (ms)}`), or in the row label when the quantity differs per row. Do not write `939~ms` in every cell.
   - A value may be converted so one row has one unit (target "2 detik" becomes `2.000` on an ms row). Tell the user that this is a display change, not a number change.
   - Uniform decimals per column: classification metrics 4 decimals, percent 1 decimal, latency integer ms. Decimal comma, thousands dot (`3.813`, `0,6996`, `99,2`).
   - Number columns right-aligned: `>{\raggedleft\arraybackslash}p{2cm}`. Centre only for short status or labels.
   - Ranges and thresholds use math symbols (`$\leq$ 2`, `$<$ 0{,}02`); differences carry an explicit sign (`$+$0,0108`, `$-$0,0067`).

7. **Empty and repeated entries.**
   - No value: write `--`, then explain it in one sentence in Keterangan ("-- : skenario putus koneksi dijalankan sekali").
   - Never write "Sama", "idem", "Konfigurasi sama", "Tidak diulang", "dst", because the reader cannot tell whether it was measured or not run. A repeat that was run with the same result is written as its value (for example `0`); one not run is written `--` plus Keterangan.
   - Same value in consecutive rows of the first column: use `\multirow` (the package is loaded), or a `\midrule` group row followed by `\multicolumn{k}{l}{\textit{Nama kelompok}}`.
   - A column with the same content in every row is deleted; its value goes into the caption or Keterangan (for example "model *window* 250").

8. **Fixed status vocabulary.**
   - Target table: Terpenuhi / Tidak terpenuhi / Belum diukur.
   - Goal achievement table: Tercapai / Sebagian tercapai / Belum tercapai.
   - Ablation table: Dipilih / Ditolak / Acuan. Every Ditolak whose F1 is higher than Dipilih is explained in Keterangan or a paragraph.
   - A metric without a target in the test plan: "Dilaporkan", then discussed in a paragraph.
   - A reference number that is not a target (for example the 2 second reference for p95) is still written in the Target column as `acuan $\leq$ 2.000`.

9. **Compute widths, do not guess.** A4 text width = 14 cm, A5 = 9,8 cm.
   - New float table: `tabularx` with `\linewidth`, text columns `>{\RaggedRight\arraybackslash}X`, number columns right-aligned `p{..}`, so the total fits.
   - `longtable` (cannot use `tabularx`): sum of `p{}` widths + 2 × `\tabcolsep` × number of columns ≤ text width; `cek_tabel.py` checks it (`T-LEBAR`).
   - Reduce font size (`\small`, then `\footnotesize`) only after shortening cells. `\scriptsize` only for the dense comparison table.

10. **Captions are noun phrases.** No full stop and no verb, at most 15 words, holding the object and the distinguishing condition (for example "pada DS2", "*threshold* 0,80"); parenthetical explanation moves to Keterangan. Patterns:
    - result: "Hasil Pengujian {Objek} terhadap {Acuan/Target}"
    - two conditions: "Perbandingan {Metrik} {Kondisi A} dan {Kondisi B}"
    - specification: "Spesifikasi {Perangkat Keras/Lunak} Ujicoba"
    - plan: "Rencana Pengujian {Objek}"
    - structure: "Struktur {Payload/Tabel} {Nama}"
    - achievement: "Ketercapaian Tujuan Penelitian"
    - comparison: "Perbandingan Penelitian Terkait"

11. **A note under the table**, inside `table` after `\end{tabular}`, 10pt left-aligned: `\par\vspace{2pt}{\footnotesize\raggedright Keterangan: ...\par}`. It holds abbreviations (TP, PDSR, p95, HOS), the meaning of `--`, and one sentence of test condition. A table-wide `\multicolumn` row holding a note moves here. "Sumber: ..." for a borrowed table goes after Keterangan.

12. **Every number is traceable.** Add a LaTeX comment `% sumber: path (nilai mentah)` after the table or per row (`.tex` comments are not printed). Numbers come only from repo artifacts (`model/artifacts/metrics/*`, the active walkthrough, code). A number that does not exist yet is written `\PlaceholderData{...}`, never guessed. Internal working labels (`HW-n`, `Fase n`, ablation tags, file names) must not appear in cells (`laporan/CLAUDE.md` §Larangan Label Kerja).

13. **A table does not stand alone.** An intro paragraph refers to the table before it appears. The explanatory paragraph after it follows the "Paragraf penjelas" part of skill `tulis-tanpa-slop` (finding first, no re-reading of the table content). Do not change a `\label` that is referenced in another chapter; check with `grep -rn "ref{tab:" laporan/buku-pa/bab`.

14. **Authority limit.** `laporan/` is read-only without confirmation (root `CLAUDE.md`). For a general request such as "rapikan tabel Bab 4", first show a per-table plan (question answered, new columns, rows moved) and edit the `.tex` after the user agrees. When the user already named the table and the chapter that may change, do it directly.

## Workflow

1. Run `cd laporan/buku-pa && python3 ../../scripts/cek_tabel.py bab/*.tex` and note errors and suggestions per table. Or from the repo root: `python3 scripts/cek_tabel.py --tanpa-prosa`.
2. For each table touched, write its question (rule 4), then pick a template from `references/templates.md`: A target vs result, B two-condition comparison, C *confusion matrix*, D ablation, E specification, F goal achievement, G related-work comparison.
3. Rebuild with rules 5-11. Content that leaves a cell moves to the explanatory paragraph or Keterangan.
4. Write or update the intro and explanatory paragraphs with skill `tulis-tanpa-slop`.
5. Build and check:
   ```bash
   cd laporan/buku-pa && make pdf-bersih
   grep -cE "undefined|Overfull" output/main.log
   ```
   Expected: 0 for the tables touched. Open the table pages in the PDF and look at them. Do not use `make rebuild`, because it deletes the DOCX in `output/`.
6. Rerun `cek_tabel.py`. Report the before and after numbers from output that was actually run; what was not run is written "belum dijalankan".

## Final checklist

- Every table touched has a one-sentence question, and all its rows answer it.
- `cek_tabel.py` 0 errors; suggestions `T-SEL`, `T-SATUAN`, `T-DESIMAL`, `T-ISIAN`, `T-CATATAN` for touched tables 0, or each suggestion left in place has a written reason.
- Three lines without `|`, `\hline`, `\rowcolor` (except `tab:perbandingan-penelitian`); caption above, `[!ht]`.
- Units in the header, uniform decimals, number columns right-aligned.
- No "Sama"/"idem"/"Tidak diulang"; there is `--` plus Keterangan.
- Status uses the rule 8 vocabulary.
- `% sumber:` exists for every number; no internal working labels in cells.
- `make pdf-bersih` succeeds and `grep -cE "undefined|Overfull" output/main.log` for touched tables is 0, from output that was run.
- Old table labels are unchanged, or all their `\ref` were replaced too.
