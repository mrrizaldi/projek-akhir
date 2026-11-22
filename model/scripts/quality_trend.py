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
    header_fields = {}
    for line in open(path):
        if not line.startswith("#"):
            break
        if line.strip() == "# jeda":
            sys.exit(f"{path}: contains '# jeda', a paused session cannot be scored per second")
        for word in line.lstrip("# ").split():
            k, _, v = word.partition("=")
            header_fields[k] = v
    return header_fields


def load_session(paths):
    excerpts = []
    for session_index, path in enumerate(paths):
        header_fields = read_header(path)
        if int(header_fields.get("fs", FS)) != FS:
            sys.exit(f"{path}: fs={header_fields['fs']}, not {FS}")
        if int(header_fields.get("lewat", 0)):
            print(f"WARNING {path}: lewat={header_fields['lewat']}")
        if session_index and int(header_fields.get("celah", -1)) != 0:
            print(f"WARNING {path}: not a gapless continuation (celah={header_fields.get('celah')})")
        excerpts.append(np.loadtxt(path, comments="#", dtype=np.float64))
    return np.concatenate(excerpts)


def scores_per_second(raw):
    n_seconds = len(raw) // FS
    second_blocks = raw[: n_seconds * FS].reshape(n_seconds, FS)
    filtered_signal = apply_bandpass(raw, design_bandpass_sos())[: n_seconds * FS].reshape(n_seconds, FS)
    ayun = filtered_signal.max(axis=1) - filtered_signal.min(axis=1)
    mains_bin = int(np.argmin(np.abs(np.fft.rfftfreq(FS, 1.0 / FS) - FREQUENCY_MAINS_HZ)))
    amp50 = PEAK_TO_PEAK * np.abs(np.fft.rfft(second_blocks, axis=1)[:, mains_bin]) / FS
    hum50 = PEAK_TO_PEAK * amp50
    ayun_bersih = np.maximum(ayun - GAIN_50HZ * hum50, 0.0)
    clipping = (second_blocks.max(axis=1) >= ADC_UPPER) | (second_blocks.min(axis=1) <= ADC_LOWER)
    return ayun, hum50, ayun_bersih, clipping


def quiet_per_second(raw, n_seconds):
    x = (raw - raw.mean()) / DETECTOR_SCALE
    r = pan_tompkins_detect(apply_bandpass(x, design_bandpass_sos()), FS)
    rr = np.diff(r) / FS
    drr = np.abs(np.ediff1d(rr, to_begin=0.0))
    plausible = (rr >= RR_MIN_S) & (rr <= RR_MAX_S) & (drr <= DRR_MAX_S)
    beat_seconds = r[FIRST_BEAT_WITH_RR:] // FS
    violated = np.zeros(n_seconds, dtype=bool)
    violated[beat_seconds[~plausible & (beat_seconds < n_seconds)]] = True
    beat = np.bincount(beat_seconds[beat_seconds < n_seconds], minlength=n_seconds)
    quiet_run_s = np.zeros(n_seconds)
    for t in range(1, n_seconds):
        quiet_run_s[t] = 0.0 if violated[t] else quiet_run_s[t - 1] + 1.0
    return beat, plausible, beat_seconds, quiet_run_s


def first_pass(conditions):
    indices = np.flatnonzero(conditions)
    if not len(indices):
        return "never"
    first = indices.min()
    return f"{first} s ({first / SECONDS_PER_MINUTE:.1f} minutes)"


def main() -> None:
    paths = sys.argv[1:]
    if not paths:
        sys.exit("usage: python scripts/quality_trend.py <session-1-file.csv> [<continuation-file.csv> ...]")
    raw = load_session(paths)
    ayun, hum50, ayun_bersih, clipping = scores_per_second(raw)
    n_seconds = len(ayun)
    beat, plausible, beat_seconds, quiet_run_s = quiet_per_second(raw, n_seconds)
    seconds = np.arange(n_seconds)

    print(f"session {len(paths)} files, {n_seconds} seconds ({n_seconds / SECONDS_PER_MINUTE:.1f} minutes)\n")
    print("minute | clean_swing median p10 | hum50 median | clipping seconds | beat | RR plausible | quiet max")
    for m in range(0, n_seconds, SECONDS_PER_MINUTE):
        s = slice(m, m + SECONDS_PER_MINUTE)
        in_minute = (beat_seconds >= m) & (beat_seconds < m + SECONDS_PER_MINUTE)
        percent_plausible = 100.0 * plausible[in_minute].mean() if in_minute.any() else float("nan")
        print(f"{m // SECONDS_PER_MINUTE:5d} | {np.median(ayun_bersih[s]):11.0f} {np.percentile(ayun_bersih[s], LOWER_PERCENTILE):4.0f}"
              f" | {np.median(hum50[s]):16.0f} | {clipping[s].sum():14d} | {beat[s].sum():4d}"
              f" | {percent_plausible:7.1f}% | {quiet_run_s[s].max():8.0f} s")

    swing_ok = ayun_bersih >= THRESHOLD_SWING
    rr_quiet = quiet_run_s >= QUIET_RR_S
    print(f"\nclean_swing >= {THRESHOLD_SWING} first        : {first_pass(swing_ok)}")
    print(f"quiet RR >= {QUIET_RR_S} s first          : {first_pass(rr_quiet)}")
    print(f"gate without {STABLE_S} s condition passes: {first_pass(swing_ok & rr_quiet)}")
    print(f"firmware gate (with {STABLE_S} s) passes: {first_pass(swing_ok & rr_quiet & (seconds >= STABLE_S))}")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    name = os.path.splitext(os.path.basename(paths[0]))[0] + f"-sesi{len(paths)}"
    out_path = os.path.join(OUTPUT_FOLDER, f"{name}.csv")
    np.savetxt(out_path, np.column_stack([seconds, ayun, hum50, ayun_bersih, clipping, beat, quiet_run_s]),
               fmt="%d", delimiter=",", header="detik,ayun,dengung50,ayun_bersih,clipping,beat,tenang_s",
               comments="")
    print(f"\n{out_path}")


if __name__ == "__main__":
    main()
