"""features_rr — Fase 2: mapping label & fitur RR. Walkthrough: docs/features-rr-walkthrough.md"""
import numpy as np

from config import FS, AAMI_MAP, ARRHYTHMIA_SYMBOLS, RR_LOCAL_WINDOW_BEATS


def to_aami_class(symbol: str) -> str:
    return AAMI_MAP[symbol]


def to_binary_label(aami_class: str) -> int:
    return int(aami_class in ARRHYTHMIA_SYMBOLS)


def compute_rr_features(r_locations: np.ndarray, fs: int = FS) -> np.ndarray:
    r = np.asarray(r_locations, dtype=np.float64)
    m = len(r)
    out = np.full((m, 3), np.nan, dtype=np.float64)
    if m < 2:
        return out.astype(np.float32)

    d = np.diff(r) / fs

    w = RR_LOCAL_WINDOW_BEATS
    j = np.arange(m - 1)
    start = np.maximum(0, j - w + 1)
    csum = np.concatenate(([0.0], np.cumsum(d)))
    local_avg = (csum[j + 1] - csum[start]) / (j + 1 - start)

    out[1:, 0] = d
    out[1:, 1] = d / local_avg
    out[2:, 2] = np.diff(d)
    return out.astype(np.float32)
