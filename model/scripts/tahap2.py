import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf

from config import (
    ARTIFACT_DIR, FS, MIN_PRESISI_NAMA, R_IN_WINDOW, SEED,
)
from scripts.ablasi import kalibrasi, pisah_val, rakit_ds1
from scripts.sweep_jitter import muat_ds2, rakit
from src.features_rr import _lebar_pada_fraksi
from src.preprocessing import design_bandpass_sos


def fitur_aturan(windows: np.ndarray, rr: np.ndarray) -> dict:
    return {
        "qrsw2_ms": _lebar_pada_fraksi(windows, 0.5, R_IN_WINDOW) / FS * 1000,
        "qrsw4_ms": _lebar_pada_fraksi(windows, 0.25, R_IN_WINDOW) / FS * 1000,
        "rr_ratio": rr[:, 1] if rr.shape[1] == 3 else rr[:, 0],
    }


def kalibrasi_ambang(f: dict, aami: np.ndarray, ditandai: np.ndarray,
                     min_presisi: float = MIN_PRESISI_NAMA) -> dict:
    v = (aami == "V") & ditandai
    kandidat = []
    for amb in np.arange(10, 121, 2.0):
        pred = ditandai & (f["qrsw2_ms"] > amb)
        n = int(pred.sum())
        if n < 20:
            continue
        p = int((pred & v).sum()) / n
        if p >= min_presisi:
            kandidat.append((float(amb), p, int((pred & v).sum()) / max(int(v.sum()), 1)))
    if not kandidat:
        return {"qrsw2_ms": None, "presisi_val": float("nan"), "cakupan_val": 0.0}
    amb, p, c = kandidat[0]
    return {"qrsw2_ms": amb, "presisi_val": p, "cakupan_val": c}


def namai(f: dict, ditandai: np.ndarray, amb: dict) -> np.ndarray:
    out = np.full(len(ditandai), "Normal", dtype="<U12")
    out[ditandai] = "tak dinamai"
    if amb["qrsw2_ms"] is not None:
        out[ditandai & (f["qrsw2_ms"] > amb["qrsw2_ms"])] = "V"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="fd_both")
    args = ap.parse_args()

    sos = design_bandpass_sos()
    path = os.path.join(ARTIFACT_DIR, f"model_fp32_{args.tag}.keras")
    model = tf.keras.models.load_model(path)

    va = pisah_val(rakit_ds1(sos, "empiris", 0, 2,
                             np.random.default_rng(SEED), ["mitdb", "svdb"]))[1]
    thr = kalibrasi(model, va)
    print(f"[{args.tag}] threshold tahap 1 dari VAL = {thr:.2f}")

    from src.io_mitdb import load_record
    from src.preprocessing import apply_bandpass, segment_beats, zscore_per_window
    from src.features_rr import rakit_fitur_ritme, to_aami_class
    from scripts.prep_beats import valid_beat_indices
    from config import VAL_RECORDS
    W, RR, A = [], [], []
    for rec in VAL_RECORDS:
        sig, r, sym, _ = load_record(str(rec))
        filt = apply_bandpass(sig, sos)
        idx = valid_beat_indices(len(sig), r)
        w = zscore_per_window(segment_beats(filt, r[idx]))
        W.append(w); RR.append(rakit_fitur_ritme(r, w, idx))
        A.append(np.array([to_aami_class(sym[i]) for i in idx]))
    Wv, RRv, Av = np.concatenate(W), np.concatenate(RR), np.concatenate(A)
    prob_v = model.predict([Wv.reshape(-1, Wv.shape[1], 1), RRv],
                           verbose=0, batch_size=8192).ravel()
    fv = fitur_aturan(Wv, RRv)
    amb = kalibrasi_ambang(fv, Av, prob_v >= thr)
    if amb["qrsw2_ms"] is None:
        print(f"[{args.tag}] TIDAK ADA ambang yang lolos presisi {MIN_PRESISI_NAMA:.0%} "
              f"di VAL -> nama V tidak ditampilkan. Diam lebih baik dari salah.")
    else:
        print(f"[{args.tag}] ambang QRSw2 dari VAL = {amb['qrsw2_ms']:.0f} ms "
              f"(presisi V di VAL {amb['presisi_val']:.1%}, cakupan {amb['cakupan_val']:.1%})")

    Xm, Xr, y, aami = rakit(muat_ds2(sos), None, 0, 0)
    prob = model.predict([Xm, Xr], verbose=0, batch_size=8192).ravel()
    ditandai = prob >= thr
    f = fitur_aturan(Xm[:, :, 0], Xr)
    label = namai(f, ditandai, amb)

    print(f"\n[{args.tag}] DS2 — apa yang alat TAMPILKAN vs kebenaran anotasi")
    print(f"{'':14}" + "".join(f"{k:>10}" for k in ("N","S","V","F","Q")) + f"{'total':>8}")
    for nm in ("Normal", "V", "tak dinamai"):
        sel = label == nm
        print(f"{nm:14}" + "".join(f"{int((sel & (aami==k)).sum()):>10}"
                                  for k in ("N","S","V","F","Q"))
              + f"{int(sel.sum()):>8}")
    ditandai_n = int(ditandai.sum())
    v_lbl = label == "V"
    print(f"\n  beat ditandai aritmia   : {ditandai_n}")
    print(f"  dinamai V               : {int(v_lbl.sum())} "
          f"({100*v_lbl.sum()/ditandai_n:.1f}% dari yang ditandai)")
    tp_v = int((v_lbl & (aami == "V")).sum())
    print(f"    benar V               : {tp_v}  -> presisi nama V {100*tp_v/max(int(v_lbl.sum()),1):.1f}%")
    print(f"    sebenarnya F          : {int((v_lbl & (aami=='F')).sum())}  (F = separuh V, "
          f"bisa dipertahankan)")
    print(f"    sebenarnya N (FP t.1) : {int((v_lbl & (aami=='N')).sum())}")
    print(f"  tak dinamai             : {int((label=='tak dinamai').sum())} "
          f"({100*(label=='tak dinamai').sum()/ditandai_n:.1f}%)")
    print(f"\n  recall V tahap 1 {100*(ditandai & (aami=='V')).sum()/max(int((aami=='V').sum()),1):.1f}% "
          f"-> plafon keras untuk nama V")


if __name__ == "__main__":
    main()
