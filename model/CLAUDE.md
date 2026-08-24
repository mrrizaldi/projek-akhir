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

- [~] **Fase 0** — dataset MIT-BIH ter-download di `data/raw/mitdb/`; eksplorasi
  record 100 sudah jalan. Sisa: `load_record()` di `src/io_mitdb.py` + DoD
  (panjang sinyal ~650.000, ~2.200 R-peak, `fs == 360`, simbol non-beat dibuang).
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
| Record kanal anomali | *(belum)* | catat record yang MLII bukan index 0 |

## Jebakan yang sudah ketemu

*(isi sambil jalan: gejala → sebab → cara hindar)*

## Kanal knowledge

Sesi Claude Code di folder ini **tidak** mewarisi riwayat sesi lain (riwayat
tersimpan per direktori kerja). File ini satu-satunya yang selalu termuat —
tulis keputusan ke sini, bukan cuma ke chat.
