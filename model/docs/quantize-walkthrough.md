# Walkthrough `src/quantize.py` — Fase 7

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 16–17. Lanjutan dari
[`evaluate-walkthrough.md`](evaluate-walkthrough.md) (Fase 6).

Reproduksi:

```
cd model
make quantize     # → artifacts/model_int8.tflite + artifacts/metrics/fase7_delta.csv
```

---

## 0. Peta besar

```
model_fp32.keras (6.417 param, 25,07 KB float32)
        │
        │  PTQ — Post-Training Quantization
        │  butuh: representative dataset (300 sampel DS1, stratified)
        ▼
model_int8.tflite   17,84 KB   ← DoD: < 20 KB ✓
        │
        │  evaluasi ULANG di DS2 yang SAMA, threshold yang SAMA (0,35)
        ▼
tabel delta float32 vs INT8   ← deliverable akhir PA
```

Kenapa fase ini ada: device menjalankan INT8, bukan float32. Klaim
"dampak kuantisasi **diukur**, bukan diasumsikan" cuma bisa dibuat kalau ada
angka delta nyata.

---

## 1. Apa yang sebenarnya terjadi saat kuantisasi

Float32 memakai 32 bit per angka. INT8 memakai 8 bit — 256 nilai saja. Pemetaan
antara keduanya affine:

$$x_{\text{float}} \approx (q_{\text{int8}} - z) \times s$$

dengan $s$ = *scale* (jarak antar-langkah) dan $z$ = *zero point* (bilangan bulat
yang memetakan nol). Model hasil kita:

| Tensor | scale | zero point |
|---|---|---|
| input morfologi | 0,042865 | −24 |
| input ritme | 0,042874 | −109 |
| output (probabilitas) | 0,00390625 = 1/256 | −128 |

Output scale 1/256 dengan zero −128 masuk akal: sigmoid selalu di $[0,1]$, jadi
256 langkah dipakai penuh untuk rentang itu — $p = (q + 128)/256$.

**Yang perlu dikalibrasi bukan bobot, tapi aktivasi.** Bobot sudah diketahui
rentangnya (tinggal dilihat). Rentang aktivasi tiap layer hanya muncul saat data
mengalir — makanya butuh *representative dataset*.

---

## 2. `stratified_indices()` — JEBAKAN #4

```python
for kelas in (0, 1):
    pool = np.flatnonzero(y == kelas)
    if len(pool) == 0:
        raise ValueError(f"kelas {kelas} tidak ada di data kalibrasi (JEBAKAN #4)")
    ambil = max(1, round(n * len(pool) / len(y)))
```

Kalau 300 sampel kalibrasi diambil acak dari DS1 tanpa stratifikasi, secara
statistik memang akan kena ~30 beat Aritmia. Tapi "biasanya kena" bukan jaminan
— dan kalau meleset, yang rusak justru **kelas yang paling kamu pedulikan**:
aktivasi khas beat aritmia tidak pernah terlihat kalibrator, rentangnya
dipotong, dan recall INT8 anjlok tanpa penyebab yang kelihatan.

Stratifikasi membuatnya deterministik: proporsi kelas kalibrasi = proporsi DS1
(270 Normal : 30 Aritmia), dan kelas kosong → `raise`, bukan diam.

`seed` dikunci supaya `make quantize` dua kali menghasilkan `.tflite` identik —
syarat reproducibility di checklist Fase 8.

### Kenapa 300, bukan 100 atau 500

PRD memberi rentang ~100–500. Makin banyak sampel, estimasi rentang aktivasi
makin stabil, tapi konversi makin lama. 300 memberi 30 beat Aritmia — cukup
untuk mencakup ekor distribusi — dan konversinya masih hitungan detik.

---

## 3. `representative_dataset_gen()` — JEBAKAN #3, dan versi yang benar-benar jalan

