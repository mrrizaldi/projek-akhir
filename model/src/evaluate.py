"""evaluate — Fase 6: metrik biner dari probabilitas. Walkthrough: docs/evaluate-walkthrough.md"""
import numpy as np

from config import THRESHOLD


def confusion_counts(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    if y_true.shape != y_pred.shape:
        raise ValueError(f"bentuk beda: {y_true.shape} vs {y_pred.shape}")
    return {
        "tp": int(((y_pred == 1) & (y_true == 1)).sum()),
        "fn": int(((y_pred == 0) & (y_true == 1)).sum()),
        "fp": int(((y_pred == 1) & (y_true == 0)).sum()),
        "tn": int(((y_pred == 0) & (y_true == 0)).sum()),
    }


def binary_metrics(counts: dict) -> dict:
    tp, fn, fp, tn = counts["tp"], counts["fn"], counts["fp"], counts["tn"]
    div = lambda a, b: a / b if b else 0.0
    recall = div(tp, tp + fn)
    precision = div(tp, tp + fp)
    return {
        "accuracy": div(tp + tn, tp + tn + fp + fn),
        "precision": precision,
        "recall": recall,
        "specificity": div(tn, tn + fp),
        "f1": div(2 * precision * recall, precision + recall),
    }


def evaluate_probabilities(y_true, y_prob, threshold: float = THRESHOLD) -> dict:
    counts = confusion_counts(y_true, np.asarray(y_prob) >= threshold)
    return {"threshold": float(threshold), **counts, **binary_metrics(counts)}


def sweep_thresholds(y_true, y_prob, thresholds) -> list:
    return [evaluate_probabilities(y_true, y_prob, t) for t in thresholds]


def per_record_metrics(y_true, y_prob, records, threshold: float = THRESHOLD) -> list:
    y_true, y_prob, records = map(np.asarray, (y_true, y_prob, records))
    rows = []
    for rec in np.unique(records):
        m = records == rec
        row = evaluate_probabilities(y_true[m], y_prob[m], threshold)
        rows.append({"record": int(rec), "n_beat": int(m.sum()),
                     "n_aritmia": int(y_true[m].sum()), **row})
    return rows


def roc_auc(y_true, y_prob) -> float:
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=np.float64)
    n_pos, n_neg = int((y_true == 1).sum()), int((y_true == 0).sum())
    if n_pos == 0 or n_neg == 0:
        raise ValueError("AUC butuh kedua kelas ada")
    order = np.argsort(y_prob, kind="mergesort")
    ranks = np.empty(len(y_prob), dtype=np.float64)
    ranks[order] = np.arange(1, len(y_prob) + 1)
    sorted_p = y_prob[order]
    i = 0
    while i < len(sorted_p):
        j = i
        while j + 1 < len(sorted_p) and sorted_p[j + 1] == sorted_p[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + j + 2) / 2.0
        i = j + 1
    return float((ranks[y_true == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))
