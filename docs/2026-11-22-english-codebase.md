# English codebase and docs

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** everything developers and agents read in this repo (identifiers, file names, script output, docs, skills, `CLAUDE.md` files, commit messages) is English, without changing what the firmware, the model pipeline or the thesis computes. New per-feature docs follow the finance-project `feature-docs` skill.

**Architecture:** follows the finance-project English refactor of 21 Nov 2026 (commits `346ceef` language rule, `d50820a` docs split, `f634089` deadcode, `bcc295b` API messages, `ee4e9c6` skills, `83d8d51` checker rename). Every rename commit carries a mechanical equivalence proof (firmware object disassembly or Python AST, both compared after applying `scripts/rename_map.tsv`). Behavior changes (translated output text, renamed CLI flags and make targets) are separate commits from renames.

**Tech stack:** Python 3.13 stdlib (system `python3`, needed for f-string tokenizing), PlatformIO + the installed `toolchain-xtensa-esp32s3` binutils, pytest (`model/.venv`), git worktrees. No new dependency.

---

## Decisions (user, 22 Nov 2026)

| # | Question | Decision |
|---|---|---|
| D1 | What becomes English | Like finance: `CLAUDE.md` ×3 and `laporan/CLAUDE.md`, READMEs, `docs/`, `model/docs/` walkthroughs, identifiers, file names, script output, commit messages, all repo skills. Laporan-writing skills get English instructions and keep their Indonesian examples word for word. `laporan/**/*.tex` body text and `presentasi/` stay Indonesian. |
| D2 | Device text | TFT menu and labels stay Indonesian (Bab 3 and Bab 4 of `buku-pa` quote them). Free-form serial log lines become English. |
| D3 | Contracts | Data contracts are frozen (list below). The `% sumber:` comments in `laporan/buku-pa` and `laporan/progres-pa-1` are updated to the new paths in one laporan-only commit. `laporan/proposal-pa` is frozen and not touched. |
| D4 | Areas without tests | A rename-only commit counts as covered when the equivalence proof passes. If the proof cannot be made for an area, stop and ask about that area. |
| D5 | Mermaid | Allowed in dev docs under `docs/features/`. The no-diagram rule stays for `laporan/` figures. |
| D6 | Docs site | Plain Markdown read on GitHub or in an editor, no VitePress. The build check becomes `pointers.sh` plus a stdlib link checker in CI. |
| D7 | Walkthroughs | New `docs/features/` pages cover device and system features; the module, menu and serial sections of `firmware/README.md` move into them. The 15 `model/docs/*-walkthrough.md` files are translated and kept as deep dives the pages link to. |

Defaults taken without asking (change them before Phase 5 if wrong):

- English docs use English number format: decimal point and comma thousands (`0.6594`, `85,812`). Laporan keeps Indonesian format.
- English prose follows the antislop core: no em dash (`—`), none of its buzzwords, specific claims only.
- Dead-code scan during planning (22 Nov 2026, AST scan of all tracked `*.py` plus a zero-reference scan of every function declared in `firmware/include/*.h`) found no item. The audit of 21 Nov was executed earlier the same day. One closing re-audit stays in Phase 7.

## Refactoring rules (user, added to `CLAUDE.md` in Task 0.1)

- Refactor commits must not change behavior; never mix with feature or bugfix changes.
- Each commit must leave all tests green.
- If the area lacks test coverage, stop and ask before refactoring.

In this plan: a commit that changes any string literal, CLI flag, make target or printed text is **not** a refactor. It gets its own `feat`/`chore` commit and its own evidence.

## Frozen (never renamed or translated)

| What | Where | Why |
|---|---|---|
| Serial protocol tokens `SIMPAN`, `---MULAI---`, `---SELESAI---` | `rekam.cpp`, `daya.cpp`; parsed by `model/scripts/pull_recording.py`, `pull_daya.py`, `uji_alur_rekam.py` | wire protocol |
| Power line `DAYA p<n> n= I= sd= mA V= P= mW beat= lewat= replay=` | `daya.cpp`; regex in `model/scripts/measure_power.py:13` | wire protocol |
| Recording header `# fs= n= lewat= lepas= [lanjutan= celah=]`, `# jeda`, CSV columns | `rekam.cpp`; read by `analyze_recording.py` and the official 22 Oct 2026 recordings | old data must keep parsing |
| Serial command letters (`r j d l h y p k m q s v V w t T b`) | `serial_cmd.cpp` | documented interface, muscle memory |
| LittleFS paths `/rekaman.csv`, `/daya/NNN.csv`, recording names `*-rekam-NNN` | `rekam.cpp`, `daya.cpp` | files already on the board and in `model/data/recordings/` |
| NVS namespace and keys (`"rekam"` and the `kunci` strings) | `konfig.cpp` | stored settings on the board |
| MQTT topics and JSON keys | `ecg_mqtt.cpp`, `dashboard/` | already English, ThingsBoard keys |
| All TFT strings | `menu.cpp`, `tampilan.cpp`, `gerbang.cpp` | D2 |
| `WIFI_DAFTAR`, `BROKER_DAFTAR` | untracked `firmware/include/wifi_secrets.h` and `wifi_secrets.example.h` | private local file on every machine |
| Paths and file names under `model/artifacts/` and `model/data/`, and the output names scripts write there | export to `laporan/*/gambar/` | laporan figures |
| Env knobs `PA_WIN_PRE`, `PA_WIN_POST`, `PA_HOS`, `PA_QRSW`, `PA_RR_RATIO` | `model/config.py` | already English |
| Indonesian pattern lists in `scripts/cek_slop.py` | | they are the data it checks |
| Git tags `rilis/*`, `pra-bersih` | | history |
| `laporan/**/*.tex` body, `laporan/proposal-pa/**`, `presentasi/**`, KiCad files, `model/PRD_Model_Aritmia_TinyML.pdf` | | D1, D3 |

