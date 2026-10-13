import numpy as np
from scipy.signal import butter, sosfilt

from config import FS, BANDPASS_LOW, BANDPASS_HIGH, BANDPASS_ORDER, WIN_PRE, WIN_POST, WIN_LEN
from src.io_mitdb import load_record  # noqa: E402

sos = butter(BANDPASS_ORDER, [BANDPASS_LOW, BANDPASS_HIGH], btype="bandpass", fs=FS, output="sos")
ba = butter(BANDPASS_ORDER, [BANDPASS_LOW, BANDPASS_HIGH], btype="bandpass", fs=FS, output="ba")
# print(sos)
# print(ba)

signal, r_locations, symbols, fs = load_record(100)

print(signal[0:10])
# print(signal.tolist())
# sosfiltered = sosfilt(signal, sos, axis=0, zi=None)
# print(sosfiltered)