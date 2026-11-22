import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import METRICS_DIR

F1_SIGNAL_THRESHOLD = 0.04
MIN_SEEDS = 3
ABLATION_COLUMNS = [("anot_f1", "F1"), ("anot_recall_S", "recall S"),
                ("anot_auc", "AUC"), ("threshold", "thr")]
CROSS_DB_COLUMNS = [("f1", "F1"), ("recall_S", "recall S"),
                ("auc", "AUC"), ("threshold", "thr")]


def mean_half_range(values: list) -> tuple:
    return sum(values) / len(values), (max(values) - min(values)) / 2


def read_file(path: str) -> tuple:
    per_key = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        kolom = ABLATION_COLUMNS if "anot_f1" in (r.fieldnames or []) else CROSS_DB_COLUMNS
        has_db = "db" in (r.fieldnames or [])
        for baris in r:
            group_key = f"{baris['tag']}|{baris['db']}" if has_db else baris["tag"]
            per_key.setdefault(group_key, []).append(baris)
    return per_key, kolom


def digest(baris: list, COLUMNS) -> dict:
    out = {"n_seed": len(baris)}
    for kolom, _ in COLUMNS:
        values = [float(b[kolom]) for b in baris if b.get(kolom) not in (None, "")]
        out[kolom] = mean_half_range(values) if values else None
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize ablasi.csv as mean +- half-range per tag, with a verdict against the F1 signal threshold (at least 3 seeds).",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", nargs="+",
                    help="default: all. For lintas_db.csv use 'tag|db'")
    ap.add_argument("--vs", metavar="TAG", help="compute the delta against this tag")
    ap.add_argument("--csv", default=os.path.join(METRICS_DIR, "ablasi", "ablasi.csv"))
    args = ap.parse_args()

    per_tag, COLUMNS = read_file(args.csv)
    tags = args.tag or list(per_tag)
    if args.vs and args.vs not in tags:
        tags = [args.vs] + tags

    missing = [t for t in tags if t not in per_tag]
    if missing:
        raise SystemExit(f"tag not in {args.csv}: {', '.join(missing)}")

    header = f"{'tag':<20}{'n':>3}  " + "  ".join(f"{n:>17}" for _, n in COLUMNS)
    print(header)
    print("-" * len(header))
    digests = {}
    for t in tags:
        s = digests[t] = digest(per_tag[t], COLUMNS)
        sel = []
        for kolom, _ in COLUMNS:
            sel.append("        -        " if s[kolom] is None
                       else f"{s[kolom][0]:8.4f} +-{s[kolom][1]:6.4f}")
        seed_note = "" if s["n_seed"] >= MIN_SEEDS else "  <- seed < 3, NOT YET VALID"
        print(f"{t:<20}{s['n_seed']:>3}  " + "  ".join(sel) + seed_note)

    if not args.vs:
        return
    baseline = digests[args.vs]
    print(f"\nDelta against `{args.vs}` (F1 signal threshold {F1_SIGNAL_THRESHOLD}):")
    for t in tags:
        if t == args.vs:
            continue
        k_f1 = COLUMNS[0][0]
        d_f1 = digests[t][k_f1][0] - baseline[k_f1][0]
        d_ren = digests[t][k_f1][1] - baseline[k_f1][1]
        verdict = "SIGNAL" if abs(d_f1) >= F1_SIGNAL_THRESHOLD else "not a signal"
        direction = "narrows" if d_ren < 0 else "widens"
        print(f"  {t:<20} dF1 {d_f1:+.4f} ({verdict})   "
              f"range F1 {direction} {abs(d_ren):.4f}")
        for kolom, label in COLUMNS[1:]:
            if digests[t][kolom] and baseline[kolom]:
                print(f"{'':>18} d{label} {digests[t][kolom][0] - baseline[kolom][0]:+.4f}   "
                      f"range {baseline[kolom][1]:.4f} -> {digests[t][kolom][1]:.4f}")


if __name__ == "__main__":
    main()
