# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

All commands run from inside the project folder (`buku-pa/`, `progres-pa-1/`, `proposal-pa/`, `surat-magang/`):

```bash
cd buku-pa

make pdf         # compile (paper size fixed per project, buku-pa/progres-pa-1/proposal-pa A4)
make rebuild     # clean + recompile from scratch
make view        # compile then open PDF
make docx        # convert to DOCX via WordCraft (wordcraft-cli, format from ../wordcraft.toml)
make clean       # delete output/ folder
make check       # verify pdflatex, bibtex, wordcraft-cli are available
```

Build runs a full cycle: `pdflatex -> bibtex -> pdflatex -> pdflatex` to resolve bibliography and cross-references. Output goes to `output/` inside each project folder.

## Architecture

This is a LaTeX monorepo for academic documents at PENS (Politeknik Elektronika Negeri Surabaya), D4 Teknik Informatika.

```
laporan/
├── wordcraft.toml        <- format DOCX untuk make docx (WordCraft)
├── pustaka/              <- PDF sumber rujukan (belum-dirujuk/ = kandidat)
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
├── buku-pa/              <- Buku Proyek Akhir FULL (A4, mode buku final, tanpa sakelar progres)
│                            front matter: abstrak + abstract; Bab 4–5 register capaian
├── progres-pa-1/         <- Buku tahap 1 (\progrestrue, judul "PROGRES PROYEK AKHIR"):
│                            buku-pa tanpa INA219 dan catu daya baterai, target isi
│                            50-70% (arahan pembimbing). Tidak disinkronkan otomatis.
└── surat-magang/         <- surat (article 12pt, berdiri sendiri)
```

Kedua folder memakai `../shared/` dan `\graphicspath` ke `../proposal-pa/gambar/`.
Perubahan isi buku dikerjakan di `buku-pa/`; `progres-pa-1/` hanya diubah atas
permintaan eksplisit user.

### Buku tahap 1 (`progres-pa-1/`)

Buku tahap 1 adalah salinan `buku-pa/` yang dipangkas sesuai arahan pembimbing
(isi 50–70%). Yang dibuang: INA219 dan catu daya baterai di seluruh bab, yaitu
teori INA219 (Bab 2), butir perangkat keras, pin, layar, menu Ukur daya, dan
rencana uji daya (Bab 3), butir hasil Konsumsi Daya, baris ketercapaian daya,
dan keterbatasan daya (Bab 4), saran daya (Bab 5), serta kalimat status daya di
abstrak. Akibatnya ketiga tujuan berstatus Tercapai dan tidak ada
`PLACEHOLDER-DATA`. Satu-satunya beda di `main.tex` adalah blok
`\newif\ifprogres \progrestrue` dan komentar kepala; halaman judul memakai
`\ifprogres PROGRES\\\fi PROYEK AKHIR`.

Meregenerasi dari `buku-pa/` (misalnya sesudah `buku-pa` diperbarui):

1. Salin isi:
   ```bash
   cd laporan
   cp buku-pa/bab/*.tex progres-pa-1/bab/
   cp buku-pa/referensi.bib progres-pa-1/
   cp -r buku-pa/gambar/. progres-pa-1/gambar/
   ```
2. Kembalikan baris `\ifprogres PROGRES\\\fi` di `progres-pa-1/bab/halaman-judul.tex`.
   Bila `buku-pa/main.tex` berubah, salin lalu sisipkan lagi blok `\progrestrue`.
3. Buang INA219 dan catu daya seperti daftar di atas, lalu pastikan bersih:
   ```bash
   grep -rn -iE "INA219|TP4056|18650|konsumsi daya|ukur daya|tangga-daya" progres-pa-1/bab/*.tex | grep -v ":[0-9]*:\s*%"
   ```
   Yang tersisa hanya kalimat tentang penelitian lain di Bab 2.
4. Periksa dan buat keluaran:
   ```bash
   cd progres-pa-1 && make pdf && make docx
   python3 ../../scripts/cek_tabel.py bab/*.tex
   ```
   Hasil yang diharapkan: `undefined` 0, `Overfull` 0, cek_tabel 0 galat.
   Kondisi 1 Nov 2026: 132 halaman, 0 galat, 0 saran, `output/main.docx` terbentuk.

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

### Shared vs Standalone Preamble