Model ini punya **dua** input. PRD memperingatkan generator satu-input akan
membuat converter gagal. Yang tidak tertulis di PRD: bentuk **list posisional**
pun bermasalah di TF 2.21.

```python
yield [X_morph[i:i+1], X_rr[i:i+1]]        # ← GAGAL
```

```
RuntimeError: tensorflow/lite/kernels/conv.cc:345 input->dims->size != 4 (3 != 4)
              Node number 1 (CONV_2D) failed to prepare.
```

Kalibrator memasangkan elemen list ke tensor input **menurut urutan internal
model**, bukan urutan yang kamu tulis. Di model ini urutan internalnya
`rhythm` lebih dulu, jadi vektor RR `(1,3)` dijejalkan ke input konvolusi.
Pesan errornya menyebut `conv.cc` dan jumlah dimensi — sama sekali tidak
menyinggung "urutan input salah".

Bentuk yang benar: **dict bernama**.

```python
yield {
    "morphology": X_morph[i:i+1].astype(np.float32),
    "rhythm":     X_rr[i:i+1].astype(np.float32),
}
```

Nama key = nama layer `Input(..., name=...)` di `src/model.py`. Ini salah satu
alasan layer input diberi nama sejak Fase 4 — bukan sekadar kerapian.

---

## 4. `quantize_int8()` — empat baris yang menentukan

```python
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = rep_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
```

| Baris | Kalau dilewatkan |
|---|---|
| `optimizations` | tidak ada kuantisasi sama sekali |
| `representative_dataset` | jadi *dynamic range quantization* — bobot INT8, aktivasi tetap float |
| `supported_ops = ..._INT8` | converter boleh menyisipkan kernel float sebagai fallback |
| `inference_*_type = int8` | I/O tetap float32, ada op quantize/dequantize di ujung |

Keputusan **int8 in / int8 out** (`config.INT8_IO = True`) dikunci agar
konsisten dengan rencana firmware: tidak ada satu pun kernel float di dalam
model. Verifikasinya mekanis di `tests/test_quantize.py`:

```
dtype semua tensor: {'int8': 30, 'int32': 12}
```

Nol tensor `float32`. `int32` yang 12 itu tensor bias — memang begitu di skema
INT8 TFLite: akumulator perkalian int8×int8 disimpan 32-bit sebelum di-*rescale*.

### Konsekuensi untuk firmware

```c
// masuk: hasil z-score (float) → int8
in[i] = (int8_t)lroundf(x[i] / 0.042865f + (-24));
// keluar: int8 → probabilitas
float p = (out[0] - (-128)) * 0.00390625f;
```

Angka `scale` dan `zero_point` ikut ter-*generate* di `model_int8.h` — jangan
di-hardcode manual di `main.cpp`, karena berubah tiap kali model dilatih ulang.

---

## 5. `predict_tflite()` — jebakan ketiga: lupa dequantize

```python
inputs = sorted(interp.get_input_details(), key=lambda d: len(d["shape"]))
rr_in, morph_in = inputs[0], inputs[1]
```

Urutan input di `.tflite` **tidak dijamin** sama dengan urutan di Keras (persis
masalah §3). Di sini dibereskan dengan mengurutkan berdasar jumlah dimensi: RR
2 dimensi `(1,3)`, morfologi 3 dimensi `(1,250,1)`. Tidak bergantung nama
maupun urutan.

Lalu kuantisasi manual masuk, dequantisasi manual keluar:

```python
np.clip(np.round(x / scale) + zero, -128, 127)     # masuk
(q.astype(np.float32) - zero) * scale              # keluar
```

`clip` wajib: nilai z-score bisa melewati rentang yang terlihat saat kalibrasi,
dan tanpa clip hasilnya *wrap around* — angka besar positif jadi negatif ekstrem.
Kalau langkah dequantize di output dilupakan, metrikmu dihitung dari bilangan
bulat −128..127 yang dibandingkan dengan threshold 0,35 → semua terprediksi 1
(PRD menyebut ini eksplisit: "lupa dequantize → metrik ngawur").

