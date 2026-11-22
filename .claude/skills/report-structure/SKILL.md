---
name: report-structure
description: Use when drafting, changing or reviewing the chapter and section skeleton of the Indonesian PA thesis report (laporan/buku-pa, progres-pa-1, proposal-pa), for example "tambah subbab", "pindahin Keterbatasan ke Bab 5", "tulis abstrak", "susun Bab 4 dan Bab 5", "pasang gambar", "bikin placeholder gambar", "cek benang merah", "audit ketercapaian tujuan", "QA sebelum kumpul", or "check the report structure". Holds the frozen Bab 4-5 skeleton, rules 4.6 and 4.7, the Permasalahan-Tujuan-Hasil-Kesimpulan thread, per-chapter register, the figure placeholder card, the ban on chapter and section pointers, and the pre-submission checklist. Also use when the user asks to change the frozen skeleton or add 4.8.
---

# Report structure

The official skeleton of Bab 1-3 is in `laporan/CLAUDE.md` under "Struktur Resmi Proposal PA", and Bab 1 of the book follows the proposal (skill `book-follows-proposal`). Paragraph style is governed by skill `tulis-tanpa-slop` together with the user skill `indonesian-antislop-writing`: load both when writing or editing paragraphs. Tables are governed by skill `report-tables`. The retired numbered paragraph-style rules live in `.claude/skills-arsip/narasi-pa/SKILL.md`; what is needed here is restated in rules 2 and 8.

`laporan/` is read-only without user confirmation. When not authorized to edit, write the answer as a proposal, and keep it a proposal throughout the whole message.

All printed report text stays Indonesian. Quoted headings, example sentences and LaTeX below are the literal strings to use.

## Rules

1. **The Bab 4-5 skeleton is frozen.** Order: 4.1 Parameter Eksperimen, 4.2 Karakteristik Data, 4.3 Tempat Ujicoba, 4.4 Waktu Ujicoba, 4.5 Spesifikasi Peralatan Ujicoba, 4.6 Hasil Eksperimen, 4.7 Analisis Hasil Eksperimen, then 5.1 Kesimpulan and 5.2 Saran. Keep the order and titles exactly, including "Ujicoba" (not "Uji Coba"), because the skeleton derives from the D4TI proposal guide and the PENS PA report pattern (`laporan/CLAUDE.md`, "Struktur Resmi Proposal PA").
   - A chapter has no opening paragraph: the chapter title is followed directly by its first section (2.1 Deskripsi Permasalahan, 3.1 Deskripsi Solusi, 4.1 Parameter Eksperimen, 5.1 Kesimpulan), as in the proposal. Checked by `cek_tabel.py` (N-PEMBUKA-BAB).
   - A section outside the skeleton (for example 4.8 Dokumentasi) is added only on user request, and that request is answered as an option: say 4.8 is outside the frozen skeleton, recommend that documentation photos go into 4.5 or an appendix, then wait for the user's decision. Moving Keterbatasan to Bab 5 is also declined, because Bab 5 carries no new findings (rule 6).

2. **4.6 and 4.7 follow the order of the goals and are named by their content.** 4.6.1 to 4.6.n follow the order of the Tujuan in Bab 1, chronological within each, and items use `\subsubsection` (lettered). 4.7 holds the achievement table (Tercapai / Sebagian tercapai / Belum tercapai, vocabulary from `report-tables` rule 8), one analysis section per same track, a protocol comparison section against related work, then the section Keterbatasan dan Status *Proof of Concept* closing Bab 4. The style follows the AFIB book, because that is the user's decision (consistent with `laporan/CLAUDE.md`).
   - Section titles and sentences name the content of the goal ("Jalur *Pipeline Edge-to-Cloud* Resilien", "Analisis Jalur *Pipeline Edge-to-Cloud* Resilien"), not a numbered label: no "(Tujuan 1)", "Ketercapaian Tujuan 2", "Subbab ini menjawab Tujuan 3", "Tujuan pertama tercapai sebagian". The achievement table column holds the track name. Checked by `cek_tabel.py` (N-TUJUAN).
   - Sections and items go straight to content, with no meta opener such as "Bab ini ...", "Subbab ini memaparkan ...", or "Butir ini bertujuan ...", because the reader already sees the heading. Checked by `cek_tabel.py` (N-META).
   - The link to the goals is stated once in the opener of 4.6 ("disusun mengikuti tujuan penelitian") and at the start of 5.1, with no `\ref` to a section (rule 11).
   - No table or paragraph on "design changes from the proposal". Bab 3 holds the final design, and measurement-based reasons appear in the result items (ablation, equivalence test).

