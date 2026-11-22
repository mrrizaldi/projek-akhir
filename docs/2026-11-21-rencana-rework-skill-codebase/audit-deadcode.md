# Audit kode mati (baca-saja), 21 Nov 2026

Metode: skill `deadcode`. vulture/ruff/cppcheck tidak terpasang, jadi dipakai analisis AST Python, grep, dan `g++ -fsyntax-only -Wall -Wextra` untuk modul native firmware. Tidak ada berkas disunting. Lingkup dikecualikan sesuai tugas: knob `PA_*`, `test_hw_*`, golden ref, skrip yang didokumentasikan README, mode simulasi.

## Ringkasan

| Komponen | Temuan | Usulan hapus | Usulan pertahankan / pindah |
|---|---|---|---|
| firmware | 3 fungsi publik tanpa pemanggil | 3 | 0 |
| model/src | 2 import tidak terpakai | 2 | 0 |
| model/scripts | 1 fungsi, 11 import tidak terpakai (di 7 berkas) | 12 | 0 |
| scripts/ (repo) | 0 | 0 | 0 |
| dashboard | 0 | 0 | 0 |
| presentasi | 0 | 0 | 0 |
| berkas ter-track | 2 (mainboard.zip, residu_ds1.npy) | 1 | 1 |
| model/tests | 1 import | 1 | 0 |

Total 20 butir hapus-kandidat, 1 pertahankan. Semua skrip di `model/scripts/`, `scripts/`, `dashboard/` dirujuk README/Makefile/skill/CI (grep per nama, tiap berkas punya minimal satu rujukan di luar dirinya). Tidak ditemukan blok tak terjangkau (return/raise diikuti pernyataan), `if False/0/True` konstan, maupun konstanta `config.py` yang tak dipakai (tiap nama dicari di seluruh `*.py`). `g++ -Wall -Wextra -Wunused` bersih untuk `ecg_pipeline`, `ecg_live`, `ina219`, `ecg_mqtt`. Modul yang butuh Arduino (menu, tampilan, rekam, dll.) tidak dikompilasi; hanya diperiksa lewat grep nama.

## firmware

| path:baris | jenis | bukti | usulan | risiko |
|---|---|---|---|---|
| firmware/include/ecg_mqtt.h:35, firmware/src/ecg_mqtt.cpp:21 | fungsi tak dipanggil `ecg_mqtt_antre_reset` | `grep -rnw ecg_mqtt_antre_reset src include test ../scripts ../model/scripts README.md` hanya mengembalikan deklarasi dan definisi. Tidak ada di test_mqtt maupun README. | hapus deklarasi + definisi | rendah; `queue_head/isi/hilang` tetap dipakai internal |
| firmware/include/ecg_mqtt.h:47, firmware/src/ecg_mqtt.cpp:350 | fungsi tak dipanggil `ecg_mqtt_tersambung` | grep yang sama: hanya deklarasi + definisi. | hapus; cek bahwa variabel `tersambung` masih dipakai fungsi lain (dipakai di ecg_mqtt.cpp) | rendah |
| firmware/include/display.h:21, firmware/src/display.cpp:313 | fungsi tak dipanggil `tampilan_monitor` | grep: hanya deklarasi + definisi. Variabel `monitor` dipakai di tempat lain di display.cpp. | hapus accessor | rendah |

Metode verifikasi tiga di atas: skrip memindai semua prototipe di `include/*.h` (kecuali `model_int8.h`, `wifi_secrets*.h`), lalu menghitung pemanggilan di `src/`, `include/`, `test/` di luar header dan di luar baris definisi. Hanya tiga nama itu bernilai nol. Macro/konstanta file-lokal (`constexpr`, `#define`, `enum`) dihitung: semuanya punya pemakaian >= 2 kali atau dipakai di test/generator (mis. `ECG_PT_OFFSET` dan `ECG_ZSCORE_EPS` di `ecg_preproc.h` dihasilkan `export_golden.py`, dipakai `ecg_pipeline.cpp`).

