import os

import numpy as np
from scipy.signal import butter, sosfilt, lfilter

from config import (
    FS, BANDPASS_LOW, BANDPASS_HIGH, BANDPASS_ORDER, WIN_PRE, WIN_POST, WIN_LEN,
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


# ── Jitter posisi R (adaptasi Dias 2021, protokol §4.2) ──────────────────────
# Paper menambahkan jitter SERAGAM +-delta (delta<=18 sampel) ke posisi R karena
# mereka tidak punya detektor — angka itu pinjaman dari literatur QRS detection.
# Kita punya detektornya, dan scripts/ukur_jitter.py sudah mengukur residunya di
# DS1: 80% beat meleset <=1 sampel, 90% <=2, lalu ekor berat sampai 54 sampel
# (record berisik 108/203/207). Inti tajam + ekor berat — bukan seragam, bukan
# normal. Maka "empiris" jadi default: ambil ulang dari kolam residu asli, tanpa
# asumsi bentuk sama sekali.
#
# Seragam tetap disediakan supaya sweep delta=0..18 bisa dibandingkan lurus
# dengan Tabel 3 paper.
#
# Jitter per beat INDEPENDEN. Detektor nyata errornya berkorelasi (satu record
# berisik menggeser banyak beat sekaligus), dan korelasi itu sebagian SALING
# MENIADAKAN di fitur RR karena RR itu selisih dua posisi. Independen berarti
# ragam RR dilebihkan — arah yang pesimistis, jadi aman sebagai asumsi.
RESIDU_DS1 = os.path.join(METRICS_DIR, "jitter", "residu_ds1.npy")


def jitter_r(r_locations: np.ndarray, delta: int = 0, rng=None,
             model: str = "empiris") -> np.ndarray:
    """Geser posisi R meniru error detektor. Label TIDAK ikut bergeser.

    model:
        "empiris" — ambil ulang dari residu terukur DS1 (delta diabaikan)
        "seragam" — U{-delta..+delta}, protokol Dias 2021
        "normal"  — N(0, delta) dibulatkan

    Urutan dijaga menaik: r yang sudah dijitter dilewatkan maximum.accumulate,
    karena satu pasang beat yang bertukar tempat membuat RR negatif dan itu
    bukan mode kegagalan detektor mana pun (refraktori 200 ms mencegahnya).
    """
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


# ── Fase A — penyeragaman laju cuplik antar-database ─────────────────────────
# svdb 128 Hz dan incartdb 257 Hz harus jadi 360 Hz sebelum masuk pipeline, dan
# alasannya BUKAN kerapian: WIN_PRE terdefinisi dalam SAMPEL, bukan waktu.
#
#     128 sampel @ 360 Hz =  355 ms   <- yang diablasi & dikunci 18 Sep
#     128 sampel @ 128 Hz = 1000 ms   <- fisiologi lain sama sekali
#
# Decision point 18 Sep bilang yang membayar itu "konteks 128 sampel SEBELUM R",
# dan mekanismenya gelombang P & interval PR yang hidup ~150-200 ms sebelum R.
# Itu durasi FISIOLOGIS. Memakai 128 sampel di 128 Hz bukan menyalin keputusan
# itu — itu melanggarnya sambil terlihat konsisten.
#
# Dengan target 360 Hz: WIN_PRE/WIN_POST, koefisien bandpass (didesain di FS),
# ECG_FS di firmware, dan golden_ref.h SEMUANYA tidak berubah. Itu sebabnya
# arahnya ke 360, bukan menurunkan mitdb ke 128.


def resample_to_fs(signal: np.ndarray, r_locations: np.ndarray,
                   fs_asal: int, fs_target: int = FS):
    """TODO(user) — samakan laju cuplik ke fs_target. Returns (signal, r_locations).

    Ini LOGIKA PREPROCESSING, jadi milikmu (CLAUDE.md aturan 1). Yang sudah
    disiapkan: kontrak, pemanggilnya (io_mitdb.load_record), dan test yang
    menjaganya (tests/test_multidataset.py). Yang perlu kamu putuskan:

    1. METODE. `scipy.signal.resample_poly(signal, up, down)` itu polyphase FIR
       — anti-alias bawaan, rasio rasional (128->360 = 45/16, 257->360 = 360/257
       yang tidak sederhana). `scipy.signal.resample` itu FFT: mengasumsikan
       sinyal periodik, jadi tepinya bisa berdenyut. Keduanya sudah ada di
       requirements (scipy dipakai sosfilt) — NOL dependency baru.

    2. POSISI R. Setelah sinyal diregangkan, indeks R lama tidak valid lagi.
       Paling langsung: r_baru = round(r_lama * fs_target / fs_asal). Konsekuensi
       yang harus kamu sadari: pembulatan itu menambah error posisi +-1 sampel di
       360 Hz — dan alignment kita SENSITIF (docs/segmentasi-deteksi-walkthrough:
       meleset 4 sampel menjatuhkan precision 0,48 -> 0,12). Pilihan lain:
       cari ulang puncak lokal di sekitar r hasil pembulatan, seperti yang
       ecg_align_r() lakukan di firmware. Lebih mahal, lebih akurat.

    3. URUTAN vs BANDPASS. Sekarang load_record memanggil ini SEBELUM
       apply_bandpass, jadi semua database difilter oleh sos yang sama di 360 Hz.
       Kalau dibalik (filter di fs asal lalu resample), tiap database dapat
       respons filter yang sedikit berbeda — dan golden reference kita cuma
       menjamin satu: sos di 360 Hz.

    Yang TIDAK bisa dilakukan resample: menciptakan detail. svdb 128 Hz tetap
    punya resolusi lebar QRS 7,8 ms/sampel setelah di-upsample; mitdb 2,8 ms.
    Itu menabrak K4 (QRSw fitur rank 1-2) -> metrik WAJIB dilaporkan per-sumber.

    Args:
        signal: [N] float32, satu kanal, belum difilter.
        r_locations: [M] int, indeks R-peak pada laju fs_asal.
        fs_asal: laju cuplik record aslinya.
        fs_target: tujuan (default FS = 360).

    Returns:
        (signal_baru [N'] float32, r_locations_baru [M] int64)
        Kalau fs_asal == fs_target: kembalikan apa adanya, jangan sentuh.
    """
    raise NotImplementedError(
        "Fase A: resample_to_fs belum diimplementasikan — lihat docstring "
        "(3 keputusan) dan docs/2026-09-19-multidataset-plan.md §2"
    )