3. **The thread is complete and traceable.** Path: Permasalahan[i] → Tujuan[i] → 2.1 challenge[i] → 3.1 feature[i] → Rencana Pengujian (metric + target) → 4.1 parameter → 4.6 number → 4.7 verdict → 5.1 conclusion[i] → 5.2 remainder. The number of Permasalahan items equals the number of Tujuan items, because an unpaired item cannot be judged.
   - Every target in Rencana Pengujian appears in 4.6 as a number with the same metric and gets a verdict in 4.7. A metric that changed is stated together with the reason.
   - A planned test that was not run is written explicitly as "belum dilakukan" with the reason, not dropped silently.
   - A target without a number ("tinggi", "kecil", "hemat") cannot be judged, even when the result is not yet measured. Write its status as "Belum dapat divonis (target tanpa angka)" in the achievement table, then state the treatment: give it a number from the plan, or write "target indikatif" and compare against the named comparator. "Belum tercapai" is only for numeric targets that were measured and not met.
   - Every chapter has at least one back reference to the goals or problems, without a number and without a section pointer ("dikaitkan kembali dengan tujuan penelitian").

4. **Register is set by chapter, not by document type.** Bab 3 stays in design register ("dirancang") even in the full book, and holds the final design of the system tested in Bab 4, with no internal revision history (rev1, rev2, "PCB revisi kedua", who designed it). Checked by `cek_tabel.py` (N-REVISI). Bab 4-5 are written as achievements with the test conditions attached to each claim. The full book has no progress phrases ("tahap progres ini", "fase berikutnya", "sprint berikutnya", "semester berikutnya") and never says "proposal ini". Things that have not happened are written `\PlaceholderData{...}` or "belum diukur", never in past tense, because a past-tense claim about something unmeasured is a false claim.

5. **Spread of figures, tables and citations.** Bab 1 and Bab 5 have no figures or tables. Bab 2 holds borrowed figures with a "Sumber", Bab 3 own designs, Bab 4 evidence. Citations pile up in Bab 1-2; in Bab 3-5 a citation only justifies a metric, threshold or evaluation protocol. A theory section exists only for theory that supports a design or evaluation decision, not for tooling (IDE, editor).

6. **Bab 5 is short and closed.** Two to four pages, no new numbers or findings, no citations. 5.1 closes per goal with the pattern claim then evidence number from Bab 4. Write "seluruh tujuan tercapai" only when the 4.7 achievement table is entirely Tercapai. 5.2 of the full book holds out-of-scope directions, 5.2 of the progress book holds remaining work. Things the user decided not to discuss (transport security TLS/MQTTS) do not appear in Keterbatasan or Saran.

7. **The abstract of the full book is a results abstract.** Order: problem and urgency, goal, device and method, main result numbers (model metrics, on-device performance, pipeline), then status and limitations in at most two sentences. Abstract numbers equal the numbers in Bab 4 and Bab 5. The English *Abstract* holds the same content. The abstract of the proposal and the progress book may be a plan without numbers.

8. **Every figure and table is framed.** Refer to it by number before it appears, explain it after it appears with a paragraph that opens with the finding or the number, then close with the meaning for the goals.
   - Never place a figure or table with "di atas" or "di bawah" ("Tabel 4.2 di atas"), because float positions move; the words stay allowed for magnitudes ("di atas ambang").
   - Read a figure along its flow (flowchart per decision branch, architecture per numbered zone, panels (a)/(b) named in the caption and in the paragraph).
   - An explanatory paragraph that only repeats the caption is a violation.

