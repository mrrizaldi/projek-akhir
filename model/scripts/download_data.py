import argparse
import os
import sys

import wfdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATASETS, raw_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("db", nargs="*", metavar="DB",
                    help=f"choices: {', '.join(DATASETS)} (default: mitdb)")
    ap.add_argument("--all", action="store_true", help="download everything in DATASETS")
    args = ap.parse_args()

    targets = list(DATASETS) if args.all else (args.db or ["mitdb"])
    tak_dikenal = [d for d in targets if d not in DATASETS]
    if tak_dikenal:
        ap.error(f"database tak dikenal: {tak_dikenal} (pilihan: {sorted(DATASETS)})")

    for db in targets:
        d = raw_dir(db)
        os.makedirs(d, exist_ok=True)
        print(f"[{db}] -> {d}  ({DATASETS[db]['fs']} Hz, lead {DATASETS[db]['leads']})")
        wfdb.dl_database(db, dl_dir=d)

    print("\nDone. Check completeness: python scripts/check_dataset.py")
    print("Verify the class distribution: make test  (tests/test_multidataset.py)")


if __name__ == "__main__":
    main()
