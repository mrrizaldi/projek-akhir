# Arsip rekaman uji coba (10 September – 11 Oktober 2026)

27 rekaman AD8232 yang diambil selama pengembangan, **sebelum** prosedur
perekaman resmi ditetapkan pada 13 Oktober 2026. Diarsipkan supaya tidak
tertukar dengan rekaman resmi di [`../../recordings/`](../../recordings/README.md).

**Hanya untuk pengembangan (diagnosis rangkaian, uji skrip analisis), bukan
data hasil.** Jangan dikutip sebagai hasil di laporan.

| Tanggal | Berkas | Rangkaian & catu | Catatan |
|---|---|---|---|
| 10 Sep 2026 | 6 (`20260910-*`) | breadboard, OUTPUT AD8232 → GPIO 4; catu USB laptop lalu powerbank | percobaan daya laptop vs powerbank dan pemasangan ulang elektroda |
| 14 Sep 2026 | 8 (`20260914-*`) | breadboard, OUTPUT dipindah dari GPIO 4 ke GPIO 8 pada hari itu (jalur GPIO 4 putus); powerbank | rangkaian masih berubah |
| 15 Sep 2026 | 11 (`20260915-*`) | breadboard, GPIO 8, firmware utama versi lama; powerbank | sebagian besar gagal (lantai derau, diduga header modul AD8232 belum disolder) |
| 11 Okt 2026 | 2 (`20261011-*`) | rangkaian uji dengan peta pin PCB, OUTPUT → GPIO 1; firmware uji perangkat keras lama | 1 rekaman lead-off penuh, 1 rekaman bersinyal |

Kondisi bersama: satu subjek, Lead II, elektroda wet-gel, firmware yang sudah
diganti (format CSV sama: header `# fs=360 n=... lewat=... [lepas=...]`).
Nama berkas = waktu **tarik**, bukan waktu rekam.

Grafik analisisnya ada di `model/artifacts/arsip/akuisisi-uji-coba/`. Riwayat
diagnosis rangkaian: `model/docs/arsip/riwayat-akuisisi-walkthrough.md`.
Menganalisis ulang (hasil grafik masuk `artifacts/metrics/akuisisi/`):

```
cd model
make analisis FILE=data/arsip/rekaman-uji-coba/20260915-1130.csv
```