## model/src

| path:baris | jenis | bukti | usulan | risiko |
|---|---|---|---|---|
| model/src/io_mitdb.py:6 | import tidak terpakai `CHANNEL`, `RAW_DIR` | `grep -nw CHANNEL src/io_mitdb.py` dan `grep -nw RAW_DIR ...` hanya baris import. Tidak ada modul yang mengimpor nama itu lewat `src.io_mitdb` (`grep -rn "from src.io_mitdb import"` kosong). | hapus dari baris import | nol |

## model/scripts

| path:baris | jenis | bukti | usulan | risiko |
|---|---|---|---|---|
| model/scripts/prep_beats.py:72 | fungsi tak dipanggil `available_records(raw_dir=RAW_DIR)` | `grep -rn available_records` di model/ dashboard/ scripts/ hanya definisi (satu hit). Hanya membungkus `records_tersedia("mitdb")`, parameter `raw_dir` malah diabaikan. Setelah dihapus, impor `RAW_DIR` di berkas yang sama mungkin ikut tak terpakai (periksa). | hapus | nol |
| model/scripts/prep_beats.py:10 | import tidak terpakai `PACED_EXCLUDED` | `grep -nw PACED_EXCLUDED scripts/prep_beats.py` hanya baris import | hapus dari import | nol |
| model/scripts/bench_pantompkins.py:11 | import `FS` | grep -nw FS: hanya baris 11 | hapus | nol |
| model/scripts/plot_fase0.py:11 | import `FS` | grep -nw FS: hanya baris 11 | hapus | nol |
| model/scripts/check_poc.py:5 | import `numpy as np` | grep -nw np: baris 5 dan satu string literal baris 40 (`"np.random.seed(SEED)"`), bukan pemakaian | hapus | nol |
| model/scripts/check_poc.py:11 | import `PROCESSED_DIR`, `THRESHOLD` | grep -nw: hanya baris 11 | hapus | nol |
| model/scripts/export_golden.py:11,14 | import `ALIGN_WIN`, `BANDPASS_LOW`, `BANDPASS_HIGH`, `BANDPASS_ORDER` | grep -nw tiap nama: hanya baris import (4 nama) | hapus | nol; generator bandpass memakai `src.preprocessing` |
| model/scripts/sweep_jitter.py:14 | import `USE_HOS` | grep -nw USE_HOS: hanya baris 14 | hapus | nol |
| model/scripts/cek_fp.py:53 | import `tensorflow as tf` (lokal dalam `main`) | `grep -n "keras\|tf\b" scripts/cek_fp.py`: `tf` tidak dipakai; `keras` dipakai baris 62 lewat `from tensorflow import keras` | hapus baris `import tensorflow as tf` saja | nol |

## model/tests

| path:baris | jenis | bukti | usulan | risiko |
|---|---|---|---|---|
| model/tests/test_features_rr.py:3 | import `RR_LOCAL_WINDOW_BEATS` | grep -nw: hanya baris 3 | hapus dari import | nol |

## scripts/, dashboard/, presentasi/

Tidak ada temuan. Cek yang dijalankan:
- Rujukan per berkas: untuk tiap `scripts/*`, `dashboard/*.py`, `model/scripts/*.py` dijalankan `git grep -l -w <nama> ... ':!laporan' ':!docs/arsip'`; semua punya rujukan di README/Makefile/skill/CI/dokumen aktif. Yang hanya dirujuk satu README: `cek_fp`, `cek_kalibrasi`, `cek_lead`, `ringkas_ablasi`, `plot_walkthrough`, `ukur_jitter`, `tahap2`, `cek_docx` (didokumentasikan sebagai alat yang dijalankan user, jadi dipertahankan).
- Flag argparse tanpa pembaca: pemindai menandai `--mulai/--durasi` (plot_rekaman) dan `--kertas/--ketat/--hanya-galat/--tanpa-prosa/--uji` (cek_tabel); diperiksa manual, semuanya terbaca lewat nama variabel lain (`arg.kertas`, `mulai_s`, dst.). Positif palsu.
- Fungsi Python tak dipanggil (nama muncul hanya sekali di seluruh `*.py` yang ter-track): hanya `available_records`. Fungsi dengan dua kemunculan (def + satu panggilan) tidak dianggap mati.
- `deck.js` (2 berkas): semua helper `const` dipakai > 1 kali.

