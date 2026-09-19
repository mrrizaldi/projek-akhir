import os


def _env_int(nama: str, bawaan: int) -> int:
    """Knob ablasi lewat environment. TANPA env, nilainya persis seperti dulu.

    Dipakai scripts/ablasi.py untuk menjalankan varian di proses terpisah —
    konstanta di sini dibaca saat import, jadi tidak bisa diganti setelahnya.
    Nilai yang MENANG dikunci dengan mengubah bawaannya di baris bawah (gate
    point: konfirmasi user), bukan dengan menyetel env secara permanen.
    """
    return int(os.environ.get(nama, bawaan))


FS = 360 # Hz, sampling MIT-BIH
BANDPASS_LOW = 0.5 # Hz, cutoff bawah Butterworth
BANDPASS_HIGH = 40.0 # Hz, cutoff atas Butterworth
BANDPASS_ORDER = 4 # orde 2–4
# Window 128/128 = 256 sampel, DIKUNCI 18 Sep 2026 menggantikan 90/160 (250).
# Bukan karena paper memakainya, tapi karena ablasi 3 seed: F1 DS2 0,5660 ->
# 0,6911. Varian penentu justru yang KALAH — 112/144 juga 256 sampel, juga
# kelipatan 8, cakupan T malah lebih panjang, hasilnya setara baseline. Jadi yang
# membayar konteks 128 sampel SEBELUM R, bukan panjang window.
# R mendarat di indeks 132 (128 + group delay 4), bukan 94 lagi.
# Rantai pooling jadi 256->128->64->32 tanpa pemotongan (250 dulu 125->62->31).
WIN_PRE = _env_int("PA_WIN_PRE", 128)   # sampel sebelum R-peak
WIN_POST = _env_int("PA_WIN_POST", 128) # sampel sesudah R-peak
WIN_LEN = WIN_PRE + WIN_POST # = 256 
CHANNEL = "MLII" # kanal utama MIT-BIH
# Pan-Tompkins (benchmark detektor R-peak on-device, TIDAK dipakai segmentasi training)
PT_BAND_LOW = 5.0 # Hz, cutoff bawah bandpass QRS-enhancer
PT_BAND_HIGH = 15.0 # Hz, cutoff atas bandpass QRS-enhancer
PT_BAND_ORDER = 2 # orde Butterworth utk bandpass QRS-enhancer
PT_MWI_WINDOW_MS = 150 # ms, lebar Moving Window Integration (~lebar QRS)
PT_REFRACTORY_MS = 200 # ms, periode refraktori antar R-peak (~300bpm max)
SEED = 42 # randomness
# Fase 2 — lebar jendela rata-rata RR lokal (beat). PRD hal. 10 bilang "~10 beat
# sekitarnya" dan menandainya DECISION POINT: kunci angkanya, jangan biarkan kabur.
RR_LOCAL_WINDOW_BEATS = 10
# Fase 2 — mapping DUA TAHAP (PRD hal. 10, konvensi AAMI / de Chazal 2004).
# Tahap 1: simbol MIT-BIH mentah → superclass AAMI {N, S, V, F, Q}
# Tahap 2: superclass AAMI → label biner (dua set di bawah AAMI_MAP).
# L & R (bundle branch block) → N: ikut AAMI supaya sebanding dgn literatur
# inter-patient. Beda dari intuisi klinis — keputusan sadar, dicatat di CLAUDE.md.
AAMI_MAP = {
    "N": "N", "L": "N", "R": "N", "e": "N", "j": "N",   # normal & bundle branch block
    "A": "S", "a": "S", "J": "S", "S": "S",             # supraventricular ectopic
    "V": "V", "E": "V",                                 # ventricular ectopic
    "F": "F",                                           # fusion
    "/": "Q", "f": "Q", "Q": "Q",                       # paced / unclassifiable
}

# Superclass AAMI → biner. 0 = Normal, 1 = Aritmia.
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

# Fase 3 — split inter-patient de Chazal 2004 (PRD hal. 11). 22 + 22 + 4 = 48.
# Dua alasan berbeda, satu daftar buang:
#   102, 104 → TEKNIS: tidak punya kanal MLII (load_record raise ValueError)
#   107, 217 → METODOLOGIS: ber-pacemaker; 107 itu 97% simbol "/" → kalau ikut
#              terlatih, satu record menyumbang 2.078 beat "Aritmia" palsu.
# Dipakai Fase 2 (prep_beats melewatinya) DAN Fase 3. Satu sumber, jangan digandakan.
PACED_EXCLUDED = [102, 104, 107, 217]

DS1 = [101, 106, 108, 109, 112, 114, 115, 116, 118, 119, 122, 124,
       201, 203, 205, 207, 208, 209, 215, 220, 223, 230]   # latih (22)
