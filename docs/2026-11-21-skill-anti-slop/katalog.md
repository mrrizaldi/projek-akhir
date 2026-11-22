# Catalog of AI writing patterns for editing the PA book (research material for the skill)

Research date: 21 Nov 2026. All sources were downloaded as data into
`src/<owner>__<repo>/` and `src/wikipedia/signs.wiki`. No script from the source
repos was run. `scripts/periksa.py` from naskah-id was downloaded as text
(`periksa.py.txt`) only to read its regex table.

Source codes used throughout the document:

| Code | Source |
|---|---|
| BS | alvinindra/bahasa-skills (modules `bahasa-inti` and `bahasa-peneliti`) |
| NI | nothinx/naskah-id |
| HI | adhiprib/humanizer-indonesia |
| HU | blader/humanizer (v4.0.0) |
| SS | hardikpandya/stop-slop |
| WP | Wikipedia:Signs of AI writing (revision as of Nov 2026) |
| NP | the house skill `narasi-pa` that already exists in the repo (not a research source, listed so the overlap is visible) |

The Tell and Fix example sentences in part B are written in the style of the PA book
(ECG, ESP32-S3, TinyML). **All numbers and `\cite` keys in the examples are
illustrations, not repo data.** The fixed examples already follow the house rules (no
colon, semicolon or em dash in paragraphs, technical terms in `\textit{}`, decimal
comma, `~\cite{}`).

---

## A. Source profiles

### A1. alvinindra/bahasa-skills (BS)

- **Contents.** An anti-slop skill package for Indonesian writing: `bahasa-inti` (Ten
  Hard Prohibitions L1 to L10, obligations, most common rules, `frasa-terlarang.md`
  with about 100 phrases, `kata-baku.md`, `padanan-istilah.md`, `ejaan-eyd.md`), then
  the category modules `bahasa-marketing`, `bahasa-website`, `bahasa-seo`, and
  `bahasa-peneliti`. The `sumber/` folder documents the research references together
  with reliability notes.
- **License.** There is no LICENSE file in the repo and the GitHub API reports an empty
  license. Legally this means full copyright with the owner. Safe to use as a source of
  ideas, not safe to copy verbatim into the house skill.
- **Relevant for academic work.** `bahasa-peneliti/SKILL.md` (formal register,
  pronouns, effective sentences prioritized by thesis error data 34 % structure, 21 %
  spelling, 18 % diction, the ban on the opener "era globalisasi", the academic
  anti-slop table, IMRaD structure, citation honesty),
  `references/kalimat-akademik.md` (prepositional subjects, economy, parallelism,
  logic, diction), `references/struktur-sitasi.md` (literature review as synthesis).
  From `bahasa-inti`: L1 to L9, `frasa-terlarang.md` parts 1, 2, 3, 5, 6, 7, and the
  calque table.
- **Reliability notes from the source itself.** `sumber/ai-slop.md` admits that there
  was no curated list of Indonesian AI phrases at the time of the research (August
  2026). The list was assembled from (1) confirmed items, (2) calques of English lists,
  (3) recognized LLM output patterns. The only distinctly Indonesian marker validated
  by native speakers is "hiruk pikuk". There is no corpus study of excess vocabulary
  for Indonesian yet.
- **Scripts.** None. Only `.github/workflows/release.yml` and the plugin manifest.

### A2. nothinx/naskah-id (NI)

- **Contents.** A skill for editing Indonesian academic work (EYD V, KBBI) with a firm
  contract: numbers, results, names, and citations are not changed, references are not
  invented, and the allowed changes are bounded per job type (correct, edit, rewrite,
  write). Separate references per problem: `pola-ai.md` (catalog AI-01 to AI-19 plus
  patterns without a code), `kalimat-efektif.md` (KE-01 to KE-17, NM-01, KL-01),
  `ejaan-eyd-v.md` (EJ-01 to EJ-10), `istilah.md` (term-equivalence decisions based on
  measured usage), `pertahankan.md` (conventions not to be corrected),
  `bagian-naskah.md`, `sitasi.md`, `singkatan.md`, `KONTRAK.md`.
- **License.** MIT (LICENSE file, frontmatter `license: MIT`).
- **Relevance.** The most relevant of all sources for this genre. Its labels separate K
  (rules, mandatory), G (style), and AI (machine cliches, "one occurrence is not yet a
  problem"). `pertahankan.md` protects the passive voice in Methods, "penelitian ini"
  as a subject, common foreign terms of the field, legitimate hedging, statistical
  "signifikan". `istilah.md` contains OpenAlex title-share data for engineering
  (mikrokontroler 91 %, *noise* 90 %, *timer* 87 %, catu daya versus *power supply*
  50:50).
- **Scripts (not run).** `scripts/periksa.py` (regex checker for K/G/AI, comparison of
  original numbers and citations against the draft, `--banding`), `scripts/openalex.py`
  (calls OpenAlex and Crossref over the network), `evals/jalankan.py`,
  `evals/banding.py`, `.github/workflows/periksa.yml`. `.mcp.json` registers the HTTP
  MCP servers `mcp.consensus.app` and `api.alphaxiv.org`. Not installed, not used.

### A3. adhiprib/humanizer-indonesia (HI)

- **Contents.** A skill for editing so that Indonesian text is not stiff, version 1.7.2
  (18 Nov 2026). `references/id-ai-tells.md` is the catalog of Indonesian tells (A
  syntax, B lexical, C cohesion, D discourse, E metric thresholds, F false positives, G
  excluded registers). `SKILL.md` (74 KB) contains an eight-step flow, Step 5b calque
  test, 5c personification and register test, 5d fusion of fragmented sentences, eleven
  mandatory checks when auditing another model's edits, and "Rules often missed". Many
  examples come from engineering texts (thermal, nuclear, *machine learning*), so they
  are close to the PA genre.
- **License.** MIT.
- **Relevance.** Catalog A to D and F, Steps 5b, 5c, 5d, the eleven checks (numbers,
  cross references `Tabel \d+\.\d+`, citations, equations), and the rules (hyphen in
  reduplication, *oleh* after a passive with an agent, *Sedangkan* not as a sentence
  opener, *linear*, KTSP consonant dropping). Important principles: "the metric is a
  necessary condition, not a sufficient one" and "rewrite, do not trim".
- **Not relevant.** The personal voice preset of the repo author (`voice-prib-id.md`),
  GPTZero calibration, the third-party Detectors section, and "Avoiding sterility" (the
  repo itself states that neutral technical text is a correct human voice).
- **Scripts (not run).** `scripts/metrik.py` (stdlib style metrics, thresholds
  calibrated to the repo owner's corpus), `portable/buat_paket.py` (package builder for
  ChatGPT/Gemini).

### A4. blader/humanizer (HU)

- **Contents.** An English skill v4.0.0, 26 patterns in six groups (A staging, B
  rhythm by rule, C inflation and borrowed authority, D format by rule, E chat and
  draft residue, F wrong reader). Derived from WP. Each pattern has a strength marker
  ("§1 to §5 once is enough", "*weak alone*").
- **License.** MIT.
- **Relevance.** The framework explaining "why" (the model picks the option that suits
  the widest readership), §1 Not X but Y, §5 arguing with a nonexistent opponent, §6
  triad, §9 stacked qualifiers, §12 AI vocabulary, §13 inflated significance, §14 vague
  association, §15 shallow *-ing* phrases, §17 borrowed authority, §18 avoiding
  *is/has*, §19 decorative bold, §24 heading repeated in the first sentence, §25
  writing about the document. The "When not to act" section (look for clusters of
  tells, not a single tell).
- **Scripts.** `scripts/validate-package.py` (package validation), `package.json`. Not
  run.

### A5. hardikpandya/stop-slop (SS)

- **Contents.** A short English skill for essay/blog prose: eight core rules,
  `phrases.md` (filler openers, emphasis crutches, business jargon, adverbs,
  meta-commentary), `structures.md` (binary contrasts, negative lists, dramatic
  fragmentation, rhetorical setup, *false agency*, distant narrator, passive, *Wh-*
  openers), a five-dimension score (below 35/50 gets revised).
- **License.** MIT.
- **Relevance.** Binary contrasts and *false agency* (personification),
  meta-commentary, vague declaratives ("implikasinya signifikan"), *lazy extremes*.
  Most of the rest conflicts with the thesis register (see D).
- **Scripts.** None.

### A6. Wikipedia:Signs of AI writing (WP)

- **Contents.** A guidance page of WikiProject AI Cleanup (`action=raw`, about 183 KB).
  Groups: Content (inflated significance and legacy, shallow *-ing* analysis, vague
  association, vague attribution, "challenges and prospects" conclusion), Language (AI
  vocabulary per model era, copula avoidance, negative parallelism, *rule of three*),
  Style (Title Case, bold, labeled lists, emoji, curly quotes), Citations (invalid
  DOIs, DOIs pointing to another article, books without pages), Signs of human
  writing, Ineffective indicators, Historical indicators (em dash 2022 to Sep 2026,
  section summaries, lexical diversity).
- **License.** CC BY-SA 4.0 (Wikipedia text). Verbatim quotes in the house skill
  require attribution and share-alike. Paraphrasing ideas is safe.
- **Relevance.** The strongest methodological warning: detectors and human judgment are
  close to random guessing, perfect grammar and formal prose are not markers, a single
  transition is not a strong marker. A new note: the newest models (Sep 2026 onward)
  are locked to not use em dashes, and as a result text that uses only commas and
  periods is starting to become a marker of its own (tagged `{{cn}}`, not yet
  sourced).
- **Scripts.** None.

---

## B. Pattern catalog

Format of each item: **Tell** (example), **Why**, **Fix** (example), **Source**,
**Machine?** (yes = regex or word list, with the pattern included; no = needs
judgment). Regexes are written in Python style, `(?i)` means case-insensitive. A
checker should strip `%` comments, `\cite{}`, `\ref{}`, `\label{}` arguments, the
`table`, `figure`, `equation` environments, and `\caption` before matching
(inference).

General principle from all sources: one occurrence is usually not yet a problem, a
cluster is (HU "When not to act", HI "Look for clusters of tells", NI "a single
occurrence is usually not yet a problem", WP "Ineffective indicators").

### B1. Word and phrase level

**B1.1 Cosmic or era openers**
- Tell: "Di era digital yang berkembang pesat ini, teknologi kesehatan memegang peranan
  yang sangat penting dalam kehidupan manusia."
- Why: the sentence can attach to any topic, so it carries no information. Reviewers
  skip it. Indonesian thesis backgrounds are full of this pattern (BS lists evidence
  from a thesis repository).
- Fix: "Rekaman Holter hanya mencakup 24 sampai 48 jam~\cite{holter}, sehingga
  aritmia yang muncul jarang dapat terlewat." If the replacement fact is not in the
  manuscript, do not invent one, mark `\PlaceholderData{...}`.
- Source: BS L1, `frasa-terlarang` §1, `bahasa-peneliti`; NI AI-01, AI-02; HI D1;
  SS ("In today's", "In a world where").
- Machine: yes.
  `(?i)\bdi (era|zaman|tengah) (digital|modern|globalisasi|serba|teknologi|pesatnya|derasnya|revolusi)`
  · `(?i)\bseiring (dengan )?(perkembangan|kemajuan|berjalannya) (zaman|teknologi|waktu)`
  · `(?i)\bdewasa ini\b` · `(?i)\bdalam dunia \w+ yang (terus|semakin) berkembang`
  · `(?i)\bdalam beberapa tahun terakhir\b` (weak, needs a number in the same sentence).

**B1.2 Emphasis without content**
- Tell: "Tidak dapat dipungkiri bahwa pemantauan jantung kontinu sangat dibutuhkan."
- Why: the intensifier replaces evidence. If the claim is well established, the
  reference alone is enough.
- Fix: "Pemantauan jantung kontinu dibutuhkan karena sebagian aritmia muncul
  sesekali~\cite{kunci}."
- Source: BS L1; NI AI-03, AI-04; HI B2, D1.
- Machine: yes. `(?i)\bt(idak|ak) (dapat|bisa) dipungkiri\b` · `(?i)\bseperti yang (kita )?(ketahui|diketahui)( bersama)?\b` · `(?i)\bsudah menjadi rahasia umum\b` · `(?i)\bsebagaimana kita ketahui\b`.

**B1.3 Meta sentences and lecturing tone**
- Tell: "Perlu diketahui bahwa sinyal ECG sangat rentan terhadap *noise*."
- Why: a sentence about the writing or an invitation to talk, not about the topic.
  Deletion test: if no information is lost, delete it.
- Fix: "Sinyal ECG rentan terhadap \textit{noise} gerak dan \textit{baseline
  wander}."
- Source: BS L7; NI AI-11; HI 5c.3; HU §4, §25; SS meta-commentary.
- Machine: yes. `(?i)\b(perlu|penting untuk) (diketahui|dicatat|dipahami|diingat|diperhatikan)( bahwa)?\b` · `(?i)\bpatut (dicatat|diperhatikan)\b` · `(?i)\bmari kita\b` · `(?i)\bperhatikan bahwa\b` · `(?i)\byang menarik(nya)? adalah\b`.

**B1.4 Slop vocabulary and prestige words without function**
- Tell: "Penelitian ini menyelami lanskap TinyML yang krusial untuk menghadirkan solusi
  holistik dan komprehensif."
- Why: words whose frequency spiked because of machines, not because of speakers. In
  English this is proven by corpus studies (BS cites Kobak et al. 2025, *delves* ratio
  28.0). The Indonesian version is a qualitative calque (BS admits this).
- Fix: "Penelitian ini menerapkan TinyML pada ESP32-S3 untuk mengklasifikasi
  aritmia langsung di perangkat."
- Source: BS L5 and `frasa-terlarang` §6; HI B2, B3; HU §12; WP AI vocabulary.
- Machine: yes, the word list in C, but it needs judgment on literal or technical
  meaning (*mengoptimalkan* is legitimate if there really is an optimization, *tangguh*
  or *robust* is legitimate as a technical term per HU §12, *mengimplementasikan* is
  common in engineering although HI B3 flags it).

**B1.5 Empty intensifiers and inflated claims**
- Tell: "Mikrokontroler memegang peranan yang sangat krusial dan menjadi kunci utama
  keberhasilan sistem."
- Why: an adjective replaces evidence. A reviewer asks "crucial compared to what".
- Fix: "Mikrokontroler menjalankan prapemrosesan, inferensi, dan pengiriman data
  dalam satu siklus 2~detik." (this triplet example is legitimate because the three
  tasks are real, see B2.3).
