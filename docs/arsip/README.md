# Arsip rencana kerja

**Isi:** rencana kerja lintas komponen (laporan, firmware) yang sudah dijalankan.
**Status:** read-only. Kondisi firmware yang berlaku ada di
[`firmware/README.md`](../../firmware/README.md); kondisi laporan ada di `laporan/` dan aturan
gayanya di `laporan/CLAUDE.md`; pola penulisan ada di
[`../pola-laporan-pa/README.md`](../pola-laporan-pa/README.md).

| Tanggal | Dokumen | Ringkasan | Status akhir / vonis |
|---|---|---|---|
| 2026-10-10 | [buku-pa-progres-plan](2026-10-10-buku-pa-progres-plan.md) | Rencana mengisi `laporan/buku-pa` menjadi laporan progres lima bab: Bab 1–3 diangkat dari proposal dan disesuaikan dengan realisasi (tabel Proposal → Realisasi), Bab 4–5 ditulis dari hasil eksperimen; ilustrasi berupa placeholder | Diterapkan: `laporan/buku-pa/bab/` memuat draf Bab 1–5 dan abstrak. Angka status di dalam rencana (HW-5, daya) mencerminkan kondisi 10 Okt 2026 |
| 2026-10-13 | [firmware-menu-plan](2026-10-13-firmware-menu-plan.md) | Menu di perangkat (tiga tombol, tekan lama 800 ms), pemecahan `main.cpp` per modul, daftar WiFi/broker di NVS, tes perangkat bersama menu dan `test_hw_*`, tangga ukur daya mandiri + `make pull-daya` | Diterapkan, Fase 0–6 selesai (commit `9ba6498` s.d. `07a5a07`). Paragraf tombol/menu di Bab 3 laporan belum disesuaikan (gate point) |

Arsip dokumen model dan hardware: [`model/docs/arsip/README.md`](../../model/docs/arsip/README.md).
Arsip bagian proposal: `laporan/proposal-pa/docs/arsip-cross-dataset.md`.