---

## 6. Tabel delta — hasil akhir

Ukuran: **18.264 byte = 17,84 KB** (< 20 KB ✓), dari 25,07 KB float32.

| Metrik | Float32 | INT8 | Delta |
|---|---|---|---|
| accuracy | 0,8878 | 0,8987 | **+0,0109** |
| precision | 0,4919 | 0,5314 | **+0,0395** |
| **recall** | 0,6661 | 0,6539 | **−0,0121** |
| F1 | 0,5659 | 0,5863 | **+0,0205** |
| specificity | 0,9152 | 0,9289 | **+0,0137** |
| AUC | 0,8866 | 0,8862 | **−0,0004** |
| TP/FN/FP/TN | 3630/1820/3750/40454 | 3564/1886/3143/41061 | — |

**Recall turun 1,21%** — di bawah ambang "ideal < 1–2%" yang disebut PRD.
Kelayakannya terbukti dengan angka, bukan asumsi.

### Cara membaca angka yang naik

Precision, F1, accuracy, dan specificity justru **membaik**. Itu bukan sihir dan
bukan bukti INT8 "lebih pintar". AUC turun 0,0004 — kemampuan model mengurutkan
praktis tidak berubah, dan itulah ukuran yang jujur.

Yang terjadi: kuantisasi menggeser distribusi probabilitas sedikit ke bawah.
Dengan threshold tetap 0,35, sedikit lebih banyak beat jatuh ke sisi "Normal" —
FP turun 607, FN naik 66. Di data yang 89% Normal, menukar 607 alarm palsu
dengan 66 aritmia yang lolos akan menaikkan hampir semua metrik agregat.

Ini pengingat penting: **selisih metrik pada threshold tetap mencampur dua hal**
— perubahan kualitas model dan pergeseran kalibrasi probabilitas. AUC yang
memisahkan keduanya, dan AUC bilang model INT8 setara.

---

## 7. Yang sengaja TIDAK dilakukan

**Tidak mengubah threshold untuk INT8.** Kalau threshold ikut disetel ulang,
yang terukur bukan lagi efek kuantisasi murni. Prosedur evaluasi harus identik
Fase 6 — DS2 yang sama, threshold yang sama, fungsi metrik yang sama.

**Tidak memakai DS2 sebagai representative dataset.** Kalibrasi mengambil dari
DS1. Menyentuh DS2 di sini akan membocorkan statistik test set ke dalam model.

**Tidak memakai QAT** (Quantization-Aware Training). PTQ sudah memenuhi target
(<1,21% delta recall, 17,84 KB); QAT berarti melatih ulang dan menambah satu
sumber variasi baru untuk keuntungan yang belum tentu ada.

---

## 8. Cek pemahaman

1. `converter.representative_dataset` tidak diisi tapi `optimizations` diisi.
   Model tetap jadi dan lebih kecil — apa yang sebenarnya terkuantisasi, dan
   kenapa itu tidak cukup untuk ESP32?
2. Kenapa ada 12 tensor `int32` di model "full-INT8", dan kenapa itu bukan
   pelanggaran klaim?
3. `np.clip(..., -128, 127)` dihapus dari `_quantize`. Kapan bug-nya muncul, dan
   kenapa tidak muncul di sebagian besar beat?
4. Precision INT8 naik 4 poin sementara AUC turun 0,0004. Jelaskan kenapa dua
   fakta itu tidak bertentangan.

## 9. Skrip pendukung

| Perintah | Keluaran |
|---|---|
| `make quantize` | `model_int8.tflite`, `fase7_delta.csv`, `fase7_confusion_int8.png` |
| `make test` | 49 test — 7 di antaranya mengunci kalibrasi & klaim full-INT8 |

---

**[← Fase 6 — evaluate](evaluate-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **—**
