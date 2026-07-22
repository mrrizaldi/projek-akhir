# Proyek Akhir — Sistem Monitoring Detak Jantung Kontinu (IoT Edge Computing)

Monorepo PA. Tiap subdir adalah satu komponen. Klasifikasi aritmia berjalan
**di edge** (ESP32-S3, TinyML INT8), bukan di server.

## Struktur

| Subdir       | Isi                                    | Toolchain            |
|--------------|----------------------------------------|----------------------|
| `laporan/`   | Dokumen PA (LaTeX): proposal-pa, buku-pa, shared | pdflatex / latexmk |
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

- Laporan:  `cd laporan/proposal-pa && make pdf`  (atau `buku-pa`)
- Model:    `cd model && make train && make quantize`   *(target masih stub)*
- Firmware: `cd firmware && pio run`                     *(main.cpp masih stub)*

## Status

Kerangka repo (scaffold). Isi `model/`, `firmware/`, dan logika `scripts/`
ditulis manual. Stub `.py`/`.cpp` menunjuk ke `PRD_Model_Aritmia_TinyML.md`
(belum ada di repo — tambahkan saat mulai implementasi).
