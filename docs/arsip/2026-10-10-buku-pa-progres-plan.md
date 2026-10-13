# Buku PA Tahap Progres — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mengisi `laporan/buku-pa` menjadi laporan **progres PA** lengkap lima bab
(siap menjadi buku PA lewat penyuntingan di tempat): Bab 1–3 diangkat dari
proposal **dan disesuaikan dengan realisasi**, Bab 4–5 ditulis baru dari hasil
eksperimen yang sudah ada di repo.

**Architecture:** Satu projek LaTeX `laporan/buku-pa` dengan sakelar
`\ifprogres`. Bab 1–3 disalin dari `laporan/proposal-pa/bab/` lalu disunting
mengikuti tabel "Proposal → Realisasi" di bawah. Bab 4 disusun **per tujuan**
(rencana di `docs/pola-laporan-pa/08-bab4-pa-kita.md`). Semua diagram/ilustrasi
baru atau yang usang = placeholder; gambar proposal yang masih benar dirujuk
lewat `\graphicspath`, plot data lewat `scripts/export_artifacts.sh`.

**Tech Stack:** pdflatex + bibtex (`laporan/shared/Makefile.inc`), preamble
bersama `laporan/shared/preamble.tex`, data angka dari `model/` (CSV + `model/CLAUDE.md`).

---

## 0. Konteks wajib untuk SETIAP task (subagent baca ini dulu)

**Baca sebelum menulis apa pun:**
1. `laporan/CLAUDE.md` — aturan gaya (wajib dipatuhi di setiap kalimat).
2. `docs/pola-laporan-pa/03-pola-paragraf.md` — arketipe paragraf (P1–P19).
3. `docs/pola-laporan-pa/05-gambar-tabel-persamaan.md` §Placeholder gambar.
4. `docs/pola-laporan-pa/07-penerapan-ke-pa-kita.md` dan `08-bab4-pa-kita.md`.

**Aturan keras:**
- Hanya sentuh berkas yang disebut di bagian **Files** task. **Jangan pernah
  mengubah `laporan/proposal-pa/`** (proposal = arsip). Jangan ubah
  `laporan/shared/`.
- **Jangan menambah entri `.bib`.** Kalau butuh sitasi yang tidak ada, tulis
  `~\cite{key}` dengan key yang diusulkan dan catat di laporan task
  (`CITE-MISSING: key — judul`). Key yang SUDAH ADA di `laporan/buku-pa/referensi.bib`:
  who_cvd al_quayed_2026 tinyml_iot_review resilient_edge_cloud mekhfioui_2025
  xie_2021 karri_2023 laiu_2026 crespi_2026 oasis_mqtt5 kim_2023 elhadad_2025
  khan_2025 sheeba_rani_2026 fahoum_2026 xiang_2026 chowdhury_2023 kumaran_2026
  verma_2024 ecg_goldberger pan_tompkins_1985 sornmo_laguna_2005 moody_mark_2001
  dechazal_2004 mulyawan_2026 zambrano_2026 goldberger_2000_physionet.
- **Setiap angka hasil** harus berasal dari berkas yang benar-benar dibuka
  subagent, dan diberi komentar LaTeX di baris sesudahnya:
  `% sumber: model/artifacts/metrics/fase7_delta.csv`. Angka tanpa sumber = gagal.
- **Diagram/ilustrasi tidak dibuat.** Tidak ada Mermaid/TikZ/SVG/skrip gambar
  baru. Pakai makro `\PlaceholderGambar` (Task 1) + kartu spesifikasi di
  komentar (format di 05 §Kartu).
- **Tidak ada `git commit`.** User memutuskan commit di akhir. Jangan `git add`.
- Subjek uji ditulis **anonim** (S01, S02, …). Keamanan transport/TLS **tidak
  dibahas sama sekali**.
- Gaya: tanpa titik koma/em dash/titik dua pengantar daftar di tengah paragraf,
  tanpa penomoran inline "(1)", desimal koma, istilah Inggris `\textit{}`
  (kecuali preprocessing, single-lead, flowchart, bufer), tanpa `\texttt{}`,
  sitasi `~\cite{}`, tabel float `[!ht]` (bukan `[H]`), tabel panjang `longtable`
  tanpa teks "bersambung".

**Verifikasi baku (dipakai di setiap task):**

```bash
cd /home/mrrizaldi/dev/projek-akhir/laporan/buku-pa && make pdf > /tmp/bukupa_build.txt 2>&1; echo "exit=$?"
grep -nE "^!|LaTeX Error|Undefined control sequence|Emergency stop" output/main.log
grep -nE "Reference .* undefined|multiply defined|Citation .* undefined" output/main.log
```

Expected: `exit=0`, grep pertama kosong, grep kedua kosong **kecuali** baris
`Citation ... undefined` untuk key yang dicatat sebagai CITE-MISSING.

**Cek gaya (dipakai di setiap task penulisan, ganti `babN`):**

```bash
cd /home/mrrizaldi/dev/projek-akhir/laporan/buku-pa/bab
grep -nE "—|;|\\\\texttt" babN.tex | grep -vE "^\s*[0-9]+:\s*%|&" ; grep -nE "[0-9]\.[0-9]+ ?(\\\\%|ms|KB|Hz|FPS|mV|detik)" babN.tex | grep -vE "^\s*[0-9]+:\s*%"
grep -niE "proposal ini|akan dikonfirmasi|direncanakan dilakukan" babN.tex
```

Expected: kosong (titik koma di dalam sel tabel `&` dikecualikan; baris komentar
dikecualikan; desimal titik pada angka bersatuan tidak boleh ada).

---

## 1. Keputusan yang sudah dikunci (user, 10 Okt 2026)

PA individu (PCB rev1 dirancang rekan → cukup kredit satu kalimat). Subjek anonim,
jumlah belum pasti. Uji di laboratorium (nama lab belum pasti → tulis
"laboratorium"). TLS tidak dibahas. Progres dan buku = satu projek `laporan/buku-pa`.
Butir Batasan Masalah 1–6 di `07 §4` dipakai.

## 2. Tabel Proposal → Realisasi (hasil pengecekan, sumber kebenaran untuk Bab 1–4)

