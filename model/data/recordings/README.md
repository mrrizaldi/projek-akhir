# Rekaman sinyal tubuh (resmi)

Folder tujuan `make pull` (`scripts/pull_recording.py`): setiap rekaman yang
ditarik dari board tersimpan di sini sebagai `<tanggal-jam-tarik>.csv`, atau
`<tanggal-jam-tarik>-rekam-NNN.csv` bila ditarik per nomor (`make pull N=<n>`).

**Rekaman resmi dimulai 13 Oktober 2026**, dengan firmware rekaman lanjut otomatis (sejak 15 Oktober 2026). Rekaman 14 Oktober 2026 masuk arsip uji coba karena firmware saat itu memotong rekaman di 300 detik. Rekaman sebelum tanggal itu adalah
uji coba selama pengembangan dan diarsipkan di
[`../arsip/rekaman-uji-coba/`](../arsip/rekaman-uji-coba/README.md) — **jangan
dipakai sebagai data hasil** (Bab 4 laporan, tabel kualitas rekaman).

Prosedur merekam, menarik, dan menganalisis: [`../../docs/akuisisi-walkthrough.md`](../../docs/akuisisi-walkthrough.md).
Hasil analisis (`make analisis FILE=data/recordings/<nama>.csv`) mengisi
penanda `PLACEHOLDER-DATA` di `laporan/buku-pa/` (`grep -rn PLACEHOLDER-DATA laporan/buku-pa`).

## Catatan per sesi

| Sesi | Berkas | Catatan |
|---|---|---|
| 15 Okt 2026 | `20261015-1727-rekam-003`, `-004` | dua sesi terpisah; 004 berisi artefak gerak dan clipping |
| 21 Okt 2026 | `20261021-1549-rekam-001` … `20261021-1550-rekam-006` | satu sesi 1.658 detik. Direkam dengan firmware yang menulis berkas ke flash di tengah sesi, sehingga ±4,7 detik pertama berkas 002–006 kehilangan sampel tanpa tercatat (header `lewat=0`; RR terkompres ±40%). Buang 5 detik pertama berkas 002–006 saat menghitung RR. Puncak R menyentuh rail atas 4095 pada 71% detak (clipping 0,62% sampel) |
