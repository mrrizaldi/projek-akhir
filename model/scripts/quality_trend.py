import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FS, METRICS_DIR
from src.preprocessing import apply_bandpass, design_bandpass_sos, pan_tompkins_detect

THRESHOLD_SWING = 60
GAIN_50HZ = 0.342
FREQUENCY_MAINS_HZ = 50.0
ADC_UPPER, ADC_LOWER = 4090, 5
RR_MIN_S, RR_MAX_S, DRR_MAX_S = 0.300, 1.500, 0.200
QUIET_RR_S = 30
STABLE_S = 600
SECONDS_PER_MINUTE = 60
DETECTOR_SCALE = 1000.0
PEAK_TO_PEAK = 2.0
LOWER_PERCENTILE = 10
FIRST_BEAT_WITH_RR = 1
OUTPUT_FOLDER = os.path.join(METRICS_DIR, "kualitas")


def read_header(path):
    kunci = {}
    for baris in open(path):
        if not baris.startswith("#"):
            break
        if baris.strip() == "# jeda":
            sys.exit(f"{path}: contains '# jeda', a paused session cannot be scored per second")
        for kata in baris.lstrip("# ").split():
            k, _, v = kata.partition("=")
            kunci[k] = v
    return kunci


def load_session(paths):
    excerpts = []
    for urutan, path in enumerate(paths):
        kunci = read_header(path)
        if int(kunci.get("fs", FS)) != FS:
            sys.exit(f"{path}: fs={kunci['fs']}, not {FS}")
        if int(kunci.get("lewat", 0)):
            print(f"WARNING {path}: lewat={kunci['lewat']}")
        if urutan and int(kunci.get("celah", -1)) != 0:
            print(f"WARNING {path}: not a gapless continuation (celah={kunci.get('celah')})")
        excerpts.append(np.loadtxt(path, comments="#", dtype=np.float64))
    return np.concatenate(excerpts)


def scores_per_second(mentah):
    n_seconds = len(mentah) // FS
    blok = mentah[: n_seconds * FS].reshape(n_seconds, FS)
    filtered_signal = apply_bandpass(mentah, design_bandpass_sos())[: n_seconds * FS].reshape(n_seconds, FS)
    ayun = filtered_signal.max(axis=1) - filtered_signal.min(axis=1)
    mains_bin = int(np.argmin(np.abs(np.fft.rfftfreq(FS, 1.0 / FS) - FREQUENCY_MAINS_HZ)))
    amp50 = PEAK_TO_PEAK * np.abs(np.fft.rfft(blok, axis=1)[:, mains_bin]) / FS
    hum50 = PEAK_TO_PEAK * amp50
    ayun_bersih = np.maximum(ayun - GAIN_50HZ * hum50, 0.0)
    clipping = (blok.max(axis=1) >= ADC_UPPER) | (blok.min(axis=1) <= ADC_LOWER)
    return ayun, hum50, ayun_bersih, clipping


def quiet_per_second(mentah, n_seconds):
    x = (mentah - mentah.mean()) / DETECTOR_SCALE
    r = pan_tompkins_detect(apply_bandpass(x, design_bandpass_sos()), FS)
    rr = np.diff(r) / FS
    drr = np.abs(np.ediff1d(rr, to_begin=0.0))
    plausible = (rr >= RR_MIN_S) & (rr <= RR_MAX_S) & (drr <= DRR_MAX_S)
    beat_seconds = r[FIRST_BEAT_WITH_RR:] // FS
    violated = np.zeros(n_seconds, dtype=bool)
    violated[beat_seconds[~plausible & (beat_seconds < n_seconds)]] = True
    beat = np.bincount(beat_seconds[beat_seconds < n_seconds], minlength=n_seconds)
    tenang = np.zeros(n_seconds)
    for t in range(1, n_seconds):
        tenang[t] = 0.0 if violated[t] else tenang[t - 1] + 1.0
    return beat, plausible, beat_seconds, tenang


def first_pass(conditions):
    indeks = np.flatnonzero(conditions)
    if not len(indeks):
        return "never"
    pertama = indeks.min()
    return f"{pertama} s ({pertama / SECONDS_PER_MINUTE:.1f} minutes)"


def main() -> None:
    paths = sys.argv[1:]
    if not paths:
        sys.exit("usage: python scripts/quality_trend.py <session-1-file.csv> [<continuation-file.csv> ...]")
    mentah = load_session(paths)
    ayun, hum50, ayun_bersih, clipping = scores_per_second(mentah)
    n_seconds = len(ayun)
    beat, plausible, beat_seconds, tenang = quiet_per_second(mentah, n_seconds)
    waktu = np.arange(n_seconds)

    print(f"session {len(paths)} files, {n_seconds} seconds ({n_seconds / SECONDS_PER_MINUTE:.1f} minutes)\n")
    print("minute | clean_swing median p10 | hum50 median | clipping seconds | beat | RR plausible | quiet max")
    for m in range(0, n_seconds, SECONDS_PER_MINUTE):
        s = slice(m, m + SECONDS_PER_MINUTE)
        in_minute = (beat_seconds >= m) & (beat_seconds < m + SECONDS_PER_MINUTE)
        percent_plausible = 100.0 * plausible[in_minute].mean() if in_minute.any() else float("nan")
        print(f"{m // SECONDS_PER_MINUTE:5d} | {np.median(ayun_bersih[s]):11.0f} {np.percentile(ayun_bersih[s], LOWER_PERCENTILE):4.0f}"
              f" | {np.median(hum50[s]):16.0f} | {clipping[s].sum():14d} | {beat[s].sum():4d}"
              f" | {percent_plausible:7.1f}% | {tenang[s].max():8.0f} s")

    swing_ok = ayun_bersih >= THRESHOLD_SWING
    rr_quiet = tenang >= QUIET_RR_S
    print(f"\nclean_swing >= {THRESHOLD_SWING} first        : {first_pass(swing_ok)}")
    print(f"quiet RR >= {QUIET_RR_S} s first          : {first_pass(rr_quiet)}")
    print(f"gate without {STABLE_S} s condition passes: {first_pass(swing_ok & rr_quiet)}")
    print(f"firmware gate (with {STABLE_S} s) passes: {first_pass(swing_ok & rr_quiet & (waktu >= STABLE_S))}")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    nama = os.path.splitext(os.path.basename(paths[0]))[0] + f"-sesi{len(paths)}"
    keluaran = os.path.join(OUTPUT_FOLDER, f"{nama}.csv")
    np.savetxt(keluaran, np.column_stack([waktu, ayun, hum50, ayun_bersih, clipping, beat, tenang]),
               fmt="%d", delimiter=",", header="detik,ayun,dengung50,ayun_bersih,clipping,beat,tenang_s",
               comments="")
    print(f"\n{keluaran}")


if __name__ == "__main__":
    main()
