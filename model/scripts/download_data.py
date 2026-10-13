import argparse
import os
import sys

import wfdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATASETS, raw_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("db", nargs="*", metavar="DB",
                    help=f"pilihan: {', '.join(DATASETS)} (default: mitdb)")
    ap.add_argument("--semua", action="store_true", help="download semua di DATASETS")
    args = ap.parse_args()

    targets = list(DATASETS) if args.semua else (args.db or ["mitdb"])
    tak_dikenal = [d for d in targets if d not in DATASETS]
    if tak_dikenal:
        ap.error(f"database tak dikenal: {tak_dikenal} (pilihan: {sorted(DATASETS)})")

    for db in targets:
        d = raw_dir(db)
        os.makedirs(d, exist_ok=True)
        print(f"[{db}] -> {d}  ({DATASETS[db]['fs']} Hz, lead {DATASETS[db]['leads']})")
        wfdb.dl_database(db, dl_dir=d)

    print("\nSelesai. Cek kelengkapan: python scripts/check_dataset.py")
    print("Verifikasi sebaran kelas: make test  (tests/test_multidataset.py)")


if __name__ == "__main__":
    main()