| # | Bagian proposal | Isi proposal | Realisasi | Sumber |
|---|---|---|---|---|
| R1 | Bab 2 ESP32-S3, Bab 3 kuantisasi, Tabel 2.x baris 13 | model < 20 KB | INT8 22,94 KB, batas disetujui 25 KB | `model/artifacts/metrics/fase7_delta.csv`, `model/CLAUDE.md` decision "Batas ukuran model" |
| R2 | Bab 2 ESP32-S3 | tensor arena "orde puluhan kilobyte"; ESP-NN disebut seolah dipakai | arena 12.948 B (±13 KB); library `Chirale_TensorFLowLite` 2.0.0 kernel referensi, **ESP-NN belum dipakai** | `model/CLAUDE.md` HW-1 + decision "Library TFLM" |
| R3 | Bab 2 AD8232 | lead-off dipakai menandai fase stabilisasi | LO tidak andal (LO 0% tanpa sinyal); gerbang = fase calibrating (stabilisasi 10 menit + RR 300–1500 ms dan \|dRR\| ≤ 200 ms tenang 30 detik) lalu gerbang ayunan per detak | `model/CLAUDE.md` HW-6 + jebakan "Telemetri akuisisi bisa berbohong" |
| R4 | Bab 2 1D-CNN, Bab 3 arsitektur | GAP | model latih tetap GAP; **varian deploy** mengganti GAP dengan DepthwiseConv1D(32) berbobot 1/32 (kernel = panjang setelah 3 pooling, 256→32; "31" di model/CLAUDE.md sisa window 250) dan kepala Dense→Conv1D kernel 1 (op MEAN di TFLM salah hitung tanpa error) | `model/CLAUDE.md` decision "Model yang dikuantisasi", "Pengganti GlobalAveragePooling", "Flatten/Reshape" |
| R5 | Bab 3 segmentasi, gambar_segmentasi, gambar_3_2, gambar_3_4 | window 250 (90/160) | **256 (128/128)**, R di indeks 132 (128 + group delay 4) | decision "Ukuran window" |
| R6 | Bab 3 filter | orde 2–4 | **orde 4** bandpass (4 seksi biquad, `ECG_N_SOS 4`; catatan "2 biquad" di model/CLAUDE.md keliru), kausal `sosfilt`, group delay +4 sampel (+11,2 ms) | `model/CLAUDE.md` Fase 1 |
| R7 | Bab 3 Pan-Tompkins → segmentasi | R-peak langsung jadi acuan | kompensasi offset 38 sampel + penyelarasan puncak ±25 + koreksi group delay; refraktori 200 ms membatasi deteksi beat prematur | decision "Segmentasi on-device", jebakan "Refraktori 200 ms" |
| R8 | Bab 3 dataset | 48 rekaman, biner | record dibuang 102, 104 (tanpa MLII), 107, 217 (paced) → 44 record; VAL = 101, 114, 201, 220, 223; latih **mitdb saja** | decision "Record dibuang", "Validation set", "Database LATIH" |
| R9 | Bab 3 dataset (paragraf diarsipkan `\iffalse`) | uji lintas basis data INCART & SVDB "menunggu pertimbangan" | **dipakai sebagai uji held-out** TEST-B (svdb) dan TEST-C (incartdb), 39 pasien, 85.812 beat, di-resample ke 360 Hz; hanya untuk ablasi, bukan untuk melatih | decision "Database LATIH", `artifacts/metrics/ablasi/lintas_db.csv` |
| R10 | Bab 3 arsitektur | Dense 16 + Dropout | **tanpa dropout** (dropout menurunkan recall), 6.417 parameter | decision "Dropout Dense 16", Fase 4 |
| R11 | Bab 3 sigmoid | threshold 0,5 | **0,80**, dikalibrasi di VAL (F1 maksimum, tie-break recall) | decision "Threshold" |
| R12 | Bab 3 pelatihan | "akan ditetapkan pada tahap eksperimen" | class_weight balanced (Normal 0,556 / Aritmia 4,947), Adam 1e-3, EarlyStopping val_auc patience 8 + restore best, **augmentasi jitter empiris ×2 salinan hanya di DS1** (Dias 2021) | decision "Strategi imbalance", "Monitor EarlyStopping", "Learning rate", "Augmentasi jitter" |
| R13 | Bab 3 PTQ | representative dataset seluruh kelas | 300 sampel stratified DS1, seed dikunci, full INT8 in/out | decision "Sampel kalibrasi PTQ", "Tipe I/O INT8" |
| R14 | Bab 3 pipeline transmisi | real-time per rekaman, batch 50–100 hanya saat reconnect | **semua beat masuk antrean dulu**, dikirim per batch maksimal 50 rekaman, PUBACK dipungut lintas iterasi loop (tidak blocking) | `firmware/src/ecg_mqtt.cpp` (baris 417–422), `firmware/include/ecg_mqtt.h` (`ECG_MQTT_BATCH_N 50`) |
| R15 | Bab 3 ring buffer | partisi ±4 MB, ±150 byte/rekaman, ±27.000 rekaman | **40 byte/entri**, 27.000 entri ≈ 1,08 MB PSRAM, overwrite tertua tetap | `firmware/include/ecg_mqtt.h` baris 29–34 |
| R16 | Bab 3 payload | ±100–150 byte/paket | field identik dengan tabel proposal, ukuran ±320 byte/rekaman di paket | `firmware/src/ecg_mqtt.cpp` (`paket_buf`), `model/CLAUDE.md` jebakan Nagle (~330 B) |
| R17 | Bab 3 ts | dari RTC | `gettimeofday` + posisi R absolut (waktu kejadian) | commit `6fc426c`, `model/CLAUDE.md` jebakan `time()` |
| R18 | Bab 3 half-open | pantau latensi PUBACK, reconnect paksa | sama, ditambah `setNoDelay(true)` dan `WiFi.setSleep(false)` | `model/CLAUDE.md` HW-6 + jebakan Nagle |
| R19 | Bab 3 perangkat keras | tidak ada subbab | breadboard (uji HW-1..HW-6) → PCB rev1 (rekan) → rev2 (berjalan); tambah TFT ST7789, buzzer aktif, 3 tombol, INA219 | memori PCB rev1, `model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md`, `firmware/src/main.cpp`, `firmware/src/hwtest.cpp` |
| R20 | Bab 3 tabel rencana model | target "recall tinggi", "penurunan kecil", "muat flash", "hemat daya" | recall: dilaporkan pada titik operasi hasil kalibrasi VAL (tanpa ambang numerik, PRD tidak menetapkan); delta: \|Δ recall\| < 0,02 (DoD PRD); ukuran: < 25 KB (DoD PRD); daya: diukur per mode p0–p3 (mA, mW) tanpa ambang | `model/scripts/check_poc.py` baris 100–128, `model/docs/arsip/2026-09-16-daya-design.md` |
| R21 | Bab 3 tabel rencana | tidak ada baris kesetaraan preprocessing | tambah baris "Kesetaraan C vs Python: keluaran perangkat identik dengan golden Python dalam toleransi 1 kuantum INT8" (berasal dari PRD, golden reference) | `firmware/test/golden_ref.h`, `model/CLAUDE.md` HW-1 |
| R22 | Bab 1 | tanpa Batasan Masalah, Sistematika versi proposal | tambah Batasan Masalah (6 butir), tulis ulang Sistematika Bab 4–5 | `docs/pola-laporan-pa/07-penerapan-ke-pa-kita.md` §4 |

## 3. Struktur berkas

| Berkas | Status | Tanggung jawab |
|---|---|---|
| `laporan/buku-pa/main.tex` | ubah | sakelar `\ifprogres`, `\graphicspath`, makro placeholder, front matter, urutan `\input` |
| `laporan/buku-pa/bab/halaman-judul.tex` | baru (dari proposal) | sampul PROGRES/PROYEK AKHIR |
| `laporan/buku-pa/bab/abstrak.tex` | baru | abstrak Indonesia versi progres |
| `laporan/buku-pa/bab/bab1.tex` | timpa placeholder 3 baris | Bab 1 |
| `laporan/buku-pa/bab/bab2.tex` | baru (dari proposal) | Bab 2 |
| `laporan/buku-pa/bab/bab3.tex` | baru (dari proposal) | Bab 3 |
| `laporan/buku-pa/bab/bab4.tex` | baru | Bab 4 |
| `laporan/buku-pa/bab/bab5.tex` | baru | Bab 5 |
| `laporan/buku-pa/gambar/` | baru (oleh export) | plot data hasil pipeline |
| `scripts/export_artifacts.sh` | ubah | tujuan figure → `buku-pa`, daftar figure Bab 4 |

---

### Task 1: Kerangka `buku-pa` (main.tex, sampul, front matter, stub bab)

**Files:**
- Modify: `laporan/buku-pa/main.tex`
- Create: `laporan/buku-pa/bab/halaman-judul.tex`, `laporan/buku-pa/bab/abstrak.tex`, `laporan/buku-pa/bab/bab2.tex`, `bab3.tex`, `bab4.tex`, `bab5.tex`
- Keep: `laporan/buku-pa/bab/bab1.tex` (diisi di Task 2)

- [ ] **Step 1: Ganti blok `% DATA MAHASISWA` sampai akhir `main.tex`** dengan isi berikut (bagian preamble di atasnya tetap):

```latex
% ============================================================
% DATA MAHASISWA & PROYEK AKHIR
% ============================================================

\newcommand{\JudulPA}{Implementasi Sistem Monitoring Detak Jantung Kontinu Berbasis IoT Edge Computing untuk Deteksi Dini Aritmia}
\newcommand{\NamaMahasiswa}{Muhammad Rafi Rizaldi}
\newcommand{\NRP}{3123600001}
\newcommand{\PembimbingSatu}{Prof. M. Udin Harun Al Rasyid, S.Kom, Ph.D}
\newcommand{\NIPSatu}{198108082005011001}
\newcommand{\PembimbingDua}{Grezio Arifiyan Primajaya, S.Kom, M.Kom}
\newcommand{\NIPDua}{199208262022031007}
\newcommand{\Tahun}{2026}

% ============================================================
% TAHAP DOKUMEN: progres (true) atau buku final (false)
% ============================================================
\newif\ifprogres
\progrestrue

% Gambar: milik buku dulu, lalu gambar proposal yang masih berlaku.
\graphicspath{{gambar/}{../proposal-pa/gambar/}}

% Placeholder gambar (aturan: diagram/ilustrasi digambar user, bukan Claude).
% Pakai di dalam figure, didahului komentar "% PLACEHOLDER-GAMBAR fig:..." + kartu.
\newcommand{\PlaceholderGambar}[2]{%
  \fbox{\parbox[c][5cm][c]{0.85\linewidth}{\centering\small
    \textbf{[PLACEHOLDER GAMBAR]}\\[3pt]
    #1: #2\\
    Spesifikasi lengkap ada di komentar sumber.}}}

% ============================================================
% DOKUMEN
% ============================================================

\begin{document}

% --- SAMPUL ---
\pagestyle{empty}
\input{bab/halaman-judul}

% --- FRONT MATTER (romawi) ---
\cleardoublepage
\pagenumbering{roman}
\pagestyle{plain}
\input{bab/abstrak}

\cleardoublepage
\phantomsection
\addcontentsline{toc}{chapter}{DAFTAR ISI}
\tableofcontents

\cleardoublepage
\phantomsection
\addcontentsline{toc}{chapter}{DAFTAR GAMBAR}
\listoffigures

\cleardoublepage
\phantomsection
\addcontentsline{toc}{chapter}{DAFTAR TABEL}
\listoftables

% --- ISI (arab) ---
\cleardoublepage
\pagenumbering{arabic}
\pagestyle{mainmatter}

\input{bab/bab1}
\input{bab/bab2}
\input{bab/bab3}
\input{bab/bab4}
\input{bab/bab5}

% --- DAFTAR PUSTAKA ---
\cleardoublepage
\phantomsection
\addcontentsline{toc}{chapter}{DAFTAR PUSTAKA}
\bibliography{referensi}

\end{document}
```

