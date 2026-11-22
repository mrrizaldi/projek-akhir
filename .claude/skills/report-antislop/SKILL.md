---
name: report-antislop
description: PA repo layer for editing or writing paragraphs of the PA reports (laporan/progres-pa-1, laporan/buku-pa) so they do not read as AI-written Indonesian prose. Use when the user types "rapikan biar tidak AI slop", "humanize", "bersihkan gaya tulis", "sunting bab 3", "rapikan narasi", "perbaiki paragraf penjelas tabel", "review bab", "polish this chapter", "remove AI slop from this chapter", or asks for the introductory and explanatory paragraphs of the Bab 4 result tables. Loads the user skill indonesian-antislop-writing first, then adds the house rules of laporan/CLAUDE.md, the shape of table-explaining paragraphs (finding, evidence, meaning), claims proportional to evidence, the procedure run from the book folder with make pdf-bersih, and the wrapper scripts/check_slop.py.
---

# Report anti-slop (PA layer)

Load the user skill `indonesian-antislop-writing` first; this skill only adds what is specific to the PA repo. The patterns, principles, the "what is not slop" list and the invariants (numbers, `\cite`, `\ref`, `\label`, claims, tables) live in that skill and are not repeated here.

## Edit scope

1. Edit only the chapters the user asked for. This style has so far been tested only on `laporan/progres-pa-1/bab/bab2.tex` through `bab4.tex`; extending it to Bab 1, Bab 5, the front matter (abstract and the like) or `laporan/buku-pa` waits for a user decision, and an explicit user request for one of them is that decision. Findings in other chapters are reported, not edited.
2. `laporan/proposal-pa` is frozen and never touched.
3. A sentence that needs a replacement fact the manuscript does not contain is left as it is and reported to the user, because numbers must never be invented.

## House rules that win over source advice

The user-level source may suggest things that contradict `laporan/CLAUDE.md`; in PA the following apply.

1. Paragraphs have no colon, semicolon or em dash, and no inline numbering. Replace them with conjunctions, commas, parentheses or a new sentence, because `laporan/CLAUDE.md` forbids them; `cek_tabel.py` N-GAYA flags semicolons and em dashes, while colons are checked by hand.
2. English technical terms are italicised (`\textit{board}`), the list of adopted words stays upright, and Indonesian equivalents are not used.
3. Decimal comma (0,6594), thousands dot (85.812), `~\cite{}`, and Title Case headings.
4. No "kami", "kita" or "saya": `S-PERSONA` is treated as an error in PA reports, not merely a review item.
5. No comma before "sehingga" (EYD V; error `S-KOMA-SEHINGGA`), because a main clause in front of a subordinate clause takes no comma.
6. Internal repo labels are not printed in the report text: HW-n, Fase n, Task n, T-n/K-n, rev1/rev2, file paths, script names, env names (`PA_*`) and the word "walkthrough". Name the content with a general term. `% sumber:` comments are not printed, so they may contain paths.
7. No meta openers ("Subbab ini membahas ...") and no numbered "Tujuan N" label in a heading or sentence; the chapter skeleton is in the skill `struktur-pa`.

## Paragraphs and the common thread

This applies to all paragraphs, not only table explanations.

1. **One paragraph, one function, 60 to 150 words.** Results (4.6), mechanism (4.7 or Bab 3), design decisions and limitations are not mixed; a paragraph over 180 words is split by function. The first sentence of each paragraph states the main claim for its function (a finding for results, a mechanism statement for mechanisms, a decision for decisions), not a detail or an introduction. Quick test: the paragraph must be nameable with a three to five word title without "dan".
2. **Common thread.** Each 4.6 result item ends with a sentence saying whether the Bab 3 plan target is met; 4.7 answers why and what it means without repeating the 4.6 numbers except as a reference; Bab 5 carries no new numbers (`struktur-pa` rules 3 and 6).

Example of splitting a 50-word sentence (a cause-effect chain) without losing the relation:

```latex
Deteksi berjalan tiap 1 detik atas \textit{ring} 4 detik, dan detak yang
ditemukan baru boleh keluar 128 sampel atau 356~ms sesudah puncak R.
Akibatnya, penundaan di sisi perangkat berada di antara 356 dan 1.356~ms.
```

## Table and figure explanation paragraphs

This paragraph shape is specific to PA reports and is not caught by generic patterns.

