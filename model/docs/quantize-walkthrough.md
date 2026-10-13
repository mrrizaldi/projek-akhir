# Walkthrough `src/quantize.py` — Fase 7

> **Ruang lingkup:** kuantisasi pasca-latih (PTQ) model ke INT8 penuh dan pengukuran dampaknya terhadap metrik DS2.
> **Kode terkait:** `src/quantize.py`, `scripts/quantize_int8.py`, `src/model.py` (`build_deploy_model`), `config.py` (`REP_SAMPLES`, `INT8_IO`, `MAX_MODEL_KB`, `MAX_RHYTHM_SCALE`)
> **Prasyarat:** [`evaluate-walkthrough.md`](evaluate-walkthrough.md) (Fase 6)

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 16–17.

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
model_int8.tflite   22,94 KB   ← di bawah batas 25 KB  (varian deploy, §4b)
        │
        │  evaluasi ULANG di DS2 yang SAMA, threshold yang SAMA (0,80)
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
yang memetakan nol). Nilai pada model yang berlaku
(`firmware/include/model_int8.h`):

| Tensor | scale | zero point |
|---|---|---|
| input morfologi | 0,042908 | −25 |
| input ritme | 0,012933 | −70 |
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

Varian deploy (§4b) menerima input ritme berbentuk `(1, 1, 3)`, bukan `(1, 3)`.
Karena itu `scripts/quantize_int8.py` memanggil generator dengan
`rr_shape=(1, 3)`, dan generator membentuk ulang vektor RR sebelum di-*yield*.

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
dtype semua tensor: {'int8': 39, 'int32': 16}
```

Nol tensor `float32`. Tensor `int32` yang 16 itu terdiri atas dua jenis, dan
keduanya sah di skema INT8 TFLite: **bias** tiap lapisan konvolusi (akumulator
perkalian int8×int8 disimpan 32-bit sebelum di-*rescale*) dan **konstanta
bentuk** statis untuk op `Squeeze`/reshape yang dipakai TFLite saat
mengimplementasikan `Conv1D` lewat konvolusi 2-D.

### Penjaga skala input ritme

`quantize_int8` memanggil `assert_skala_ritme_wajar` sebelum mengembalikan
blob. Skala INT8 input ritme diturunkan dari min/max sampel kalibrasi; satu
beat ber-RR ekstrem di kolam kalibrasi (record 207 punya `RR_prev` = 100 s)
melebarkan skala puluhan kali, RR normal tinggal beberapa level int8, dan
cabang ritme praktis mati. Gejalanya recall S yang buruk, bukan error. Blob
dengan skala di atas `MAX_RHYTHM_SCALE` (0,05) ditolak dengan `ValueError`;
nilai pada model yang berlaku 0,0129.

### Konsekuensi untuk firmware

```c
// masuk: hasil z-score (float) → int8
in[i] = (int8_t)lroundf(x[i] / ECG_IN_MORPH_SCALE + ECG_IN_MORPH_ZERO);
// keluar: int8 → probabilitas
float p = (out[0] - ECG_OUT_ZERO) * ECG_OUT_SCALE;
```

Angka `scale` dan `zero_point` ikut ter-*generate* di `model_int8.h` sebagai
makro `ECG_*_SCALE`/`ECG_*_ZERO` — jangan di-hardcode manual di firmware,
karena berubah tiap kali model dilatih ulang.

---

## 4b. Yang dikuantisasi bukan model latih, tapi varian deploy

```python
deploy = build_deploy_model(tf.keras.models.load_model(keras_path))
blob = quantize_int8(deploy, ...)
```

Model latih memakai `GlobalAveragePooling1D` → op `MEAN`, dan **TFLite Micro
menghitung `MEAN` berbeda dari TFLite biasa**. Di PC hasilnya 0,973; di ESP32-S3
model yang sama memberi 0,336 — tanpa error apa pun.

`build_deploy_model` menukar dua op, bobot disalin apa adanya (identik sampai
1,19e-07 di float32, jadi **tanpa latih ulang**):

| Model latih | Model deploy | Kenapa |
|---|---|---|
| `GlobalAveragePooling1D` (`MEAN`) | `DepthwiseConv1D(L)` bobot 1/L, L = panjang deret (32 pada window 256) | konvolusi = rata-rata yang sama, tapi dapat skala kuantisasi output sendiri |
| `Dense` | `Conv1D` kernel 1 | tetap 3-D → tidak butuh `Flatten` (yang memunculkan op shape-dinamis) |

Alternatif `AveragePooling1D` **tidak dipakai**: op pooling mewarisi skala
input (0,332), sedangkan rata-rata 31 nilai jauh lebih kecil dari rentang itu →
~3 bit resolusi terbuang dan recall DS2 jatuh 0,655 → 0,528 (terukur pada model
baseline berwindow 250, yang panjang deret di titik ini 31). Konvolusi mendapat
skala output sendiri (0,0429, sama persis dengan pilihan `MEAN`).
`build_deploy_model` mengambil panjang kernel dari bentuk tensor, jadi pada
window 256 yang berlaku kernelnya 32.

Cerita lengkap pengejaran bug ini: [`firmware-walkthrough`](firmware-walkthrough.md) §5.

---

## 5. `predict_tflite()` — jebakan ketiga: lupa dequantize

```python
inputs = sorted(interp.get_input_details(), key=lambda d: int(np.prod(d["shape"])))
rr_in, morph_in = inputs[0], inputs[1]
```

Urutan input di `.tflite` **tidak dijamin** sama dengan urutan di Keras (persis
masalah §3). Di sini dibereskan dengan mengurutkan berdasar **jumlah elemen**:
RR `(1,1,3)` = 3 elemen, morfologi `(1,256,1)` = 256 elemen. Jumlah dimensi
tidak bisa dipakai pembeda, karena di model deploy keduanya sama-sama 3-D.
Cara ini tidak bergantung nama maupun urutan.

Lalu kuantisasi manual masuk, dequantisasi manual keluar:

```python
np.clip(np.round(x / scale) + zero, -128, 127)     # masuk
(q.astype(np.float32) - zero) * scale              # keluar
```

`clip` wajib: nilai z-score bisa melewati rentang yang terlihat saat kalibrasi,
dan tanpa clip hasilnya *wrap around* — angka besar positif jadi negatif ekstrem.
Kalau langkah dequantize di output dilupakan, metrik dihitung dari bilangan
bulat −128..127 yang dibandingkan dengan threshold 0,80: setiap q ≥ 1 (p ≳ 0,5)
jadi Aritmia, sehingga titik operasi diam-diam pindah tanpa error apa pun (PRD
menyebut ini eksplisit: "lupa dequantize → metrik ngawur").

---

## 6. Tabel delta — hasil akhir

Ukuran: **23.488 byte = 22,94 KB** (< 25 KB), dari 25,07 KB float32.

| Metrik | Float32 | INT8 | Delta |
|---|---|---|---|
| accuracy | 0,9207 | 0,9198 | −0,0009 |
| precision | 0,6235 | 0,6169 | −0,0067 |
| **recall** | 0,6996 | 0,7105 | **+0,0108** |
| F1 | 0,6594 | 0,6604 | +0,0010 |
| specificity | 0,9479 | 0,9456 | −0,0023 |
| AUC | 0,9334 | 0,9344 | +0,0010 |
| TP/FN/FP/TN | 3813/1637/2302/41904 | 3872/1578/2405/41801 | — |

**|Delta recall| 1,08 poin** — di bawah ambang "ideal < 1–2%" yang disebut PRD.
Kelayakannya terbukti dengan angka, bukan asumsi.

### Cara membaca angka yang bergeser

Recall naik, precision dan specificity turun. Itu bukan bukti INT8 "lebih
peka". AUC bergeser +0,001 — kemampuan model mengurutkan praktis tidak berubah,
dan itulah ukuran yang jujur.

Yang terjadi: kuantisasi menggeser distribusi probabilitas sedikit. Dengan
threshold tetap 0,80, sebagian beat berpindah sisi: 59 aritmia tambahan
tertangkap (FN 1.637 → 1.578) dan 103 alarm palsu tambahan muncul (FP 2.302 →
2.405). Arah pergeseran ini tidak tetap: pada model baseline (window 250,
threshold 0,35) arahnya terbalik — recall −0,0112, precision +0,0383, AUC
−0,0004. Yang tetap adalah besarnya: kecil, dan AUC nyaris diam.

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
(|delta recall| 0,0108 < 0,02; 22,94 KB < 25 KB); QAT berarti melatih ulang dan
menambah satu sumber variasi baru untuk keuntungan yang belum tentu ada.

---

## 8. Cek pemahaman

1. `converter.representative_dataset` tidak diisi tapi `optimizations` diisi.
   Model tetap jadi dan lebih kecil — apa yang sebenarnya terkuantisasi, dan
   kenapa itu tidak cukup untuk ESP32?
2. Kenapa ada 16 tensor `int32` di model "full-INT8", dan kenapa itu bukan
   pelanggaran klaim?
3. `np.clip(..., -128, 127)` dihapus dari `_quantize`. Kapan bug-nya muncul, dan
   kenapa tidak muncul di sebagian besar beat?
4. Recall INT8 naik 1,1 poin dan precision turun 0,7 poin, sementara AUC hanya
   bergeser +0,001. Jelaskan kenapa fakta-fakta itu tidak bertentangan.

## 9. Skrip pendukung

| Perintah | Keluaran |
|---|---|
| `make quantize` | `model_int8.tflite`, `fase7_delta.csv`, `fase7_confusion_int8.png` |
| `make test` | seluruh suite pytest; 9 test di `tests/test_quantize.py` mengunci kalibrasi, klaim full-INT8, dan skala input ritme |

---

**[← Fase 6b — segmentasi deteksi](segmentasi-deteksi-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[firmware — port ke ESP32-S3 →](firmware-walkthrough.md)**
