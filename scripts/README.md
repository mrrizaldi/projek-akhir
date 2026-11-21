# scripts/ — otomasi lintas-komponen

| Skrip | Fungsi |
|---|---|
| `export_artifacts.sh` | Sinkronisasi artefak produsen → konsumen: `model_int8.tflite` → `firmware/include/model_int8.h`; dengan `--laporan`, figure final dari `model/artifacts/metrics/` dan `dashboard/preview.png` → `laporan/<projek>/gambar/` |

```bash
bash scripts/export_artifacts.sh                                 # model -> firmware
bash scripts/export_artifacts.sh --laporan                       # + figure -> laporan/buku-pa/gambar/
LAPORAN_PROJ=proposal-pa bash scripts/export_artifacts.sh --laporan
AKUISISI="akuisisi/akuisisi_<tgl-jam>" bash scripts/export_artifacts.sh --laporan   # + grafik rekaman resmi
```

Langkah figure tidak berjalan tanpa `--laporan` karena `laporan/` bersifat
read-only tanpa konfirmasi. Artefak tidak disalin manual. `LAPORAN_PROJ`
memilih projek tujuan (bawaan `buku-pa`; `proposal-pa` = arsip). `AKUISISI`
berisi daftar grafik rekaman tambahan (data resmi = sesi 22 Okt 2026 siang, grafik R1 sudah ada di daftar tetap; relatif terhadap
`model/artifacts/metrics/`, tanpa `.png`, dipisah spasi) yang ikut disalin.

## Indeks berkas lewat browser

`sajikan.py` menyalakan server lokal (stdlib, tanpa dependency) yang
menyajikan seluruh repo. Halaman `/` mendaftar semua `.pdf`, `.docx`, dan
`.pptx` di repo (kecuali `.git`, `.venv`, `node_modules`, `.pio`),
dikelompokkan per folder. Folder dengan berkas paling baru tampil paling
atas, jadi PDF yang baru di-`make pdf` langsung ada di urutan pertama.
Daftar dibaca ulang setiap halaman dimuat, tanpa langkah build. Tautan
terbuka di tab baru.

1. Jalankan dari akar repo:

   ```bash
   python3 scripts/sajikan.py          # port bawaan 8700
   python3 scripts/sajikan.py 9000     # port lain
   ```

2. Buka `http://127.0.0.1:8700/` di browser. PDF terbuka di viewer browser;
   `.docx`/`.pptx` terunduh.
3. Hentikan dengan `Ctrl+C`.

Folder `laporan/rilis/<proyek>/vN` dengan N > 0 punya tautan "banding vN-1
dan vN" di judul grupnya. Tautan itu membuka halaman `/banding` berisi dua PDF
berdampingan. Perubahan teks per kata ada di `banding-vM-vN.pdf` di folder yang
sama. Parameter `lama` dan `baru` pada `/banding` hanya menerima PDF di dalam
repo.

Server hanya mendengar di `127.0.0.1`, jadi tidak terjangkau dari perangkat
lain di jaringan. Selain berkas di indeks, path apa pun di repo bisa dibuka
langsung lewat URL (`/model/artifacts/metrics/...png`).

## Pemeriksa

`cek_komentar.py` menegakkan aturan TANPA KOMENTAR KODE (`CLAUDE.md` root,
Aturan keras 5). Memindai berkas tracked git dan keluar dengan kode 1 sambil
mencetak `berkas:baris: isi` untuk tiap komentar yang ditemukan.

| Jenis | Yang dilarang | Yang boleh |
|---|---|---|
| C/C++ (`.c .cpp .h .hpp`) | `//`, `/* */` | `//` atau `/*` di dalam string/char literal |
| Python (`.py`) | `#`, docstring modul/kelas/fungsi | shebang baris 1, baris `coding` |
| Shell (`.sh`, `.githooks/*`) | `#` di awal kata di luar string | shebang baris 1, `$#`, `${#v}`, isi heredoc |
| `platformio.ini` | baris diawali `;` atau `#` | — |
| Makefile | `#` (termasuk `##` judul seksi) | `##` deskripsi di baris target (`make help`) |