- `proposal-pa/main.tex` delegates formatting to `shared/preamble.tex` (common) plus a
  `shared/size-aX.tex` (size-specific), input in that order.
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

### Penanda `% MANUAL` (WordCraft sync)

Kalau penulis menyunting dokumen di WordCraft (atau DOCX) lalu menyimpan balik ke `.tex`, setiap
paragraf yang ditulis oleh sync diberi satu baris penanda di atasnya:

```latex
% MANUAL 2026-11-01 (wordcraft sync): teks penulis, jangan diubah otomatis
Paragraf yang ditulis penulis dari WordCraft.
```

Aturan untuk agen dan skrip:

- Paragraf tepat di bawah baris `% MANUAL <tanggal> (wordcraft sync): …` adalah **teks penulis sendiri**, ditulis apa adanya dari WordCraft. **Jangan ditulis ulang, dirapikan, atau dikoreksi**, termasuk oleh agen dan skrip (`cek_tabel.py` dan sejenisnya).
- Agen dan skrip **boleh melaporkan** pelanggaran aturan di paragraf itu (titik dua, titik koma, istilah, desimal, dan seterusnya), lalu penulis yang memutuskan.
- Hapus penanda hanya kalau penulis memintanya. Sync berikutnya mengganti penanda lama (tidak menumpuk).
- Baris `% KOMENTAR [nama, tanggal]: …` (dengan lanjutan `%   …` untuk balasan) adalah catatan reviewer dari komentar Word. Kerjakan isinya, lalu hapus barisnya.
- Sync tidak menulis tabel, gambar, persamaan, heading, atau baris/kolom tabel baru, tidak menulis perubahan rumus (inline maupun display, sunting di LaTeX), dan tidak menulis komentar pada sel tabel. Bagian itu ditambahkan di LaTeX dan dilaporkan sync (daftar skipped); rumus tidak pernah ditulis dan tidak dilaporkan. Paragraf yang tidak bisa ditulis (misal berisi `\small`, `\hspace*`, `\textsc`, atau dibungkus grup `{...}`) tetap di dokumen yang belum disimpan dan hanya dilaporkan; `\emph` ditulis kembali sebagai `\textit`.

### Larangan Label Kerja Internal Repo (WAJIB)

Proposal, progres, dan buku adalah dokumen akademik formal. Label kerja internal
repo **dilarang muncul di teks yang tercetak** (semua baris non-komentar `.tex`,
termasuk caption, sel tabel, dan argumen `\PlaceholderGambar`). Yang dilarang:

- Label tahap/tugas: `HW-1`..`HW-7`, `Fase 0`..`Fase 8`, `Fase 6b/6c`, `Fase A`..`G`,
  `Task n`, `gate point`, `decision point`, `DoD`.
- Nama berkas dan path repo: `model/docs/...`, `firmware/src/...`, `*.md`, `*.py`,
  `*.h`, `*.cpp` (mis. `golden_ref.h`, `model_int8.h`, `ukur_pipeline.py`), kecuali
  dirujuk formal sebagai lampiran kode.
- Nama env PlatformIO dan perintah (`esp32-s3`, `native`, `pio test ...`),
  nama variabel/konstanta/knob (`PA_WIN_PRE`, `AMBANG_AYUN`, `golden_raw`, `ECG_*`),
  nama state firmware (`calibrating`), pesan serial, toggle serial (`y`, `m`, `k`).
- Riwayat revisi perangkat keras: `rev1`, `rev2`, "PCB revisi kedua", siapa
  yang mendesain PCB, dan apa yang diperbaiki antarrevisi. Buku memuat
  rancangan akhir saja (keputusan user 19 Okt 2026).
- Jargon kerja: "walkthrough", "golden ref", tag ablasi (`w128b`, `fb_svdb`,
  `t8_lr1e3`), nama himpunan internal (`TEST-B`, `TEST-C`).

Ganti dengan istilah deskriptif formal, contoh: "tahap pengujian akuisisi sinyal",
"uji publikasi MQTT", "eksperimen lintas basis data", "uji unit kode C di komputer",
"data acuan keluaran Python (*golden reference*)" lalu "data acuan", "sinyal acuan",
"fase kalibrasi", "ambang ayunan", "data uji SVDB/INCART", ID varian ablasi `A1`..`An`.
Nama *field* payload/telemetri yang menjadi bagian rancangan (`signal\_quality`,
`ts`, `ecg\_snippet`) dan nama API standar boleh tetap.

