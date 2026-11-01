# Arsip rencana kerja

**Isi:** rencana, audit, dan riset lintas komponen (laporan, firmware) yang sudah
selesai dijalankan.
**Status:** catatan historis, read-only, **tidak berlaku** sebagai acuan kerja.
Isi yang masih berlaku sudah dipindah ke tempatnya: kondisi firmware di
[`firmware/README.md`](../../firmware/README.md), kondisi laporan di `laporan/`
dan aturan gayanya di `laporan/CLAUDE.md`, pola penulisan di skill `struktur-pa`,
`narasi-pa`, `tabel-pa`, dan `buku-ikut-proposal`. Pekerjaan yang masih berjalan
ada di [`docs/`](../README.md), satu tingkat di atas folder ini.

| Tanggal | Dokumen | Ringkasan | Status akhir / vonis |
|---|---|---|---|
| 2026-10-10 | [buku-pa-progres-plan](2026-10-10-buku-pa-progres-plan.md) | Rencana mengisi `laporan/buku-pa` menjadi laporan progres lima bab: Bab 1–3 diangkat dari proposal dan disesuaikan dengan realisasi (tabel Proposal → Realisasi), Bab 4–5 ditulis dari hasil eksperimen; ilustrasi berupa placeholder | Diterapkan: `laporan/buku-pa/bab/` memuat draf Bab 1–5 dan abstrak. Angka status di dalam rencana (HW-5, daya) mencerminkan kondisi 10 Okt 2026 |
| 2026-10-10 | [pola-laporan-pa/](2026-10-10-pola-laporan-pa/README.md) | Bedah enam laporan PA PENS sebagai asal aturan penulisan | Didistilasi ke skill `struktur-pa`, `narasi-pa`, `tabel-pa`, dan `buku-ikut-proposal` (15 Okt 2026); skill itulah acuannya |
| 2026-10-13 | [firmware-menu-plan](2026-10-13-firmware-menu-plan.md) | Menu di perangkat (tiga tombol, tekan lama 800 ms), pemecahan `main.cpp` per modul, daftar WiFi/broker di NVS, tes perangkat bersama menu dan `test_hw_*`, tangga ukur daya mandiri + `make pull-daya` | Diterapkan, Fase 0–6 selesai (commit `9ba6498` s.d. `07a5a07`). Paragraf tombol/menu di Bab 3 laporan belum disesuaikan (gate point) |
| 2026-10-15 | [audit-referensi](2026-10-15-audit-referensi.md) | Audit `laporan/buku-pa/referensi.bib` lewat Scopus dan Crossref: keberadaan dokumen, DOI, metadata | Diterapkan ke `referensi.bib`; dilanjutkan oleh referensi-pra-2020 |
| 2026-10-19 | [referensi-pra-2020](2026-10-19-referensi-pra-2020.md) | Penggantian pustaka terbitan sebelum 2020 (15 → 7 dari 41 entri) beserta rasional per entri yang dipertahankan | Diterapkan ke `referensi.bib`; dokumen ini tetap menjadi rasional per entri yang dirujuk `CLAUDE.md` |

Arsip dokumen model dan hardware: [`model/docs/arsip/README.md`](../../model/docs/arsip/README.md).
Arsip bagian proposal: `laporan/proposal-pa/docs/arsip-cross-dataset.md`.