Dikecualikan: `laporan/`, `docs/`, `*.md`, `*.tex`, folder `arsip/`, dan berkas
non-kode lain.

```bash
python3 scripts/cek_komentar.py                       # seluruh repo
python3 scripts/cek_komentar.py firmware/src model/x.py  # sebagian (folder/berkas)
python3 scripts/cek_komentar.py --uji                 # uji mandiri pemeriksa
```

CI menjalankannya di `.github/workflows/cek.yml` (job `komentar`), bersama
`pio test -e native` (job `firmware-native`). Pytest model tidak ikut karena
butuh data MIT-BIH yang tidak di-commit.

Hook lokal opsional memeriksa berkas yang di-stage sebelum commit. Aktifkan
sekali per clone:

```bash
git config core.hooksPath .githooks
```

Batasan: hook membaca isi berkas di working tree, bukan isi yang di-stage;
raw string C++ (`R"(...)"`) dan pemisah digit (`1'000`) belum dikenali tokenizer C.

## Pemeriksa tabel dan narasi laporan

`cek_tabel.py` memeriksa tabel LaTeX dan paragraf penjelasnya di laporan PA
(skill `tabel-pa` dan `tulis-tanpa-slop`). Galat keluar dengan kode 1, sedangkan
saran hanya dicetak (`--ketat` membuat saran ikut gagal). Format keluaran:
`berkas:baris: [KODE tingkat] pesan`.

| Kode | Tingkat | Yang diperiksa |
|---|---|---|
| `T-BAB` | galat | tabel di Bab 1 atau Bab 5 |
| `T-GRID` | galat | `booktabs`, padahal panduan PENS memakai grid penuh |
| `T-HEADER` | galat | header tanpa `\rowcolor{headgray}` |
| `T-CAPTION` | galat/saran | caption hilang atau di bawah tabel (galat), berakhir titik, memuat kurung, > 15 kata (saran) |
| `T-LEBAR` | galat | jumlah lebar `p{}` + `\tabcolsep` melebihi lebar teks (A4 14 cm) |
| `T-RUJUK` | galat/saran | label tidak pernah dirujuk (galat) atau baru dirujuk sesudah tabel (saran) |
| `T-FLOAT` | saran | `[H]` |
| `T-SEL` | saran | sel > 20 kata |
| `T-CATATAN` | saran | baris `\multicolumn` selebar tabel berisi catatan panjang |
| `T-SATUAN` | saran | satuan diulang di ≥ 3 sel satu kolom |
| `T-DESIMAL` | saran | jumlah desimal tidak seragam dalam satu kolom |
| `T-ISIAN` | saran | isian "Sama", "idem", "Tidak diulang", "Konfigurasi sama" |
| `N-PEMBUKA` | saran | penjelas berurutan dengan pembuka sama, "Berdasarkan Tabel" > 3 per bab |
| `N-ULANG` | saran | penjelas mengulang > 50% angka tabel (tabel ≥ 5 angka) |
| `N-PANJANG` | saran | penjelas > 180 kata |
| `N-KALIMAT` | saran | kalimat > 35 kata (diringkas per bab, 5 terpanjang) |
| `N-GAYA` | saran | titik koma atau em dash di paragraf |
| `N-SEHINGGA` | saran | "sehingga" > 5 per 1.000 kata |

```bash
python3 scripts/cek_tabel.py                                 # laporan/buku-pa/bab/bab*.tex
python3 scripts/cek_tabel.py laporan/buku-pa/bab/bab4.tex    # satu bab
python3 scripts/cek_tabel.py --tanpa-prosa                   # tabel dan penjelasnya saja
python3 scripts/cek_tabel.py --kertas a5 <berkas-bab.tex>    # lebar teks A5
python3 scripts/cek_tabel.py --uji                           # uji mandiri pemeriksa
```

