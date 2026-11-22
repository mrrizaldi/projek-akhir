# Skill for writing reports without AI writing patterns

Goal: the text of `laporan/buku-pa` and `laporan/progres-pa-1` must not read as
language-model output (cliche phrases, uniform rhythm, three-item patterns, closing
sentences that restate the paragraph).

## Candidate external skills

| Skill | Fit | Notes |
|---|---|---|
| naskah-id (nothinx) | Best fit | Scientific work (thesis, research report), EYD V and KBBI, does not change numbers, results, and citations |
| humanizer-indonesia (adhiprib) | Partial | A catalog of Indonesian AI writing patterns; its working mode re-edits text, so only the catalog is taken |
| opencraftdev/humanizer | Not used | Narrow thesis coverage, overlaps with naskah-id, claude.ai ZIP format |
| Indonesia EYD Writing Skill (ClaudSkills) | Not yet | Aggregator source, origin repo not yet known |
| blader/humanizer, hardikpandya/stop-slop | Not used | English patterns |
| coreyhaines31/marketingskills | Not used | Marketing and SEO |
| alvinindra/bahasa-skills | Comparison reference | A from-scratch Indonesian writing package |

The existence and contents of the repos above have not been checked directly (the list
comes from chat research, 21 Nov 2026).

## Conflicts with repo rules

External skills are not installed as is because they conflict with the rules in force:

1. Technical terms stay English and italic (`\textit{board}`, not "papan"), a user
   decision of 20 Oct 2026. EYD skills tend to standardize terms.
2. The author's sentences are not rewritten without confirmation (`laporan/CLAUDE.md`
   §Ingest suntingan WordCraft).
3. The ban on colons, semicolons, and em dashes in paragraphs already exists in
   `laporan/CLAUDE.md` and is checked by `scripts/cek_tabel.py`.
4. Paragraph structure was originally governed by the `narasi-pa` skill, which was
   deactivated on 21 Nov 2026 (see Skill position decision).

## Skill position decision

The plan to distil into `narasi-pa` is not used: on 21 Nov 2026 the user decided that
`report-antislop` replaces `narasi-pa`.

## Order of work (user decision, 21 Nov 2026)

The anti-slop work starts from code (the `antislop-code` skill for the code comments of
WordCraft and the scripts that get touched). The report-writing skill is discussed
separately afterwards; the discussion of the candidates above continues later.

## Research and trial results (21 Nov 2026)

The research catalog (74 patterns, source profiles and licenses, conflicts with house
rules, gaps): `2026-11-21-skill-anti-slop/katalog.md`. By user decision, `narasi-pa`
was ignored for this trial and a new skill `report-antislop` was created together with
the checker `scripts/check_slop.py`. The trial covers only `laporan/progres-pa-1`
Chapter 2 to Chapter 4; Chapter 1, the front matter, and Chapter 5 were not touched.
Backup before the trial: git tag `backup/pra-antislop-20261121-1127` and archive
`~/backups/projek-akhir/progres-pa-1-20261121-1127.tar.gz`.

Baseline `check_slop.py --ringkas` before editing:

| Chapter | Words | Mean sentence length (sd) | errors | review | karena itu inserted | paragraphs with yaitu ≥ 2 |
|---|---|---|---|---|---|---|
| 2 | 4,545 | 20.3 (7.9) | 8 | 8 | 1 | 2 |
| 3 | 7,472 | 17.2 (7.8) | 2 | 37 | 18 | 10 |
| 4 | 7,674 | 16.3 (8.1) | 7 | 41 | 25 | 7 |

A finding that is in no source: the ban on colons and the ban on the opener "Oleh karena
itu" in the old rules produced a new habit, namely "karena itu" inserted in the middle
of a clause and strings of "yaitu". Both went into the skill as main patterns.

Trial results (commits `0852264`, `a02a466`, `57b5f8c`; each chapter `--banding`
invariant safe, `cek_tabel` 0 errors, PDF 125 pages 0 undefined/Overfull):

| Chapter | errors | review | Mean sentence length (sd) |
|---|---|---|---|
| 2 | 8 → 0 | 8 → 2 | 20.3 (7.9) → 19.5 (7.5) |
| 3 | 2 → 0 | 37 → 7 | 17.2 (7.8) → 17.3 (7.8) |
| 4 | 7 → 0 | 41 → 8 | 16.3 (8.1) → 16.2 (8.0) |

Skill eval (writer sonnet, grader haiku): 8, 9, 9, 9, 10 out of 10. Rounds 4 and 5 were
run with the user's permission; what made it pass was a two-sentence example for "karena
itu" that refers to the previous sentence. Score history is in the commit messages
(`git log -- .claude/skills/report-antislop`).

Content findings during editing, fixed in commit `39d0268`: progres-pa-1 Chapter 3 said
"lima hal" for four items (now "empat hal"), and the sentence "TinyML memungkinkan ..."
in buku-pa Chapter 2 was swallowed by the `% sumber:` comment line (now on its own line
and printed).

## Remaining work

1. The user reviews the trial result of progres-pa-1 Chapter 2 to 4, then decides
   whether to keep it or revert it
   (`git checkout backup/pra-antislop-20261121-1127 -- laporan/progres-pa-1/bab`).
2. If kept: extension to progres-pa-1 Chapter 1, Chapter 5, the abstract, and to
   buku-pa. Awaiting the user's decision.
3. Claims without numbers that were left because the fact is not in the manuscript.
   The user supplies the numbers or decides the claims are softened.
   - bab2: Mulyawan's accuracy "tinggi";
   - bab2: "baru sedikit yang dibuktikan" and "salah satu dari sedikit studi";
   - bab2: "dua keperluan yang berbeda", only one is described;
   - bab3: "menekan jumlah parameter secara drastis" and "model yang telah
     teruji akurat".
4. Rule gaps. `narasi-pa` was deactivated on 21 Nov 2026; the following rules
   have no equivalent yet and become material for the next tuning of
   `report-antislop`.

   | narasi-pa rule | Summary (≤ 8 words) | Equivalent in report-antislop |
   |---|---|---|
   | 1 | Table explainer: finding, evidence, meaning | none |
   | 2 | Vary the openers of explanatory paragraphs | none |
   | 3 | Do not re-read the table contents | none |
   | 4 | Claim strength proportional to evidence | exists (Frasa: S-SIGNIFIKAN, S-MUTLAK; no word table) |
   | 5 | Sentences of 15–30 words, split above 35 | exists (Kalimat: S-PANJANG, S-RANTAI-YANG) |
   | 6 | One paragraph one function, 60–150 words | none |
   | 7 | No meta openers in subsections | exists (Paragraf: S-DOKUMEN) |
   | 8 | Old-to-new cohesion, rotated openers | none |
   | 9 | Consistent terms and abbreviations | exists (Yang bukan slop: term repetition) |
   | 10 | Thread from result to target | none |
   | 11 | Design versus achievement register | none |
   | 12 | Editing does not change content | exists (Yang tidak boleh berubah) |
5. `laporan/progres-pa-1/bab/bab2.tex:96`: the `% sumber:` comment line still
   contains a remnant of the text "TinyML memungkinkan model kecerdasan buatan". It is
   not printed, the sentence already exists in the prose line; it only needs tidying
   when that chapter is edited again.
