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
   [1]  │  preprocessing.py   bandpass 0,5-40 Hz KAUSAL, potong 250 sampel,
        ▼                       z-score per window   → windows [K,250]
        │
   [2]  │  features_rr.py     RR_prev / RR_ratio / dRR + label biner
        │  prep_beats.py      valid_beat_indices → 44 × per_record/*.npz  [2b]
        ▼                     100.619 beat (10,5% aritmia)
        │
   [3]  │  dataset.py         split PER PASIEN (de Chazal 2004)
        ▼                     train.npz DS1 50.965 | test.npz DS2 49.654
        │
   [4]  │  model.py           CNN morfologi + Dense ritme → 6.417 param
        ▼
        │
   [5]  │  train.py           class_weight, EarlyStopping(val_auc)
        ▼                     → model_fp32.keras   (val: recall 0,81)
        │
        │  calibrate_threshold.py   threshold 0,35 dikunci DI VAL
        ▼
   [6]  │  evaluate.py        DS2 dibuka SEKALI → recall 0,666 AUC 0,887
        ▼
        │
   [7]  │  quantize.py        PTQ INT8 → 17,84 KB, delta recall -1,21%
        ▼
   [8]     check_poc.py       8/8 DoD terverifikasi
           export_model_h.py  → firmware/include/model_int8.h
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
| 7 | [quantize](quantize-walkthrough.md) | Apa yang berubah saat INT8, kenapa metrik bisa "naik" tapi model tidak membaik |

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

Tiga dari empat **tidak menghasilkan error apa pun**. Itu benang merahnya: bug
paling mahal di ML bukan yang crash, tapi yang menghasilkan angka bagus dari
prosedur yang salah.

---

## Angka penting (rujukan cepat)

```
dataset     44 record, 100.619 beat, 10,5% aritmia (dibuang 114 = 44x2 + 26 tepi)
split       DS1 50.965 (10,1%) | DS2 49.654 (11,0%) | val 10.348 dari DS1
model       6.417 param, float32 25,07 KB → INT8 17,84 KB
threshold   0,35  (kriteria F1 maksimum, dikalibrasi di VAL)
VAL         recall 0,8117  precision 0,8132  F1 0,8124
DS2 fp32    recall 0,6661  precision 0,4919  F1 0,5659  AUC 0,8866
DS2 INT8    recall 0,6539  precision 0,5314  F1 0,5863  AUC 0,8862
per kelas   V 0,9332 | S 0,3034 | F 0,1675
```

Dua angka yang paling perlu kamu bisa jelaskan di sidang:

1. **Accuracy DS2 (0,8878) lebih rendah dari menebak Normal terus (0,8903)** —
   dan kenapa model tetap jauh lebih berguna. → [5](train-walkthrough.md) §3,
   [6](evaluate-walkthrough.md) §4
2. **Recall F cuma 0,1675** — dan kenapa itu sudah bisa diramalkan sejak Fase 3
   (372 dari 414 beat F di DS1 ada di record 208 sendirian). →
   [6](evaluate-walkthrough.md) §5

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
make test                   # 49 test
```

Seed dikunci (`config.SEED = 42`), jadi angka di atas harus keluar sama.
