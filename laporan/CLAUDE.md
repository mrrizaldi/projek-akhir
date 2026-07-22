# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

All commands run from inside the project folder (`proposal-pa/` or `buku-kp/`):

```bash
cd proposal-pa   # or: cd buku-kp

make pdf         # compile (paper size fixed per project: proposal-pa A4, buku-kp A5)
make rebuild     # clean + recompile from scratch
make view        # compile then open PDF
make docx        # convert to DOCX via pandoc
make clean       # delete output/ folder
make check       # verify pdflatex, bibtex, pandoc are available
```

Build runs a full cycle: `pdflatex -> bibtex -> pdflatex -> pdflatex` to resolve bibliography and cross-references. Output goes to `output/` inside each project folder.

## Architecture

This is a LaTeX monorepo for academic documents at PENS (Politeknik Elektronika Negeri Surabaya), D4 Teknik Informatika.

```
texdocs/
├── shared/
│   ├── preamble.tex      <- common preamble (size-independent): packages + formatting
│   ├── size-a4.tex       <- A4 knobs: geometry, \setstretch, heading font macros
│   ├── size-a5.tex       <- A5 knobs: geometry, \setstretch, heading font macros
│   └── Makefile.inc      <- build targets shared by all projects
├── proposal-pa/          <- Proposal Proyek Akhir (A4)
│   ├── main.tex          <- entry point: documentclass + \input size-a4 + preamble
│   ├── Makefile          <- include ../shared/Makefile.inc
│   ├── referensi.bib     <- BibTeX bibliography
│   └── bab/              <- halaman-judul, bab1, bab2, bab3, abstrak, etc.
├── buku-kp/              <- Laporan Kerja Praktik (A5)
│   ├── main.tex          <- standalone preamble (does not use shared/preamble.tex)
│   ├── Makefile          <- include ../shared/Makefile.inc
│   └── images/
└── buku-pa/              <- Buku Proyek Akhir (placeholder, no content yet)
```

### Paper Size Mechanism

Paper size is **fixed per project** — no compile-time switch. Each project picks one
size in `main.tex`. There is no `make a4`/`make a5` and no `_papersize.tex`.

For projects using the shared preamble (proposal-pa, buku-pa), `main.tex` does:

```latex
\documentclass[12pt,a4paper,fleqn]{report}
\input{../shared/size-a4}   % or size-a5 — geometry, spacing, heading font macros
\input{../shared/preamble}  % common formatting (size-independent)
```

- `size-a4.tex` / `size-a5.tex` are the **reusable per-size configs**: each loads
  `geometry`, sets `\setstretch`, and defines the font macros consumed by `preamble.tex`:
  `\FontChapterHead`, `\FontSectionHead`, `\FontKutipan`.
- To change a project's size: swap both the `\documentclass` options and the `size-aX`
  input. Keep the two consistent.
- `buku-kp` is a separate standalone template (A5 hardcoded in its own `main.tex`); it
  does not use the shared preamble or size files.

### Shared vs Standalone Preamble

- `proposal-pa/main.tex` delegates formatting to `shared/preamble.tex` (common) plus a
  `shared/size-aX.tex` (size-specific), input in that order.
- `buku-kp/main.tex` has its own self-contained preamble (does not use `shared/preamble.tex`).
- `shared/preamble.tex` requires a `size-aX.tex` to be `\input`-ed first (it provides the
  `\FontChapterHead` / `\FontSectionHead` / `\FontKutipan` macros, geometry, and spacing).

### PENS Formatting Conventions (shared/preamble.tex + size-aX.tex)

- Font: Times New Roman via `mathptmx`
- A4 (`size-a4.tex`): 12pt, 1.5 line spacing, margins 3/3/4/3 cm (top/bottom/left/right)
- A5 (`size-a5.tex`): 10-11pt, 1.2 line spacing, margins 2.5/2.5/3.0/2.0 cm
- Paragraph indent: 0.5 in, no extra paragraph spacing
- Chapter heading: centered, bold, uppercase, "BAB N\nJUDUL"
- Section: left-aligned, uppercase, bold, number in 0.5in box
- Page numbering: arabic, bottom-center (via `mainmatter` pagestyle)
- Captions: bold, centered, period separator (`Gambar X.Y.` / `Tabel X.Y.`)
- Equation tags: bold, format `(Persamaan X.Y)`, numbered per chapter
- Bibliography: IEEE style via `natbib` + `IEEEtran.bst`
- Custom environment `kutipan` for long block quotes (indented 10mm each side)

