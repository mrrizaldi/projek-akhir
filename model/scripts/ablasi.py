import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf

from config import (
    ARTIFACT_DIR, DATASETS, DS1, METRICS_DIR, SEED, USE_HOS, VAL_RECORDS,
    N_RR_FEATURES, WIN_LEN, WIN_PRE, WIN_POST,
)
from src.dataset import bagi_train_test, record_int_id, records_tersedia
from src.evaluate import binary_metrics, confusion_counts, roc_auc, sweep_thresholds
from src.features_rr import (
    rakit_fitur_ritme, to_aami_class, to_binary_label,
)
from src.io_mitdb import load_record
from src.model import build_hybrid_model
from src.preprocessing import (
    apply_bandpass, design_bandpass_sos, jitter_r, segment_beats, selaraskan_r,
    zscore_per_window,
)
from src.train import train
from scripts.prep_beats import valid_beat_indices
from scripts.sweep_jitter import muat_ds2, rakit

OUT_DIR = os.path.join(METRICS_DIR, "ablasi")
F1_TIE_MARGIN = 0.005
SEED_DS2 = (11, 12, 13)


def catatan_latih(db_list) -> list:
    pasangan = [("mitdb", str(r)) for r in DS1]
    for db in db_list:
        if db == "mitdb":
            continue
        tersedia = records_tersedia(db)
        n_harap = DATASETS[db]["n_record"]
        if len(tersedia) != n_harap:
            raise ValueError(
                f"{db}: {len(tersedia)}/{n_harap} record — held-out `[::4]` akan "
                f"BEDA. Selesaikan download dulu (lihat n_record di config.py)."
            )
        pasangan += [(db, r) for r in bagi_train_test(tersedia)[0]]
    return pasangan


def rakit_ds1(sos, model_jitter: str, delta: int, salinan: int, rng,
              db_list=("mitdb",)) -> dict:
    W, R, Y, REC = [], [], [], []
    for db, rec in catatan_latih(db_list):
        signal, r0, sym, _ = load_record(rec, db=db)
        filtered = apply_bandpass(signal, sos)
        if DATASETS[db]["selaraskan"]:
            r0 = selaraskan_r(r0, filtered)
        label = np.array([to_binary_label(to_aami_class(s)) for s in sym], dtype=np.int8)
        n_salinan = salinan if db == "mitdb" else 0

        for salinan_ke in range(n_salinan + 1):
            r = r0 if salinan_ke == 0 or model_jitter == "none" else \
                jitter_r(r0, delta, rng, model_jitter)
            idx = valid_beat_indices(len(signal), r)
            w = zscore_per_window(segment_beats(filtered, r[idx]))
            W.append(w)
            R.append(rakit_fitur_ritme(r, w, idx))
            Y.append(label[idx])
            REC.append(np.full(len(idx), record_int_id(rec, db), dtype=np.int32))
            if model_jitter == "none":
                break
    return {"X_morph": np.concatenate(W).reshape(-1, WIN_LEN, 1).astype(np.float32),
            "X_rr": np.concatenate(R).astype(np.float32),
            "y": np.concatenate(Y), "records": np.concatenate(REC)}


def rakit_heldout(sos, db: str) -> dict:
    W, R, Y, A = [], [], [], []
    for rec in bagi_train_test(records_tersedia(db))[1]:
        signal, r0, sym, _ = load_record(rec, db=db)
        filtered = apply_bandpass(signal, sos)
        if DATASETS[db]["selaraskan"]:
            r0 = selaraskan_r(r0, filtered)
        idx = valid_beat_indices(len(signal), r0)
        w = zscore_per_window(segment_beats(filtered, r0[idx]))
        aami = np.array([to_aami_class(s) for s in sym])[idx]
        W.append(w)
        R.append(rakit_fitur_ritme(r0, w, idx))
        A.append(aami)
        Y.append(np.array([to_binary_label(a) for a in aami], dtype=np.int8))
    return {"X_morph": np.concatenate(W).reshape(-1, WIN_LEN, 1).astype(np.float32),
            "X_rr": np.concatenate(R).astype(np.float32),
            "y": np.concatenate(Y), "aami": np.concatenate(A)}


