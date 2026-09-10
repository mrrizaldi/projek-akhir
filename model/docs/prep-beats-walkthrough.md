# Walkthrough `scripts/prep_beats.py` — Fase 2 (eksekusi)

Dokumen belajar, bukan spesifikasi. Pasangan dari
[`features-rr-walkthrough.md`](features-rr-walkthrough.md): kalau dokumen itu
membahas **rumusnya**, dokumen ini membahas **siapa yang menjalankan rumus itu
ke 44 record dan menjaga semuanya tetap sejajar**.

Reproduksi:

```
cd model
make prep       # 44 record → data/processed/per_record/*.npz
```

---

## 0. Kenapa file ini ada — dan kenapa dia di `scripts/`, bukan `src/`

`src/` berisi fungsi murni: masuk array, keluar array. Tidak ada satu pun dari
mereka yang tahu bahwa MIT-BIH punya 48 record, bahwa 4 di antaranya dibuang,
atau bahwa hasilnya disimpan sebagai `.npz`. Itu semua **kebijakan**, dan
kebijakan tinggal di sini.

```
        src/ (murni, calon port ke C)          scripts/ (eksekusi)
   ┌────────────────────────────────┐    ┌──────────────────────────┐
   │ load_record()                  │    │                          │
   │ apply_bandpass()               │◄───┤   prep_beats.py          │
   │ segment_beats()                │    │   - record mana dipakai  │
   │ zscore_per_window()            │    │   - beat mana dibuang    │
   │ compute_rr_features()          │    │   - tulis .npz, cetak    │
   │ to_aami_class/to_binary_label()│    │                          │
   └────────────────────────────────┘    └──────────────────────────┘
```

Pemisahan ini bukan soal kerapian. Fungsi di `src/` akan ditulis ulang di C
untuk ESP32; kalau `np.savez` dan `print` ikut bersarang di dalamnya, porting
jadi acara bongkar-pasang. Sebaliknya, dengan semua kebijakan buang-beat
terkumpul di satu fungsi di sini, pertanyaan "beat mana yang dipakai?" punya
**satu** jawaban yang bisa dibaca dalam 4 baris.

`prep_beats.py` juga **eksekusi produksi pertama Fase 1**. Sebelum ini,
`preprocessing.py` cuma dipanggil skrip plot untuk satu record. Di sinilah
filter benar-benar dijalankan ke 44 record.

---

## 1. `valid_beat_indices()` — satu-satunya sumber kebenaran alignment

```python
r = np.asarray(r_locations)
i = np.arange(len(r))
fits = (r - WIN_PRE >= 0) & (r + WIN_POST <= signal_len)
return i[fits & (i >= 2)]
```

Tiga syarat, **irisan** (`&`), bukan gabungan:

| Syarat | Asal | Alasan |
|---|---|---|
| `r - 90 >= 0` dan `r + 160 <= N` | Fase 1 | window 250 sampel harus muat di sinyal |
| `i >= 1` | Fase 2 | butuh `r[i-1]` untuk RR_prev |
| `i >= 2` | Fase 2 | butuh RR_prev beat sebelumnya untuk dRR |

Dua syarat terakhir dipadatkan jadi `i >= 2` — beat ke-2 otomatis punya keduanya.

Yang dikembalikan **indeks beat**, bukan array data. Itu intinya: satu daftar
indeks dipakai untuk memotong `windows`, `rr`, `labels`, dan `symbols` sekaligus,
jadi keempatnya mustahil bergeser satu sama lain.

### Kenapa bukan "samakan saja panjangnya"

Ini jebakan termahal di seluruh proyek, dan gejalanya **tidak ada**:

```python
labels = labels[:len(windows)]     # ← assert panjang LOLOS, data rusak
```

`segment_beats` membuang beat tepi; `compute_rr_features` tidak bisa mengisi
beat 0 & 1. Dua himpunan **berbeda** yang panjangnya bisa kebetulan sama.
Simulasi di record 100: 100% baris tergeser satu beat, 68 label jadi salah
simbol — padahal aritmia asli di record itu cuma 34 (tiap 1 aritmia merusak 2
baris). Loss tetap turun mulus. Baru ketahuan di Fase 6 saat recall ~0, tanpa
petunjuk apa pun tentang penyebabnya.

Sejajarkan lewat **indeks**, jangan pernah lewat panjang.

---