DS2 = [100, 103, 105, 111, 113, 117, 121, 123, 200, 202, 210, 212,
       213, 214, 219, 221, 222, 228, 231, 232, 233, 234]   # uji  (22)
# ── Fase A (19 Sep 2026) — dataset tambahan: svdb + incartdb ─────────────────
# Permintaan pembimbing dari awal: perluas data latih. Sebaran di bawah TERUKUR
# dari anotasi asli PhysioNet, dipetakan lewat AAMI_MAP di atas — bukan angka
# yang disalin dari paper:
#
#   svdb      78 rec, 128 Hz | S 12.198/73rec  V  9.943/67rec  F  23/6rec   Q 79/20rec
#   incartdb  75 rec, 257 Hz | S  1.960/36rec  V 20.013/70rec  F 219/22rec  Q  6/5rec
#
# Kenapa dua ini, bukan yang lain: keduanya punya anotasi BEAT-LEVEL (.atr, satu
# simbol per R-peak) dengan alfabet WFDB yang sama, jadi AAMI_MAP di atas sudah
# menanganinya apa adanya. PTB-XL / CPSC / Chapman dibuang bukan karena frekuensi
# tapi karena diagnosisnya PER-REKAMAN — label per-beat tidak bisa diturunkan
# dari sana, berapa pun frekuensinya.
#
# Peran masing-masing:
#   svdb     -> recall S (0,422 +- 0,156). Dari 634 beat/~20 pasien ke ~11.250/~102.
#   incartdb -> KONSENTRASI F. Punya kita 372 dari 394 beat F ada di record 208
#               saja; incartdb menyebar 219 beat di 22 record. Yang diperbaiki
#               cakupan pasien, bukan jumlah beat.
#   Q        -> TIDAK ada yang menolong: 100 beat di tiga database
#               digabung (8+7 mitdb + 79 svdb + 6 incartdb = 100). Q tetap
#               bukan kelas yang bisa dilaporkan.
#
# ATURAN YANG TIDAK BOLEH DILANGGAR: DS2 (mitdb) di atas tidak berubah satu byte.
# Dia satu-satunya yang sebanding dengan literatur (de Chazal DS1/DS2), dan §7
# aturan 4 (DS2 tak pernah memilih apa pun) cuma bisa ditegakkan kalau
# komposisinya bukan variabel. Data baru masuk TRAIN; sisanya jadi test TERPISAH
# untuk generalisasi antar-database.
#
# id_offset: `records` di dataset.py bertipe int32, sedangkan record incartdb
# bernama "I01".."I75" -> dipetakan ke 1001..1075. mitdb 100-234 dan svdb 800-894
# sudah numerik, jadi offset 0. Tiga rentang itu tidak bertumpuk.
#
# leads: dipilih yang PERTAMA tersedia. mitdb MLII = acuan alat (AD8232 lead II).
# incartdb "II" paling dekat dengannya. svdb Holter, lead tidak dinamai -> ECG1
# dipakai dan POLARITASNYA BELUM DIVERIFIKASI (gate, lihat docs plan §3).
# selaraskan: geser anotasi R ke puncak sebenarnya sebelum memotong window.
# Perlu karena konvensi anotasi antar-database BEDA — terukur 19 Sep atas beat
# normal, posisi puncak relatif anotasi di sinyal ter-bandpass:
#
#   mitdb  median  +3   p5..p95  +1..+5     <- anotasi DI puncak; +3/+4 = group delay
#   svdb   median +10   p5..p95  -2..+15    <- ~6 sampel lebih awal, sebaran 3x lebar
#
# Bias +6 sampel itu DI ATAS ambang bahaya repo ini (meleset 4 sampel menjatuhkan
# precision 0,48 -> 0,12) dan SISTEMATIS, bukan jitter zero-mean: tanpa koreksi
# tiap beat svdb tergeser searah dan model membacanya sebagai morfologi lain
# (alias belajar identitas dataset — lawan semangat inter-patient).
#
# mitdb WAJIB False: dia acuan golden_ref.h dan semua ablasi terkunci. Median +3
# vs +4 berarti menyelaraskannya akan menggeser r ~1 sampel dan membatalkan
# semuanya. Yang diperbaiki database baru, bukan acuannya.
DATASETS = {
    "mitdb":    {"fs": 360, "leads": ("MLII",),  "id_offset": 0,    "selaraskan": False, "n_record": 44},
    "svdb":     {"fs": 128, "leads": ("ECG1",),  "id_offset": 0,    "selaraskan": True,  "n_record": 78},
    "incartdb": {"fs": 257, "leads": ("II",),    "id_offset": 1000, "selaraskan": True,  "n_record": 75},
}