9. **Figure placeholders.** Do not create diagrams or illustrations (no Mermaid, TikZ, PlantUML, Graphviz, SVG, draw.io, new drawing scripts, or AI images): the user draws them. Place a placeholder holding a specification card at the figure position, and write the caption, `\label`, all `\ref`, the intro paragraph and the explanatory paragraph in final form.
   - The figure reading in the explanatory paragraph names only elements, labels and flow that are on the card, in exactly the same words (card "gerbang kalibrasi" means paragraph "gerbang kalibrasi", not "gerbang awal"), so the paragraph stays true once the figure is drawn.
   - After the whole reading, close the paragraph with exactly one meaning sentence that may tie the figure to the goals, with no section pointer (rule 11). Do not insert function or reason sentences ("syarat ini mencegah ...") in the middle of the reading, and do not add a second meaning sentence.
   - Experiment data plots from the repo pipeline (confusion matrix, curve, latency chart) are not illustrations. Refer to the exported file. If it does not exist yet, the placeholder names the producing script, and no new plot script is written unless asked.
   - Labels `RM1..RM4` never appear in figures.
   - Find remaining placeholders: `grep -rn "PLACEHOLDER-GAMBAR" laporan/`.

   The specification card holds: ID (`fig:{bab}-{slug}`, equal to the `\label`), location, type (arsitektur, flowchart, diagram alir data, state machine, blok diagram, skematik, wiring/pinout, mockup, foto perangkat, tangkapan layar, ilustrasi konsep, plot data), one-sentence main message, required elements, reading flow, text in the figure (exact labels the paragraph uses), repo material (source-of-truth path), size (landscape `width=\linewidth` or vertical `height=0.6\textheight`), and source when borrowed.

   ```latex
   % PLACEHOLDER-GAMBAR fig:3-arsitektur  (digambar user, bukan Claude)
   % Lokasi     : {subbab tempat gambar}
   % Jenis      : arsitektur sistem, landscape
   % Pesan      : {satu kalimat}
   % Elemen     : {elemen 1}, {elemen 2}, {elemen 3}
   % Alur baca  : {urutan}
   % Teks       : {label persis}
   % Bahan repo : {path}
   % Ukuran     : width=\linewidth (landscape) atau height=0.6\textheight (vertikal)
   \begin{figure}[!ht]
     \centering
     \fbox{\parbox[c][5cm][c]{0.85\linewidth}{\centering\small
       \textbf{[PLACEHOLDER GAMBAR]}\\[3pt]
       {Jenis}: {ringkasan isi satu baris}\\
       Spesifikasi lengkap ada di komentar sumber.}}
     \caption{Desain Arsitektur Sistem}
     \label{fig:3-arsitektur}
   \end{figure}
   ```

   When the figure exists, replace the `\fbox{...}` block with `\includegraphics` and delete the `PLACEHOLDER-GAMBAR` comment lines. Figures enter `laporan/*/gambar/` through `scripts/export_artifacts.sh --laporan`, not by manual copy.

10. **The PA supervisor is the same as for the AFIB book (Mulyawan 2026).** Copy its format: Tujuan with targets, a State of the Art table whose last row is "Penelitian ini", 4.7 closing with limitations and *proof of concept* status. Avoid its weaknesses: goal targets not measured with the promised metric, a *confusion matrix* described loosely, accuracy only, and a claim that all goals are met without an achievement table.
    - Never set this PA's *inter-patient* F1 directly beside AFIB accuracy, because metric and protocol differ.
    - 4.7 holds an evaluation protocol table (data split, unit, classes, metric), and 4.1 holds the reason accuracy is not used (the Normal class dominates).
    - The tone is "continuing earlier research", not tearing it down.
    - Every claimed advantage over AFIB (on-device inference, *inter-patient* evaluation, preprocessing equivalence, resilience to connection loss, model size) has a number in Bab 4.

