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
