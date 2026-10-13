# Arsip dokumen model/ dan hardware

**Isi:** dokumen desain, rencana implementasi, dan changelog eksperimen yang
sudah selesai dijalankan atau ditutup, beserta catatan riwayat yang dikeluarkan
dari dokumen aktif.
**Status:** read-only. Berkas di folder ini tidak diperbarui mengikuti kode;
kondisi sistem yang berlaku dijelaskan oleh dokumen aktif
([`../README.md`](../README.md), [`../../CLAUDE.md`](../../CLAUDE.md), dan
[`../../../firmware/README.md`](../../../firmware/README.md)).

Isi dokumen arsip ditulis pada saat dokumen itu berlaku, termasuk status
sementara ("belum diimplementasikan", checklist terbuka) dan angka dari
konfigurasi yang kemudian diganti. Kolom *Status akhir* di bawah menyatakan
nasib akhir tiap dokumen terhadap kode saat ini.

Rencana yang isinya sudah sepenuhnya terwujud di kode dan walkthrough dihapus
pada 13 Okt 2026 (desain workflow `model/`, rencana implementasi daya, rencana
ketahanan Fase 6c, skrip eksplorasi awal `scripts/arsip/`). Salinannya tersedia
di git pada tag `pra-bersih`.

## Dokumen desain, rencana, dan changelog

| Tanggal | Dokumen | Ringkasan | Status akhir / vonis |
|---|---|---|---|
| 2026-09-16 | [daya-design](2026-09-16-daya-design.md) | Desain pengukuran konsumsi daya: tangga mode beban `p0`–`p4`, pembacaan INA219 tanpa library, pemasangan fisik, konversi mA ke mAh | Belum dijalankan; satu-satunya spesifikasi pengukuran daya yang masih terbuka. Yang sudah ada di kode: konversi INA219 murni (`ina219.cpp` + `test_ina219`) dan sumber sinyal replay (toggle `y`) |
| 2026-09-18 | [robustness-changelog](2026-09-18-robustness-changelog.md) | Fase 6c (adaptasi Dias 2021): rencana → pelaksanaan, keputusan yang diambil, cara mengulang, verifikasi di board | Window 128/128 dan threshold 0,80 dikunci; F1 DS2 0,5659 → 0,6594, AUC 0,8866 → 0,9334. HOS dan penggantian filter ditolak. Temuan metodologis: seed terkunci tidak mengunci hasil, sehingga ablasi memakai 3 seed |
| 2026-09-19 | [fitur-design](2026-09-19-fitur-design.md) | Sintesis 7 paper; 10 usul yang bertabrakan dengan decision point terkunci; §9 skor akhir dan prasyarat pembukaan kembali | Ditutup tanpa perubahan konfigurasi: 4 gugur, 2 dorman, 3 dikonfirmasi, 4 dihentikan. Satu-satunya yang masuk produksi: assert `MAX_RHYTHM_SCALE` |
| 2026-09-19 | [multidataset-plan](2026-09-19-multidataset-plan.md) | Fase A: gabungan mitdb + svdb + incartdb, frekuensi, gate polaritas lead, split, audit 13 pemeriksaan | Infrastruktur multi-database tersedia (`ablasi.py --db`), DS2 byte-identik. Database latih tetap mitdb |
| 2026-09-19 | [faseB-changelog](2026-09-19-faseB-changelog.md) | Fase B–F: 4 varian database × 3 seed, `class_weight`, titik operasi, tabel 2×2 dataset × fitur, tahap 2 | Tanpa perubahan konfigurasi. `class_weight` balanced tetap; efek svdb dan fitur baru saling meniadakan |
| 2026-09-19 | [faseG-changelog](2026-09-19-faseG-changelog.md) | Fase G: regime latih (rata-rata bobot, learning rate, k-dari-n), TEST-B/TEST-C sebagai wasit | Tanpa perubahan konfigurasi. Learning rate tetap 1e-3: 1e-4 menaikkan AUC tetapi menurunkan recall S; pertukaran dilaporkan |
| 2026-10-08 | [pcb-rev2-adjustment](2026-10-08-pcb-rev2-adjustment.md) | Penyesuaian skematik PCB rev1 → rev2: TFT, buzzer, tombol, AD8232, pin map rev2, catatan rangkaian baterai, checklist pabrik | Pin map rev2 dipakai `firmware/src/hwtest.cpp`. Rangkaian baterai dan checklist pabrik berada di luar lingkup firmware |

## Riwayat per dokumen

Saat dokumentasi aktif diformalkan (Okt 2026), catatan perubahan, koreksi, dan
konteks historis dikeluarkan dari dokumen aktif dan dipindah ke berkas
`riwayat-<nama-dokumen>.md` di folder ini, satu berkas per dokumen sumber.
Setiap berkas diawali tautan ke dokumen sumbernya dan berisi entri per tanggal
atau topik dengan butir **Perubahan** dan **Alasan / bukti**. Dokumen aktif
hanya memuat klaim yang berlaku; berkas riwayat menyimpan jalur yang ditempuh
menuju klaim itu.

| Berkas riwayat | Dokumen sumber |
|---|---|
| [riwayat-status-fase](riwayat-status-fase.md) | `model/CLAUDE.md`, bagian status fase |
| [riwayat-akuisisi-walkthrough](riwayat-akuisisi-walkthrough.md) | [`akuisisi-walkthrough.md`](../akuisisi-walkthrough.md) |
| [riwayat-dataset-walkthrough](riwayat-dataset-walkthrough.md) | [`dataset-walkthrough.md`](../dataset-walkthrough.md) |
| [riwayat-evaluate-walkthrough](riwayat-evaluate-walkthrough.md) | [`evaluate-walkthrough.md`](../evaluate-walkthrough.md) |
| [riwayat-features-rr-walkthrough](riwayat-features-rr-walkthrough.md) | [`features-rr-walkthrough.md`](../features-rr-walkthrough.md) |
| [riwayat-firmware-walkthrough](riwayat-firmware-walkthrough.md) | [`firmware-walkthrough.md`](../firmware-walkthrough.md) |
| [riwayat-jitter-walkthrough](riwayat-jitter-walkthrough.md) | [`jitter-walkthrough.md`](../jitter-walkthrough.md) |
| [riwayat-komentar-kode](riwayat-komentar-kode.md) | komentar & docstring kode (`firmware/`, `model/`, `dashboard/`) |
| [riwayat-model-walkthrough](riwayat-model-walkthrough.md) | [`model-walkthrough.md`](../model-walkthrough.md) |
| [riwayat-mqtt-walkthrough](riwayat-mqtt-walkthrough.md) | [`mqtt-walkthrough.md`](../mqtt-walkthrough.md) |
| [riwayat-prep-beats-walkthrough](riwayat-prep-beats-walkthrough.md) | [`prep-beats-walkthrough.md`](../prep-beats-walkthrough.md) |
| [riwayat-preprocessing-walkthrough](riwayat-preprocessing-walkthrough.md) | [`preprocessing-walkthrough.md`](../preprocessing-walkthrough.md) |
| [riwayat-quantize-walkthrough](riwayat-quantize-walkthrough.md) | [`quantize-walkthrough.md`](../quantize-walkthrough.md) |
| [riwayat-segmentasi-deteksi-walkthrough](riwayat-segmentasi-deteksi-walkthrough.md) | [`segmentasi-deteksi-walkthrough.md`](../segmentasi-deteksi-walkthrough.md) |
| [riwayat-train-walkthrough](riwayat-train-walkthrough.md) | [`train-walkthrough.md`](../train-walkthrough.md) |
