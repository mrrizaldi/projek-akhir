---
name: report-figures
description: PA repo layer for drafting, revising or reviewing illustration figures of the PA reports (laporan/buku-pa, laporan/progres-pa-1) in draw.io from a PLACEHOLDER-GAMBAR card: hardware block diagram, system architecture, flowchart, state machine, menu tree, data-flow diagram, and revisions of proposal figures. Use when the user types "gambarin", "bikin draf gambar", "gambar blok perangkat keras", "gambar pohon menu", "revisi gambar proposal", "rapikan gambar biar tidak AI slop", "gambarnya kekecilan pas dicetak", "draw the block diagram", or asks to fill a figure placeholder. Loads the user skills antislop, antislop-ui and antislop-human first, then adds the house style (references/house-style.md acts as their DESIGN.md), print readability, scripts/check_figures.py, export and looking at the PNG, and the rule that a draft stays in gambar/draf/ until the user approves it. Not for device photos, screen mockups, data plots from the model pipeline, or dev diagrams in docs/features.
---

# Report figures (PA layer)

Load the user skills `antislop`, `antislop-ui` and `antislop-human` first (third party, `miqdadbadjuber/anti-slop`, tested at v3.2.32; install with `npx antislop-ai`). This skill only adds what is specific to the PA reports. The antislop rules R-01 to R-40, its During/After modes and its Delivery Gate live in those skills and are not repeated here. If antislop is not installed, say so in the final report and still run the static-figure Delivery Gate below from this skill.

Direction comes from `references/house-style.md`, which antislop treats as the `DESIGN.md` (R-37): Design Read, dials ENERGY 1 / RHYTHM 1 / MOTION 1, role palette with measured contrast, and the one-line R-31 reasons. A finished example that passes every check is `laporan/buku-pa/gambar/draf/blok-perangkat-keras.drawio`; copy cell styles from it instead of inventing new ones.

## Scope

| Card type | This skill? |
|---|---|
| block diagram, architecture, flowchart, state machine, menu tree, data-flow diagram | yes |
| revision of a proposal figure (group A in `gambar/daftar-placeholder.md`) | yes, revision mode (rule 7) |
| device photo, electrode photo | no, the user takes the photo |
| TFT screen mockup | no unless the user asks; the card suggests an annotated photo of the screen |
| data plot (curve, confusion matrix, buffer) | no; pipeline scripts in `model/` (`report-structure` rule 9) |
| Mermaid in `docs/features/` | no; `feature-docs` |

## Tools

| Purpose | Command |
|---|---|
| check all drafts | `python3 scripts/check_figures.py` |
| check one file | `python3 scripts/check_figures.py laporan/buku-pa/gambar/draf/<slug>.drawio` |
| export PDF (vector) and PNG (about 300 dpi, source embedded) | `python3 scripts/check_figures.py --export laporan/buku-pa/gambar/draf/<slug>.drawio` |
| take the source out of a proposal PNG | `python3 scripts/check_figures.py --extract laporan/proposal-pa/gambar/<asal>.png laporan/buku-pa/gambar/draf/<slug>.drawio` |
| revision mode (labels and print size only) | add `--revision` |
| measure a new color | antislop-human `contrast-check.py "<fg>" "<bg>"` |

Export needs draw.io Desktop (tested 32.6.1); without a display the script uses `xvfb-run`. If Times New Roman is not installed, draw.io falls back to Liberation Serif, which has the same metrics, so layout does not move; `pdffonts` then names LiberationSerif.

## Rules

