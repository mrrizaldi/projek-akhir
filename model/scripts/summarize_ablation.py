import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import METRICS_DIR

AMBANG = 0.04
SEED_MINIMAL = 3
KOLOM_ABLASI = [("anot_f1", "F1"), ("anot_recall_S", "recall S"),
                ("anot_auc", "AUC"), ("threshold", "thr")]
KOLOM_LINTAS = [("f1", "F1"), ("recall_S", "recall S"),
                ("auc", "AUC"), ("threshold", "thr")]


def rerata_rentang(nilai: list) -> tuple:
    return sum(nilai) / len(nilai), (max(nilai) - min(nilai)) / 2


def baca(path: str) -> tuple:
    per_kunci = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        kolom = KOLOM_ABLASI if "anot_f1" in (r.fieldnames or []) else KOLOM_LINTAS
        pakai_db = "db" in (r.fieldnames or [])
        for baris in r:
            kunci = f"{baris['tag']}|{baris['db']}" if pakai_db else baris["tag"]
            per_kunci.setdefault(kunci, []).append(baris)
    return per_kunci, kolom


def ringkas(baris: list, KOLOM) -> dict:
    out = {"n_seed": len(baris)}
    for kolom, _ in KOLOM:
        nilai = [float(b[kolom]) for b in baris if b.get(kolom) not in (None, "")]
        out[kolom] = rerata_rentang(nilai) if nilai else None
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize ablasi.csv as mean +- half-range per tag, with a verdict against the F1 signal threshold (at least 3 seeds).",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", nargs="+",
                    help="default: all. For lintas_db.csv use 'tag|db'")
    ap.add_argument("--vs", metavar="TAG", help="compute the delta against this tag")
    ap.add_argument("--csv", default=os.path.join(METRICS_DIR, "ablasi", "ablasi.csv"))
    args = ap.parse_args()

    per_tag, KOLOM = baca(args.csv)
    tags = args.tag or list(per_tag)
    if args.vs and args.vs not in tags:
        tags = [args.vs] + tags

    hilang = [t for t in tags if t not in per_tag]
    if hilang:
        raise SystemExit(f"tag not in {args.csv}: {', '.join(hilang)}")

    judul = f"{'tag':<20}{'n':>3}  " + "  ".join(f"{n:>17}" for _, n in KOLOM)
    print(judul)
    print("-" * len(judul))
    hasil = {}
    for t in tags:
        s = hasil[t] = ringkas(per_tag[t], KOLOM)
        sel = []
        for kolom, _ in KOLOM:
            sel.append("        -        " if s[kolom] is None
                       else f"{s[kolom][0]:8.4f} +-{s[kolom][1]:6.4f}")
        tanda = "" if s["n_seed"] >= SEED_MINIMAL else "  <- seed < 3, NOT YET VALID"
        print(f"{t:<20}{s['n_seed']:>3}  " + "  ".join(sel) + tanda)

    if not args.vs:
        return
    dasar = hasil[args.vs]
    print(f"\nDelta against `{args.vs}` (F1 signal threshold {AMBANG}):")
    for t in tags:
        if t == args.vs:
            continue
        k_f1 = KOLOM[0][0]
        d_f1 = hasil[t][k_f1][0] - dasar[k_f1][0]
        d_ren = hasil[t][k_f1][1] - dasar[k_f1][1]
        vonis = "SIGNAL" if abs(d_f1) >= AMBANG else "not a signal"
        arah = "narrows" if d_ren < 0 else "widens"
        print(f"  {t:<20} dF1 {d_f1:+.4f} ({vonis})   "
              f"range F1 {arah} {abs(d_ren):.4f}")
        for kolom, nama in KOLOM[1:]:
            if hasil[t][kolom] and dasar[kolom]:
                print(f"{'':>18} d{nama} {hasil[t][kolom][0] - dasar[kolom][0]:+.4f}   "
                      f"range {dasar[kolom][1]:.4f} -> {hasil[t][kolom][1]:.4f}")


if __name__ == "__main__":
    main()
