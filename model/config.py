FS = 360 # Hz, sampling MIT-BIH
BANDPASS_LOW = 0.5 # Hz, cutoff bawah Butterworth
BANDPASS_HIGH = 40.0 # Hz, cutoff atas Butterworth
BANDPASS_ORDER = 4 # orde 2–4
WIN_PRE = 90 # sampel sebelum R-peak
WIN_POST = 160 # sampel sesudah R-peak
WIN_LEN = WIN_PRE + WIN_POST # = 250 
CHANNEL = "MLII" # kanal utama MIT-BIH
SEED = 42 # randomness
NORMAL_SYMBOLS = {"N"}
ARRHYTHMIA_SYMBOLS = {"V", "S", "F", "Q"}