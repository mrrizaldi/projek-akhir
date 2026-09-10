# Walkthrough `src/io_mitdb.py` — Fase 0

Dokumen belajar, bukan spesifikasi. Spesifikasi resmi tetap
`PRD_Model_Aritmia_TinyML.pdf` hal. 5–6. Fase paling awal, dan fase yang
kesalahannya paling mahal — semua fase sesudahnya memakai keluarannya apa adanya.

Reproduksi:

```
cd model
make data                 # sekali: unduh MIT-BIH
make check                # kelengkapan .hea/.dat/.atr
make plot0 REC=114        # overlay R-peak anotasi
```

---

## 0. Kontraknya satu baris

```python
signal, r_locations, symbols, fs = load_record("100")
```

| Keluaran | Bentuk | Isi |
|---|---|---|
| `signal` | `[N] float32` | sinyal kanal MLII, dalam mV |
| `r_locations` | `[M] int64` | indeks sampel puncak R (anotasi kardiolog) |
| `symbols` | `list[str]`, len M | simbol MIT-BIH per beat |
| `fs` | `int` | sampling rate, dijamin 360 |

Record 100: `signal` 650.000 sampel (30 menit × 360 Hz), 2.273 beat.

Modul ini **murni**: tanpa `print`, tanpa plot, tanpa kode top-level. Itu yang
membuatnya bisa di-`import` di pytest tanpa ikut memuat record 30 menit.

---

## 1. Anatomi satu record MIT-BIH

Tiap record adalah tiga file dengan nama sama:

| File | Isi |
|---|---|
| `100.hea` | header teks: nama kanal, fs, jumlah sampel, gain |
| `100.dat` | sinyal biner dua kanal |
| `100.atr` | anotasi kardiolog: posisi sampel + simbol per beat |

```python
record = wfdb.rdrecord(path)        # .hea + .dat
annotation = wfdb.rdann(path, "atr")  # .atr
```

Anotasi itulah aset paling berharga dari MIT-BIH: dua kardiolog independen
menandai **tiap** detak selama 30 menit × 48 rekaman. Itu sebabnya dataset 1980-an
ini masih jadi standar sampai sekarang.

---

## 2. Dua gerbang yang gagal berisik

```python
if record.fs != FS:
    raise ValueError(f"record {record_id}: fs={record.fs}, harus {FS}")
if CHANNEL not in record.sig_name:
    raise ValueError(f"record {record_id}: kanal {CHANNEL} tidak ada, hanya {record.sig_name}")
```

**Kenapa `raise`, bukan `continue` atau resample diam-diam.** Kalau satu record
ber-`fs` berbeda lolos, seluruh fitur RR-nya salah skala (dibagi 360 padahal
seharusnya lain) dan tidak ada satu pun tanda di hilir. Kegagalan yang berisik di
awal jauh lebih murah daripada angka yang salah diam-diam di Fase 6.

Yang benar-benar tertangkap gerbang ini:

```
102 → ValueError: kanal MLII tidak ada, hanya ['V5', 'V2']
104 → ValueError: kanal MLII tidak ada, hanya ['V5', 'V2']
```

Dua record itu memang tidak punya MLII. Mereka juga ada di
`config.PACED_EXCLUDED` — jadi alasannya dua: **teknis** (tak punya kanal) dan
**metodologis** (pasien ber-pacemaker).

---

## 3. Jebakan urutan kanal — record 114

```python
channel = record.sig_name.index(CHANNEL)
signal = record.p_signal[:, channel].astype(np.float32)
```

Kelihatan sepele, dan justru di sini jebakannya. Hampir semua record MIT-BIH
menaruh MLII di kolom 0:

```
record 100 → sig_name = ['MLII', 'V5']    → MLII di index 0
record 114 → sig_name = ['V5', 'MLII']    → MLII di index 1  ←
```

`p_signal[:, 0]` akan bekerja mulus untuk 45 record dan **diam-diam mengambil
kanal yang salah** untuk 114. Sinyal V5 tetap terlihat seperti EKG normal di
plot; yang berubah cuma morfologi QRS — persis hal yang dipelajari model.

Karena itu kanal dicari **lewat nama**, tidak pernah lewat indeks tetap.
Verifikasinya: `make plot0 REC=114` — garis R-peak anotasi harus mendarat tepat
di puncak R, plus assert mekanis membandingkan hasil `load_record` dengan
`p_signal[:, 1]`.

---

## 4. Menyaring non-beat — dan kenapa `is_qrs` tidak boleh dipakai

File `.atr` tidak hanya berisi detak. Ada juga penanda peristiwa:

