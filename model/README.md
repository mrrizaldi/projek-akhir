# model/ — jalur TinyML

Jalur pengembangan model klasifikasi aritmia biner (Normal vs Aritmia) dari
data MIT-BIH sampai header C untuk firmware ESP32-S3.

- **Spesifikasi:** `PRD_Model_Aritmia_TinyML.pdf` (folder ini).
- **Aturan kerja dan status fase:** `CLAUDE.md` (folder ini).
- **Penjelasan per fase:** [`docs/README.md`](docs/README.md).

## Lingkungan

- Python 3.11.9 (`.python-version`), venv `.venv`, dependensi `requirements.txt`.
- Semua skrip dijalankan dari folder ini, misalnya `python scripts/check_dataset.py`.
- Dataset MIT-BIH di `data/raw/mitdb/` (di-ignore git), diunduh dengan `make data`.

## Struktur

| Folder/berkas | Isi |
|---|---|
| `config.py` | Seluruh konstanta (FS, bandpass, window, label map, threshold) |
| `src/` | Modul murni (fungsi masukan → keluaran, tanpa efek samping) |
| `scripts/` | Skrip eksekusi: unduh, prep, latih, evaluasi, kuantisasi, ekspor, ablasi |
| `tests/` | pytest untuk DoD tiap fase |
| `artifacts/` | Model terlatih, `model_int8.tflite`, metrik dan plot |
| `docs/` | Walkthrough per fase ([peta](docs/README.md)) |

## Perintah utama

```bash
make data && make check   # unduh & cek dataset
make prep && make split   # Fase 2-3
make train                # Fase 5
make eval                 # Fase 6 (float32, DS2)
make quantize             # Fase 7 (PTQ INT8)
make poc                  # Fase 8 (checklist DoD)
make export               # model_int8.h -> firmware/include/
make test                 # pytest
make pull                 # tarik rekaman dari board -> data/recordings/
make analyze FILE=data/recordings/<berkas>.csv
```

Daftar lengkap target: `make help`. Target plot memakai `REC=<record>` (bawaan
100), misalnya `make plot0 REC=114`.

## Skrip (`scripts/`)

Semua dijalankan dari folder `model/`. Skrip yang mengimpor `config` memasang
`sys.path.insert` satu baris karena `python scripts/x.py` menaruh `scripts/` di
`sys.path[0]`; `conftest.py` melakukan hal yang sama untuk pytest. Penjelasan
alur dan alasan ada di walkthrough yang disebut di kolom terakhir.