1. **Finding, evidence, meaning.** The first sentence is the main finding with a `Tabel~\ref{}` reference inside the sentence or in a closing parenthesis. The evidence holds at most five numbers in the whole paragraph, and every number in the paragraph counts, including targets, thresholds, differences and test-condition numbers (repeat count, sample count). A metric without a target (e.g. p95) stays in the table and does not enter the paragraph. Pick the table numbers that decide the point, and compare each one with a target, reference or other condition, or explain its cause; a number without a comparison is transcription ("F1 naik 0,0010" alone is wrong, "F1 naik 0,0010, jauh di bawah ambang 0,02" is right), and a number that cannot be given a comparison is dropped. Count the numbers before handing in and state the count correctly. The closing sentence ties the finding to the target or design decision. One or two sentences on an anomaly or limitation may follow; if longer, make them their own paragraph.
2. **Do not re-read the table.** The paragraph repeats at most half of the table numbers. If the paragraph must walk every row to make sense, fix the table design through the skill `tabel-pa`.
3. **Varied openers.** "Berdasarkan Tabel" and "Tabel~\ref{..} memperlihatkan/menunjukkan" are counted together, at most three times per chapter and never in two consecutive explanations. Pick the opener from the content: a direct finding ("Seluruh target pengiriman terpenuhi pada kedua ulangan (Tabel~\ref{..})."), a comparison ("Dibandingkan {acuan}, {objek} naik {besaran}"), an exception ("Seluruh selisih berada di bawah ambang kecuali {metrik}"), or a continuation of the previous paragraph.
4. **`% sumber:` lines** move together with their sentence when the sentence is moved or split.

## Claims proportional to evidence

The user skill flags absolute words and "signifikan"; in PA the strength of a claim also follows the test design.

1. One measurement under one condition takes "menunjukkan" or "terukur"; "konsisten" needs at least two repeats or three *seeds*; "terbukti" or "setara" needs the whole claimed scope tested; what is only inferred from the mechanism takes "diperkirakan" or "diduga".
2. "Signifikan" without a statistical test becomes "bermakna di atas ambang {nilai}" or "selisih {nilai}".
3. Cause and effect only from a controlled ablation (one setting changed, at least three *seeds*); simultaneous observations are written "bertepatan dengan" or "diikuti", not "menyebabkan".
4. The test condition sticks to the claim: replay or body signal source, repeat count, and test data (DS2). A claim about body signals must not rest on a replay test.
5. A metric without a target (for example p95) is not positioned against another metric's threshold; if a reference number exists, call it a reference, not a target. Inside a table-explaining paragraph, a metric without a target stays in the table and is not reported in the paragraph (item 1 of the table explanation section).
6. What has not been measured is written "belum diukur" or `\PlaceholderData{...}`, never in the past tense, because a past-tense claim about something that has not happened is a false claim. The design register (Bab 3) and the achievement register (Bab 4 and 5) are in `struktur-pa` rule 4.

## Terms and abbreviations

One concept, one term across the whole book. Before introducing a term, run `grep -rn "istilah" laporan/buku-pa/bab`. Abbreviations are defined at first appearance in each chapter (PDSR, AUC, p95, ISR).

## Procedure

Run from the folder of the book being edited. The wrapper `scripts/check_slop.py` forwards to the user skill checker (all options pass through unchanged) and gives a clear message when the user skill is not installed.

```bash
cd laporan/progres-pa-1
cp bab/bab3.tex /tmp/bab3.lama.tex
python3 ../../scripts/check_slop.py --summary bab/bab3.tex
python3 ../../scripts/check_slop.py bab/bab3.tex
python3 ../../scripts/check_slop.py --compare /tmp/bab3.lama.tex bab/bab3.tex
python3 ../../scripts/cek_tabel.py bab/*.tex
python3 ../../scripts/check_slop.py --summary bab/bab3.tex
make pdf-bersih
grep -cE "undefined|Overfull" output/main.log
```

Expected result: the checker prints `errors` and `review`; `errors` is 0 and `S-PERSONA` is 0 in the output even though its level is `review`, review items went down and the rest are deliberate, `invarian aman`, `cek_tabel` 0 errors, log 0. Use `make pdf-bersih` for evidence because `make rebuild` deletes the DOCX files in `output/`. One chapter per commit, and the commit message carries the `--summary` metrics before and after. For `laporan/buku-pa`, change the working folder; the procedure is the same.

## Extra checklist

- [ ] Table explanations touched: opened with the finding, at most five numbers that are compared or explained, closed with the meaning.
- [ ] `cek_tabel.py`: `N-PEMBUKA`, `N-ULANG`, `N-PANJANG` for touched paragraphs 0; `N-KALIMAT` and `N-SEHINGGA` per chapter down, with numbers taken from the output actually run.
- [ ] No persona, colon, semicolon, em dash or internal label in the paragraphs.
- [ ] The test condition sticks to every result claim.
- [ ] Only the requested chapter changed; `git diff --stat` checked.