```python
symbols = np.asarray(annotation.symbol)
is_beat = np.isin(symbols, list(BEAT_SYMBOLS))
```

Yang benar-benar terbuang:

| Record | Anotasi mentah | Dibuang | Beat tersisa |
|---|---|---|---|
| 100 | 2.274 | `+`×1 | 2.273 → `{N: 2239, A: 33, V: 1}` |
| 114 | 1.890 | `+`×3, `~`×7, `\|`×1 | 1.879 → `{N: 1820, V: 43, A: 10, F: 4, J: 2}` |

Arti simbolnya: `+` perubahan ritme, `~` perubahan kualitas sinyal, `|` artefak
isolated QRS-like. Semuanya **peristiwa**, bukan detak — kalau ikut, mereka jadi
"beat" tanpa QRS di tengah window.

### JEBAKAN: `wfdb.io.annotation.is_qrs`

Cara yang tampak paling natural adalah memakai tabel bawaan wfdb:

```python
is_beat = [wfdb.io.annotation.is_qrs[s] for s in symbols]   # ← JANGAN
```

Gejalanya: `[`, `]`, `x`, `)` lolos sebagai "beat". Sebabnya tabel wfdb menandai
penanda **awal/akhir ventricular flutter** dan **non-conducted P-wave** sebagai
QRS — benar secara terminologi sinyal, salah untuk keperluan kita.

Solusinya **whitelist eksplisit**, bukan blacklist:

```python
BEAT_SYMBOLS = {"N","L","R","e","j", "A","a","J","S", "V","E", "F", "/","f","Q"}
```

15 simbol, persis yang punya kelas AAMI. Perbedaan whitelist vs blacklist di sini
menentukan: dengan blacklist, simbol yang tidak kamu antisipasi **lolos**; dengan
whitelist, simbol tak dikenal **ikut terbuang**. Untuk data medis, gagal ke arah
membuang jauh lebih aman.

Ini juga yang membuat `AAMI_MAP[symbol]` di Fase 2 boleh melempar `KeyError` —
apa pun yang sampai ke sana dijamin sudah ada di whitelist, jadi `KeyError`
berarti ada yang bocor di hulu.

---

## 5. Kenapa MLII, dan kenapa `float32`

**MLII** (modified limb lead II) adalah lead dengan kompleks QRS paling menonjol
pada mayoritas orang — sumbu jantung kira-kira sejajar dengannya. Praktisnya:
46 dari 48 record MIT-BIH punya MLII, dan alat sadap satu-lead seperti AD8232
di proyek ini juga memasang elektroda pada posisi yang mendekati lead II. Jadi
memilih MLII bukan cuma soal ketersediaan data — itu menjaga **kesamaan antara
data latih dan sinyal yang nanti benar-benar masuk ke ESP32**.

`astype(np.float32)`: `p_signal` bawaan wfdb float64. Separuh memori, dan sama
dengan presisi yang dipakai TFLite nanti. 650.000 sampel × 48 record: 250 MB vs
125 MB.

---

## 6. Angka rujukan

```
48 record lengkap (.hea + .dat + .atr)      → make check
record 100: 650.000 sampel, 2.273 beat, fs 360, kanal ['MLII', 'V5']
record 114: 650.000 sampel, 1.879 beat, fs 360, kanal ['V5', 'MLII']  ← MLII index 1
record 102 & 104: ValueError (tanpa MLII)
```

---

## 7. Cek pemahaman

1. `channel = 0` di-hardcode. Record mana yang rusak, dan kenapa bug itu **tidak**
   akan terlihat di grafik sinyal maupun di loss training?
2. Whitelist `BEAT_SYMBOLS` diganti blacklist `{"+", "~", "|"}`. Simbol apa yang
   lolos, dan apa akibatnya pada window yang tersegmentasi?
3. `fs` yang tidak cocok di-resample diam-diam, bukan di-`raise`. Fitur mana yang
   rusak, dan di fase berapa kamu baru akan menyadarinya?
4. Kenapa fungsi ini mengembalikan `symbols` mentah dan bukan langsung label
   biner? (Petunjuk: lihat pemakaian `symbols` di Fase 6.)

## 8. Skrip pendukung

| Perintah | Melihat apa |
|---|---|
| `make data` | Unduh 48 record MIT-BIH (sekali) |
| `make check` | Kelengkapan `.hea`/`.dat`/`.atr` tiap record |
| `make plot0 REC=n` | Overlay R-peak anotasi di sinyal — verifikasi kanal benar |

---

**—**  ·  [Peta walkthrough](README.md)  ·  **[Fase 1 — preprocessing →](preprocessing-walkthrough.md)**
