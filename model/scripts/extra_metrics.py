import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf

from config import AAMI_MAP, ARTIFACT_DIR, DS2, METRICS_DIR, PER_RECORD_DIR, PROCESSED_DIR, THRESHOLD
from src.evaluate import average_precision, evaluate_probabilities, mcc, per_record_metrics
from src.quantize import predict_tflite

ARRHYTHMIA_CLASSES = ("S", "V", "F")
OUTPUT_FILE = "fase7_metrik_tambahan.csv"
INT8_PER_RECORD_FILE = "fase7_per_record_int8.csv"


def aami_symbols_ds2() -> np.ndarray:
    symbols = []
    for rec in DS2:
        with np.load(os.path.join(PER_RECORD_DIR, f"{rec}.npz")) as z:
            symbols.append(z["symbols"])
    return np.array([AAMI_MAP[s] for s in np.concatenate(symbols)])


def digest(y, prob, records, aami) -> dict:
    metrics = evaluate_probabilities(y, prob, THRESHOLD)
    predicted = prob >= THRESHOLD
    per_record = per_record_metrics(y, prob, records, THRESHOLD)
    recall_recording = [r["recall"] for r in per_record if r["n_aritmia"] > 0]
    summary_metrics = {
        "pr_auc": average_precision(y, prob),
        "prevalensi": float(np.mean(y)),
        "mcc": mcc(metrics),
        "tp": metrics["tp"], "fn": metrics["fn"], "fp": metrics["fp"], "tn": metrics["tn"],
        "recall": metrics["recall"],
        "recall_rerata_rekaman": float(np.mean(recall_recording)),
        "recall_median_rekaman": float(np.median(recall_recording)),
        "n_rekaman_aritmia": len(recall_recording),
    }
    for aami_class in ARRHYTHMIA_CLASSES:
        members = aami == aami_class
        summary_metrics[f"recall_{aami_class}"] = float(predicted[members].mean())
        summary_metrics[f"n_{aami_class}"] = int(members.sum())
    return summary_metrics


def main() -> None:
    with np.load(os.path.join(PROCESSED_DIR, "test.npz")) as z:
        ds2 = {k: z[k] for k in ("X_morph", "X_rr", "y", "records")}
    aami = aami_symbols_ds2()
    if len(aami) != len(ds2["y"]):
        raise ValueError(f"symbols {len(aami)} != DS2 beats {len(ds2['y'])}")
    if not np.array_equal(np.isin(aami, ARRHYTHMIA_CLASSES + ("Q",)), ds2["y"] == 1):
        raise ValueError("AAMI symbols are not aligned with the DS2 labels")

    model = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))
    prob_fp32 = model.predict([ds2["X_morph"], ds2["X_rr"]], verbose=0).ravel()
    print(f"INT8 inference over {len(ds2['y']):,} DS2 beats ...")
    prob_int8 = predict_tflite(os.path.join(ARTIFACT_DIR, "model_int8.tflite"),
                               ds2["X_morph"], ds2["X_rr"])

    fp32 = digest(ds2["y"], prob_fp32, ds2["records"], aami)
    int8 = digest(ds2["y"], prob_int8, ds2["records"], aami)
    flipped = (prob_fp32 >= THRESHOLD) != (prob_int8 >= THRESHOLD)

    print(f"\n{'Metrik':<24} {'Float32':>10} {'INT8':>10} {'Delta':>10}")
    for k in fp32:
        print(f"{k:<24} {fp32[k]:>10.4f} {int8[k]:>10.4f} {int8[k] - fp32[k]:>+10.4f}")
    print(f"labels changed float32 -> INT8: {int(flipped.sum())} of {len(flipped)} "
          f"({100 * flipped.mean():.2f}%)")

    with open(os.path.join(METRICS_DIR, OUTPUT_FILE), "w") as f:
        f.write("metrik,float32,int8,delta\n")
        for k in fp32:
            f.write(f"{k},{fp32[k]:.6f},{int8[k]:.6f},{int8[k] - fp32[k]:+.6f}\n")
        f.write(f"label_berubah,,{int(flipped.sum())},\n")
        f.write(f"threshold,{THRESHOLD},{THRESHOLD},0\n")

    per_record = per_record_metrics(ds2["y"], prob_int8, ds2["records"], THRESHOLD)
    with open(os.path.join(METRICS_DIR, INT8_PER_RECORD_FILE), "w") as f:
        f.write("record,n_beat,n_aritmia,tp,fn,fp,tn,recall,precision,specificity\n")
        for r in per_record:
            f.write("%d,%d,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f\n" % (
                r["record"], r["n_beat"], r["n_aritmia"], r["tp"], r["fn"], r["fp"],
                r["tn"], r["recall"], r["precision"], r["specificity"]))


if __name__ == "__main__":
    main()