# n_record: jumlah record LENGKAP yang diharapkan (mitdb 48 - 4 PACED_EXCLUDED).
# Bukan hiasan — aturan held-out `sorted(records)[::4]` dihitung dari daftar yang
# ADA, jadi database yang baru separuh terunduh menghasilkan held-out yang BEDA
# tanpa bersuara. Terukur 19 Sep pada 65/75 record incartdb: I68 masuk held-out
# padahal seharusnya tidak, dan I65/I69/I73 hilang (I65 memegang 4 beat F).
# build_split_multi() menolak kalau jumlahnya tidak pas.

# Setengah-lebar jendela cari-puncak untuk `selaraskan`. 16 (±44 ms) menutup
# p1..p99 svdb (-9..+15) tanpa menjangkau gelombang T (~200-300 ms = 72-108
# sampel). BUKAN PT_REFINE_WIN=25 (±70 ms): itu untuk sebaran detektor
# Pan-Tompkins (std 13 sampel), dan di sini terlalu lebar — risiko argmax
# melompat ke fitur yang salah tanpa alasan.
ALIGN_WIN = 16

# Held-out tiap dataset baru = setiap record ke-N dalam urutan tersortir.
# ATURAN, bukan seed: tidak ada yang bisa dipancing, dan siapa pun bisa
# memverifikasinya dengan sorted(records)[::4]. ~25% disisihkan.
# Konsekuensi yang sudah diperiksa: held-out incartdb cuma dapat ~13-20 beat F
# (I05=9, I65=4, + sisa kecil) karena F terbesar (I18=56, I74=48) jatuh ke train.
# Itu DISENGAJA — train yang kekurangan F, bukan test. F di test dilaporkan
# sebagai hitungan TP/FN mentah, JANGAN sebagai recall berkoma.
SPLIT_SETIAP_KE = 4

# Database yang IKUT LATIH. incartdb sengaja TIDAK di sini — Fase B mengukurnya
# merugikan meski menyumbang 256.454 beat latih (4 varian x 3 seed,
# docs/2026-09-19-faseB-changelog.md):
#
#                 mitdb      +svdb    +incartdb   +keduanya
#   AUC          0,9373     0,9314     0,8881      0,9092
#   recall S     0,4221     0,4980     0,3312      0,4050
#
# recall S +svdb [0,423;0,573] vs +incartdb [0,307;0,355] TERPISAH: efeknya
# BERLAWANAN, dan di "+keduanya" mereka hampir persis saling meniadakan (-0,017).
# Bukan soal lead (II ~ MLII, gate A2) atau resolusi (257 > 128 Hz) tapi
# komposisi: 15.592 beat V dari populasi lain menumpulkan pemisahan N-vs-S.
#
# incartdb TETAP DIPAKAI sebagai test antar-database (41.108 beat, 19 pasien) —
# itu pemakaian terbaiknya, dan tetap jadi kontribusi E3C untuk laporan.
DB_LATIH = ("mitdb", "svdb")

def raw_dir(db: str) -> str:
    """Folder mentah per database. RAW_DIR di atas tetap ada (= raw_dir("mitdb"))."""
    if db not in DATASETS:
        raise KeyError(f"database tak dikenal: {db} (pilihan: {sorted(DATASETS)})")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw", db)


# Fase 2-3 — keluaran prep_beats.py (per record) & build_split.py (train/test).
PROCESSED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "data", "processed")
PER_RECORD_DIR = os.path.join(PROCESSED_DIR, "per_record")

# Fase 4 — arsitektur hybrid (PRD hal. 13). Angka di sini menentukan count_params.
CONV_FILTERS = (16, 32, 32)   # per blok Conv1D
CONV_KERNELS = (7, 5, 3)      # lebar kernel per blok, mengerucut
POOL_SIZE = 2                 # MaxPooling1D tiap blok
DENSE_UNITS = 16              # lapisan penggabung morfologi + ritme
DROPOUT_RATE = 0.0            # 0.0 = tanpa dropout (keputusan terkunci)
# Fitur cabang ritme. HOS (kurtosis+skewness, Dias 2021 Pers. 12-13) menempel di
# cabang yang sama, bukan cabang morfologi: dua skalar, bukan deret waktu.
USE_HOS = os.environ.get("PA_HOS", "0") == "1"
N_RR_FEATURES = 3 + (2 if USE_HOS else 0)   # RR_prev, RR_ratio, dRR [, kurt, skew]

