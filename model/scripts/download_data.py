"""Fase 0 — download MIT-BIH Arrhythmia Database ke data/raw/mitdb/.

Sekali jalan (~100 MB). Aman diulang: wfdb melewati file yang sudah ada.
    python scripts/download_data.py
"""
import os

import wfdb

DL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "mitdb")

if __name__ == "__main__":
    os.makedirs(DL_DIR, exist_ok=True)
    wfdb.dl_database("mitdb", dl_dir=DL_DIR)
    print(f"Selesai. Cek kelengkapan: python scripts/check_dataset.py")