- Source: BS `bahasa-peneliti` anti-slop table; NI AI-07, AI-09; HI B2; HU §13;
  WP undue emphasis; SS vague declaratives; NP rule 4.
- Machine: yes. `(?i)\bmemegang peranan (yang )?(sangat )?(penting|krusial|vital|sentral|strategis)` · `(?i)\bberperan (sangat )?(vital|krusial)\b` · `(?i)\bmenjadi (kunci utama|faktor kunci)\b` · `(?i)\btak lepas dari\b|\btidak (dapat )?dipisahkan dari\b` · `(?i)\bsolusi (yang )?(inovatif|revolusioner|tepat guna)\b` · `(?i)\bsangat (efektif dan efisien|luar biasa)\b`.

**B1.6 "Signifikan" without a statistical test**
- Tell: "Kuantisasi INT8 menurunkan akurasi secara tidak signifikan."
- Why: in a quantitative manuscript "signifikan" means statistical and is not graded.
- Fix: "Kuantisasi INT8 menurunkan akurasi 0,4 poin persentase, di bawah ambang
  1 poin yang ditetapkan."
- Source: BS; NI AI-12, `pertahankan.md`; HI B3; NP rule 4.
- Machine: yes for flagging. `(?i)\bsangat signifikan\b` (certainly wrong) · `(?i)\bsignifikan\b` without `p\s*[<=>]` or a test name in the same sentence (review).

**B1.7 Absolute words**
- Tell: "Sistem ini selalu mampu mendeteksi aritmia secara pasti."
- Why: an absolute claim without data across its whole scope.
- Fix: "Sistem mendeteksi 97,1 % detak aritmia pada data uji MIT-BIH."
- Source: BS diction; HI B5; SS lazy extremes; NP rule 4.
- Machine: yes. `(?i)\b(pasti|selalu|tidak pernah|menjamin|dijamin|sempurna|tanpa cacat|tidak diragukan lagi|semua orang)\b`.

**B1.8 Repeated cliche transitions and connectors**
- Tell: "Selain itu, ... Oleh karena itu, ... Di sisi lain, ... Dengan demikian, ..."
  at the start of nearly every sentence or paragraph.
- Why: connectors that keep appearing lose their function. Indonesian connects through
  repetition of key words and the clitic *-nya* (HI C1). HI warns that an edit that
  removes nearly all connectors reads even more like AI, so what is acted on is the
  density, not the presence.
- Fix: "Bufer menampung 2.500 sampel. Isinya dikirim saat penuh, sehingga
  pengiriman tidak memblok akuisisi."
- Source: BS L6 (each transition at most once per text, not in two consecutive
  paragraphs); NI AI-16, AI-17, AI-19 (thresholds 3 and 2 times); HI C1 (more than 3
  per 100 words or more than 50 % of paragraphs opened by a connector); HI 5c.3
  (*Konsekuensinya*); WP (a single transition is not a strong marker); NP rule 8
  (rotation of five opener types).
- Machine: yes, counting. List: `Selain itu|Tidak hanya itu|Terlebih lagi|Lebih lanjut|Tak kalah penting|Namun demikian|Oleh karena itu|Oleh sebab itu|Dengan demikian|Di sisi lain|Sementara itu|Selanjutnya|Secara keseluruhan|Pada akhirnya|Dengan kata lain|Konsekuensinya` at the start of a sentence. Proposed threshold (inference, combining HI and NI): more than 3 per 100 words, or the same connector more than 2 times per subsection, or two consecutive paragraphs opened by a connector.

**B1.9 "Hal ini" and vague pointers**
- Tell: "Akurasi turun pada data sinyal tubuh. Hal ini disebabkan oleh *noise* gerak."
- Why: the reader has to guess what is pointed at.
- Fix: "Akurasi turun pada data sinyal tubuh. Penurunan tersebut berasal dari
  \textit{noise} gerak."
- Source: NI AI-15 (threshold 3); HI A5 example; NP rule 8.
- Machine: yes. `(?i)\bhal (ini|tersebut)\b` count, flag at 3 or more per subsection.

**B1.10 Empty umbrella words**
- Tell: "Kinerja model dipengaruhi berbagai aspek dan faktor-faktor tertentu."
- Why: it defers the content, the variables are not named.
- Fix: "Kinerja model dipengaruhi panjang \textit{window}, kuantisasi, dan
  galat penempatan R-\textit{peak}."
- Source: NI pattern "Empty umbrella words"; BS (berbagai macam).
- Machine: yes. `(?i)\bberbagai (aspek|faktor|bidang|kalangan|hal|dimensi)\b` · `(?i)\bfaktor-faktor tertentu\b` · `(?i)\bperan strategis\b`.

**B1.11 Vague attribution**
- Tell: "Banyak penelitian menunjukkan bahwa CNN satu dimensi unggul untuk ECG."
- Why: an unnamed authority props up the claim. WP also notes inflation of the number
  of sources (one source written as "banyak penelitian").
- Fix: "CNN satu dimensi mencapai akurasi di atas 95 % pada MIT-BIH~\cite{a,b}."
  If the reference is not there yet, mark it, do not invent.
