# CLAUDE.md: Final Project (PA monorepo)

Guide for Claude Code when working in this repo. Read it before acting.
Subdir-specific rules: `model/CLAUDE.md` (TinyML track, decision points, pitfalls)
and `laporan/CLAUDE.md` (report writing style).

## What this is

Final Project (PA) monorepo: **continuous heart rate monitoring, arrhythmia
classification at the edge** (ESP32-S3 + TinyML INT8). Components per subdir;
see `README.md` for the table and the artifact flow.

**Running working documents** that span components live in `docs/`
(index `docs/README.md`). History is in git.

**Open work** (dated, do not lose track): single list in
[`model/CLAUDE.md` §Open work](model/CLAUDE.md#open-work):
power consumption, **board WiFi deliberately OFF (emergency since 14 Oct 2026,
turn it back ON after the battery converter is set to 5 V)**, then the plan to
record raw data straight to the server over WiFi, and PCB rev2. Official body
signal data = the 22 Oct 2026 midday session (`model/data/recordings/README.md`);
data before 13 Oct 2026 = trial runs. Report numbers waiting for data: `grep -rn
PLACEHOLDER-DATA laporan/buku-pa` (only power is left).

## Hard rules (STRICT, set by the user 13 Oct 2026)

Apply to all code in the repo. No exceptions without the user's permission.

### Verify your own work
A. **Run it yourself before saying it is done.** Build, flash, run on the board
   (board plugged in = Claude runs it), press/inject its buttons, read the serial
   log, run the script. The user is not the verifier.
B. **Every commit carries evidence:** passing test output, a serial log excerpt,
   script output, or a screenshot/photo. Write the evidence in the commit message
   or the final report. No evidence, no commit.
C. **If it cannot be verified, stop and say so.** State exactly what is not yet
   proven (e.g. screen display, buzzer sound, power figures on battery) and how
   the user can check it. A guess that looks finished is the worst thing that
   can be handed over.

### Know the code first
1. **Read the feature map before touching a module.** Maps already written:
   `README.md` (components), `firmware/README.md` (modules, buttons, menus, serial
   commands), `model/docs/README.md` (model pipeline), `model/CLAUDE.md`
   (decision points). Do not guess a structure that is already documented.
2. **Open a file before editing it.** Never write code from memory of a file's
   contents.
3. **One feature per commit.** A feature does not include another feature; shared
   code goes through a shared layer. Firmware: shared layer = `perangkat`, `konfig`,
   `ecg_*`, `ina219`; wiring = `main.cpp` and `menu.cpp`; other features do not
   include each other.

### Hard rules, enforced by the checker
4. **No `useEffect`** (applies when there is React/frontend code): derive the
   value or handle it in the event.
5. **NO CODE COMMENTS.** C/C++, Python (including docstrings), shell, and
   `platformio.ini`. If code needs a comment, rename it or split it until it does
   not. Explanations, rationale, pitfalls, and usage are written in separate
   DOCUMENTS (`firmware/README.md`, walkthrough, `model/docs/`), not in the code.
   GENERATED files also have no comments (the generator writes no comments).
   Functional exceptions only: the `##` target descriptions in the Makefile (used
   by `make help`) and CLI help text that the program prints.
6. **The rules live in CI.** Checkers: `python3 scripts/check_comments.py` and
   `.github/workflows/checks.yml`. A rule that a machine cannot check is turned
   into a check, or removed from this file.

### Close the loop
7. **Every failure the user catches becomes a skill the same day**
   (`.claude/skills/<nama>/SKILL.md`, or a user repo skill if the rule is
   generic). The same failure must not happen again.
8. **Every skill has an eval** in skill-creator format
   (`.claude/skills/<nama>/evals/<kasus>/{prompt.md,case.yaml,graders/}`) and a
   trigger set `triggers/evals.json`, graded by a model different from the
   author, target = pass all graders, **at most 3 rounds**. Not passing after the
   3rd round → stop, write the best score and the findings in the commit
   message, then ask the user. Eval questions are narrow with a definite answer
   (the original failure). A score that does not rise for two rounds in a row =
   stop early. Scores are not stored as a table in the repo.
9. **Checks green → commit right away**, without waiting for approval; the user
   reviews afterwards. One revert is cheaper than a blocked agent.
   Push to the remote stays only on explicit request.

### Refactor
10. **Refactor without behavior change.** Refactor commits must not change behavior; never mix with feature or bugfix changes.
11. **Every commit green.** Each commit must leave all tests green.
12. **Area without tests: stop and ask.** If the area lacks test coverage, stop and
    ask before refactoring. A rename-only
    commit (only identifiers and file names change, every string literal stays) counts
    as covered when an equivalence proof passes: compiled objects of both revisions
    identical after applying the rename map (C/C++), or ASTs identical after applying it
    (Python). The tool that did this for the English refactor is kept in git, not in the
    tree: `git show a0754a6:scripts/renames.py > /tmp/renames.py` (its maps are at that
    same commit). A commit that changes a string literal, CLI flag, make target or
    printed text is not a refactor.

## Skills, load before starting

Skills often do not trigger on their own; load the skill in this table before
starting matching work. The table is updated whenever a skill is added, renamed,
or extracted.

| Task | Load skill |
|---|---|
| "tambah buffer/antrean/durasi maksimum", "tulis berkas di loop", firmware with limits or slow operations | `firmware-limits` (loads `firmware-bounded-limits`) |
| "sunting buku-pa", "Bab 1", "tanya user soal isi buku", proposal sync | `book-follows-proposal` |
| "bikin slide", "deck seminar", "slide bimbingan", "PPTX sidang" | `defense-deck` |
| "ingest", "sync balik", "masukin suntingan Word ke tex" | `word-ingest` (loads `wordcraft-latex-ingest`) |
| "PCB", "skematik KiCad", "routing", "Freerouting", KiCad files from a friend | `kicad-pcb` (loads `kicad-mcp-pcb`) |
| "tambah bab/subbab", "abstrak", "Bab 4/Bab 5", "pasang gambar", "QA sebelum kumpul" | `report-structure` |
| "buat tabel", "rapikan tabel", Bab 4 result tables | `report-tables` |
| "dokumentasikan fitur", "update docs", `docs/features` pages, after a firmware/model feature changes | `feature-docs` |
| writing or editing code (C/C++, Python, shell, `platformio.ini`), prompts to code-writing subagents | `no-code-comments` (loads the user skill of the same name) |
| "indeks rujukan", "daftar bukti", documents with links to local files | user skill `local-file-links` (PA: reference index in `laporan/pustaka/`, evidence list from `model/artifacts`) |
| "rapikan biar tidak AI slop", "humanize", "bersihkan gaya tulis" | `report-antislop` (loads `indonesian-antislop-writing`) |
| "gambarin", "bikin draf gambar", "revisi gambar proposal", "gambarnya kekecilan", filling a `PLACEHOLDER-GAMBAR` illustration | `report-figures` (loads `antislop`, `antislop-ui`, `antislop-human`) |
| `git stash`/`reset`/`checkout` path/`clean`, committing while another session or agent is working, `index.lock`, a dirty `git status` blocking | user skill `shared-worktree` |

## Working rules (non-negotiable)

1. **Non-destructive.** Do not delete/move/rename existing files. All file
   creation follows the "create if not present" pattern, never overwrite. Plan
   documents and one-off tools that are finished are deleted per
   **Documentation**, only with the user's approval. A rename through `git mv`
   that is listed in a plan the user approved is allowed, except in `laporan/`
   (still a gate point).
2. **`laporan/` is read-only by default.** `.tex`, `.bib`, `bab/`, `gambar/`
   must not be touched without confirmation. Relative paths are fragile. One
   exception: figure drafts made through the skill `report-figures` may be
   written to `laporan/<projek>/gambar/draf/`. Detailed
   rules (writing style, table/figure conventions, chapter structure) are in
   `laporan/CLAUDE.md`; read it first when working in `laporan/`.
3. **PRD = `model/PRD_Model_Aritmia_TinyML.pdf`** (a PDF, not `.md`; read it with
   Read `pages=`). Follow the function contracts and pitfalls there; no
   vibe-coding.
4. **Search your own repo before designing.** The plans, scripts, and
   mechanisms you need often ALREADY exist and only need to be carried out or
   extended. Example: the replay signal source for tests without hardware
   already exists in the firmware (the "Sumber sinyal" menu, or serial toggle
   `y`), and the R-peak alignment chain is already built in
   `model/scripts/eval_detected_segmentation.py`. Redesigning from scratch in
   such a place = wasted duplicate work.

## Evidence beats rigidity

The rules above protect what is already proven. This section keeps what is
proven from freezing into dogma.

- **The golden reference (`firmware/test/golden_ref.h`) is a REGRESSION TEST, not
  a design fence.** What it guarantees: C and Python compute the same thing. What
  it does NOT guarantee: that the parameters are optimal. If there is concrete
  evidence (a paper with ablations, or our own experiment) that other parameters
  are better, change the parameters, then **regenerate** the golden
  (`python scripts/export_golden.py` from `model/`) and run `pio test -e native`.
  Regeneration = routine procedure. Refusing a change "because the golden will
  change" = the wrong reason.
- **Adopt from a paper only if the paper ablates its claim.** If a paper just
  uses method X without ever comparing it, what we have is not evidence but
  precedent. It may be copied, after we ablate it ourselves.
  Example: Dias 2021 ablates jitter (Tables 3, 6-8, 33 repetitions) but never
  ablates its filter, so the jitter was adopted and the filter was not.
- **Do not copy a paper's empirical constants if we can measure our own.**
  Dias uses uniform jitter of ±18 samples because they have no detector.
  We have one, and the residual has a completely different shape (sharp core
  ±2, heavy tail up to 54). Copying 18 means training the model against an
  error that is not ours.
- **Experiment knobs go through the environment, not through editing final
  values.** `config.py` reads `PA_WIN_PRE`, `PA_WIN_POST`, `PA_HOS` (and other
  ablation knobs recorded in `model/CLAUDE.md`); without env, the values are
  exactly the defaults. Ablations run without touching a gate point. The
  WINNING value is locked in by changing the default, and that is still a gate
  point.

## How the user wants to work

- **Data, not assumptions.** The cause of a problem (broken hardware, slow broker,
  noise from a module) may be concluded only after it is measured. If a hypothesis
  fails, add a counter/measure first, do not guess the next suspect and do not
  go in circles.
- **An approved plan is carried out to the end** without asking for confirmation
  at every step; stop only at an anomaly or a gate point. Work that can run in
  parallel may be spread across subagents.
- **Design/trade-off decisions belong to the user.** Present options + a
  recommendation with its reasons (cite the PRD/data), then let the user choose.
  Proposals from paper research that deviate from the original plan are
  summarized first, before implementation.
- **Exploration outside the plan does not automatically become the plan.** A
  side check of a spec or experiment is only reported; do not write it into a
  plan document unless asked.
- **The official reference beats memory.** A module's official datasheet/docs
  (electrode placement, I2C pins, buzzer polarity, etc.) that the user cites
  are followed; do not argue from memory.
- **Simple.** Do not split functions/abstractions without a reason; avoid
  over-engineering.
- **Report only when asked.** When working on the program, do not slip in or
  suggest `laporan/` work as a next step.
- **Git:** commit automatically after the checks are green (Hard rule 9); push
  only when explicitly asked (the user often pushes themselves).
- **End a task with a short report:** what was done, the verification numbers,
  and the work remaining against the plan.
- **What is learned is recorded in the repo**, not only in chat: decisions and
  pitfalls to the relevant `CLAUDE.md`, explanations to the walkthrough/README,
  never to code comments.

## Documentation

- **Every finished piece of work gets its documentation written too**, complete
  enough that the user can repeat it without Claude: where data is stored, how to
  pull it, how to analyze it and make plots, how to toggle/flag. Model
  walkthrough: rules in `model/CLAUDE.md`, map in `model/docs/README.md`.
- **Active document = official documentation of the CURRENT state.** No revision
  markers ("CORRECTION", "revised from ...", "update:"), session narration,
  relative-time words ("formerly", "originally", "it turned out"), progress
  checklists, or marker emoji. A claim that was once corrected is written only in
  its correct version. Design rationale and rejected alternatives are still
  written ("Alternative X is not used because ..."). Dates only as measurement
  metadata ("Test condition: N16R8 board, 19 Sep 2026").
- **`docs/` = working documents that are still valid** (work lists, research
  whose action is not yet decided, plans not yet finished), named
  `YYYY-MM-DD-<topik>.md`, listed in `docs/README.md`.
- **History is in git, not in documents.** Plans and notes that are finished
  are deleted after their results are recorded in the document that applies;
  operational facts that still apply (data location, how to recover,
  configuration values) are moved first to the component's README or
  walkthrough. One-off tools are deleted when they are no longer referenced.
- **What is obsolete is removed from active documents and code**, not marked
  "old" (example: the active buzzer that is no longer used).
- **Language:** English for everything developers and agents read: docs, README,
  `CLAUDE.md` files, skills, commit messages, identifiers, file names, script output,
  serial log text. Indonesian stays for `laporan/` text, `presentasi/`, TFT strings
  and the frozen data contracts below. English docs
  use decimal point and comma thousands; laporan keeps decimal comma (0,6594) and dot
  thousands (85.812). Things that are run (build, record, flash, calibrate) are
  written as procedures: numbered steps, commands in code blocks, expected result.
- **Frozen data contracts (stay Indonesian or unchanged, never renamed or translated):**

  | What | Where | Why |
  |---|---|---|
  | Serial protocol tokens `SIMPAN`, `---MULAI---`, `---SELESAI---` | `firmware/src/recorder.cpp`, `power.cpp`; parsed by `model/scripts/pull_recording.py`, `pull_power.py`, `record_flow_check.py` | wire protocol |
  | Power line `DAYA p<n> n= I= sd= mA V= P= mW beat= lewat= replay=` | `firmware/src/power.cpp`; regex in `model/scripts/measure_power.py` | wire protocol |
  | Recording header `# fs= n= lewat= lepas= [lanjutan= celah=]`, `# jeda`, CSV columns | `firmware/src/recorder.cpp`; read by `model/scripts/analyze_recording.py` and the official 22 Oct 2026 recordings | old data must keep parsing |
  | Serial command letters (`r j d l h y p k m q s v V w t T b`) | `firmware/src/serial_cmd.cpp` | documented interface |
  | LittleFS paths `/rekaman.csv`, `/daya/NNN.csv`, recording names `*-rekam-NNN` | `firmware/src/recorder.cpp`, `power.cpp` | files on the board and in `model/data/recordings/` |
  | NVS namespace and keys | `firmware/src/app_settings.cpp` | settings stored on the board |
  | MQTT topics and JSON keys | `firmware/src/ecg_mqtt.cpp`, `dashboard/` | ThingsBoard keys |
  | All TFT strings | `firmware/src/menu.cpp`, `display.cpp`, `gate.cpp` | the book quotes them |
  | `WIFI_DAFTAR`, `BROKER_DAFTAR` | untracked `firmware/include/wifi_secrets.h`, `wifi_secrets.example.h` | private local file on every machine |
  | Paths and file names under `model/artifacts/`, `model/data/` and the names scripts write there | `scripts/export_artifacts.sh` → `laporan/*/gambar/` | laporan figures |
  | Indonesian pattern lists in `scripts/check_slop.py` | | the data it checks |
  | File names and CLI flags of `scripts/cek_docx.py`, `scripts/rilis.py` (incl. `--catatan`, and its tag body `halaman= galat_log=`), `scripts/cek_tabel.py`, `dashboard/ukur_pipeline.py` | `laporan/shared/Makefile.inc` runs the first two; `laporan/CLAUDE.md` names the last two | renaming them breaks the laporan build or its instructions |
  | Everything under `laporan/` and `presentasi/`, KiCad files, git tags `rilis/*` and `pra-bersih` | | thesis text, hardware data, history |
- **Result files** (recordings, plots) are named with a timestamp and grouped in
  one folder per category, not a generic name such as "percobaan".

## Artifacts: producer → consumer

- `model/` → `model_int8.h` → `firmware/include/` (GENERATED, do not edit by hand)
- `model/scripts/export_golden.py` → `firmware/test/golden_ref.h` (GENERATED)
- `model/artifacts/metrics/*.png` & `dashboard/preview.png` → figure →
  `laporan/*/gambar/` (`export_artifacts.sh --laporan`)
- Synced via `scripts/export_artifacts.sh`. **Do not copy by hand.**
- Commit policy: **B1**: final figures + `.h` are committed; raw MIT-BIH data
  and intermediate `.npz` are ignored (`.gitignore`).

## Build

- Laporan:  `cd laporan/<projek> && make pdf` → `output/main.pdf` (gitignored).
  Projects: `proposal-pa` (A4), `buku-pa`, `surat-magang`; `shared/` = preamble +
  `Makefile.inc`. **Paper size is fixed per project** (`\input ../shared/size-aX`),
  there is no `make a4`/`make a5`.
- Model:    `cd model && make <target>` (list: `make help`; summary in
  `model/CLAUDE.md`). Python 3.11.9 (`model/.python-version`), venv in
  `model/.venv`, deps in `model/requirements.txt`. Ad-hoc check/exploration
  scripts → `model/scripts/` (run from the `model/` folder).
- **Laporan checkpoint:** the user says *checkpoint* → commit first, then `make rilis` in `laporan/buku-pa` and `laporan/progres-pa-1` (those rejected because nothing changed are skipped), report `version=` and `diff=`. The release tag is not pushed.
- Firmware: see **ESP32 / microcontroller** below.
- Dashboard: `cd dashboard && docker compose up -d` (ThingsBoard CE).

## ESP32 / microcontroller → PlatformIO

All ESP32/microcontroller work (build, flash, monitor, test, library check,
board/pin check) goes **through the PlatformIO CLI (`pio`)**, not the Arduino
IDE/CLI, not `idf.py`/`esptool.py` directly. The single configuration =
`firmware/platformio.ini` (env `esp32-s3` = main firmware + `test_hw_*` device
tests on the N16R8 board, env `native` = tests on the PC). Run from `firmware/`.

- Build:        `pio run` (default env `esp32-s3`)
- Flash:        `pio run -t upload` · monitor: `pio device monitor` (115200)
- Port/board:   `pio device list` · `pio boards <kata>`
- PC test:      `pio test -e native` (no board) · on device: `pio test -e esp32-s3`
- Library:      `pio pkg search|show <nama>`; adding to `lib_deps` in
  `platformio.ini` = new dependency → **gate point, ask first**.
- Board/framework info: read from `~/.platformio/platforms/espressif32` &
  `~/.platformio/packages/` (installed versions) before guessing from memory.
- **Board plugged in → Claude itself** runs `pio device list`, flash,
  monitor, and reads the result. Do not hardcode the port: it moves between
  `/dev/ttyACM*` and `/dev/ttyUSB*`.
- **Test without a sensor through a flag/simulation mode** (golden replay,
  serial toggle, build flag), not a separate copy of the code.
- **Before changing a pin/driver**, make sure which hardware is in use
  (breadboard or PCB rev N). The single pin map is in
  `firmware/include/board.h`; the pin map and circuit rationale of the PCB are in
  `hardware/mainboard/README.md` (sections "Pin map" and "Module circuit rationale").

## Diagrams & laporan figures

- **Illustration figures for `laporan/` are draw.io drafts made through the skill
  `report-figures` and approved by the user** (dev docs in `docs/features/` may contain
  Claude-made Mermaid with real names). The figure position in the `.tex` still holds a
  **placeholder** + a content spec card (type, message, required elements,
  reading flow, material in the repo); template: skill `report-structure` rule 9.
  Claude may draft the figure from that card in `laporan/<projek>/gambar/draf/`
  (house style, `python3 scripts/check_figures.py` green, exported and looked at,
  antislop Delivery Gate); the placeholder is replaced only after the user approves
  the draft. No Mermaid, TikZ, PlantUML, Graphviz, figure scripts, or AI images in
  `laporan/`. A proposal revision changes only the card's "Ubah" column and keeps the
  user's style. Device photos and screen mockups stay with the user. The caption,
  `\label`, `\ref`, and the intro/explanatory paragraph are still written in final form.
  Remaining placeholders: `grep -rn "PLACEHOLDER-GAMBAR" laporan/`.
- Experiment data plots (confusion matrix, curves, latency charts) produced by
  the repo pipeline are not illustrations: reference the already-exported file. If
  it does not exist yet → placeholder + name the script that produces it, do not
  write a new plot script unless asked.
- The requirement labels `RM1..RM4` **MUST NOT appear** in any diagram.

## Writing the report (progress / PA book)

Writing reference = four skills in `.claude/skills/`: `report-structure` (chapter
skeleton, thread, register, figure placeholders, QA before submission),
`report-antislop` (layer on top of the user skill `indonesian-antislop-writing`:
paragraphs without AI-writing patterns, checked by `scripts/check_slop.py`), `report-tables` (tables), and `book-follows-proposal` (Bab 1
and proposal sync). `narasi-pa` is inactive and
kept in `.claude/skills-arsip/narasi-pa/` as a reference. The dissection of 6
PENS PA reports that rules come from is already distilled into the skills. The writing style rules remain in `laporan/CLAUDE.md`.
Scope decisions the user already made: individual PA, anonymous test subjects
(codes S01, S02, ...), test place = laboratory, TLS/transport security is not
discussed at all. The book covers only MIT-BIH: SVDB/INCART and the
cross-database test are not written even though the results are in the repo (19 Oct 2026).
References prefer 2020 and later, except the original source of a method/data
and standards that are still in force (lecturer's directive; rationale per entry in
`laporan/CLAUDE.md`, section Daftar Pustaka). Full book =
`laporan/buku-pa` (in progress), stage 1 book = `laporan/progres-pa-1`
(buku-pa without INA219 and power supply, content 50–70% according to the supervisor;
regeneration procedure in `laporan/CLAUDE.md`). **`laporan/proposal-pa` has been
submitted and frozen (15 Oct 2026): no longer edited, including its
`.bib`.** The book has no "changes from the proposal" table and does not
give numbered "Tujuan N" labels in headings or sentences; style follows the
AFIB book (user decision 19 Oct 2026, skill `report-structure` rule 2).

- **Internal repo work labels MUST NOT appear in the official report text**
  (printed `laporan/**/*.tex`): HW-n, Fase n / Fase A–G, Task n, T-n/K-n,
  PCB revisions (rev1, rev2, "PCB revisi kedua"),
  file paths, script names, env/knob names (`PA_*`, PlatformIO env), and the word
  "walkthrough". Those labels are only for internal repo documents (`model/docs/`,
  `CLAUDE.md`, README). In the report, name the content with general terms
  ("pengujian akuisisi sinyal tubuh", "ablasi ukuran window"). The
  `% sumber:` comments in `.tex` are not printed, so they may contain paths.

## Gate points (stop, ask for confirmation)

- Moving/renaming anything in `laporan/` → use `git mv`, confirm first.
- Adding a new dependency → ask first; prefer stdlib/what already exists.
- Changing a final value in `model/config.py` (FS, bandpass, window, label map)
  → belongs to the user, confirm first.
- Push to the remote → only on explicit request.
- Refactor in an area without tests that cannot be proven equivalent (Hard rule 12)
  → ask first.