| Skrip | Perintah | Guna dan catatan |
|---|---|---|
| `download_data.py` | `python scripts/download_data.py [svdb incartdb \| --all]` | Unduh database PhysioNet ke `data/raw/<db>/`. Aman diulang (wfdb melewati berkas yang sudah ada). Ukuran ~100 MB mitdb, ~200 MB svdb, ~700 MB incartdb (12 kanal). Syarat database: anotasi beat-level (lihat [dataset](docs/dataset-walkthrough.md) §4) |
| `check_dataset.py` | `make check` | Cek kelengkapan berkas, baca record 100, ringkas label, plot 30 detik pertama kanal MLII dengan simbol anotasi |
| `plot_phase0.py` | `make plot0 REC=100` | DoD Fase 0: garis R-peak anotasi harus mendarat PAS di puncak R. Meleset berarti kanal salah baca ([io-mitdb](docs/io-mitdb-walkthrough.md)) |
| `plot_phase1.py` | `make plot1` | Mentah vs bandpass: panel waktu, PSD, dan spectrogram memakai jendela waktu yang sama supaya energi tinggi di spectrogram bisa dicocokkan ke QRS ([preprocessing](docs/preprocessing-walkthrough.md)) |
| `plot_phase1_segment.py` | `make plot1seg` | Tiap window `WIN_LEN` sampel, R di garis tengah; sesudah z-score semua window sebanding (mean ~0, std ~1) |
| `plot_walkthrough.py` | `python scripts/plot_walkthrough.py 100` | Dua gambar pendamping preprocessing: jalur training (mentah → filter → segmen → z-score) dan kaskade Pan-Tompkins |
| `bench_pantompkins.py` | `python scripts/bench_pantompkins.py 100` | Sensitivity/precision detektor terhadap anotasi, toleransi ±150 ms (PRD hal. 7-9), pemasangan greedy 1-ke-1 dari sisi anotasi. Detektor TIDAK dipakai segmentasi training |
| `prep_beats.py` | `make prep` | Fase 0-2 per record → `per_record/<rec>.npz` ([prep-beats](docs/prep-beats-walkthrough.md)) |
| `build_split.py` | `make split`, `--combined` | Fase 3 ([dataset](docs/dataset-walkthrough.md)). `--combined` menulis `train_multi.npz`/`test_ds2.npz`/`test_<db>.npz` dan tidak menimpa `train.npz`/`test.npz`, yang tetap dipakai mereproduksi ablasi terkunci |
| `train_model.py` | `make train` | Fase 5 ([train](docs/train-walkthrough.md)) |
| `calibrate_threshold.py` | `python scripts/calibrate_threshold.py` | Kunci threshold di VAL ([evaluate](docs/evaluate-walkthrough.md) §2) |
| `eval_fp32.py` | `make eval` | Fase 6 di DS2; threshold dipakai apa adanya dari `config.THRESHOLD` |
| `quantize_int8.py` | `make quantize` | Fase 7; prosedur evaluasi sama persis dengan Fase 6 supaya delta = efek kuantisasi saja ([quantize](docs/quantize-walkthrough.md)) |
| `check_poc.py` | `make poc` | Fase 8: tiap item DoD PRD hal. 17 diverifikasi mekanis; exit code ≠ 0 bila ada yang gagal. Cek tabel `CLAUDE.md` hanya di seksi decision point |
| `export_model_h.py` | `make export` | `model_int8.tflite` → `firmware/include/model_int8.h`. Beda dari `xxd -i`: ikut membawa scale & zero_point tiap tensor ([firmware](docs/firmware-walkthrough.md)) |
| `export_golden.py` | `python scripts/export_golden.py` | `ecg_preproc.h` + `golden_ref.h` ([firmware](docs/firmware-walkthrough.md) §1, §3) |
| `extra_metrics.py` | `.venv/bin/python scripts/extra_metrics.py` | DS2 float32 dan INT8: PR-AUC (*average precision*) dengan prevalensi sebagai garis dasar, MCC pada `THRESHOLD`, *recall* per kelas AAMI S/V/F (simbol dari `per_record/<rek>.npz`, urutan DS2 diperiksa terhadap `y`), rerata dan median *recall* per rekaman, jumlah label yang berubah karena kuantisasi → `artifacts/metrics/fase7_metrik_tambahan.csv` ([evaluate](docs/evaluate-walkthrough.md) §3b, [quantize](docs/quantize-walkthrough.md) §6) |
| `window_quality.py` | `.venv/bin/python scripts/window_quality.py <rekaman.csv> ...` | SQI Orphanidou 2015 per jendela 10 detik → `artifacts/metrics/kualitas/jendela10s_<rekaman>.csv` ([akuisisi](docs/acquisition-walkthrough.md) §6) |
| `eval_detected_segmentation.py` | `python scripts/eval_detected_segmentation.py` | Biaya segmentasi Pan-Tompkins vs anotasi ([segmentasi-deteksi](docs/segmentasi-deteksi-walkthrough.md)). Angka pembanding dibaca dari keluaran `eval_fp32.py`, tidak dihafal |
| `measure_jitter.py`, `sweep_jitter.py` | `python scripts/measure_jitter.py`, `python scripts/sweep_jitter.py [--tag dasar]` | Residu detektor DS1 dan metrik sebagai fungsi jitter ([jitter](docs/jitter-walkthrough.md)) |
| `ablasi.py` | `python scripts/ablasi.py --tag <nama> [--jitter empiris --copies 2]` | Satu varian ujung ke ujung, lihat di bawah |
| `summarize_ablation.py` | `python scripts/summarize_ablation.py [--tag A B] [--vs A]` | Rerata ± setengah-rentang per tag, vonis ambang F1 0,04, tag < 3 seed ditandai |
| `check_lead.py`, `check_calibration.py`, `check_fp.py`, `check_operating_point.py`, `second_stage_rules.py` | lihat [docs/README.md](docs/README.md) §Alat analisis pendukung | Diagnosis eksperimen; DS2 hanya mendiagnosis, tidak memilih parameter |
| `pull_recording.py` | `make pull [N=n]` | Tarik rekaman dari board ([akuisisi](docs/acquisition-walkthrough.md)). Bila board masih merekam, skrip menghentikan & menyimpannya dulu. Port lain: `ECG_PORT=/dev/ttyACM1` |
| `analyze_recording.py` | `make analyze FILE=... [JUDUL="R1"]` | Nilai kualitas rekaman dengan angka, lihat di bawah |
| `quality_trend.py` | `.venv/bin/python scripts/quality_trend.py <berkas-1.csv> [<lanjutan>.csv ...]` | Kualitas per detik satu sesi rekam (berkas lanjutan disambung urut, `celah` selain 0 diperingatkan, berkas ber-`# jeda` ditolak) dengan rumus gerbang firmware: ayunan tersaring, dengung 50 Hz (bin FFT 1 detik = bin Goertzel `gate.cpp`), `ayun_bersih`, clipping, RR wajar, lama RR tenang. Mencetak ringkasan per menit dan detik pertama tiap syarat gerbang terpenuhi; tabel per detik → `artifacts/metrics/kualitas/<berkas-1>-sesi<k>.csv`. Dasar durasi pemanasan 60 s gerbang kalibrasi ([mqtt](docs/mqtt-walkthrough.md) §3.1) |
| `plot_recording.py` | `make plot FILE=... [MULAI=detik]` | Grafik EKG 60 detik terbaik (atau mulai detik tertentu) dalam baris 10 detik + HR per detak ([akuisisi](docs/acquisition-walkthrough.md) §5) |
| `measure_power.py`, `pull_power.py` | `.venv/bin/python scripts/measure_power.py`, `make pull-power [N=n]` | Tangga daya dari laptop dan dari board ([firmware](docs/firmware-walkthrough.md) §5d) |
| `broker_info.py` | `make broker-info` | SSID WiFi laptop, IPv4 LAN, status port, saran entri `wifi_secrets.h`. Firmware tidak me-resolve nama host, jadi broker = alamat IP dan board harus di SSID yang sama. Memakai `ip -j` (iproute2, Linux saja) dan `nmcli -t` |

