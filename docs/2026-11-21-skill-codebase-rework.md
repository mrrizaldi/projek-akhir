# Rework of the PA repo skills and codebase

> **For the executing agent:** REQUIRED to use the sub-skill
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans. Steps use checkboxes (`- [ ]`).

**Goal:** the PA repo skills are rewritten to the skill-creator standard,
generic skills are extracted to the user's English skill repos, evals move to
the `evals/` + `triggers/` format, a skill structure validator enters CI, and
the docs and code are cleaned of written history, dead code, and AI writing
patterns.

**Architecture:** follows the finance-project rework of 21 Nov 2026
(`docs/2026-11-21-riset-rework-skill.md` (deleted; contents in git `0fc2777`)). User skills live in
`~/dev/<nama>` (their own git repo, symlinked to `~/.claude/skills/<nama>`);
PA repo skills become a thin layer whose first sentence tells the agent to
load the user skill, or a full skill when it is tied to the PENS format.
Parallel subagent waves are only for work that does not share files.

**Tech stack:** Python 3 stdlib (validator), skill-creator `scripts.run_eval`
(trigger test, `uv run`), git, GitHub CLI (only when the user asks for a push).

## User decisions (21 Nov 2026)

1. Skills extracted to user scope are written in English. PA repo skills,
   code, docs, and reports stay in Indonesian.
2. Extracted: `tautan-lokal`, `batas-tidak-diam`, `tulis-tanpa-slop`,
   `kicad-pcb-pa` (general part), `ingest-word` (general part);
   `tanpa-komentar-kode` is merged into the existing `no-code-comments`.
   Staying in the repo: `deck-pa`, `struktur-pa`, `tabel-pa`, `buku-ikut-proposal`.
3. Written history is trimmed as in finance-project: documents describe the
   current state, history is in git; `docs/arsip/` and `model/docs/arsip/`
   are emptied step by step after the operational facts are separated out.
4. Skill-creator eval format: `evals/<kasus>/` + `triggers/evals.json` +
   CI validator; eval scores go in the commit message, not in a table in the repo.

## Limits

- Push, GitHub repo creation, and mass deletion (wave 4) only after the user
  approves the list.
- `laporan/**/*.tex` is not touched by this rework.
- `~/dev/no-code-comments` is also used by finance-project: changes there are
  limited to adding generic rules, local commit, no push.
- Trigger tests use a separate `CLAUDE_CONFIG_DIR`; stop if a `*-skill-*`
  file appears in `~/.claude/commands`.

## File map

| File | Wave | Content |
|---|---|---|
| `CLAUDE.md`, `laporan/CLAUDE.md`, `model/CLAUDE.md` | 0 | Strict rule 8 (eval format), Documentation (trim history), the table "Skill, muat sebelum mulai" |
| `scripts/check_skills.py` (new), `.github/workflows/checks.yml`, `.gitignore` | 0 | skill structure validator, exception for `triggers/evals.json` |
| `scripts/trigger_eval.sh` (new) | 0 | isolated trigger test runner |
| `~/dev/{local-file-links,firmware-bounded-limits,indonesian-antislop-writing,kicad-mcp-pcb,wordcraft-latex-ingest}` (new) | 1 | user skill repos |
| `~/dev/no-code-comments` | 1 | generic rules from `tanpa-komentar-kode` that are not there yet |
| `.claude/skills/*` | 2 | repo skills rewritten, `eval.md` replaced by `evals/` + `triggers/` |
| `docs/`, `docs/arsip/`, `model/docs/`, `model/docs/arsip/`, README | 4 | trim history |
| code in `model/`, `firmware/`, `scripts/`, `dashboard/`, `presentasi/` | 4 | `deadcode` report, cleanup |
| `.agents/`, `AGENTS.md` | 4 | Codex copy: deleted or regenerated (user decision) |

---

## Wave 0: rules and tools (sequential, one agent)

### Task 0.1: repo rules follow the decisions

- [ ] `CLAUDE.md` Strict rule 8 is replaced:

```markdown
8. **Setiap skill punya eval** dalam format skill-creator
   (`.claude/skills/<nama>/evals/<kasus>/{prompt.md,case.yaml,graders/}`) dan
   set pemicu `triggers/evals.json`, dinilai model berbeda dari penulis,
   target lulus semua grader, **maksimal 3 putaran**. Belum lulus sesudah
   putaran ke-3 → berhenti, tulis skor terbaik dan temuannya di pesan
   commit, lalu tanya user. Soal eval sempit dan berjawaban pasti
   (kegagalan aslinya). Skor yang tidak naik dua putaran berturut-turut =
   berhenti lebih awal. Skor tidak disimpan sebagai tabel di repo.
```

