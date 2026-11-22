# scripts/: cross-component automation

| Script | Function |
|---|---|
| `export_artifacts.sh` | Artifact sync, producer → consumer: `model_int8.tflite` → `firmware/include/model_int8.h`; with `--laporan`, final figures from `model/artifacts/metrics/` and `dashboard/preview.png` → `laporan/<projek>/gambar/` |

```bash
bash scripts/export_artifacts.sh                                 # model -> firmware
bash scripts/export_artifacts.sh --laporan                       # + figure -> laporan/buku-pa/gambar/
LAPORAN_PROJ=proposal-pa bash scripts/export_artifacts.sh --laporan
AKUISISI="akuisisi/akuisisi_<tgl-jam>" bash scripts/export_artifacts.sh --laporan   # + grafik rekaman resmi
```

The figure step does not run without `--laporan` because `laporan/` is
read-only without confirmation. Artifacts are not copied by hand. `LAPORAN_PROJ`
selects the target project (default `buku-pa`; `proposal-pa` = archive).
`AKUISISI` holds the list of extra recording plots (official data = the
22 Oct 2026 afternoon session, the R1 plot is already in the fixed list;
relative to `model/artifacts/metrics/`, without `.png`, separated by spaces)
that are copied as well.

## File index in the browser

`serve.py` starts a local server (stdlib, no dependencies) that serves the
whole repo. The `/` page lists all `.pdf`, `.docx`, and `.pptx` files in the
repo (except `.git`, `.venv`, `node_modules`, `.pio`), grouped by folder. The
folder with the newest file appears at the top, so a PDF that was just built
with `make pdf` is immediately first. The list is re-read every time the page
loads, with no build step. Links open in a new tab.

1. Run from the repo root:

   ```bash
   python3 scripts/serve.py          # port bawaan 8700
   python3 scripts/serve.py 9000     # port lain
   ```

2. Open `http://127.0.0.1:8700/` in a browser. PDFs open in the browser
   viewer; `.docx`/`.pptx` are downloaded.
3. Stop with `Ctrl+C`.

Folders `laporan/rilis/<proyek>/vN` with N > 0 have a link "banding vN-1 dan
vN" (compare vN-1 and vN) in their group title. The link opens the `/banding`
page with two PDFs side by side. The per-word text changes are in
`banding-vM-vN.pdf` in the same folder. The `lama` (old) and `baru` (new)
parameters of `/banding` accept only PDFs inside the repo.

The server listens only on `127.0.0.1`, so it is not reachable from other
devices on the network. Besides the files in the index, any path in the repo
can be opened directly by URL (`/model/artifacts/metrics/...png`).

## Checkers

`check_comments.py` enforces the NO CODE COMMENTS rule (root `CLAUDE.md`,
Strict rule 5). It scans git-tracked files and exits with code 1 while
printing `berkas:baris: isi` for each comment found.

| Kind | Forbidden | Allowed |
|---|---|---|
| C/C++ (`.c .cpp .h .hpp`) | `//`, `/* */` | `//` or `/*` inside a string/char literal |
| Python (`.py`) | `#`, module/class/function docstrings | shebang on line 1, `coding` line |
| Shell (`.sh`, `.githooks/*`) | `#` at the start of a word outside a string | shebang on line 1, `$#`, `${#v}`, heredoc contents |
| `platformio.ini` | lines starting with `;` or `#` | — |
| Makefile | `#` (including `##` section titles) | `##` description on a target line (`make help`) |

Excluded: `laporan/`, `docs/`, `*.md`, `*.tex`, `arsip/` folders, and other
non-code files.

```bash
python3 scripts/check_comments.py                       # seluruh repo
python3 scripts/check_comments.py firmware/src model/x.py  # sebagian (folder/berkas)
python3 scripts/check_comments.py --self-test             # uji mandiri pemeriksa
```

CI runs it in `.github/workflows/checks.yml` (job `comments`), together with
`pio test -e native` (job `firmware-native`). The model pytest is not included
because it needs MIT-BIH data that is not committed.

An optional local hook checks staged files before commit. Enable it once per
clone:

```bash
git config core.hooksPath .githooks
```

Limitations: the hook reads the contents of the working tree file, not the
staged contents; C++ raw strings (`R"(...)"`) and digit separators (`1'000`)
are not yet recognized by the C tokenizer.

## Report table and narrative checker