## Proof per area (D4)

| Area | Tests that exist | Rename proof | Output-change proof |
|---|---|---|---|
| `firmware/src`, `firmware/include` (17 modules) | native: `test_preproc`, `test_ina219`, `test_mqtt` (cover `ecg_pipeline`, `ecg_live`, `ina219`, `ecg_mqtt`); device: `test_inference`, `test_hw_*` | `scripts/renames.py firmware` (object disassembly identical after the map) + `pio test -e native` | board run (Task 4.1); no board = stop and say so |
| `firmware/test` | same | `pio test -e native` (same test count) | `pio test -e esp32-s3` on the board |
| `model/src` | pytest (`model/tests`, 92 tests) | `scripts/renames.py python` + pytest (same collected count) | pytest |
| `model/scripts` | pytest for `analyze_recording`, `kualitas_jendela`, `plot_rekaman`, `prep_beats`, `tren_kualitas`, jitter | `scripts/renames.py python` | pytest where covered; otherwise run the script on a fixed input before and after (stated per task) |
| `scripts/*.py` | `--uji` self-tests in `cek_slop`, `cek_skill`, `cek_tabel` | `scripts/renames.py python` + self-tests | self-tests + a run on a fixed input |
| `dashboard/*.py` | none | `scripts/renames.py python` | ask the user (no runnable fixed input without ThingsBoard) |
| Shell (`scripts/export_artifacts.sh`, `scripts/uji_pemicu.sh`, `.githooks/pre-commit`) | none | no tool | **stop and ask** before touching anything beyond the file name |
| Generators `export_golden.py`, `export_model_h.py` | `pio test -e native` uses `golden_ref.h` | regenerated headers identical to the old ones after applying the map | same |

## File map

| File | Phase | Purpose |
|---|---|---|
| `CLAUDE.md` | 0, 5 | refactoring rules, language rule, Mermaid scope, rename permission; translated in Phase 5 |
| `scripts/renames.py` (new, one-off) | 0 | `apply`, `leftovers`, `python`, `firmware` subcommands |
| `scripts/rename_map.tsv` (new, one-off) | 0, grows in 2–3 | `old<TAB>new`, one line per identifier, file name or phrase |
| `scripts/glossary.tsv` (new, one-off) | 0 | Indonesian word → English word, drives the map and `leftovers` |
| `firmware/**` | 2, 4 | renames, then English serial text |
| `model/**`, `dashboard/*.py`, `scripts/**` | 3, 4 | renames, then English output, flags and targets |
| `.claude/skills/feature-docs/` (new), `scripts/check_docs.py` (new), `.github/workflows/cek.yml` | 5 | feature-docs skill and link checker |
| `docs/features/*.md` (new), `docs/README.md`, `firmware/README.md` | 5 | per-feature pages |
| all other `*.md` outside `laporan/` and `presentasi/` | 5 | translation |
| `.claude/skills/*` | 5 | English, renamed folders |
| `laporan/buku-pa/**/*.tex`, `laporan/progres-pa-1/**/*.tex` (comment lines only), `laporan/shared/Makefile.inc` | 3, 6 | script names, `% sumber:` pointers |

## Order and parallelism

| Phase | Parallel | Gate |
|---|---|---|
| 0 rules and tools | no | none |
| 2 firmware renames | no (shared headers) | none |
| 3 Python renames | up to 3 agents, one per area (`model/src`+tests, `model/scripts`, `scripts/`+`dashboard/`), never the same file | shell scripts: ask |
| 4 output translation | no | board connected for 4.1 |
| 5 docs and skills | 4 agents for translation, one page per agent for features | skill evals at most 3 rounds |
| 6 laporan pointers | no | `make pdf` text identical |
| 7 closeout | no | user approves deleting the one-off tools |

---

## Phase 0: rules and tools

### Task 0.1: repo rules

**Files:** Modify `CLAUDE.md`

- [ ] **Step 1:** Under `## Aturan keras`, after `### Tutup lingkarannya`, add:

```markdown
### Refactor
10. Refactor commits must not change behavior; never mix with feature or bugfix changes.
11. Each commit must leave all tests green.
12. If the area lacks test coverage, stop and ask before refactoring. A rename-only
    commit counts as covered when `python3 scripts/renames.py firmware|python <rev-a> <rev-b>`
    passes. A commit that changes a string literal, CLI flag, make target or printed
    text is not a refactor.
```

- [ ] **Step 2:** In `## Aturan kerja (non-negotiable)` rule 1, append: "Rename lewat `git mv` yang tercantum di rencana yang disetujui user diperbolehkan."
- [ ] **Step 3:** In `## Dokumentasi`, replace the `**Bahasa:**` bullet with:

```markdown
- **Language:** English for everything developers and agents read: docs, README,
  `CLAUDE.md` files, skills, commit messages, identifiers, file names, script output,
  serial log text. Indonesian stays for `laporan/` text, `presentasi/`, TFT strings
  and the data contracts frozen in `docs/2026-11-22-english-codebase.md`. English docs
  use decimal point and comma thousands; laporan keeps decimal comma (0,6594) and dot
  thousands (85.812).
```