- [ ] **Step 2: Buat `bab/halaman-judul.tex`**: salin isi `laporan/proposal-pa/bab/halaman-judul.tex` apa adanya, lalu ganti SATU baris judul dokumen

```latex
  {\fontsize{16}{20}\selectfont\bfseries PROPOSAL\\PROYEK AKHIR\par}
```

menjadi

```latex
  {\fontsize{16}{20}\selectfont\bfseries \ifprogres PROGRES\\\fi PROYEK AKHIR\par}
```

dan ganti komentar baris ke-2 file (`"PROPOSAL PROYEK AKHIR"`) menjadi `"PROGRES PROYEK AKHIR" / "PROYEK AKHIR"`.
Logo `gambar/logo-pens.png` ditemukan lewat `\graphicspath` (tidak perlu disalin).

- [ ] **Step 3: Buat `bab/abstrak.tex` sementara** (isi final di Task 12): salin
baris 1–31 `laporan/proposal-pa/bab/abstrak.tex` (bagian ABSTRAK Indonesia saja,
tanpa ABSTRACT Inggris), lalu tambahkan `\clearpage` di akhir.

- [ ] **Step 4: Buat stub bab** (masing-masing satu file):

```latex
% bab2.tex
\chapter{Kajian Pustaka}
\label{chap:kajian-pustaka}
```

```latex
% bab3.tex
\chapter{Deskripsi Sistem}
\label{chap:deskripsi-sistem}
```

```latex
% bab4.tex
\chapter{Eksperimen dan Analisis}
\label{chap:eksperimen}
```

```latex
% bab5.tex
\chapter{Penutup}
\label{chap:penutup}
```

- [ ] **Step 5: Jalankan Verifikasi baku.** Expected: `exit=0`, log bersih,
PDF memuat sampul bertuliskan "PROGRES PROYEK AKHIR", lalu Abstrak, Daftar Isi,
Daftar Gambar, Daftar Tabel bernomor romawi, lalu BAB 1–5 bernomor arab mulai
di halaman ganjil. Cek: `pdftotext -f 1 -l 1 output/main.pdf - | head -5`
memuat "PROGRES".

---

### Task 2: Bab 1 Pendahuluan (proposal + penyesuaian)

**Files:**
- Modify (timpa placeholder): `laporan/buku-pa/bab/bab1.tex`
- Sumber: `laporan/proposal-pa/bab/bab1.tex`

- [ ] **Step 1: Salin** seluruh `laporan/proposal-pa/bab/bab1.tex` ke `laporan/buku-pa/bab/bab1.tex` (menimpa placeholder 3 baris "Placeholder Buku Proyek Akhir. Konten menyusul.").

- [ ] **Step 2: Tambah Batasan Masalah** tepat sesudah blok `\section{Permasalahan}` (sesudah `\end{enumerate}` miliknya, sebelum `\section{Tujuan}`):

```latex
\section{Batasan Masalah}
\label{sec:batasan-masalah}

Agar penelitian tetap terarah dan tujuan dapat dicapai, ruang lingkup penelitian ini dibatasi pada butir berikut.
\begin{enumerate}
  \item Klasifikasi dirumuskan secara biner, yaitu Normal dan Aritmia. Penamaan jenis aritmia (ventrikular, supraventrikular, atau fusi) tidak termasuk keluaran sistem.
  \item Model dilatih menggunakan MIT-BIH \textit{Arrhythmia Database} pada sadapan MLII dengan pembagian data \textit{inter-patient} (DS1 untuk pelatihan, DS2 untuk pengujian). Basis data MIT-BIH \textit{Supraventricular Arrhythmia Database} dan St.~Petersburg INCART hanya digunakan sebagai data uji lintas basis data, bukan untuk pelatihan.
  \item Akuisisi sinyal menggunakan modul AD8232 dalam konfigurasi single-lead Lead II dengan elektroda \textit{wet-gel}.
  \item Pengujian perangkat dilakukan pada subjek sehat yang dianonimkan dalam lingkungan laboratorium non-klinis. Sistem tidak dirancang sebagai alat diagnosis dan pengujian ini bukan uji klinis.
  \item Ketahanan \textit{pipeline} diuji dalam batas kapasitas \textit{ring buffer} PSRAM. Kehilangan daya pada perangkat berada di luar cakupan pengujian ketahanan.
  \item Konsumsi daya diukur, tetapi tidak dioptimasi. Rangkaian baterai dan jalur daya perangkat \textit{wearable} berada di luar lingkup penelitian ini.
\end{enumerate}
```

- [ ] **Step 3: Tujuan.** Biarkan kalimat orisinalitas dan tiga butir tujuan. Sesudah `\end{enumerate}` milik Tujuan, tambahkan satu paragraf:

```latex
Kriteria keberhasilan setiap tujuan dirumuskan secara terukur pada rencana pengujian di Subbab~\ref{sec:rencana-pengujian}, dan ketercapaiannya dianalisis per tujuan pada Bab~\ref{chap:eksperimen}.
```

- [ ] **Step 4: Sistematika Penulisan.** Ganti dua blok terakhir (BAB 4 dan BAB 5) dengan versi berikut, blok BAB 1–3 dibiarkan kecuali kata "perumusan masalah, tujuan" menjadi "perumusan masalah, batasan masalah, tujuan":

```latex
\noindent
\textbf{\makebox[1.5cm][l]{BAB 4}EKSPERIMEN DAN ANALISIS}\\
\hspace*{1.5cm} Bab ini memaparkan parameter eksperimen, karakteristik data, tempat dan waktu ujicoba, spesifikasi peralatan, serta hasil eksperimen yang disusun per tujuan, yaitu jalur preprocessing \textit{real-time} di mikrokontroler, jalur model TinyML INT8 di ESP32-S3, dan jalur \textit{pipeline edge-to-cloud} yang resilien. Bab ini ditutup dengan analisis ketercapaian setiap tujuan pada tahap progres beserta keterbatasannya.

\noindent
\textbf{\makebox[1.5cm][l]{BAB 5}PENUTUP}\\
\hspace*{1.5cm} Bab ini merangkum temuan utama dari perancangan, implementasi, dan eksperimen tahap progres, kemudian memberikan saran pengembangan untuk tahap berikutnya.
```

- [ ] **Step 5: Jalankan Verifikasi baku + Cek gaya (`bab1`).** Expected bersih. Catatan: `\ref{sec:rencana-pengujian}` dan `\ref{chap:eksperimen}` baru terselesaikan setelah Task 4 dan Task 1 — `chap:eksperimen` sudah ada sejak Task 1; `sec:rencana-pengujian` boleh berstatus "undefined" sampai Task 4 selesai (catat di laporan task).

---

### Task 3: Bab 2 Kajian Pustaka (proposal + penyesuaian)

**Files:**
- Modify (timpa stub): `laporan/buku-pa/bab/bab2.tex`
- Sumber: `laporan/proposal-pa/bab/bab2.tex`

- [ ] **Step 1: Salin** seluruh `laporan/proposal-pa/bab/bab2.tex` ke `laporan/buku-pa/bab/bab2.tex`.

- [ ] **Step 2: Paragraf pembuka bab** (Panduan mewajibkan, proposal belum punya). Sisipkan sesudah `\label{chap:kajian-pustaka}`, sebelum `\section{Deskripsi Permasalahan}`, satu paragraf pola P1 (03): masalah utama dalam ranahnya (monitoring aritmia kontinu yang masih *cloud-centric*, model yang dievaluasi di PC, *pipeline* tanpa resiliensi) → bab ini menguraikan teori penunjang → penelitian terkait diulas untuk menegaskan posisi dan keunikan penelitian. 3–4 kalimat, tanpa sitasi baru.