- Source: BS L8; NI; HI B5; HU §17; WP vague attributions.
- Machine: yes. `(?i)\b(banyak|sejumlah|berbagai|beberapa) (penelitian|studi|peneliti|ahli|literatur)\b|\bpara ahli\b` without `\cite` in the same sentence.

**B1.12 Ritual closers**
- Tell: "Dengan demikian dapat disimpulkan bahwa sistem yang dirancang sangat penting
  bagi kesehatan masyarakat."
- Why: the paragraph is closed by repeating its content or by empty praise.
- Fix: delete the sentence if the paragraph already contains the finding, or close with
  a concrete consequence "Latensi 1,2~detik ini masih di bawah batas peringatan 5~detik."
- Source: BS L2, `frasa-terlarang` §3; NI AI-18, KE (Dengan demikian dapat disimpulkan);
  HI D2; HU §2, §13; WP section summaries.
- Machine: yes. `(?i)\bdengan demikian,? dapat disimpulkan( bahwa)?\b` · `(?i)\bsecara keseluruhan\b` · `(?i)\bdemikianlah\b` · `(?i)\bsebagai (kesimpulan|penutup)\b` · `(?i)\bmasa depan \w+ (terlihat )?(sangat )?menjanjikan\b` · `(?i)\bsemoga\b`.

**B1.13 Chatbot residue and tool traces**
- Tell: "Tentu, berikut revisi subbab pengujian latensi." or `【4†source】`,
  `oaicite`, `[cite: 1]` that got copied along.
- Why: conversation leftovers, the clearest sign and the easiest to miss (HU §22).
- Fix: delete the wrapper, keep the content.
- Source: BS `frasa-terlarang` §7; HI D11; HU §22, §23; WP collaborative communication,
  phrasal templates.
- Machine: yes. `(?i)\b(tentu|baik),? berikut\b` · `(?i)\bsemoga (membantu|bermanfaat)\b` · `(?i)\bjangan ragu untuk\b` · `contentReference|oaicite|turn0search|\[cite:\s*\d+\]|【|】` · placeholder `\[(Nama|Tanggal|Tahun|NAMA)[^\]]*\]`.

**B1.14 Pleonasm**
- Tell: "Data adalah merupakan hasil rekaman yang disebabkan karena kebutuhan uji."
- Why: a grammar rule, not specific to AI, but it often accompanies machine prose and
  translations.
- Fix: "Data ini hasil rekaman untuk kebutuhan uji."
- Source: NI KE-02 to KE-09; BS economy; HI B1.
- Machine: yes (NI regex). `(?i)\badalah merupakan\b` · `(?i)\b(agar supaya|demi untuk|sejak dari)\b` · `(?i)\bsangat\s+\w+\s+sekali\b` · `(?i)\b(para|banyak|berbagai|beberapa)\s+(\w+)-\2\b` · `(?i)\bberbagai macam\b` · `(?i)\b(naik ke atas|turun ke bawah|mundur ke belakang|maju ke depan)\b` · `(?i)\bdisebabkan karena\b` · `(?i)\bdalam rangka untuk\b` · `(?i)\bberdasarkan (pada|kepada)\b` · `(?i)\bseperti\b[^.;]{1,80}?\b(dan lain-lain|dll\.?|dan sebagainya|dsb\.?)`.

### B2. Sentence level

**B2.1 Negative parallelism and formulaic contrast**
- Tell: "Sistem ini tidak hanya mendeteksi aritmia, tetapi juga menghadirkan pemantauan
  yang komprehensif." or "Edge computing bukan lagi pilihan, melainkan keharusan."
- Why: the negative half names something nobody ever claimed, so the positive half
  sounds bigger without adding a claim. The number one AI pattern according to BS and
  HU.
- Fix: "Sistem mendeteksi aritmia di perangkat dan mengirim ringkasannya ke
  \textit{dashboard}."
- Note: NI stresses that "bukan hanya ..., tetapi juga ..." is a standard conjunction.
  What is acted on is repeated use or an empty negative half.
- Source: BS L3; NI AI-10, `pertahankan.md`; HI D7; HU §1; SS binary contrasts; WP
  negative parallelisms.
- Machine: yes. `(?i)\b(bukan|tidak) (hanya|sekadar|cuma)\b[^.]{1,80}?\b(tetapi|namun|melainkan) (juga)?\b` · `(?i)\blebih dari sekadar\b` · `(?i)\bbukan lagi\b[^.]{1,40}?\bmelainkan\b` · `(?i)\bbukan tentang\b[^.]{1,60}?\bmelainkan\b`.

**B2.2 Anticipatory denial (arguing with a nonexistent opponent)**
- Tell: "Akurasi model mencapai 98 %. Ini bukan berarti sistem siap dipakai di klinik."
- Why: it denies a conclusion the reader did not draw. HI rates this the most easily
  recognized slop, target zero per document.
- Fix: "Akurasi model 98 % diukur pada data MIT-BIH, sedangkan validasi klinis
  belum dilakukan."
- Source: HI D7, 5c.4; HU §5; SS ("doesn't mean X").
- Machine: yes. `(?i)\b(ini|hal ini|itu)? ?bukan berarti\b` · `(?i),\s*bukan berarti\b`. Exclude "tidak berarti" in the statistical sense.

**B2.3 Triplet (rule of three)**
- Tell: "Sistem yang dirancang bersifat efektif, efisien, dan andal."
- Why: three qualities sound complete but are rarely proven one by one.
- Fix: "Sistem mengonsumsi 180~mA saat inferensi dan bertahan 9~jam dengan
  baterai 2.000~mAh." Three items that are all meaningful (three metrics, three
  classes) remain legitimate. HI gives four actions (drop the item without information,
  state the hidden hierarchy, move the item with a different relation into its own
  sentence, split the combined competence) and a tentative benchmark of about 1.5
  triplets per 1,000 words. A triplet in parentheses is still a triplet.
- Source: BS L4; NI; HI D3; HU §6; SS; WP rule of three.
- Machine: partly. Heuristic `\b(\w+), (\w+),? dan (\w+)\b` with all three being
  adjectives from the list (efektif, efisien, andal, akurat, cepat, tepat, aman, nyaman,
  murah, inovatif, optimal, terjangkau, berkelanjutan), count the density per 1,000
  words. The decision remains a judgment.

**B2.4 Missing subject because of a preposition**
- Tell: "Berdasarkan Tabel~4.2 menunjukkan bahwa latensi rata-rata 1,2~detik." or
  "Pada Gambar~3.5 memperlihatkan alur prapemrosesan."
- Why: the preposition turns the candidate subject into an adverbial, so the sentence
  has no subject. Structure errors are the largest error class in theses (34 %).
- Fix: "Tabel~4.2 menunjukkan latensi rata-rata 1,2~detik." or "Berdasarkan
  Tabel~4.2, latensi rata-rata 1,2~detik."
- Source: BS `kalimat-akademik` §1; NI KE-01; HI A6. The "Berdasarkan Tabel" pattern is
  also limited by NP rule 2.
- Machine: yes (NI regex KE-01, adjusted for sentence start).
  `(?:^|(?<=[.!?])\s+)(?:Dari|Dalam|Pada|Bagi|Menurut|Berdasarkan)\s(?:(?!\b(?:penulis|peneliti)\b)[^.?!,;:]){1,60}?\s(?:menunjukkan|membahas|memperlihatkan|menjelaskan|mengatakan|menyatakan|menggambarkan|menyajikan|menyimpulkan|membuktikan)\b`.

**B2.5 Paired conjunctions**
- Tell: "Meskipun akurasinya tinggi, tetapi galat masih muncul pada kelas minoritas."
  or "Berdasarkan uraian tersebut, maka diperlukan sistem pemantauan kontinu."
- Why: two conjunctions for one relation. A grammar rule, often appearing in calques.
- Fix: "Meskipun akurasinya tinggi, galat masih muncul pada kelas minoritas."
- Source: BS; NI KE-14, KE-15; HI A7.
- Machine: yes. `(?i)\b(meskipun|walaupun|walau|biarpun|kendatipun)\b[^.;]{1,120}?,\s*(tetapi|namun)\b` · `(?:^|(?<=[.!?])\s+)(Karena|Sebab|Oleh karena|Berdasarkan|Mengingat)\b[^.;]{1,120}?,\s*maka\b`.

**B2.6 "Sehingga" and "Sedangkan" as sentence openers, comma before "sehingga"**
- Tell: "Bufer penuh dalam 10~detik. Sehingga data harus segera dikirim."
- Why: both are intra-sentence conjunctions. EYD V comma rule 4 (no comma when the main
  clause precedes the subordinate clause).
- Fix: "Bufer penuh dalam 10~detik sehingga datanya harus segera dikirim." or
  "Akibatnya, data harus segera dikirim."
- Source: NI KE-16, EJ-10; HI rule *Sedangkan*; NP rule 5 (limit on "sehingga").
- Machine: yes. `(?:^|(?<=[.!?])\s+)(Sehingga|Sedangkan)\b` · `,\s+sehingga\b`.

**B2.7 Copula avoided or copula as default**
- Tell (avoided): "ESP32-S3 berperan sebagai otak dari keseluruhan sistem." Tell
  (default): every paragraph opens with "X merupakan ...".
- Why: the model replaces "adalah" and "punya" with "berperan sebagai, hadir sebagai,
  menawarkan, dilengkapi dengan" (WP notes a drop of more than 10 % in *is/are* in 2023
  academic writing). Conversely HI A5 notes *merupakan* as the default copula of
  Indonesian models.
- Fix: "ESP32-S3 adalah pengendali utama sistem." For true definitions *merupakan* or
  *adalah* remain legitimate (HI F5).