- [ ] Section "Dokumentasi": the `docs/arsip/` item and "Riwayat masuk arsip"
  are replaced by one item: "**Riwayat ada di git, bukan di dokumen.** Rencana dan
  catatan yang selesai dihapus sesudah hasilnya tercatat di dokumen yang
  berlaku; fakta operasional yang masih berlaku (lokasi data, cara
  memulihkan, nilai konfigurasi) dipindah dulu ke README atau walkthrough
  komponennya." Other items that name the archive as a move destination are
  adjusted (one-off tools are deleted).
- [ ] New table in `CLAUDE.md` after "Aturan keras":
  `| Pekerjaan | Muat skill |` one row per skill (repo and user), following
  `~/dev/finance-project/CLAUDE.md` section "Skills - load before you start".
  Filled in again in wave 2 once the skill names are final.
- [ ] Check `grep -n "arsip" CLAUDE.md laporan/CLAUDE.md model/CLAUDE.md`
  and adjust the references that tell the reader to move things to the archive.
- [ ] Commit with the rule diff in the message body.

### Task 0.2: skill structure validator

- [ ] Port `~/dev/finance-project/scripts/check_skills.py` (163 lines,
  stdlib) to `scripts/check_skills.py`: function names and messages in
  Indonesian, same behavior (frontmatter `name` = folder name, `description`
  ≤ 1,024 characters with no newline, body < 500 lines, `evals/<kasus>/`
  contains `prompt.md`, `case.yaml`, `graders/*.md`, `triggers/evals.json`
  is a list of `{query, should_trigger}` with two classes). PA-specific
  addition: `.claude/skills/*/eval.md` must no longer exist. The `--uji`
  option for a self-test like `check_slop.py --uji`.
- [ ] `.github/workflows/checks.yml`: step `python3 scripts/check_skills.py`.
  Until wave 2 is done, the validator runs with
  `--lewati-eval-lama` so CI stays green; the option is removed at the end of
  wave 2.
- [ ] `.gitignore`: make sure `.claude/skills/*/triggers/evals.json` is not
  ignored (`git check-ignore -v` must return rc=1).
- [ ] Check: `python3 scripts/check_comments.py scripts/check_skills.py`,
  `python3 scripts/check_skills.py --uji`. Commit.

### Task 0.3: trigger test runner

- [ ] `scripts/trigger_eval.sh` from the finance-project runner pattern (copied
  in `docs/2026-11-21-riset-rework-skill.md` (deleted; contents in git `0fc2777`) §Temuan item 4): argument
  `<folder skill>...`; `T=$(mktemp -d)`; `config/` holds only a copy of the
  Claude Code credentials (`~/.claude/.credentials.json`, ask the user if the
  file does not exist); `proj/` is an empty folder with its own `.claude/`;
  `CLAUDE_CONFIG_DIR=$T/config PYTHONPATH=<skill-creator> uv run -q
  --no-project --with pyyaml python -m scripts.run_eval --eval-set
  <skill>/triggers/evals.json --skill-path <skill> --runs-per-query 1
  --num-workers 4 --timeout 60`; stop with exit 3 if
  `~/.claude/commands` holds `*-skill-*`; summary `nama=… benar=…/20`.
  The skill-creator path is found with
  `find ~/.claude/skills -path '*skill-creator/scripts/run_eval.py'`.
- [ ] No comments (strict rule 5). Test with one skill that already has a
  trigger set: `~/dev/no-code-comments`. Record the cost (number of calls)
  in `scripts/README.md`. Commit.

## Wave 1: user skills (parallel, one agent per repo)

Each agent's brief contains: the old SKILL.md, the old `eval.md`, the reference structure
`~/dev/no-code-comments` (`SKILL.md`, `README.md`, `CLAUDE.md`, `evals/`,
`triggers/evals.json`, `scripts/check_skill.py`, `.github/workflows/tests.yml`),
the conventions in `docs/2026-11-21-riset-rework-skill.md` (deleted; contents in git `0fc2777`) §Konvensi, and the rule
"every old rule is mapped: user skill, repo skill, or dropped with the
reason that it is obsolete".

