import numpy as np

from scripts.quality_trend import FREQUENCY_MAINS_HZ, scores_per_second, quiet_per_second

FS = 360


def _synthetic_ecg(seconds, beat_times, baseline=2000):
    t = np.arange(int(seconds * FS)) / FS
    x = np.full_like(t, baseline)
    for tb in beat_times:
        x += 1500 * np.exp(-0.5 * ((t - tb) / 0.012) ** 2)
    return x


def test_hum_50hz_measured_peak_to_peak():
    t = np.arange(5 * FS) / FS
    _, hum50, _, clipping = scores_per_second(2000 + 100 * np.sin(2 * np.pi * FREQUENCY_MAINS_HZ * t))
    assert np.allclose(hum50, 200, rtol=0.01)
    assert not clipping.any()


def test_quiet_rr_grows_and_resets_on_premature_beat():
    regular = _synthetic_ecg(60, np.arange(0.5, 60, 1.0))
    *_, quiet_run_s = quiet_per_second(regular, 60)
    assert quiet_run_s.max() >= 55

    premature = np.sort(np.r_[np.arange(0.5, 60, 1.0), 30.85])
    *_, quiet_run_s = quiet_per_second(_synthetic_ecg(60, premature), 60)
    assert quiet_run_s[30] == 0 and quiet_run_s[31] == 0
    assert quiet_run_s[59] >= 25
