# CLAUDE.md — model/ (jalur TinyML)

Spesifikasi lengkap: `PRD_Model_Aritmia_TinyML.pdf` (19 hal, Fase 0–8).
Baca fase terkait sebelum menyentuh file apa pun. Jangan vibe-coding.
Desain workflow: `docs/2026-08-18-workflow-model-design.md`.

## Aturan

1. **USER yang menulis logika algoritma.** Claude: scaffolding, review, debug,
   docs, build glue. Jangan isi `src/*.py` kecuali diminta eksplisit.
2. **`src/` = modul MURNI** (fungsi in→out, tanpa kode top-level, import-safe).
   **`scripts/` = eksekusi** (cetak, plot, tulis file). Jangan campur.
3. **Semua konstanta di `config.py`.** Jangan hardcode angka di `src/`.
4. **DS2 haram disentuh sebelum Fase 6.** Bukan validation, bukan tuning
   threshold. Sekali sentuh di Fase 6–7, itu saja.
5. **`sosfilt`, BUKAN `filtfilt`** (kausal — JEBAKAN #1 PRD). `filtfilt` mustahil
   real-time di MCU → train/deploy mismatch.
6. **Segmentasi training pakai R-peak dari ANOTASI**, bukan Pan-Tompkins
   (keputusan terkunci, PRD Fase 2).

## Perintah

```
make data      # download MIT-BIH (sekali)      make train     # Fase 5
make check     # cek kelengkapan dataset        make eval      # Fase 6
make plot0     # verifikasi Fase 0 (R-peak)     make quantize  # Fase 7
make plot1     # verifikasi Fase 1 (filter)     make export    # .h ke firmware
make prep      # Fase 2 → per_record/*.npz      make test      # pytest
make split     # Fase 3 → train/test.npz
```

## Status fase

Maksimal ~5 baris per fase: angka DoD, keputusan di-lock, jebakan ketemu.
Naratif panjang → langsung ke Bab 4 laporan, jangan di sini.

- [x] **Fase 0** — 48 record lengkap. Rec 100 → 650.000 sampel, 2.273 beat,
  `fs == 360`, simbol tersisa `{A, N, V}`. Rec 114 (MLII index 1): garis mendarat
  pas di puncak R (`make plot0 REC=114`) + di-assert mekanis vs `p_signal[:, 1]`.
  Rec 102/104 (tanpa MLII) ditolak `ValueError`. `make test` → 9 passed.
- [ ] **Fase 1** — preprocessing (golden reference)
- [ ] **Fase 2** — beat, label biner, fitur RR
- [ ] **Fase 3** — split inter-patient DS1/DS2
- [ ] **Fase 4** — model hybrid ~6.000 param
- [ ] **Fase 5** — training + class weight
- [ ] **Fase 6** — evaluasi float32 di DS2
- [ ] **Fase 7** — kuantisasi INT8 + tabel delta
- [ ] **Fase 8** — checklist PoC

## Decision point yang sudah di-lock

Tabel ini = LAMPIRAN B PRD versi hidup. Isi begitu ketok palu, jangan tunda.

| Keputusan | Nilai | Alasan singkat |
|---|---|---|
| Klasifikasi | biner (Normal/Aritmia) | inter-patient bikin F & Q recall ~0 |
| Split | inter-patient de Chazal | intra-patient = akurasi palsu |
| Filter | kausal `sosfilt` | `filtfilt` mustahil di MCU |
| Segmentasi | R-peak anotasi | jaga jalur model murni dari error detektor |
| Normalisasi | z-score per window | kebal beda amplitudo, nol kebocoran statistik |
| Pooling | GlobalAveragePooling1D | param jauh lebih kecil dari Flatten |
| Threshold | 0,5 | kalibrasi di DS1/val, **bukan** DS2 |
| Orde Butterworth | *(belum)* | 2 vs 4 — kunci satu, konsisten Python↔C |
| Strategi imbalance | *(belum)* | class_weight **atau** oversampling, jangan dua-duanya |
| Dropout Dense 16 | *(belum)* | |
| Tipe I/O INT8 | *(belum)* | konsisten dengan rencana firmware |
| Record kanal anomali | 114 (MLII idx 1); 102 & 104 tanpa MLII → `raise` | 102/104 paced, dibuang di Fase 3 juga |
| Filter non-beat | whitelist `BEAT_SYMBOLS` di `config.py` | simbol tak dikenal ikut kebuang, bukan lolos |

## Jebakan yang sudah ketemu

- **`wfdb.io.annotation.is_qrs` tidak bisa dipakai buat filter non-beat.**
  Gejala: `[`, `]`, `x`, `)` lolos sebagai "beat". Sebab: tabel wfdb menandai
  penanda awal/akhir ventricular flutter & non-conducted P-wave sebagai QRS.
  Hindari: whitelist eksplisit `config.BEAT_SYMBOLS` (15 simbol AAMI).
- **`import config` gagal dari `scripts/`.** Gejala: `ModuleNotFoundError` walau
  dijalankan dari `model/`. Sebab: `python scripts/x.py` menaruh `scripts/` di
  `sys.path[0]`, bukan cwd. Hindari: shim 1 baris `sys.path.insert` (lihat
  `scripts/plot_fase0.py`); `conftest.py` sudah menangani sisi pytest.

## Kanal knowledge

Sesi Claude Code di folder ini **tidak** mewarisi riwayat sesi lain (riwayat
tersimpan per direktori kerja). File ini satu-satunya yang selalu termuat —
tulis keputusan ke sini, bukan cuma ke chat.
