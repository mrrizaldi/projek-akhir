# Walkthrough `src/features_rr.py` — Fase 2

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 10–11. Lanjutan dari
[`preprocessing-walkthrough.md`](preprocessing-walkthrough.md) (Fase 1).

Semua angka di sini dari **record 100 utuh** (2273 beat, `fs = 360 Hz`).
Reproduksi:

```
cd model
.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
import numpy as np
from src.io_mitdb import load_record
from src.features_rr import compute_rr_features
sig, r, sym, fs = load_record('100')
print(compute_rr_features(r)[:5])
"
```

> File `src/features_rr.py` sengaja **tanpa komentar**. Penjelasannya ada di sini
> — kode dijaga sependek mungkin supaya gampang dibaca sebagai persamaan, dan
> supaya nanti tinggal diterjemahkan ke C untuk firmware.

---

## 0. Peta besar — di mana Fase 2 berdiri

Fase 1 menghasilkan **bentuk** (morfologi) tiap detak. Fase 2 menambahkan
**ritme**, lalu memberi tiap detak sebuah label.

```
 load_record()  →  signal, r_locations, symbols
        │                  │                │
        │ (Fase 1)         │ (Fase 2a)      │ (Fase 2b)
        ▼                  ▼                ▼
  bandpass → segment   compute_rr_       to_aami_class
  → z-score            features()        → to_binary_label
        │                  │                │
   windows [K,250]     rr [K,3]         labels [K]
        └──────────────────┴────────────────┘
                           │
                  valid_beat_indices()   ◄── prep_beats.py, BUKAN src/
                           │
                    data/processed/per_record/<rec>.npz
```

Model nanti menerima **dua input**: window morfologi 250 sampel dan vektor
ritme 3 angka. Dua-duanya wajib — PVC dan beat normal bisa mirip bentuknya,
yang membedakan justru kedatangannya yang prematur.

---

## 1. Dua tahap label — kenapa tidak langsung 0/1

```python
def to_aami_class(symbol: str) -> str:
    return AAMI_MAP[symbol]

def to_binary_label(aami_class: str) -> int:
    return int(aami_class in ARRHYTHMIA_SYMBOLS)
```

Tiga penyempitan berurutan:

```
anotasi wfdb   ~40 simbol   "N" "L" "V" "A" "+" "~" "|" ...
     │  load_record()  ← whitelist BEAT_SYMBOLS (INI yang memfilter)
     ▼
beat saja      15 simbol   "N" "L" "V" "A" ...
     │  to_aami_class()   ← memetakan, tidak membuang
     ▼
superclass AAMI  5 kelas   N  S  V  F  Q
     │  to_binary_label() ← mengerucutkan
     ▼
label biner      2 kelas   0 = Normal, 1 = Aritmia
```

`to_aami_class` **tidak membuang apa pun**. Satu simbol masuk, satu kelas keluar.
Penyaringan non-beat sudah selesai di `load_record`.

### `AAMI_MAP` itu tabel, bukan algoritma

```python
AAMI_MAP = {"N":"N", "L":"N", "R":"N", "e":"N", "j":"N",
            "A":"S", "a":"S", "J":"S", "S":"S",
            "V":"V", "E":"V", "F":"F",
            "/":"Q", "f":"Q", "Q":"Q"}
```

Aturannya hidup sebagai **data di `config.py`**, bukan sebagai rantai `if` di
`src/`. Mau ubah "L → S" nanti? Satu baris config, `src/` tak tersentuh.

**L & R (bundle branch block) → N** adalah keputusan yang terasa salah secara
klinis (LBBB jelas patologis) tapi benar secara metodologis: standar AAMI
EC57 dan de Chazal 2004 menaruhnya di N, dan seluruh literatur inter-patient
memakai konvensi itu. Kalau kita menyimpang, angka kita tidak bisa dibandingkan
dengan siapa pun.

### Kenapa `AAMI_MAP[symbol]`, bukan `.get(symbol, "Q")`

`.get` dengan default akan **diam-diam** melabeli simbol tak dikenal sebagai Q →
Aritmia. Bracket melempar `KeyError`. Kalau whitelist di hulu bocor, kamu tahu
saat itu juga — bukan di Fase 6 saat recall tiba-tiba aneh dan tidak ada
petunjuk kenapa.

### `int(... in ...)`

