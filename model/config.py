import os

FS = 360 # Hz, sampling MIT-BIH
BANDPASS_LOW = 0.5 # Hz, cutoff bawah Butterworth
BANDPASS_HIGH = 40.0 # Hz, cutoff atas Butterworth
BANDPASS_ORDER = 4 # orde 2–4
WIN_PRE = 90 # sampel sebelum R-peak
WIN_POST = 160 # sampel sesudah R-peak
WIN_LEN = WIN_PRE + WIN_POST # = 250 
CHANNEL = "MLII" # kanal utama MIT-BIH
# Pan-Tompkins (benchmark detektor R-peak on-device, TIDAK dipakai segmentasi training)
PT_BAND_LOW = 5.0 # Hz, cutoff bawah bandpass QRS-enhancer
PT_BAND_HIGH = 15.0 # Hz, cutoff atas bandpass QRS-enhancer
PT_BAND_ORDER = 2 # orde Butterworth utk bandpass QRS-enhancer
PT_MWI_WINDOW_MS = 150 # ms, lebar Moving Window Integration (~lebar QRS)
PT_REFRACTORY_MS = 200 # ms, periode refraktori antar R-peak (~300bpm max)
SEED = 42 # randomness
NORMAL_SYMBOLS = {"N"}
ARRHYTHMIA_SYMBOLS = {"V", "S", "F", "Q"}
# Fase 0 — path & filter anotasi
RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw", "mitdb")

# Simbol MIT-BIH yang BENAR-BENAR detak (whitelist, konvensi AAMI).
# Sisanya non-beat: + ~ | x ! [ ] " → dibuang di load_record() (JEBAKAN PRD Fase 0).
# Whitelist, bukan blacklist: simbol tak dikenal ikut kebuang, bukan lolos diam-diam.
BEAT_SYMBOLS = {"N", "L", "R", "e", "j",      # supraventrikular normal-ish
                "A", "a", "J", "S",            # atrial/nodal ektopik
                "V", "E",                      # ventrikular
                "F",                           # fusi
                "/", "f", "Q"}                 # paced, fusi-paced, unclassifiable
