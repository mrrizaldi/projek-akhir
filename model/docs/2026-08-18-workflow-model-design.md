# Desain Workflow & Kontrak Antar-Fase — model/

Tanggal: 2026-08-18
Status: disetujui (hasil brainstorming), belum diimplementasikan
Acuan: `../PRD_Model_Aritmia_TinyML.pdf` (19 hal, Fase 0–8)

Dokumen ini TIDAK mengubah metodologi PRD. PRD sudah mengunci arsitektur,
split, dan semua decision point ilmiah (lihat LAMPIRAN B PRD). Yang dirancang
di sini hanya **cara kerjanya ditata**: peran file, cara verifikasi, bentuk
artefak antar-fase, orkestrasi, dan tempat mendaratkan keputusan.

---

## 1. Struktur & peran file

Aturan pemisah: **kalau file menghasilkan efek (menulis file, memunculkan plot,
mencetak angka), tempatnya `scripts/`. `src/` hanya menerima dan mengembalikan
data.**

```
model/
├── CLAUDE.md          BARU — aturan kerja + status/hasil tiap fase
├── config.py          lengkapi: AAMI_MAP, DS1, DS2, PACED_EXCLUDED
├── Makefile           isi target yang sekarang masih echo
├── docs/              dokumen desain (file ini)
├── src/               MODUL — import-safe, tanpa kode top-level
│   ├── io_mitdb.py        load_record()                           (Fase 0)
│   ├── preprocessing.py   design_bandpass_sos, apply_bandpass,
│   │                      pan_tompkins_detect, segment_beats,
│   │                      zscore_per_window                       (Fase 1)
│   ├── features_rr.py     to_binary_label, compute_rr_features    (Fase 2)
│   ├── dataset.py         build_split()                           (Fase 3)
│   ├── model.py           build_hybrid_model()                    (Fase 4)
│   ├── train.py           make_class_weights, train()             (Fase 5)
│   ├── evaluate.py        evaluate_fp32()                         (Fase 6)
│   └── quantize.py        representative_dataset_gen,
│                          quantize_int8, evaluate_int8            (Fase 7)
├── scripts/           EKSEKUSI — boleh cetak, plot, tulis file
│   ├── download_data.py    wfdb.dl_database (sekali jalan)
│   ├── check_dataset.py    (sudah ada)
│   ├── plot_fase0.py       overlay R-peak      <- isi io_mitdb.py lama pindah ke sini
│   ├── plot_fase1.py       raw vs bandpass; 5 window N vs 5 window V
│   ├── prep_beats.py       Fase 2 -> per_record/*.npz
│   ├── build_split.py      Fase 3 -> train.npz + test.npz
│   ├── train_model.py      Fase 5 -> artifacts/model_fp32.keras + kurva
│   ├── eval_fp32.py        Fase 6 -> confusion matrix + tabel metrik
│   └── quantize_int8.py    Fase 7 -> model_int8.tflite + tabel delta
├── tests/             assert DoD yang berupa angka (pytest)
├── data/processed/
│   ├── per_record/*.npz
│   ├── train.npz
│   └── test.npz
└── artifacts/         model_fp32.keras, model_int8.tflite, metrics/
```

Konsekuensi: training/evaluasi/kuantisasi juga eksekusi. `src/train.py` berisi
fungsi `train(...)` yang menerima model + data dan mengembalikan history; yang
menyimpan `.keras` dan menulis kurva adalah `scripts/train_model.py`. Pola sama
untuk Fase 6 dan 7.

### Rasional

Kode di level teratas sebuah file Python dieksekusi saat **import**, bukan hanya
saat dijalankan. `src/io_mitdb.py` saat ini memuat record, membuat plot, dan
menulis PNG di level teratas — begitu Fase 1 menulis
`from io_mitdb import load_record`, semua itu ikut jalan.

Tiga akibat yang menyentuh klaim PA:

1. **Reproducibility (DoD Fase 8).** Efek samping saat import membuat hasil
   bergantung pada urutan import dan state file di disk.
2. **Golden reference (Fase 1).** Yang bisa ditiru identik di C adalah fungsi
   murni (masuk array, keluar array). `sosfilt(sos, signal)` punya padanan
   biquad di C; `plt.savefig` tidak. Pemisahan menjaga batas "mana yang di-port"
   tetap tegas.
3. **Testability.** DoD seperti "window persis 250" hanya bisa di-assert kalau
   fungsinya bisa dipanggil tanpa menyeret pemuatan record 30 menit.

Alternatif ditolak: `if __name__ == "__main__":` di tiap file `src/`. Aman dari
efek samping, tapi blok itu cenderung tumbuh dan menggemukkan file yang justru
harus tetap ramping sebagai acuan porting C.

---

## 2. Verifikasi: assert otomatis + plot manual

DoD di PRD ada dua jenis dan tidak bisa saling menggantikan.

**Otomatis (pytest, `tests/`)** — pernyataan benar/salah tanpa tafsir:

| Assert | Fase | Kenapa penting |
|---|---|---|
| `fs == 360` | 0 | salah kanal/record ketahuan sejak awal |
| `windows.shape[1] == 250` | 1 | menutup jebakan "±250 -> 500 total" |
| `mean(w) ~ 0`, `std(w) ~ 1` per window | 1 | membuktikan z-score per-window, bukan global (anti kebocoran statistik) |
| `apply_bandpass` memakai `sosfilt` | 1 | JEBAKAN #1 PRD (kausal, bukan `filtfilt`) |
| `set(DS1) & set(DS2) == set()` | 3 | **bukti mekanis tidak ada kebocoran antar-pasien** |
| `set(DS1|DS2) & set(PACED) == set()`, total 48 | 3 | paced record benar-benar dibuang |
| `count_params() ~ 6000` | 4 | menangkap Flatten/Dense kegedean tanpa sadar |
| `len(windows) == len(rr) == len(labels)` | 2 | array sejajar (DoD Fase 2) |

**Manual (plot via `scripts/`)** — butuh mata manusia: baseline wander hilang
tapi bentuk QRS tetap; 5 window N mirip; window V terlihat lebar tanpa P;
overlay R-peak mendarat pas di puncak.

Kualitas deteksi Pan-Tompkins TIDAK dijadikan unit test — ground truth-nya
anotasi MIT-BIH, dan itu sudah jadi benchmark deteksi terpisah di Fase 1.2.

Assert menjawab "apakah masih benar setelah aku ubah sesuatu"; plot menjawab
"apakah benar sekarang". Keduanya diperlukan karena `config.py` akan disentuh
lagi setelah Fase 5.

Keputusan: pakai **pytest** (ditambahkan ke `requirements.txt` — dependency baru
yang disetujui sadar, 2026-08-18).

---

## 3. Kontrak artefak `.npz`

Nama key dikunci di sini. Salah ketik nama key baru ketahuan satu fase kemudian.

### `data/processed/per_record/<rec>.npz` — produsen Fase 2 (`prep_beats.py`)

| key | dtype | shape | isi |
|---|---|---|---|
| `windows` | float32 | `[K, 250]` | window ter-z-score; K = beat valid |
| `rr` | float32 | `[K, 3]` | RR_prev, RR_ratio, dRR |
| `labels` | int8 | `[K]` | 0 = Normal, 1 = Aritmia |
| `symbols` | `<U2` | `[K]` | simbol MIT-BIH asli, untuk audit |
| `n_dropped` | int32 | skalar | beat dibuang (window keluar batas / tanpa RR_prev) |

### `data/processed/train.npz` & `test.npz` — produsen Fase 3 (`build_split.py`)

| key | dtype | shape | isi |
|---|---|---|---|
| `X_morph` | float32 | `[N, 250, 1]` | channel dim sudah ditambah untuk Conv1D |
| `X_rr` | float32 | `[N, 3]` | |
| `y` | int8 | `[N]` | |
| `records` | int32 | `[N]` | asal record tiap beat |

### Rasional

- **Per-record wajib**: DoD Fase 2 menuntut distribusi label dicetak per record;
  itu cara menemukan record bermasalah. Rerun satu record jadi murah.
  Struktur per-record juga mencerminkan struktur klaim: satuan pemisah split
  adalah record, dan penggabungan hanya terjadi di satu tempat
  (`build_split.py`, membaca DS1/DS2 dari config).
- **Gabungan juga disimpan**: training dijalankan berkali-kali; menggabung 22
  file tiap kali adalah kerja berulang. `test.npz` juga menjadi titik beku —
  "DS2 tidak disentuh" jadi sesuatu yang bisa ditunjukkan.
- **`symbols`** (di luar PRD): menjawab "beat yang salah klasifikasi itu simbol
  aslinya apa (V/S/F/Q)?" saat analisis error.
- **`records`** (di luar PRD): memungkinkan metrik per-record kalau pembimbing
  meminta (PRD Fase 6 menyebut kemungkinan ini). Murah sekarang, mahal nanti.
- **`n_dropped`**: DoD Fase 1 menuntut beat out-of-bound terbuang DAN tercatat.

Harga yang dibayar: duplikasi data di disk, dan risiko file gabungan basi.
Mitigasi ada di bagian 4 (dependensi Makefile).

---

## 4. Orkestrasi: Makefile

