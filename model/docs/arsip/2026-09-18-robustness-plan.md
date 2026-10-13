# Robustness terhadap error segmentasi — Rencana Adaptasi Dias 2021

> **Untuk pekerja agentik:** pakai `superpowers:executing-plans`. Langkah
> memakai checkbox (`- [ ]`).

**Sumber:** Dias et al., *Arrhythmia classification from single-lead ECG signals
using the inter-patient paradigm*, Comput Methods Programs Biomed 202 (2021)
105948. DOI 10.1016/j.cmpb.2021.105948.

**Goal:** Angka DS2 kita saat ini memakai posisi R dari anotasi yang sempurna,
sementara di alat posisi R datang dari Pan-Tompkins yang meleset. Selisih itu
belum pernah diukur, jadi metrik laporan **melebih-lebihkan** performa nyata.
Rencana ini menutup selisih tersebut: ukur jitter yang sebenarnya, latih dengan
jitter, laporkan metrik sebagai fungsi jitter.

**Bukan bagian dari rencana ini:** MQTT & resiliensi pipeline (dibuka oleh
Task 0), pergantian filter (§Ditolak).

---

## Keputusan: apa yang diadaptasi, apa yang tidak

| # | Usul paper | Keputusan | Alasan |
|---|---|---|---|
| 1 | Jitter ±δ pada posisi R, latih & evaluasi di bawahnya | **Adopsi** | kita punya detektor nyata; docs/segmentasi-deteksi §2 sudah menyarankan hal yang sama (augmentasi ±4) tanpa angka. Paper memberi protokolnya. |
| 2 | Fitur HOS (kurtosis, skewness) | **Uji (ablasi)** | sendirian payah (SeS 2,2%), tapi **datar terhadap jitter** — perannya penstabil, bukan pendorong. Ongkosnya 2 skalar. |
| 2b | Fitur RR: `ln()`, median ±15 beat, rerata record | **Uji, prioritas rendah** | kita sudah punya 3 fitur RR + jendela lokal 10 beat. `ln()` menolong LDA; untuk NN ber-input ter-z-score manfaatnya belum jelas. |
| 3 | Window 256 (128 pre / 127 post) | **Uji (ablasi), tidak diadopsi buta** | lihat analisis di bawah. |
| 4 | Buang kelas F & Q; window simetris | **Tidak** | beda definisi masalah (kita biner N vs Aritmia). Dicatat di laporan sebagai batas pembandingan, bukan diubah. |
| — | Filter: dua moving-average 200/600 ms | **Ditolak** | paper tidak pernah mengablasi filternya, jadi tak ada bukti ia lebih baik — hanya lebih murah. Kandidat perbaikan preprocessing yang berbukti ada di paper lain (denoising multi-tahap + deteksi artefak gerak), dan itu menjawab masalah nyata kita (rekaman badan berisik), bukan masalah MIT-BIH. |

### Soal ukuran window — kenapa tidak langsung ikut 256

Panjang totalnya nyaris sama: kita 250 sampel (694 ms), paper 256 (711 ms).
Yang berbeda **letak R di dalamnya**:

| | pre-R | post-R |
|---|---|---|
| kita | 90 sampel = 250 ms | 160 sampel = 444 ms |
| paper | 128 sampel = 355 ms | 127 sampel = 353 ms |

Interval PR normal 120–200 ms = 43–72 sampel, jadi `WIN_PRE = 90` **sudah**
memuat gelombang P dengan sisa. Tambahan 38 sampel milik paper membeli garis
dasar sebelum P, bukan informasi P yang kita belum punya. Sebaliknya di sisi
kanan: pada denyut lambat, T bisa melewati 353 ms — window paper memotongnya,
window kita tidak. T yang utuh itu justru pembeda beat ventrikular.

Satu hal yang memang lebih rapi di 256: stride total CNN = 8, dan 256 habis
dibagi 8 (250 tidak). Nilainya kecil, tapi gratis.

Kesimpulan: ada argumen fisiologis untuk mempertahankan 90/160 dan argumen
aritmetika untuk 128/127 — **diputuskan oleh eksperimen, bukan oleh paper.**
Kandidat ketiga yang layak ikut diuji: **112/144 (=256)**, ambil kelipatan 8
tanpa mengorbankan cakupan T.