Rujukan sumber ke repo tetap ditulis, tetapi **hanya di komentar `%`**, dan harus ke
sumber yang stabil: walkthrough aktif `model/docs/*-walkthrough.md`, kode, atau
artefak `model/artifacts/metrics/*`. Dokumen rencana di `model/docs/arsip/` bisa
dihapus, jadi jangan dijadikan satu-satunya sumber (changelog eksperimen dan
`2026-10-08-pcb-rev2-adjustment.md` boleh). Cek cepat sebelum selesai:

```bash
grep -nE "HW-[0-9]|Fase [0-9A-G]|\.md|\.py|walkthrough|Task [0-9]" bab/*.tex | grep -vE ":[0-9]+:\s*%"
```

### Istilah Asing & Penulisan Teknis

- **Istilah teknis yang sudah lazim ditulis biasa (TANPA italic, TANPA diterjemahkan).** Perlakukan sebagai kosakata yang sudah diadopsi, bukan bahasa asing. Daftar yang sudah disepakati:
  - `preprocessing` (BUKAN "pra-pemrosesan", BUKAN `\textit{preprocessing}`)
  - `single-lead` (BUKAN "sadapan tunggal", BUKAN `\textit{single-lead}`)
  - `flowchart` (BUKAN "diagram alir", BUKAN `\textit{flowchart}`)
  - `bufer` (BUKAN "penyangga", BUKAN `\textit{buffer}`) — sudah masuk KBBI
- **Jangan terjemahkan istilah teknis ke Bahasa Indonesia.** Tulis dalam Bahasa Inggris aslinya dan miringkan (`\textit{}` / `\emph{}`). Contoh: tulis `\textit{board}` untuk papan elektronik (BUKAN "papan", keputusan user 20 Okt 2026), `\textit{library}` (BUKAN "pustaka", keputusan user 20 Okt 2026, diperiksa `cek_tabel.py` N-ISTILAH; "Kajian Pustaka" dan "Daftar Pustaka" tetap), `\emph{prototype}` (BUKAN "purwarupa"), `\emph{half-open}` (BUKAN "setengah-terbuka"), `\emph{reconnect}` (BUKAN "penyambungan ulang"), `\emph{buffer}` (BUKAN "penyangga"), `\emph{timestamp}` (BUKAN "penanda waktu"). Terjemahan Indonesia boleh muncul sekali sebagai penjelasan awal di dalam tanda kurung, lalu selanjutnya pakai istilah Inggris italic.
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
- **Gaya tiga garis di `buku-pa`** (keputusan user 19 Okt 2026, mengikuti tabel riset dan buku AFIB): `\toprule` di atas header, `\midrule` di bawah header, `\bottomrule` di akhir. Tanpa garis vertikal, tanpa `\hline`/`\cline`, tanpa `\rowcolor{headgray}`. Pemisah kelompok di badan cukup `\midrule`. Pengecualian: tabel Perbandingan Penelitian Terkait (`tab:perbandingan-penelitian`) memakai grid tertutup polos, yaitu garis vertikal dan `\hline` tanpa warna (keputusan user 20 Okt 2026, `TABEL_GRID_PENUH` di `scripts/cek_tabel.py`). Diperiksa `python3 scripts/cek_tabel.py` (kode T-GRID dan T-HEADER). Aturan lengkap: skill `tabel-pa`.
- Tabel panjang multi-halaman pakai `longtable` dengan header yang diulang (`\endfirsthead` + `\endhead`).
- **Tanpa teks "Bersambung ke halaman berikutnya" / "Lanjutan Tabel X.Y"** di footer/header lanjutan — user tidak suka. Cukup `\bottomrule` di `\endfoot`.
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

**Bab 2 Kajian Pustaka** — panduan meminta paragraf pembuka setelah judul bab, tetapi proposal yang diserahkan tidak memilikinya, dan `buku-pa` mengikuti proposal: tidak ada bab yang memiliki paragraf pembuka, judul bab langsung diikuti subbab pertama (keputusan user 20 Okt 2026, diperiksa `cek_tabel.py` N-PEMBUKA-BAB). Teks juga tidak memuat penunjuk ke bab, subbab, atau butir lain ("diuraikan pada Subbab~\ref{..}"), diperiksa N-PENUNJUK. Lalu `2.1 Deskripsi Permasalahan`, `2.2 Teori Penunjang` (semua klaim/teori wajib bersitasi), `2.3 Penelitian Terkait` (riset lain dengan Problem sama tapi Uniqueness beda; rujuk pustaka tepercaya).

