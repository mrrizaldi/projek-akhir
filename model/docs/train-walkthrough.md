# Walkthrough `src/train.py` — Fase 5

> **Ruang lingkup:** pelatihan model hybrid di DS1: class weight, metrik yang dipantau, EarlyStopping, dan jadwal latih pada konfigurasi terkunci.
> **Kode terkait:** `src/train.py`, `scripts/train_model.py`, `scripts/ablasi.py`, `src/dataset.py` (`split_train_val`), `config.py` (`EPOCHS`, `BATCH_SIZE`, `EARLY_STOP_*`, `VAL_RECORDS`, `SEED`, `THRESHOLD`), `tests/test_train.py`
> **Prasyarat:** [`model-walkthrough.md`](model-walkthrough.md)

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 13–14. Lanjutan dari
[`model-walkthrough.md`](model-walkthrough.md) (Fase 4).

Reproduksi:

```
cd model
make train          # → artifacts/model_fp32.keras + artifacts/metrics/fase5_training.png
```

---

## 0. Peta besar

```
train.npz (DS1, 152.904 beat = 50.968 × 3 salinan)
        │
        │  split_train_val()   ← per pasien: 5 record VAL_RECORDS disisihkan
        ▼
 train 121.857 beat           val 31.047 beat
 (12.315 aritmia, 10,11%)     (3.138 aritmia, 10,11%)
        │                            │
        │  class_weight              │  EarlyStopping(val_auc)
        ▼                            ▼
   model.fit(...)  ──────────►  artifacts/model_fp32.keras
                                artifacts/metrics/fase5_training.png
```

**DS2 tidak disentuh sama sekali di fase ini.** Semua angka yang kamu lihat —
loss, recall, AUC, threshold — datang dari DS1. Train dan val sama-sama memuat
salinan ber-jitter (satu bersih + dua ber-jitter per beat), karena keduanya
dipotong dari `train.npz` yang sama.

---

## 1. Masalahnya: 90% Normal

Kalau model menebak "Normal" untuk semua 121.857 beat, accuracy-nya **89,9%**.
Terdengar bagus, gunanya nol: recall aritmia = 0. Untuk deteksi dini, satu-satunya
kesalahan yang benar-benar berbahaya adalah **aritmia yang lolos** (false
negative), dan justru itu yang model malas pelajari kalau dibiarkan.

Tanpa penanganan, gradien dari 109.542 beat Normal menenggelamkan gradien dari
12.315 beat Aritmia. Model menemukan jalan pintas, dan jalan pintas itu terlihat
sukses di metrik yang salah.

---

## 2. `make_class_weights()` — menyetarakan suara, bukan menyalin data

```python
counts = np.bincount(y, minlength=2)
if (counts == 0).any():
    raise ValueError(...)
return {c: len(y) / (2.0 * counts[c]) for c in (0, 1)}
```

Rumus *balanced* baku:

$$w_c = \frac{N}{K \cdot n_c}, \qquad K = 2\ \text{kelas}$$

Untuk DS1-train:

$$w_0 = \frac{121857}{2 \cdot 109542} = 0{,}556, \qquad
w_1 = \frac{121857}{2 \cdot 12315} = 4{,}948$$

Yang penting bukan angkanya, tapi **hasil kalinya**:

$$n_0 w_0 = 109542 \times 0{,}556 \approx 60929 \approx 12315 \times 4{,}948 = n_1 w_1$$

Kedua kelas menyumbang total loss yang sama besar. Satu beat Aritmia yang salah
"berteriak" 8,9× lebih keras daripada satu beat Normal yang salah. Ini
di-assert di `tests/test_train.py::test_kontribusi_dua_kelas_jadi_setara`.

### Kenapa bukan oversampling

Oversampling menggandakan beat minoritas sampai seimbang. Efek loss-nya mirip,
tapi duplikatnya adalah **beat dari pasien yang sama** — model jadi punya lebih
banyak kesempatan menghafal individu, bertentangan dengan seluruh semangat
inter-patient. Plus epoch membengkak ~1,8×. PRD tegas: pilih satu, jangan
dua-duanya (bisa over-koreksi).