- [ ] **Step 3: R1 + R2 di subbab ESP32-S3** (`\subsection{Mikrokontroler ESP32-S3}`):
  - Kalimat "didukung pustaka kernel terakselerasi ESP-NN, sehingga operasi ... lebih efisien" → ubah agar ESP-NN disebut sebagai **kemampuan platform**, lalu tambahkan kalimat bahwa pada penelitian ini inferensi masih memakai kernel referensi TFLite Micro dan ESP-NN menjadi opsi optimasi berikutnya.
  - "Dengan model berukuran di bawah 20 KB dan tensor arena yang hanya berorde puluhan kilobyte" → "Dengan model INT8 berukuran sekitar 23 KB dan \textit{tensor arena} sekitar 13 KB". Tambah komentar `% sumber: model/artifacts/metrics/fase7_delta.csv (ukuran_kb 22.94); model/CLAUDE.md HW-1 (arena 12.948 B)`.

- [ ] **Step 4: R3 di subbab AD8232.** Kalimat terakhir paragraf kedua ("... fitur deteksi lepasnya elektroda ... dimanfaatkan dalam penelitian ini untuk menandai fase stabilisasi elektroda awal.") ganti dengan dua kalimat: fitur *lead-off* tersedia, tetapi penanda ini tidak cukup sebagai jaminan adanya sinyal karena dapat terpenuhi oleh satu jalur impedansi rendah. Oleh karena itu, kualitas sinyal pada penelitian ini dinilai dari ayunan sinyal hasil ADC, sebagaimana dirinci pada Bab~\ref{chap:deskripsi-sistem}.

- [ ] **Step 5: R4 di subbab 1D-CNN.** Sesudah kalimat tentang GAP menekan jumlah parameter, tambah satu kalimat: pada saat *deployment*, operasi GAP dapat diwujudkan dengan operasi lain yang setara secara matematis bila *runtime* mikrokontroler menghitungnya berbeda, sebagaimana dibahas pada Bab~\ref{chap:deskripsi-sistem}. Tanpa sitasi baru.

- [ ] **Step 6: Tambah dua subbab teori baru** tepat sebelum `\section{Penelitian Terkait}` (sesudah subbab MIT-BIH):

```latex
\subsection{Evaluasi \textit{Inter-Patient} dan Metrik Klasifikasi}
\label{subsec:evaluasi-metrik}
```
Isi (pola P7, dua sampai tiga paragraf + satu persamaan set metrik): pembagian *inter-patient* DS1/DS2 menurut de Chazal~\cite{dechazal_2004} dan alasannya (pembagian per detak membuat detak pasien yang sama muncul di data latih dan uji sehingga metrik optimistis). Definisi *recall*, *precision*, *specificity*, F1, dan AUC dari TP, FP, TN, FN dalam satu blok `align`/`equation` bernomor dengan penjelasan "di mana ...". Satu paragraf alasan **accuracy tidak dipakai sebagai metrik utama**: pada data dengan detak Normal sekitar 89\%, menebak Normal untuk semua detak sudah memberi accuracy sekitar 0,89 (`% sumber: model/CLAUDE.md Fase 6 (lama) — accuracy tebak-Normal 0,8903`). Tutup "Dalam penelitian ini, ...".

```latex
\subsection{Augmentasi Data Berbasis Galat Segmentasi}
\label{subsec:augmentasi-jitter}
```
Isi (pola P7, dua paragraf): detektor R-peak di perangkat tidak selalu menaruh puncak tepat di posisi anotasi, sehingga *window* yang masuk model bergeser. Augmentasi *jitter* menggeser posisi segmentasi data latih secara acak agar model tahan terhadap pergeseran tersebut~\cite{dias_2021}. Penelitian ini mengadopsi gagasan tersebut, tetapi besar pergeserannya diambil dari sebaran galat detektor yang diukur sendiri, bukan nilai seragam dari literatur. Catat `CITE-MISSING: dias_2021 — F. M. Dias et al., "Arrhythmia classification from single-lead ECG signals using the inter-patient paradigm," Computer Methods and Programs in Biomedicine, vol. 202, 105948, 2021, doi:10.1016/j.cmpb.2021.105948` (sumber detail: `model/docs/jitter-walkthrough.md` baris 3–5).

- [ ] **Step 7: R1 di Tabel Perbandingan Penelitian Terkait**, baris 13 (Proposed System): "($<$20 KB)" → "($\pm$23 KB)", dan frasa "dalam satu perangkat ESP32-S3 hemat daya" → "dalam satu perangkat ESP32-S3". Jangan ubah baris lain.

- [ ] **Step 8: Paragraf penutup 2.3** (sesudah tabel, kalimat "Dari Tabel ... belum ada penelitian ..."): tambahkan satu paragraf pola P9 (03): angka akurasi pada penelitian terkait tidak dapat dibandingkan langsung dengan hasil penelitian ini karena skema pembagian data berbeda. Sebut hanya fakta yang tertulis di bab ini: Zambrano-de la Torre et al. membagi data per detak~\cite{zambrano_2026}, penelitian pendahulu melaporkan akurasi pada klasifikasi AF/Non-AF~\cite{mulyawan_2026}, sedangkan penelitian ini memakai skema *inter-patient* dan metrik pada Subbab~\ref{subsec:evaluasi-metrik}. **Jangan** menyebut skema pembagian paper lain yang tidak tertulis di Bab 2.

- [ ] **Step 9: Verifikasi baku + Cek gaya (`bab2`).** Expected bersih kecuali `Citation dias_2021 undefined`.

---

### Task 4: Bab 3 Deskripsi Sistem (proposal + penyesuaian + perangkat keras)

**Files:**
- Modify (timpa stub): `laporan/buku-pa/bab/bab3.tex`
- Sumber: `laporan/proposal-pa/bab/bab3.tex`, `firmware/src/main.cpp`, `firmware/src/hwtest.cpp`, `firmware/include/ecg_mqtt.h`, `firmware/src/ecg_mqtt.cpp`, `model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md`, `model/CLAUDE.md`, `dashboard/dashboard_ekg.json`

Kala: Bab 3 menggambarkan **rancangan yang berlaku sekarang**, ditulis deskriptif ("dirancang", "digunakan"), tanpa "akan" dan tanpa "direncanakan". Perubahan dari proposal TIDAK diceritakan di sini (itu tugas Bab 4 pembuka 4.6).

- [ ] **Step 1: Salin** seluruh `laporan/proposal-pa/bab/bab3.tex` ke `laporan/buku-pa/bab/bab3.tex`.

- [ ] **Step 2: Paragraf pembuka bab** sesudah `\label{chap:deskripsi-sistem}` (Panduan, pola P1): lingkup bab = deskripsi solusi, rancangan perangkat keras, alur preprocessing, model klasifikasi beserta data dan pelatihannya, *pipeline edge-to-cloud*, antarmuka monitoring, dan rencana pengujian. 2–3 kalimat.

- [ ] **Step 3: Subbab baru Perancangan Perangkat Keras** (R19). Sisipkan sebagai `\subsection` PERTAMA di bawah `\section{Desain Sistem}`, sesudah paragraf penjelas Gambar arsitektur (`fig:arsitektur-sistem`), sebelum `\subsection{Akuisisi dan Preprocessing Sinyal ECG}`:

```latex
\subsection{Perancangan Perangkat Keras}
\label{subsec:perangkat-keras}
```
Isi:
  a. Paragraf komponen (pola P13, butir a–f): ESP32-S3 N16R8 (board `4d_systems_esp32s3_gen4_r8n16`), AD8232 + elektroda, layar TFT ST7789 1,47 inci, *buzzer* aktif, tiga tombol, INA219 (pengukur daya). Fungsi masing-masing satu sampai dua kalimat.
  b. Gambar diagram blok → placeholder:

```latex
% PLACEHOLDER-GAMBAR fig:blok-perangkat-keras  (digambar user, bukan Claude)
% Jenis      : diagram blok perangkat keras, landscape
% Pesan      : komponen dan jalur sinyal/daya di sekitar ESP32-S3
% Elemen     : ESP32-S3 N16R8; AD8232 (OUT ke ADC, LO+ LO-); elektroda RA LA RL;
%              TFT ST7789 (SPI); buzzer aktif via transistor 2N2222; 3 tombol;
%              INA219 (I2C) di jalur daya; sumber daya USB/baterai
% Alur baca  : sensor kiri -> ESP32-S3 tengah -> keluaran (TFT, buzzer, WiFi) kanan; daya bawah
% Teks       : nama komponen persis seperti di paragraf
% Bahan repo : model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md; firmware/src/hwtest.cpp
\begin{figure}[H]
  \centering
  \PlaceholderGambar{Diagram blok perangkat keras}{ESP32-S3, AD8232, TFT, buzzer, tombol, INA219}
  \caption{Diagram blok perangkat keras}
  \label{fig:blok-perangkat-keras}
\end{figure}
```

  c. Tabel pin map (`table` `[!ht]`, kolom: Komponen | Sinyal | Pin breadboard | Pin PCB rev1/rev2). Isi dari berkas, bukan ingatan: pin breadboard dari konstanta pin di `firmware/src/main.cpp`; pin PCB dari `firmware/src/hwtest.cpp` (komentar "Pin map PCB rev1") dan perubahan rev2 dari `model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md` (BTN1 pindah ke GPIO14, J2 TFT jadi 8 pin dengan CS ke GND, divider resistor TFT dihapus). Komentar `% sumber:` per baris kelompok.
  d. Paragraf versi perangkat: pengujian pada Bab 4 dilakukan pada rangkaian breadboard. Desain PCB rev1 disusun oleh rekan, dan revisi rev2 sedang dikerjakan untuk memperbaiki level tegangan GPIO 3,3 V pada tombol, INA219, dan TFT. Prinsip "GPIO hanya dari 3V3" disebut satu kalimat.

