import os

import numpy as np
from math import gcd

from scipy.signal import butter, sosfilt, lfilter, resample_poly

from config import (
    ALIGN_WIN, FS, BANDPASS_LOW, BANDPASS_HIGH, BANDPASS_ORDER, GROUP_DELAY_SAMPLES,
    WIN_PRE, WIN_POST, WIN_LEN,
    METRICS_DIR,
    PT_BAND_LOW, PT_BAND_HIGH, PT_BAND_ORDER, PT_MWI_WINDOW_MS, PT_REFRACTORY_MS,
)


def design_bandpass_sos():
    sos = butter(BANDPASS_ORDER, [BANDPASS_LOW, BANDPASS_HIGH], btype="bandpass", fs=FS, output="sos")
    return sos

def apply_bandpass(signal: np.ndarray, sos: np.ndarray) -> np.ndarray:
    return sosfilt(sos, signal, axis=0, zi=None)

def _pt_bandpass(signal: np.ndarray, fs: int) -> np.ndarray:
    sos = butter(PT_BAND_ORDER, [PT_BAND_LOW, PT_BAND_HIGH], btype="bandpass", fs=fs, output="sos")
    return sosfilt(sos, signal)


def _pt_derivative(signal: np.ndarray, fs: int) -> np.ndarray:
    T = 1.0 / fs
    b = np.array([1, 2, 0, -2, -1], dtype=np.float64) / (8 * T)
    return lfilter(b, [1.0], signal)


def _pt_square(signal: np.ndarray) -> np.ndarray:
    return signal ** 2


def _pt_moving_window_integration(signal: np.ndarray, fs: int) -> np.ndarray:
    n = max(1, round(PT_MWI_WINDOW_MS / 1000 * fs))
    b = np.ones(n, dtype=np.float64) / n
    return lfilter(b, [1.0], signal)


def _pt_adaptive_threshold_detect(integrated: np.ndarray, fs: int) -> np.ndarray:
    n = len(integrated)
    refractory = max(1, round(PT_REFRACTORY_MS / 1000 * fs))

    candidates = np.where(
        (integrated[1:-1] > integrated[:-2]) & (integrated[1:-1] >= integrated[2:])
    )[0] + 1
    if len(candidates) == 0:
        return np.array([], dtype=int)

    init_n = min(n, 2 * fs)
    spki = float(np.max(integrated[:init_n]))
    npki = float(np.mean(integrated[:init_n]))

    peaks = []
    last_peak = -refractory
    for i in candidates:
        if i - last_peak < refractory:
            continue
        value = integrated[i]
        threshold1 = npki + 0.25 * (spki - npki)
        if value > threshold1:
            spki = 0.125 * value + 0.875 * spki
            peaks.append(i)
            last_peak = i
        else:
            npki = 0.125 * value + 0.875 * npki

    return np.array(peaks, dtype=int)


def pan_tompkins_detect(signal: np.ndarray, fs: int = FS) -> np.ndarray:
    qrs = _pt_bandpass(signal, fs)
    deriv = _pt_derivative(qrs, fs)
    squared = _pt_square(deriv)
    integrated = _pt_moving_window_integration(squared, fs)
    return _pt_adaptive_threshold_detect(integrated, fs)


def segment_beats(signal: np.ndarray, r_locations: np.ndarray) -> np.ndarray:
    windows = []
    for r in r_locations:
        start, end = r - WIN_PRE, r + WIN_POST
        if start < 0 or end > len(signal):
            continue
        window = signal[start:end]
        if len(window) != WIN_LEN:
            continue
        windows.append(window)

    if not windows:
        return np.empty((0, WIN_LEN), dtype=np.float32)
    return np.asarray(windows, dtype=np.float32)


def zscore_per_window(windows: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    mean = windows.mean(axis=1, keepdims=True)
    std = windows.std(axis=1, keepdims=True)
    return ((windows - mean) / (std + eps)).astype(np.float32)


RESIDU_DS1 = os.path.join(METRICS_DIR, "jitter", "residu_ds1.npy")


def jitter_r(r_locations: np.ndarray, delta: int = 0, rng=None,
             model: str = "empiris") -> np.ndarray:
    r = np.asarray(r_locations, dtype=np.int64)
    if model != "empiris" and delta == 0:
        return r
    rng = np.random.default_rng() if rng is None else rng

    if model == "empiris":
        kolam = np.load(RESIDU_DS1)
        geser = rng.choice(kolam, size=len(r)).astype(np.int64)
    elif model == "seragam":
        geser = rng.integers(-delta, delta + 1, size=len(r))
    elif model == "normal":
        geser = np.rint(rng.normal(0.0, float(delta), size=len(r))).astype(np.int64)
    else:
        raise ValueError(f"model jitter tak dikenal: {model}")

    return np.maximum.accumulate(r + geser)


def resample_to_fs(signal: np.ndarray, r_locations: np.ndarray,
                   fs_asal: int, fs_target: int = FS):
    r = np.asarray(r_locations, dtype=np.int64)
    if fs_asal == fs_target:
        return np.asarray(signal, dtype=np.float32), r

    faktor = gcd(int(fs_asal), int(fs_target))
    up, down = int(fs_target) // faktor, int(fs_asal) // faktor

    baru = resample_poly(np.asarray(signal, dtype=np.float64), up, down)
    r_baru = np.rint(r * (up / down)).astype(np.int64)

    if len(r_baru) > 1 and np.any(np.diff(r_baru) <= 0):
        raise ValueError(
            f"resample {fs_asal}->{fs_target} Hz membuat R-peak bertabrakan "
            f"(RR <= 0). Perlu cari-ulang puncak, bukan pembulatan."
        )

    return baru.astype(np.float32), r_baru


def selaraskan_r(r_locations: np.ndarray, filtered: np.ndarray,
                 win: int = ALIGN_WIN) -> np.ndarray:
    r = np.asarray(r_locations, dtype=np.int64)
    n = len(filtered)
    hasil = np.empty_like(r)
    for i, lo in enumerate(r):
        a, b = max(0, lo - win), min(n, lo + win + 1)
        hasil[i] = a + int(np.argmax(filtered[a:b])) if b > a else lo
    return hasil - GROUP_DELAY_SAMPLES