```python
"V" in {"V","S","F","Q"}   →  True   →  int(True) = 1
"N" in {"V","S","F","Q"}   →  False  →  int(False) = 0
```

`bool` itu subclass `int` di Python, jadi cast-nya no-op secara nilai. Gunanya
bikin `np.array(labels, dtype=np.int8)` di `prep_beats` tidak menghasilkan
`dtype=bool` yang bikin class-weight Fase 5 rewel.

**Asimetri yang perlu disadari:** keanggotaan dicek di `ARRHYTHMIA_SYMBOLS`,
jadi kelas tak dikenal jatuh ke 0 (Normal) diam-diam. Aman *hanya karena*
`to_aami_class` sudah melempar `KeyError` di hulu — dua fungsi ini selalu
dipanggil berpasangan.

---

## 2. `compute_rr_features()` — tiga angka ritme per detak

### 2.1 Kenapa RR, kenapa tiga

Interval RR = jarak waktu antar detak. Dari situ tiga fitur:

| Fitur | Rumus | Menangkap |
|---|---|---|
| `RR_prev` | $(r_i - r_{i-1}) / f_s$ | kecepatan absolut detak ini |
| `RR_ratio` | $\text{RR}_{\text{prev}} / \overline{\text{RR}}_{\text{lokal}}$ | prematur/terlambat **relatif ritme orang itu** |
| `dRR` | $\text{RR}_{\text{prev},i} - \text{RR}_{\text{prev},i-1}$ | perubahan — pola cepat-lalu-jeda khas PVC |

`RR_prev` sendirian tidak cukup: 0,6 detik itu normal untuk orang ber-HR 100,
tapi prematur untuk orang ber-HR 60. `RR_ratio` yang menormalkan ke ritme
pasien itu sendiri — **inilah fitur yang selamat menyeberangi split
inter-patient**, karena tidak membawa bias detak-dasar pasien latih.

### 2.2 Jalannya kode, baris per baris

```python
r = np.asarray(r_locations, dtype=np.float64)
m = len(r)
out = np.full((m, 3), np.nan, dtype=np.float64)
if m < 2:
    return out.astype(np.float32)
```

Kanvas NaN duluan. Baris yang tak sempat terisi **tetap NaN** — itu kontrak,
bukan kelalaian (§2.5). Record < 2 beat langsung pulang; tanpa guard ini
`np.diff` menghasilkan array kosong dan pembagian di bawah meledak.

```python
d = np.diff(r) / fs                      # [1.0, 2.0, 1.0]  detik
```

$M$ beat → $M-1$ interval. Pergeseran indeks yang harus dipegang erat:

$$d[i-1] \ \text{adalah}\ \text{RR}_{\text{prev}}\ \text{milik beat}\ i$$

Beat 0 tidak punya pendahulu — itu sebabnya `d` satu lebih pendek dari `r`.

```python
w = RR_LOCAL_WINDOW_BEATS                # 10
j = np.arange(m - 1)
start = np.maximum(0, j - w + 1)
csum = np.concatenate(([0.0], np.cumsum(d)))
local_avg = (csum[j + 1] - csum[start]) / (j + 1 - start)
```

Rata-rata **kausal** atas paling banyak 10 interval terakhir, termasuk interval
ini sendiri:

$$\overline{\text{RR}}_{\text{lokal}}[j] = \frac{1}{j - s + 1}\sum_{k=s}^{j} d[k],
\qquad s = \max(0,\ j - 9)$$

`np.cumsum` bikin **jumlah prefix**, jadi jumlah jendela berapa pun lebarnya
selesai dalam dua operasi: `csum[j+1] - csum[start]`. Nol di depan (`[0.0]`)
supaya `csum[0] = 0` dan rumusnya berlaku juga untuk `start = 0`.

```python
out[1:, 0] = d                           # RR_prev  → baris 1..M-1
out[1:, 1] = d / local_avg               # RR_ratio → baris 1..M-1
out[2:, 2] = np.diff(d)                  # dRR      → baris 2..M-1
return out.astype(np.float32)
```

`out[1:]` dan `out[2:]` itu penerjemahan langsung dari pergeseran indeks di
atas: RR_prev mulai ada di beat 1, dRR baru ada di beat 2 (butuh dua RR).

### 2.3 Contoh angka

```python
r = [0, 360, 1080, 1440]        # fs = 360
d = [1.0, 2.0, 1.0]             # detik
local_avg = [1.000, 1.500, 1.333]
```

