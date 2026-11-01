import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tensorflow as tf

from config import AAMI_MAP, ARTIFACT_DIR, DS2, METRICS_DIR, PER_RECORD_DIR, PROCESSED_DIR, THRESHOLD
from src.evaluate import average_precision, evaluate_probabilities, mcc, per_record_metrics
from src.quantize import predict_tflite

KELAS_ARITMIA = ("S", "V", "F")
BERKAS_KELUARAN = "fase7_metrik_tambahan.csv"
BERKAS_PER_REKAMAN_INT8 = "fase7_per_record_int8.csv"


def simbol_aami_ds2() -> np.ndarray:
    simbol = []
    for rec in DS2:
        with np.load(os.path.join(PER_RECORD_DIR, f"{rec}.npz")) as z:
            simbol.append(z["symbols"])
    return np.array([AAMI_MAP[s] for s in np.concatenate(simbol)])


def ringkas(y, prob, records, aami) -> dict:
    hasil = evaluate_probabilities(y, prob, THRESHOLD)
    prediksi = prob >= THRESHOLD
    baris = per_record_metrics(y, prob, records, THRESHOLD)
    recall_rekaman = [r["recall"] for r in baris if r["n_aritmia"] > 0]
    ringkasan = {
        "pr_auc": average_precision(y, prob),
        "prevalensi": float(np.mean(y)),
        "mcc": mcc(hasil),
        "tp": hasil["tp"], "fn": hasil["fn"], "fp": hasil["fp"], "tn": hasil["tn"],
        "recall": hasil["recall"],
        "recall_rerata_rekaman": float(np.mean(recall_rekaman)),
        "recall_median_rekaman": float(np.median(recall_rekaman)),
        "n_rekaman_aritmia": len(recall_rekaman),
    }
    for kelas in KELAS_ARITMIA:
        anggota = aami == kelas
        ringkasan[f"recall_{kelas}"] = float(prediksi[anggota].mean())
        ringkasan[f"n_{kelas}"] = int(anggota.sum())
    return ringkasan


def main() -> None:
    with np.load(os.path.join(PROCESSED_DIR, "test.npz")) as z:
        ds2 = {k: z[k] for k in ("X_morph", "X_rr", "y", "records")}
    aami = simbol_aami_ds2()
    if len(aami) != len(ds2["y"]):
        raise ValueError(f"simbol {len(aami)} != detak DS2 {len(ds2['y'])}")
    if not np.array_equal(np.isin(aami, KELAS_ARITMIA + ("Q",)), ds2["y"] == 1):
        raise ValueError("simbol AAMI tidak sejajar dengan label DS2")

    model = tf.keras.models.load_model(os.path.join(ARTIFACT_DIR, "model_fp32.keras"))
    prob_fp32 = model.predict([ds2["X_morph"], ds2["X_rr"]], verbose=0).ravel()
    print(f"inferensi INT8 atas {len(ds2['y']):,} detak DS2 ...")
    prob_int8 = predict_tflite(os.path.join(ARTIFACT_DIR, "model_int8.tflite"),
                               ds2["X_morph"], ds2["X_rr"])

    fp32 = ringkas(ds2["y"], prob_fp32, ds2["records"], aami)
    int8 = ringkas(ds2["y"], prob_int8, ds2["records"], aami)
    berubah = (prob_fp32 >= THRESHOLD) != (prob_int8 >= THRESHOLD)

    print(f"\n{'Metrik':<24} {'Float32':>10} {'INT8':>10} {'Delta':>10}")
    for k in fp32:
        print(f"{k:<24} {fp32[k]:>10.4f} {int8[k]:>10.4f} {int8[k] - fp32[k]:>+10.4f}")
    print(f"label berubah float32 -> INT8: {int(berubah.sum())} dari {len(berubah)} "
          f"({100 * berubah.mean():.2f}%)")

    with open(os.path.join(METRICS_DIR, BERKAS_KELUARAN), "w") as f:
        f.write("metrik,float32,int8,delta\n")
        for k in fp32:
            f.write(f"{k},{fp32[k]:.6f},{int8[k]:.6f},{int8[k] - fp32[k]:+.6f}\n")
        f.write(f"label_berubah,,{int(berubah.sum())},\n")
        f.write(f"threshold,{THRESHOLD},{THRESHOLD},0\n")

    baris = per_record_metrics(ds2["y"], prob_int8, ds2["records"], THRESHOLD)
    with open(os.path.join(METRICS_DIR, BERKAS_PER_REKAMAN_INT8), "w") as f:
        f.write("record,n_beat,n_aritmia,tp,fn,fp,tn,recall,precision,specificity\n")
        for r in baris:
            f.write("%d,%d,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f\n" % (
                r["record"], r["n_beat"], r["n_aritmia"], r["tp"], r["fn"], r["fp"],
                r["tn"], r["recall"], r["precision"], r["specificity"]))


if __name__ == "__main__":
    main()
