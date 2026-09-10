# Walkthrough `src/train.py` — Fase 5

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
train.npz (DS1, 50.965 beat)
        │
        │  split_train_val()   ← per pasien: 5 record disisihkan
        ▼
 train 40.617 beat            val 10.348 beat
 (4.105 aritmia, 10,11%)      (1.046 aritmia, 10,11%)
        │                            │
        │  class_weight              │  EarlyStopping(val_auc)
        ▼                            ▼
   model.fit(...)  ──────────►  artifacts/model_fp32.keras
                                artifacts/metrics/fase5_training.png
```

**DS2 tidak disentuh sama sekali di fase ini.** Semua angka yang kamu lihat —
loss, recall, AUC, threshold — datang dari DS1.

---

## 1. Masalahnya: 90% Normal

Kalau model menebak "Normal" untuk semua 40.617 beat, accuracy-nya **89,9%**.
Terdengar bagus, gunanya nol: recall aritmia = 0. Untuk deteksi dini, satu-satunya
kesalahan yang benar-benar berbahaya adalah **aritmia yang lolos** (false
negative), dan justru itu yang model malas pelajari kalau dibiarkan.

Tanpa penanganan, gradien dari 36.512 beat Normal menenggelamkan gradien dari
4.105 beat Aritmia. Model menemukan jalan pintas, dan jalan pintas itu terlihat
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

$$w_0 = \frac{40617}{2 \cdot 36512} = 0{,}556, \qquad
w_1 = \frac{40617}{2 \cdot 4105} = 4{,}947$$

Yang penting bukan angkanya, tapi **hasil kalinya**:

$$n_0 w_0 = 36512 \times 0{,}556 \approx 20308 \approx 4105 \times 4{,}947 = n_1 w_1$$

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
baris di atas, dan `scikit-learn` belum ada di `requirements.txt`. Aturan gate
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
| **`val_auc`** ✓ | Mengukur kualitas **peringkat** probabilitas, tidak tergantung threshold, dan tidak bisa dipalsukan dengan menebak satu kelas. |

`restore_best_weights=True` penting: setelah `patience=8` epoch tanpa perbaikan,
bobot dikembalikan ke epoch terbaik — bukan bobot epoch terakhir yang sudah
overfit. `EPOCHS = 60` di `config.py` cuma batas atas; yang benar-benar
menentukan kapan berhenti adalah callback ini.

---

## 5. Hasil training

```
train 40617 beat (4105 aritmia)   val 10348 beat (1046 aritmia)
class_weight  Normal 0.556  Aritmia 4.947

VAL @ threshold 0.5   TP=728  FN=318  FP=67  TN=9235
  recall 0.6960    precision 0.9157    specificity 0.9928
```

Kurvanya: `artifacts/metrics/fase5_training.png`.

### Membaca angkanya jujur

**Recall 0,70** — dari 1.046 beat aritmia di val, 728 tertangkap, **318 lolos**.
Untuk inter-patient yang jujur ini masuk akal (literatur intra-patient yang
melaporkan 99% bermain di aturan berbeda), tapi jelas belum layak klinis.

**Precision 0,92 & specificity 0,993** — kalau alat berbunyi, hampir selalu
benar. Dari 9.302 beat normal, cuma 67 memicu alarm palsu.

**Ketimpangan recall vs precision itu petunjuk arah:** model terlalu
konservatif di threshold 0,5. Menurunkan threshold akan menukar precision
(yang berlebih) dengan recall (yang kurang) — dan PRD memang menyebut threshold
sebagai knob yang boleh dikalibrasi **di val, bukan DS2**.

### Yang terlihat dari kurva: overfitting nyata

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

## 6. Dropout: keputusan diuji ulang dengan angka

Keputusan awal (`DROPOUT_RATE = 0.0`) diambil dari rasio 50.965 sampel : 6.417
param ≈ 8. Begitu kurva menunjukkan overfit, keputusan itu **wajib diuji ulang**
— bukan dipertahankan karena sudah tertulis. Empat nilai, seed sama:

| dropout | val AUC | val recall | val precision |
|---|---|---|---|
| **0.0** ✓ | 0,9576 | **0,6998** | 0,9470 |
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

## 7. Yang sengaja TIDAK dilakukan

**Tidak menyentuh DS2.** Termasuk untuk "mengintip" saja. Sekali dilihat untuk
mengambil keputusan, DS2 tidak murni lagi dan seluruh klaim Fase 6 gugur.

**Tidak mengubah threshold di sini.** Tetap 0,5. Kalibrasinya boleh, tapi
memakai kurva val — dan itu urusan Fase 6 dengan prosedur yang tercatat.

**Tidak menyetel learning rate.** `adam` default (1e-3). Menambah knob yang
belum terbukti perlu = ruang tuning yang harus dipertanggungjawabkan di sidang
tanpa alasan kuat.

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
| `make test` | 34 test — 4 di antaranya mengunci rumus class weight |

---

**[← Fase 4 — model](model-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 6 — evaluate →](evaluate-walkthrough.md)**
