"""Fase 8 — checklist PoC yang DIJALANKAN, bukan dicentang manual.

    make poc         (atau: python scripts/check_poc.py)

Tiap item PRD hal. 17 diverifikasi mekanis. Exit code != 0 kalau ada yang gagal,
jadi bisa dipakai di CI atau sebelum menulis Bab 4.
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (  # noqa: E402
    ARTIFACT_DIR, MAX_MODEL_KB, METRICS_DIR, PACED_EXCLUDED, DS1, DS2,
    PER_RECORD_DIR, PROCESSED_DIR, SEED, THRESHOLD,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
hasil = []


def cek(nama: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as e:                                   # noqa: BLE001
        ok, detail = False, f"{type(e).__name__}: {e}"
    hasil.append((ok, nama, detail))


def _baca_csv(path: str) -> dict:
    with open(path) as f:
        kolom = f.readline().strip().split(",")
        nilai = f.readline().strip().split(",")
    return dict(zip(kolom, nilai))


def reproducible():
    req = os.path.join(ROOT, "requirements.txt")
    paket = open(req).read() if os.path.exists(req) else ""
    kurang = [p for p in ("tensorflow", "wfdb", "numpy", "scipy") if p not in paket]
    if kurang:
        return False, f"requirements.txt kurang: {kurang}"
    src = open(os.path.join(ROOT, "scripts", "train_model.py")).read()
    if "np.random.seed(SEED)" not in src or "tf.random.set_seed(SEED)" not in src:
        return False, "seed tidak dikunci di train_model.py"
    return True, f"requirements.txt lengkap, SEED={SEED} dikunci di training & PTQ"


def preprocessing_kausal():
    src = open(os.path.join(ROOT, "src", "preprocessing.py")).read()
    if "filtfilt" in src:
        return False, "filtfilt ditemukan — JEBAKAN #1 PRD"
    if "sosfilt" not in src:
        return False, "sosfilt tidak dipakai"
    return True, "sosfilt (kausal), nol pemakaian filtfilt"


def split_terverifikasi():
    from src.dataset import assert_split_valid
    assert_split_valid()
    for r in DS1 + DS2:
        if not os.path.exists(os.path.join(PER_RECORD_DIR, f"{r}.npz")):
            return False, f"per_record/{r}.npz hilang — jalankan `make prep`"
    return True, f"DS1 {len(DS1)} + DS2 {len(DS2)} + paced {len(PACED_EXCLUDED)} = 48, disjoint"


def model_hybrid():
    from src.model import build_hybrid_model
    m = build_hybrid_model()
    n = m.count_params()
    if not 5000 <= n <= 7000:
        return False, f"count_params()={n}, di luar ~6.000"
    if len(m.inputs) != 2:
        return False, f"{len(m.inputs)} input, harus 2"
    return True, f"{n:,} param, 2 input, output {tuple(m.output.shape)}"


def metrik_fp32():
    path = os.path.join(METRICS_DIR, "fase6_metrics_fp32.csv")
    if not os.path.exists(path):
        return False, "fase6_metrics_fp32.csv belum ada — jalankan `make eval`"
    row = _baca_csv(path)
    recall = float(row["recall"])
    if recall <= 0.05:
        return False, f"recall Aritmia {recall:.4f} ~ 0 — ada bug, cek class_weight"
    png = os.path.join(METRICS_DIR, "fase6_confusion_fp32.png")
    if not os.path.exists(png):
        return False, "confusion matrix PNG belum ada"
    return True, (f"recall {recall:.4f}, precision {float(row['precision']):.4f}, "
                  f"AUC {float(row['auc']):.4f} @ threshold {row['threshold']}")


def model_int8():
    path = os.path.join(ARTIFACT_DIR, "model_int8.tflite")
    if not os.path.exists(path):
        return False, "model_int8.tflite belum ada — jalankan `make quantize`"
    kb = os.path.getsize(path) / 1024
    if kb >= MAX_MODEL_KB:
        return False, f"{kb:.2f} KB >= batas {MAX_MODEL_KB} KB"
    import tensorflow as tf
    interp = tf.lite.Interpreter(model_path=path)
    interp.allocate_tensors()
    dtypes = {t["dtype"].__name__ for t in interp.get_tensor_details()}
    if "float32" in dtypes:
        return False, f"masih ada tensor float32: {dtypes}"
    return True, f"{kb:.2f} KB < {MAX_MODEL_KB} KB, full-INT8 (dtype: {sorted(dtypes)})"


def tabel_delta():
    path = os.path.join(METRICS_DIR, "fase7_delta.csv")
    if not os.path.exists(path):
        return False, "fase7_delta.csv belum ada — jalankan `make quantize`"
    baris = {}
    with open(path) as f:
        f.readline()
        for ln in f:
            k, *v = ln.strip().split(",")
            baris[k] = v
    wajib = ["accuracy", "precision", "recall", "f1", "specificity", "auc", "ukuran_kb"]
    kurang = [k for k in wajib if k not in baris]
    if kurang:
        return False, f"baris kurang: {kurang}"
    d_recall = float(baris["recall"][2])
    catatan = "layak" if abs(d_recall) < 0.02 else "PERIKSA representative dataset"
    return True, f"lengkap; delta recall {d_recall:+.4f} ({catatan})"


def decision_tercatat():
    md = open(os.path.join(ROOT, "CLAUDE.md")).read()
    # HANYA seksi decision point — tabel lain (mis. indeks walkthrough) boleh kosong.
    seksi = re.search(r"## Decision point yang sudah di-lock(.*?)(?=\n## )", md, flags=re.S)
    if seksi is None:
        return False, "seksi 'Decision point yang sudah di-lock' tidak ditemukan"
    tabel = re.findall(r"^\|.*\*\(belum\)\*.*$", seksi.group(1), flags=re.M)
    if tabel:
        return False, f"{len(tabel)} decision point masih *(belum)*"
    for kunci in ("Orde Butterworth", "Beat tanpa `dRR`", "Strategi imbalance",
                  "Tipe I/O INT8", "Threshold"):
        if kunci not in md:
            return False, f"decision point '{kunci}' tidak tercatat"
    return True, "semua decision point terisi di tabel CLAUDE.md"


def main() -> None:
    cek("Reproducible (requirements + seed lock)", reproducible)
    cek("Preprocessing kausal (sosfilt, bukan filtfilt)", preprocessing_kausal)
    cek("Split inter-patient disjoint + paced dibuang", split_terverifikasi)
    cek("Model hybrid ~6.000 param, 2 input", model_hybrid)
    cek("Metrik float32 DS2 ada & recall tidak ~0", metrik_fp32)
    cek("Model INT8 < 20 KB, full-INT8", model_int8)
    cek("Tabel delta float32 vs INT8 lengkap", tabel_delta)
    cek("Semua decision point tercatat", decision_tercatat)

    print(f"\n{'':2} {'Checklist PoC (PRD Fase 8)':<46} Detail")
    print("-" * 100)
    for ok, nama, detail in hasil:
        print(f"{'[x]' if ok else '[ ]'} {nama:<46} {detail}")
    gagal = [n for ok, n, _ in hasil if not ok]
    print("-" * 100)
    if gagal:
        print(f"{len(gagal)} item BELUM beres: {gagal}")
        sys.exit(1)
    print(f"PoC LENGKAP — {len(hasil)}/{len(hasil)} item terverifikasi.")


if __name__ == "__main__":
    main()
