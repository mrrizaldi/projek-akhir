"""Bandingkan recall per kelas pada RECALL TOTAL yang disamakan (T12).

    python scripts/cek_titik_operasi.py

Menjawab: apakah defisit recall S model ber-LR rendah NYATA, atau cuma akibat
thresholdnya jatuh di tempat lain? Aturan §A5 changelog 18 Sep melarang
membandingkan recall di dua titik operasi berbeda — jadi threshold tiap model
digeser sampai recall TOTAL-nya sama, baru recall per kelas diadu.

Model tersimpan = seed 42 saja (ablasi.py cuma menyimpan seed utama), jadi SATU
seed. Yang menguatkan bukan jumlah seed melainkan konsistensi arah di 6 titik.
"""
import sys, os, numpy as np
sys.path.insert(0, os.getcwd()); os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL","3")
from tensorflow import keras
from config import DS2, PER_RECORD_DIR, PROCESSED_DIR, ARTIFACT_DIR, AAMI_MAP

d = np.load(os.path.join(PROCESSED_DIR, "test.npz"))
sym = np.concatenate([np.load(f"{PER_RECORD_DIR}/{r}.npz")["symbols"] for r in DS2])
sym = np.array([s.decode() if isinstance(s, bytes) else str(s) for s in sym])
aami = np.array([AAMI_MAP[s] for s in sym])
y = d["y"].astype(int)

prob = {}
for tag in ("t8_lr1e3", "t8_lr3e4", "t8_lr1e4"):
    m = keras.models.load_model(os.path.join(ARTIFACT_DIR, f"model_fp32_{tag}.keras"))
    prob[tag] = m.predict([d["X_morph"], d["X_rr"]], batch_size=4096, verbose=0).ravel()

def pada_recall(p, target):
    """Threshold terendah yang memberi recall total >= target; -> (recall, recS, prec)."""
    for t in np.arange(0.999, 0.0, -0.001):
        pred = (p >= t).astype(int)
        rec = pred[y == 1].mean()
        if rec >= target:
            return rec, pred[aami == "S"].mean(), pred[aami == "V"].mean(), \
                   (y[pred == 1].mean() if pred.sum() else 0.0)
    return None

print("Recall S pada RECALL TOTAL yang disamakan (DS2, seed 42)\n")
print(f"{'recall total':>13} | " + " | ".join(f"{t:>21}" for t in prob))
print("-" * 80)
for target in (0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
    sel = []
    for t in prob:
        r = pada_recall(prob[t], target)
        sel.append(f"recS {r[1]:.3f} recV {r[2]:.3f}" if r else "         -           ")
    print(f"{target:>13.2f} | " + " | ".join(f"{s:>21}" for s in sel))
