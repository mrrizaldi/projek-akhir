# Arsip rencana kerja

**Isi:** rencana kerja lintas komponen (laporan, firmware) yang sudah dijalankan.
**Status:** read-only. Kondisi firmware yang berlaku ada di
[`firmware/README.md`](../../firmware/README.md); kondisi laporan ada di `laporan/` dan aturan
gayanya di `laporan/CLAUDE.md`; pola penulisan ada di
[`2026-10-10-pola-laporan-pa/README.md`](2026-10-10-pola-laporan-pa/README.md)
(diarsipkan 15 Okt 2026 setelah isinya didistilasi ke skill `struktur-pa`,
`narasi-pa`, `tabel-pa`, dan `buku-ikut-proposal`).

| Tanggal | Dokumen | Ringkasan | Status akhir / vonis |
|---|---|---|---|
| 2026-10-10 | [buku-pa-progres-plan](2026-10-10-buku-pa-progres-plan.md) | Rencana mengisi `laporan/buku-pa` menjadi laporan progres lima bab: Bab 1–3 diangkat dari proposal dan disesuaikan dengan realisasi (tabel Proposal → Realisasi), Bab 4–5 ditulis dari hasil eksperimen; ilustrasi berupa placeholder | Diterapkan: `laporan/buku-pa/bab/` memuat draf Bab 1–5 dan abstrak. Angka status di dalam rencana (HW-5, daya) mencerminkan kondisi 10 Okt 2026 |
| 2026-10-13 | [firmware-menu-plan](2026-10-13-firmware-menu-plan.md) | Menu di perangkat (tiga tombol, tekan lama 800 ms), pemecahan `main.cpp` per modul, daftar WiFi/broker di NVS, tes perangkat bersama menu dan `test_hw_*`, tangga ukur daya mandiri + `make pull-daya` | Diterapkan, Fase 0–6 selesai (commit `9ba6498` s.d. `07a5a07`). Paragraf tombol/menu di Bab 3 laporan belum disesuaikan (gate point) |
| 2026-11-01 | [celah-target](2026-11-01-celah-target.md) | Pindai celah terhadap target Bab 1/Bab 3/PRD: satu target belum diukur (daya), sembilan terpenuhi dengan cakupan sempit, empat target PRD belum disebut, tiga kalimat buku basi soal INA219 | Daftar kerja aktif; butir dicoret saat ditutup |
| 2026-11-01 | [crosscheck-metrik-bab4](2026-11-01-crosscheck-metrik-bab4.md) | Crosscheck metrik dan cara ukur Bab 4 terhadap standar (AAMI EC57, MLPerf Tiny, IEC 60601, IETF IPPM, ITU-T G.1010/H.810) dan 86 sumber teks lengkap, lima laporan rinci per kategori | Hasil riset; aksi A–D dan empat keputusan user menunggu |

Arsip dokumen model dan hardware: [`model/docs/arsip/README.md`](../../model/docs/arsip/README.md).
Arsip bagian proposal: `laporan/proposal-pa/docs/arsip-cross-dataset.md`.
