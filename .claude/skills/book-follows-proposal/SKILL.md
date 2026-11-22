---
name: book-follows-proposal
description: Use when editing laporan/buku-pa, especially Bab 1 (Latar Belakang, Permasalahan, Tujuan, Manfaat, Sistematika), and when composing questions or the final report to the user about the book's content. Triggers on "rapikan Bab 1", "samakan buku dengan proposal", "tambah batasan masalah", "ikuti format AFIB", "proposal sesuaikan sama buku", "tabel perubahan dari proposal", or when about to ask the user about the test assembly, number of subjects, final PCB, or cover colour. The Bab 1 skeleton follows the proposal, the proposal is frozen, section references are not used, and questions to the user are only for decisions that change the book's content now. Also applies when rewriting Bab 1 of the progress book or composing the final report of a book-writing session. Edit and write buku-pa chapter one, follow the proposal outline.
---

# Book follows proposal

Bab 1 of the book follows the proposal because the proposal is approved and frozen; the book only adds the final design and the results. The book text stays Indonesian; quoted headings and phrases below are literal.

## Bab 1 skeleton

1. Make the skeleton of `laporan/buku-pa/bab/bab1.tex` equal to `laporan/proposal-pa/bab/bab1.tex`: Latar Belakang, Permasalahan (3 items "Bagaimana ...?"), Tujuan (3 items), Manfaat (3 items), Sistematika Penulisan. The number of Permasalahan and Tujuan items stays 3, so the thread to results and conclusion does not shift.
2. End the Tujuan section at the goal list, with no sentence after it, because the proposal has none.
3. Do not add Bab 1 sections that the proposal lacks (Batasan Masalah, Ruang Lingkup, Kontribusi and the like), even though the AFIB reference report has them. User decision: Bab 1 of the book follows the proposal.
4. Update the content of Bab 1 sections (numbers, citations, terms) when the facts change. What is followed from the proposal is the outline, not the sentences: the three problems, the three goals, and what is tested (Rencana Pengujian in Bab 3). Write the book's sentences with skill `report-antislop`; they need not be identical to the proposal.
5. When correcting facts in Bab 1, use facts already proven in Bab 2 together with their source, not new claims, because Bab 1 must not carry claims that are not proven in later chapters (a Bab 1 correction approved by the user).

## The proposal is not edited

1. Do not edit `laporan/proposal-pa`, including its `.bib`, even when the book has moved on (numeric targets, extra tests, new citations). The proposal is already submitted; editing it changes a document that has been graded.
2. Do not write an edit plan for the proposal. When the user asks "sesuaikan proposal dengan buku", decline for that reason and offer the alternative: the book holds the final design in Bab 3 and the results in Bab 4.
3. Do not create a table "perubahan dari proposal" in the book; user decision, following the AFIB book.

## Scope without a Batasan section

Write the scope in the following fixed sections, with no `\ref` to a Bab 1 section that does not exist:

- healthy anonymous subjects, non-clinical, primary data: Bab 4 `\section{Karakteristik Data}` and `\section{Tempat Ujicoba}`;
- binary classification, not a diagnostic tool, power not optimised: Bab 4 `\subsection{Keterbatasan dan Status Proof of Concept}`;
- mitdb inter-patient DS1/DS2 training data: Bab 3 `\subsubsection{\textit{Dataset} dan Pelabelan}`.

Rules for writing references:

1. Replace a reference to a deleted section with a whole sentence that stands alone (delete the clause "sesuai ..."), because pointers to sections are banned.
2. Do not use a `\ref` pointer to a chapter or section at all; follow `report-structure` rule 11.
3. Do not use pointers without a target such as "pada subbab ini" or "seperti di atas", because the reader does not know where they point.

## Build evidence

After editing, run it and read the output:

```bash
cd /home/mrrizaldi/dev/projek-akhir/laporan/buku-pa && make pdf-bersih
grep -cE "undefined|Overfull" output/main.log
```

The count must be 0. Use `pdf-bersih`, not `make rebuild`, because `rebuild` deletes the DOCX in `output/`.

## Questions to the user

Ask only about decisions that change the book's content now and cannot be answered from the repo, because a question whose answer is already written wastes the user's time. Look first in `model/CLAUDE.md`, `model/docs/` (the "Kondisi uji" line in the walkthroughs), `model/data/arsip/rekaman-uji-coba/README.md` (assembly and pins per date of the trial recordings), and the book's own content. Sort like this:

1. History already recorded in the repo (old assembly, test dates, old pins): use it as is, do not ask.
2. Numbers waiting for official data: write `\PlaceholderData{...}`, do not ask.
3. Things waiting for an event (final PCB printed, official recordings): record as an item in `model/CLAUDE.md` §Pekerjaan terbuka, do not ask. In book text and tables do not write them as if they had happened: not "PCB final" but `\PlaceholderData{rakitan final}`.
4. A decision owned by the user that was never made and has no answer in the repo (cover colour, campus template, new wording): ask once with options and a recommendation. Such a decision blocks finishing the book even though other chapters can still be written; do not decide it silently with "use the default".

## Final report to the user

1. State what changed and the build evidence actually run in that session: page count and the result of `grep -cE "undefined|Overfull"` on `output/main.log`.
2. Write "belum dijalankan" for a command that was not run, not "sukses" or "0", because a number that was not observed misleads.
3. End with only the questions from item 4 of the Questions to the user section, reasoned from repo facts, not "biasanya". No question at all is also fine.

## Final checklist

- `diff` of the `\section` skeleton of Bab 1 in the book and the proposal: equal.
- Permasalahan 3 items, Tujuan 3 items.
- `grep -rn "batasan-masalah" laporan/buku-pa/bab` is empty (or another label whose section was deleted).
- `make pdf-bersih` succeeds and the `undefined|Overfull` count is 0, from output that was run.
- No cell or sentence states something that has not happened as a fact; use `\PlaceholderData`.
- Replacement text for references: a whole sentence, no `\ref` to a chapter or section, no "pada subbab ini".
- Every question to the user passes the sorting above.
