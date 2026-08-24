# model/ — jalur TinyML

Spesifikasi: `PRD_Model_Aritmia_TinyML.pdf` (di folder ini).

- Python 3.11.9 (`.python-version`), venv `.venv`, deps `requirements.txt`
- Jalankan semua script dari folder ini: `python scripts/check_dataset.py`
- Dataset MIT-BIH → `data/raw/mitdb/` (gitignored; unduh via `wfdb.dl_database('mitdb', dl_dir='data/raw/mitdb')`)
- Konstanta final (FS, bandpass, window, label map) → `config.py`
