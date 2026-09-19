# Proyek Akhir — Sistem Monitoring Detak Jantung Kontinu (IoT Edge Computing)

Monorepo PA. Tiap subdir adalah satu komponen. Klasifikasi aritmia berjalan
**di edge** (ESP32-S3, TinyML INT8), bukan di server.

## Struktur

| Subdir       | Isi                                    | Toolchain            |
|--------------|----------------------------------------|----------------------|
| `laporan/`   | Dokumen (LaTeX): proposal-pa, buku-pa, surat-magang, shared | pdflatex |
| `model/`     | Jalur TinyML: preprocessing→train→INT8  | Python + TF Lite     |
| `firmware/`  | Program IoT ESP32-S3                     | PlatformIO (C/C++)   |
| `hardware/`  | Skematik & foto rakitan                 | —                    |
| `diagrams/`  | Sumber Mermaid + render PNG/SVG         | mermaid-cli          |
| `dashboard/` | Export konfig ThingsBoard               | —                    |
| `scripts/`   | Otomasi lintas-komponen (export dsb)    | bash                 |

## Alur artefak (produsen → konsumen)

- `model/` meng-generate `model_int8.h` → dikonsumsi `firmware/`.
- `model/` & `diagrams/` meng-generate figure → dikonsumsi `laporan/`.
- Sinkronisasi lewat `scripts/export_artifacts.sh` — **jangan copy manual**.

Kebijakan artefak generated: **di-commit** (figure final + `.h` kecil) supaya
laporan & firmware bisa di-build tanpa menjalankan seluruh pipeline model.
Data mentah MIT-BIH & intermediate (`.npz`) **di-ignore** (lihat `.gitignore`).

## Build cepat

- Laporan:  `cd laporan/proposal-pa && make pdf`  → `output/main.pdf`
  (projek lain: `buku-pa`, `surat-magang`; ukuran kertas fixed per projek)
- Model:    `cd model && make train && make quantize`
- Firmware: `cd firmware && pio run -e esp32-s3` (uji: `pio test -e native`)
- Dashboard: `cd dashboard && docker compose up -d` → <http://localhost:8080>

## Status (19 Sep 2026)

| Komponen | Status | Bukti |
|---|---|---|
| `model/` Fase 0-8 | **selesai** | `make poc` 8/8 mekanis, pytest 56, INT8 22,94 KB, F1 DS2 0,6594 AUC 0,9334 |
| `model/` ablasi Fase A-G | **selesai, kunci nol** | 10 usul x 3-6 seed; TEST-B/C 85.812 beat / 39 pasien. Detail: `model/docs/README.md` |
| `firmware/` HW-1..HW-4, HW-7 | **jalan di board** | 26,6 ms/detak, arena 12.948 B, RAM 21,2%, sampel hilang 0 |
| `firmware/` HW-5 elektroda | **buntu** | sisa satu variabel: header AD8232 belum disolder |
| `firmware/` HW-6 MQTT | **belum** | broker siap, klien di ESP32 belum ada |
| `dashboard/` | **jadi** | ThingsBoard CE: broker + rule engine + dashboard |
| `laporan/proposal-pa` | **lengkap** | bab1-3 + abstrak |
| `laporan/buku-pa` | **kosong** | bahan sudah ada di `model/docs/` (14 walkthrough) |

Status per fase yang rinci ada di `model/CLAUDE.md`, bukan di sini — file ini
sengaja cuma peta, supaya tidak ada dua sumber kebenaran yang bisa berbeda.