## Pengunduh daftar pustaka

`unduh_pustaka.py` mengunduh PDF untuk entri `laporan/*/referensi.bib` ke
`laporan/pustaka/<kunci-bib>.pdf` (folder di-ignore git: PDF penerbit tidak
boleh masuk repo). Sumber: DOI → Unpaywall → URL PDF open access; entri
`@misc` yang `url`-nya langsung `.pdf` diunduh apa adanya. Berkas yang sudah
ada dilewati, jadi aman dijalankan berulang. Entri tanpa DOI di bib proposal
(beku) diberi DOI lewat tabel `DOI_TAMBAHAN` di skrip, hasil pencarian judul
di Scopus (15 Okt 2026).

```bash
cd model && .venv/bin/python ../scripts/unduh_pustaka.py   # python3 biasa juga bisa, stdlib saja
```

Keluaran: baris `[unduh]`, `[ada]`, atau `[gagal]` per kunci, lalu rekap.
Kode keluar 1 bila ada yang gagal. Skrip ini hanya menjangkau penerbit yang
mengizinkan unduhan otomatis; sisanya diunduh manual lewat browser dengan
akun kampus, lalu disimpan dengan nama `<kunci-bib>.pdf` di folder yang sama.

Kondisi 15 Okt 2026 (48 entri gabungan tiga bib):

| Status | Entri |
|---|---|
| Terunduh otomatis (10) | `al_quayed_2026`, `david_2021`, `escobedo_2026`, `jacob_2018`, `kim_2023`, `li_2020`, `reoukadji_2025`, `saito_2015`, `tipparaju_2021`, `zambrano_2026` |
| Terunduh lewat browser Chrome headed (4; MDPI, IEEE OA, Nature) | `xiao_2023`, `orphanidou_2015`, `lueken_2023`, `joutsen_2024` (tiga terakhir belum di bib, bahan bedah paper) |
| Terunduh dari repositori institusi penulis (1; 20 Okt 2026) | `yaacoub_2020` (AUB ScholarWorks, `https://scholarworks.aub.edu.lb/server/api/core/bitstreams/eb7f173e-d502-4682-9b35-c2b2acfe60bd/content`) |
| Elsevier/ScienceDirect: CAPTCHA, unduh manual (18; 8 di antaranya open access) | `tinyml_iot_review`, `resilient_edge_cloud`, `mekhfioui_2025`, `xie_2021`, `karri_2023`, `laiu_2026`, `crespi_2026`, `sheeba_rani_2026`, `chowdhury_2023`, `dias_2021`, `safdar_2023`, `bui_2021`, `elhadad_2025`, `khan_2025`, `fahoum_2026`, `xiang_2026`, `kumaran_2026`, `verma_2024` |
| IEEE berbayar, perlu akun kampus (6) | `pan_tompkins_1985`, `moody_mark_2001`, `dechazal_2004`, `shi_2016`, `kiranyaz_2016`, `lee_2013` |
| Open access tetapi diblokir untuk otomasi (3) | `yahyati_2025` (IEEE Access), `goldberger_2000_physionet` (AHA), `skorinkapov_2010` (Wiley) |
| Springer berbayar (1) | `bahrami_2025` |
| Bukan artikel: buku, tesis, standar, halaman web (8) | `ecg_goldberger`, `sornmo_laguna_2005`, `mulyawan_2026`, `aami_ec57_2012`, `iec_60601_2_27_2011`, `who_cvd`, `oasis_mqtt5`, `analog_ad8232` |

MDPI, IEEE open access, dan Unpaywall menolak `curl`/`urllib` dengan 403;
yang berhasil untuk mereka adalah unduhan lewat browser sungguhan (Chrome
headed), bukan headless. CAPTCHA ScienceDirect/AHA/Wiley tidak dilewati.

