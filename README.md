# Proyek Akhir — Sistem Monitoring Detak Jantung Kontinu (IoT Edge Computing)

Monorepo Proyek Akhir untuk pemantauan EKG kontinu dengan klasifikasi aritmia
**di edge**. Sinyal EKG satu lead diakuisisi AD8232, diproses dan diklasifikasi
oleh model TinyML INT8 di ESP32-S3, lalu hasil per detak dipublikasikan lewat
MQTT ke ThingsBoard. Klasifikasi berjalan di alat, bukan di server.

## Struktur

| Subdir | Isi | Toolchain |
|---|---|---|
| `model/` | Jalur TinyML: data MIT-BIH → preprocessing → pelatihan → kuantisasi INT8 → ekspor | Python 3.11 + TensorFlow/TFLite |
| `firmware/` | Program ESP32-S3: akuisisi 360 Hz, deteksi R-peak, inferensi TFLite Micro, MQTT | PlatformIO (C/C++) |
| `dashboard/` | ThingsBoard CE (broker MQTT, rule engine, dashboard) dan skrip pengukuran pipeline | Docker Compose, Python |
| `laporan/` | Dokumen LaTeX: `proposal-pa`, `buku-pa`, `surat-magang`, `shared` | pdflatex + bibtex |
| `scripts/` | Otomasi lintas-komponen (sinkronisasi artefak) | bash |
| `docs/` | Pola penulisan laporan PA dan arsip rencana kerja | Markdown |

## Alur artefak (produsen → konsumen)

- `model/` menghasilkan `model_int8.h` → dikonsumsi `firmware/include/`.
- `model/scripts/export_golden.py` menghasilkan `firmware/test/golden_ref.h`
  (regression test C ↔ Python).
- `model/artifacts/metrics/` (plot eksperimen) dan `dashboard/preview.png`
  menghasilkan figure → dikonsumsi `laporan/*/gambar/`. Diagram ilustrasi
  digambar penulis langsung ke `laporan/*/gambar/`.
- Sinkronisasi lewat `scripts/export_artifacts.sh`. Artefak tidak disalin manual.

Kebijakan commit: figure final dan header `.h` hasil generate **di-commit**,
sehingga laporan dan firmware dapat di-build tanpa menjalankan seluruh pipeline
model. Data mentah MIT-BIH dan berkas intermediate (`.npz`) **di-ignore**
(lihat `.gitignore`).

## Build cepat

```bash
# Laporan (ukuran kertas tetap per projek)
cd laporan/buku-pa && make pdf            # -> output/main.pdf
# Model
cd model && make train && make quantize && make export
# Firmware
cd firmware && pio run -e esp32-s3 -t upload && pio device monitor
cd firmware && pio test -e native         # uji di PC, tanpa board
# Dashboard
cd dashboard && docker compose up -d      # -> http://localhost:8080
```

## Status komponen

| Komponen | Kondisi | Bukti |
|---|---|---|
| `model/` Fase 0-8 | Selesai | `make poc` 8/8, INT8 22,94 KB, DS2 F1 0,6594, AUC 0,9334 |
| `model/` ablasi Fase A-G | Selesai, konfigurasi tidak berubah | 10 usul × 3-6 seed; TEST-B/C 85.812 beat / 39 pasien ([peta](model/docs/README.md)) |
| `firmware/` env `esp32-s3` | Berjalan di board | Inferensi 26,6 ms/detak, tensor arena 12.948 B, sampel hilang 0; MQTT PDSR 99,2-100%, latensi median 939-1.108 ms |
| Akuisisi sinyal tubuh | Pipeline siap (13 Okt 2026), **pengujian resmi belum** | Rekaman sebelum 13 Okt 2026 = uji coba, diarsipkan di [`model/data/arsip/rekaman-uji-coba/`](model/data/arsip/rekaman-uji-coba/README.md); rekaman resmi → `model/data/recordings/` |
| `firmware/` test perangkat | Lulus di board | `pio test -e esp32-s3`: 29 test (preprocessing, inferensi, buzzer, TFT, ADC, INA219, tombol, integrasi replay) |
| `firmware/` env `native` | Lulus | `pio test -e native`: 23 test |
| `dashboard/` | Berjalan | ThingsBoard CE self-host, dashboard tujuh widget, uji deduplikasi |
| `laporan/proposal-pa` | Lengkap | Bab 1-3 dan abstrak |
| `laporan/buku-pa` | Draf Bab 1-5 | Gambar ilustrasi berupa placeholder (`grep -rn PLACEHOLDER-GAMBAR laporan/`); hasil rekaman sinyal tubuh menunggu pengujian resmi (`grep -rn PLACEHOLDER-DATA laporan/buku-pa`) |

Status rinci per fase model berada di `model/CLAUDE.md`. Berkas ini hanya peta,
agar tidak ada dua sumber kebenaran. Pekerjaan yang masih terbuka (rekaman
sinyal tubuh resmi, gerbang kalibrasi, konsumsi daya) didaftar bertanggal di
[`model/CLAUDE.md` §Pekerjaan terbuka](model/CLAUDE.md#pekerjaan-terbuka).

## Peta dokumentasi

| Dokumen | Isi |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Aturan kerja repo, gate point, kebijakan gambar |
| [`model/README.md`](model/README.md) | Ringkasan komponen model |
| [`model/docs/README.md`](model/docs/README.md) | Peta walkthrough Fase 0-8 dan HW, angka rujukan, eksperimen yang tidak diadopsi |
| [`model/docs/arsip/README.md`](model/docs/arsip/README.md) | Indeks arsip desain, rencana, dan changelog eksperimen model/hardware |
| [`firmware/README.md`](firmware/README.md) | Env PlatformIO, perintah, pin map, perintah serial |
| [`dashboard/README.md`](dashboard/README.md) | ThingsBoard, kontrak payload, pengukuran pipeline |
| [`docs/pola-laporan-pa/README.md`](docs/pola-laporan-pa/README.md) | Pola penulisan laporan PA PENS |
| [`docs/arsip/README.md`](docs/arsip/README.md) | Indeks arsip rencana kerja laporan |
| [`scripts/README.md`](scripts/README.md) | Otomasi lintas-komponen (sinkronisasi artefak) |
| [`model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md`](model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md) | Penyesuaian PCB rev1 → rev2 (skematik KiCad di luar repo) |
| `laporan/CLAUDE.md` | Aturan gaya penulisan laporan |
| `model/PRD_Model_Aritmia_TinyML.pdf` | Spesifikasi resmi jalur model |