### Adding a New Project

```bash
mkdir buku-pa
echo 'include ../shared/Makefile.inc' > buku-pa/Makefile
# Use proposal-pa/main.tex as template.
# For A5: \documentclass[10pt,a5paper,fleqn]{report} + \input{../shared/size-a5}
# For A4: \documentclass[12pt,a4paper,fleqn]{report} + \input{../shared/size-a4}
```

### Student/Document Data

Edit `\newcommand` declarations at the top of `main.tex` in each project:
`\JudulPA`, `\NamaMahasiswa`, `\NRP`, `\PembimbingSatu`, `\NIPSatu`, `\PembimbingDua`, `\NIPDua`, `\Tahun`

### Gaya Penulisan Paragraf

Aturan penulisan paragraf akademik untuk proposal dan buku:

- **Jangan pakai titik dua (`:`)** di dalam paragraf untuk memperkenalkan daftar. Gunakan konjungsi seperti "yaitu", "meliputi", "berupa", atau "mulai dari ... hingga ..."
- **Jangan pakai titik koma (`;`)** di dalam paragraf. Gunakan koma + konjungsi ("dan", "serta") atau pecah menjadi kalimat terpisah
- **Jangan pakai em dash (`—`)** di dalam paragraf. Gunakan konjungsi yang sesuai ("yang", "sehingga", "karena") atau koma
- **Jangan pakai numbering inline** seperti `(1)`, `(2)`, `(3)` di dalam paragraf. Sebut secara naratif dengan koma dan konjungsi, atau gunakan environment `enumerate` jika butuh daftar bernomor
- Pengecualian: titik koma dalam tabel (sel pendek) dan label heading terstruktur (misal "Tahap 1") diperbolehkan

### Istilah Asing & Penulisan Teknis

- **Istilah teknis yang sudah lazim ditulis biasa (TANPA italic, TANPA diterjemahkan).** Perlakukan sebagai kosakata yang sudah diadopsi, bukan bahasa asing. Daftar yang sudah disepakati:
  - `preprocessing` (BUKAN "pra-pemrosesan", BUKAN `\textit{preprocessing}`)
  - `single-lead` (BUKAN "sadapan tunggal", BUKAN `\textit{single-lead}`)
  - `flowchart` (BUKAN "diagram alir", BUKAN `\textit{flowchart}`)
  - `bufer` (BUKAN "penyangga", BUKAN `\textit{buffer}`) — sudah masuk KBBI
- **Jangan terjemahkan istilah teknis ke Bahasa Indonesia.** Tulis dalam Bahasa Inggris aslinya dan miringkan (`\textit{}` / `\emph{}`). Contoh: tulis `\emph{prototype}` (BUKAN "purwarupa"), `\emph{half-open}` (BUKAN "setengah-terbuka"), `\emph{reconnect}` (BUKAN "penyambungan ulang"), `\emph{buffer}` (BUKAN "penyangga"), `\emph{timestamp}` (BUKAN "penanda waktu"). Terjemahan Indonesia boleh muncul sekali sebagai penjelasan awal di dalam tanda kurung, lalu selanjutnya pakai istilah Inggris italic.
- Istilah asing lain yang belum lazim tetap di-`\textit{}` seperti biasa (`\textit{edge computing}`, `\textit{real-time}`, `\textit{cloud}`, `\textit{baseline wander}`, dll). Default tetap italic; hanya istilah pada daftar di atas (dan yang user tetapkan kemudian) yang ditulis biasa.
- **Jangan pakai `\texttt{}` (font monospace).** Tulis nama field, nilai, dan variabel dengan teks biasa. Contoh: tulis `signal\_quality` (BUKAN `\texttt{signal\_quality}`), tulis `label = 1` (BUKAN `\texttt{label = 1}`).
- **Konten dari spec/brief eksternal tetap harus melalui aturan penulisan di CLAUDE.md.** Jangan langsung tempel mentah; cek dulu: tidak ada titik koma/em dash/titik dua di paragraf, istilah teknis italic bukan diterjemahkan, desimal pakai koma, sitasi pakai `~\cite`.
- Saat menambah istilah baru ke daftar "tulis biasa", terapkan ke SEMUA bab (`bab1`–`bab3`, termasuk sel tabel), bukan hanya tempat user menunjuk.
- **Desimal pakai koma**, bukan titik (`98,2\%`, `0,5--40 Hz`), sesuai kaidah Bahasa Indonesia.
- **Sitasi pakai `~\cite{...}`** (non-breaking space sebelum cite) agar nomor tidak terpisah dari kata di akhir baris.
- **Jangan buat entri `.bib` baru sendiri** kalau detail sitasi belum lengkap — laporkan cite key yang hilang ke user. Kalau key di `.bib` namanya beda dari yang diminta, sesuaikan `\cite{...}` agar match, jangan ubah `.bib`.