- [ ] **Step 4: Gambar arsitektur dan flowchart proposal yang usang → placeholder revisi.** Untuk setiap gambar berikut, GANTI baris `\includegraphics[...]{...}` dengan placeholder, caption dan label TETAP sama, tambah blok komentar kartu:

| Label | File lama | Yang harus berubah (tulis di kartu) |
|---|---|---|
| `fig:arsitektur-sistem` | gambar_3_1.png | label payload "JSON ~100–150 byte" → "±320 byte per rekaman, batch ≤ 50" (R14, R16) |
| `fig:alir-preprocessing` | gambar_3_2.png | segmentasi "±250 sampel di R" → "256 sampel (128 sebelum, 128 sesudah R)"; tambah langkah "kompensasi offset + penyelarasan puncak" antara deteksi R-peak dan segmentasi (R5, R7) |
| `fig:segmentasi` | gambar_segmentasi_normalisasi.png | "window tetap = 250 sampel, 90 pra-R, 160 pasca-R" → "256 sampel, 128 pra-R, 128 pasca-R" (R5) |
| `fig:pipeline-training` | gambar_3_4.png | "Window ECG 250 x 1" → "256 x 1"; "Dense 16 ReLu - Dropout" → "Dense 16 ReLU"; "Sigmoid σ ≥ 0.5" → "Sigmoid σ ≥ 0,80" (R5, R10, R11) |
| `fig:alir-firmware` | gambar_3_5.png | "Publikasi real-time per-rekaman" + "Baca 50–100 rekaman" → "semua beat masuk antrean PSRAM, kirim batch ≤ 50, PUBACK dipungut tanpa blocking"; tambah fase "calibrating" dan gerbang ayunan sebelum publikasi (R3, R14) |

Format kartu: `% PLACEHOLDER-GAMBAR <label>  REVISI dari <file lama>` lalu baris `% Ubah :` per butir kolom ketiga. Isi `\PlaceholderGambar{Revisi <file lama>}{<ringkasan satu baris>}`.

- [ ] **Step 5: Teks Akuisisi–Segmentasi** (R5, R6, R7):
  - Akuisisi: tambah satu kalimat bahwa pencuplikan 360 Hz dilakukan di *timer interrupt* dan sampel diantrekan sebelum diproses, agar beban komputasi yang datang sesaat (deteksi dan inferensi bersamaan) tidak menghilangkan sampel.
  - Filter: "Filter berorde 2--4 dinilai memadai" → filter orde 4 diimplementasikan sebagai dua *biquad* kausal. Tambah kalimat *group delay* sekitar 4 sampel (11,2 ms) yang konsisten antara pelatihan dan perangkat.
  - Pan-Tompkins: tambah kalimat refraktori 200 ms.
  - Segmentasi: "250 sampel, yaitu 90 sampel sebelum dan 160 sampel sesudah" → "256 sampel, yaitu 128 sampel sebelum dan 128 sampel sesudah". Tambah paragraf singkat: posisi R hasil detektor dikompensasi (offset 38 sampel yang dikalibrasi di DS1), diselaraskan ke puncak terdekat (±25 sampel), lalu ditempatkan pada indeks 132 (128 + *group delay* 4), sama dengan posisi R pada data latih. `% sumber: model/CLAUDE.md decision "Segmentasi on-device"`.

- [ ] **Step 6: Dataset dan pelabelan** (R8, R9):
  - Tambah paragraf: record 102 dan 104 tidak memiliki kanal MLII, record 107 dan 217 berisi detak *paced*, sehingga keempatnya dikeluarkan dan tersisa 44 record. Pembagian DS1/DS2 mengikuti de Chazal~\cite{dechazal_2004}. Lima record DS1 (101, 114, 201, 220, 223) dipisahkan sebagai data validasi untuk pemilihan *epoch* dan kalibrasi *threshold*.
  - Kalimat "Penggolongan beberapa kelainan konduksi mengikuti standar yang akan dikonfirmasi lebih lanjut pada pelaksanaan eksperimen." → "Penggolongan simbol mengikuti pemetaan AAMI yang digunakan de Chazal~\cite{dechazal_2004}."
  - Blok `\iffalse ... \fi` (uji lintas basis data): HAPUS pembungkus `\iffalse`/`\fi` dan komentar arsipnya, lalu tulis ulang paragrafnya: SVDB dan INCART dipakai sebagai data uji *held-out* (TEST-B dan TEST-C) setelah di-*resample* ke 360 Hz, hanya untuk ablasi dan evaluasi generalisasi, tidak untuk pelatihan. Ganti "\emph{window} 250 sampel" → "\emph{window} 256 sampel". Sitasi tetap `~\cite{goldberger_2000_physionet}`.

- [ ] **Step 7: Arsitektur model** (R4, R10, R11): "Window ECG 250 sampel" → 256; hapus "dan \textit{Dropout} untuk menekan \textit{overfitting}"; kalimat "Nilai $\hat{y} \geq 0{,}5$ diklasifikasikan sebagai Aritmia" → "*threshold* klasifikasi ditetapkan 0,80 melalui kalibrasi pada data validasi"; "ukuran model setelah kuantisasi INT8 tetap di bawah 20 KB" → "berukuran sekitar 23 KB". Tambah satu paragraf **varian deploy** (R4): model yang dikuantisasi adalah varian yang mengganti GAP dengan `DepthwiseConv1D` berukuran 32 berbobot 1/32 (rata-rata yang sama) dan lapisan *Dense* dengan konvolusi berkernel 1, karena TFLite Micro menghitung operasi rata-rata global berbeda dari TFLite di PC tanpa memunculkan galat. Bobot disalin apa adanya tanpa pelatihan ulang. Total parameter 6.417 `% sumber: model/CLAUDE.md Fase 4`.

- [ ] **Step 8: Pelatihan dan kuantisasi** (R12, R13): ganti kalimat "Model direncanakan dilatih ..." dan "Detail konfigurasi pelatihan ... akan ditetapkan pada tahap eksperimen." dengan konfigurasi nyata: *class weight* seimbang $w_c = N/(2 n_c)$ (Normal 0,556, Aritmia 4,947), *optimizer* Adam *learning rate* $10^{-3}$, *batch* 64, *early stopping* memantau AUC validasi (*patience* 8, bobot terbaik dikembalikan), augmentasi *jitter* empiris dua salinan hanya pada DS1 (rujuk Subbab~\ref{subsec:augmentasi-jitter}). PTQ: 300 sampel representatif *stratified* dari DS1, kuantisasi penuh INT8 termasuk masukan dan keluaran. Paragraf "Distribusi kelas ... sangat timpang" dipertahankan tetapi kalimat "Strategi yang direncanakan meliputi ... atau penyeimbangan sampel" → pembobotan kelas tanpa *oversampling*. Ganti "Target ukuran model setelah kuantisasi berada di bawah 20 KB" → batas 25 KB. Setiap angka diberi `% sumber:`.

- [ ] **Step 9: Pipeline** (R14–R18):
  - Ring buffer: "partisi sekitar 4 MB dan ukuran \textit{payload} per detak $\approx$150 byte" → setiap entri 40 byte, kapasitas 27.000 entri sekitar 1,08 MB PSRAM, setara 4–7 jam. `% sumber: firmware/include/ecg_mqtt.h`.
  - Transmisi: tulis ulang subbab "Transmisi Real-Time dan Batch Offloading": semua hasil inferensi masuk antrean PSRAM terlebih dahulu, lalu dikirim dalam paket berisi paling banyak 50 rekaman. Saat koneksi normal antrean hampir kosong sehingga paket berisi satu atau beberapa rekaman, saat koneksi pulih antrean dikuras per 50 rekaman. PUBACK ditunggu tanpa menahan alur akuisisi. Ganti judul subbab menjadi `\subsubsection{Antrean Tunggal dan Pengiriman \textit{Batch}}`.
  - Half-open: tambah kalimat Nagle dimatikan (`setNoDelay`) dan mode hemat daya WiFi dinonaktifkan agar konfirmasi tidak tertahan.
  - Payload: tabel field tetap; kolom ts "dicuplik dari RTC internal" → "waktu kejadian detak, dari jam sistem (\textit{gettimeofday}) yang disinkronkan dan posisi R-peak". Kalimat "estimasi satu paket JSON ... sekitar 100--150 byte" → sekitar 320 byte per rekaman. "dikirimkan \textit{window} 250 sampel" → 256.
  - Gerbang kualitas (R3): sesudah tabel payload, tambah paragraf: fase calibrating (stabilisasi 10 menit, lalu interval RR 300–1500 ms dan $|\Delta RR| \leq 200$ ms stabil selama 30 detik) sebelum CNN dijalankan, lalu gerbang ayunan sinyal per detak. Kriteria RR hanya gerbang masuk, tidak ditegakkan terus karena akan membungkam aritmia. `% sumber: model/CLAUDE.md HW-6`.