Paper berbayar yang ditandai Unpaywall `closed` kadang punya salinan legal
di repositori institusi penulis (DSpace, mis. AUB ScholarWorks, QSpace).
Cari judulnya di sana sebelum meminta akun kampus. Pada DSpace 7, berkas
diambil lewat `/server/api/core/bitstreams/<uuid>/content`.

## Pemeriksa kemiripan DOCX terhadap PDF

`cek_docx.py` membandingkan PDF hasil pdfLaTeX dengan DOCX hasil WordCraft per
halaman. DOCX dirender ulang ke PDF lewat `wordcraft-cli convert` di folder
sementara, lalu kedua PDF dibaca dengan `pdftotext`. Sebuah halaman dianggap
sama bila enam kata pertamanya sama (huruf kecil, tanda baca dan nomor halaman
dibuang, kata terpenggal di akhir baris disambung). Keluaran berisi jumlah
halaman, halaman awal tiap bab beserta selisihnya, jumlah halaman yang berawal
sama, dan cuplikan lima halaman pertama yang berbeda. Kode keluar 0 hanya bila
jumlah halaman dan awal setiap halaman sama.

```bash
cd laporan/buku-pa
make pdf docx
make cek-docx                                  # memakai wordcraft-cli di PATH
make cek-docx WORDCRAFT=/path/ke/wordcraft-cli # binary lain, mis. hasil build branch
```

## Pemeriksa pola tulisan AI

`cek_slop.py` adalah pembungkus tipis atas
`~/.claude/skills/indonesian-antislop-writing/scripts/check_slop.py`. Sumber
pola, ambang, dan katalog ada di skill user itu (`references/catalog.md`);
repo ini tidak menyimpan salinannya. Opsi lama dipetakan: `--ringkas` ke
`--summary`, `--banding` ke `--compare`, `--uji` ke `--self-test`; argumen lain
diteruskan apa adanya dan kode keluarnya sama dengan pemeriksa asli. Bila skill
user tidak terpasang, pembungkus mencetak pesan dan keluar dengan kode 2.
Lingkungan tabel, gambar, persamaan, dan komentar `%` dilewati. Temuan bertingkat
`error` (kode keluar 1) dan `review`; `--compare` gagal bila angka, kunci
`\cite`/`\ref`/`\label`, atau baris komentar `%` berubah.

```bash
cd laporan/progres-pa-1
python3 ../../scripts/cek_slop.py --ringkas bab/bab2.tex bab/bab3.tex bab/bab4.tex
python3 ../../scripts/cek_slop.py bab/bab3.tex
python3 ../../scripts/cek_slop.py --banding /tmp/bab3.lama.tex bab/bab3.tex
python3 ../../scripts/cek_slop.py --uji
```

## cek_skill.py

`cek_skill.py` memeriksa struktur setiap skill di `.claude/skills/*/`
(`.claude/skills-arsip/` tidak diperiksa). Yang diperiksa:

- `SKILL.md`: frontmatter hanya `name` dan `description`, `name` sama dengan
  nama folder, `description` satu baris dan paling banyak 1.024 karakter,
  badan kurang dari 500 baris.
- `evals/<kasus>/`: `prompt.md` (frontmatter dan teks), `case.yaml`
  (`schema_version: "1.1"`, `name` sama dengan nama folder,
  `expected_outcome`), dan minimal satu `graders/*.md` berfrontmatter
  `type`, `focus`, `weight`.
- `triggers/evals.json`: daftar `{query, should_trigger}` dengan kelas true
  dan false.
- Skill yang tidak punya `evals/` atau `triggers/`, atau yang masih punya
  `eval.md`, dianggap galat. Opsi `--lewati-eval-lama` melewati pemeriksaan
  eval untuk skill yang masih memakai `eval.md` (masa transisi).

