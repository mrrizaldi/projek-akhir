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


def hos_features(windows: np.ndarray) -> np.ndarray:
    w = np.asarray(windows, dtype=np.float64)
    kurt = (w ** 4).mean(axis=1)
    skew = (w ** 3).mean(axis=1)
    return np.stack([kurt, skew], axis=1).astype(np.float32)


def _lebar_pada_fraksi(windows: np.ndarray, frac: float, r_idx: int,
                       cari: int = 4) -> np.ndarray:
    w = np.asarray(windows, dtype=np.float64)
    k, n = w.shape
    if k == 0:
        return np.zeros(0)

    lo, hi = max(0, r_idx - cari), min(n, r_idx + cari + 1)
    puncak_idx = lo + np.argmax(w[:, lo:hi], axis=1)
    puncak = w[np.arange(k), puncak_idx]
    ambang = (frac * puncak)[:, None]

    idx = np.arange(n)[None, :]
    bawah = w < ambang
    kiri_ok = bawah & (idx < puncak_idx[:, None])
    kanan_ok = bawah & (idx > puncak_idx[:, None])
    kiri = np.where(kiri_ok.any(1), (idx * kiri_ok).max(1), 0)
    kanan = np.where(kanan_ok.any(1), np.where(kanan_ok, idx, n).min(1), n - 1)
    return (kanan - kiri).astype(np.float64)


def qrs_width_features(windows: np.ndarray, r_idx: int = None,
                       w: int = RR_LOCAL_WINDOW_BEATS) -> np.ndarray:
    from config import R_IN_WINDOW
    r_idx = R_IN_WINDOW if r_idx is None else r_idx
    kolom = []
    for frac in (0.5, 0.25):
        lebar = _lebar_pada_fraksi(windows, frac, r_idx)
        j = np.arange(len(lebar))
        start = np.maximum(0, j - w + 1)
        csum = np.concatenate(([0.0], np.cumsum(lebar)))
        rerata = (csum[j + 1] - csum[start]) / (j + 1 - start)
        kolom.append(lebar / np.maximum(rerata, 1e-8))
    return np.stack(kolom, axis=1).astype(np.float32)


def compute_rr_ratio_features(r_locations: np.ndarray, fs: int = FS) -> np.ndarray:
    r = np.asarray(r_locations, dtype=np.float64)
    m = len(r)
    out = np.full((m, 4), np.nan, dtype=np.float64)
    if m < 3:
        return out.astype(np.float32)

    d = np.diff(r) / fs
    w = RR_LOCAL_WINDOW_BEATS
    j = np.arange(m - 1)
    start = np.maximum(0, j - w + 1)
    csum = np.concatenate(([0.0], np.cumsum(d)))
    n_pakai = j + 1 - start
    avg = (csum[j + 1] - csum[start]) / n_pakai
    csum2 = np.concatenate(([0.0], np.cumsum(d ** 2)))
    var = np.maximum((csum2[j + 1] - csum2[start]) / n_pakai - avg ** 2, 0.0)
    std = np.sqrt(var)

    rr0 = d
    out[1:, 0] = rr0 / avg
    out[1:-1, 1] = d[1:] / rr0[:-1]
    out[2:, 2] = rr0[:-1] / rr0[1:]
    out[1:, 3] = (rr0 - avg) / np.maximum(std, 1e-8)
    return out.astype(np.float32)


def rakit_fitur_ritme(r_locations: np.ndarray, windows: np.ndarray,
                      idx: np.ndarray) -> np.ndarray:
    from config import USE_HOS, USE_QRSW, USE_RR_RATIO
    dasar = (compute_rr_ratio_features(r_locations) if USE_RR_RATIO
             else compute_rr_features(r_locations))[idx]
    bagian = [dasar]
    if USE_HOS:
        bagian.append(hos_features(windows))
    if USE_QRSW:
        bagian.append(qrs_width_features(windows))
    return np.hstack(bagian).astype(np.float32) if len(bagian) > 1 else dasar