- [ ] **Step 4:** In `## Diagrams & gambar laporan`, append: "Larangan ini berlaku untuk `laporan/`. Dokumen dev di `docs/features/` boleh memuat Mermaid buatan Claude dengan nama nyata (fungsi, topik MQTT, berkas)."
- [ ] **Step 5:** Run `grep -c '—' CLAUDE.md` before and after; the added lines contain none.
- [ ] **Step 6:** Commit (English message from here on):

```bash
git add CLAUDE.md
git commit -m "docs(claude-md): refactoring rules and English language rule" -m "Decisions D1-D7 in docs/2026-11-22-english-codebase.md. Evidence: text-only change; git diff --stat CLAUDE.md shows only the four edited sections."
```

### Task 0.2: rename map, glossary, `scripts/renames.py`

**Files:** Create `scripts/renames.py`, `scripts/rename_map.tsv` (empty), `scripts/glossary.tsv`

- [ ] **Step 1:** Create `scripts/glossary.tsv` (tab-separated, one Indonesian word per line). Each English word appears once, so two Indonesian words never collapse into one name:

```
akuisisi	acquisition
ambang	threshold
ambil	fetch
antre	queue
atas	upper
atur	configure
ayun	swing
bagian	part
baik	good
baca	read
baru	new
batal	cancel
batas	limit
bawah	lower
beku	freeze
berkas	file
bersih	clean
bip	beep
bisu	mute
blok	block
buang	drop
buka	open
bulan	month
bunyi	sound
buruk	bad
cari	search
cetak	print
daftar	list
dasar	base
daya	power
dengung	hum
denyut	pulse
deteksi	detect
diagnosa	diagnostics
diam	idle
dijeda	paused
dilewati	skipped
dinamis	dynamic
disimpan	saved
ditekan	pressed
ditolak	rejected
fase	phase
gagal	failed
gambar	draw
ganti	switch
gerbang	gate
hapus	delete
hasil	result
hilang	lost
hitung	count
isi	fill
jadwal	schedule
jala	mains
jalan	running
jaringan	network
jeda	pause
jendela	window
kalibrasi	calibration
kanal	channel
kirim	send
klasifikasi	classifier
klik	click
konfig	settings
kontak	contact
kualitas	quality
lama	long
lambat	slow
langkah	step
lanjut	resume
lapor	report
layani	service
layar	screen
lebar	width
lepas	leadoff
lewat	missed
lewati	skip
lihat	look
lulus	pass
maks	max
mentah	raw
menulis	writing
mulai	begin
nada	tone
nilai	score
nomor	number
paket	packet
pasang	push
pemanasan	warmup
pendek	short
penuh	full
perangkat	board
periode	period
peringatan	warning
pesan	message
pilih	select
pita	band
rekam	recorder
rekaman	recording
ringkas	summary
ritme	rhythm
sah	valid
salinan	copies
sampel	sample
sesi	session
siapkan	prepare
simpan	save
skala	scale
suntik	inject
sumber	source
tahap	stage
tangga	sweep
tampilan	display
tenang	quiet
terakhir	last
terbuka	isopen
terkirim	sent
tersaring	filtered
tiap	every
tolak	reject
tombol	button
tulis	write
tunggu	wait
uji	test
ukur	measure
ulang	retry
```

Words missing from this list are added by the task that meets them, keeping one English word per Indonesian word.

- [ ] **Step 2:** Create `scripts/renames.py`:

The tool is `scripts/renames.py` (committed in Task 0.2 and hardened after review: repo-wide pairing and guards in the Python check, global string and collision guards, external-keyword check, `-h -t` in the firmware listing, vacuous-pass failure). Read it there; it is not duplicated here.

What each guard prevents:
- `load_pairs` refuses a map with a line that lacks exactly one TAB, a duplicate old key, an explicit key that shadows a derived file stem with another value, two old names sharing one new name (two variables merged into one would still pass the AST and object checks), and chained renames (a new name that is also an old key).
- `apply` and the Python check share one guard function. It refuses a file where a new name is already used for something else, and a new name that already exists anywhere in the same language set (global collision, C/C++ and Python separately).
- An old Python name that also appears inside any string literal of any tracked `.py` file (argparse `dest`, DataFrame columns, `getattr`) is refused: those are interface changes for Phase 4.
- A renamed name used as a keyword argument that is not a parameter of any function defined in the repo is reported as `EXTERNAL-KWARG file:line name` (calls into libraries would change meaning).
- The Python check pairs every `*.py` of rev-a with its counterpart in rev-b (map applied to the basename), so a stale importer of a renamed definition shows as `DIFF` and an unmatched file as `UNPAIRED`. It prints `compared N files` and fails when N is 0.
- C/C++ string and char literals are never edited, so TFT text, NVS keys and protocol tokens cannot change in a rename commit. The object check would catch it anyway, because `-s` dumps `.rodata`.
- The firmware listing includes `-h` (section sizes, so a changed `.bss` array is caught) and `-t` (symbol table with binding and size). The check prints `compared N objects` and fails with `no objects built` when rev-a yields none.
- After `apply`, every file-name key still present in any tracked text file, including skipped directories such as `laporan/`, is listed as `stale <path>:<line> <key>` (report only).

