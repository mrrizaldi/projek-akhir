"""Diagnosis titik operasi: seberapa jauh kalibrasi VAL dari optimum DS2?

    python scripts/cek_kalibrasi.py [--tag w128b fb_svdb ...]

DS2 dipakai untuk MENDIAGNOSIS, bukan MEMILIH. Threshold produksi tetap datang
dari VAL (§7 aturan 4). Kolom "DS2-opt" ada untuk mengukur berapa yang hilang,
bukan untuk dipakai.

Membandingkan tiga set kalibrasi yang semuanya SAH (bukan train, bukan DS2):
    VAL sekarang        5 pasien mitdb
    + svdb held-out    25 pasien
    + incartdb held-out 44 pasien

Catatan jujur: skrip ini memuat model yang tersimpan, dan ablasi.py cuma
menyimpan seed utama. Jadi hasilnya SATU seed — dan masalah sebenarnya
(variansi threshold antar-seed) butuh tiga seed untuk dibuktikan.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf  # noqa: E402

from config import ARTIFACT_DIR, PROCESSED_DIR, SEED  # noqa: E402
from scripts.ablasi import kalibrasi, pisah_val, rakit_ds1  # noqa: E402
from scripts.sweep_jitter import muat_ds2, rakit  # noqa: E402
from src.preprocessing import design_bandpass_sos  # noqa: E402


def gabung(*ds) -> dict:
    return {k: np.concatenate([d[k] for d in ds])
            for k in ("X_morph", "X_rr", "y", "records")}


def muat_npz(nama: str) -> dict:
    with np.load(os.path.join(PROCESSED_DIR, nama)) as z:
        return {k: z[k] for k in ("X_morph", "X_rr", "y", "records")}


def set_kalibrasi(sos) -> dict:
    val = pisah_val(rakit_ds1(sos, "empiris", 0, 2,
                              np.random.default_rng(SEED), ["mitdb", "svdb"]))[1]
    sv, ic = muat_npz("test_svdb.npz"), muat_npz("test_incartdb.npz")
    return {"VAL (5 pasien)": val,
            "+svdb held-out": gabung(val, sv),
            "+svdb+incart": gabung(val, sv, ic)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", nargs="+",
                    default=["w128b", "fb_svdb", "fb_svdb_nocw", "fb_multi"])
    args = ap.parse_args()

    sos = design_bandpass_sos()
    SET = set_kalibrasi(sos)
    for nm, d in SET.items():
        print(f"  {nm:18} {len(np.unique(d['records'])):>3} pasien, {len(d['y']):>7,} baris")

    Xm, Xr, y, _ = rakit(muat_ds2(sos), None, 0, 0)
    pos = int(y.sum())
    grid = np.arange(0.05, 0.996, 0.01)

    print(f"\n{'model':16}" + "".join(f"{n:>24}" for n in SET) + f"{'DS2-opt (diagnosis)':>22}")
    print("-" * (16 + 24 * len(SET) + 22))
    for tag in args.tag:
        path = os.path.join(ARTIFACT_DIR, f"model_fp32_{tag}.keras")
        if not os.path.exists(path):
            print(f"{tag:16} (model belum tersimpan)")
            continue
        prob = tf.keras.models.load_model(path).predict(
            [Xm, Xr], verbose=0, batch_size=8192).ravel()

        def f1_at(t):
            pred = prob >= t
            tp = int((pred & (y == 1)).sum())
            fp = int((pred & (y == 0)).sum())
            if tp == 0:
                return 0.0
            p, r = tp / (tp + fp), tp / pos
            return 2 * p * r / (p + r)

        baris = f"{tag:16}"
        for d in SET.values():
            t = kalibrasi(tf.keras.models.load_model(path), d)
            baris += f"  thr {t:.2f} -> {f1_at(t):.4f}"
        to = float(grid[np.argmax([f1_at(t) for t in grid])])
        print(baris + f"{'':>4}{to:.2f} -> {f1_at(to):.4f}")


if __name__ == "__main__":
    main()
