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
| `scripts/arsip/` | Skrip eksplorasi awal yang tidak lagi dipakai pipeline |
| `tests/` | pytest untuk DoD tiap fase |
| `artifacts/` | Model terlatih, `model_int8.tflite`, metrik dan plot |
| `docs/` | Walkthrough per fase; `docs/arsip/` berisi dokumen desain, rencana, dan changelog eksperimen ([indeks](docs/arsip/README.md)) |

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
make analisis FILE=data/recordings/<berkas>.csv
```

Daftar lengkap target: `make help`.