- [ ] **Step 3:** `touch scripts/rename_map.tsv`. Run `python3 scripts/cek_komentar.py scripts/renames.py`. Expected: exit 0.
- [ ] **Step 4: positive control.** `python3 scripts/renames.py firmware HEAD HEAD`. Expected: 17 lines `same <module>.cpp.o -> <module>.cpp.o`, exit 0.
- [ ] **Step 5: rename control.** In a scratch worktree reproduce the planning spike: map line `tombol_suntik	button_inject`, rename it in `firmware/` with `renames.py apply firmware`, commit in the scratch worktree, run `renames.py firmware <base> <scratch-commit>`. Expected: all `same`. Delete the scratch worktree and branch.
- [ ] **Step 6: negative control.** `c=$(git log -1 --format=%h -- firmware/src); python3 scripts/renames.py firmware $c^ $c`. Expected: at least one `DIFF`, exit 1. If it says `same`, the tool cannot see changes: stop.
- [ ] **Step 7: Python controls.** `python3 scripts/renames.py python HEAD HEAD` exits 0 with no lines. `c=$(git log -1 --format=%h -- 'model/*.py'); python3 scripts/renames.py python $c^ $c` prints `DIFF`.
- [ ] **Step 8:** Commit `scripts/renames.py scripts/rename_map.tsv scripts/glossary.tsv` as `chore(scripts): rename map and equivalence checker for the English refactor`, with the outputs of steps 4–7 in the body.

**Planning spike (board-free, 22 Nov 2026), recorded so the next agent does not repeat it.** Two plain `pio run` builds of the same commit give different `firmware.bin` (`menu.cpp` prints `__DATE__`/`__TIME__`, and `VERSI_GIT` comes from `git describe`). With `SOURCE_DATE_EPOCH=0` and a pinned `VERSI_GIT` the binary is reproducible. A pure identifier rename still changes `firmware.bin`, because `-ffunction-sections` places code by symbol name. Comparing per-object disassembly after applying the map gave 17 of 17 objects identical for `tombol_suntik` → `button_inject` plus `tombol.cpp/.h` → `button.cpp/.h`. Without the map, the same comparison showed 24 differing lines. That is why the tool compares objects, not the binary.

---

## Phase 2: firmware renames

### Procedure R (every rename task in Phases 2 and 3 follows it)

1. List the Indonesian identifiers of the area: `python3 scripts/renames.py leftovers <paths>`.
2. Append one map line per identifier and per file name to `scripts/rename_map.tsv`, using `scripts/glossary.tsv` word by word (`rekam_cetak_daftar` → `recorder_print_list`). Public prefixes follow the module table. Constants keep their style (`REKAM_DETIK_MAKS` → `RECORDER_SECONDS_MAX`).
3. New header names: `find ~/.platformio/packages/framework-arduinoespressif32* firmware/.pio/libdeps -name '<new>.h'` must print nothing; if it prints a path, pick another name, because a library header with the same name would shadow or be shadowed.
4. `git mv` the files listed in the task.
5. `python3 scripts/renames.py apply firmware model scripts dashboard docs .claude CLAUDE.md README.md hardware .github .githooks`. Any `REFUSED` line: change the map entry (or move that name to Phase 4) and rerun.
6. `python3 scripts/renames.py leftovers <paths>` prints only names deferred on purpose; list them in the commit body.
7. Commit locally, then prove: `pio run` and `pio test -e native` in `firmware/` (same pass count as before), `python3 scripts/renames.py firmware HEAD~1 HEAD`, plus for Python areas `python3 scripts/renames.py python HEAD~1 HEAD` and `cd model && .venv/bin/pytest -q` (collected count unchanged). On failure fix and `git commit --amend`.
8. `python3 scripts/cek_komentar.py` on touched code, `python3 scripts/cek_skill.py`, and `git grep -n '<old file name>'` outside `laporan/` and the one-off files prints nothing. A hit inside a code string (a `subprocess` path, `open("scripts/...")`) is edited in the same commit, because the old path would break at runtime while the AST check still passes. The checker then reports `DIFF` for exactly those strings; quote them in the commit body as the only accepted differences.
9. Commit `refactor(<area>): English names in <module>` with the proof outputs in the body. One module per commit.

### Tasks 2.1–2.11

Order is leaf modules first, so each commit touches the fewest callers.

| Task | `git mv` | Prefix and guard |
|---|---|---|
| 2.1 | `firmware/include/perangkat.h` → `board.h`, `firmware/src/perangkat.cpp` → `board.cpp` | `perangkat_` → `board_`, `PERANGKAT_H` → `BOARD_H` |
| 2.2 | `konfig.h/.cpp` → `settings.h/.cpp` | `konfig_` → `settings_`, `KONFIG_H` → `SETTINGS_H` (not `config.h`: generic name, library clash risk) |
| 2.3 | `tombol.h/.cpp` → `buttons.h/.cpp`; `firmware/test/test_hw_tombol` → `test_hw_buttons` | `tombol_` → `buttons_`, `TOMBOL_LAMA/PENDEK` → `BUTTON_LONG/SHORT` |
| 2.4 | `gerbang.h/.cpp` → `gate.h/.cpp` | `gerbang_` → `gate_` |
| 2.5 | `akuisisi.h/.cpp` → `acquisition.h/.cpp`; `firmware/test/test_hw_adc` unchanged | `akuisisi_` → `acquisition_` |
| 2.6 | `klasifikasi.h/.cpp` → `classifier.h/.cpp` | `klasifikasi_` → `classifier_` |
| 2.7 | `rekam.h/.cpp` → `recorder.h/.cpp` | `rekam_` → `recorder_`, `REKAM_*` → `RECORDER_*`; string `"rekam"` (NVS key) and `/rekaman.csv` stay |
| 2.8 | `daya.h/.cpp` → `power.h/.cpp` | `daya_` → `power_`, `tangga` → `sweep`; the `DAYA p...` print format stays |
| 2.9 | `diagnosa.h/.cpp` → `diagnostics.h/.cpp`; `test_hw_integrasi` → `test_hw_integration` | `diagnosa_` → `diagnostics_` |
| 2.10 | `tampilan.h/.cpp` → `display.h/.cpp` | `tampilan_` → `display_`; every TFT string stays |
| 2.11 | none | Indonesian internals of `menu.cpp`, `serial_cmd.cpp`, `main.cpp`, `ecg_live`, `ecg_mqtt` (`ecg_mqtt_antre_*` → `ecg_mqtt_queue_*`), `ecg_pipeline` (`ecg_qrs_lebar` → `ecg_qrs_width`), `ina219` (`ina219_baca` → `ina219_read`), `VERSI_GIT` → `GIT_VERSION` in `platformio.ini` and `menu.cpp`, `firmware/test/*.cpp` |