`cek_tabel.py` checks LaTeX tables and their explanatory paragraphs in the PA
report (skills `tabel-pa` and `tulis-tanpa-slop`). Errors exit with code 1,
while suggestions are only printed (`--ketat` makes suggestions fail as well).
Output format: `berkas:baris: [KODE tingkat] pesan`.

| Code | Level | What is checked |
|---|---|---|
| `T-BAB` | error | table in Chapter 1 or Chapter 5 |
| `T-GRID` | error | `booktabs`, although the PENS guideline uses a full grid |
| `T-HEADER` | error | header without `\rowcolor{headgray}` |
| `T-CAPTION` | error/suggestion | caption missing or below the table (error), ends with a period, contains parentheses, > 15 words (suggestion) |
| `T-LEBAR` | error | sum of `p{}` widths + `\tabcolsep` exceeds the text width (A4 14 cm) |
| `T-RUJUK` | error/suggestion | label never referenced (error) or only referenced after the table (suggestion) |
| `T-FLOAT` | suggestion | `[H]` |
| `T-SEL` | suggestion | cell > 20 words |
| `T-CATATAN` | suggestion | `\multicolumn` row as wide as the table holding a long note |
| `T-SATUAN` | suggestion | unit repeated in ≥ 3 cells of one column |
| `T-DESIMAL` | suggestion | number of decimals not uniform within one column |
| `T-ISIAN` | suggestion | fill-in values "Sama", "idem", "Tidak diulang", "Konfigurasi sama" (same, idem, not repeated, same configuration) |
| `N-PEMBUKA` | suggestion | consecutive explanatory paragraphs with the same opening, "Berdasarkan Tabel" (based on Table) > 3 per chapter |
| `N-ULANG` | suggestion | explanatory paragraph repeats > 50% of the table numbers (table with ≥ 5 numbers) |
| `N-PANJANG` | suggestion | explanatory paragraph > 180 words |
| `N-KALIMAT` | suggestion | sentence > 35 words (summarized per chapter, 5 longest) |
| `N-GAYA` | suggestion | semicolon or em dash in a paragraph |
| `N-SEHINGGA` | suggestion | "sehingga" (so that) > 5 per 1,000 words |

```bash
python3 scripts/cek_tabel.py                                 # laporan/buku-pa/bab/bab*.tex
python3 scripts/cek_tabel.py laporan/buku-pa/bab/bab4.tex    # satu bab
python3 scripts/cek_tabel.py --tanpa-prosa                   # tabel dan penjelasnya saja
python3 scripts/cek_tabel.py --kertas a5 <berkas-bab.tex>    # lebar teks A5
python3 scripts/cek_tabel.py --uji                           # uji mandiri pemeriksa
```

## Reference list downloader

`fetch_references.py` downloads PDFs for the `laporan/*/referensi.bib` entries
into `laporan/pustaka/<kunci-bib>.pdf` (the folder is git-ignored: publisher
PDFs must not enter the repo). Sources: DOI → Unpaywall → open access PDF URL;
`@misc` entries whose `url` is directly a `.pdf` are downloaded as is. Files
that already exist are skipped, so it is safe to run repeatedly. Entries
without a DOI in the proposal bib (frozen) are given a DOI through the
`EXTRA_DOIS` table in the script, the result of title searches in Scopus
(15 Oct 2026).

```bash
cd model && .venv/bin/python ../scripts/fetch_references.py   # python3 biasa juga bisa, stdlib saja
```

Output: a `[unduh]` (downloaded), `[ada]` (exists), or `[gagal]` (failed) line
per key, then a summary. Exit code 1 if any failed. This script only reaches
publishers that allow automated downloads; the rest are downloaded manually
through a browser with a campus account, then saved as `<kunci-bib>.pdf` in the
same folder.

State on 15 Oct 2026 (48 entries combined from three bibs):

