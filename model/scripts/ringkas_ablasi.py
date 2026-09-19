"""Ringkas ablasi.csv jadi rerata +- setengah-rentang, dan tegakkan ambang sinyal.

    python scripts/ringkas_ablasi.py                      # semua tag
    python scripts/ringkas_ablasi.py --tag w128b g_swa3
    python scripts/ringkas_ablasi.py --tag g_swa3 --vs w128b

Aturan §7 (docs/2026-09-19-fitur-design.md) dipakai apa adanya:
  * minimal 3 seed — tag ber-seed < 3 ditandai, bukan diam-diam dipercaya
  * dilaporkan rerata DAN setengah-rentang, bukan angka tunggal
  * |delta| < AMBANG F1 BUKAN sinyal

Dipakai supaya vonis ablasi tidak lagi dihitung tangan tiap kali — kesalahan
paling mahal di repo ini bukan yang crash, tapi yang menghasilkan angka yang
kelihatan bagus.
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import METRICS_DIR  # noqa: E402

AMBANG = 0.04          # selisih F1 di bawah ini bukan sinyal (oneDNN, changelog 18 Sep)
SEED_MINIMAL = 3
# ablasi.csv memberi awalan `anot_`; lintas_db.csv (T8) tidak. Satu alat, dua
# berkas: awalan dideteksi dari header, bukan ditebak dari nama file.
KOLOM_ABLASI = [("anot_f1", "F1"), ("anot_recall_S", "recall S"),
                ("anot_auc", "AUC"), ("threshold", "thr")]
KOLOM_LINTAS = [("f1", "F1"), ("recall_S", "recall S"),
                ("auc", "AUC"), ("threshold", "thr")]


def rerata_rentang(nilai: list) -> tuple:
    """(rerata, setengah-rentang). Setengah-rentang, bukan stdev: n=3 terlalu
    kecil untuk stdev bermakna, dan yang ingin dijawab 'seberapa lebar hasilnya'."""
    return sum(nilai) / len(nilai), (max(nilai) - min(nilai)) / 2


def baca(path: str) -> tuple:
    """-> (per_kunci, KOLOM). Kunci = tag, atau "tag|db" kalau berkasnya punya
    kolom `db` (lintas_db.csv): satu tag di dua database itu dua hasil, bukan
    satu yang boleh dirata-rata."""
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
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", nargs="+",
                    help="bawaan: semua. Untuk lintas_db.csv pakai 'tag|db'")
    ap.add_argument("--vs", metavar="TAG", help="hitung delta terhadap tag ini")
    ap.add_argument("--csv", default=os.path.join(METRICS_DIR, "ablasi", "ablasi.csv"))
    args = ap.parse_args()

    per_tag, KOLOM = baca(args.csv)
    tags = args.tag or list(per_tag)
    if args.vs and args.vs not in tags:
        tags = [args.vs] + tags

    hilang = [t for t in tags if t not in per_tag]
    if hilang:
        raise SystemExit(f"tag tidak ada di {args.csv}: {', '.join(hilang)}")

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
        tanda = "" if s["n_seed"] >= SEED_MINIMAL else "  <- seed < 3, BELUM SAH"
        print(f"{t:<20}{s['n_seed']:>3}  " + "  ".join(sel) + tanda)

    if not args.vs:
        return
    dasar = hasil[args.vs]
    print(f"\nDelta terhadap `{args.vs}` (ambang sinyal F1 {AMBANG}):")
    for t in tags:
        if t == args.vs:
            continue
        k_f1 = KOLOM[0][0]          # `anot_f1` atau `f1`, tergantung berkasnya
        d_f1 = hasil[t][k_f1][0] - dasar[k_f1][0]
        d_ren = hasil[t][k_f1][1] - dasar[k_f1][1]
        vonis = "SINYAL" if abs(d_f1) >= AMBANG else "bukan sinyal"
        arah = "menyempit" if d_ren < 0 else "melebar"
        print(f"  {t:<20} dF1 {d_f1:+.4f} ({vonis})   "
              f"rentang F1 {arah} {abs(d_ren):.4f}")
        for kolom, nama in KOLOM[1:]:
            if hasil[t][kolom] and dasar[kolom]:
                print(f"{'':>18} d{nama} {hasil[t][kolom][0] - dasar[kolom][0]:+.4f}   "
                      f"rentang {dasar[kolom][1]:.4f} -> {hasil[t][kolom][1]:.4f}")


if __name__ == "__main__":
    main()
