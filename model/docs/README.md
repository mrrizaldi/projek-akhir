# Peta walkthrough — jalur model TinyML, Fase 0 → 8

Titik masuk untuk belajar pipeline ini. Tiap fase punya satu dokumen: alur kode
langkah demi langkah, matematika di baliknya, keputusan beserta alternatif yang
ditolak, angka nyata, dan soal cek pemahaman.

**Ini dokumen belajar, bukan spesifikasi.** Spesifikasi resmi =
`PRD_Model_Aritmia_TinyML.pdf`. Keputusan yang mengikat = tabel decision point
di `../CLAUDE.md`.

---

## Alur data, satu layar

```
data/raw/mitdb/*.dat  (48 record MIT-BIH, 30 menit @360 Hz)
        │
   [0]  │  io_mitdb.py        pilih kanal MLII, saring non-beat
        ▼                     → signal, r_locations, symbols
        │
   [1]  │  preprocessing.py   bandpass 0,5-40 Hz KAUSAL, potong 256 sampel,
        ▼                       z-score per window   → windows [K,256]
        │
   [2]  │  features_rr.py     RR_prev / RR_ratio / dRR + label biner
        │  prep_beats.py      valid_beat_indices → 44 × per_record/*.npz  [2b]
        ▼                     202.560 beat (DS1 ×3 salinan ber-jitter, DS2 bersih)
        │
   [3]  │  dataset.py         split PER PASIEN (de Chazal 2004)
        ▼                     train.npz DS1 152.904 | test.npz DS2 49.656
        │
   [4]  │  model.py           CNN morfologi + Dense ritme → 6.417 param
        ▼
        │
   [5]  │  train.py           class_weight, EarlyStopping(val_auc)
        ▼                     → model_fp32.keras   (val: recall 0,81)
        │
        │  calibrate_threshold.py   threshold 0,80 dikunci DI VAL
        ▼
   [6]  │  evaluate.py        DS2 dibuka SEKALI → recall 0,700 AUC 0,933
        ▼
        │
   [7]  │  quantize.py        PTQ INT8 → 22,94 KB, delta recall +1,08%
        ▼
   [8]     check_poc.py       8/8 DoD terverifikasi
           export_model_h.py  → firmware/include/model_int8.h
        │
  [HW]  │  ecg_pipeline.cpp   port preprocessing ke C, diadu ke golden Python
        │  TFLite Micro       inferensi di ESP32-S3: 26,0 ms/detak
        ▼  akuisisi           AD8232 -> make pull -> make analisis -> grafik
```

---

## Urutan baca

Berurutan 0 → 7. Tiap dokumen mengasumsikan yang sebelumnya sudah dibaca.

| # | Dokumen | Menjawab |
|---|---|---|
| 0 | [io-mitdb](io-mitdb-walkthrough.md) | Dari mana data datang, kenapa MLII, apa yang dibuang sebelum apa pun dihitung |
| 1 | [preprocessing](preprocessing-walkthrough.md) | Kenapa filter kausal, bagaimana Butterworth & Pan-Tompkins bekerja, kenapa window 250 |
| 2 | [features-rr](features-rr-walkthrough.md) | Kenapa butuh fitur ritme selain bentuk, bagaimana label AAMI dipetakan, jebakan alignment |
| 2b | [prep-beats](prep-beats-walkthrough.md) | Siapa yang menjalankan Fase 0-2 ke 44 record, beat mana yang dibuang & pembukuannya |
| 3 | [dataset](dataset-walkthrough.md) | Kenapa split per pasien, apa itu kebocoran identitas |
| 4 | [model](model-walkthrough.md) | Kenapa dua cabang, kenapa GAP bukan Flatten, dari mana 6.417 param |
| 5 | [train](train-walkthrough.md) | Kenapa accuracy dilarang, bagaimana class weight bekerja, kenapa monitor AUC |
| 6 | [evaluate](evaluate-walkthrough.md) | Kenapa threshold dikunci sebelum DS2, kelas aritmia mana yang gagal & kenapa |
| 6b | [segmentasi-deteksi](segmentasi-deteksi-walkthrough.md) | Biaya segmentasi on-device: kenapa geser 4 sampel menjatuhkan precision 4×, dan kenapa detektor membuang aritmia |
| 6c | [jitter](jitter-walkthrough.md) | Berapa jauh R-peak di alat meleset sungguhan, kenapa ±18 sampel milik paper tidak boleh disalin, dan kenapa melatih dengan error justru menaikkan angka di data bersih |
| 7 | [quantize](quantize-walkthrough.md) | Apa yang berubah saat INT8, kenapa metrik bisa "naik" tapi model tidak membaik |
| HW | [firmware](firmware-walkthrough.md) | Port ke C, harness golden Python↔C, dan kenapa op `MEAN` harus diganti untuk TFLM |
| HW | [akuisisi](akuisisi-walkthrough.md) | **Panduan kerja**: merekam dari badan, menarik data, menilai kualitas, membuat grafik |