**Bab 3 Deskripsi Sistem** — paragraf pembuka menurut panduan (lingkup: model, rancangan, variabel, teknik pengumpulan data, analisis data) tidak dipakai di `buku-pa`, sama seperti Bab 2; `3.1 Deskripsi Solusi` (argumentatif, fitur unik = orisinalitas), `3.2 Desain Sistem` (mulai dari diagram *high-level view*, baru rinci per komponen). Section variabel penelitian, teknik pengumpulan data, dan analisis data masuk sesuai lingkup paragraf pembuka.

**Aturan kutipan.** Kutipan langsung pendek (1–2 baris): petik ganda + italic + sitasi, mis. *"..."*`~\cite{x}`. Kutipan langsung panjang (>2 baris): environment `kutipan` (paragraf terpisah, 10pt, margin masuk 10mm kiri-kanan) + sitasi. Parafrase: sitasi di akhir kalimat.

**Gambar.** Rata tengah, sisakan 1 baris kosong atas-bawah. Caption (nomor + keterangan) di BAWAH gambar, tebal & rata tengah. Jika isi gambar kutipan: tulis "Sumber: ..." 10pt rata tengah DI ATAS caption.

**Persamaan.** Baris sendiri, masuk 10mm dari kiri (`fleqn`), 1 baris kosong atas-bawah. Nomor rata kanan tebal format "(Persamaan X.Y)". Wajib dirujuk & dibahas di paragraf.

**Tabel.** Rata tengah, 1 baris kosong atas-bawah. Caption (nomor + keterangan) di ATAS tabel, tebal & rata tengah (beda dari gambar yang di bawah). Panduan memberi latar abu-abu pada header dan grid penuh; gaya ini hanya dipakai `proposal-pa` (beku). `buku-pa` memakai gaya tiga garis (lihat Konvensi Tabel & Gambar). Jika kutipan: "Sumber: ..." 10pt rata tengah di bawah tabel. Wajib dirujuk di paragraf. Panduan resmi: 1 tabel ≤ 1 halaman; proyek ini meng-override aturan ini untuk tabel perbandingan panjang dengan `longtable` (lihat Konvensi Tabel & Gambar).

**Daftar Pustaka.** Bernomor `[n]`, gaya IEEE (`IEEEtran.bst` via `natbib`). Urutan & format per jenis sumber: jurnal (pengarang, judul, nama jurnal, vol/no/hal, penerbit, tahun), seminar, buku (pengarang, judul, penerbit, edisi, tahun), tugas akhir/skripsi/disertasi, media publik, media online (judul, situs, alamat, tanggal akses, tahun).

### DOCX Notes

DOCX dibuat oleh WordCraft dari proyek LaTeX (`make pdf docx`; `make pdf` dulu supaya
`output/main.bbl` ada untuk nomor sitasi). Formatnya (heading BAB, caption, margin, spasi,
daftar isi, pustaka) datang dari `laporan/wordcraft.toml`, bukan dari preamble: kalau
`shared/preamble.tex` / `size-a4.tex` berubah, sesuaikan `wordcraft.toml` juga. Page break
bisa geser 1–2 halaman dari PDF. DOCX untuk dibaca/review; submit tetap PDF.

Sync balik ke `.tex` sudah ada. Dua jalur:

- Dari aplikasi WordCraft: buka `main.tex`, sunting, Ctrl+S. Hanya paragraf yang berubah
  yang ditulis ulang, apa adanya, dengan penanda `% MANUAL` di atasnya (lihat "Penanda `% MANUAL`").
- Dari DOCX yang disunting di Word/LibreOffice: `make sync DOCX=output/main.docx`
  (`DOCX` default `output/main.docx`). `make sync-dry` hanya menampilkan diff tanpa menulis.

Kalau `.tex` berubah setelah DOCX dibuat, sync menolak (guard hash): jalankan `make docx` lagi
dan sunting ulang. Komentar Word menjadi baris `% KOMENTAR`. Tabel, gambar, persamaan, dan heading
baru tidak ditulis balik. Detail: `wordcraft/docs/latex.md`.