def ukur_array(model, d: dict, thr: float) -> dict:
    prob = model.predict([d["X_morph"], d["X_rr"]], verbose=0, batch_size=4096).ravel()
    pred = (prob >= thr).astype(int)
    m = binary_metrics(confusion_counts(d["y"], pred))
    m["auc"] = roc_auc(d["y"], prob)
    for k in ("S", "V", "F"):
        sel = d["aami"] == k
        m[f"recall_{k}"] = float(pred[sel].mean()) if sel.any() else float("nan")
    return m


def pisah_val(d: dict):
    is_val = np.isin(d["records"], VAL_RECORDS)
    ambil = lambda m: {k: v[m] for k, v in d.items()}
    return ambil(~is_val), ambil(is_val)


def kalibrasi(model, va: dict) -> float:
    prob = model.predict([va["X_morph"], va["X_rr"]], verbose=0, batch_size=4096).ravel()
    rows = sweep_thresholds(va["y"], prob, np.arange(0.05, 0.96, 0.05))
    f1_max = max(r["f1"] for r in rows)
    kandidat = [r for r in rows if f1_max - r["f1"] < F1_TIE_MARGIN]
    return float(max(kandidat, key=lambda r: r["recall"])["threshold"])


def ukur(model, cache, thr: float, model_jitter, seed: int) -> dict:
    X_morph, X_rr, y, aami = rakit(cache, model_jitter, 0, seed)
    prob = model.predict([X_morph, X_rr], verbose=0, batch_size=4096).ravel()
    pred = (prob >= thr).astype(int)
    m = binary_metrics(confusion_counts(y, pred))
    m["auc"] = roc_auc(y, prob)
    for k in ("S", "V", "F"):
        sel = aami == k
        m[f"recall_{k}"] = float(pred[sel].mean()) if sel.any() else float("nan")
    return m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--jitter", default="none", choices=["none", "empiris", "seragam"])
    ap.add_argument("--delta", type=int, default=0)
    ap.add_argument("--salinan", type=int, default=0,
                    help="jumlah tiruan ber-jitter di atas salinan bersih")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--seed", type=int, default=SEED,
                    help="ulangi varian yang sama dgn seed lain — selisih F1 "
                         "beberapa poin bisa cuma kebisingan inisialisasi")
    ap.add_argument("--tanpa-class-weight", action="store_true",
                    help="ablasi K1/T1: class_weight=None. Nilai terkunci "
                         "(balanced) tidak diubah — ini flag ablasi saja.")
    ap.add_argument("--swa", type=int, default=0, metavar="N",
                    help="ablasi T7: rata-ratakan bobot N epoch ber-val_auc "
                         "terbaik, bukan memungut argmax-nya. 0 = jalur terkunci.")
    ap.add_argument("--lr", type=float, default=0.0,
                    help="ablasi T12: learning rate Adam. 0 = bawaan 1e-3 = "
                         "jalur terkunci. val_auc memuncak di epoch 0 dgn 1e-3.")
    ap.add_argument("--lintas-db", action="store_true",
                    help="T8: ukur juga di held-out svdb (TEST-B) & incartdb "
                         "(TEST-C), 39 pasien. Threshold tetap dari VAL. Hasil "
                         "ke lintas_db.csv terpisah — skema ablasi.csv tak bergeser.")
    ap.add_argument("--db", nargs="+", default=["mitdb"], choices=list(DATASETS),
                    help="database LATIH. Bawaan mitdb saja = jalur terkunci, "
                         "byte-identik dengan ablasi sebelum Fase A. DS2 tetap "
                         "mitdb apa pun isinya.")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    t0 = time.time()

    sos = design_bandpass_sos()
    ds1 = rakit_ds1(sos, args.jitter, args.delta, args.salinan, rng, args.db)
    tr, va = pisah_val(ds1)
    print(f"[{args.tag}] window {WIN_PRE}/{WIN_POST}={WIN_LEN}  n_rr={N_RR_FEATURES}  "
          f"HOS={USE_HOS}  jitter={args.jitter} x{args.salinan}  db={'+'.join(args.db)}  "
          f"class_weight={'OFF' if args.tanpa_class_weight else 'balanced'}  "
          f"swa={args.swa or 'OFF'}  lr={args.lr or '1e-3 (bawaan)'}")
    print(f"[{args.tag}] train {len(tr['y']):,} beat ({int(tr['y'].sum()):,} aritmia)  "
          f"val {len(va['y']):,} ({int(va['y'].sum()):,})")

    model = build_hybrid_model()
    kw = {"epochs": args.epochs} if args.epochs else {}
    train(model, tr, va, pakai_class_weight=not args.tanpa_class_weight,
          swa_n=args.swa, lr=args.lr, **kw)

    thr = kalibrasi(model, va)
    print(f"[{args.tag}] threshold dari VAL = {thr:.2f}")

    cache = muat_ds2(sos)
    bersih = ukur(model, cache, thr, None, 0)
    kotor = [ukur(model, cache, thr, "empiris", s) for s in SEED_DS2]
    rerata = {k: float(np.mean([m[k] for m in kotor])) for k in bersih}

    if args.seed == SEED:
        model.save(os.path.join(ARTIFACT_DIR, f"model_fp32_{args.tag}.keras"))

    baris = {"tag": args.tag, "seed": args.seed,
             "win_pre": WIN_PRE, "win_post": WIN_POST,
             "hos": int(USE_HOS), "jitter": args.jitter, "salinan": args.salinan,
             "threshold": thr, "n_train": len(tr["y"]),
             "menit": round((time.time() - t0) / 60, 1)}
    baris.update({f"anot_{k}": v for k, v in bersih.items()})
    baris.update({f"jit_{k}": v for k, v in rerata.items()})

    out = os.path.join(OUT_DIR, "ablasi.csv")
    baru = not os.path.exists(out)
    with open(out, "a") as f:
        if baru:
            f.write(",".join(baris) + "\n")
        f.write(",".join(f"{v:.6f}" if isinstance(v, float) else str(v)
                         for v in baris.values()) + "\n")

    print(f"[{args.tag}] DS2 anotasi : recall {bersih['recall']:.4f}  "
          f"prec {bersih['precision']:.4f}  F1 {bersih['f1']:.4f}  AUC {bersih['auc']:.4f}")
    print(f"[{args.tag}] DS2 jitter  : recall {rerata['recall']:.4f}  "
          f"prec {rerata['precision']:.4f}  F1 {rerata['f1']:.4f}  AUC {rerata['auc']:.4f}")
    print(out)

    if args.lintas_db:
        out2 = os.path.join(OUT_DIR, "lintas_db.csv")
        for db, nama in (("svdb", "TEST-B"), ("incartdb", "TEST-C")):
            d = rakit_heldout(sos, db)
            m = ukur_array(model, d, thr)
            r = {"tag": args.tag, "seed": args.seed, "db": db, "set": nama,
                 "n_beat": len(d["y"]), "n_aritmia": int(d["y"].sum()),
                 "threshold": thr, **m}
            baru2 = not os.path.exists(out2)
            with open(out2, "a") as f:
                if baru2:
                    f.write(",".join(r) + "\n")
                f.write(",".join(f"{v:.6f}" if isinstance(v, float) else str(v)
                                 for v in r.values()) + "\n")
            print(f"[{args.tag}] {nama} {db:<9}: recall {m['recall']:.4f}  "
                  f"prec {m['precision']:.4f}  F1 {m['f1']:.4f}  AUC {m['auc']:.4f}  "
                  f"({len(d['y']):,} beat)")


if __name__ == "__main__":
    main()