Kode keluar 1 bila ada galat. CI menjalankan `--uji` dan pemeriksaan tanpa opsi.

```bash
python3 scripts/cek_skill.py
python3 scripts/cek_skill.py --uji
```

## uji_pemicu.sh

`uji_pemicu.sh` mengukur apakah deskripsi sebuah skill memicu pada kueri yang
tepat dan tidak pada kueri lain, memakai `run_eval.py` dari skill-creator dan
`triggers/evals.json` milik skill. Jalannya terisolasi: konfigurasi Claude
sementara (`CLAUDE_CONFIG_DIR`) hanya berisi salinan `~/.claude/.credentials.json`,
dan proyeknya folder kosong, sehingga skill lain dan `CLAUDE.md` tidak ikut.
Salinan kredensial dihapus saat skrip selesai.

Prasyarat: `uv`, skill-creator di `~/.claude/skills` (folder `.trash` dilewati),
dan login aktif (`claude login`). Prasyarat yang kurang membuat skrip keluar
dengan kode 2 dan pesan.

```bash
scripts/uji_pemicu.sh .claude/skills/<skill> [.claude/skills/<skill2> ...]
```

Keluaran per skill: `nama=<skill> benar=<n>/<total>` dan `json=<path>`; JSON
lengkap dan log galat ada di folder sementara `$T/out/`. Satu kueri dijalankan
satu kali (`--runs-per-query 1`), jadi hasilnya sampel kecil dan bisa
bergeser antarjalan. Biaya: satu panggilan model per kueri, sekitar 20
panggilan per skill dengan 20 kueri, dan sekitar 25 detik.

Jebakan kebocoran: uji pemicu dapat meninggalkan berkas `*-skill-*` di
`~/.claude/commands` yang lalu terbaca sebagai perintah di sesi lain. Skrip
berhenti dengan kode 3 bila folder itu sudah memuatnya sebelum mulai, dan
memeriksa lagi di akhir. Bersihkan berkas itu sebelum menjalankan ulang.

## rilis.py

`rilis.py` membekukan PDF dan DOCX `buku-pa` atau `progres-pa-1` sebagai rilis
bernomor. Build berjalan dari sebuah commit di git worktree sementara, jadi
suntingan yang belum di-commit tidak ikut. Keluaran disalin ke
`laporan/rilis/<proyek>/vN/` (gitignored), PDF latexdiff terhadap rilis
sebelumnya dibuat bila ada, dan tag beranotasi `rilis/<proyek>/vN` dipasang
pada commit yang dibangun. Berkas rilis tidak di-commit, hanya tagnya; tag
tidak di-push.

1. Commit semua perubahan laporan.
2. Jalankan salah satu:

```bash
cd laporan/<proyek> && make rilis CATATAN="..."
python3 scripts/rilis.py <proyek> --rev <commit> --catatan "..."
```

3. Keluaran: `versi=`, `rev=`, `pdf=`, `halaman=`, `galat_log=` (baris
   `undefined` atau `Overfull` di log LaTeX), `banding=` atau `warn=`, dan
   `tag=`.
4. Hasil ada di `laporan/rilis/<proyek>/vN/`: `<proyek>-vN.pdf`,
   `<proyek>-vN.docx`, `banding-vM-vN.pdf`. Folder ini terlihat di `sajikan.py`.
5. Folder rilis yang hilang dibangun ulang dari tag:

```bash
git worktree add --detach /tmp/r rilis/<proyek>/vN
make -C /tmp/r/laporan/<proyek> pdf docx
git worktree remove --force /tmp/r
```

Salin `output/main.pdf` dan `output/main.docx` dari `/tmp/r` sebelum worktree
dihapus.

Penolakan: pohon `laporan/` punya perubahan yang belum di-commit (hanya untuk
`--rev HEAD`), tidak ada perubahan di `laporan/<proyek>` atau `laporan/shared`
sejak rilis terakhir, atau folder versi sudah ada.
