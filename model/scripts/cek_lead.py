"""Gate A2 — apakah lead dataset baru sebanding dengan MLII mitdb?

    python scripts/cek_lead.py

Yang diukur: nilai window ter-z-score DI POSISI R (indeks WIN_PRE + group delay
= 132), dirata-rata atas beat NORMAL saja. Itu persis angka yang dilihat model.

DUA pertanyaan dijawab di sini, dan HARUS dibaca dari kolom yang berbeda:

  POLARITAS  -> baca kolom "mentah" (tanpa selaraskan). Kalau mitdb positif kuat
                dan dataset lain negatif / %pos kacau, lead-nya terbalik:
                morfologi QRS kebalik dan model belajar invariansi yang tak kita
                mau. Gejalanya di Fase B bukan error, cuma "dataset baru tidak
                menolong".
  ALIGNMENT  -> baca kolom "selaras". Puncak harus mendarat di 132.

Kolom "selaras" TIDAK BOLEH dipakai memvonis polaritas: selaraskan_r memakai
signed argmax, jadi dia memaksa nilai di R jadi positif — lead terbalik pun akan
tampak sebanding sesudahnya.

Beat V/F sengaja dibuang dari statistik: morfologinya memang aneh dan bisa
negatif di lead yang benar, jadi mencampurnya mengaburkan sinyal yang dicari.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AAMI_MAP, DATASETS, WIN_PRE  # noqa: E402
from src.dataset import records_tersedia  # noqa: E402
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import (  # noqa: E402
    apply_bandpass, design_bandpass_sos, segment_beats, selaraskan_r,
    zscore_per_window,
)

R_IDX = WIN_PRE + 4  # group delay bandpass kausal = +4 sampel (= 132)
N_REC = int(os.environ.get("PA_CEK_REC", 8))   # gate, bukan ablasi


def ukur(db: str, rec: str, sos, lead_paksa=None) -> dict:
    """Satu record, dua pengukuran: mentah (apa adanya) & selaras (lewat selaraskan_r)."""
    if lead_paksa:
        DATASETS[db]["leads"] = (lead_paksa,)
    signal, r0, sym, _ = load_record(rec, db=db)
    filt = apply_bandpass(signal, sos)
    normal = np.array([AAMI_MAP[s] == "N" for s in sym])

    out = {}
    for nama, r in (("mentah", r0), ("selaras", selaraskan_r(r0, filt))):
        ok = (r - WIN_PRE >= 0) & (r + WIN_PRE <= len(signal)) & normal
        if ok.sum() < 20:
            return {}
        w = zscore_per_window(segment_beats(filt, r[ok]))
        di_r = w[:, R_IDX]
        out[nama] = {
            "n": len(w),
            "mean": float(di_r.mean()),
            "%positif": float((di_r > 0).mean() * 100),
            # argmax |mean window|: mengukur amplitudo ABSOLUT, jadi bisa
            # menunjuk gelombang S yang dalam alih-alih R. Baca bareng "mean".
            "puncak_di": int(np.argmax(np.abs(w).mean(axis=0))),
        }
    return out


def main() -> None:
    sos = design_bandpass_sos()
    print(f"nilai window ter-z-score di indeks R={R_IDX}, beat NORMAL saja\n")
    print(f"{'db':10} {'lead':6} {'rec':6} {'n':>6} | "
          f"{'MENTAH: mean':>12} {'%pos':>5} {'pk':>4} | "
          f"{'SELARAS: mean':>13} {'%pos':>5} {'pk':>4}")
    print("-" * 82)

    rencana = [("mitdb", None), ("svdb", "ECG1"), ("svdb", "ECG2"),
               ("incartdb", None)]
    ringkas = {}
    for db, lead in rencana:
        recs = records_tersedia(db)
        if not recs:
            print(f"{db:10} {'-':6} belum ada record lengkap — lewati")
            continue
        asli = DATASETS[db]["leads"]
        nilai = []
        for rec in recs[:N_REC]:
            try:
                m = ukur(db, rec, sos, lead)
            except ValueError as e:      # lead tidak ada di record ini
                print(f"{db:10} {lead or asli[0]:6} {rec:6} {str(e)[:40]}")
                continue
            if not m:
                continue
            nilai.append((m["mentah"]["mean"], m["selaras"]["mean"]))
            print(f"{db:10} {lead or asli[0]:6} {rec:6} {m['mentah']['n']:>6} | "
                  f"{m['mentah']['mean']:>12.3f} {m['mentah']['%positif']:>4.0f}% "
                  f"{m['mentah']['puncak_di']:>4} | "
                  f"{m['selaras']['mean']:>13.3f} {m['selaras']['%positif']:>4.0f}% "
                  f"{m['selaras']['puncak_di']:>4}")
        DATASETS[db]["leads"] = asli
        if nilai:
            a = np.asarray(nilai)
            ringkas[f"{db}/{lead or asli[0]}"] = (a[:, 0].mean(), a[:, 1].mean(),
                                                 (a[:, 0] > 0).mean(), len(a))

    print("\n── vonis POLARITAS (dari kolom MENTAH — jangan dari SELARAS) ──")
    acuan = ringkas.get("mitdb/MLII", (None,))[0]
    for k, (mentah, selaras, konsisten, n) in ringkas.items():
        vonis = ""
        if acuan is not None and k != "mitdb/MLII":
            vonis = ("  <- SEBANDING" if np.sign(mentah) == np.sign(acuan) and konsisten > 0.8
                     else "  <- CURIGA / TERBALIK")
        print(f"  {k:18} mentah {mentah:+7.3f}  ({100*konsisten:.0f}% record positif, "
              f"n={n}){vonis}")
    print("\n── vonis ALIGNMENT (dari kolom SELARAS; puncak harus 132) ──")
    for k, (mentah, selaras, konsisten, n) in ringkas.items():
        print(f"  {k:18} selaras {selaras:+7.3f}")


if __name__ == "__main__":
    main()