```make
PY := python

.PHONY: data check prep split train eval quantize export test plot0 plot1 clean

## Fase 0 — data
data:  ; $(PY) scripts/download_data.py
check: ; $(PY) scripts/check_dataset.py
plot0: ; $(PY) scripts/plot_fase0.py 100     # verifikasi overlay R-peak
plot1: ; $(PY) scripts/plot_fase1.py 100     # verifikasi filter + window

## Fase 2 — beat, label, fitur RR
data/processed/per_record/.stamp: config.py src/preprocessing.py src/features_rr.py
	$(PY) scripts/prep_beats.py && touch $@
prep: data/processed/per_record/.stamp

## Fase 3 — split inter-patient
data/processed/train.npz: data/processed/per_record/.stamp config.py src/dataset.py
	$(PY) scripts/build_split.py
split: data/processed/train.npz

## Fase 5-7
train:    data/processed/train.npz ; $(PY) scripts/train_model.py
eval:     ; $(PY) scripts/eval_fp32.py
quantize: ; $(PY) scripts/quantize_int8.py
export:   ; bash ../scripts/export_artifacts.sh

test: ; pytest tests/ -q
clean: ; rm -rf data/processed artifacts/metrics/*.png artifacts/metrics/*.csv
```

Dua hal disengaja:

- **`.stamp` dan `train.npz` target file, bukan `.PHONY`.** Memberi penjagaan
  urutan: `make train` membangun ulang split kalau `config.py` atau
  `src/dataset.py` berubah setelah split terakhir dibuat. Tidak bisa melatih
  dari data basi tanpa sadar.
- **`clean` tidak menghapus `data/raw/` dan `artifacts/*.keras`/`*.tflite`.**
  Hanya membuang yang murah dibuat ulang.

Alternatif ditolak: CLI tunggal (`run.py --fase N`) — menduplikasi peran
Makefile yang sudah berdiri dan sudah dijanjikan di README + CLAUDE.md root.

---

## 5. `model/CLAUDE.md` sebagai logbook

Sesi Claude Code di `model/` TIDAK mewarisi riwayat sesi di root repo (riwayat
disimpan per direktori kerja). Yang selalu ikut termuat hanyalah CLAUDE.md dari
cwd naik ke parent. Jadi file ini rangkap fungsi: catatan keputusan untuk
penulis, sekaligus satu-satunya kanal knowledge lintas sesi.

Kerangka:

```markdown
# CLAUDE.md — model/ (jalur TinyML)

Spesifikasi lengkap: PRD_Model_Aritmia_TinyML.pdf (19 hal). Baca fase terkait
sebelum menyentuh file apa pun. Jangan vibe-coding.

## Aturan
1. USER yang menulis logika algoritma. Claude: scaffolding, review, debug, docs.
2. src/ = modul MURNI (fungsi in->out, tanpa kode top-level, import-safe).
   scripts/ = eksekusi (cetak, plot, tulis file). Jangan campur.
3. Semua konstanta di config.py. Jangan hardcode angka di src/.
4. DS2 haram disentuh sebelum Fase 6. Bukan validation, bukan tuning threshold.
5. sosfilt, BUKAN filtfilt (kausal — JEBAKAN #1 PRD).

## Status fase
- [x] Fase 0 — <angka DoD>
- [ ] Fase 1 — ...
  (maks ~5 baris/fase: angka DoD, keputusan di-lock, jebakan ketemu)

## Decision point yang sudah di-lock
| Keputusan | Nilai | Alasan singkat |
|---|---|---|
| Orde Butterworth | ? | ... |
| Strategi imbalance | ? | ... |
| Dropout Dense 16 | ? | ... |
| Threshold | 0,5 | dikalibrasi di DS1/val, bukan DS2 |
| Tipe I/O INT8 | ? | konsisten dengan rencana firmware |

## Kanal knowledge
Sesi Claude di folder ini TIDAK mewarisi riwayat sesi lain. File ini
satu-satunya yang selalu termuat — tulis keputusan ke sini, bukan ke chat.
```

Disiplin: **maksimal ~5 baris per fase.** File ini dimuat utuh tiap sesi, jadi
naratif panjang dibayar berulang kali. Naratif lengkapnya langsung ke Bab 4
laporan.

Tabel decision point sengaja sebentuk dengan LAMPIRAN B PRD supaya bisa
dipindahkan langsung saat menyusun Bab 4 dan menyiapkan sidang.

---

## 6. Perubahan pendukung

- `requirements.txt`: tambah `pytest`.
- `.gitignore` root: pola `model/data/processed/*.npz` TIDAK menangkap
  subfolder. Ubah jadi `model/data/processed/`.
- `config.py`: lengkapi `AAMI_MAP`, `DS1`, `DS2`, `PACED_EXCLUDED`.
  Daftar DS1/DS2 adalah **gated decision** — cross-check ke de Chazal 2004
  sebelum dipakai (perintah PRD Fase 3).
- `src/io_mitdb.py`: isi eksplorasi sekarang dipindah ke `scripts/plot_fase0.py`;
  file diisi kontrak `load_record()`. Pemindahan menunggu persetujuan (aturan
  non-destruktif repo).

## 7. Yang TIDAK dicakup

- Logika algoritma apa pun (ditulis manual oleh user — aturan repo #1).
- Metodologi PRD (sudah terkunci, tidak dibahas ulang di sini).
- Jalur firmware/pipeline (LAMPIRAN C PRD, butuh hardware).