| New repo | From | User content (English) | Remainder in the PA repo |
|---|---|---|---|
| `~/dev/local-file-links` | `tautan-lokal` | all of it | none (repo skill deleted) |
| `~/dev/firmware-bounded-limits` | `batas-tidak-diam` | limits on buffers, queues, durations, capacity; slow operations in the loop | PA modules (LittleFS, PSRAM, firmware file names) |
| `~/dev/indonesian-antislop-writing` | `tulis-tanpa-slop` + `scripts/check_slop.py` | pattern catalog, principles, procedure, checker (script name in English, patterns stay Indonesian) | house rules `laporan/CLAUDE.md`, book paths |
| `~/dev/kicad-mcp-pcb` | `kicad-pcb-pa` | KiCad 9 MCP flow, Freerouting, reading pads, board check | PA board, nets, `cek_board.py` |
| `~/dev/wordcraft-latex-ingest` | `ingest-word` | flow backup → dry-run → confirm → sync → tidy → build | book paths, `make pdf-bersih`, local branch binary |

Steps per agent:
- [ ] `git init ~/dev/<repo>`, write the files following the reference, `check_skill.py`
  and `check_comments.py` green, local commit.
- [ ] One or more eval cases from the original failures (the old `eval.md`
  questions converted), one round (writer sonnet, grader haiku, run by the
  coordinator), score in the commit message.
- [ ] `triggers/evals.json` 20 queries (10 trigger, 10 similar that do not
  trigger, mixed Indonesian and English).
- [ ] Coordinator: `ln -s ~/dev/<repo> ~/.claude/skills/<repo>`, invariant map
  by a reviewer of a different model, then a commit in the PA repo for the
  thin layer (wave 2).
- [ ] `tanpa-komentar-kode`: generic rules that are not yet in
  `~/dev/no-code-comments` (named numeric literals, named indices, grep the
  name before naming, target document) are added there, local commit.

## Wave 2: PA repo skills (parallel, one agent per skill)

Indonesian, skill-creator conventions, no history in the skill.

- [ ] Thin layer (first sentence loads the user skill): `batas-tidak-diam`,
  `tulis-tanpa-slop`, `kicad-pcb-pa`, `ingest-word`, `tanpa-komentar-kode`.
- [ ] Full skills rewritten: `deck-pa`, `struktur-pa`, `tabel-pa`,
  `buku-ikut-proposal`.
- [ ] Items from `docs/2026-11-21-deferred-work.md` come along: the evidence
  procedure using `make pdf-bersih` (item 6), the proposed `ingest-word` eval
  rubric C (item 3), the `narasi-pa` rules without an equivalent assessed one
  by one for `tulis-tanpa-slop` (item 4; kept or dropped with a reason).
- [ ] The `ingest-word` result of the provenfix-style pilot (`temuan.md`,
  `referensi/`, `templat/`) is aligned: a one-sentence reason without dates in
  SKILL.md, `temuan.md` deleted, `templat/` kept if still referenced.
- [ ] Each skill's `eval.md` is converted to `evals/<kasus>/`; the score
  history table is not carried over (already in git).
- [ ] `.claude/skills/README.md` becomes an index + layout + eval procedure
  (reference `~/dev/finance-project/.claude/skills/README.md`); the table
  "Skill, muat sebelum mulai" in `CLAUDE.md` is filled in.
- [ ] Invariant map per skill by a reviewer of a different model; one commit per
  skill; end of wave: the validator's `--lewati-eval-lama` option is removed,
  `python3 scripts/check_skills.py` green.

## Wave 3: evals (coordinator)

- [ ] One round of behavior eval per skill (repo and user) not yet
  graded in waves 1–2; at most 3 rounds per Strict rule 8.
- [ ] Baseline trigger test once per skill with `scripts/trigger_eval.sh`
  (about 20 Opus calls per skill, 15 skills about 300 calls;
  run in stages so the quota is not exhausted). Results in the commit
  message; a description is changed only if the score rises above noise.

## Wave 4: docs and code (report first, execution after the user agrees)

- [ ] History inventory: list of dated documents in `docs/`,
  `docs/arsip/`, `model/docs/arsip/`, dated narrative in READMEs and
  walkthroughs. Each item is labeled `hapus` or `pindahkan fakta ke
  <file>`; operational facts (data locations, recovery steps,
  configuration values) must not be lost. The list goes to the user.