### Kenapa tidak pakai `sklearn.utils.class_weight`

PRD mencontohkan `compute_class_weight("balanced", ...)`. Rumusnya persis dua
baris di atas, dan `scikit-learn` tidak ada di `requirements.txt`. Aturan gate
point `CLAUDE.md`: jangan tambah dependency untuk sesuatu yang beberapa baris
sudah selesai — apalagi paket sebesar sklearn yang cuma dipakai satu fungsi.

---

## 3. Metrik: kenapa `accuracy` tidak ada di daftar

```python
metrics=[Recall(name="recall"), Precision(name="precision"), AUC(name="auc")]
```

| Metrik | Menjawab pertanyaan | Kenapa ada di sini |
|---|---|---|
| **Recall** | Dari semua aritmia asli, berapa % tertangkap? | Kegagalan paling berbahaya = aritmia lolos |
| **Precision** | Dari semua alarm, berapa % benar? | Alarm palsu bikin alat diabaikan (*alarm fatigue*) |
| **AUC** | Seberapa baik model **mengurutkan** aritmia di atas normal? | Bebas threshold — lihat §4 |

Accuracy sengaja tidak dipantau. Di data 90:10 dia bisa 89,9% tanpa model
belajar apa pun; menampilkannya cuma mengundang salah baca.

---

## 4. EarlyStopping — dan kenapa memantau AUC, bukan recall

```python
callbacks.EarlyStopping(monitor="val_auc", mode="max",
                        patience=8, restore_best_weights=True)
```

Tiga kandidat yang dipertimbangkan:

| Monitor | Masalahnya |
|---|---|
| `val_recall` | Bisa "dicurangi": tebak Aritmia untuk semua → recall 1,0, precision hancur. Metrik yang bisa dimaksimalkan dengan model rusak bukan pemandu yang aman. |
| `val_loss` | Loss di sini sudah **terdistorsi `class_weight`** — nilainya bukan lagi likelihood yang bisa ditafsir langsung, dan bergerak tidak sejalan dengan kualitas urutan. |
| **`val_auc`** (dipakai) | Mengukur kualitas **peringkat** probabilitas, tidak tergantung threshold, dan tidak bisa dipalsukan dengan menebak satu kelas. |

`restore_best_weights=True` penting: setelah `patience=8` epoch tanpa perbaikan,
bobot dikembalikan ke epoch terbaik — bukan bobot epoch terakhir yang sudah
overfit. `EPOCHS = 60` di `config.py` cuma batas atas; yang benar-benar
menentukan kapan berhenti adalah callback ini.

Pada konfigurasi terkunci, "epoch terbaik" adalah **epoch 0**, sehingga
`patience=8` melatih 8 epoch yang seluruhnya dibuang. Lihat §6b.

---

## 5. Hasil training

Model produksi (`artifacts/model_fp32.keras`), konfigurasi terkunci:

```
train 121857 beat (12315 aritmia)  val 31047 beat (3138 aritmia)
class_weight  Normal 0.556  Aritmia 4.948

VAL @ threshold 0.8   TP=2052  FN=1086  FP=743  TN=27166
  recall(sensitivity) 0.6539   precision 0.7342   specificity 0.9734
```

Kurvanya: `artifacts/metrics/fase5_training.png`.

### Membaca angkanya jujur

`make train` mencetak VAL pada `THRESHOLD` terkunci (0,80), bukan 0,5. Pada 0,5
model yang sama memberi recall 0,8445 tetapi precision cuma 0,3193 (5.650 alarm
palsu dari 27.909 beat normal). Threshold 0,80 dipilih di VAL dengan kriteria F1
maksimum dan memindahkan titik operasi ke recall 0,65 / precision 0,73. Itu
pertukaran yang sah karena dikalibrasi **di val, bukan DS2**; prosedurnya milik
Fase 6 (`scripts/calibrate_threshold.py`).