# Fase 6c — augmentasi ketahanan segmentasi (docs/jitter-walkthrough.md).
# Dipakai `make prep`: tiap record DS1 ditumpuk 1 salinan bersih + JITTER_SALINAN
# tiruan ber-jitter. DS2 TIDAK PERNAH dijitter — dia tolok ukur jujur.
# "empiris" = ambil ulang dari residu detektor terukur (artifacts/metrics/jitter/
# residu_ds1.npy, dari scripts/ukur_jitter.py), bukan seragam +-18 ala paper.
JITTER_MODEL = "empiris"
JITTER_SALINAN = 2

# Fase 5 — validation dari DS1 (per pasien, bukan per beat). DS2 haram jadi val.
# Dipilih supaya rasio aritmia val ~= rasio DS1 (10,11%) dan kedua jenis aritmia
# utama terwakili (S=310, V=714). 208 sengaja TIDAK di sini: dia memegang 372
# dari 414 beat kelas F di DS1 — kalau ikut val, train nyaris kehilangan kelas F.
VAL_RECORDS = [101, 114, 201, 220, 223]

# Fase 5-7 — artefak keluaran (model, kurva, tabel metrik).
ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
METRICS_DIR = os.path.join(ARTIFACT_DIR, "metrics")

# Fase 5 — training (PRD hal. 14). Threshold 0,5 dikalibrasi di val, bukan DS2.
EPOCHS = 60
BATCH_SIZE = 64
EARLY_STOP_PATIENCE = 8
EARLY_STOP_MONITOR = "val_auc"   # AUC, bukan recall: recall bisa "dicurangi" tebak 1 semua
# Threshold DIKUNCI dari kalibrasi di VAL (DS1), bukan DS2 — JEBAKAN PRD Fase 6.
# Kriteria: F1 maksimum, tie-break ke recall bila selisih F1 < 0,005 (tidak berubah).
#
# 18 Sep 2026: 0,35 -> 0,80 setelah window 128/128 + augmentasi jitter.
# Val F1 maksimum 0,6917; kandidat dalam margin {0,80; 0,85} -> recall menang -> 0,80.
# Naik drastis BUKAN karena model jadi konservatif, tapi karena VAL sekarang ikut
# ber-jitter: sebaran probabilitasnya bergeser ke atas, jadi titik operasi yang
# benar ikut bergeser. Memakai 0,35 di model ini memberi precision 0,19.
# Angka lama (val F1 0,8124 @ 0,35) diukur di val BERSIH — tidak sebanding.
# Reproduksi: python scripts/calibrate_threshold.py
THRESHOLD = 0.80

# Fase 7 — PTQ INT8 (PRD hal. 16-17).
REP_SAMPLES = 300        # sampel kalibrasi, stratified dari DS1 (PRD: ~100-500)
INT8_IO = True           # True = full-INT8 end-to-end; harus konsisten dgn firmware
# DoD PRD semula < 20 KB. Dinaikkan ke 25 KB setelah terbukti varian deploy
# (tanpa MEAN & tanpa shape dinamis) yang jalan benar di TFLM memakan 20,8 KB.
# Flash ESP32-S3 16 MB — batas ini soal disiplin, bukan kapasitas.
MAX_MODEL_KB = 25
# Ambang skala kuantisasi tensor input ritme (Fase 7). Bukan hiasan: skala INT8
# diturunkan dari min/max REP_SAMPLES sampel kalibrasi, dan segelintir beat
# ber-RR ekstrem (record 207: RR_prev = 100 s, celah anotasi) bisa masuk undian.
# Kalau kena, skala melompat ~40x dan RR normal (0,18-2,58 s) tinggal ~3 level
# int8 -> cabang ritme praktis mati, dan GEJALANYA recall S buruk, BUKAN error.
# Peluang per seed terukur 19 Sep: 4,6% (mitdb saja), 1,8% (tiga database).
# Nilai sehat sekarang 0,0129; sehat secara teori ~0,0197 (p99,99 |X_rr| = 2,51);
# yang rusak ~0,78. Ambang 0,05 = ~2,5x headroom dari sehat, ~15x di bawah rusak.
MAX_RHYTHM_SCALE = 0.05

# Fase 6b — penyelarasan R-peak untuk segmentasi ON-DEVICE (docs/segmentasi-deteksi).
# Urutan wajib: r - PT_DETECTOR_OFFSET -> puncak dlm +-PT_REFINE_WIN -> - GROUP_DELAY.
# Salah satu terlewat: R tidak mendarat di indeks 94 dan precision jatuh 4x.
PT_DETECTOR_OFFSET = 38   # median (deteksi - anotasi) di DS1; std 13
PT_REFINE_WIN = 25        # +-70 ms, cari puncak R sebenarnya
GROUP_DELAY_SAMPLES = 4   # geseran bandpass kausal 0,5-40 Hz (JEBAKAN Fase 1)