- Source: BS `frasa-terlarang` §5; HI A5; HU §18; WP copulatives.
- Machine: partly. `(?i)\b(berperan|bertindak|hadir|berdiri) sebagai\b|\bmenjadi wadah bagi\b` · count paragraphs whose first sentence contains `\bmerupakan\b` (review if more than half).

**B2.8 Nominalization and light verbs**
- Tell: "Peneliti melakukan pengukuran terhadap arus yang mengalami peningkatan sebesar
  12 %."
- Why: the number one cause of stiffness according to HI. Not an absolute ban in the
  scientific register (BS, NI) when the noun is truly the subject matter.
- Fix: "Arus terukur naik 12 %."
- Source: BS obligation 3, `kalimat-akademik` §2; NI NM-01; HI A1 (threshold more than 1
  per 100 words).
- Machine: yes. `(?i)\b(melakukan|mengalami|memberikan|mengadakan|melaksanakan)\s+(pe\w{3,}an|ke\w{3,}an)\b` · `(?i)\bmemberikan (pengaruh|kontribusi) terhadap\b` · `(?i)\btelah dilakukan pe\w+an terhadap\b`.

**B2.9 Stacked reflexive passives**
- Tell: "Pengujian dilakukan dengan menggunakan board. Hasil diperoleh setelah
  pengujian dilakukan. Grafik ditampilkan pada Gambar~4.1."
- Why: the passive is legitimate in Methods and Results (NI, HI F1), what becomes a
  tell is the stack of *dilakukan, diperoleh, ditampilkan* and passive plus
  nominalization.
- Fix: "Pengujian memakai \textit{board} N16R8, dan hasilnya tersaji pada
  Gambar~4.1."
- Source: HI A2 (passive ratio above 60 % outside Methods); NI stacked passive.
- Machine: partly. Count `(?i)\bdi\w+kan\b|\bdi\w+i\b` per sentence, flag paragraphs
  with `\bdilakukan\b` 2 times or more (inference threshold).

**B2.10 Interpretive tail clause**
- Tell: "Latensi inferensi 38~ms, yang menunjukkan keandalan sistem dalam pemantauan
  waktu nyata."
- Why: the equivalent of the English *-ing* phrase that attaches meaning or
  significance to a simple fact without basis.
- Fix: "Latensi inferensi 38~ms, jauh di bawah periode \textit{window} 2~detik."
- Source: BS `frasa-terlarang` §5 (tail clause); HU §15; WP superficial analyses.
- Machine: partly. `(?i),\s*(yang )?(menunjukkan|mencerminkan|menegaskan|menandakan|menggarisbawahi|menyoroti|menjadikannya)\b` then review whether what follows is a fact or a judgment.

**B2.11 Monotonous sentence openers and direction markers**
- Tell: "Hasilnya jelas." "Pertanyaannya sederhana." "Kemudian ada tantangan konsumsi
  daya." repeated across several subsections.
- Why: sentences that only announce the topic or stage the point. The largest source of
  AI sentences in HI's test.
- Fix: merge with the first fact, "Konsumsi daya menjadi kendala karena
  modul WiFi menarik arus puncak 310~mA."
- Source: HI 5c.3, 5c.5, D8; HU §4, §7; SS throat-clearing.
- Machine: partly. List from HI: `Pertanyaannya sederhana|Gagasannya sederhana|Hasilnya tegas|Prosedurnya begini|Cara membacanya begini|Mari kita lihat|Perhatikan bahwa|Tiga hal langsung terlihat|Konsekuensinya,|Di situlah`. Repeated openers can be counted (the same first three words of a sentence more than 2 times per chapter). General direction markers need judgment.

**B2.12 Uniform or fragmented rhythm**
- Tell: a series of sentences of 20 to 28 words with the same pattern, or a series of
  short single-clause sentences.
- Why: models tend toward flat rhythm. HI finds both directions equally conspicuous.
- Fix: short finding sentences, longer cause-and-effect ones, join fragments with
  meaningful conjunctions (*karena, sehingga, sedangkan, meskipun*), not commas and
  *dan*.
- Source: BS obligation 5; NI KL-01 (more than 35 words); HI A4 (mean above 24,
  standard deviation below 6), 5d (mean below 16 and more than 30 % of sentences of 10
  words or fewer); HU §2; SS; NP rule 5 (15 to 30 words).
- Machine: yes (sentence-length metrics per paragraph and per subsection).

**B2.13 Dramatic fragments and one-line closers**
- Tell: "Hasilnya? Sangat memuaskan." or "Sederhana, tetapi efektif."
- Why: asks the reader to stop at a claim instead of adding facts.
- Fix: "Seluruh 12 skenario uji memenuhi target latensi."
- Source: HU §2, §3; SS dramatic fragmentation, rhetorical setups.
- Machine: partly. A sentence under 5 words at the end of a paragraph, or a `?` mark in
  the paragraph body (see B3.14).

**B2.14 Stacked modality and shifted degree of certainty**
- Tell: "Penambahan filter mungkin dapat berpotensi meningkatkan akurasi." or the
  opposite "Hasil ini membuktikan bahwa \textit{jitter} menyebabkan kenaikan F1."
- Why: one clause needs only one uncertainty marker. Editing must not shift the ladder
  *menunjukkan* (fact), *mengindikasikan* (inference), *diduga* (hypothesis) in either
  direction (HI B4).
- Fix: "Penambahan filter berpotensi meningkatkan akurasi." · "Pada tiga
  \textit{seed}, \textit{jitter} diikuti kenaikan F1 sebesar 0,012."
- Source: BS L8, `kalimat-akademik` §5; NI KK-01, `pertahankan.md` legitimate hedging;
  HI B4; HU §9; NP rule 4.
- Machine: yes for flagging. `(?i)\b(mungkin|dapat|bisa|cenderung|berpotensi|kemungkinan|diduga)\s+(mungkin|dapat|bisa|cenderung|berpotensi|kemungkinan)\b` · `(?i)\bmembuktikan\b` (check claim strength).

**B2.15 Chain of "yang"**
- Tell: "Sistem yang dirancang yang memakai sensor yang dipasang pada dada yang ..."
- Why: stacked relative clauses lose the main clause of the sentence.
- Fix: split into two sentences.
- Source: NI pattern Chain of "yang".
- Machine: yes. Three or more `\byang\b` within a 15-word window without a comma.

**B2.16 Personification of inanimate objects (false agency)**
- Tell: "Model cukup cerdas untuk mengenali detak ektopik, sedangkan ESP32-S3 bekerja
  keras menjaga data tetap aman."
- Why: inanimate objects are given character, intent, or emotion. HI rates it the most
  conspicuous tell in technical text and no script sees it.
- Fix: "Model mengklasifikasi detak ektopik dengan \textit{recall} 0,91. Data
  disimpan ke LittleFS sebelum dikirim."
- Note: dead metaphors that are standard in the engineering literature remain allowed
  (*sinyal merambat*, *gradien lenyap*). SS's advice "name the human or use *you*" does
  not apply (D).
- Source: HI 5c.1; SS false agency.
- Machine: no (a word list of character words such as *cerdas, malas, berani, tahu,
  berusaha, bekerja keras* can help flag, but the decision is a judgment).

**B2.17 Vague association**
- Tell: "Penurunan akurasi berkaitan dengan kualitas elektroda."
- Why: states that two things are connected without naming the relation.
- Fix: "Akurasi turun 4 poin saat impedansi elektroda di atas 50~k$\Omega$."
  If the relation really is unknown, keep the vague wording and state it as a
  conjecture.
- Source: HU §14; WP vague connection.
- Machine: partly. `(?i)\b(berkaitan|terkait|berhubungan|terhubung|berasosiasi) dengan\b` for review.

### B3. Paragraph and structure level

**B3.1 Sentences about the document**
- Tell: "Subbab ini akan membahas perancangan perangkat keras." or "Tulisan ini
  membahas ..."
- Why: the document explains itself, not its topic.
- Fix: go straight to the content, "Perangkat keras terdiri atas ESP32-S3, AD8232, dan
  INA219."
- Source: BS L7; HU §25; SS meta-commentary; HI 5b (document made the agent).
  Already required by NP rule 7 (N-META).
- Machine: yes. `(?i)\b(bab|subbab|bagian|butir|tulisan|artikel) ini (akan )?(membahas|memaparkan|menguraikan|menjelaskan|bertujuan)\b` · `(?i)\bpada (bab|subbab|bagian) ini akan\b`.

**B3.2 Heading repeated in the first sentence**
- Tell: `\subsection{Pengujian Latensi}` then "Pengujian latensi merupakan pengujian
  untuk mengukur latensi sistem."
- Why: the first sentence repeats the title before the content begins.
- Fix: "Latensi diukur dari detak terakhir dalam \textit{window} sampai alarm
  berbunyi."
- Source: HU §24.
- Machine: partly. Flag when more than half of the content words of the heading appear
  in the first sentence that contains "merupakan" or "adalah" (inference heuristic).

**B3.3 Summary at the end of every paragraph**
- Tell: every paragraph ends with "Hal ini membuktikan bahwa sistem bekerja dengan baik."
- Why: repeats the content of the paragraph. The conclusion belongs in Chapter 5 only.
- Fix: delete, or replace with a consequence not yet mentioned.
- Source: NI AI-18; HI D2; HU §2; WP section summaries.
- Machine: partly. The B1.12 patterns in the last sentence of a paragraph, plus
  `(?i)\bhal ini (membuktikan|menunjukkan) bahwa\b` in final position.

**B3.4 Paragraphs that are too tidy**
- Tell: every paragraph follows the pattern thesis sentence, three supports, closing
  sentence.
- Why: perfect structure feels algorithmic (HI D5).
- Fix: keep the claim sentence at the start (NP rule 6), drop the ritual closing
  sentence, let the number of supporting sentences follow the content.
- Source: HI D5.
- Machine: no.