**Recall 0,65** — dari 3.138 beat aritmia di val, 2.052 tertangkap, **1.086
lolos**. Untuk inter-patient yang jujur ini masuk akal (literatur intra-patient
yang melaporkan 99% bermain di aturan berbeda), tapi jelas belum layak klinis.

**Specificity 0,973** — dari 27.909 beat normal, 743 memicu alarm palsu.

### Yang terlihat dari kurva: overfitting nyata

Kondisi ukur bagian ini dan §6: window 90/160 (250 sampel), tanpa augmentasi
jitter, Adam 1e-3, threshold 0,5. Pada konfigurasi itu val berisi 10.348 beat
(1.046 aritmia) dan model terbaik memberi VAL @0,5: TP=728 FN=318 FP=67 TN=9235
(recall 0,6960, precision 0,9157, specificity 0,9928). Pelajaran tentang
overfitting dan `restore_best_weights` berlaku sama pada konfigurasi terkunci,
yang bahkan memuncak lebih awal (§6b).

| | epoch 4 (terbaik) | epoch 12 (berhenti) |
|---|---|---|
| train recall | 0,924 | 0,960 |
| **val** recall | 0,696 | 0,772 |
| **val** precision | 0,916 | 0,693 |
| **val AUC** | **0,9432** | 0,9271 |

Train terus membaik sementara val AUC menurun sejak epoch 4 — definisi
overfitting. `restore_best_weights` yang menyelamatkan; tanpa itu model yang
tersimpan adalah versi epoch 12 dengan precision anjlok ke 0,69.

---

## 6. Dropout: keputusan diuji dengan angka

`DROPOUT_RATE = 0.0` berangkat dari rasio data : parameter
([`model-walkthrough.md`](model-walkthrough.md) §4). Karena kurva menunjukkan
overfit, nilai itu diuji, bukan dipertahankan karena sudah tertulis. Empat
nilai, seed sama, kondisi ukur seperti §5:

| dropout | val AUC | val recall | val precision |
|---|---|---|---|
| **0.0** (dipakai) | 0,9576 | **0,6998** | 0,9470 |
| 0.2 | 0,9616 | 0,2744 | 0,9863 |
| 0.3 | 0,9290 | 0,3585 | 0,9446 |
| 0.5 | 0,9615 | 0,6511 | 0,9813 |

Kesimpulan: **dropout tidak membantu di sini, malah merusak recall.** Yang
terjadi — dropout membuat model makin konservatif (precision naik, recall
turun), padahal masalah kita justru recall yang kurang. AUC nyaris tidak
berubah, artinya kemampuan *mengurutkan* sama saja; yang bergeser cuma di mana
probabilitasnya menumpuk relatif terhadap 0,5.

Pelajarannya: overfitting yang terlihat di kurva **tidak otomatis berarti
"tambah regularisasi"**. Di sini akar masalahnya bukan model terlalu besar
(6.417 param), tapi variasi antar-pasien — dan itu tidak bisa diobati dropout.

---

## 6b. Jadwal latih pada konfigurasi terkunci

Pada konfigurasi window 90/160 tanpa augmentasi (§5), training berhenti di
epoch 12 dengan epoch terbaik 4. Pada konfigurasi terkunci (window 128/128 +
augmentasi jitter ×3), bentuk kurvanya lain sama sekali.

### Model produksi adalah hasil SATU epoch

```
lr 1e-3 (terkunci), seed 7      lr 1e-4, seed 7
epoch 0  val_auc 0,9492  <-     epoch 0   0,8797   masih naik
epoch 1          0,9345         epoch 2   0,9067
epoch 2          0,9279         epoch 2-19  dataran ~0,905-0,911
...      turun monoton          epoch 18  0,9113  <- puncak
epoch 8          0,8635  stop   epoch 26  0,9082  stop
9 epoch, 8 terbuang             27 epoch, membaik selama 19
```