11. **No chapter, section or item pointers in printed text.** Do not write "sebagaimana diuraikan pada Bab~\ref{..}", "(Subbab~\ref{..})", "pada Bab 3", "dibahas pada butir d", or "dijelaskan pada sub-bagian berikut". Write the content directly ("metrik *recall*, *precision*, ...", "di antara modul pengisi baterai dan konverter"), or drop the pointer when the sentence stays whole. This is the user's decision, because the proposal does not use them.
    - Still allowed: references to Tabel, Gambar and Persamaan, and "... pada butir berikut" directly followed by a list.
    - The Tujuan section of Bab 1 ends at the goal list, with no sentence after it.
    - The rule applies to printed `.tex` sentences. Messages, plans and notes to the user may name chapter and section numbers.
    - Checked by `cek_tabel.py` (N-PENUNJUK).

## Checked anti-patterns

| Group | Mistake to look for | Prevention |
|---|---|---|
| Leftovers from an old version | "proposal ini" in the book, "tiga bab" when there are five, references to a deleted table, old technology in theory, dataset theory not used | grep from the checklist, delete an element together with all its `\ref` |
| Navigation | duplicate numbers, "Tabel X di atas" when it appears later, section title not matching content, typo in a fixed title | `\label`/`\ref`, the framing pattern (rule 8), titles copied from rule 1 |
| Citations | manual numbers drifting, one number two sources, blog used for theory, literature number without `\cite` | BibTeX and `~\cite`, sources from journal/proceedings/datasheet/official documentation |
| Content and logic | benefits exceeding limitations, text number differing from table, a metric that cannot fail, inverted verbs ("penurunan dari E ke A"), planned test missing in Bab 4 | rule 3, take text numbers from the table, reread number sentences |
| Style | explanation repeating the caption, doubled paragraph, "uji coba"/"ujicoba" alternating, mixed decimals | rule 8, `tulis-tanpa-slop`, `laporan/CLAUDE.md` |

## Pre-submission checklist

Run it yourself and write numbers from real output. A command not run is written "belum dijalankan", because a guessed number is worse than an empty one.

```bash
cd laporan/buku-pa && make pdf-bersih && grep -cE "undefined|Overfull|multiply defined" output/main.log
grep -rhoE "\\label\{[^}]+\}" bab/ | sort | uniq -d
grep -rniE "proposal ini|tahap progres|sprint berikutnya|fase berikutnya|semester berikutnya" bab/
grep -rn "PLACEHOLDER-GAMBAR\|PlaceholderData" bab/ | wc -l
grep -nE "HW-[0-9]|Fase [0-9A-G]|\.md|\.py|walkthrough|Task [0-9]" bab/*.tex | grep -vE ":[0-9]+:\s*%"
grep -rn "di atas\|di bawah" bab/ | grep -iE "tabel|gambar"
python3 ../../scripts/cek_tabel.py
```

`make pdf-bersih` is used because `make rebuild` deletes the DOCX in `output/`. The `main.log` count must be 0 and the duplicate label list must be empty, because a duplicate label makes `\ref` point at the wrong number.

Then check by hand:
- Every Tujuan has a number in 4.6, a verdict in 4.7 and a sentence in 5.1.
- Abstract numbers equal Bab 4 and Bab 5.
- Manfaat and Kesimpulan do not exceed Keterbatasan.
- Sistematika Penulisan matches the chapters that exist.
- Identity (name, NRP, NIP, year) matches the official source.

## Final checklist

- The Bab 4-5 skeleton equals rule 1, 4.6 and 4.7 follow the goal order, titles by content, no "Tujuan N" and no table of changes from the proposal.
- Every Rencana Pengujian target has a number in 4.6 with the same metric and a verdict in 4.7, or is explicitly written as not done.
- Bab 3 is still design, Bab 4-5 are achievements, no progress phrases in the book.
- Bab 1 and Bab 5 have no figures or tables, Bab 5 has no new numbers.
- No chapter has an opening paragraph (`cek_tabel.py` N-PEMBUKA-BAB 0), no chapter, section or item pointers in printed text (N-PENUNJUK 0), and the Bab 1 Tujuan ends at the list.
- Every new figure is a placeholder with a complete card, and its explanation names only card elements.
- The pre-submission checklist commands were run, with numbers from real output.
- The final message only claims edits to files that were actually changed.