**B3.5 Generic challenges-and-prospects section, generic suggestions**
- Tell: "Meskipun memiliki beberapa keterbatasan, sistem ini tetap memiliki prospek
  yang menjanjikan." or the suggestion "Perlu dilakukan penelitian lebih lanjut."
- Why: the "despite its challenges" formula and a suggestion without direction.
- Fix: "Konsumsi daya belum diukur dengan baterai, sehingga daya tahan 9~jam
  masih perkiraan dari arus rata-rata." · "Uji sinyal tubuh perlu diperluas ke subjek
  dengan riwayat aritmia."
- Source: WP outline-like conclusions; HU §13; BS `frasa-terlarang` §3,
  `struktur-sitasi`; NI `bagian-naskah` (Simpulan).
- Machine: partly. `(?i)\bmeskipun (memiliki|terdapat) (beberapa |berbagai )?(keterbatasan|kekurangan|tantangan)\b` · `(?i)\bperlu (dilakukan )?penelitian lebih lanjut\b` (review whether the direction is named).

**B3.6 Literature review as a per-source list**
- Tell: "Menurut Ahmad~\cite{a}, ... Senada dengan itu, Budi~\cite{b} ... Menurut
  Citra~\cite{c}, ..."
- Why: each sentence opens with a name, and the relation between findings is only
  "senada". No synthesis happens.
- Fix: "Klasifikasi aritmia di mikrokontroler umumnya memakai CNN satu dimensi
  dengan kuantisasi INT8~\cite{a,b}, sedangkan pendekatan LSTM membutuhkan memori
  lebih besar~\cite{c}."
- Note: the source examples use APA style (Name, year). The PA book uses numbered
  citations, so the pattern becomes "Menurut X~\cite{}" and "Penelitian X~\cite{}"
  (inference). If the per-paper Related Work structure is a campus convention (a
  subsection per paper title in buku-pa), this rule applies in synthesis paragraphs,
  not in the per-paper subsections.
- Source: BS `struktur-sitasi`; NI `bagian-naskah`; HI D9 (the metric counts 3 or more
  "Menurut Nama" sentences).
- Machine: yes. Count sentences opened by `(?i)^(Menurut|Penelitian oleh|Penelitian)\s+\S+.*~?\\cite` more than 2 per subsection · `(?i)\b(senada|sejalan) dengan (itu|hal tersebut)\b`.

**B3.7 Background from the cosmos to the topic**
- Tell: the first paragraph of Chapter 1 starts from information technology in general,
  then health, then the heart, only then the topic.
- Why: the classic Indonesian academic slop (BS).
- Fix: the first sentence contains specific data or the problem, with the order
  phenomenon with data, what is already known, gap, objective.
- Source: BS `bahasa-peneliti`; NI `bagian-naskah` (Pendahuluan).
- Machine: no (B1.1 catches some of the opening sentences).

**B3.8 Bulleted lists for arguments, bold label plus colon**
- Tell: `\item \textbf{Efisiensi:} sistem sangat efisien ...` for a discussion.
- Why: an outline forced into prose. Indonesian scientific manuscripts convey arguments
  in paragraphs (NI).
- Fix: a paragraph with a topic sentence. Lists remain in use for true enumeration
  (steps, specifications), per NP rule 5.
- Source: NI dotted lists; HI D6; BS L10; HU §19; WP inline-header lists.
- Machine: yes. `\\item\s*\\textbf\{[^}]*\}\s*:?` and `\\textbf\{` inside ordinary
  paragraphs (decorative bold).

**B3.9 Enumeration leaning on "seperti"**
- Tell: "Sistem memakai komponen seperti ESP32-S3, AD8232, INA219, buzzer, dan lain
  sebagainya."
- Why: a bloated sentence, and "seperti" implies an incomplete list without basis (WP
  also notes *such as* before a complete list).
- Fix: "Sistem terdiri atas ESP32-S3, AD8232, INA219, dan \textit{buzzer}." The
  referring function ("seperti yang ditunjukkan Gambar~3.2") remains legitimate (HI F6).
- Source: HI D4 (more than 1 per 1,000 words); NI KE-09; WP.
- Machine: yes. `(?i)\b(seperti|antara lain|misalnya|di antaranya)\s+[^.]{0,60},[^.]{0,60}\bdan\b` excluded when followed by `yang (ditunjukkan|terlihat|disajikan)`.

**B3.10 Pseudo-range "mulai dari X hingga Y"**
- Tell: "Sistem dapat dipakai mulai dari rumah sakit hingga rumah pasien."
- Why: X and Y are not the ends of one scale.
- Fix: "Sistem dapat dipakai di rumah sakit dan di rumah pasien." A real range
  ("frekuensi 0,5 hingga 40~Hz") remains legitimate.
