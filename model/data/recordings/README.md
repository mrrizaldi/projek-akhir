# Rekaman sinyal tubuh (resmi)

Folder tujuan `make pull` (`scripts/pull_recording.py`): setiap rekaman yang
ditarik dari board tersimpan di sini sebagai `<tanggal-jam-tarik>.csv`, atau
`<tanggal-jam-tarik>-rekam-NNN.csv` bila ditarik per nomor (`make pull N=<n>`).

**Rekaman resmi dimulai 13 Oktober 2026.** Rekaman sebelum tanggal itu adalah
uji coba selama pengembangan dan diarsipkan di
[`../arsip/rekaman-uji-coba/`](../arsip/rekaman-uji-coba/README.md) — **jangan
dipakai sebagai data hasil** (Bab 4 laporan, tabel kualitas rekaman).

Prosedur merekam, menarik, dan menganalisis: [`../../docs/akuisisi-walkthrough.md`](../../docs/akuisisi-walkthrough.md).
Hasil analisis (`make analisis FILE=data/recordings/<nama>.csv`) mengisi
penanda `PLACEHOLDER-DATA` di `laporan/buku-pa/` (`grep -rn PLACEHOLDER-DATA laporan/buku-pa`).