## 2. `process_record()` — urutannya menentukan benar/rusak

```python
signal, r, sym, _ = load_record(record_id)
filtered = apply_bandpass(signal, sos)

idx = valid_beat_indices(len(signal), r)
windows = zscore_per_window(segment_beats(filtered, r[idx]))
rr = compute_rr_features(r)[idx]
labels = np.array([to_binary_label(to_aami_class(sym[i])) for i in idx], dtype=np.int8)
symbols = np.array([sym[i] for i in idx], dtype="<U2")
```

Perhatikan baris `rr`. Dua bentuk yang terlihat setara:

```python
rr = compute_rr_features(r)[idx]     # ✓ BENAR — hitung dari r UTUH, baru potong
rr = compute_rr_features(r[idx])     # ✗ SALAH — potong dulu, baru hitung
```

Bedanya: `RR_prev` beat `idx[0]` butuh posisi beat **sebelumnya**, yang justru
sudah dibuang dari `idx`. Kalau `r` dipotong duluan, beat pertama yang lolos
menghitung intervalnya dari tetangga yang salah — dan hasilnya tetap angka yang
masuk akal, tidak ada error, tidak ada NaN.

Bandingkan dengan baris `windows`: di situ `r[idx]` justru **benar**, karena
`segment_beats` memotong sinyal di sekitar tiap R-peak secara independen — tidak
butuh tetangga. Aturannya: **fungsi yang butuh konteks tetangga selalu diberi
data utuh; penyaringan dilakukan setelahnya.**

### Dua assert yang menjaga kontrak

```python
assert len(windows) == len(rr) == len(labels) == len(symbols) == len(idx)
assert not np.isnan(rr).any(), f"record {record_id}: NaN lolos ke rr"
```

Yang kedua adalah jaring pengaman kedua. NaN dari beat 0 & 1 seharusnya sudah
tersaring `idx`; kalau lolos, artinya `valid_beat_indices` dan
`compute_rr_features` **tidak sepakat** soal beat mana yang valid. Ketahuan di
`make prep` yang jalannya semenit, bukan di Fase 5 saat `loss = nan` tanpa jejak.

---

## 3. Anatomi keluaran

```python
{"windows": [K,250] float32,   # morfologi ter-z-score
 "rr":      [K,3]   float32,   # RR_prev, RR_ratio, dRR
 "labels":  [K]     int8,      # 0 Normal / 1 Aritmia
 "symbols": [K]     <U2,       # simbol MIT-BIH asli
 "n_dropped":       int32}     # berapa beat dibuang
```

Dua field terakhir tidak dipakai model — dan justru itu gunanya.

**`symbols`** menyimpan informasi yang **hilang permanen** begitu label
dikerucutkan jadi 0/1. Di Fase 6 dialah yang memungkinkan tabel recall per kelas
AAMI (V 0,9332 / S 0,3034 / F 0,1675) — temuan paling berisi di Bab 4-mu. Tanpa
disimpan sekarang, tidak bisa direkonstruksi nanti.

**`n_dropped`** masuk `.npz`, bukan sekadar di-`print`. Angka "dari 100.619 beat,
114 dibuang karena ..." adalah baris tabel di laporan; kalau cuma dicetak, dia
hilang saat terminal ditutup.

---

## 4. `available_records()` dan `main()` — lapisan kebijakan

```python
excluded = {str(x) for x in PACED_EXCLUDED}
ids = sorted(f[:-4] for f in os.listdir(raw_dir) if f.endswith(".hea"))
return [i for i in ids if i not in excluded]
```

Daftar record datang dari **isi folder**, bukan dari daftar yang diketik ulang —
satu tempat lebih sedikit untuk salah ketik. `PACED_EXCLUDED` diambil dari
`config.py`, daftar yang sama yang dipakai Fase 3. Satu sumber, jangan
digandakan.

`main()` mencetak tabel per record lalu total. Cetakan itu bukan hiasan: PRD
mensyaratkan distribusi label dicetak per record sebagai DoD, dan ketimpangan
yang terlihat di situ adalah yang membenarkan `class_weight` di Fase 5.

---

## 5. Angka nyata — dan apa yang bisa dibaca darinya

```
44 record  100.619 beat  Normal 90.018 (89,5%)  Aritmia 10.601 (10,5%)  buang 114
```

### Pembukuan 114 beat yang dibuang