## Berkas ter-track / artefak

| path | jenis | bukti | usulan | risiko |
|---|---|---|---|---|
| hardware/mainboard.zip | arsip biner ter-track, tidak dirujuk | `git grep -F mainboard.zip -- . ':!laporan' ':!docs/arsip'` kosong. `unzip -l`: salinan 16 Okt 2026 berisi `.mcp-backups/`, `mainboard-backups/`, `mainboard.dsn`, `fp-info-cache`, `.kicad_pcb` lama (520 KB). Isinya sudah ada (versi terbaru) di `hardware/mainboard/`. Commit pembawanya: 2410147 "arsip mainboard". | pindah ke arsip atau hapus bila tidak dibutuhkan (git menyimpan riwayat); kebijakan repo memakai `git mv` ke `hardware/arsip/` | rendah; berisi backup kerja lama, bukan sumber |
| model/artifacts/metrics/jitter/residu_ds1.npy | `.npy` intermediate ter-track | ditulis `ukur_jitter.py:142`; dibaca (dirujuk) `model/CLAUDE.md`, `model/README.md`, `jitter-walkthrough.md` sebagai masukan `PA_JITTER=empiris`. | pertahankan: dibaca model pada jitter empiris, bukan hasil buang | alasan mempertahankan; kebijakan B1 hanya mengecualikan `.npz` |
| model/artifacts/metrics/ablasi/ablasi_seed42.csv | CSV arsip tak dirujuk dokumen aktif | `git grep -n ablasi_seed42 -- model`: hanya `model/docs/arsip/...robustness-changelog.md` ("arsip batch pertama"). Tidak ditulis oleh skrip mana pun. | pindah ke `model/artifacts/arsip/` atau hapus | rendah |
| model/artifacts/metrics/{pantompkins_114,fase0_114,fase1_114}.png | figure kembaran record 114 | tak dirujuk dokumen aktif (`git grep pantompkins_114 fase0_114 fase1_114` kosong); dibangkitkan ulang oleh `bench_pantompkins.py`, `plot_fase0.py`, `plot_fase1.py` (`make plot0/plot1`). | pertahankan: figure final B1 (versi `_100` dirujuk buku); tinjau bila ingin mengurangi | rendah |

Catatan: `model/artifacts/metrics/akuisisi/akuisisi_device.png` (untracked pada gitStatus) tidak termasuk audit.

## Lima temuan paling yakin

1. `ecg_mqtt_antre_reset` (firmware/include/ecg_mqtt.h:35, src/ecg_mqtt.cpp:21): nol pemanggil di src, include, test, skrip.
2. `ecg_mqtt_tersambung` (ecg_mqtt.h:47, ecg_mqtt.cpp:350): nol pemanggil.
3. `tampilan_monitor` (display.h:21, display.cpp:313): nol pemanggil.
4. `available_records` (model/scripts/prep_beats.py:72): nol pemanggil, parameter diabaikan.
5. Impor mati: `model/scripts/export_golden.py` (`ALIGN_WIN`, `BANDPASS_LOW/HIGH/ORDER`) dan `model/src/io_mitdb.py` (`CHANNEL`, `RAW_DIR`), hanya baris import.

Setiap penghapusan harus dikonfirmasi user (gate skill deadcode), diikuti `pio test -e native`, `pio run`, `make test`/pytest di `model/`, dan `python3 scripts/cek_komentar.py` sebelum commit.