### Konvensi Heading (subsubsection)

- `secnumdepth` diset ke `3` agar `\subsubsection` ikut bernomor (default `report` hanya sampai `subsection`).
- Format `\subsubsection` (di `shared/preamble.tex`): **huruf `a. b. c.`** (`\alph`), **tidak bold**, reset tiap subsection, rata kiri tanpa indent. Berfungsi sebagai numbering daftar, bukan heading tebal yang setara subsection.
- Pakai `\subsubsection` (tanpa `*`) supaya bernomor. `\subsubsection*` hilang nomornya — hindari kecuali memang sengaja tanpa nomor.

### Konvensi Tabel & Gambar

Tabel:
- Tabel panjang multi-halaman pakai `longtable` dengan header yang diulang (`\endfirsthead` + `\endhead`).
- **Tanpa teks "Bersambung ke halaman berikutnya" / "Lanjutan Tabel X.Y"** di footer/header lanjutan — user tidak suka. Cukup `\hline` di `\endfoot`.
- Tabel perbandingan padat (banyak kolom) pakai `\scriptsize` + `\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}` untuk kolom rata-kiri yang membungkus. `\newcolumntype{L}` sudah didefinisikan di `shared/preamble.tex`.
- **Jangan `\clearpage` sebelum tabel** — biarkan `longtable` mengalir mengisi ruang kosong di halaman berjalan.
- **Pakai `\begin{table}[!ht]`, bukan `[H]`**, untuk tabel float satu halaman. `[H]` (paket `float`) mengunci tabel persis di titik deklarasi; kalau tidak muat di sisa halaman, seluruh blok tabel + teks sesudahnya terdorong ke halaman berikutnya dan meninggalkan whitespace besar. `[!ht]` membuat tabel mengambang (LaTeX menunda float) sehingga paragraf sesudahnya mengisi ruang kosong sementara tabel naik ke atas halaman. Tanda `!` melonggarkan batas fraksi float LaTeX yang sering jadi penyebab tabel lompat halaman lebih dini. Pakai `[H]` hanya kalau memang wajib tepat di posisi itu.
- Kalau ada kata panjang yang `Overfull` di sel sempit, sisipkan `\allowbreak` atau `\-` sebagai titik putus; jangan langsung perkecil font kalau cukup ditangani per-kata.
- **Jaga nama `\label` tetap** kalau dirujuk `\ref`/`\autoref` di bab lain — cek dulu sebelum mengganti label tabel.

Gambar:
- Diagram **landscape** (mis. arsitektur sistem): `\includegraphics[width=\linewidth,keepaspectratio]{...}`.
- **Flowchart vertikal** (tinggi & sempit): batasi **tinggi**, bukan lebar — `\includegraphics[height=0.6\textheight,keepaspectratio]{...}` — supaya tidak meluber satu halaman penuh.
- Sumber diagram sebaiknya di-export resolusi tinggi (≥300 DPI di ukuran cetak) atau format vektor (PDF/SVG). Hindari PNG resolusi rendah yang harus di-zoom.

### Struktur Resmi Proposal PA (Panduan D4TI)

Acuan: `proposal-pa/Panduan_Proposal_PA_D4TI/` (file A–E, format `.docx`). Setiap bab wajib mengikuti kerangka di bawah; cek ke sini sebelum menambah/menghapus section.

**Kerangka Problem.** Judul PA dipecah jadi tiga komponen yang dipakai konsisten lintas bab: *Problem* (apa yang dipecahkan), *Problem Domain* (bidang masalahnya), dan *Uniqueness/orisinalitas* (solusi unik yang ditawarkan).