```
sebaran per record: {3 beat: 26 record, 2 beat: 18 record}
114 = 44×2 (beat 0 & 1, deterministik) + 26 (beat tepi)
```

Semua 26 beat tepi itu ada di **akhir** rekaman: R-peak terakhir jatuh setelah
sampel 649.840, sehingga jendela `+160` tidak muat di 650.000 sampel.

```
rec 103  r[-1] = 649.875  (butuh <= 649.840)  → dibuang
rec 113  r[-1] = 649.994  (butuh <= 649.840)  → dibuang
rec 223  r[-1] = 649.849  (butuh <= 649.840)  → dibuang, cuma lewat 9 sampel
```

### Yang menarik: beat awal tidak pernah menambah hitungan

Beberapa record punya R-peak pertama terlalu dekat ke awal sinyal:

```
rec 220  r[0] = 28   (butuh >= 90)
rec 208  r[0] = 46
rec 100  r[0] = 77
```

Beat-beat itu **memang** gagal syarat window — tapi mereka sudah dibuang duluan
oleh syarat `i >= 2`. Karena `valid_beat_indices` memakai **irisan**, satu beat
yang gagal dua syarat tetap dihitung sekali.

Ini kenapa angkanya bisa serapi 44×2 + 26. Kalau ada kode lain yang diam-diam
ikut membuang beat, pembukuan sesederhana ini tidak akan cocok — jadi angka
114 itu sendiri berfungsi sebagai bukti bahwa kebijakan buang-beat benar-benar
terpusat di satu tempat.

### Sebaran kelas per record itu ekstrem

```
rec 212 → 0,0% aritmia        rec 232 → 77,7% aritmia
rec 230 → 0,0%                rec 208 → 46,3%
```

Ketimpangan global 10,5% menyembunyikan kenyataan bahwa tiap pasien adalah
distribusi yang berbeda. Ini pembenaran langsung untuk keputusan Fase 3 (split
per pasien) — dan penjelasan kenapa metrik DS2 nanti didominasi satu-dua pasien.

---

## 6. Yang sengaja TIDAK dilakukan

**Tidak menggabungkan jadi satu file besar.** Keluaran tetap 44 `.npz` terpisah.
Fase 3 membelah per pasien, jadi selama data masih per record, split itu cuma
soal memilih file. Lihat [dataset-walkthrough](dataset-walkthrough.md) §0.

**Tidak mengacak apa pun.** Urutan beat mengikuti urutan waktu di rekaman.
Pengacakan adalah urusan training, di memori, per epoch.

**Tidak melewati record yang gagal dibaca.** `load_record` melempar `ValueError`
untuk record tanpa MLII — dan record itu memang sudah ada di `PACED_EXCLUDED`,
jadi tidak pernah sampai ke sini. Kalau suatu saat sampai, program berhenti,
bukan menghasilkan dataset yang diam-diam lebih kecil.

---

## 7. Cek pemahaman

1. Baris `rr` diubah jadi `compute_rr_features(r[idx])`. Berapa banyak baris yang
   nilainya salah, dan kenapa test `assert len(...)` tetap lolos?
2. `valid_beat_indices` diubah dari irisan (`&`) jadi gabungan (`|`). Berapa beat
   yang lolos di record 100, dan apa yang terjadi saat `compute_rr_features`
   di-slice dengan indeks itu?
3. Record 223 punya `r[-1] = 649.849`, cuma 9 sampel melewati batas. Kalau
   `WIN_POST` diturunkan 160 → 150, berapa total beat yang terselamatkan di 44
   record, dan bagian gelombang apa yang hilang dari window?
4. `symbols` tidak disimpan ke `.npz`. Tabel apa di Bab 4 yang jadi mustahil
   dibuat, dan kenapa tidak bisa direkonstruksi dari `labels`?

## 8. Skrip pendukung

| Perintah | Melihat apa |
|---|---|
| `make prep` | Jalankan 44 record + tabel distribusi label per record |
| `make plot1seg REC=n` | Window hasil segmentasi + z-score, verifikasi visual |
| `make test` | 4 test `tests/test_prep_beats.py` mengunci kontrak alignment |

---

**[← Fase 2 — features_rr](features-rr-walkthrough.md)**  ·  [Peta walkthrough](README.md)  ·  **[Fase 3 — dataset →](dataset-walkthrough.md)**
