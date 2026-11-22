# Deferred work (Word pipeline, anti-slop, release, skills)

Single list of work from the 21 Nov 2026 sessions that has not been executed,
with the documents that hold the details. Hardware and model work stays in
`model/CLAUDE.md` §Open work.

| # | Work | Status | Details |
|---|---|---|---|
| 2 | WordCraft environment: `rustup target add wasm32-unknown-unknown` then `cargo xtask ci` in `~/dev/wordcraft` (test `swiss_german_and_portugal_portuguese_keep_their_languages_rules` also fails on `main` because the craft-i18n data is missing), and the GUI application built from the branch `fix/latex-env-scopes-declarations` | deferred by the user; low value as long as the branch is not PR'd and edits go through `make docx` | `laporan/CLAUDE.md` §DOCX Notes |
| 3 | Tuning `tulis-tanpa-slop` with `narasi-pa` rules that have no counterpart yet | rules 1, 2, 3, 6, 10 are already in the PA layer; the rest were decided not to go in (reason in the history of commit 0fd0e25) | `.claude/skills/tulis-tanpa-slop/SKILL.md` |
| 4 | Extending the `tulis-tanpa-slop` style to progres-pa-1 Chapter 1, Chapter 5, the abstract, and to buku-pa | held by the user ("jangan dulu", not yet) | `docs/2026-11-21-skill-anti-slop.md` §Remaining work |
| 5 | Visual DOCX check against the PDF (`make cek-docx`), floats and line cutting accepted as limitations | waiting for the user | `laporan/CLAUDE.md` §DOCX Notes |
| 8 | Private GitHub repo for the five user skills (`local-file-links`, `firmware-bounded-limits`, `indonesian-antislop-writing`, `kicad-mcp-pcb`, `wordcraft-latex-ingest`) and their LICENSE (the PA repo and `no-code-comments` were pushed on 22 Nov 2026; `rilis/*` tags are deliberately not pushed) | waiting for the user's command | `.claude/skills/README.md` |
| 9 | `wordcraft-latex-ingest`: the "stash" option when the guard refuses cannot run because the `.tex` changes are already committed (clean-tree rule); alternative: sync in a worktree at the commit the DOCX came from, then merge | waiting for the user's decision | `~/dev/wordcraft-latex-ingest/SKILL.md` guard step |