- [ ] **Step 10: Dashboard.** Cocokkan Tabel widget dengan `dashboard/dashboard_ekg.json` (cari nama widget dan *data key*). Ubah baris yang tidak cocok sesuai berkas. Kalau semua cocok, biarkan.

- [ ] **Step 11: Tabel rencana pengujian** (R20, R21): di Tabel "Rencana pengukuran pada pengujian model", kolom Target Indikatif:
  - Kualitas model: "\textit{Recall} kelas Aritmia tinggi" → "Dilaporkan pada \textit{threshold} hasil kalibrasi data validasi (F1 maksimum)".
  - Dampak kuantisasi: "Penurunan metrik kecil" → "$|\Delta \textit{recall}| < 0{,}02$".
  - Ukuran model: "Muat di \textit{flash} perangkat" → "$<$ 25 KB".
  - Konsumsi daya: "Hemat daya untuk operasi berkelanjutan" → "Dilaporkan per mode operasi".
  - Tambah satu baris sebelum baris Latensi: Aspek "Kesetaraan preprocessing dan inferensi" | Metrik "Selisih keluaran perangkat terhadap Python" | Cara "\textit{Golden reference} diputar ulang di perangkat" | Target "Identik dalam toleransi satu kuantum INT8".
  - Hapus komentar ARSIP cross-dataset di dalam tabel (lima baris berawalan `%`) dan ganti dengan baris aktif: Aspek "Generalisasi lintas basis data" | Metrik "F1 dan \textit{recall} kelas S" | Cara "Evaluasi \textit{held-out} pada SVDB dan INCART setelah \textit{resample} 360 Hz" | Target "Dilaporkan sebagai pembanding ablasi".
  - Di teks jalur Pengujian Model: hapus pembungkus `\iffalse`/`\fi` paragraf arsip INCART/SVDB bila ada, tulis ulang konsisten dengan Step 6.
  - Pastikan subsection rencana pengujian ber-label `\label{sec:rencana-pengujian}` (sudah ada di proposal). Tabel pipeline tidak diubah.

- [ ] **Step 12: Pembersihan kala.** `grep -nE "akan |direncanakan" bab3.tex`: ubah setiap kemunculan yang menyatakan rencana menjadi deskripsi rancangan yang berlaku, kecuali di dalam subbab Rencana Pengujian (boleh "dilakukan").

- [ ] **Step 13: Verifikasi baku + Cek gaya (`bab3`).** Expected bersih. Laporkan daftar label placeholder yang dibuat.

---

### Task 5: Plot data ke `buku-pa/gambar` lewat skrip export

**Files:**
- Modify: `scripts/export_artifacts.sh` (blok langkah 2)
- Hasil: `laporan/buku-pa/gambar/*.png`

- [ ] **Step 1: Regenerasi plot segmentasi** yang masih window 250:

```bash
cd /home/mrrizaldi/dev/projek-akhir/model && make plot1seg REC=100
ls -l --time-style=+%Y-%m-%d artifacts/metrics/fase1_segment_100.png
```

Expected: tanggal file = hari ini.

- [ ] **Step 2: Ubah langkah 2 skrip export** menjadi:

```bash
# 2) figure final -> laporan/<projek>/gambar/   (opt-in)
#    LAPORAN_PROJ memilih projek tujuan (default buku-pa; proposal-pa = arsip).
if [[ "${1:-}" == "--laporan" ]]; then
  DEST="$ROOT/laporan/${LAPORAN_PROJ:-buku-pa}/gambar"
  echo "==> figure -> $DEST"
  mkdir -p "$DEST"
  for f in fase0_100 fase1_100 fase1_segment_100 pantompkins_100 \
           fase5_training fase6_confusion_fp32 fase7_confusion_int8 \
           jitter/jitter_residu jitter/sweep_jitter_dasar \
           akuisisi/akuisisi_20260915-1130 akuisisi/akuisisi_20260915-1205; do
    src="$MODEL_DIR/artifacts/metrics/$f.png"
    [[ -f "$src" ]] && cp -v "$src" "$DEST/" || echo "    lewat: $f.png belum ada"
  done
  [[ -f "$ROOT/dashboard/preview.png" ]] && cp -v "$ROOT/dashboard/preview.png" "$DEST/dashboard_preview.png"
else
```

- [ ] **Step 3: Jalankan export.**

```bash
cd /home/mrrizaldi/dev/projek-akhir && bash scripts/export_artifacts.sh --laporan
ls laporan/buku-pa/gambar
```

Expected: 12 berkas png (11 metrik + dashboard_preview.png), tidak ada "lewat:". Langkah 1 skrip (export model .h) ikut berjalan dan tidak boleh mengubah `firmware/include/model_int8.h`: cek `git diff --stat firmware/include/model_int8.h` kosong. Kalau berubah, `git checkout firmware/include/model_int8.h` dan laporkan.

- [ ] **Step 4: Pastikan `akuisisi_20260915-1205` adalah rekaman GAGAL** (ayunan kecil): buka gambarnya (Read tool). Kalau ternyata berhasil, pilih rekaman lain bertanggal 2026-09-15 sesudah 11:30 yang ayunannya kecil, ganti nama di skrip, ulangi Step 3. Laporkan pilihan akhir.

---

### Task 6: Bab 4 bagian A — pembuka, 4.1–4.5, tabel perubahan

**Files:**
- Modify: `laporan/buku-pa/bab/bab4.tex`
- Sumber: `docs/pola-laporan-pa/08-bab4-pa-kita.md` §1, §3, §4 pembuka; tabel R1–R22 di plan ini; `model/CLAUDE.md`; `firmware/platformio.ini`; `dashboard/docker-compose.yml`; `model/.python-version`

- [ ] **Step 1: Paragraf pembuka bab** (templat 08 §1), isi ringkasan lingkup progres: diukur penuh = model DS2, kuantisasi, kesetaraan, kinerja di perangkat, *pipeline* dengan sumber sinyal *replay*. Parsial = akuisisi sinyal tubuh. Ditunda = konsumsi daya, PCB rev2.

- [ ] **Step 2: 4.1 Parameter Eksperimen** (`\section{Parameter Eksperimen}`): tabel `longtable` kolom Kategori | Metrik | Target | Alasan/acuan, tujuh kategori a–g sesuai 08 §3 4.1, target diambil dari Tabel rencana Bab 3 versi Task 4 (rujuk `\ref{tab:pengujian-model}` dan `\ref{tab:pengujian-pipeline}`). Lalu `\subsection{Lingkup Tahap Progres}` dengan tabel tiga kolom Diukur penuh | Fungsional/parsial | Ditunda beserta alasan (08 §3).

- [ ] **Step 3: 4.2 Karakteristik Data** (`\section{Karakteristik Data}`), lima butir `\subsubsection` a–e sesuai 08 §3 4.2. Tabel himpunan data diisi dari: DS1/DS2 dari `model/CLAUDE.md` Fase 3 (DS1 152.904 beat 10,1\%, DS2 49.656 beat 11,0\%), TEST-B/C dari decision "Database LATIH" (85.812 beat, 39 pasien). Jumlah beat VAL: hitung dari data bila tersedia, kalau tidak cukup sebut "lima record" tanpa jumlah beat. Butir b (data primer): hitung jumlah rekaman `ls /home/mrrizaldi/dev/projek-akhir/model/data/recordings/*.csv | wc -l` dan sebut subjek dengan kode anonim S01 (penulis memastikan nanti). Butir c (replay) dan d (penyelarasan) dari 08.

- [ ] **Step 4: 4.3 Tempat Ujicoba**: laboratorium (nama lab belum ditetapkan, tulis "laboratorium" tanpa nama), alasan lingkungan terkontrol, broker ThingsBoard di komputer lokal, WiFi lokal. Sebagian pengembangan model dilakukan di komputer pribadi.

