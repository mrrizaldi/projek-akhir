---
name: defense-deck
description: Create, rework or review Proyek Akhir (PA) presentation decks in PPTX format, such as the progress seminar slides, the PA defense (sidang) or the supervision-meeting slides. Use when the user types "bikin deck sidang", "buat slide seminar progres", "rombak slide PA", "cek deck presentasi", "make the PA slides", or "review my defense deck". Deck content is derived from laporan/buku-pa, numbers are copied from the book (never invented), internal repo labels do not appear on slides, illustration figures are placeholder boxes for the user to draw, and every slide is rendered and looked at before handing over. PPTX file mechanics follow the skill document-skills:pptx.
---

# PA presentation deck

This skill governs deck content. How to write the `.pptx` file (the `pptxgenjs` API, hex color traps, layout, bullets) follows the skill `document-skills:pptx`; load both. The deck itself is Indonesian: slide text, speaker notes and placeholders are written in Indonesian exactly as in the examples below.

## Tools

- `pptxgenjs` is installed under the user prefix, not system-wide. Run the deck script with `NODE_PATH=~/.local/lib/node_modules node deck.js`; without `NODE_PATH`, `require('pptxgenjs')` fails. If it is missing, install it with `npm i -g --prefix ~/.local pptxgenjs`, not `sudo npm i -g`.
- Rendering uses `deckcraft-cli` and `pdftoppm`, both already on the system.
- `scripts/office/validate.py` of the `pptx` skill needs `defusedxml`, which is not installed. Installing it is a new dependency, so ask the user first. Without it, the evidence of a healthy file is a successful PDF render with every slide looking right.

## Location and files

One deck, one folder `presentasi/YYYY-MM-DD-<event>/`, holding `deck.js` (source, committed) and `output/` (`.pptx`, `.pdf`, `.png`; already ignored through `presentasi/*/output/`). The folder also holds a `README.md` with the rebuild steps for that deck. This follows the folders already in `presentasi/`.

`deck.js` is code, so it is written without comments (skill `tanpa-komentar-kode`). Speaker notes are written through `addNotes`, not comments, so the explanation stays without breaking the code rule.

## Content derives from the book

The single source of deck content is `laporan/buku-pa/bab/*.tex`, so the deck and the book never contradict each other.

- The Permasalahan and Tujuan in the deck equal the 3 items in Bab 1 of the book. They may be condensed, but the count and meaning stay.
- The deck's Kesimpulan answers those 3 permasalahan per Bab 5, one item per permasalahan.
- The deck carries no claim that is not in the book, because the examiners compare the two.
- A claim from the user's draft is checked against the book before it becomes a title or bullet; a claim that is absent from or contradicts the book is corrected to follow the book or marked `[N]`, because a draft may carry a claim that was already rejected.
- Scope the user already decided applies: anonymous test subjects (S01, S02, ...), laboratory test site, and TLS and transport security not discussed at all.

## Numbers

Copy every number from the book, or from a result file the book cites (e.g. `model/artifacts/metrics/*.csv`). An invented number cannot be defended in front of examiners.

- Indonesian format: decimal comma (0,9123), thousands dot (41.801).
- A number that is `\PlaceholderData{X}` in the book appears on the slide as the text `[PLACEHOLDER DATA: X]` with the same X. Do not replace it with an estimate, and do not use trial numbers from before 13 Okt 2026, because they are not official data.
- List of placeholders in the book: `grep -rn PlaceholderData laporan/buku-pa/bab`.

## No internal labels

Slide text and the speaker notes that are read aloud carry no internal working label of the repo, because the audience does not know them: HW-n, Fase n or Fase A–G, Task n, T-n/K-n, file paths, script names, env or knob names (`PA_*`, PlatformIO env), the word "walkthrough", and the labels `RM1..RM4`. Name the content with a general term. A placeholder for content not yet known also carries no label, e.g. `[N: isi tujuan, salin dari Bab 1 buku]`, not "memenuhi tujuan berlabel RM2", because a placeholder that repeats the label leaks it onto the slide.

Image file names (e.g. `fase7_confusion_int8.png`) appear only in `deck.js`, not on slides.

## Figures

- Data plots from the pipeline already exported to `laporan/buku-pa/gambar/` are placed directly from there with `addImage`, keeping the original aspect ratio.
- Illustration figures (architecture, block diagram, flowchart, state machine, wiring, device photo, mockup) are not drawn by Claude, including with `pptxgenjs` shapes and arrows (several `addShape`, lines, connected boxes), because the user draws them.
- At the illustration position put exactly one dashed-outline box (`addText` with `line: { dashType: 'dash' }`, or one rectangle `addShape`) holding `[PLACEHOLDER GAMBAR] <jenis>: <ringkasan satu baris>`.
- The specification card (type, main message, required elements, reading flow, text in the figure, material in the repo) goes in that slide's speaker notes, under the line `KARTU GAMBAR (tidak dibacakan)`. Only this card may contain repo paths; the read-aloud part of the notes stays free of internal labels.
- If the book already has a placeholder for the same figure, copy its card from the `PLACEHOLDER-GAMBAR` comment in the `.tex`.

## Slide structure

- One slide, one message. The title is a finding sentence or a question (e.g. "Ukuran window menentukan akurasi pada ablasi DS2"), not a label ("Hasil"), so the audience knows the slide's conclusion before reading the body.
- A slide body has at most 6 bullets, each at most 12 words.
- A table has at most 5 data rows and 4 columns. A larger book table is trimmed to the rows that answer the slide title, and the rest is referenced as "lengkap di buku, Tabel X" with the correct table number.
- Standard flow: Judul (nama, NRP, pembimbing), Latar belakang, Permasalahan, Tujuan, Rancangan sistem, Metode pengujian, Hasil (ordered per tujuan), Kesimpulan, Saran, penutup. Slides outside the flow are added only at the user's request.

## Decisions that belong to the user

The campus template, colors and presentation duration have never been decided in the repo. If the task needs them and the user has not said them, ask once with options and a recommendation before building, and do not silently use a default template.

The slide count is not asked separately: derive it from the duration (about one slide per minute) and state it in the message as an assumption the user can change. Things already recorded in the repo or waiting for official data are not asked, following the skill `buku-ikut-proposal`.

## Verification before handing over

Run it yourself, because the user is not the verifier.

1. `cd presentasi/<folder> && NODE_PATH=~/.local/lib/node_modules node deck.js`
2. `deckcraft-cli convert output/deck.pptx output/deck.pdf`
3. `pdftoppm -png -r 60 output/deck.pdf output/slide`
4. Open every `output/slide-*.png` with Read. Check that no text leaves its frame or is cut off, nothing overlaps, images are not squashed, and placeholders are legible.
5. `pdftotext output/deck.pdf output/deck.txt`, then
   `grep -nE "HW-[0-9]|Fase [0-9A-G]|PA_[A-Z]|walkthrough|RM[1-4]|\.(py|png|csv|tex|js)\b|(model|firmware|laporan|scripts|dashboard)/" output/deck.txt`
   must be empty.

The final report states the slide count from real output (the number of `slide-*.png`), the results of steps 4 and 5, and what is not verified: font rendering in real PowerPoint, animations, speaking time. A command not yet run is written "belum dijalankan", and any claim that depends on it ("deck selesai dibangun", "N slide", "label internal bersih") is written as unproven; if a number has not been observed, write `[N]`.
