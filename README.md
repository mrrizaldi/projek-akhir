# Final Project: Continuous Heart Rate Monitoring System (IoT Edge Computing)

Final Project monorepo for continuous ECG monitoring with arrhythmia classification
**at the edge**. A single-lead ECG signal is acquired by the AD8232, processed and
classified by a TinyML INT8 model on the ESP32-S3, and the per-beat result is
published over MQTT to ThingsBoard. Classification runs on the device, not on a server.

## Structure

| Subdir | Contents | Toolchain |
|---|---|---|
| `model/` | TinyML track: MIT-BIH data → preprocessing → training → INT8 quantization → export | Python 3.11 + TensorFlow/TFLite |
| `firmware/` | ESP32-S3 program: 360 Hz acquisition, R-peak detection, TFLite Micro inference, MQTT | PlatformIO (C/C++) |
| `dashboard/` | ThingsBoard CE (MQTT broker, rule engine, dashboard) and pipeline measurement scripts | Docker Compose, Python |
| `hardware/` | PCB mainboard rev2: schematic, layout, DevKitC-1 library, automatic checks ([`hardware/mainboard/`](hardware/mainboard/README.md)) | KiCad 9 |
| `laporan/` | LaTeX documents: `proposal-pa`, `buku-pa`, `surat-magang`, `shared` | pdflatex + bibtex |
| `scripts/` | Cross-component automation (artifact sync) | bash |
| `docs/` | Running working documents across components ([index](docs/README.md)) | Markdown |

## Artifact flow (producer → consumer)

- `model/` produces `model_int8.h` → consumed by `firmware/include/`.
- `model/scripts/export_golden.py` produces `firmware/test/golden_ref.h`
  (C ↔ Python regression test).
- `model/artifacts/metrics/` (experiment plots) and `dashboard/preview.png`
  produce figures → consumed by `laporan/*/gambar/`. Illustration diagrams
  are drawn by the author directly into `laporan/*/gambar/`.
- Sync goes through `scripts/export_artifacts.sh`. Artifacts are not copied by hand.

Commit policy: final figures and generated `.h` headers **are committed**
so the laporan and the firmware can be built without running the whole model
pipeline. Raw MIT-BIH data and intermediate files (`.npz`) **are ignored**
(see `.gitignore`).

## Quick build

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

## Component status

| Component | Condition | Evidence |
|---|---|---|
| `model/` Phase 0-8 | Done | `make poc` 8/8, INT8 22.94 KB, DS2 F1 0.6594, AUC 0.9334 |
| `model/` ablation Phase A-G | Done, configuration unchanged | 10 proposals × 3-6 seeds; TEST-B/C 85,812 beats / 39 patients ([map](model/docs/README.md)) |
| `firmware/` env `esp32-s3` | Runs on the board | Inference 26.6 ms/beat, tensor arena 12,948 B, lost samples 0; MQTT PDSR 99.2-100%, median latency 939-1,108 ms |
| Body signal acquisition | Done: official data = 22 Oct 2026 midday session (R1–R4, 927.1 s, 4/4 Berhasil) | Session index in [`model/data/recordings/README.md`](model/data/recordings/README.md); development recordings archived in [`model/data/arsip/rekaman-uji-coba/`](model/data/arsip/rekaman-uji-coba/README.md) |
| `firmware/` device tests | Passes on the board | `pio test -e esp32-s3`: 29 tests (preprocessing, inference, buzzer, TFT, ADC, INA219, buttons, replay integration) |
| `firmware/` env `native` | Passes | `pio test -e native`: 23 tests |
| `dashboard/` | Running | self-hosted ThingsBoard CE, seven-widget dashboard, deduplication test |
| `laporan/proposal-pa` | Complete | Bab 1-3 and abstract |
| `laporan/buku-pa` | Draft Bab 1-5 | Illustration figures are placeholders (`grep -rn PLACEHOLDER-GAMBAR laporan/`); power consumption numbers wait for measurement (`grep -rn PLACEHOLDER-DATA laporan/buku-pa`) |

Detailed status per model phase is in `model/CLAUDE.md`. This file is only a map,
so there are not two sources of truth. Work that is still open (power
consumption, emergency WiFi OFF, recording to the server, PCB rev2) is listed with dates in
[`model/CLAUDE.md` §Open work](model/CLAUDE.md#open-work).

## Documentation map

| Document | Contents |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Repo working rules, gate points, figure policy |
| [`model/README.md`](model/README.md) | Summary of the model component |
| [`model/docs/README.md`](model/docs/README.md) | Map of the Phase 0-8 and HW walkthroughs, reference numbers, experiments that were not adopted |
| [`firmware/README.md`](firmware/README.md) | PlatformIO envs, commands, pin map, serial commands |
| [`dashboard/README.md`](dashboard/README.md) | ThingsBoard, payload contract, pipeline measurement |
| [`.claude/skills/`](.claude/skills/) | Index of repo skills (laporan: `struktur-pa`, `tulis-tanpa-slop`, `tabel-pa`, `buku-ikut-proposal`, `deck-pa`; firmware: `batas-tidak-diam`; code: `tanpa-komentar-kode`; PCB: `kicad-pcb-pa`; `ingest-word`) and the user skills they load |
| [`scripts/README.md`](scripts/README.md) | Cross-component automation (artifact sync) |
| [`hardware/mainboard/README.md`](hardware/mainboard/README.md) | Mainboard PCB: pin map, power supply, circuit rationale of the modules, differences from the rev2 schematic, what is not yet verified |
| `laporan/CLAUDE.md` | Report writing style rules |
| `model/PRD_Model_Aritmia_TinyML.pdf` | Official specification of the model track |