1. **A draft lives in `laporan/<projek>/gambar/draf/`, never in the `.tex`.** Write only `<slug>.drawio` and its exports there (`fig:3-pohon-menu` gives `3-pohon-menu.drawio`). Do not touch `.tex`, `bab/`, other files in `gambar/`, or `daftar-placeholder.md`. Replace the placeholder only after the user says the draft is approved, by following steps 1 to 6 of `gambar/daftar-placeholder.md` with the size from the card and without changing `\caption` or `\label`. Reason: `laporan/` is read-only by default (root `CLAUDE.md`, working rule 2), and the figures are the user's work.
2. **The card is the order.** Every element on the "Elemen" line is drawn, the "Alur baca" is followed, and text in the figure is copied exactly from the card and the explanatory paragraph: symbols (`LO+ / LO−`, `VIN+ → VIN−`), capitalisation, and italic foreign words (`\textit{buzzer}` becomes `<i>buzzer</i>`). Nothing that is on neither the card nor the paragraph is added (for example GPIO numbers that already sit in the pin map table); ask first. A one-row line legend is allowed when the figure uses more than one line type. Reason: `report-structure` rule 9 makes the paragraph read the card in the same words, so a figure that adds or renames things makes the paragraph wrong.
3. **Facts come from the repo material, not from guessing.** Arrow directions, signal names and voltages are read from the "Bahan repo" paths and the explanatory paragraph ("INA219 dibaca ESP32-S3 melalui I2C" means the I2C arrow points from INA219 to ESP32-S3). If the card and the paragraph disagree, do not pick one; report it. Reason: a wrong arrow is a factual error in the thesis, and the examiner reads the figure against the paragraph.
4. **Styles come only from the tokens.** Every `style` is copied from `references/house-style.md` or from the example draft. A cell with draw.io defaults (Helvetica, `fontSize=12`, a color picked from the UI panel) counts as unstyled. Reason: one role means one color across the whole book, and the reasons for every style choice are already written down there (antislop R-31).
5. **antislop applied to a static print figure.** The checker enforces what can be counted; the rest is checked on the PNG.
   - R-29 and R-01: at most 3 core colors plus 1 accent, colors meaning roles, the accent only on the focal element (counted by the checker).
   - R-10, R-11, R-12, R-13: no gradient, shadow, glass, glow or sketch; square boxes, with rounded corners only where the notation gives them meaning (stadium start/end, UML state).
   - R-04, R-22, R-23: no emoji, stock icons or clipart people, clouds or lightning; a photo only of a real component already in `gambar/` and only when the card asks for it.
   - R-05 and C-3: no title inside the figure; the title is the `\caption`.
   - R-06: Times New Roman in every cell, including decision diamonds and line labels.
   - R-25 and WCAG 1.4.11: text at least 4.5:1 on its fill, box borders at least 3:1 against white (the stock draw.io green, orange and yellow borders fail at 2.0 to 2.5:1).
   - R-02: no em dash in a label. The minus and arrow symbols copied from the card are not em dashes.
   - R-17, R-36, R-38: every number and label exists on the card, in the paragraph or in the repo material.
   - Part 3 liveliness: one focal element with a 1.5 px border and bold name, one accent, and the amber power motif, so the figure is not a sterile grey default.

   Reason: antislop is written for web UI, so this list fixes once which rules apply to a printed figure and how they are checked.
6. **Readable once printed.** The smallest text must print at 8 pt or more at the size the card names; the checker fails below 7 pt and warns between 7 and 8 pt, using the formula in `references/house-style.md`. If the content does not fit, split the figure or drop elements; never shrink the text. Reason: `width=\linewidth` scales the whole canvas, so a wide canvas turns 14 px text into 4 pt print.
7. **A proposal revision changes only what the "Ubah" column lists.** Take the source with `--extract` into `gambar/draf/`, change only those labels or steps, and keep the user's colors, fonts, photos and layout. Check with `--revision` (labels and print size only). Use antislop After mode for any other finding: a numbered list with R-XX references, and the user picks the numbers. Print problems of the original are reported as the user's decision (split, enlarge, or leave as is), never fixed silently: at `\linewidth` the proposal's `gambar_3_5` prints at about 3.5 pt and `gambar_3_1` at about 4.9 pt. The old Mermaid draft `gambar_3_5_revisi.mmd` is not used as a base. Reason: the proposal figures are the user's drawings, and the user decides how they change.
8. **Look at it before handing it over.**
   1. `python3 scripts/check_figures.py laporan/<projek>/gambar/draf/<slug>.drawio` shows 0 errors.
   2. `python3 scripts/check_figures.py --export laporan/<projek>/gambar/draf/<slug>.drawio`.
   3. Open `<slug>.png` with Read and check that:
      - every card element is present;
      - no line crosses a box or another line;
      - no label covers an arrowhead or breaks across lines ("5 / V");
      - lines are straight without small jogs (exit and entry points aligned);
      - arrow directions match the paragraph;
      - nothing from rule 5 shows.
   4. Fix and repeat steps 1 to 3, and name every round that changed something in the report.

   Reason: the checker cannot see crossings, jogs or covered arrowheads, and antislop R-35 asks for evidence that the output was inspected, not assumed.
