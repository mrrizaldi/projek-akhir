import os


def _env_int(nama: str, bawaan: int) -> int:
    return int(os.environ.get(nama, bawaan))


FS = 360
BANDPASS_LOW = 0.5
BANDPASS_HIGH = 40.0
BANDPASS_ORDER = 4
WIN_PRE = _env_int("PA_WIN_PRE", 128)
WIN_POST = _env_int("PA_WIN_POST", 128)
WIN_LEN = WIN_PRE + WIN_POST
CHANNEL = "MLII"
PT_BAND_LOW = 5.0
PT_BAND_HIGH = 15.0
PT_BAND_ORDER = 2
PT_MWI_WINDOW_MS = 150
PT_REFRACTORY_MS = 200
SEED = 42
RR_LOCAL_WINDOW_BEATS = 10
AAMI_MAP = {
    "N": "N", "L": "N", "R": "N", "e": "N", "j": "N",
    "A": "S", "a": "S", "J": "S", "S": "S",
    "V": "V", "E": "V",
    "F": "F",
    "/": "Q", "f": "Q", "Q": "Q",
}

NORMAL_SYMBOLS = {"N"}
ARRHYTHMIA_SYMBOLS = {"V", "S", "F", "Q"}
RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw", "mitdb")

BEAT_SYMBOLS = {"N", "L", "R", "e", "j",
                "A", "a", "J", "S",
                "V", "E",
                "F",
                "/", "f", "Q"}

PACED_EXCLUDED = [102, 104, 107, 217]

DS1 = [101, 106, 108, 109, 112, 114, 115, 116, 118, 119, 122, 124,
       201, 203, 205, 207, 208, 209, 215, 220, 223, 230]
DS2 = [100, 103, 105, 111, 113, 117, 121, 123, 200, 202, 210, 212,
       213, 214, 219, 221, 222, 228, 231, 232, 233, 234]
DATASETS = {
    "mitdb":    {"fs": 360, "leads": ("MLII",),  "id_offset": 0,    "selaraskan": False, "n_record": 44},
    "svdb":     {"fs": 128, "leads": ("ECG1",),  "id_offset": 0,    "selaraskan": True,  "n_record": 78},
    "incartdb": {"fs": 257, "leads": ("II",),    "id_offset": 1000, "selaraskan": True,  "n_record": 75},
}


ALIGN_WIN = 16

SPLIT_SETIAP_KE = 4

DB_LATIH = ("mitdb", "svdb")

def raw_dir(db: str) -> str:
    if db not in DATASETS:
        raise KeyError(f"database tak dikenal: {db} (pilihan: {sorted(DATASETS)})")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw", db)


PROCESSED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "data", "processed")
PER_RECORD_DIR = os.path.join(PROCESSED_DIR, "per_record")

CONV_FILTERS = (16, 32, 32)
CONV_KERNELS = (7, 5, 3)
POOL_SIZE = 2
DENSE_UNITS = 16
DROPOUT_RATE = 0.0
USE_HOS = os.environ.get("PA_HOS", "0") == "1"
USE_QRSW = os.environ.get("PA_QRSW", "0") == "1"
USE_RR_RATIO = os.environ.get("PA_RR_RATIO", "0") == "1"
N_RR_BASE = 4 if USE_RR_RATIO else 3
N_RR_FEATURES = N_RR_BASE + (2 if USE_HOS else 0) + (2 if USE_QRSW else 0)

R_IN_WINDOW = WIN_PRE + 4

JITTER_MODEL = "empiris"
JITTER_SALINAN = 2

VAL_RECORDS = [101, 114, 201, 220, 223]

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
METRICS_DIR = os.path.join(ARTIFACT_DIR, "metrics")

EPOCHS = 60
BATCH_SIZE = 64
EARLY_STOP_PATIENCE = 8
EARLY_STOP_MONITOR = "val_auc"
THRESHOLD = 0.80

REP_SAMPLES = 300
INT8_IO = True
MAX_MODEL_KB = 25
MAX_RHYTHM_SCALE = 0.05

MIN_PRESISI_NAMA = 0.90

PT_DETECTOR_OFFSET = 38
PT_REFINE_WIN = 25
GROUP_DELAY_SAMPLES = 4
