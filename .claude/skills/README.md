# PA repo skills

The skills in this repo are thin layers. General rules live once in a user
skill (`~/.claude/skills/`); a repo skill names the user skill to load first,
then adds only what is specific to PA (paths, commands, constant names,
traps). Load the user layer, then the repo layer. Strict rules 7–8 in the root
`CLAUDE.md`: every failure the user catches becomes a skill the same day, and
every skill has an eval graded by a different model, at most 3 rounds.

## Repo skills

| Skill | When | User skill loaded |
|---|---|---|
| `firmware-limits` | firmware with a bounded buffer, duration, or capacity, or a slow operation in `loop()` | `firmware-bounded-limits` |
| `kicad-pcb` | mainboard KiCad PCB or schematic, DRC, routing, Gerber | `kicad-mcp-pcb` |
| `word-ingest` | DOCX edits from a friend brought back into LaTeX | `wordcraft-latex-ingest` |
| `no-code-comments` | writing or editing code, prompts to code-writing subagents | `no-code-comments` |
| `report-antislop` | report paragraphs that must not read as AI-written | `indonesian-antislop-writing` |
| `report-structure` | chapter skeleton, common thread, figure placeholders, QA before submission | none |
| `report-tables` | LaTeX tables in the reports | none |
| `book-follows-proposal` | Bab 1 of the book follows the proposal, questions to the user about book content | none |
| `defense-deck` | PA presentation decks (PPTX) | none |
| `feature-docs` | per-feature pages in `docs/features/` with verified `file:line` pointers | none |

`narasi-pa` is inactive and kept in
`.claude/skills-arsip/narasi-pa/` as a reference.

## User skills

Each user skill is a local repo `~/dev/<nama>` with a symlink
`~/.claude/skills/<nama>`. The GitHub repos do not exist yet; for now they are
local repos only. Once a remote exists, install on another machine with
`git clone <url> ~/dev/<nama> && ln -s ~/dev/<nama> ~/.claude/skills/<nama>`.

| User skill | Local repo | Used for |
|---|---|---|
| `local-file-links` | `~/dev/local-file-links` | documents that link local files (reference index in `laporan/pustaka/`, evidence list from `model/artifacts`) |
| `firmware-bounded-limits` | `~/dev/firmware-bounded-limits` | firmware limits never drop data silently |
| `indonesian-antislop-writing` | `~/dev/indonesian-antislop-writing` | editing Indonesian prose, with `check_slop.py` |
| `kicad-mcp-pcb` | `~/dev/kicad-mcp-pcb` | KiCad PCBs through MCP, pcbnew, kicad-cli, Freerouting |
| `wordcraft-latex-ingest` | `~/dev/wordcraft-latex-ingest` | DOCX to LaTeX |
| `no-code-comments` | `~/dev/no-code-comments` | comment-free code, with `check_comments.py` |
| `shared-worktree` | `~/dev/shared-worktree` | git safety when several sessions share one clone |

## Skill layout

```
<skill>/
  SKILL.md                  rules, frontmatter name + description
  evals/<kasus>/
    prompt.md               task text for the test
    case.yaml               schema_version: "1.1", name, expected_outcome
    graders/NN-*.md         one statement that can be graded pass/fail
  triggers/evals.json       list of {query, should_trigger}, true and false classes
  references/               optional, details loaded when needed
```

`SKILL.md` conventions (skill-creator format):

- Frontmatter only `name` (equal to the folder name) and `description`.
- `description` on one line, at most 1,024 characters, slightly pushy:
  it says when to use the skill with phrases the user types, and its limits.
- Each rule comes with a one-sentence reason.
- No history, no revision notes, body under 500 lines.
- Details that apply only under certain conditions move to `references/`.

## Eval procedure

Two separate agents per round, from the Agent tool or separate sessions.

1. The **writer** (model A) gets only `SKILL.md` (user and repo layers,
   plus `references/`) and each case's `prompt.md`. It does not open
   `case.yaml` or `graders/`, does not run commands, and writes one answer
   file with a `## <kasus>` heading per case.
2. The **grader** (model B, different from A) gets `SKILL.md`, each case's
   `case.yaml` and `graders/`, and the answer file. It grades each statement
   pass or fail with a quoted piece of evidence, and writes a table
   `Kasus | Penilai | Lulus | Bukti`, a line `Lulus: X/Y`, and at most
   three `SKILL.md` violations outside the graders.
3. Not everything passes: fix the ambiguous rule in `SKILL.md` or the
   ambiguous grader, then run the next round with a new writer (not by
   continuing the old agent).
4. Stop when everything passes, at round 3, or when the score does not rise
   for two rounds in a row; whatever still fails is put to the user.
5. Scores and the pass table go in the commit message. There is no score
   history file; `git log` is the history. Every `SKILL.md` change after a
   pass requires a new round.

## Checks

- Structure: `python3 scripts/check_skills.py` (no options; `--self-test` for
  the self-test). Runs in CI.
- Triggering: `scripts/trigger_eval.sh <folder skill>` measures whether the
  description triggers on the `triggers/evals.json` queries (`scripts/README.md`).
- Reports: `python3 scripts/cek_tabel.py`, `python3 scripts/check_slop.py`.