- Source: HI D12. See the conflict in D (the house rules recommend "mulai dari ... hingga
  ..." as a replacement for the colon).
- Machine: yes for flagging. `(?i)\bmulai dari\b[^.]{1,60}?\b(hingga|sampai)\b`, review whether both ends are numeric or scaled.

**B3.11 Pseudo-spatial references**
- Tell: "Hasil pengujian dapat dilihat pada tabel di bawah ini."
- Why: the LaTeX float position moves. Refer by number.
- Fix: "Tabel~\ref{tab:latensi} menyajikan hasil pengujian latensi."
- Source: HI D10, the rule "Refer to tables and figures by their number".
- Machine: yes. `(?i)\b(tabel|gambar|grafik|diagram|persamaan)\s+(berikut( ini)?|di (atas|bawah)( ini)?)\b` · `(?i)\bsebagai berikut\b` (weak).

**B3.12 Strings of facts and the textbook order mechanism**
- Tell: a Chapter 2 paragraph that lists the ESP32-S3 specifications in sequence (core,
  frequency, SRAM, PSRAM, WiFi) without a link to the needs of the system.
- Why: still reads as AI even though the sentences are clean (HI, one test text,
  tentative).
- Fix: tie the facts to a claim that is already in the manuscript with *karena* or
  *sehingga*, "PSRAM 8~MB dipilih karena bufer rekaman 30~menit membutuhkan sekitar
  1,8~MB." Do not add new facts.
- Source: HI D13, 5c.6.
- Machine: no.

**B3.13 Decorative formatting**
- Tell: random `\textbf{}` in the middle of a paragraph, emoji, divider lines, titles in
  popular-article style ("Mengapa ESP32? Jawabannya Mengejutkan").
- Why: formatting by rule, not by content.
- Fix: bold only for the term being defined, descriptive titles.
- Source: BS L10; HI D11; HU §19, §20; WP style.
- Machine: yes. `\\textbf\{` in a paragraph · the Unicode emoji range `[\U0001F300-\U0001FAFF☀-➿]` · `\\hrule|\\rule\{\\linewidth\}`.

**B3.14 Rhetorical questions**
- Tell: "Lalu, bagaimana jika sinyal terganggu saat pasien bergerak?"
- Why: rhetorical setup, a lecture or blog tone.
- Fix: "Sinyal yang terganggu gerak ditandai \textit{lead-off} dan tidak
  diklasifikasi."
- Source: BS §1 (Pernahkah Anda, Tahukah Anda); HI D11; SS rhetorical setups.
- Machine: yes. The `?` mark in the paragraph body outside quotes and problem statements.

### B4. Register

**B4.1 First and second person pronouns**
- Tell: "Kami merancang sistem ini agar Anda dapat memantau jantung kapan saja."
- Why: the scientific register rests on ideas, not on the writer. House rule: a single
  writer, no "kami".
- Fix: "Sistem dirancang untuk memantau detak jantung secara kontinu."
- Source: BS `bahasa-peneliti` (passive plus "penelitian ini"); NI (one point of view
  per manuscript); HI pronoun rules.
- Machine: yes. `(?i)\b(kami|kita|saya|anda|kamu|aku)\b` (exclude direct quotes).

**B4.2 Promotional tone**
- Tell: "Kini hadir sebagai solusi tepat, sistem ini dirancang khusus untuk memberikan
  hasil yang maksimal."
- Why: advertising register in engineering text.
- Fix: "Sistem mengklasifikasi lima kelas detak AAMI di perangkat tanpa koneksi
  internet."
- Source: BS §4, §5 (robotic solution bridge); WP promotional language; HU §16.
- Machine: yes. `(?i)\b(kini|telah) hadir\b` · `(?i)\bsolusi (terbaik|tepat|lengkap|terpercaya|jitu)\b` · `(?i)\bdirancang khusus\b` · `(?i)\bhasil (yang )?(maksimal|optimal)\b` · `(?i)\btak perlu (khawatir|pusing) lagi\b` · `(?i)\bmempermudah (hidup|kehidupan)\b` · `(?i)\b(revolusioner|terobosan baru|pengubah permainan|game changer)\b`.

**B4.3 Colloquial**
- Tell: "Prosesnya gampang dan nggak ribet, nilai F1 berayun dari 0,85 sampai 0,92."
- Why: conversational register in a formal manuscript.
- Fix: "Nilai F1 berfluktuasi antara 0,85 dan 0,92."
- Source: BS academic diction; HI 5c.2.
- Machine: yes. `(?i)\b(bikin|banget|nggak|ngga|gak|kayak|gampang|ribet|gimana|aja|nembus|muter|jadul|goyangan|tukar guling)\b`.

**B4.4 Emotional and evaluative words**
- Tell: "Hasilnya sangat mengejutkan dan luar biasa memuaskan."
- Why: report the numbers, let the reader judge.
- Fix: "Akurasi pada data sinyal tubuh 0,93, lebih tinggi dari perkiraan 0,88."
- Source: BS `kalimat-akademik` §5, `bahasa-peneliti`; SS telling instead of showing.
- Machine: yes. `(?i)\b(mencengangkan|mengejutkan|luar biasa|sayangnya|menakjubkan|sangat menarik|memuaskan)\b`.

**B4.5 Overcorrection to a bureaucratic register**
- Tell: "Adapun dalam rangka guna mengetahui kinerja sistem, maka dilaksanakan
  kegiatan pengujian."
- Why: HI warns against swapping calques and colloquialisms for a bureaucratic register.
- Fix: "Kinerja sistem diuji dengan rekaman sinyal tubuh S01."
- Source: HI guardrails 5b and 5c; NI openers "Adapun", "dalam rangka".
- Machine: yes. `(?:^|(?<=[.!?])\s+)Adapun\b` · `(?i)\bdalam rangka\b` · `(?i)\bguna (mengetahui|meningkatkan)\b`.

### B5. English calques and typical Indonesian translationese

**B5.1 "di mana" or "dimana" as a connector**
- Tell: "Data diambil dari MIT-BIH, di mana setiap rekaman berdurasi 30~menit."
- Why: imitates *where*, *in which*. Appears most often in text edited by models (HI).
- Fix: "Data diambil dari MIT-BIH. Setiap rekamannya berdurasi 30~menit."
- Source: BS; NI AI-14, EJ-01; HI A3, rules.
- Machine: yes. `(?i)\bdimana\b` · `(?<=\w)[,]?\s+di mana\s+(?!pun\b|saja\b)(?!.{0,80}\?)(?=[a-z])` (NI AI-14 regex).

**B5.2 "yang mana"**
- Tell: "Filter dipasang sebelum CNN, yang mana hal ini mengurangi \textit{noise}."
- Why: imitates *which*.
- Fix: "Filter dipasang sebelum CNN untuk mengurangi \textit{noise}."
- Source: BS; NI AI-13; HI A3.
- Machine: yes. `(?i)\byang mana\b`.

**B5.3 Calque verb phrases**
- Tell: "Kuantisasi memainkan peran penting dalam memperkecil model. Pengujian mengambil
  tempat di laboratorium."
- Why: literal translation of *play a role*, *take place*, *it is important to*.
- Fix: "Kuantisasi berperan memperkecil model. Pengujian berlangsung di
  laboratorium."
- Source: NI AI-05, AI-06, AI-08, calque nominalization; HI 5b.
- Machine: yes. `(?i)\bmemainkan perana?n?\b` · `(?i)\bmengambil tempat\b` · `(?i)\badalah penting untuk\b|\bitu adalah mungkin\b` · `(?i)\bmembuat keputusan\b` (weak) · `(?i)\bmemberikan kontribusi\b`.

**B5.4 Calque fillers**
- Tell: "Dalam hal ini, model dilatih dengan data DS1. Dalam konteks ini, ..."
- Why: from *in this case*, *in terms of*. Usually deletable.
- Fix: "Model dilatih dengan data DS1."
- Source: NI filler "dalam hal ini"; BS calques (*dalam hal*, *berbicara tentang*, *pada
  akhir hari*, *membuat masuk akal*).
- Machine: yes. `(?i)\bdalam (hal|kasus|konteks) ini\b` · `(?i)\bberbicara (tentang|soal)\b` · `(?i)\bpada akhir hari\b` · `(?i)\bmembuat masuk akal\b`.

**B5.5 Participial clause at the start of a sentence (dangling)**
- Tell: "Menggunakan kuantisasi INT8, ukuran model berkurang menjadi 48~kB."
- Why: a calque of *Using X, ...*. The subject of the main clause (ukuran model) is not
  the agent of "menggunakan".
- Fix: "Kuantisasi INT8 memperkecil model menjadi 48~kB."
- Source: HI 5b (*Living in Bogor, I ...*).
- Machine: partly. `(?:^|(?<=[.!?])\s+)(Menggunakan|Memanfaatkan|Dengan menggunakan|Mempertimbangkan|Mengingat)\s[^,]{3,60},` then review the main-clause subject.

**B5.6 Document or study as the agent**
- Tell: "Tulisan ini membahas ..." or "Paper ini mengusulkan ..."
- Why: HI considers it a calque of *This paper discusses*. NI `pertahankan.md` on the
  contrary declares "Penelitian ini bertujuan ..." a standard Indonesian pattern.
- Fix: keep "Penelitian ini" as the subject of an objective or finding (NI).
  "Tulisan ini membahas" in the chapter body is handled by B3.1.
- Source: HI 5b; NI `pertahankan.md` (contradiction between sources, needs a user
  decision).
- Machine: partly (see B3.1).

**B5.7 Technical terms translated literally, non-living derived words**
- Tell: "Dilakukan sapuan parameter pada ukuran jendela." (*parameter sweep*,
  *window*).
- Why: word-by-word translation that is not used in the field.
- Fix per house rules: "Ukuran \textit{window} divariasikan dalam ablasi."
- Source: HI 5b; NI `istilah.md` (an equivalent is rejected if field readers do not
  use it).
- Machine: partly. The house list of banned translations (penyangga, purwarupa, pustaka
  for *library*, papan for *board*, penanda waktu) is already checked by `cek_tabel.py`
  N-ISTILAH. New literal translations need judgment.

**B5.8 Wrong collocations and subtle figurative language**
- Tell: "Model ini bekerja paling baik dan paling kokoh, dan selisih akurasinya
  menyempit."
- Why: calques of *performs best*, *most robust*, *the gap narrows*.
- Fix: "Model ini mencapai F1 tertinggi, dan selisih akurasinya menurun dari
  0,03 menjadi 0,01."
- Source: HI 5b.
- Machine: no.

**B5.9 Indonesian affixes on foreign words**
- Tell: "Model di-deploy ke ESP32-S3 setelah meng-compile firmware."
- Why: NI prescribes a hyphen for affixes on foreign words and italics for the foreign
  word. HI flags English verbs forced to take the *me-* affix.
- Fix: "Model dipasang ke ESP32-S3 setelah \textit{firmware} dikompilasi." or
  "di-\textit{deploy}" if the foreign term is kept.
- Source: NI `istilah.md`; HI 5b.
- Machine: yes. `(?i)\b(di|me|meng|ter)-?(deploy|upload|download|compile|flash|install|train|update|reset|setting)\b` without `\textit`.

**B5.10 Calque connectors and comparison rules**
- Tell: "Akurasi CNN lebih baik dari LSTM, dan perbedaan antara INT8 dengan float32
  kecil."
- Why: standard rules for connectors are often violated by translations.
- Fix: "Akurasi CNN lebih baik daripada LSTM, dan perbedaan antara INT8 dan
  \textit{float32} kecil."
- Source: NI KE-11, KE-12, KE-13, KE-17.
- Machine: yes. `(?i)\blebih\s+(?!dari\b)\w+\s+dari\b(?!\s+(pada|sekadar)\b)` · `(?i)\bantara\s+(?!lain\b)[^.,;]{1,40}?\sdengan\b` · `(?i)\bbaik\s[^.,;]{1,40}?\sataupun\b` · `(?i)\bbukan\s(?!hanya\b|saja\b|sekadar\b)[^.;]{1,60}?,\s*tetapi\b`.

### B6. References, numbers, and punctuation

**B6.1 Fictitious references or references from memory**
- Tell: a `.bib` entry with a DOI that points to another article, a book without pages,
  a real author with a title that does not exist.
- Why: the worst failure of AI-assisted writing. WP gives the example of an IEEE DOI
  that points to an unrelated article.
- Fix: references only from sources the user provided or that were opened and
  verified. Gaps are marked with the house marker, not filled with guesses.
- Source: BS `bahasa-peneliti`, `struktur-sitasi`; NI KONTRAK article 3; WP citations.
- Machine: partly. A `\cite` key that is not in the `.bib` (BibTeX warning), an `@book`
  entry without `pages`, a DOI that does not resolve. The truth of the reference content
  remains a manual check.

**B6.2 Numbers, citations, and cross references change during editing**
- Tell: after tidying, "0,9712" becomes "sekitar 97 %", one `\cite` disappears because
  the sentence was merged.
- Why: the model summarizes until the meaning shifts. HI names the cross-reference
  check as the one that most often saves technical documents.
- Fix: the set of numbers, `\cite`, `\ref`, `\label` before and after must be equal.
- Source: NI KONTRAK article 4, `periksa.py --banding`; HI principle 2, the eleven
  checks; NP rule 12.
- Machine: yes (set comparison, normalize `{,}` to `,` first).

**B6.3 Decimal point and units**
- Tell: "Arus rata-rata 0.18A pada tegangan 3.3 Volt."
- Why: house rule and EYD V.
- Fix: "Arus rata-rata 0,18~A pada tegangan 3,3~V."
- Source: NI EJ-07, EJ-08, EJ-09; BS `kalimat-akademik` §7.
- Machine: yes. `\b\d+\.\d{1,4}\b` in prose (exclude software versions, subsection
  numbers, `\ref`) · `(?<![\d.,])\d+(?:[.,]\d+)?(V|mV|mA|kW|Hz|kHz|MHz|kB|MB|ms)\b` · `\d\s?(Volt|Ampere|Watt|Hertz|Celcius)\b`.

**B6.4 Em dash, en dash, curly quotes**
- Tell: "Sistem ini cepat — dan hemat daya." or `---` in a LaTeX paragraph, or curly
  quotes “...” in the `.tex` source.
- Why: the em dash as a stylistic punctuation mark is a long-standing strong marker
  (WP: 2022 to Sep 2026). House rules ban it in paragraphs.
- Fix: a conjunction ("yang", "sehingga", "karena") or a comma.
- Source: BS L10; HI principle 4; HU §8, §21; SS; WP historical em dash.
- Machine: yes. `—|–` · `(?<!-)---(?!-)` in a paragraph · `[“”‘’]` in `.tex` files.

**B6.5 Gap claims without a literature check**
- Tell: "Belum ada penelitian yang menerapkan TinyML untuk klasifikasi aritmia."
- Why: an absolute negative claim that is almost certainly wrong.
- Fix: "Penelitian sebelumnya~\cite{a,b} belum mengukur kinerja pada sinyal tubuh
  dari sensor AD8232."
- Source: NI `bagian-naskah`.
- Machine: yes for flagging. `(?i)\bbelum (ada|pernah ada) (penelitian|studi)\b`.

---

## C. List of Indonesian phrases and words (combined, without duplicates)

Source tags: BS, NI, HI. Words that BS derived as calques of English lists are marked
"BS-k" (equivalents of *delve*, *landscape*, and so on from WP/HU). The column "Genre
note" is an inference by the catalog author for an engineering PA book.

### C1. Openers and emphasis

| Phrase | Source | Genre note |
|---|---|---|
| di era digital (yang serba cepat) ini, di era globalisasi, di era modern | BS, NI, HI | |
| di zaman (modern seperti) sekarang ini | BS | |
| seiring (dengan) perkembangan teknologi / zaman, seiring berjalannya waktu | BS, NI, HI | |
| di tengah pesatnya kemajuan teknologi, di tengah derasnya | NI, HI | |
| dewasa ini, belakangan ini (without data) | BS, `bahasa-peneliti` | |
| tidak dapat dipungkiri (bahwa), tak bisa dimungkiri | BS, NI, HI | |
| seperti yang kita ketahui (bersama), sebagaimana kita ketahui bersama | BS, NI, HI | |
| sudah menjadi rahasia umum | NI | |
| dalam dunia X yang terus berkembang, dalam dunia yang serba cepat | BS, HI | |
| dalam beberapa tahun terakhir X mengalami pertumbuhan signifikan | BS | needs a number and a reference |
| pernahkah Anda ..., tahukah Anda ..., siapa yang tidak mengenal ... | BS | |
| mari kita (menyelami / telusuri / bahas / lihat / mulai) | BS, NI, HI | |
| sebelum membahas lebih lanjut, mari kita pahami dulu apa itu X | BS | |
| artikel/bab/subbab/tulisan ini akan membahas | BS, NP | |
| berikut adalah beberapa hal yang perlu diketahui | BS | |
| X memainkan peran yang sangat penting dalam ... | BS, NI | |
| pendidikan/teknologi merupakan hal yang sangat penting | BS `bahasa-peneliti` | |

### C2. Transitions and fillers

| Phrase | Source | Genre note |
|---|---|---|
| selain itu, tidak hanya itu, terlebih lagi, lebih lanjut | BS, NI, HI | legitimate now and then, NP rule 8 rotates "Selain itu" |
| tak kalah penting, yang tidak kalah menarik | BS | |
| namun demikian | BS, NI (G), HI | replace with "Namun," |
| oleh karena itu, oleh sebab itu, dengan demikian | BS, NI, HI | standard, acted on when repeated |
| secara keseluruhan, pada akhirnya | BS, NI, HI | |
| di sisi lain (without a real contrast) | BS, HI | |
| sementara itu, adapun, selanjutnya | BS, NI (Adapun) | |
| dalam hal ini, dalam kasus ini, dalam konteks ini | BS, NI | |
| penting untuk dicatat/dipahami/diketahui bahwa, patut dicatat, perlu diingat bahwa, perlu diketahui bahwa | BS, NI, HI | |
| seperti yang telah disebutkan sebelumnya | BS | |
| dengan kata lain | BS, NI | |
| hal ini, hal tersebut (repeated) | NI | |
| konsekuensinya | HI | |
| senada dengan itu, sejalan dengan itu | HI | |
| pertanyaannya sederhana, gagasannya sederhana, hasilnya tegas, prosedurnya begini, cara membacanya begini, perhatikan bahwa, tiga hal langsung terlihat, di situlah ... yang sebenarnya | HI | |

### C3. Closers

| Phrase | Source | Genre note |
|---|---|---|
| sebagai kesimpulan, kesimpulannya, sebagai penutup | BS, HI | the title "Kesimpulan" of Chapter 5 remains legitimate |
| dengan demikian (dapat) disimpulkan bahwa | NI, HI | |
| demikianlah ..., nah, itulah tadi pembahasan ... | BS, `bahasa-peneliti` | |
| semoga (artikel ini) bermanfaat, semoga membantu | BS, HI | |
| jangan ragu untuk ... | BS, HI | |
| dengan memahami hal-hal di atas | BS | |
| masa depan X terlihat (sangat) menjanjikan | BS | |
| meski memiliki banyak tantangan, X tetap menjadi ...; dengan segala kelebihan dan kekurangannya | BS | |
| hal ini membuktikan bahwa (at the end of a paragraph) | NI | |
| perlu (dilakukan) penelitian lebih lanjut (without direction) | BS, NI | |

### C4. Intensifiers, claims, and umbrella words

| Phrase | Source | Genre note |
|---|---|---|
| memegang peranan (yang sangat) penting / krusial / vital / sentral | BS, NI, HI | |
| berperan vital, aspek vital, sangat krusial, semakin krusial | BS, HI | |
| menjadi kunci utama, menjadi faktor kunci | HI | |
| tak lepas dari, tidak dapat dipisahkan dari (kehidupan) | BS, HI | |
| patut diperhatikan, menjadi sorotan | HI | |
| sangat signifikan, signifikan (without a test) | BS, NI, HI | |
| solusi (yang) inovatif / revolusioner / terbaik / tepat / lengkap / jitu | BS, NI | |
| sangat efektif dan efisien; efektif, efisien, dan inovatif; cepat, tepat, dan akurat; aman, nyaman, dan andal | BS, NI, HI | triplet |
| luar biasa, mencengangkan, mengejutkan, sayangnya | BS | |
| pasti, selalu, tidak pernah, tanpa cacat, tidak diragukan lagi, semua orang | BS, HI | |
| para ahli menilai, sejumlah penelitian menunjukkan, banyak peneliti sepakat, berbagai studi menunjukkan, menurut berbagai sumber, banyak orang percaya, beberapa ahli berpendapat | BS, HI | |
| dapat dikatakan bahwa, cenderung, pada umumnya, relatif (stacked) | BS | a single hedge is legitimate (NI) |
| mungkin dapat (cenderung / berpotensi), diduga kemungkinan dapat | BS, NI, HI | |
| berbagai aspek, faktor-faktor tertentu, dimensi kehidupan, peran strategis | NI | |
| berbagai macam, segudang, sederet | BS, NI | |

### C5. Slop and prestige vocabulary

| Word | Source | Genre note |
|---|---|---|
| hiruk pikuk | BS (the only one validated by speakers) | |
| lanskap (figurative) | BS-k | |
| ranah ("dalam ranah X") | BS | |
| krusial | BS-k, HI | |
| menyelami, menggali lebih dalam, mengupas (tuntas) | BS-k, HI | *mengupas* has a journalistic tone (HI) |
| menggarisbawahi, menyoroti (figurative) | BS-k | |
| memanfaatkan, mendayagunakan, mengoptimalkan (figurative) | BS, HI | *mengoptimalkan* is legitimate if there is an optimization |
| mengimplementasikan, merealisasikan, mengakomodasi | HI | common in engineering, judge case by case |
| memupuk, menumbuhkan (figurative) | BS | |
| tangguh, kokoh (for software) | BS, HI (*paling kokoh*) | technical *robust* is allowed, write \textit{robust} when it is a term |
| mulus, tanpa hambatan, terintegrasi dengan mulus | BS | |
| menavigasi, mengarungi (figurative) | BS-k | |
| memberdayakan, merampingkan (figurative) | BS-k | |
| transformatif, mutakhir, tercanggih | BS | |
| holistik, sinergi, paradigma | BS, HI (holistik) | |
| komprehensif, esensial, fundamental, masif | HI | |
| semarak, dinamis (community) | BS-k | |
| yang terus berkembang | BS-k | |
| bersemayam, terletak indah | BS-k | |
| memulai perjalanan | BS-k | |
| beresonansi, menggema (figurative) | BS-k | |
| jalinan, permadani (figurative) | BS-k | |
| garda terdepan, mercusuar (hope) | BS | |
| membuka (memaksimalkan) potensi | BS-k | |
| bukti nyata (commitment) | BS-k | |
| game changer, pengubah permainan, revolusioner, terobosan baru | BS | |

### C6. Promotional phrases (BS §4, relevant if they appear in Chapter 1 or the Abstract)

kini hadir / telah hadir (sebagai solusi), tak perlu pusing / khawatir lagi, bawa X ke
level berikutnya, dirancang khusus untuk memenuhi kebutuhan, hasil (yang) maksimal /
optimal, meningkatkan efisiensi dan produktivitas (without numbers), pilihan tepat / cerdas,
pengalaman yang tak terlupakan, siap menemani, mempermudah hidup Anda, langkah awal
menuju kesuksesan. All BS.

### C7. Calques and connectors

| Phrase | Source |
|---|---|
| di mana / dimana (connector), yang mana, dalam mana | BS, NI, HI |
| memainkan peran(an) | NI, HI |
| mengambil tempat | NI |
| adalah penting untuk, itu adalah mungkin untuk | NI |
| membuat keputusan | NI |
| memberikan kontribusi terhadap, memberikan pengaruh terhadap | NI, HI |
| melakukan analisis / pengukuran / perbandingan / pengujian terhadap, mengalami peningkatan / penurunan | BS, NI, HI |
| dalam hal (in terms of), berbicara tentang, pada akhir hari, membuat masuk akal, take-away / poin kunci | BS |
| ini bukan berarti, hal ini bukan berarti, X bukan berarti Y | HI |
| bukan hanya ... tetapi juga ..., bukan sekadar ... melainkan ..., lebih dari sekadar, X bukan lagi pilihan melainkan keharusan, bukan tentang X melainkan Y | BS, NI, HI |
| mulai dari X hingga Y (pseudo-range) | HI |
| tabel di bawah ini, grafik di atas | HI |
| dikarenakan, berdasarkan pada, antara A dengan B, baik A ataupun B, lebih baik dari, daripada itu, sedangkan / sehingga (sentence opener) | NI, HI |
| teknologi pemungkin, sapuan parameter, armada pembangkit, paling kokoh, bekerja paling baik, selisihnya menyempit | HI |

### C8. Machine residue

Tentu, berikut ...; Semoga membantu; Jangan ragu untuk ...; `contentReference`,
`oaicite`, `[cite: 1]`, `【】`, `turn0search` (BS, HI). Fill-in placeholders that were
forgotten and not replaced (WP).

---

## D. Conflicts with house rules and excluded items

### D1. Direct conflicts with house rules

| # | Source rule | Source | House rule | Proposed decision |
|---|---|---|---|---|
| 1 | Replace the em dash with a comma, colon, or parentheses; lists "preceded by a colon, not hung on adalah" | HI principle 4, 5b technique 1; HU §8; SS; BS spelling (colon after a complete statement) | No colon in paragraphs | The only replacements in the house skill are conjunctions ("yaitu", "meliputi", "berupa"), a comma, parentheses, or a new sentence |
| 2 | Fix examples use a colon ("... penanda keanggotaan marga: hanya warga ...") | NI AI-10, BS examples | Same | Examples are not copied, they are rewritten |
| 3 | The em dash is allowed for ranges (2020—2025) in non-formal registers | BS L10, `ejaan-eyd` | No em dash in paragraphs | Ranges are written with "sampai" or "hingga" |
| 4 | Use the COMMON equivalent in all registers (unduh, berkas, perangkat keras, tautan, pembaruan, umpan balik) | BS `padanan-istilah` | Technical terms stay English and italic, not translated | The BS equivalents list is not used. Only "do not use stiff equivalents" still applies |
| 5 | Indonesian equivalent first, foreign term in parentheses at first occurrence ("beban kognitif (*cognitive load*)"); HI "give the equivalent in parentheses per chapter" | BS `bahasa-peneliti` no. 7; HI foreign-term rules | English italic is primary, a translation is allowed once in parentheses | The direction is reversed, the English term outside the parentheses |
| 6 | Foreign terms italic every time they appear | NI, HI | Certain adopted words upright (bufer, `preprocessing`, `single-lead`, `flowchart`) | The house exception list wins |
| 7 | "kami" is legitimate for a team; *penulis* or *peneliti* when the agent needs to be named | HI pronoun rules; NI; BS | The author is a single student, no "kami" | "kami" is banned. The use of "penulis" has not been decided by the house, ask the user |
| 8 | Numbers of one or two words written in letters (3 kali becomes tiga kali), regarded as not a change of value | NI contract 3 | Numbers never change | Do not change the form of numbers when editing, or ask the user for permission, because it breaks the number comparison check |
| 9 | "mulai dari X hingga Y" flagged as a pseudo-range | HI D12 | `laporan/CLAUDE.md` recommends "mulai dari ... hingga ..." as a replacement for the colon | Allowed only for real numeric or scaled ranges, otherwise use "yaitu" or "meliputi" |
| 10 | Headings use sentence case, Title Case is an AI marker | BS L10; HU §20; WP style | Chapter/subsection headings in buku-pa use Title Case (template convention) | The Title Case rule is excluded |
| 11 | Gap markers `[RUJUKAN DIPERLUKAN: ...]` or `[PERLU DATA: ...]` / `[PERLU RUJUKAN: ...]` | BS; NI | `\PlaceholderData{...}`, `PLACEHOLDER-DATA`, `PLACEHOLDER-GAMBAR` | Use the house markers |
| 12 | Default APA citation style (Name, year) and the example "Menurut Nama (tahun)" | BS; NI; HI D9 | Numbered `~\cite{}` | Formulaic citation patterns are adapted to the numbered form |
| 13 | Certain transitions at most once per text | BS L6 | Not a house rule, but NP rule 8 rotates "Selain itu" and "Dengan demikian" | NP wins, the density thresholds from HI or NI are used as a check |
| 14 | Wikipedia: the newest models that avoid all alternative punctuation (only commas and periods) are now a new marker | WP (`{{cn}}`, not yet sourced) | No colon, semicolon, em dash | The house rule stays. Inference: variation in sentence structure (subordinate clauses, parentheses, conjunctions) must be maintained so that the punctuation ban does not produce a flat comma-period rhythm |
| 15 | Abstract of 150 to 250 words, five elements, no citations | BS; NI | The abstract structure is governed by the `struktur-pa` skill | Not part of the new skill, refer to `struktur-pa` |

### D2. Items not suited to a technical PA book (excluded)

- **SS:** "kill all adverbs", "two items beat three", "use *you*", "put the reader in the
  room", "every sentence needs a human subject", "no passive constructions", the ban on
  *Wh-* openers, the 35/50 score. Essay or blog style and in conflict with the
  legitimate passive in Methods and the ban on "kami".
- **BS obligation 4** "active sentences as the default". Without "kami", the passive and
  inanimate subjects are the main tool. NI and HI F1 protect the passive in Methods and
  Results.
- **HI "Avoiding sterility"** (opinion, first person, slightly untidy) and the personal
  voice preset. HI itself states that neutral technical text is a correct human voice.
- **HI GPTZero calibration and the `metrik.py` thresholds** tuned to the corpus of one
  writer. The goal of the house skill is readability, not passing detectors (NI and HI
  both reject that goal).
- **BS marketing, website/UX, SEO modules** entirely, including `frasa-terlarang` §4
  except as a list of promotional phrases that must be zero.
- **HU §26** (answering a reader who already knows the context, for message replies),
  §10 (hyphen in English compound words).
- **WP** wiki-specific parts (edit summary, AfC, wikitext markup, utm_source,
  maintenance templates, secondary sources and notability).
- **NI network tools** (`openalex.py`, MCP Consensus and alphaXiv). In conflict with the
  house habit of not sending data to outside services unless asked. The term-usage data
  in `istilah.md` may still be quoted as material.
- **HI "bila" replaced by "jika"** and **"capability claims get *dapat*"**. HI author
  preferences, not rules. No need to adopt.

---

## E. Gaps (not covered by any source for this genre)

All items below are inferences by the catalog author from comparing the contents of the
sources with the needs of the PA book.

1. **LaTeX.** No source handles `.tex` source text. A checker must know how to strip
   `\cite`, `\ref`, `\label`, `%`, float environments, equations, and `\textit{}`
   before matching regexes, and recognize `~` as a non-breaking space and `{,}` in math
   mode as a decimal comma. HI only touches on `0{,}5` and the count of
   `\begin{equation}`.
2. **Register per engineering chapter.** The sources discuss journal IMRaD, not the
   structure of a PENS PA book (Chapter 2 Supporting Theory and Related Work, Chapter 3
   design, Chapter 4 results and analysis). The distinction of Chapter 3 written as
   design and Chapter 4 written as achievement, and "belum diukur" for what has no data
   yet, exists only in the house skills (`narasi-pa` rule 11, `struktur-pa`).
3. **Explanatory paragraphs for tables and figures.** The sources only say "do not
   repeat the whole table" and "refer by number". The Finding, Evidence, Meaning
   pattern, the five-number limit, and the requirement that numbers carry a comparison
   exist only in `narasi-pa`.
4. **Electrical engineering and *embedded* language.** There is no list of tells typical
   of hardware descriptions (for example "otak dari sistem", "jantung dari rangkaian",
   "menjembatani", "mengorkestrasi", "secara *seamless*", "*real-time* yang andal"
   without a latency number, "hemat daya" without mA). This is a candidate for a new
   list, to be collected from real drafts.
5. **Performance claims without test conditions.** The sources act on "signifikan" and
   "membuktikan", but do not require the test conditions to be attached to the claim
   (*replay* signal source versus body signal, number of repeats, test data). Exists
   only in `narasi-pa` rule 4.
6. **Use of English terms in Indonesian reports.** All sources lean toward Indonesian
   equivalents or toward "measure usage". None discusses the "English italic as the
   default" policy and its typical errors (inconsistent italics, the same term
   sometimes upright, affixes on italic words, plural "*sensor-sensor*", capitalization
   of terms at the start of a sentence).