- [ ] `deadcode` audit (skill `deadcode`) of `model/`, `firmware/`,
  `scripts/`, `dashboard/`, `presentasi/`: report only, handed to the
  user.
- [ ] Sweep of AI writing patterns in Indonesian READMEs and docs with
  `check_slop.py` (house rules apply); code already has zero comments
  (`check_comments.py`), so `antislop-code` only checks CLI help text
  and Makefile descriptions.
- [ ] `.agents/` and `AGENTS.md`: proposal to delete (git keeps them) or
  regenerate from `.claude/skills/`; user decision.
- [ ] After the user approves the list: execute per category, one commit per
  category, a reviewer checks that no operational fact is lost.

## Wave 5: closing

- [ ] `docs/2026-11-21-deferred-work.md` is updated (finished items
  removed).
- [ ] Final report: skill table (old → new, user/repo, eval score, trigger
  score), commits, and the push questions: PA repo, and creating the private
  GitHub repos `mrrizaldi/<nama>` for the five user skills (only on command).

## Order and parallelism

| Wave | Parallel | Gate |
|---|---|---|
| 0 | no (shared rules and tools) | none |
| 1 | five agents, one per user repo | none |
| 2 | three to four agents per batch, one per skill | none |
| 3 | coordinator, in stages | quota |
| 4 | two agents (docs inventory, code audit) | user approves the delete list |
| 5 | none | user decides on push and GitHub repos |

## Operational facts in the archive that must be moved before wave 4

Found during waves 1–2. These archive files must not be deleted before their
facts are in a valid document.

| Archive file | Facts not yet in an active document | Destination |
|---|---|---|
| `model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md` | the 2k2/3k3 dividers on all four TFT lines are removed (R3, R4, R6, R8), R2/R5/R7/R9 become jumpers or 33 Ω for damping SCK ringing; TFT CS is tied to GND so the firmware must use `SPI_MODE3`; the reason the buzzer module VCC is 3V3 and not 5V; ESP32-S3 GPIOs do not tolerate 5 V as the factor tying all the changes together; the option of TFT BLK on GPIO 12 for PWM | `hardware/mainboard/README.md` §Perbedaan terhadap skematik rev2 |
| `docs/arsip/2026-10-19-referensi-pra-2020.md` | rationale per pre-2020 reference entry | referenced by `CLAUDE.md` section Menulis laporan; move to a valid report document |
| `model/docs/arsip/2026-09-16-daya-design.md` | power measurement design | referenced by `model/CLAUDE.md`; move to the power walkthrough |
| `model/docs/arsip/2026-09-19-faseG-changelog.md` §2, `2026-09-19-faseB-changelog.md` §9 | details of the learning rate and training database ablations | referenced by the `model/CLAUDE.md` table; move to the model walkthrough |

## Status (22 Nov 2026)

Waves 0–3 are done. The document history part of wave 4 was executed
on 22 Nov 2026 according to the user's decision on `inventaris-riwayat.md`: operational
facts were moved, `docs/arsip/` and `model/docs/arsip/` were deleted,
finished working documents were deleted; the trial data `model/data/arsip/` and
`model/artifacts/arsip/` were kept. Dead code was removed (`pio run`,
`pio test -e native` 23/23, pytest 92 passed), `.agents/` and `AGENTS.md`
were deleted, and the sweep of AI writing patterns in 27 Markdown documents brought the
`check_slop` errors down from 160 to 43 (remainder: the list of practice questions in the walkthroughs,
left on purpose). Remaining work is in `docs/2026-11-21-deferred-work.md`.
Baseline trigger test (`scripts/trigger_eval.sh`, 1 run per query): every skill
rejects 10/10 queries that must not trigger; correct triggering 0–3/10 (repo:
batas-tidak-diam 3, buku-ikut-proposal 3, tulis-tanpa-slop 3, deck-pa 2,
kicad-pcb-pa 2, tabel-pa 2, struktur-pa 1, tanpa-komentar-kode 1,
ingest-word 0; user: local-file-links 2, wordcraft-latex-ingest 2,
firmware-bounded-limits 1, kicad-mcp-pcb 1, indonesian-antislop-writing 0,
no-code-comments 2). Mitigation: the table "Skill, muat sebelum mulai" in
`CLAUDE.md`; descriptions were not optimized (finance-project saw no
improvement). Pushing the PA repo and creating the GitHub repos for the user skills wait for the user.