### Soal golden reference

`golden_ref.h` itu **regression test**, bukan pagar desain: ia menjamin C dan
Python menghitung hal yang sama, bukan bahwa parameternya sudah optimal. Setiap
perubahan `config.py` yang diadopsi rencana ini **wajib** diikuti
`python scripts/export_golden.py` + `make export`. Regenerasi = prosedur rutin,
bukan pelanggaran.

---

## Task 0 — Buka jalan ke MQTT: sumber sinyal replay

Tidak ada kode baru. Sumbernya **sudah dirancang** di
`2026-09-16-daya-plan.md` **Task 4** (replay `golden_raw` di ISR, toggle serial
`y`, skala 1000 counts/mV + offset 2048). Itu persis "rekayasa data" yang
dibutuhkan: 2400 sampel record 208 diputar berulang = 8 beat (N, F, V) per
6,7 detik, ~72 bpm, tanpa elektroda, **deterministik**.

- [x] Kerjakan `2026-09-16-daya-plan.md` Task 4 (6 langkah, sudah tertulis penuh)
      — kode masuk, `pio run -e esp32-s3` SUCCESS (RAM 21,2%, Flash 6,6%)
- [x] Verifikasi DI BOARD (18 Sep 2026): 11 beat/putaran 6,67 dtk, pola identik,
      `sampel hilang 0`, antrean puncak 21/256. Satu bug ketemu di sini: float
      di ISR → panic `Coprocessor exception` detik 18,49. Diperbaiki.

Determinisme itulah yang membuat uji resiliensi bisa diukur: jumlah beat yang
*seharusnya* terkirim diketahui persis, jadi **beat hilang = beat seharusnya −
beat sampai di broker**. Tanpa itu, "resilien" cuma kesan.

**Tidak** membuat `ecg_sim.h` baru dulu. Tambah hanya kalau dashboard butuh
rekaman lebih panjang/beragam kelas — keputusan setelah MQTT jalan, bukan
sebelum.

---

## Task 1 — Ukur jitter yang sebenarnya (prasyarat semua task berikutnya)

Paper memakai δ seragam ±18 sampel karena mereka **tidak punya detektor** —
angka itu pinjaman dari literatur QRS detection. Kita punya detektornya. Jadi
jangan menyalin 18; ukur milik sendiri.

`docs/segmentasi-deteksi-walkthrough.md` §2 mencatat std 13 sampel, tapi itu
**sebelum** penghalusan puncak ±25 sampel dan koreksi group delay. Residu
setelah rantai penuh belum pernah diukur.

- [x] Buat `model/scripts/ukur_jitter.py`: untuk tiap record DS1, jalankan
      rantai penuh (PT → −offset → puncak ±25 → −group delay), pasangkan tiap R
      deteksi ke anotasi terdekat, kumpulkan residunya
- [x] Keluarkan: median, std, p5/p95, histogram ke `artifacts/metrics/jitter/`
- [x] Catat juga beat yang **tidak terdeteksi sama sekali** dan deteksi palsu —
      itu mode kegagalan yang tidak ditangkap model jitter mana pun

**Keluaran yang dipakai:** δ yang dipakai Task 2–3 = p95 residu (dibulatkan),
bukan 18. Kalau residu ternyata ≤4 sampel, jitter jadi murah dan rencana ini
menyusut — itu hasil yang bagus, bukan kegagalan.

---

## Task 2 — Jitter sebagai protokol evaluasi (tabel ala Tabel 3 paper)

Injeksi jitter cuma **satu titik**: `scripts/prep_beats.py::process_record`.
Posisi R yang sudah dijitter harus dipakai **seluruhnya** — window *dan* fitur
RR — karena detektor yang meleset merusak dua-duanya sekaligus. Label tetap
dari indeks anotasi asli.

```python
# process_record(), setelah load_record:
r_jit = jitter_r(r, delta, rng)          # <-- kamu yang tulis
idx     = valid_beat_indices(len(signal), r_jit)
windows = zscore_per_window(segment_beats(filtered, r_jit[idx]))
rr      = compute_rr_features(r_jit)[idx]
labels  = ...                            # tetap dari sym[idx] — anotasi asli
```

