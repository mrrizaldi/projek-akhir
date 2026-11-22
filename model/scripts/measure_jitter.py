import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import DS1, FS, METRICS_DIR, PT_DETECTOR_OFFSET
from src.evaluate import pair_detected
from src.features_rr import to_aami_class
from src.io_mitdb import load_record
from src.preprocessing import (
    apply_bandpass, design_bandpass_sos, pan_tompkins_detect,
)
from scripts.eval_detected_segmentation import refine_peaks

TOLERANCE_WINDOW_MS = 150
OUT_DIR = os.path.join(METRICS_DIR, "jitter")


def record_residual(rec: str, sos, tolerance: int):
    signal, r_anot, simbol, _ = load_record(rec)
    filtered = apply_bandpass(signal, sos)

    r_used = refine_peaks(pan_tompkins_detect(filtered, FS) - PT_DETECTOR_OFFSET, filtered)
    pasangan = pair_detected(r_used, r_anot, tolerance)

    cocok = pasangan >= 0
    residu = r_used[cocok] - r_anot[pasangan[cocok]]
    n_palsu = int((~cocok).sum())
    n_lewat = len(r_anot) - int(cocok.sum())

    class_missed = {}
    terdeteksi = np.zeros(len(r_anot), dtype=bool)
    terdeteksi[pasangan[cocok]] = True
    for symbol_short, ok in zip(simbol, terdeteksi):
        k = to_aami_class(symbol_short)
        a, b = class_missed.get(k, (0, 0))
        class_missed[k] = (a + 1, b + int(not ok))

    return residu, n_palsu, n_lewat, len(r_anot), class_missed


def digest(residu: np.ndarray) -> dict:
    a = np.abs(residu)
    return {
        "n": len(residu),
        "median": float(np.median(residu)),
        "mean": float(residu.mean()),
        "std": float(residu.std()),
        "p5": float(np.percentile(residu, 5)),
        "p95": float(np.percentile(residu, 95)),
        "abs_p95": float(np.percentile(a, 95)),
        "abs_p99": float(np.percentile(a, 99)),
        "abs_maks": float(a.max()),
    }


def plot(residu: np.ndarray, out_path: str, s: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.2))

    lo, hi = int(np.percentile(residu, 0.5)), int(np.percentile(residu, 99.5))
    ax1.hist(residu, bins=np.arange(lo - 0.5, hi + 1.5), color="#3b6ea5")
    ax1.axvline(0, color="k", lw=1)
    ax1.axvline(s["median"], color="#c0392b", lw=1.5,
                label=f"median {s['median']:.0f}")
    ax1.set_xlabel("residu (sampel)  [+ = deteksi terlambat]")
    ax1.set_ylabel("jumlah beat")
    ax1.set_title(f"Residu penyelarasan R di DS1 (n={s['n']:,})")
    ax1.legend()
    ax1.grid(alpha=0.3)

    a = np.sort(np.abs(residu))
    ax2.plot(a, np.arange(1, len(a) + 1) / len(a), color="#3b6ea5")
    for p, gaya in ((s["abs_p95"], "--"), (s["abs_p99"], ":")):
        ax2.axvline(p, ls=gaya, color="#c0392b")
    ax2.set_xlim(0, max(4, s["abs_p99"] * 2))
    ax2.set_xlabel("|residu| (sampel)")
    ax2.set_ylabel("proporsi beat")
    ax2.set_title(f"ECDF |residu| — p95 {s['abs_p95']:.0f}, p99 {s['abs_p99']:.0f} sampel")
    ax2.grid(alpha=0.3)

    fig.suptitle("Jitter segmentasi on-device yang terukur (rantai penuh, DS1)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    sos = design_bandpass_sos()
    tolerance = round(TOLERANCE_WINDOW_MS / 1000 * FS)

    semua, baris = [], []
    total_false = total_missed = tot_beat = 0
    kelas = {}

    print(f"{'rec':>5} {'beat':>7} {'matched':>7} {'missed':>6} {'false':>6} "
          f"{'med':>5} {'std':>6} {'|p95|':>6}")
    for rec in DS1:
        residu, n_palsu, n_lewat, n_beat, kl = record_residual(str(rec), sos, tolerance)
        semua.append(residu)
        total_false += n_palsu
        total_missed += n_lewat
        tot_beat += n_beat
        for k, (a, b) in kl.items():
            x, y = kelas.get(k, (0, 0))
            kelas[k] = (x + a, y + b)

        s = digest(residu)
        baris.append((rec, n_beat, s["n"], n_lewat, n_palsu, s["median"], s["std"],
                      s["abs_p95"]))
        print(f"{rec:>5} {n_beat:>7} {s['n']:>7} {n_lewat:>6} {n_palsu:>6} "
              f"{s['median']:>5.0f} {s['std']:>6.2f} {s['abs_p95']:>6.1f}")

    residu = np.concatenate(semua)
    s = digest(residu)

    print("-" * 60)
    print(f"DS1: {tot_beat:,} annotated beats, {s['n']:,} paired, "
          f"{total_missed:,} missed ({100 * total_missed / tot_beat:.2f}%), "
          f"{total_false:,} false detections")
    print(f"residual: median {s['median']:.1f}  mean {s['mean']:.2f}  std {s['std']:.2f}  "
          f"p5 {s['p5']:.0f}  p95 {s['p95']:.0f}")
    print(f"|residual|: p95 {s['abs_p95']:.0f}  p99 {s['abs_p99']:.0f}  "
          f"max {s['abs_maks']:.0f} samples "
          f"({1000 * s['abs_p95'] / FS:.0f} / {1000 * s['abs_p99'] / FS:.0f} ms)")
    print("missed beats per AAMI class: " + "  ".join(
        f"{k} {b}/{a} ({100 * b / a:.1f}%)" for k, (a, b) in sorted(kelas.items())))

    with open(os.path.join(OUT_DIR, "jitter_residu.csv"), "w") as f:
        f.write("record,n_anotasi,n_cocok,n_lewat,n_palsu,median,std,abs_p95\n")
        for r in baris:
            f.write("%s,%d,%d,%d,%d,%.1f,%.3f,%.1f\n" % r)
        f.write("TOTAL,%d,%d,%d,%d,%.1f,%.3f,%.1f\n" % (
            tot_beat, s["n"], total_missed, total_false, s["median"], s["std"], s["abs_p95"]))

    np.save(os.path.join(OUT_DIR, "residu_ds1.npy"), residu.astype(np.int16))
    plot(residu, os.path.join(OUT_DIR, "jitter_residu.png"), s)
    print(f"\n{OUT_DIR}/jitter_residu.csv + .png")


if __name__ == "__main__":
    main()