| Status | Entries |
|---|---|
| Downloaded automatically (10) | `al_quayed_2026`, `david_2021`, `escobedo_2026`, `jacob_2018`, `kim_2023`, `li_2020`, `reoukadji_2025`, `saito_2015`, `tipparaju_2021`, `zambrano_2026` |
| Downloaded through headed Chrome browser (4; MDPI, IEEE OA, Nature) | `xiao_2023`, `orphanidou_2015`, `lueken_2023`, `joutsen_2024` (the last three are not yet in the bib, material for the paper dissection) |
| Downloaded from the authors' institutional repository (1; 20 Oct 2026) | `yaacoub_2020` (AUB ScholarWorks, `https://scholarworks.aub.edu.lb/server/api/core/bitstreams/eb7f173e-d502-4682-9b35-c2b2acfe60bd/content`) |
| Elsevier/ScienceDirect: CAPTCHA, manual download (18; 8 of them open access) | `tinyml_iot_review`, `resilient_edge_cloud`, `mekhfioui_2025`, `xie_2021`, `karri_2023`, `laiu_2026`, `crespi_2026`, `sheeba_rani_2026`, `chowdhury_2023`, `dias_2021`, `safdar_2023`, `bui_2021`, `elhadad_2025`, `khan_2025`, `fahoum_2026`, `xiang_2026`, `kumaran_2026`, `verma_2024` |
| IEEE paywalled, needs a campus account (6) | `pan_tompkins_1985`, `moody_mark_2001`, `dechazal_2004`, `shi_2016`, `kiranyaz_2016`, `lee_2013` |
| Open access but blocked for automation (3) | `yahyati_2025` (IEEE Access), `goldberger_2000_physionet` (AHA), `skorinkapov_2010` (Wiley) |
| Springer paywalled (1) | `bahrami_2025` |
| Not an article: book, thesis, standard, web page (8) | `ecg_goldberger`, `sornmo_laguna_2005`, `mulyawan_2026`, `aami_ec57_2012`, `iec_60601_2_27_2011`, `who_cvd`, `oasis_mqtt5`, `analog_ad8232` |

MDPI, IEEE open access, and Unpaywall reject `curl`/`urllib` with 403; what
works for them is a download through a real browser (headed Chrome), not
headless. The ScienceDirect/AHA/Wiley CAPTCHAs are not bypassed.

Paywalled papers marked `closed` by Unpaywall sometimes have a legal copy in
the authors' institutional repository (DSpace, e.g. AUB ScholarWorks,
QSpace). Search for the title there before asking for a campus account. On
DSpace 7, files are fetched through `/server/api/core/bitstreams/<uuid>/content`.

Bib entry verification: the existence of the document, journal, and DOI is
checked in Scopus (MCP `scopus`); authors, volume, and pages are taken from
Crossref (`api.crossref.org/works/<DOI>`) because `get_abstract_details` on
this subscription does not return them. Entries not indexed by Scopus are
verified against their official source: `david_2021` (MLSys) at
proceedings.mlsys.org, `aami_ec57_2012` at the ANSI webstore,
`iec_60601_2_27_2011` at the IEC webstore, and web entries, standards, or other
*datasheets* (`who_cvd`, `oasis_mqtt5`, `analog_ad8232`) at the publisher's
page.

## DOCX vs PDF similarity checker

`cek_docx.py` compares the PDF produced by pdfLaTeX with the DOCX produced by
WordCraft, page by page. The DOCX is re-rendered to PDF through
`wordcraft-cli convert` in a temporary folder, then both PDFs are read with
`pdftotext`. A page is considered the same if its first six words are the same
(lowercase, punctuation and page numbers removed, words hyphenated at line
ends joined). The output contains the page count, the starting page of each
chapter with the difference, the number of pages that start the same, and
excerpts of the first five pages that differ. The exit code is 0 only if the
page count and the start of every page are the same.

```bash
cd laporan/buku-pa
make pdf docx
make cek-docx                                  # memakai wordcraft-cli di PATH
make cek-docx WORDCRAFT=/path/ke/wordcraft-cli # binary lain, mis. hasil build branch
```

## AI writing pattern checker

`check_slop.py` is a thin wrapper around
`~/.claude/skills/indonesian-antislop-writing/scripts/check_slop.py`. The
source of patterns, thresholds, and catalog is in that user skill
(`references/catalog.md`); this repo does not keep a copy. All options are
forwarded as is and the exit code is the same as the original checker. If the
user skill is not installed, the wrapper prints a message and exits with code
2. Table, figure, equation environments, and `%` comments are skipped.
Findings are graded `error` (exit code 1) and `review`; `--compare` fails if
numbers, `\cite`/`\ref`/`\label` keys, or `%` comment lines change.