7. **Repo internal labels leaking into printed text** (file paths, script names, "Fase
   n", `PA_*` env names, PCB revisions). Not in the sources. A machine can check this
   with the regex `\bFase\s+[A-G0-9]\b|\bHW-\d|\bPA_[A-Z_]+|\.py\b|\.cpp\b|/` in prose.
8. **Uncertainty markers typical of measurement** (instrument accuracy, small sample
   size, a single subject). The sources discuss general hedging, not how to write
   hardware measurement limitations honestly without sounding defensive.
9. **Cross-chapter consistency in a long book.** NI and HI suggest a term list up front,
   but there is no mechanism for abbreviations redefined per chapter, `Tabel~\ref`
   numbers spoken in words, or terms that change between Chapter 3 and Chapter 4.
   `narasi-pa` rule 9 only says to `grep`.
10. **Float lead-in sentences and *captions*.** No source discusses *captions* that sound
    like AI sentences ("Gambar ini menunjukkan ...") or figure lead-in paragraphs that
    only announce the figure.
11. **Validation of Indonesian tells.** There is no corpus study of excess vocabulary
    for Indonesian (BS admits it). HI thresholds are calibrated to one writer and
    GPTZero, NI gives no density threshold other than a count of 2 or 3. Thresholds for
    the house skill must be measured from buku-pa itself (for example run the checker
    on a draft the user has already approved as a baseline) before being made hard
    limits.
12. **Evals.** Only NI has `evals/cases.json`. For house rule no. 8 (eval 10/10), test
    cases must be built from real buku-pa sentences with definite answers (for example
    the KE-01 regex, di mana, numbers changed), not from the source examples.
