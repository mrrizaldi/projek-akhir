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
berisi daftar grafik rekaman resmi (≥ 13 Okt 2026, relatif terhadap
`model/artifacts/metrics/`, tanpa `.png`, dipisah spasi) yang ikut disalin.

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
(skill `tabel-pa` dan `narasi-pa`). Galat keluar dengan kode 1, sedangkan
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
python3 scripts/cek_tabel.py --kertas a5 laporan/buku-kp/... # lebar teks A5
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