`patience=8` membuat training selalu jalan 9 epoch, lalu
`restore_best_weights` mengembalikan epoch 0. Delapan epoch sisanya murni
overfitting.

**Kenapa secepat itu?** Karena "epoch" menyesatkan sebagai satuan. DS1 yang
sudah diaugmentasi punya 121.857 beat; dengan `BATCH_SIZE = 64` itu **1.905
langkah gradien per epoch**. Untuk model 6.417 parameter dengan Adam 1e-3,
satu epoch sudah lebih dari cukup untuk menghafal. Yang terlihat sebagai
"berhenti di epoch 9" sebenarnya "berhenti setelah 17.145 langkah".

Pelajaran umum: **jangan pernah menilai lama latih dari jumlah epoch** tanpa
mengalikannya dengan langkah per epoch. Augmentasi ×3 di Fase 6c melipatgandakan
langkah per epoch, jadi setiap kali ukuran data latih berubah, kurva `val_auc`
perlu dicetak ulang untuk melihat letak puncaknya.

### Alternatif yang tidak dipakai: rata-rata bobot (`--swa N`)

Hipotesis: kalau yang memilih bobot akhir adalah lotere `val_auc` yang berisik,
rata-ratakan saja beberapa epoch teratas alih-alih memungut argmax-nya.
`RataBobotTerbaik` dipasang **sesudah** `EarlyStopping` supaya menimpa hasil
`restore_best_weights`.

Aman tanpa hitung ulang apa pun: model ini **tidak punya BatchNorm**
(Conv1D → MaxPool → GAP → Dense), jadi jebakan baku SWA — statistik BN harus
dihitung ulang setelah bobot dirata-rata — tidak berlaku.

Hasil 3 seed: F1 DS2 0,6911 → 0,6346 (**−0,057, di atas ambang sinyal**).
Diagnosis mencetak epoch yang dirata-rata: `[0, 1, 2]`.

**Kenapa gagal:** tidak ada "nyaris seri" untuk dirata-rata. Puncaknya di tepi
kurva dan sisanya menurun monoton, jadi merata-rata apa pun berarti menarik
masuk bobot yang lebih buruk. Rata-rata bobot butuh **dataran**, dan pada
1e-3 tidak ada dataran. Knob `--swa` ditinggal: di 1e-4 dataran itu ada, jadi
hipotesisnya layak diuji ulang di sana.

### Learning rate 1e-4 (`--lr`)

| Set uji | pasien | F1 1e-3 | F1 1e-4 | AUC |
|---|---|---|---|---|
| DS2 | 22 | 0,6535 ±0,0280 | 0,6729 ±0,0483 | 0,9305 → 0,9415 |
| TEST-B (svdb) | 20 | 0,5237 ±0,0084 | 0,5306 ±0,0339 | 0,8667 → 0,8860 |
| TEST-C (incartdb) | 19 | 0,6784 ±0,1080 | **0,8025 ±0,0277** | 0,9352 → 0,9525 |

AUC naik di 4 dari 4 set. Tapi ada pertukaran tajam: **recall V naik di 3 dari
3 seed, recall S turun di 2 dari 3** — padahal threshold 1e-4 lebih longgar
(0,53 vs 0,65), yang seharusnya menaikkan recall. Jadi ini bukan artefak titik
operasi: modelnya memang memeringkat beat S lebih buruk.

Artinya 1e-4 memperbaiki kelas yang sudah kuat (V) dan memperburuk yang lemah
(S) — arah yang berlawanan dengan kebutuhan proyek ini. Recall per kelas di
DS2 (rerata 3 seed), termasuk LR tengah 3e-4:

