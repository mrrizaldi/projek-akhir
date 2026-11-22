---
name: word-ingest
description: Write the user's edits in the DOCX of a PA report (output/main.docx of laporan/buku-pa or laporan/progres-pa-1, edited in WordCraft or Word) back into this repo's .tex files through make sync. Use when the user has finished editing in Word and asks for the changes to go into LaTeX, for example "ingest", "sync balik", "masukin suntingan Word ke tex", "udah selesai edit di WordCraft, masukin ke tex", "pull my Word edits back into LaTeX", "sync the docx back to tex", "ingest my WordCraft changes", also when make sync-dry or the wordcraft-cli guard refuses in a PA book. A thin layer over the user skill wordcraft-latex-ingest: it supplies the paths, make targets, backup name, format checkers and the binary specific to the PA repo. Not for creating a new DOCX (just make docx), editing .tex directly, or polishing writing style (skill report-antislop). Does not push.
---

# Ingest Word edits into LaTeX (PA repo)

Load the user skill `wordcraft-latex-ingest` first; this skill only adds what is specific to the PA repo. Procedure 0-8, the base rules and the dry-run summary live there. Below is what replaces its placeholders.

## Project and commands

- Project: `laporan/buku-pa` or `laporan/progres-pa-1`. Every command runs from its folder (`cd laporan/<projek>`); `<main>` = `main.tex`, `<out>` = `output/`, `<dir>` = `laporan/<projek>` (the folder holding `main.tex`). The diff and the `% KOMENTAR` check are limited to `bab/` because only chapters are written by sync. The real source stays the `.tex`, so the DOCX is only an editing route.
- Use the make targets from `laporan/shared/Makefile.inc`, not raw `wordcraft-cli`, because those targets already carry `--main main.tex` and the correct output location:

| Step | Command |
|---|---|
| Dry-run | `make sync-dry DOCX=output/suntingan-<stempel>.docx` |
| Write | `make sync DOCX=output/suntingan-<stempel>.docx` |
| Rebuild PDF | `make pdf-bersih` |
| Regenerate DOCX | `make docx` (after sync, not before); expected output `DOCX tersimpan di output/main.docx` |

## PA repo specific rules

- **Backup name `output/suntingan-<YYYYMMDD-HHMM>.docx`.** The user skill uses `edits-<stempel>`; in this repo the backup uses the prefix `suntingan-` to match the habit of the `output/` folder.
- **Build evidence from `make pdf-bersih`, not `make pdf` and not `make rebuild`.** `make pdf` reuses old auxiliary files so Overfull can hide; `make rebuild` calls `clean`, which deletes `output/` including the DOCX backup. Count with `grep -cE "undefined|Overfull" output/main.log`; expected `0`.
- **Format checkers for step 6:**

```bash
python3 ../../scripts/cek_tabel.py bab/*.tex
python3 ../../scripts/check_slop.py bab/<berkas>.tex
```

  `cek_tabel` for all chapters, taking the findings on the lines the ingest produced. `check_slop` for each `.tex` that sync wrote, taking the `galat` findings. Without `--summary`, because only the full form prints `berkas:baris: KODE [galat]`; `--summary` gives only counts per code. The `cek_tabel` output after the fixes goes into the commit message.
- **House rules join the format list.** Besides the generic list (colon, semicolon, em dash, terms not yet italicised), check for decimal points (this repo uses a decimal comma and a thousands dot) and for internal repo labels that must not be printed (HW-n, Fase n, file paths, script names, `PA_*`, "walkthrough"). The user's sentences are still not rewritten; only the fix is proposed.
- **New tables, equations or figures that sync did not write** are made in LaTeX following the skill `report-tables` and `laporan/CLAUDE.md`; illustration figures stay placeholders, the user draws them.
- **`skipped` items and `% KOMENTAR`** are handled as in the user skill; leftover comments are checked with `grep -n "% KOMENTAR" bab/*.tex` (expected empty).
- **The confirmation screen** follows `templates/summary.md` of the user skill, written in Indonesian, with Sumber = `output/suntingan-<stempel>.docx`.
- **Commit only the `.tex` in `laporan/<projek>/bab/`** through `git add bab/<berkas>.tex` from `laporan/<projek>`; `output/suntingan-*.docx` is ignored by git. No push.

## Binary

`wordcraft-cli` on PATH is `~/.cargo/bin/wordcraft-cli`, a build of the local WordCraft branch `fix/latex-env-scopes-declarations` (fixes for class sizes, table cells, `\parbox`, the table of contents). Version 0.18.1 is backed up at `~/.cargo/bin/wordcraft-cli-0.18.1`; use it only when the local build is suspected of causing odd behavior. The make targets use the binary on PATH, so `WORDCRAFT=` is not needed.
