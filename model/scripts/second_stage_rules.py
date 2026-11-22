import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf

from config import (
    ARTIFACT_DIR, FS, MIN_NAMED_PRECISION, R_IN_WINDOW, SEED,
)
from scripts.ablasi import kalibrasi, split_val, assemble_ds1
from scripts.sweep_jitter import load_ds2, rakit
from src.features_rr import _width_at_fraction
from src.preprocessing import design_bandpass_sos


def rule_features(windows: np.ndarray, rr: np.ndarray) -> dict:
    return {
        "qrsw2_ms": _width_at_fraction(windows, 0.5, R_IN_WINDOW) / FS * 1000,
        "qrsw4_ms": _width_at_fraction(windows, 0.25, R_IN_WINDOW) / FS * 1000,
        "rr_ratio": rr[:, 1] if rr.shape[1] == 3 else rr[:, 0],
    }


def calibrate_stage_thresholds(f: dict, aami: np.ndarray, flagged: np.ndarray,
                     min_presisi: float = MIN_NAMED_PRECISION) -> dict:
    v = (aami == "V") & flagged
    kandidat = []
    for chosen_thresholds in np.arange(10, 121, 2.0):
        pred = flagged & (f["qrsw2_ms"] > chosen_thresholds)
        n = int(pred.sum())
        if n < 20:
            continue
        p = int((pred & v).sum()) / n
        if p >= min_presisi:
            kandidat.append((float(chosen_thresholds), p, int((pred & v).sum()) / max(int(v.sum()), 1)))
    if not kandidat:
        return {"qrsw2_ms": None, "presisi_val": float("nan"), "cakupan_val": 0.0}
    chosen_thresholds, p, c = kandidat[0]
    return {"qrsw2_ms": chosen_thresholds, "presisi_val": p, "cakupan_val": c}


def name_label(f: dict, flagged: np.ndarray, chosen_thresholds: dict) -> np.ndarray:
    out = np.full(len(flagged), "Normal", dtype="<U12")
    out[flagged] = "tak dinamai"
    if chosen_thresholds["qrsw2_ms"] is not None:
        out[flagged & (f["qrsw2_ms"] > chosen_thresholds["qrsw2_ms"])] = "V"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="fd_both")
    args = ap.parse_args()

    sos = design_bandpass_sos()
    path = os.path.join(ARTIFACT_DIR, f"model_fp32_{args.tag}.keras")
    model = tf.keras.models.load_model(path)

    va = split_val(assemble_ds1(sos, "empiris", 0, 2,
                             np.random.default_rng(SEED), ["mitdb", "svdb"]))[1]
    thr = kalibrasi(model, va)
    print(f"[{args.tag}] stage 1 threshold from VAL = {thr:.2f}")

    from src.io_mitdb import load_record
    from src.preprocessing import apply_bandpass, segment_beats, zscore_per_window
    from src.features_rr import assemble_rhythm_features, to_aami_class
    from scripts.prep_beats import valid_beat_indices
    from config import VAL_RECORDS
    W, RR, A = [], [], []
    for rec in VAL_RECORDS:
        sig, r, sym, _ = load_record(str(rec))
        filt = apply_bandpass(sig, sos)
        idx = valid_beat_indices(len(sig), r)
        w = zscore_per_window(segment_beats(filt, r[idx]))
        W.append(w); RR.append(assemble_rhythm_features(r, w, idx))
        A.append(np.array([to_aami_class(sym[i]) for i in idx]))
    Wv, RRv, Av = np.concatenate(W), np.concatenate(RR), np.concatenate(A)
    prob_v = model.predict([Wv.reshape(-1, Wv.shape[1], 1), RRv],
                           verbose=0, batch_size=8192).ravel()
    fv = rule_features(Wv, RRv)
    chosen_thresholds = calibrate_stage_thresholds(fv, Av, prob_v >= thr)
    if chosen_thresholds["qrsw2_ms"] is None:
        print(f"[{args.tag}] NO threshold passes precision {MIN_NAMED_PRECISION:.0%} "
              f"on VAL -> V name is not shown. Silence beats a wrong name.")
    else:
        print(f"[{args.tag}] QRSw2 threshold from VAL = {chosen_thresholds['qrsw2_ms']:.0f} ms "
              f"(V precision on VAL {chosen_thresholds['presisi_val']:.1%}, coverage {chosen_thresholds['cakupan_val']:.1%})")

    Xm, Xr, y, aami = rakit(load_ds2(sos), None, 0, 0)
    prob = model.predict([Xm, Xr], verbose=0, batch_size=8192).ravel()
    flagged = prob >= thr
    f = rule_features(Xm[:, :, 0], Xr)
    label = name_label(f, flagged, chosen_thresholds)

    print(f"\n[{args.tag}] DS2: what the device SHOWS vs the annotation truth")
    print(f"{'':14}" + "".join(f"{k:>10}" for k in ("N","S","V","F","Q")) + f"{'total':>8}")
    for set_name in ("Normal", "V", "tak dinamai"):
        sel = label == set_name
        print(f"{set_name:14}" + "".join(f"{int((sel & (aami==k)).sum()):>10}"
                                  for k in ("N","S","V","F","Q"))
              + f"{int(sel.sum()):>8}")
    n_flagged = int(flagged.sum())
    v_lbl = label == "V"
    print(f"\n  beats flagged arrhythmia: {n_flagged}")
    print(f"  named V                 : {int(v_lbl.sum())} "
          f"({100*v_lbl.sum()/n_flagged:.1f}% of the flagged)")
    tp_v = int((v_lbl & (aami == "V")).sum())
    print(f"    correct V             : {tp_v}  -> V name precision {100*tp_v/max(int(v_lbl.sum()),1):.1f}%")
    print(f"    actually F          : {int((v_lbl & (aami=='F')).sum())}  (F = half of V, "
          f"can be kept)")
    print(f"    actually N (stage 1 FP): {int((v_lbl & (aami=='N')).sum())}")
    print(f"  unnamed                 : {int((label=='tak dinamai').sum())} "
          f"({100*(label=='tak dinamai').sum()/n_flagged:.1f}%)")
    print(f"\n  stage 1 recall V {100*(flagged & (aami=='V')).sum()/max(int((aami=='V').sum()),1):.1f}% "
          f"-> hard ceiling for the V name")


if __name__ == "__main__":
    main()