- [ ] **Step 5: 4.4 Waktu Ujicoba**: tabel kegiatan + rentang dari 08 §3 4.4, dengan kalimat bahwa tanggal mengikuti catatan pengembangan. Tambah kalimat pembatas: data hasil pada bab ini diambil sampai 19 September 2026 (tanggal HW-6 terverifikasi, `% sumber: git log 33d9a80`), dan pengujian lanjutan dilaporkan pada tahap berikutnya.

- [ ] **Step 6: 4.5 Spesifikasi Peralatan Ujicoba**: dua tabel `[!ht]` (perangkat keras, perangkat lunak). Versi perangkat lunak diambil dengan perintah, lalu ditulis persis:

```bash
cd /home/mrrizaldi/dev/projek-akhir/model && .venv/bin/python -c "import tensorflow,numpy,scipy,wfdb;print(tensorflow.__version__,numpy.__version__,scipy.__version__,wfdb.__version__)"
cat .python-version
cd ../firmware && pio pkg list -e esp32-s3 2>/dev/null | head -20
grep -n "image:" ../dashboard/docker-compose.yml
```

Spesifikasi komputer: `lscpu | grep -E "Model name|^CPU\(s\)"` dan `free -h | head -2`. Tambah `\subsection{Validitas Pengukuran}` satu paragraf + butir (08 §3 4.5): reset board saat port serial dibuka, resolusi `time()` diganti `gettimeofday`, ukuran build bergantung kredensial WiFi, ohmmeter pada rangkaian bertegangan. Setiap butir: masalah → penanganan. `% sumber: model/CLAUDE.md bagian Jebakan`.

- [ ] **Step 7: Pembuka 4.6** (`\section{Hasil Eksperimen}`): satu paragraf pengantar (hasil disusun per tujuan) + tabel `[!ht]` "Perubahan rancangan dari proposal" dengan kolom Aspek | Proposal | Realisasi | Alasan, berisi baris R5, R11, R12 (augmentasi), R1, R4, R10, R14, R15, R9 dari tabel plan ini (ringkas, satu baris per butir).

- [ ] **Step 8: Verifikasi baku + Cek gaya (`bab4`).**

---

### Task 7: Bab 4 bagian B — 4.6.1 Jalur Preprocessing Real-Time (Tujuan 1)

**Files:**
- Modify: `laporan/buku-pa/bab/bab4.tex` (tambahkan di akhir)
- Sumber: `docs/pola-laporan-pa/08-bab4-pa-kita.md` §4 4.6.1; `model/CLAUDE.md` Fase 0–1, HW-1..HW-5, Fase 6b; `model/artifacts/metrics/fase6b_segmentasi_deteksi.csv`; `firmware/test/golden_ref.h`; `model/docs/akuisisi-walkthrough.md`

- [ ] **Step 1:** `\subsection{Jalur Preprocessing \textit{Real-Time} (Tujuan 1)}` + paragraf pengantar yang menyebut Tujuan 1.
- [ ] **Step 2: butir a–e** sebagai `\subsubsection` sesuai tabel 08 §4.6.1, masing-masing pola P15 (03). Gambar yang dipakai (sudah ada di `gambar/` dari Task 5): `fase0_100.png` (R-peak), `fase1_100.png` (filter), `fase1_segment_100.png` (segmentasi), `pantompkins_100.png`, `akuisisi_20260915-1130.png` dan rekaman gagal dari Task 5. Placeholder: `fig:alur-isr` (kartu dari 08 §6).
- [ ] **Step 3: Tabel kesetaraan** (format 08): jalankan `cd /home/mrrizaldi/dev/projek-akhir/firmware && pio test -e native 2>&1 | tail -15` dan laporkan hasilnya di teks (jumlah test lulus). Angka probabilitas PC vs perangkat ambil dari `model/CLAUDE.md` HW-1 (satu beat beda satu kuantum: 0,0820 vs 0,0859). Kalau angka per beat lengkap tidak tersedia di berkas, tabel hanya memuat baris yang tersedia dan teks menyatakan "seluruh beat golden cocok kecuali satu yang berbeda satu kuantum".
- [ ] **Step 4: Butir d (segmentasi di perangkat)** pakai `fase6b_segmentasi_deteksi.csv`, dan tulis jelas bahwa angka ini diukur pada **model versi window 250** (`[lama]`), karena belum diukur ulang dengan model berlaku.
- [ ] **Step 5: Butir e (akuisisi)**: tabel kualitas rekaman (format 08) dari `model/CLAUDE.md` HW-5 (rekaman 15 Sep 11:30: ayunan 3128 counts, dengung 3,3\%, 64 R-peak dalam 47,2 detik, BPM wajar 100\%; enam rekaman sesudahnya 40–55 counts). Konversi mV: 0,757 mV/count dibagi gain ±1100 untuk amplitudo input. Narasi rantai eliminasi dan status **Sebagian**.
- [ ] **Step 6: Verifikasi baku + Cek gaya (`bab4`).**

---

### Task 8: Bab 4 bagian C — 4.6.2 Jalur Model TinyML On-Device (Tujuan 2)

**Files:**
- Modify: `laporan/buku-pa/bab/bab4.tex` (tambahkan di akhir)
- Sumber: 08 §4.6.2; `model/artifacts/metrics/fase6_metrics_fp32.csv`, `fase6_per_record_fp32.csv`, `fase7_delta.csv`, `fase5_threshold_sweep.csv`, `jitter/*.csv`, `ablasi/ablasi.csv`, `ablasi/lintas_db.csv`; `model/CLAUDE.md`

- [ ] **Step 1:** `\subsection{Jalur Model TinyML \textit{On-Device} (Tujuan 2)}` + pengantar.
- [ ] **Step 2: Butir a–g** sesuai 08 §4.6.2. Gambar dari `gambar/`: `fase5_training.png`, `fase6_confusion_fp32.png`, `fase7_confusion_int8.png`, `jitter_residu.png`, `sweep_jitter_dasar.png`. Placeholder (plot belum ada skripnya): `fig:per-pasien`, `fig:ablasi` — kartu jenis "plot data", bahan repo = CSV terkait, catatan "skrip belum ada, tanyakan user".
- [ ] **Step 3: Tabel CM + metrik** dari `fase6_metrics_fp32.csv` (TP, FN, FP, TN persis; recall, precision, specificity, F1, AUC empat desimal dengan koma). Rumus tidak ditulis ulang, rujuk persamaan di Subbab~\ref{subsec:evaluasi-metrik}. Sebaran per pasien dari `fase6_per_record_fp32.csv`: hitung median recall (abaikan record tanpa aritmia, sebutkan aturannya) dengan

```bash
cd /home/mrrizaldi/dev/projek-akhir/model && .venv/bin/python -c "
import csv,statistics as s
r=[x for x in csv.DictReader(open('artifacts/metrics/fase6_per_record_fp32.csv')) if int(x['n_aritmia'])>0]
v=sorted((float(x['recall']),x['record']) for x in r)
print(len(r),'record ber-aritmia; median recall',round(s.median([a for a,_ in v]),4)); print('terendah',v[:3])"
```

- [ ] **Step 4: Tabel ablasi** dari keluaran

```bash
cd /home/mrrizaldi/dev/projek-akhir/model && .venv/bin/python scripts/ringkas_ablasi.py
.venv/bin/python scripts/ringkas_ablasi.py --csv artifacts/metrics/ablasi/lintas_db.csv
```

Pilih baris yang menentukan keputusan (bersih, jitter, w128, w112, hos, w128s3, fb_svdb, fb_incartdb, fd_rr, fd_both, g_lr1e4, t8_lr1e3, t8_lr1e4), kolom F1 rerata ± setengah-rentang, recall S, AUC, vonis (dikunci/ditolak/bukan sinyal) mengikuti decision table `model/CLAUDE.md`. Baris ber-seed < 3 tidak dimasukkan. Tulis ambang bermakna 0,04 F1. Pertukaran LR dengan pola trade-off (03 P16).

- [ ] **Step 5: Tabel delta INT8** dari `fase7_delta.csv` (semua baris kecuali threshold), dan vonis terhadap target $|\Delta recall| < 0{,}02$.
- [ ] **Step 6: Tabel sumber daya** (kolom Besaran | Nilai | Kondisi build | Target) dari `model/CLAUDE.md` HW-1 (26,6 ms/detak, arena 12.948 B, heap bebas 312.396 B) dan HW-6 (RAM 36,9\%, Flash 13,5\% dengan kredensial WiFi terisi), plus beban HW-3/HW-4. Ukuran model 22,94 KB vs 25 KB.
- [ ] **Step 7: Butir g (daya)**: status belum diukur, rencana mode p0–p3 dari `model/docs/arsip/2026-09-16-daya-design.md` (sebut keempat mode), pembacaan INA219 lewat I2C belum dikerjakan (Task 3 rencana implementasi daya; rencana itu dihapus 13 Okt 2026, salinan di tag git `pra-bersih`).
- [ ] **Step 8: Verifikasi baku + Cek gaya (`bab4`).**

