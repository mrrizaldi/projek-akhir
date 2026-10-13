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