```bash
cd laporan/progres-pa-1
python3 ../../scripts/check_slop.py --summary bab/bab2.tex bab/bab3.tex bab/bab4.tex
python3 ../../scripts/check_slop.py bab/bab3.tex
python3 ../../scripts/check_slop.py --compare /tmp/bab3.lama.tex bab/bab3.tex
python3 ../../scripts/check_slop.py --self-test
```

## check_skills.py

`check_skills.py` checks the structure of every skill in `.claude/skills/*/`
(`.claude/skills-arsip/` is not checked). What is checked:

- `SKILL.md`: frontmatter only `name` and `description`, `name` equal to the
  folder name, `description` on one line and at most 1,024 characters, body
  under 500 lines.
- `evals/<kasus>/`: `prompt.md` (frontmatter and text), `case.yaml`
  (`schema_version: "1.1"`, `name` equal to the folder name,
  `expected_outcome`), and at least one `graders/*.md` with frontmatter
  `type`, `focus`, `weight`.
- `triggers/evals.json`: a list of `{query, should_trigger}` with both true and
  false classes.
- A skill without `evals/` or `triggers/`, or one that still has `eval.md`,
  counts as an error. The option `--lewati-eval-lama` skips the eval checks for
  skills that still use `eval.md` (transition period).

Exit code 1 if there are errors. CI runs `--self-test` and the check without
options.

```bash
python3 scripts/check_skills.py
python3 scripts/check_skills.py --self-test
```

## trigger_eval.sh

`trigger_eval.sh` measures whether a skill's description triggers on the right
queries and not on others, using `run_eval.py` from skill-creator and the
skill's own `triggers/evals.json`. It runs in isolation: the temporary Claude
configuration (`CLAUDE_CONFIG_DIR`) contains only a copy of
`~/.claude/.credentials.json`, and the project is an empty folder so other
skills and `CLAUDE.md` are not included. The credentials copy is deleted when
the script finishes.

Prerequisites: `uv`, skill-creator in `~/.claude/skills` (the `.trash` folder is
skipped), and an active login (`claude login`). A missing prerequisite makes
the script exit with code 2 and a message.

```bash
scripts/trigger_eval.sh .claude/skills/<skill> [.claude/skills/<skill2> ...]
```

Output per skill: `name=<skill> passed=<n>/<total>` and `json=<path>`; the full
JSON and error logs are in the temporary folder `$T/out/`. Each query is run
once (`--runs-per-query 1`), so the result is a small sample and can shift
between runs. Cost: one model call per query, about 20 calls per skill with 20
queries, and about 25 seconds.

Leak pitfall: a trigger test can leave `*-skill-*` files in
`~/.claude/commands` that are then read as commands in other sessions. The
script stops with code 3 if that folder already contains them before it
starts, and checks again at the end. Clean those files before running again.

## rilis.py

`rilis.py` freezes the PDF and DOCX of `buku-pa` or `progres-pa-1` as a
numbered release. The build runs from a commit in a temporary git worktree, so
uncommitted edits are not included. The output is copied to
`laporan/rilis/<proyek>/vN/` (gitignored), a latexdiff PDF against the previous
release is produced if there is one, and an annotated tag
`rilis/<proyek>/vN` is placed on the built commit. Release files are not
committed, only the tag; the tag is not pushed.

1. Commit all report changes.
2. Run one of:

```bash
cd laporan/<proyek> && make rilis CATATAN="..."
python3 scripts/rilis.py <proyek> --rev <commit> --catatan "..."
```

3. Output: `version=`, `rev=`, `pdf=`, `pages=`, `log_errors=` (lines
   `undefined` or `Overfull` in the LaTeX log), `diff=` or `warn=`, and
   `tag=`.
4. The result is in `laporan/rilis/<proyek>/vN/`: `<proyek>-vN.pdf`,
   `<proyek>-vN.docx`, `banding-vM-vN.pdf`. This folder is visible in
   `serve.py`.
5. A missing release folder is rebuilt from the tag:

```bash
git worktree add --detach /tmp/r rilis/<proyek>/vN
make -C /tmp/r/laporan/<proyek> pdf docx
git worktree remove --force /tmp/r
```

Copy `output/main.pdf` and `output/main.docx` from `/tmp/r` before the
worktree is removed.

Refusals: the `laporan/` tree has uncommitted changes (only for `--rev HEAD`),
there are no changes in `laporan/<proyek>` or `laporan/shared` since the last
release, or the version folder already exists.