- [ ] Task 2.1
- [ ] Task 2.2
- [ ] Task 2.3
- [ ] Task 2.4
- [ ] Task 2.5
- [ ] Task 2.6
- [ ] Task 2.7
- [ ] Task 2.8
- [ ] Task 2.9
- [ ] Task 2.10
- [ ] Task 2.11

### Task 2.12: generated headers

**Files:** `model/scripts/export_golden.py`, `firmware/test/golden_ref.h`, `firmware/include/ecg_preproc.h`

The generator writes C names as strings (`ECG_N_RR_DASAR`, `ECG_QRSW_CARI`, `ECG_LIVE_TIAP`), so the AST check reports `DIFF` for it on purpose. The proof is on its output.

- [ ] **Step 1:** Map lines for the emitted Indonesian names (`ECG_N_RR_DASAR` → `ECG_N_RR_BASE`, `ECG_QRSW_CARI` → `ECG_QRSW_SEARCH`, `ECG_LIVE_TIAP` → `ECG_LIVE_EVERY`, plus any other `leftovers` hit in `firmware/include/ecg_preproc.h` and `firmware/test/golden_ref.h`).
- [ ] **Step 2:** Edit the strings in `export_golden.py` to the new names; apply the map to firmware callers (Procedure R step 5).
- [ ] **Step 3:** `cd model && .venv/bin/python scripts/export_golden.py`. Then prove the output equals the old output after renaming:

```bash
git show HEAD:firmware/test/golden_ref.h > /tmp/old_golden.h
python3 - <<'EOF'
import sys
sys.path.insert(0, "scripts")
import renames
pairs = renames.load_pairs(renames.MAP)
old = renames.apply_c(open("/tmp/old_golden.h").read(), pairs)
new = open("firmware/test/golden_ref.h").read()
print("identical" if old == new else "DIFFERENT")
EOF
```

Expected: `identical`; same for `ecg_preproc.h`.
- [ ] **Step 4:** `renames.py firmware HEAD <commit>` all `same`; `pio test -e native` same pass count. Commit `refactor(firmware): English names in generated headers`.

---

## Phase 3: Python renames

Procedure R applies. Map lines for file renames list the file name (`cek_fp.py	check_fp.py`); the stem entry for imports is derived automatically.

Run Task 4.2 (English output text) for an area before its Phase 3 rename. Indonesian messages contain the same words as the variables (`jendela`, `hasil`), and `apply` refuses a Python name that also appears in a string literal. Once the messages are English, most of those refusals are gone. Names that still collide (for example `lewat`, used in the frozen `DAYA` regex) keep their Indonesian name and are listed in the commit body.

### Task 3.1: `model/src` and `model/tests`