| beat | RR_prev | RR_ratio | dRR | tafsir |
|---|---|---|---|---|
| 0 | NaN | NaN | NaN | tak ada pendahulu |
| 1 | 1.00 | 1.00 | NaN | belum ada RR pembanding |
| 2 | 2.00 | 1.33 | +1.00 | **jeda** — 33% lebih lambat dari ritme lokal |
| 3 | 1.00 | 0.75 | −1.00 | **prematur** — 25% lebih cepat |

Beat 2 & 3 berpasangan: itu tanda tangan ekstrasistol — satu detak datang cepat,
lalu jeda kompensasi.

### 2.4 Keputusan: jendela KAUSAL, menyusut di tepi

PRD menandai ini DECISION POINT. Pilihannya dua:

| | simetris (5 kiri + 5 kanan) | **kausal (10 kiri)** ← dipilih |
|---|---|---|
| Butuh beat masa depan | ya | tidak |
| Bisa jalan di ESP32 | harus tunda 5 beat (~4 detik) | langsung |
| Konsisten dengan Fase 1 | tidak (`sosfilt` kausal) | ya |
| Estimasi ritme | sedikit lebih halus | cukup |

Alasan yang menentukan sama dengan JEBAKAN #1 PRD: apa pun yang butuh masa depan
mustahil di device yang menerima sampel satu per satu, dan train/deploy mismatch
lebih mahal daripada rata-rata yang sedikit lebih kasar.

Di awal record jendela **menyusut**, bukan di-pad: beat ke-3 memakai rata-rata 3
interval yang benar-benar ada. Padding nol akan menciptakan interval palsu 0
detik yang menyeret `local_avg` ke bawah dan bikin `RR_ratio` meledak.

Di MCU nanti bentuk yang setara: ring buffer 10 `float` + `running_sum += baru −
terlama`. O(1) per beat, RAM 40 byte.

### 2.5 Keputusan: NaN, bukan 0

Beat 0 dan 1 tiap record tidak punya semua fitur. Diberi NaN, **bukan** 0.

`dRR = 0` itu nilai yang **sah dan sering** — artinya "ritme stabil", justru ciri
khas beat Normal. Kalau 0 juga dipakai sebagai penanda "tidak diketahui", model
belajar dari dua hal berbeda yang tampak identik. NaN tidak punya tafsir sah
apa pun, jadi aman sebagai sentinel.

Bonus: NaN adalah **detektor bug alignment gratis**. Kalau nanti `loss = nan` di
Fase 5, itu bukti langsung `valid_beat_indices` tidak membuang beat 0 & 1 —
bukan misteri yang harus diburu.

Biayanya: 2 beat per record × 44 record = **88 beat dari ~100.000**.

### 2.6 Yang sengaja TIDAK dilakukan

**Tidak ada normalisasi mean/std.** JEBAKAN #2 PRD: menghitung $\mu,\sigma$ dari
gabungan DS1+DS2 adalah kebocoran data — statistik test set merembes ke training.
Skala RR sudah $O(1)$ apa adanya (0,5–1,2 detik), jadi tidak ada yang perlu
diskalakan. Bandingkan dengan `zscore_per_window` di Fase 1: itu boleh karena
statistiknya dari **dalam window itu sendiri**, tidak butuh apa pun dari dataset.

**Tidak menyaring apa pun.** Fungsi mengembalikan `[M, 3]` sepanjang
`r_locations` utuh. Alasannya di §3.

---

## 3. Alignment — jebakan paling mahal di fase ini

Kontrak: **indeks baris == indeks beat**, selamanya. Pemanggil menulis

```python
rr = compute_rr_features(r)[idx]        # BENAR
rr = compute_rr_features(r[idx])        # SALAH
```

Bedanya halus tapi fatal. `r[idx]` memotong daftar R-peak duluan, jadi beat
pertama yang lolos kehilangan tetangga aslinya dan `RR_prev`-nya dihitung dari
beat yang salah — diam-diam, tanpa error.

### Kenapa penyaringan bukan di sini

Tiga syarat buang-beat berasal dari tiga tempat berbeda:

1. window muat di sinyal → milik `segment_beats` (Fase 1)
2. punya `RR_prev` → milik `compute_rr_features` (Fase 2)
3. punya `dRR` → milik `compute_rr_features` (Fase 2)