9. **One figure, one message.** If the card carries two flows (for example the signal path and the resilience path) and the canvas breaks the rule 6 limit, propose splitting it into two figures; do not cram both. Reason: a crammed figure fails print size first and readability second.
10. **Repo rules win over antislop where they differ.** The order is:
    1. Card and repo rules (exact text, read-only `laporan/`, no code comments).
    2. antislop.
    3. Taste.

    If the card or paragraph asks for a pattern antislop forbids, name the element and the rule and ask the user, following the R-37 conflict protocol. `no-code-comments` is stricter than `antislop-code`, so no comment stays in the scripts. Reason: the card and the house rules are the owner's direction, and antislop itself says direction is the owner's.

## Final report

```
Draft: laporan/<projek>/gambar/draf/<slug>.drawio (+ .pdf, .png)
Card: fig:<label>, elements <n>/<n> present; text copied from <card/paragraph>
Checker: check_figures.py: <e> errors, <w> warnings; smallest text about <x> pt; <f> fill colors
Looked at: <slug>.png, <k> rounds; fixed: <short list>
PDF font: <Times New Roman | Liberation Serif (same metrics)>
Not done: placeholder in <bab>.tex:<line> not replaced, waiting for the user's approval
Questions: <card vs paragraph conflicts, or a proposal to split the figure>
```

A command that was not run is written "not run" with its output as [N], and any claim that depends on it ("checker passes", "looked at") is written as not proven.

Then the antislop Delivery Gate for a static figure: one line per item, every PASS with evidence. Items that only exist for interactive UI are N/A with the reason. A single FAIL means the draft is not handed over.

```
Delivery Gate (antislop, static figure)
R-02 PASS: no em dash in labels (checker 0 errors)
R-17/R-36/R-38 PASS: every number and label is on the card or in the paragraph: <example>
R-23 PASS: made from an explicit card, kept as a draft in gambar/draf/
R-25 PASS: text >= 4.5:1, borders >= 3:1 (checker; palette measured)
R-35 PASS: exported and the PNG looked at in <k> rounds: <what was checked>
R-37 PASS: direction = references/house-style.md, dials ENERGY 1 / RHYTHM 1 / MOTION 1
R-03, R-24, R-26, R-27, R-28, R-32, R-34, R-39, R-40 N/A: static print figure, no interaction or page
Purpose-Gate (R-01, R-04, R-06, R-10, R-12, R-13, R-22) PASS: <technique used + reason, or "not used">
Liveliness PASS: focal point <element>, accent <color> only on it, amber power motif
Quality Locks (R-05, R-11, R-29, R-31) PASS: <f> fill colors (<= 3+1); R-31 reasons in house-style.md
```

## Checklist

- [ ] The draft is only in `gambar/draf/`; `.tex` and other `gambar/` files are untouched.
- [ ] Every card element is present, text matches the card or paragraph, no internal labels.
- [ ] Styles come from the tokens: Times New Roman, at most 3 core colors plus 1 accent, square lines, no gradient, shadow, emoji or title.
- [ ] `check_figures.py` shows 0 errors; smallest text at least 8 pt, or the warning is named.
- [ ] The PNG was opened and checked, and the fix rounds are named.
- [ ] A proposal revision changes only the "Ubah" column; the original style stays.
- [ ] The placeholder is not replaced until the user approves.
- [ ] The Delivery Gate is written with no FAIL, and the antislop mode was announced by its own protocol.