**Halaman Judul** (urut, rata tengah): "PROPOSAL PROYEK AKHIR" + logo PENS → JUDUL (uppercase, tebal) → Nama Mahasiswa (tebal) → "NRP. ..." → "DOSEN PEMBIMBING" (tebal) → Pembimbing 1 (+ NIP) → Pembimbing 2 (+ NIP) → "PROGRAM STUDI SARJANA TERAPAN" lalu "TEKNIK INFORMATIKA" → "DEPARTEMEN TEKNIK INFORMATIKA DAN KOMPUTER" → "POLITEKNIK ELEKTRONIKA NEGERI SURABAYA" → Tahun. Cover biru `proposal-pa` adalah varian desain yang disengaja; isi & urutan elemen tetap mengikuti daftar ini.

**Bab 1 Pendahuluan** — `1.1 Latar Belakang` (uraikan Problem Domain + urgensi: tren naik, tingkat keparahan), `1.2 Permasalahan` (jabarkan Problem, gaya deskriptif, yakinkan urgensi), `1.3 Tujuan` (DIAWALI kalimat klaim orisinalitas: "Penelitian ... mengajukan pendekatan/algoritma/metode baru untuk mengatasi ... dengan ...", baru rinci fitur unik), `1.4 Manfaat` (kontribusi spesifik: siapa dapat manfaat apa, jangan mengada-ada), `1.5 Sistematika Penulisan` (ringkas isi Bab 1–5).

**Bab 2 Kajian Pustaka** — WAJIB ada paragraf pembuka setelah judul bab (utarakan Problem pada Problem Domain → arahkan ke teori penunjang → ulasan penelitian terkait untuk menguatkan orisinalitas). Lalu `2.1 Deskripsi Permasalahan`, `2.2 Teori Penunjang` (semua klaim/teori wajib bersitasi), `2.3 Penelitian Terkait` (riset lain dengan Problem sama tapi Uniqueness beda; rujuk pustaka tepercaya).

**Bab 3 Deskripsi Sistem** — paragraf pembuka (lingkup: model, rancangan, variabel, teknik pengumpulan data, analisis data), `3.1 Deskripsi Solusi` (argumentatif, fitur unik = orisinalitas), `3.2 Desain Sistem` (mulai dari diagram *high-level view*, baru rinci per komponen). Section variabel penelitian, teknik pengumpulan data, dan analisis data masuk sesuai lingkup paragraf pembuka.

**Aturan kutipan.** Kutipan langsung pendek (1–2 baris): petik ganda + italic + sitasi, mis. *"..."*`~\cite{x}`. Kutipan langsung panjang (>2 baris): environment `kutipan` (paragraf terpisah, 10pt, margin masuk 10mm kiri-kanan) + sitasi. Parafrase: sitasi di akhir kalimat.

**Gambar.** Rata tengah, sisakan 1 baris kosong atas-bawah. Caption (nomor + keterangan) di BAWAH gambar, tebal & rata tengah. Jika isi gambar kutipan: tulis "Sumber: ..." 10pt rata tengah DI ATAS caption.

**Persamaan.** Baris sendiri, masuk 10mm dari kiri (`fleqn`), 1 baris kosong atas-bawah. Nomor rata kanan tebal format "(Persamaan X.Y)". Wajib dirujuk & dibahas di paragraf.

**Tabel.** Rata tengah, 1 baris kosong atas-bawah. Caption (nomor + keterangan) di ATAS tabel, tebal & rata tengah (beda dari gambar yang di bawah). Baris header diberi latar agak gelap (`\rowcolor{headgray}`). Jika kutipan: "Sumber: ..." 10pt rata tengah di bawah tabel. Wajib dirujuk di paragraf. Panduan resmi: 1 tabel ≤ 1 halaman; proyek ini meng-override aturan ini untuk tabel perbandingan panjang dengan `longtable` (lihat Konvensi Tabel & Gambar).

**Daftar Pustaka.** Bernomor `[n]`, gaya IEEE (`IEEEtran.bst` via `natbib`). Urutan & format per jenis sumber: jurnal (pengarang, judul, nama jurnal, vol/no/hal, penerbit, tahun), seminar, buku (pengarang, judul, penerbit, edisi, tahun), tugas akhir/skripsi/disertasi, media publik, media online (judul, situs, alamat, tanggal akses, tahun).

### DOCX Notes

LaTeX -> DOCX via pandoc is imperfect. Plain text, headings, and paragraphs convert well; complex tables and math equations may need manual adjustment. Use DOCX for review only; submit via PDF.