Fase 8 tidak punya walkthrough — isinya verifikasi, bukan konsep baru.
Jalankan `make poc` dan baca `scripts/check_poc.py`.

---

## Empat jebakan yang membentuk seluruh desain

Kalau waktumu sempit, empat ini yang paling menentukan:

| Jebakan | Gejala kalau kena | Dibahas di |
|---|---|---|
| **Filter non-kausal** (`filtfilt`) | Training mulus, akurasi di device anjlok | [1](preprocessing-walkthrough.md) §2 |
| **Alignment window ↔ label** | `assert len(a)==len(b)` LOLOS, recall ~0 di Fase 6 | [2](features-rr-walkthrough.md) §3, [2b](prep-beats-walkthrough.md) §1-2 |
| **Kebocoran identitas pasien** | Akurasi 99% yang tidak berarti apa-apa | [3](dataset-walkthrough.md) §1 |
| **Threshold dituning di DS2** | Angka bagus yang gugur saat ditanya penguji | [6](evaluate-walkthrough.md) §0 |
| **Op sama, hasil beda di TFLM** | Model benar di PC, keyakinan runtuh di device | [HW](firmware-walkthrough.md) §5 |
| **R-peak meleset 4 sampel** | Precision jatuh 4×, tanpa error | [6b](segmentasi-deteksi-walkthrough.md) §2 |
| **Threshold dikalibrasi di kondisi yang salah** | AUC nyaris utuh tapi F1 anjlok 20% | [6c](jitter-walkthrough.md) §4 |

Tiga dari empat **tidak menghasilkan error apa pun**. Itu benang merahnya: bug
paling mahal di ML bukan yang crash, tapi yang menghasilkan angka bagus dari
prosedur yang salah.

---

## Angka penting (rujukan cepat)

**Berlaku sejak 18 Sep 2026** (window 256 + augmentasi jitter, Fase 6c):

```
dataset     44 record, 202.560 beat — DS1 ditumpuk 3 salinan (1 bersih + 2 jitter)
split       DS1 152.904 (10,1%) | DS2 49.656 (11,0%, TIDAK pernah dijitter)
window      128/128 = 256 sampel, R mendarat di indeks 132 (128 + group delay 4)
model       6.417 param (tak berubah: Conv1D tidak tergantung panjang window)
threshold   0,80  (kriteria sama: F1 maksimum di VAL; VAL kini ikut ber-jitter)
DS2 fp32    recall 0,6996  precision 0,6235  F1 0,6594  AUC 0,9334
DS2 INT8    recall 0,7105  precision 0,6169  F1 0,6604  AUC 0,9344   22,94 KB
```

Sebelum Fase 6c (window 250, tanpa augmentasi, threshold 0,35) — rujukan sejarah:

```
dataset     100.619 beat | DS1 50.965 | DS2 49.654
DS2 fp32    recall 0,6661  precision 0,4919  F1 0,5659  AUC 0,8866
DS2 INT8    recall 0,6549  precision 0,5302  F1 0,5859  AUC 0,8862
device      26,0 ms/detak, tensor arena 12.756 B, cocok PC digit demi digit
per kelas   V 0,9332 | S 0,3034 | F 0,1675
```

Kandidat perbaikan Fase 6c (3 seed, BELUM dikunci ke `config.py` — lihat
[jitter](jitter-walkthrough.md) §5):

```
baseline (rantai sama)   F1 DS2 0,5660 ± 0,0202   AUC 0,8870
+ augmentasi jitter      F1 DS2 0,6354 ± 0,0428   AUC 0,9084
+ window 128/127         F1 DS2 0,6775 ± 0,0112   AUC 0,9394
jitter empiris di DS2    F1      0,6670 ± 0,0194  (model w128, kondisi deploy)
```

