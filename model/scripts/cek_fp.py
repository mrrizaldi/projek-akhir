import argparse
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ARTIFACT_DIR, DS2, PER_RECORD_DIR, PROCESSED_DIR, THRESHOLD


def panjang_run(mask: np.ndarray, records: np.ndarray) -> np.ndarray:
    hasil = []
    for r in np.unique(records):
        s = mask[records == r]
        i = 0
        while i < len(s):
            if s[i]:
                j = i
                while j + 1 < len(s) and s[j + 1]:
                    j += 1
                hasil.append(j - i + 1)
                i = j + 1
            else:
                i += 1
    return np.array(hasil, dtype=int)


def ringkas_run(nama: str, mask: np.ndarray, records: np.ndarray) -> None:
    R = panjang_run(mask, records)
    n = int(R.sum())
    if n == 0:
        print(f"{nama:<18} tidak ada")
        return
    print(f"{nama:<18} {n:>5} beat  {len(R):>5} run  "
          f"tunggal {100 * R[R == 1].sum() / n:5.1f}%  "
          f"run>=3 {100 * R[R >= 3].sum() / n:5.1f}%  terpanjang {R.max()}")


def muat_simbol(records_ds2) -> np.ndarray:
    sym = np.concatenate([np.load(os.path.join(PER_RECORD_DIR, f"{r}.npz"))["symbols"]
                          for r in records_ds2])
    return np.array([s.decode() if isinstance(s, bytes) else str(s) for s in sym])


def main() -> None:
    ap = argparse.ArgumentParser(description="Asal false positive DS2: sebaran per record, panjang run TP vs FP, FP per simbol. DS2 hanya mendiagnosis, tidak memilih parameter.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    args = ap.parse_args()

    import tensorflow as tf
    from tensorflow import keras

    d = np.load(os.path.join(PROCESSED_DIR, "test.npz"))
    y, rec = d["y"].astype(int), d["records"]
    sym = muat_simbol(DS2)
    if len(sym) != len(y):
        raise ValueError(f"simbol {len(sym)} != beat {len(y)} — urutan DS2 tidak cocok")

    model = keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))
    prob = model.predict([d["X_morph"], d["X_rr"]], batch_size=512, verbose=0).ravel()
    pred = (prob >= args.threshold).astype(int)

    tp_mask = (pred == 1) & (y == 1)
    fp_mask = (pred == 1) & (y == 0)
    n_fp = int(fp_mask.sum())
    print(f"threshold {args.threshold}  |  {len(y)} beat  |  "
          f"TP {int(tp_mask.sum())}  FP {n_fp}\n")

    print("== 1. Sebaran FP per record ==")
    print(f"{'rec':>5} {'FP':>6} {'%tot':>6} {'kum%':>6} {'FPR':>8}")
    per_rec = sorted(((int(r), int((fp_mask & (rec == r)).sum()),
                       int(((y == 0) & (rec == r)).sum()))
                      for r in np.unique(rec)), key=lambda t: -t[1])
    kum = 0
    for r, fp, neg in per_rec[:8]:
        kum += fp
        print(f"{r:>5} {fp:>6} {100 * fp / n_fp:5.1f}% {100 * kum / n_fp:5.1f}% "
              f"{fp / neg if neg else 0:8.4f}")
    print(f"8 record teratas = {100 * kum / n_fp:.1f}% dari seluruh FP "
          f"({len(per_rec)} record total)\n")

    print("== 2. Panjang run: TP vs FP ==")
    ringkas_run("TP (pred=1,y=1)", tp_mask, rec)
    ringkas_run("FP (pred=1,y=0)", fp_mask, rec)
    for r, _, _ in per_rec[:2]:
        ringkas_run(f"  FP rec {r}", fp_mask & (rec == r), rec)
    print("\nVonis k-dari-n: aturan 'k beat berturut-turut' menolong hanya kalau FP\n"
          "lebih TUNGGAL daripada TP. Bandingkan kolom 'tunggal' di atas.\n")

    print("== 3. FP per simbol MIT-BIH ==")
    print(f"{'sim':>4} {'FP':>6} {'%FP':>6} {'n_negatif':>10} {'FPR':>8}")
    for s, c in Counter(sym[fp_mask]).most_common():
        neg = int(((sym == s) & (y == 0)).sum())
        print(f"{s:>4} {c:>6} {100 * c / n_fp:5.1f}% {neg:>10} {c / neg if neg else 0:8.3f}")
    bbb = int((fp_mask & np.isin(sym, ["L", "R"])).sum())
    print(f"\nL+R (bundle branch block, dipetakan AAMI ke Normal): "
          f"{bbb} FP = {100 * bbb / n_fp:.1f}%")


if __name__ == "__main__":
    main()