### `ablasi.py`

Satu varian = satu proses. Ukuran window dan HOS dibaca `config` saat import,
jadi varian dipilih lewat environment, bukan argumen:

```bash
python scripts/ablasi.py --tag bersih
python scripts/ablasi.py --tag jitter --jitter empiris --copies 2
PA_WIN_PRE=128 PA_WIN_POST=127 python scripts/ablasi.py --tag w128 --jitter empiris --copies 2
PA_HOS=1 python scripts/ablasi.py --tag hos --jitter empiris --copies 2
```

Tiap varian menjalani rantai yang sama: rakit DS1 → split per pasien → latih →
kalibrasi threshold di VAL → ukur di DS2 (segmentasi anotasi dan ber-jitter
empiris). Threshold tidak disetel ulang di set uji mana pun. Hasil menumpuk di
`artifacts/metrics/ablasi/ablasi.csv`, satu baris per varian; model yang
disimpan hanya seed utama sehingga `check_calibration.py` dan
`check_operating_point.py` bekerja atas satu seed. `ablasi.csv` tidak punya kolom
`db`: header hanya ditulis saat berkas belum ada, jadi menambah kolom akan
menggeser baris lama; database dikodekan di `tag`. `lintas_db.csv` (TEST-B/C)
punya kolom `db`, dan `summarize_ablation.py` mengenali awalan kolom (`anot_` atau
tidak) dari header, lalu memakai kunci `tag|db` supaya satu tag di dua database
tidak dirata-rata jadi satu. Setengah-rentang dipakai, bukan stdev, karena n=3
terlalu kecil untuk stdev bermakna.

Awalan tag di `ablasi.csv` menandai kelompok eksperimen: tanpa awalan =
ablasi window/jitter/HOS (Fase 6c; `w128s3` = `--copies 3`), `fb_` = database
latih (`fb_svdb`, `fb_incartdb`, `fb_multi`, `fb_svdb_nocw` = tanpa
`class_weight`), `fd_` = tabel 2×2 dataset × fitur (`fd_mitdb_only`, `fd_both`,
`fd_qrsw`, `fd_rr`), `g_` = regime latih (`g_swa3` = `--swa 3`, `g_lr1e4`,
dan run diagnosis `g_diag`, `g_diagbase`, `g_lrdiag`), `t8_` = learning rate
dengan `--cross-db` (`t8_lr1e3`, `t8_lr3e4`, `t8_lr1e4`; baris TEST-B/C di
`lintas_db.csv`).
Vonis tiap kelompok ada di [docs/README.md](docs/README.md) §Eksperimen yang
tidak diadopsi; `ablasi_seed42.csv` dijelaskan di
[jitter](docs/jitter-walkthrough.md) §5.

Salinan jitter hanya untuk mitdb. Database lain tidak dijitter karena kolam
residu (`residu_ds1.npy`) diukur dari detektor di mitdb 360 Hz; memakainya untuk
beat 128/257 Hz yang sudah di-resample menumpuk dua sumber error posisi, dan
yang kedua belum pernah diukur. Bila diperlukan, ukur dulu residunya di database
itu dengan `measure_jitter.py`.

### `analyze_recording.py`

Masukan: keluaran `dump` firmware (baris `# fs=.. n=.. lewat=..` lalu satu nilai
ADC per baris; format di [akuisisi](docs/acquisition-walkthrough.md) §3). Semua
hitungan berjalan per segmen lalu digabung: filter mulai dari nol di awal tiap
segmen dan interval RR tidak pernah melintasi `# jeda`
(`tests/test_analyze_recording.py`).

- **Denyut periodik tanpa mendeteksi puncak.** Pan-Tompkins mudah tertipu
  dengung 50 Hz (energinya bocor lewat kuadrat + integrasi dan terhitung sebagai
  QRS). Autokorelasi energi pita QRS 5-15 Hz menanyakan hal lain yang lebih
  tahan derau: apakah pola berulang dengan periode 0,4-1,5 detik. Segmen lebih
  pendek dari 1,5 detik dilewati.
- **Penjaga positif palsu.** Denyut memberi satu puncak autokorelasi dominan;
  gangguan periodik (dengung dan harmoniknya) memberi deretan puncak setara
  berjarak seragam. Puncak lain yang tingginya ≥ 80% puncak utama dihitung
  sebagai "puncak setara".
- **Rentang fisiologis 30-200 bpm.** Proporsi RR yang jatuh di rentang ini
  dilaporkan; di luar itu hampir pasti deteksi palsu.