Dua angka yang paling perlu kamu bisa jelaskan di sidang:

1. **Accuracy DS2 (0,8878) lebih rendah dari menebak Normal terus (0,8903)** —
   dan kenapa model tetap jauh lebih berguna. → [5](train-walkthrough.md) §3,
   [6](evaluate-walkthrough.md) §4
2. **Recall F cuma 0,1675** — dan kenapa itu sudah bisa diramalkan sejak Fase 3
   (372 dari 414 beat F di DS1 ada di record 208 sendirian). →
   [6](evaluate-walkthrough.md) §5

---

## Riwayat eksperimen yang TIDAK mengubah config (19 Sep 2026)

Tiga dokumen di bawah mencatat eksperimen besar yang **kesimpulannya: jangan
diubah**. Dibaca kalau kamu bertanya *"kenapa tidak pakai dataset lain?"* atau
*"kenapa fitur lebar QRS tidak dipakai padahal peringkat 1?"* — jawabannya sudah
diukur, bukan diasumsikan.

| Dokumen | Isi | Vonis |
|---|---|---|
| [fitur-design](2026-09-19-fitur-design.md) | Sintesis 7 paper, 10 temuan yang menabrak decision point terkunci | dokumen KEPUTUSAN, bukan hasil |
| [multidataset-plan](2026-09-19-multidataset-plan.md) | Fase A: gabung mitdb + svdb + incartdb, audit 13 pemeriksaan | infrastruktur jadi, DS2 byte-identik |
| [faseB-changelog](2026-09-19-faseB-changelog.md) | Fase B-F: 10 varian × 3-6 seed, tabel 2×2, tahap 2 | **kunci nol** |

### Ringkasan satu layar

Tabel 2×2 dataset × fitur (ambang sinyal §7: < 0,04 F1 bukan sinyal):

```
F1              fitur LAMA (3)    fitur BARU (6)
mitdb saja      0,6911 +-0,029    0,6882 +-0,023     <- yang TERPASANG
mitdb+svdb      0,6262 +-0,063    0,6960 +-0,049

svdb merugikan -0,065   fitur baru menambalnya +0,070   hasil akhir +0,005
```

**Interaksi murni, bukan dua perbaikan bertumpuk.** svdb menurunkan F1 lewat
pergeseran domain; fitur baru cuma menambal kerusakan itu; gabungannya kembali ke
titik awal. Tanpa sel keempat (mitdb + fitur baru), kesimpulannya salah dua kali.

Yang **masuk produksi** dari seluruh eksperimen: satu assert
(`MAX_RHYTHM_SCALE`). Yang jadi **temuan untuk laporan**: 10 butir, dicatat di
faseB-changelog §10.

### Alat baru yang tersedia

| Skrip | Untuk apa |
|---|---|
| `scripts/cek_lead.py` | Polaritas & alignment lead antar-database. Dua kolom (mentah/selaras), dua vonis — jangan tertukar |
| `scripts/cek_kalibrasi.py` | Seberapa jauh kalibrasi VAL dari optimum DS2. DS2 mendiagnosis, TIDAK memilih |
| `scripts/tahap2.py` | Aturan penamaan V/S di atas keputusan biner. Tidak dikirim: VAL cuma bisa mensertifikasi presisi 43,9% |
| `scripts/ablasi.py --db` | Latih multi-database. Bawaan `mitdb` = jalur terkunci, byte-identik |
| `PA_QRSW=1` `PA_RR_RATIO=1` | Knob fitur Fase D. Tanpa env, nilainya persis seperti semula |

---

## Cara menjalankan ulang semuanya

```
make data && make check     # Fase 0  (sekali)
make prep                   # Fase 2  → per_record/*.npz
make split                  # Fase 3  → train.npz, test.npz
make train                  # Fase 5  → model_fp32.keras
python scripts/calibrate_threshold.py   # kunci threshold di VAL
make eval                   # Fase 6  → metrik DS2 float32
make quantize               # Fase 7  → model_int8.tflite + tabel delta
make poc                    # Fase 8  → checklist 8/8
make export                 # → firmware/include/model_int8.h
make test                   # 80 test
cd ../firmware && pio test -e native      # 17 test preprocessing di PC
                  pio test -e esp32-s3    # + inferensi di board
```

Seed dikunci (`config.SEED = 42`), jadi angka di atas harus keluar sama.