Kalau tiap fungsi membuang sendiri-sendiri, hasilnya **tiga himpunan berbeda
yang panjangnya bisa kebetulan sama**. `assert len(windows) == len(labels)`
akan LOLOS, loss turun mulus, dan baru ketahuan di Fase 6 saat recall ~0.

Simulasi record 100: 100% baris tergeser 1 beat, 68 label jadi salah simbol
padahal aritmia asli cuma 34 — tiap 1 aritmia merusak 2 baris.

Makanya semua kebijakan buang-beat dikumpulkan di satu fungsi,
`valid_beat_indices` di `scripts/prep_beats.py`, dan `src/` tetap murni:

```python
r = np.asarray(r_locations)
i = np.arange(len(r))
fits = (r - WIN_PRE >= 0) & (r + WIN_POST <= signal_len)
return i[fits & (i >= 2)]
```

Irisan (`&`), bukan gabungan. `i >= 2` menutup syarat RR_prev sekaligus dRR —
beat 2 pasti punya keduanya.

---

## 4. Angka record 100 (rujukan cepat)

```
beat            = 2273        baris NaN = 2  (beat 0 & 1)
simbol          = N:2239  A:33  V:1
label biner     = Normal 2239 (98,5%)   Aritmia 34 (1,5%)

           mean      std      min      max
RR_prev   0.7946   0.0488   0.5222   1.1306    detik
RR_ratio  0.9996   0.0502   0.6729   1.3967    tanpa satuan
dRR      -0.0000   0.0632  -0.3444   0.5944    detik
```

Dua pembacaan penting:

**Fiturnya memang memisahkan.** Median `RR_ratio`: Normal **1,0003** vs Aritmia
**0,7664**. Beat aritmia record 100 hampir semuanya `A` (atrial premature) —
datang ~23% lebih cepat dari ritme lokal, persis yang diharapkan.

**`dRR` mean $\approx$ 0 itu benar, bukan bug.** Beda maju yang dijumlahkan
sepanjang record selalu mendekati nol (teleskopik) — jantung tidak bisa terus
melambat selamanya. Yang informatif simpangannya, bukan reratanya.

**Ketimpangannya ekstrem (1,5%)** — dan itu wajar untuk MIT-BIH. Justru inilah
alasan Fase 5 memakai class weighting. Kalau distribusinya ternyata seimbang,
mapping label yang salah.

### Seluruh dataset (`make prep`)

```
44 record   100.619 beat   Normal 90.018 (89,5%)   Aritmia 10.601 (10,5%)
dibuang     114 beat = 88 (beat 0 & 1 tiap record) + 26 (window tak muat di tepi)
```

Rasio global 10,5% jauh lebih ramah daripada record 100 (1,5%) — record 100
kebetulan pasien yang tenang. Sebarannya sendiri liar: **212 → 0% aritmia**
(tidak menyumbang satu pun contoh positif), **232 → 77,7%** (mayoritas justru
aritmia). Inilah kenapa split harus per pasien: kalau 232 masuk train dan
212 masuk test, angkamu bicara soal dua penyakit berbeda.

---

## 5. Cek pemahaman

1. `RR_LOCAL_WINDOW_BEATS` diubah 10 → 3. Apa yang terjadi pada `RR_ratio` beat
   PVC yang muncul tepat setelah beat prematur lain? (Petunjuk: jendela pendek
   ikut tercemar beat abnormal.)
2. Kenapa `compute_rr_features` boleh dipanggil dengan `r` utuh yang mengandung
   beat yang nanti dibuang, tapi `segment_beats` tidak boleh?
3. Kalau NaN diganti 0 dan `valid_beat_indices` lupa membuang beat 0 & 1, gejala
   apa yang muncul di Fase 5 — dan kenapa itu lebih berbahaya daripada `loss = nan`?
4. Record 232 punya banyak beat `A` beruntun. Apa yang terjadi pada
   `local_avg`-nya, dan apakah `RR_ratio` masih bisa dipercaya di situ?

## 6. Skrip pendukung

| Perintah | Melihat apa |
|---|---|
| `make test` | 16 test — 7 di antaranya mengunci perilaku `features_rr` |
| `make prep` | Fase 2 end-to-end → 44 × `per_record/*.npz` + tabel distribusi |

---

**[← Fase 1 — preprocessing](preprocessing-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 2b — prep_beats →](prep-beats-walkthrough.md)**
