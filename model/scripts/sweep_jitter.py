"""Fase 6c — metrik sebagai fungsi error segmentasi (protokol Dias 2021 Tabel 3).

    python scripts/sweep_jitter.py [--model model_fp32.keras] [--tag dasar]

Semua angka Fase 6 dipotong dari R-peak ANOTASI yang sempurna. Di alat, R datang
dari Pan-Tompkins yang meleset. Skrip ini mengukur berapa metrik yang hilang
sebagai fungsi besarnya kemelesetan — bukan satu angka, tapi satu kurva.

Dua sumbu dijalankan:
  seragam delta=0..18  protokol paper, bisa dibandingkan lurus dengan Tabel 3
  empiris              sebaran residu detektor kita sendiri (ukur_jitter.py)

Model tidak dilatih ulang di sini. Yang berubah cuma cara window dipotong.
DS2 dipakai MURNI untuk mengukur; tidak ada parameter yang diambil darinya.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import tensorflow as tf  # noqa: E402

from config import ARTIFACT_DIR, DS2, METRICS_DIR, THRESHOLD, USE_HOS, WIN_LEN  # noqa: E402
from src.evaluate import binary_metrics, confusion_counts, roc_auc  # noqa: E402
from src.features_rr import (
    rakit_fitur_ritme, to_aami_class, to_binary_label,
)
from src.io_mitdb import load_record  # noqa: E402
from src.preprocessing import (  # noqa: E402
    apply_bandpass, design_bandpass_sos, jitter_r, segment_beats, zscore_per_window,
)
from scripts.prep_beats import valid_beat_indices  # noqa: E402

OUT_DIR = os.path.join(METRICS_DIR, "jitter")
DELTA = list(range(0, 19, 2))
N_SEED = 5


def muat_ds2(sos) -> list:
    """Sekali baca + sekali bandpass. Yang diulang per delta cuma pemotongan."""
    simpan = []
    for rec in DS2:
        signal, r, sym, _ = load_record(str(rec))
        simpan.append({
            "rec": rec,
            "n": len(signal),
            "filtered": apply_bandpass(signal, sos),
            "r": r,
            "aami": np.array([to_aami_class(s) for s in sym]),
            "y": np.array([to_binary_label(to_aami_class(s)) for s in sym], dtype=np.int8),
        })
    return simpan


def rakit(cache: list, model_jitter: str, delta: int, seed: int):
    """Potong ulang seluruh DS2 dengan satu setelan jitter."""
    rng = np.random.default_rng(seed)
    W, R, Y, A = [], [], [], []
    for d in cache:
        r = d["r"] if (model_jitter is None) else jitter_r(d["r"], delta, rng, model_jitter)
        idx = valid_beat_indices(d["n"], r)
        w = zscore_per_window(segment_beats(d["filtered"], r[idx]))
        W.append(w)
        R.append(rakit_fitur_ritme(r, w, idx))
        Y.append(d["y"][idx])            # label dari anotasi asli, tidak ikut geser
        A.append(d["aami"][idx])
    return (np.concatenate(W).reshape(-1, WIN_LEN, 1), np.concatenate(R),
            np.concatenate(Y), np.concatenate(A))


def ukur(model, cache, model_jitter, delta, seed) -> dict:
    X_morph, X_rr, y, aami = rakit(cache, model_jitter, delta, seed)
    prob = model.predict([X_morph, X_rr], verbose=0, batch_size=4096).ravel()
    pred = (prob >= THRESHOLD).astype(int)
    m = binary_metrics(confusion_counts(y, pred))
    baris = {"model_jitter": model_jitter or "anotasi", "delta": delta, "seed": seed,
             "n": len(y), **m, "auc": roc_auc(y, prob)}
    for k in ("S", "V", "F"):            # recall per superclass AAMI, ala paper
        sel = aami == k
        baris[f"recall_{k}"] = float(pred[sel].mean()) if sel.any() else float("nan")
    return baris


def plot(rows: list, out_path: str) -> None:
    ser = [r for r in rows if r["model_jitter"] == "seragam"]
    emp = [r for r in rows if r["model_jitter"] == "empiris"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    for ax, key, judul in zip(axes, ("recall", "precision", "f1"),
                              ("Recall Aritmia", "Precision", "F1")):
        mean = [np.mean([r[key] for r in ser if r["delta"] == d]) for d in DELTA]
        lo = [np.min([r[key] for r in ser if r["delta"] == d]) for d in DELTA]
        hi = [np.max([r[key] for r in ser if r["delta"] == d]) for d in DELTA]
        ax.plot(DELTA, mean, "o-", color="#3b6ea5", label="jitter seragam ±δ")
        ax.fill_between(DELTA, lo, hi, alpha=0.2, color="#3b6ea5")
        if emp:
            e = np.mean([r[key] for r in emp])
            ax.axhline(e, color="#c0392b", ls="--",
                       label=f"jitter empiris (detektor kita) {e:.3f}")
        ax.set_xlabel("δ (sampel)")
        ax.set_title(judul)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Ketahanan terhadap error segmentasi di DS2 — model dilatih tanpa jitter")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="model_fp32.keras")
    ap.add_argument("--tag", default="dasar")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    model = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, args.model))
    cache = muat_ds2(design_bandpass_sos())

    rows = [ukur(model, cache, None, 0, 0)]
    print(f"{'jitter':>8} {'δ':>3} {'seed':>4} {'recall':>7} {'prec':>7} {'F1':>7} "
          f"{'AUC':>7} {'reS':>6} {'reV':>6}")
    cetak = lambda r: print(
        f"{r['model_jitter']:>8} {r['delta']:>3} {r['seed']:>4} {r['recall']:>7.4f} "
        f"{r['precision']:>7.4f} {r['f1']:>7.4f} {r['auc']:>7.4f} "
        f"{r['recall_S']:>6.3f} {r['recall_V']:>6.3f}")
    cetak(rows[0])

    for delta in DELTA:
        for seed in range(N_SEED):
            if delta == 0 and seed > 0:
                continue                 # δ=0 deterministik, sekali cukup
            rows.append(ukur(model, cache, "seragam", delta, seed))
            cetak(rows[-1])
    for seed in range(N_SEED):
        rows.append(ukur(model, cache, "empiris", 0, seed))
        cetak(rows[-1])

    kolom = list(rows[0])
    out = os.path.join(OUT_DIR, f"sweep_jitter_{args.tag}.csv")
    with open(out, "w") as f:
        f.write(",".join(kolom) + "\n")
        for r in rows:
            f.write(",".join(f"{r[k]:.6f}" if isinstance(r[k], float) else str(r[k])
                             for k in kolom) + "\n")
    plot(rows, os.path.join(OUT_DIR, f"sweep_jitter_{args.tag}.png"))
    print(f"\n{out}")


if __name__ == "__main__":
    main()
