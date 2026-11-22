import numpy as np

from scripts.analyze_recording import (
    CLIPPING_PERCENT_THRESHOLD, AUTOCORRELATION_WINDOW_S, analyze_segment, compute_clipping, autocorrelation_pulse, pulse_per_window, combine, muat,
)

FS = 360


def _synthetic_ecg(seconds, phase, baseline):
    t = np.arange(int(seconds * FS)) / FS
    x = np.full_like(t, baseline)
    for tb in np.arange(phase, seconds, 1.0):
        x += 1500 * np.exp(-0.5 * ((t - tb) / 0.012) ** 2)
    return x.astype(int)


def test_rr_does_not_cross_pause(tmp_path):
    s1, s2 = _synthetic_ecg(20, 0.5, 2000), _synthetic_ecg(20, 0.3, 2600)
    berkas = tmp_path / "rekam.csv"
    berkas.write_text(f"# fs={FS} n={len(s1) + len(s2)}\n"
                      + "\n".join(map(str, s1)) + "\n# jeda\n"
                      + "\n".join(map(str, s2)) + "\n")

    segments, fs, _ = muat(str(berkas))
    assert fs == FS and [len(s) for s in segments] == [len(s1), len(s2)]

    analyses = [analyze_segment(s, fs) for s in segments]
    r, rr, *_ = combine(analyses, fs)
    assert all(len(h["r"]) > 10 for h in analyses)
    assert len(rr) == len(r) - 2
    assert np.all(np.abs(rr - 1.0) < 0.05)


def test_short_autocorrelation_keeps_whole_segment():
    x = (_synthetic_ecg(50, 0.5, 2000) - 2000) / 1000.0
    assert pulse_per_window(x, FS) == autocorrelation_pulse(x, FS)


def test_long_autocorrelation_median_per_window():
    x = (_synthetic_ecg(95, 0.5, 2000) - 2000) / 1000.0
    n = AUTOCORRELATION_WINDOW_S * FS
    per_window = [autocorrelation_pulse(x[i:i + n], FS) for i in range(0, len(x) - n + 1, n)]
    strength, bpm, _ = pulse_per_window(x, FS)
    assert len(per_window) == 3
    assert strength == float(np.median([k for k, _, _ in per_window]))
    assert bpm == float(np.median([b for _, b, _ in per_window]))


def test_clipping_judged_by_fraction_of_samples_at_firmware_rail():
    x = np.full(100000, 2000.0)
    x[:5] = 4093
    n, percent, ok = compute_clipping(x)
    assert (n, ok) == (5, True)
    x[:200] = 4090
    x[200:201] = 5
    n, percent, ok = compute_clipping(x)
    assert n == 201 and percent > CLIPPING_PERCENT_THRESHOLD and not ok
