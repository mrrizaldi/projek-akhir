# Walkthrough `src/model.py` — Fase 4

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 12–13. Lanjutan dari
[`dataset-walkthrough.md`](dataset-walkthrough.md) (Fase 3).

Reproduksi:

```
cd model
.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from src.model import build_hybrid_model
build_hybrid_model().summary()
"
```

---

## 0. Peta besar — dua cabang, satu keputusan

```
 X_morph [N,250,1]                          X_rr [N,3]
        │                                        │
   Conv1D(16,7) → MaxPool                        │
   Conv1D(32,5) → MaxPool                        │   RR_prev
   Conv1D(32,3) → MaxPool                        │   RR_ratio
   GlobalAveragePooling1D                        │   dRR
        │                                        │
     [N,32]  ──────── Concatenate ──────────  [N,3]
                          │
                      [N,35]
                   Dense(16, ReLU)
                          │
                Dense(1, sigmoid) → p(Aritmia)
```

Dua cabang karena aritmia punya **dua tanda tangan yang tidak saling
menggantikan**:

| Cabang | Menangkap | Contoh yang cuma dia bisa lihat |
|---|---|---|
| Morfologi (CNN) | **bentuk** detak | PVC: QRS melebar, gelombang P hilang |
| Ritme (RR) | **waktu** kedatangan | APC: bentuknya nyaris normal, tapi datang terlalu cepat |

Beat atrial premature (`A`) — 33 dari 34 aritmia di record 100 — morfologinya
mirip beat normal. CNN sendirian akan melewatkannya. Yang membedakan cuma
`RR_ratio` 0,77 vs 1,00. Sebaliknya PVC bisa datang tepat waktu tapi bentuknya
jelas beda. Butuh dua-duanya.

Ongkos cabang RR: `Dense(16)` menerima 35 input, bukan 32 → **48 parameter
tambahan**. Murah sekali untuk informasi yang tidak bisa didapat dari mana pun.

---

## 1. Kenapa Functional API, bukan Sequential

```python
return Model(inputs=[morph_in, rr_in], outputs=out, name="hybrid_ecg")
```

`Sequential` itu tumpukan lurus: satu input, satu jalur, satu output. Model ini
punya **dua input yang bertemu di tengah**, jadi Sequential secara struktural
tidak bisa. Functional API memperlakukan layer sebagai fungsi
(`x = layers.Conv1D(...)(x)`), sehingga percabangan dan penggabungan tinggal
soal siapa memanggil siapa.

---

## 2. Cabang morfologi — tiga blok yang mengerucut

```python
for filters, kernel in zip(CONV_FILTERS, CONV_KERNELS):   # (16,32,32), (7,5,3)
    x = layers.Conv1D(filters, kernel, activation="relu", padding="same")(x)
    x = layers.MaxPooling1D(POOL_SIZE)(x)
```

Perjalanan bentuknya:

| Tahap | Output | Param | Cakupan 1 neuron (reseptif) |
|---|---|---|---|
| Input | (250, 1) | — | 1 sampel = 2,8 ms |
| Conv1D(16, 7) | (250, 16) | 128 | 7 sampel ≈ 19 ms |
| MaxPool 2 | (125, 16) | 0 | 39 ms |
| Conv1D(32, 5) | (125, 32) | 2.592 | ~19 sampel asli ≈ 53 ms |
| MaxPool 2 | (62, 32) | 0 | 106 ms |
| Conv1D(32, 3) | (62, 32) | 3.104 | ~35 sampel asli ≈ 97 ms |
| MaxPool 2 | (31, 32) | 0 | ~194 ms |
| GAP | (32,) | 0 | seluruh window |

**Kernel mengerucut 7 → 5 → 3** mengikuti logika ini: di awal, satu sampel cuma
2,8 ms sehingga butuh kernel lebar untuk melihat pola yang berarti. Setelah dua
kali pooling, satu langkah sudah mewakili 11 ms, jadi kernel 3 pun sudah
mencakup ~97 ms — kira-kira selebar kompleks QRS. Filter melihat detail lokal
dulu (lereng, puncak), lalu susunan detail itu (bentuk QRS utuh).

**Filter bertambah 16 → 32 → 32** karena resolusi waktu yang hilang ditukar
dengan keragaman pola. Blok ketiga tidak naik ke 64: itu akan menambah ~6.000
param sendirian dan melanggar anggaran.

`padding="same"` menjaga panjang tetap sebelum pooling, jadi aritmatika
bentuknya bisa diprediksi: 250 → 125 → 62 → 31 (pembagian 2 yang membulat ke
bawah). Nanti saat ditulis di C, angka-angka ini yang jadi ukuran buffer.

---

## 3. `GlobalAveragePooling1D` — keputusan yang menyelamatkan anggaran

Setelah blok terakhir, tensor berbentuk `(31, 32)` = 992 angka. Dua cara
memampatkannya jadi vektor:

| | `Flatten` | **`GlobalAveragePooling1D`** |
|---|---|---|
| Output | 992-dim | 32-dim |
| Param `Dense(16)` berikutnya | 992×16 + 16 = **15.888** | 35×16 + 16 = **576** |
| Total model | ~21.700 | **6.417** |
| INT8 di flash | ~22 KB | **< 20 KB** ✓ |
| Sifat | hafal *di mana* pola muncul | tahan geser: *apakah* pola muncul |

GAP merata-ratakan tiap feature map jadi satu angka: "seberapa kuat filter ini
menyala di sepanjang window". Untuk EKG itu justru cocok — R-peak sudah selalu
di indeks ~94 berkat segmentasi Fase 1, jadi model tidak perlu menghafal posisi.

Ini alasan tunggal terbesar model bisa muat di ESP32. Kalau suatu saat
`count_params()` melompat ke puluhan ribu, tersangka pertama: `Flatten`
menyelinap masuk.

---

## 4. Penggabungan dan kepala klasifikasi

```python
merged = layers.Concatenate()([x, rr_in])          # 32 + 3 = 35
merged = layers.Dense(DENSE_UNITS, activation="relu")(merged)   # 576 param
out = layers.Dense(1, activation="sigmoid")(merged)             # 17 param
```

`Dense(16)` inilah tempat dua sumber informasi benar-benar berinteraksi — di
sini model bisa belajar aturan seperti "QRS lebar **dan** RR_ratio rendah →
sangat mungkin PVC". Sebelum lapisan ini, kedua cabang tidak saling tahu.

`sigmoid` memampatkan skor mentah ke $(0,1)$:

$$\sigma(z) = \frac{1}{1 + e^{-z}}$$

Dipasangkan dengan `binary_crossentropy` (Fase 5). Threshold 0,5 adalah default
yang **dikalibrasi di DS1/val, bukan DS2** — dan menurunkannya adalah cara sah
menaikkan sensitivity nanti.

### Keputusan: tanpa dropout

`DROPOUT_RATE = 0.0` di `config.py`. Alasannya rasio data:

$$\frac{50.965\ \text{sampel latih}}{6.417\ \text{parameter}} \approx 8$$

Model sekecil ini dengan data sebanyak itu lebih mungkin **underfit** daripada
overfit. Dropout 0,3 di lapisan 16-unit berarti mematikan ~5 neuron tiap step —
agresif untuk satu-satunya tempat morfologi dan ritme bertemu, dan berisiko
mengganggu kelas minoritas yang cuma 10%.

Kodenya tetap menyediakan jalannya:

```python
if dropout_rate > 0:
    merged = layers.Dropout(dropout_rate)(merged)
```

Jadi `build_hybrid_model(dropout_rate=0.3)` langsung bisa dipakai kalau kurva
Fase 5 menunjukkan val recall menyimpang dari train. Keputusan berdasar bukti,
bukan berdasar kebiasaan.

---

## 5. Verifikasi

```
Total params: 6,417 (25.07 KB)
```

Rinciannya: 128 + 2.592 + 3.104 + 576 + 17. Cocok dengan target PRD ~6.000.
25 KB itu float32; INT8 nanti ≈ 6,4 KB bobot + overhead runtime → target < 20 KB
masih longgar.

Empat test mengunci kontraknya (`tests/test_model.py`):

| Test | Menangkap kalau... |
|---|---|
| `test_param_budget` | `Flatten` menyelinap, atau Dense kegedean |
| `test_dua_input_satu_output` | bentuk input/output menyimpang dari `.npz` Fase 3 |
| `test_predict_dummy_di_rentang_probabilitas` | aktivasi output bukan sigmoid |
| `test_cabang_ritme_benar_benar_terpakai` | `Concatenate` salah sambung |

Yang terakhir paling berharga dan paling gampang dilupakan: ubah **hanya**
`X_rr`, morfologi dibiarkan nol, output harus berubah. Kalau cabang RR
tak tersambung, model tetap latih mulus, akurasi tetap masuk akal, dan tidak
ada satu pun error — persis jenis bug yang baru ketahuan saat recall APC
mengecewakan di Fase 6.

---

## 6. Cek pemahaman

1. `padding="same"` diganti `"valid"`. Panjang tiap tahap jadi berapa, dan
   kenapa `count_params()` **tidak** berubah?
2. Blok Conv terakhir dinaikkan 32 → 64 filter. Berapa param totalnya sekarang,
   dan apakah masih < 20 KB setelah INT8?
3. GAP diganti `GlobalMaxPooling1D`. Apa yang berubah secara makna untuk sinyal
   EKG yang sudah ter-z-score?
4. Cabang RR dihapus (model cuma morfologi). Kelas aritmia mana yang paling
   dirugikan, dan kenapa metrik akurasi global mungkin nyaris tidak bergerak?

## 7. Skrip pendukung

| Perintah | Melihat apa |
|---|---|
| `make test` | 28 test — 4 di antaranya mengunci arsitektur Fase 4 |
| `python -c "...build_hybrid_model().summary()"` | Tabel layer + `count_params()` |

---

**[← Fase 3 — dataset](dataset-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 5 — train →](train-walkthrough.md)**