| LR | recall **S** | recall **V** | recall **F** | DS2 AUC | TEST-C F1 |
|---|---|---|---|---|---|
| **1e-3** (dipakai) | **0,4473** | 0,9151 | 0,1804 | 0,9305 | 0,6784 ±0,1080 |
| 3e-4 | 0,2024 | 0,9663 | 0,3265 | 0,9348 | **0,8481 ±0,0098** |
| 1e-4 | 0,3126 | **0,9736** | **0,3591** | **0,9415** | 0,8025 ±0,0277 |

3e-4 justru paling buruk di S, jadi tidak ada titik tengah yang memuaskan
keduanya: menurunkan LR menurunkan S dan menaikkan yang lain. Defisit S
terbukti nyata di titik operasi yang setara (6 dari 6 titik,
`scripts/cek_titik_operasi.py`), bukan artefak threshold. **LR tetap 1e-3.**

### Efek samping metodologis: ambang 0,04 berlaku untuk rerata 3 seed

Konfigurasi identik, seed identik, dijalankan dua kali pada hari yang sama:

```
batch 1   F1 DS2 0,6911 ±0,0290
batch 2   F1 DS2 0,6535 ±0,0280
selisih   0,0376
```

**Rerata 3 seed pun bergoyang ~0,04 antar batch.** Konsekuensinya: selisih di
bawah 0,04 tidak berubah jadi sinyal hanya karena diulang 3 seed. Yang benar-benar
menaikkan daya pisah adalah **set uji yang lebih besar** — itulah gunanya
TEST-B/TEST-C (39 pasien held-out, `ablasi.py --lintas-db`).

---

## 7. Yang sengaja TIDAK dilakukan

**Tidak menyentuh DS2.** Termasuk untuk "mengintip" saja. Sekali dilihat untuk
mengambil keputusan, DS2 tidak murni lagi dan seluruh klaim Fase 6 gugur.

**Tidak mengkalibrasi threshold di sini.** Metrik Keras selama latih memakai
0,5 bawaan. Kalibrasi threshold memakai kurva val dan merupakan urusan Fase 6
dengan prosedur yang tercatat (`scripts/calibrate_threshold.py` → 0,80);
`make train` hanya membaca `THRESHOLD` untuk ringkasan VAL.

**Tidak menurunkan learning rate.** `adam` bawaan (1e-3). Konsekuensinya
diketahui: `val_auc` memuncak di **epoch 0**, jadi model produksi adalah hasil
**satu epoch** latih (§6b). LR lebih rendah sudah diablasi (3 LR × 3 seed + 39
pasien held-out) dan **menukar recall S dengan recall V dan F**. Karena S adalah
fokus penelitian ini, pertukaran itu ditolak dan dilaporkan apa adanya. Knob
`ablasi.py --lr` tersedia untuk pengujian ulang.

**Seed dikunci** (`np.random.seed(SEED)`, `tf.random.set_seed(SEED)`) sebelum
model dibangun. Tanpa ini, hasil tidak reproducible dan angka di Bab 4 tidak
bisa diulang oleh penguji.

---

## 8. Cek pemahaman

1. `class_weight` dihapus. Prediksi apa yang terjadi pada accuracy, recall, dan
   AUC — dan kenapa dua di antaranya bisa terlihat *membaik*?
2. `restore_best_weights=False`. Model mana yang tersimpan, dan berapa
   precision-nya menurut tabel §5?
3. Threshold diturunkan 0,5 → 0,3. Ke arah mana TP, FP, recall, dan precision
   bergerak? Kenapa kalibrasi ini haram dilakukan di DS2?
4. Dropout 0,2 memberi val AUC **tertinggi** (0,9616) tapi recall terburuk
   (0,2744). Bagaimana dua hal itu bisa terjadi bersamaan?

## 9. Skrip pendukung

| Perintah | Melihat apa |
|---|---|
| `make train` | Latih + simpan model & kurva + ringkasan confusion matrix val |
| `make test` | Seluruh test; `tests/test_train.py` mengunci rumus class weight dan `RataBobotTerbaik` |

---

**[← Fase 4 — model](model-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 6 — evaluate →](evaluate-walkthrough.md)**