- [x] `jitter_r()` di `src/preprocessing.py` — DIKERJAKAN CLAUDE atas permintaan
      eksplisit ("gas sampai task 5"). Keputusan yang diambil ada di §3
      `docs/jitter-walkthrough.md`; ganti kalau tidak setuju, tesnya menjaga
      sifatnya bukan pilihannya.
      Keputusan yang ada di dalamnya, bukan salin-tempel:
      **(a)** sebaran seragam ±δ (ikut paper) atau normal(0, σ) dari Task 1
      (lebih setia ke detektor kita) — dua-duanya bisa dibela, pilih satu dan
      tulis alasannya; **(b)** jitter per-beat independen, atau berkorelasi
      antar-beat tetangga? Detektor nyata errornya **berkorelasi** (morfologi
      pasien menggeser semua beatnya ke arah sama) — independen itu asumsi
      optimis; **(c)** jaga urutan tetap menaik (δ ≪ RR minimum 72 sampel, jadi
      aman, tapi assert-nya murah)
- [x] `process_record(..., jitter=callable)` — TIDAK jadi argparse di dua skrip:
      `sweep_jitter.py` dan `ablasi.py` merakit di memori, jadi plumbing CLI +
      npz per varian tidak pernah dibutuhkan
- [x] Evaluasi **model yang sekarang** (tanpa latih ulang) di DS2 untuk
      δ = 0,2,4,…,18, 5 seed per δ → CSV + kurva
- [x] Tulis hasilnya ke `docs/jitter-walkthrough.md` §4

---

## Task 3 — Jitter sebagai augmentasi training

- [x] Latih ulang dengan jitter pada DS1 (δ dari Task 1; val ikut dijitter,
      DS2 **tidak** — DS2 dijitter hanya saat evaluasi Task 2)
- [x] Ukur model baru di DS2 anotasi DAN DS2 ber-jitter (`ablasi.py`)
- [x] Kalibrasi ulang threshold di val — tiap varian dapat threshold sendiri.
      Terbukti WAJIB: separuh kerusakan jitter itu titik operasi, bukan model
- [x] ~~Kriteria adopsi berbasis recall~~ → DIGANTI F1 + AUC (alasan: tiap varian
      punya threshold sendiri dari kalibrasi VAL, 0,40–0,85; membandingkan recall
      antar titik operasi berbeda itu membandingkan dua hal berbeda).
      Lihat changelog A5.

---

## Task 4 — Ablasi window (butuh Task 3 selesai supaya pembandingnya adil)

- [x] Latih 3 varian: `90/160` (sekarang), `128/127` (paper), `112/144` (256,
      cakupan T tetap) — semuanya **dengan** jitter dari Task 3
- [x] **HASIL (3 seed, rerata ± setengah-rentang, DS2 anotasi F1):**
      `bersih` 0,5660±0,0202 · `jitter` 0,6354±0,0428 · **`w128` 0,6775±0,0112**
      · `w112` 0,5786±0,0311 · `hos` 0,6150±0,0509. AUC `w128` 0,9394±0,0047.
      Tabel penuh + tafsirannya: `docs/jitter-walkthrough.md` §5.
      `w112` (panjang 256 yang sama) TIDAK ikut menang → yang membayar konteks
      pre-R, bukan panjang window.
- [x] Per-simbol: **recall S naik MONOTON dengan `WIN_PRE`** (90→0,268,
      112→0,369, 128→0,42-0,49), recall V tidak bergerak (0,91-0,94), recall F
      TURUN (0,308→0,15-0,20). Mekanismenya gelombang P + interval PR di sisi
      kiri window. Tabel di `jitter-walkthrough.md` §5.
- [x] Ongkos terukur di board: latensi 26,0 → **26,6 ms** (+2,3%), tensor arena
      12.756 → **12.948 B** (+1,5%), model INT8 22,91 → **22,94 KB**, param
      **tidak berubah** (6.417). Input +2,4% → ongkos +2,3%, kebetulan sepadan.
- [x] **Gate point dibuka user 18 Sep 2026**; regen golden + re-quantize +
      `make export` semuanya dijalankan.

---

