"""preprocessing — Fase 1: filter kausal + Pan-Tompkins + segmentasi + z-score.

Modul MURNI: masuk array, keluar array. Tanpa print/plot/tulis file — itu ada
di scripts/plot_fase1.py. Spesifikasi lengkap: PRD_Model_Aritmia_TinyML.pdf hal 7-9.

Urutan pemakaian:
    apply_bandpass(load_record().signal, design_bandpass_sos())
        -> segment_beats(..., r_locations dari io_mitdb.load_record())
        -> zscore_per_window(...)
    pan_tompkins_detect() TIDAK di jalur ini — lihat catatan perannya sendiri.
"""
import numpy as np
from scipy.signal import butter, sosfilt, lfilter

from config import (
    FS, BANDPASS_LOW, BANDPASS_HIGH, BANDPASS_ORDER, WIN_PRE, WIN_POST, WIN_LEN,
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
    # Kernel turunan klasik Pan-Tompkins [-1,-2,0,2,1]/(8T), digeser 2 sampel
    # (b = [1,2,0,-2,-1]) supaya causal — lfilter cuma pakai x[n], x[n-1], ...
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