---

### Task 9: Bab 4 bagian D — 4.6.3 Jalur Pipeline Edge-to-Cloud Resilien (Tujuan 3)

**Files:**
- Modify: `laporan/buku-pa/bab/bab4.tex` (tambahkan di akhir)
- Sumber: 08 §4.6.3; `model/CLAUDE.md` HW-6 + jebakan jaringan; `model/docs/mqtt-walkthrough.md`; `dashboard/`

- [ ] **Step 1:** `\subsection{Jalur \textit{Pipeline Edge-to-Cloud} Resilien (Tujuan 3)}` + pengantar.
- [ ] **Step 2: Butir a–e** (08 §4.6.3). Gambar: `dashboard_preview.png` dari `gambar/`. Placeholder: `fig:state-gerbang`, `fig:latensi`, `fig:bufer` (kartu 08 §6).
- [ ] **Step 3: Tabel 6 target** (kolom Aspek | Metrik | Target | Ulangan 1 | Ulangan 2 | Status) dari `model/CLAUDE.md` HW-6: PDSR 100\% / 99,2\%; latensi median 939 / 1.108 ms; p95 1.404 / 3.304 ms; data hilang 0; flush sekitar 24 detik; duplikat ts 0; target dari tabel pipeline Bab 3. Bila `model/docs/mqtt-walkthrough.md` memuat angka entri bufer, isi juga baris pemenuhan bufer, kalau tidak tulis status "tidak *overflow*" tanpa angka.
- [ ] **Step 4: Tabel dekomposisi latensi**: sisi alat 869 ms (89\%) = kadens deteksi 1 detik + 356 ms *post-window*; jaringan+cloud ±130 ms; broker 1,1 ms median (diukur dengan `dashboard/probe_rtt.py`). Paragraf ekor p95 = retransmisi TCP (RTO 1-2-4 detik) karena kontensi WiFi, penanganan `setNoDelay` + `WiFi.setSleep(false)`, dan alasan sisa ekor tidak dikejar (pola trade-off P16).
- [ ] **Step 5:** Tekankan bahwa seluruh uji ini memakai sumber sinyal *replay* (record 208) karena akuisisi tubuh belum stabil, dan bahwa *replay* melewati gerbang RR dengan pengumuman (record 208 aritmik).
- [ ] **Step 6: Verifikasi baku + Cek gaya (`bab4`).**

---

### Task 10: Bab 4 bagian E — 4.7 Analisis Hasil Eksperimen

**Files:**
- Modify: `laporan/buku-pa/bab/bab4.tex` (tambahkan di akhir)
- Sumber: 08 §5; isi `bab4.tex` hasil Task 6–9; `docs/pola-laporan-pa/07-penerapan-ke-pa-kita.md` §3

- [ ] **Step 1:** `\section{Analisis Hasil Eksperimen}` + pengantar satu paragraf.
- [ ] **Step 2: 4.7.1–4.7.3** satu `\subsection` per tujuan, pola P16 (klaim → bukti angka dengan `\ref` ke tabel Task 6–9 → mekanisme → kaitan tujuan → batasan) dan satu kalimat vonis Tercapai / Sebagian Tercapai / Tercapai dengan sumber *replay*.
- [ ] **Step 3: Tabel ketercapaian** (`[!ht]`, kolom Tujuan | Target | Hasil | Status | Justifikasi) — draf status 08 §5, angka mengutip tabel di bab ini (jangan menulis angka baru).
- [ ] **Step 4: 4.7.4 Perbandingan dengan Penelitian Terkait**: paragraf P9 + tabel kecil hanya untuk penelitian yang skemanya tertulis di Bab 2 (penelitian ini, `zambrano_2026`, `mulyawan_2026`). Jelaskan baseline accuracy tebak-Normal. Jangan menyebut angka paper yang tidak ada di Bab 2.
- [ ] **Step 5: 4.7.5 Keterbatasan dan Status \textit{Proof of Concept}** (08 §5): subjek terbatas dan anonim, akuisisi tubuh sebagian, daya belum diukur, p95 latensi tidak stabil, model biner, recall kelas S rendah sebagai pertukaran yang disengaja, uji *pipeline* memakai *replay*. TLS tidak disebut.
- [ ] **Step 6: Verifikasi baku + Cek gaya (`bab4`).**

---

### Task 11: Bab 5 Penutup (versi progres)

**Files:**
- Modify (timpa stub): `laporan/buku-pa/bab/bab5.tex`
- Sumber: `docs/pola-laporan-pa/07-penerapan-ke-pa-kita.md` §4 Bab 5; `bab4.tex`

- [ ] **Step 1:** Kalimat pembuka bab + `\section{Kesimpulan}`: paragraf pembuka "berdasarkan perancangan, implementasi, dan eksperimen tahap progres", lalu 3–4 temuan bernomor naratif ("Pertama, ... Kedua, ...") dipilih dari 07 §4 Bab 5 (wajib: ketidakcocokan diam-diam TFLM yang tertangkap golden; augmentasi jitter sebagai regularisasi; 87\% latensi di sisi alat (869/(869+130); "89%" di catatan tidak tereproduksi); opsional: telemetri akuisisi menipu). Setiap temuan menyebut angka yang SAMA dengan Bab 4 (salin dari `bab4.tex`, bukan dari sumber lain). Tutup dengan satu paragraf status ketercapaian per tujuan (sama dengan tabel ketercapaian).
- [ ] **Step 2:** `\section{Saran}` `enumerate` berjudul (pola P19 progres): akuisisi sinyal tubuh dengan PCB rev2; pengukuran daya per mode lewat INA219; uji gerbang kualitas penuh dengan sinyal tubuh; peninjauan ulang pertukaran *learning rate* bila fokus bergeser dari kelas S; kernel ESP-NN bila daya menjadi kendala; pengukuran ulang segmentasi di perangkat dengan model yang berlaku.
- [ ] **Step 3: Verifikasi baku + Cek gaya (`bab5`).**

---

### Task 12: Abstrak versi progres

**Files:**
- Modify: `laporan/buku-pa/bab/abstrak.tex`

- [ ] **Step 1:** Ganti paragraf abstrak (baris setelah komentar TODO, sebelum "Kata kunci") dengan 200–280 kata mengikuti struktur abstrak hasil (01 §3): masalah dan urgensi → kesenjangan → tujuan → rancangan (preprocessing di MCU, CNN hibrida INT8, *pipeline* MQTT dengan bufer PSRAM) → hasil tahap progres dengan angka yang SAMA dengan Bab 4 (recall, F1, AUC DS2 float32; ukuran INT8; delta recall; latensi inferensi per detak; PDSR dan latensi median *pipeline* dengan *replay*) → status (akuisisi tubuh dan daya pada tahap berikutnya). Hapus komentar `% TODO`. Kata kunci tetap.
- [ ] **Step 2: Verifikasi baku + Cek gaya (`abstrak`).**

---

### Task 13: QA menyeluruh

**Files:** baca semua `laporan/buku-pa/bab/*.tex`, ubah hanya untuk memperbaiki temuan.

- [ ] **Step 1: Build bersih** (Verifikasi baku). Satu-satunya `Citation undefined` yang boleh = `dias_2021`.
- [ ] **Step 2: Cek gaya semua bab** (ulang Cek gaya untuk bab1..bab5 dan abstrak).
- [ ] **Step 3: Konsistensi angka.** Untuk angka kunci berikut, `grep -rn` di `bab/` dan pastikan nilainya sama di setiap kemunculan: 0,6996 / 0,6594 / 0,9334 (DS2 float32), 22,94 (KB), 26,6 (ms), 0,0108 (delta), 100 dan 99,2 (PDSR), 939 dan 1.108 (ms). Perbaiki yang beda ke nilai sumber.
- [ ] **Step 4: Sisa usang.** `grep -rnE "250 sampel|90 sampel|160 sampel|20 KB|0,5 diklasifikasikan|Dropout|ESP-NN" laporan/buku-pa/bab/` → setiap kemunculan harus disengaja (mis. tabel perubahan di 4.6). Laporkan.
- [ ] **Step 5: Placeholder.** `grep -rn "PLACEHOLDER-GAMBAR" laporan/buku-pa/bab/` → daftar label + jenis untuk laporan akhir ke user.
- [ ] **Step 6: Benang merah.** Pastikan setiap butir Tujuan (Bab 1) punya subbab di 4.6, baris di tabel ketercapaian 4.7, dan kalimat di 5.1.
- [ ] **Step 7:** Laporkan ringkasan: jumlah halaman PDF (`pdfinfo output/main.pdf | grep Pages`), daftar placeholder, CITE-MISSING, keputusan yang perlu user.