## Task 5 — Ablasi HOS (murah, dikerjakan bareng Task 4)

Window kita sudah ter-z-score, jadi mean = 0 dan std = 1. Rumus paper
(Pers. 12–13) runtuh jadi dua momen mentah — itu sebabnya ongkosnya nyaris nol
di MCU, dan window-nya sudah ada di RAM saat itu.

- [x] `hos_features(windows)` di `src/features_rr.py` — DIKERJAKAN CLAUDE atas
      permintaan eksplisit; momen bias, kurtosis mentah (Pers. 12). Yang perlu kamu putuskan: momen bias atau unbiased
      (`ddof`), dan apakah kurtosis dilaporkan mentah atau dikurangi 3 (excess).
      Paper memakai bentuk mentah di Pers. 12.
- [x] Sambungkan sebagai 2 fitur tambahan ke cabang RR (3 → 5), `N_RR_FEATURES`
      jadi turunan lewat `PA_HOS`
- [x] Ablasi: HOS 0,6150±0,0509 vs 0,6354±0,0428 tanpa HOS — tumpang tindih
      penuh, **ditolak**. Kode & knob `PA_HOS` ditinggal untuk ablasi ulang.
- [x] Hipotesis Tabel 8 ("selisih membesar di δ tinggi") **tidak terbukti**:
      kolom anotasi (δ=0) dan jitter empiris sama-sama tumpang tindih penuh.
      Dibuang, sesuai kriteria yang ditulis di muka.

---

## Task 6 — Kunci & sebarkan

- [x] Kunci nilai yang menang di `config.py` — **18 Sep 2026, user setuju**:
      `WIN_PRE/WIN_POST 128/128`, `THRESHOLD 0,80`, `JITTER_MODEL empiris`,
      `JITTER_SALINAN 2`
- [x] `python scripts/export_golden.py` → regen `ecg_preproc.h` + `golden_ref.h`
      (golden jadi 9 beat, dulu 8)
- [x] `pio test -e native` → **17/17**; `test_preproc.cpp` diparametrisasi
      (`R_IDX = ECG_WIN_PRE + ECG_GROUP_DELAY`, dulu hafal 94)
- [x] `ecg_live.cpp` & `ecg_pipeline.cpp` sudah memakai konstanta header — nol
      perubahan dibutuhkan. Yang menghafal angka cuma test + komentar
- [x] `make quantize && make export` → INT8 22,94 KB, `model_int8.h` dgn
      `ECG_WIN_LEN 256` & `ECG_THRESHOLD 0.8f`; `pio run` SUCCESS
- [x] `docs/` diperbarui (`jitter-walkthrough`, `README`, `firmware-walkthrough`,
      `CLAUDE.md`, changelog). Tabel laporan menunggu — `laporan/` read-only.

---

## Status per 18 Sep 2026

**Task 0-6 SELESAI.** Rinciannya beserta semua penyimpangan dari rencana ini ada
di [`2026-09-18-robustness-changelog.md`](2026-09-18-robustness-changelog.md).

Hasil akhir di DS2: F1 **0,5659 → 0,6594**, AUC **0,8866 → 0,9334**, INT8
22,94 KB (delta recall +0,0108). Window dikunci ke **128/128 = 256** dan
threshold ke **0,80** setelah user menyetujui hasil ablasi.

Sisa: verifikasi replay + `pio test -e esp32-s3` di board (butuh hardware).

Temuan metodologis yang muncul di tengah jalan dan mengubah cara semua angka di
atas dibaca: **seed yang dikunci tidak mengunci hasil** (nondeterminisme oneDNN
di CPU). Semua klaim di atas dari 3 run, bukan 1.

---

## Urutan & ketergantungan

```
Task 0  (replay)  ────────────────► MQTT & resiliensi  (jalur terpisah, paralel)

Task 1 (ukur δ) → Task 2 (eval vs δ) → Task 3 (latih dgn jitter) → Task 4 (window)
                                                                 └► Task 5 (HOS)
                                                                        │
                                                                     Task 6
```

Task 0 tidak bergantung pada yang lain — kerjakan duluan supaya jalur MQTT
tidak menunggu. Task 1 murah dan bisa mengecilkan sisa rencana; jangan lompati.