- [ ] Internal Indonesian names in `model/src/*.py` and `model/config.py` constant names: `SPLIT_SETIAP_KE` → `SPLIT_EVERY_NTH`, `DB_LATIH` → `TRAIN_DATABASES`, `JITTER_SALINAN` → `JITTER_COPIES`, `MIN_PRESISI_NAMA` → `MIN_NAMED_PRECISION`. Values stay; only names change, so the `config.py` gate point (final values) is not touched.
- [ ] Test function names in `model/tests/*.py` (`test_split_disjoint_dan_48` → `test_split_disjoint_and_48`). `git mv model/tests/test_kualitas_jendela.py model/tests/test_window_quality.py`, `test_plot_rekaman.py` → `test_plot_recording.py`, `test_tren_kualitas.py` → `test_quality_trend.py` (these follow Task 3.2's script names; run 3.2 first if done in parallel).
- [ ] Proof: `renames.py python`, `cd model && .venv/bin/pytest -q --collect-only | tail -1` equal before and after, `pytest -q` green. One commit for `src`+`config.py`, one for `tests`.

### Task 3.2: `model/scripts`

| Old | New |
|---|---|
| `ablasi.py` | `ablation.py` |
| `cek_fp.py` | `check_fp.py` |
| `cek_kalibrasi.py` | `check_calibration.py` |
| `cek_lead.py` | `check_lead.py` |
| `cek_titik_operasi.py` | `check_operating_point.py` |
| `kualitas_jendela.py` | `window_quality.py` |
| `metrik_tambahan.py` | `extra_metrics.py` |
| `plot_fase0.py`, `plot_fase1.py`, `plot_fase1_segment.py` | `plot_phase0.py`, `plot_phase1.py`, `plot_phase1_segment.py` |
| `plot_rekaman.py` | `plot_recording.py` |
| `pull_daya.py` | `pull_power.py` |
| `ringkas_ablasi.py` | `summarize_ablation.py` |
| `tahap2.py` | `second_stage_rules.py` |
| `tren_kualitas.py` | `quality_trend.py` |
| `uji_alur_rekam.py` | `record_flow_check.py` (not `test_*`: pytest would collect it) |
| `ukur_jitter.py` | `measure_jitter.py` |

- [ ] Callers in `model/Makefile` recipes, docs and skills are updated by `apply` (file names contain a dot). Output file names the scripts write (`fase0_100.png`, `akuisisi_<ts>.png`) are strings and stay (Frozen).
- [ ] Batch by subject, one commit each: plots; checks (`cek_*`); recording and power (`plot_rekaman`, `pull_daya`, `uji_alur_rekam`, `tren_kualitas`, `kualitas_jendela`); ablation and jitter; the rest. Proof per commit: `renames.py python`, pytest for covered scripts, `python3 -m py_compile` for all.

### Task 3.3: repo `scripts/` and `dashboard/`

| Old | New |
|---|---|
| `scripts/cek_komentar.py` | `scripts/check_comments.py` |
| `scripts/cek_skill.py` | `scripts/check_skills.py` |
| `scripts/cek_slop.py` | `scripts/check_slop.py` |
| `scripts/cek_tabel.py` | `scripts/check_tables.py` |
| `scripts/cek_docx.py` | `scripts/check_docx.py` |
| `scripts/rilis.py` | `scripts/release.py` |
| `scripts/sajikan.py` | `scripts/serve.py` |
| `scripts/unduh_pustaka.py` | `scripts/fetch_references.py` |
| `scripts/uji_pemicu.sh` | `scripts/trigger_eval.sh` |
| `dashboard/ukur_pipeline.py` | `dashboard/measure_pipeline.py` |

- [ ] Callers: `.github/workflows/cek.yml`, `.githooks/pre-commit`, `laporan/shared/Makefile.inc`, `laporan/CLAUDE.md`, `CLAUDE.md`, skills. `apply` skips `laporan/`, so edit `laporan/shared/Makefile.inc` and `laporan/CLAUDE.md` by hand for the script names only. Evidence for the laporan build: `cd laporan/buku-pa && make pdf` succeeds and `pdftotext output/main.pdf -` is identical before and after.
- [ ] Shell files: only the file name changes here. Their internal variable names (`berkas`) are an area without a proof tool: **ask the user** whether to rename them and accept `bash -n` plus one real run as evidence, or leave them.
- [ ] Proof: `renames.py python`, `python3 scripts/check_slop.py --uji`, `python3 scripts/check_skills.py --uji`, `python3 scripts/check_tables.py --uji`, the pre-commit hook run on one staged file, each CI job command run locally.

---

## Phase 4: output translation (behavior changes, not refactors)

Each task is its own commit, typed `feat` or `chore`, never mixed with a rename.

### Task 4.1: firmware serial log text

- [ ] **Step 1:** `pio device list`. No board: stop and say so (repo rule C). The rest of Phase 4 can continue.
- [ ] **Step 2:** Translate every free-form `Serial.print*` text in `firmware/src` and `firmware/test/test_hw_*` to English (`"tangga: mulai, perkiraan %lu s\n"` → `"sweep: start, estimate %lu s\n"`, `"DENGARKAN: tiga bip pendek."` → `"LISTEN: three short beeps."`). Keep every Frozen token byte for byte.
- [ ] **Step 3:** Same commit: update the patterns in `model/scripts/record_flow_check.py` (`"ganti sumber"`, `"tangga daya"`, `"mode daya"`, `"tangga: mulai"`) and every message `pull_power.py` matches. Grep for each changed text in `model/`, `dashboard/`, `scripts/`, docs.
- [ ] **Step 4:** Flash, then run `python3 model/scripts/record_flow_check.py` on the board, `make pull` of a short recording, and `pio test -e esp32-s3 -f test_hw_buttons -f test_hw_integration`. Paste the serial lines into the commit body. TFT unchanged: one photo of the menu, or say it was not checked.

### Task 4.2: Python output, errors, argparse help and flags

- [ ] One commit per area (`model/src`, `model/scripts`, `scripts/`, `dashboard/`): `print`, `sys.exit` and exception texts, argparse `help=` and `description=`, Indonesian flags (`--mulai` → `--start`, `--kertas` → `--paper`, `--uji` → `--self-test`) together with their `args.*` names (moved here by `REFUSED` in Phase 3). `check_slop.py` pattern lists stay Indonesian.
- [ ] Tests asserting messages are updated in the same commit. Proof: pytest, self-tests, `--help` output pasted for each script whose flags changed.
- [ ] `PA_CEK_REC` → `PA_CHECK_REC` (reader and docs, one commit).

### Task 4.3: make targets and Makefile help

- [ ] `model/Makefile`: `data-semua` → `data-all`, `analisis` → `analyze`, `grafik` → `plot`, `pull-daya` → `pull-power`; every `##` description in English. Add map phrase lines `make analisis	make analyze` (and the others) so Phase 6 can update laporan comments.
- [ ] Proof: `git show HEAD:model/Makefile > /tmp/Makefile.old`, then for each target `diff <(make -n -f /tmp/Makefile.old <old> FILE=x.csv) <(make -n <new> FILE=x.csv)` is empty; `make help` output pasted.
- [ ] CI workflow and job names in `.github/workflows/cek.yml` (`cek` → `checks`, `komentar` → `comments`) in the same chore commit as Task 4.2 for `scripts/`.

---

## Phase 5: docs and skills

### Task 5.1: port `feature-docs`

**Files:** Create `.claude/skills/feature-docs/{SKILL.md,scripts/pointers.sh,evals/,triggers/evals.json}`, `scripts/check_docs.py`; Modify `.github/workflows/cek.yml`, `CLAUDE.md` skills table

- [ ] **Step 1:** Copy `~/dev/finance-project/.claude/skills/feature-docs/scripts/pointers.sh`. Change its extension list to this repo's code: `(cpp|h|py|sh|ini|yml|md)` and add `Makefile` (the `grep -oE` line).
- [ ] **Step 2:** Write `SKILL.md` from the finance skill, adapted:
  - Where things live: `docs/features/<feature>.md`; index `docs/README.md`; deep dives `model/docs/*-walkthrough.md`; build, flash, test quickstart `firmware/README.md`; pin map and circuit `hardware/mainboard/README.md`.
  - Modes, page skeleton, `file:line` rules, final report: as in finance. The footer is `**Code:**` without an emoji (repo rule: no marker emoji in docs).
  - Mermaid: as in finance, scoped to `docs/features/` (D5); `flowchart LR` per feature, real names (ISR, `ecg_live_push`, MQTT topic).
  - No walkthrough-video section and no VitePress sidebar (D6). Registration = a line in `docs/README.md`.
  - Language: English; TFT labels quoted in Indonesian with a gloss once ("Sumber sinyal" (signal source)); Frozen tokens verbatim.
  - Verify: `python3 scripts/check_docs.py` and `pointers.sh <page>`.
- [ ] **Step 3:** `scripts/check_docs.py`: walk `git ls-files '*.md'` minus `laporan/` and `.claude/skills/*/evals/`; for each `[text](target)` whose target is not `http(s):`/`mailto:`/`#...`, resolve it relative to the file (drop `#anchor`) and print `file:line: missing target` if it does not exist; exit 1 on any. Add `python3 scripts/check_docs.py` to the CI job that runs `check_comments.py`.

```python
import re
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
EXTERNAL = ("http://", "https://", "mailto:", "#")


def pages():
    files = subprocess.run(["git", "ls-files", "*.md"], capture_output=True, text=True, check=True).stdout.split()
    return [f for f in files if not f.startswith("laporan/") and "/evals/" not in f]


def main():
    missing = 0
    for page in pages():
        for number, line in enumerate(Path(page).read_text().splitlines(), 1):
            for target in LINK.findall(line):
                if target.startswith(EXTERNAL):
                    continue
                if not (Path(page).parent / target.split("#")[0]).exists():
                    missing += 1
                    print(f"{page}:{number}: missing target {target}")
    print(f"{missing} missing link targets")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4:** Evals (repo rule 8): `evals/create-calibration-gate-page/` (create mode from pasted `gate.cpp` excerpts and grep output) and `evals/update-stale-recorder-page/` (pointers moved after a rename, a dated note to rewrite, an unverifiable latency claim to drop). Graders like finance's. `triggers/evals.json` with 10 should-trigger and 10 near-miss queries, mixed Indonesian and English. Graded by a different model, at most 3 rounds, score in the commit body.
- [ ] **Step 5:** `python3 scripts/check_skills.py`, `python3 scripts/check_docs.py` green. Commit `feat(skills): feature-docs for docs/features pages`.

### Task 5.2: feature pages (create mode, one page per commit)

Each agent loads `feature-docs` and writes one page from the code plus the matching `firmware/README.md` section, then removes that section from `firmware/README.md` in the same commit. Facts move, they are not duplicated. Every fact in the removed section must be on the page, or be listed in the commit body as dropped (with the reason: stale, or not provable in code).

| Page | Code | From `firmware/README.md` |
|---|---|---|
| `docs/features/architecture.md` | `main.cpp`, `menu.cpp`, `dashboard/`, `model/Makefile` export | Struktur, Antarmuka alat |
| `acquisition.md` | `acquisition.*`, `board.*` | Jebakan (ADC, timer parts) |
| `signal-pipeline.md` | `ecg_pipeline.*`, `ecg_live.*`, `ecg_preproc.h` | Jebakan (filter parts) |
| `classification.md` | `classifier.*`, `model_int8.h` | |
| `calibration-gate.md` | `gate.*` | |
| `display-and-buzzer.md` | `display.*` | |
| `buttons-and-menu.md` | `buttons.*`, `menu.*` | Peta tombol, Pohon menu |
| `recording.md` | `recorder.*` | Merekam |
| `mqtt-telemetry.md` | `ecg_mqtt.*`, `dashboard/` | |
| `network-settings.md` | `settings.*`, `wifi_secrets.example.h` | Konfigurasi jaringan dan broker |
| `power-measurement.md` | `power.*`, `ina219.*` | Catu daya dan pengukuran arus |
| `diagnostics.md` | `diagnostics.*`, `firmware/test/test_hw_*` | Test (device part) |
| `serial-commands.md` | `serial_cmd.*` | Perintah serial |
| `model-pipeline.md` | `model/Makefile`, `model/src/`, `export_golden.py`, `export_model_h.py` | links each `model/docs` walkthrough |

- [ ] Pages with no shared file run in parallel; `docs/README.md` (index) is written once after the last page: a "Features" list in sidebar order above the working-docs table.
- [ ] `firmware/README.md` keeps: environments, commands, tests, deliberate limits that are not tied to one feature, and links to the pages.
- [ ] Per commit: `pointers.sh <page>` shows every pointer landing on its named symbol, `check_docs.py` green, `grep -c '—' <page>` is 0, the skill's final report in the commit body.

### Task 5.3: translate the remaining docs

Four parallel agents, one file group each, finance `d50820a` rules: inline code, paths and Frozen tokens byte-identical; ambiguous phrases reported back and kept literal; numbers converted to English format (default above); no em dash; antislop buzzwords none.

| Group | Files |
|---|---|
| A | `CLAUDE.md`, `model/CLAUDE.md`, `laporan/CLAUDE.md` (English instructions, Indonesian examples and quoted rules verbatim), `README.md` |
| B | `model/docs/README.md` + 7 walkthroughs (`akuisisi` → rename file `acquisition-walkthrough.md`, `dataset`, `evaluate`, `features-rr`, `firmware`, `io-mitdb`, `jitter`) |
| C | 7 walkthroughs (`model`, `mqtt`, `prep-beats`, `preprocessing`, `quantize`, `segmentasi-deteksi` → `detection-segmentation-walkthrough.md`, `train`), `model/README.md` |
| D | `firmware/README.md` (what is left), `firmware/include/README.md`, `hardware/mainboard/README.md`, `dashboard/README.md`, `scripts/README.md`, READMEs under `model/data/` and `model/artifacts/`, `docs/*.md` working docs (file names to English: `pekerjaan-ditunda` → `deferred-work`, `celah-target` → `target-gaps`, `crosscheck-metrik-bab4` → `bab4-metrics-crosscheck`) |

- [ ] Fidelity check per file, pasted in the commit body: inline-code spans counted old vs new (a `grep -o` over backtick pairs piped to `sort | uniq -c`, diff empty except the reported ones); every `file:line` pointer still resolves (`pointers.sh`); `check_docs.py` green; `grep -c '—'` 0.
- [ ] Group A changes section headings that skills cite (`laporan/CLAUDE.md §DOCX Notes`): Task 5.4 runs after group A.
- [ ] Ask the user before deleting finished working docs (`docs/2026-11-21-rencana-rework-skill-codebase*`): repo rule, deletion needs approval.

### Task 5.4: skills in English, renamed folders

| Old | New |
|---|---|
| `batas-tidak-diam` | `firmware-limits` |
| `buku-ikut-proposal` | `book-follows-proposal` |
| `deck-pa` | `defense-deck` |
| `ingest-word` | `word-ingest` |
| `kicad-pcb-pa` | `kicad-pcb` |
| `struktur-pa` | `report-structure` |
| `tabel-pa` | `report-tables` |
| `tanpa-komentar-kode` | `no-code-comments` (same name as the user skill, as in finance) |
| `tulis-tanpa-slop` | `report-antislop` |

- [ ] One agent per skill, one commit per skill: `git mv`, frontmatter `name` = folder name, English body, Indonesian examples and quoted laporan rules verbatim, eval prompts keep the user's Indonesian voice, graders English, `triggers/evals.json` keeps its mixed queries.
- [ ] Eval rerun per skill (repo rule 8): different model grades, at most 3 rounds, two rounds without improvement = stop; score in the commit body.
- [ ] `.claude/skills/README.md` and the `CLAUDE.md` table "Skill, muat sebelum mulai" (translated in group A) list the new names; `python3 scripts/check_skills.py` green.

---

## Phase 6: laporan pointers

### Task 6.1: `% sumber:` comments

**Files:** `laporan/buku-pa/**/*.tex`, `laporan/progres-pa-1/**/*.tex` (comment lines only). Not `laporan/proposal-pa`.

- [ ] **Step 1:** Build both books and keep the text: `make pdf && pdftotext output/main.pdf /tmp/<book>-before.txt` in each.
- [ ] **Step 2:** Rewrite only lines whose first non-space character is `%`:

```bash
python3 - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, "scripts")
import renames
pairs = renames.load_pairs(renames.MAP)
for book in ("laporan/buku-pa", "laporan/progres-pa-1"):
    for tex in Path(book).rglob("*.tex"):
        lines = tex.read_text().splitlines(keepends=True)
        new = [renames.apply_text(l, pairs) if l.lstrip().startswith("%") else l for l in lines]
        if new != lines:
            tex.write_text("".join(new))
            print(tex)
EOF
```

- [ ] **Step 3:** Rebuild; `diff /tmp/<book>-before.txt <(pdftotext output/main.pdf -)` must be empty for both books. `git diff -U0 -- laporan | grep '^[-+][^-+]' | grep -v '^[-+]\s*%'` must print nothing (only comment lines changed).
- [ ] **Step 4:** Commit `docs(laporan): source comments point at the renamed code` with both empty diffs in the body.

---

## Phase 7: closeout

- [ ] **7.1** Deadcode re-audit (skill `deadcode`): report only, renames can expose duplicates; user approves items; removal commit with build, native tests and pytest.
- [ ] **7.2** `python3 scripts/renames.py leftovers firmware model scripts dashboard` prints only Frozen names.
- [ ] **7.3** Ask the user to approve deleting `scripts/renames.py`, `scripts/rename_map.tsv`, `scripts/glossary.tsv` (one-off tools, repo rule). Git keeps them.
- [ ] **7.4** This plan: move any fact still valid into `CLAUDE.md` or a README (the Frozen table goes into `CLAUDE.md` §Language), then ask to delete the plan and its `docs/README.md` row.
- [ ] **7.5** Final report: commits per phase, proof outputs, what was not verified (TFT photo, board runs skipped), skill eval scores. Push only on request.
