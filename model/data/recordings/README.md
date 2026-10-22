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
| 21 Okt 2026 | `20261021-1549-rekam-001` … `20261021-1550-rekam-006` | satu sesi 1.658 detik. **Lead I** (kuning di dada kiri atas mengikuti panduan SparkFun), bukan MLII; dipakai untuk mengukur waktu stabil gerbang kalibrasi, bukan untuk hasil klasifikasi. Direkam dengan firmware yang menulis berkas ke flash di tengah sesi, sehingga ±4,7 detik pertama berkas 002–006 kehilangan sampel tanpa tercatat (header `lewat=0`; RR terkompres ±40%). Buang 5 detik pertama berkas 002–006 saat menghitung RR. Puncak R menyentuh rail atas 4095 pada 71% detak (clipping 0,62% sampel) |
| 22 Okt 2026 | `20261022-1219-rekam-002` … `20261022-1220-rekam-005` | satu sesi 903 detik, MLII (kuning di bawah rusuk kiri), powerbank, elektroda baru, ulangan ke-2 waktu stabil gerbang kalibrasi. Tanpa sampel hilang (`lewat=0`). Dengung 50 Hz 13–28 di 30 detik pertama lalu naik bertangga sampai ±1.100 (35–130 detik) dan tinggal 190–360; elektroda lepas (LO) 14% / 0% / 41% / 62% per berkas; guncangan pada 810–840 detik (dilaporkan subjek di menit 13) dengan clipping. Berkas 003 (5–10 menit) paling bersih: dengung 3,3%, derau 4,7%, clipping 0 |
| 22 Okt 2026 (±12.38–12.54 WIB) | `20261022-1256-rekam-001`, `-002`, `20261022-1257-rekam-003`, `-004` | **Data resmi laporan** (keputusan user 22 Okt 2026, buku-pa Tabel kualitas rekaman R1–R4). Satu sesi 927,1 detik tanpa jeda, MLII, powerbank, elektroda baru, subjek S01 = penulis, Laboratorium MSECT PENS. Ulangan ke-3 waktu stabil gerbang kalibrasi. `lewat=0`, LO 0%, keempatnya Berhasil (dengung 1,9–3,8%, autokorelasi 0,28–0,38, BPM wajar 100%), jenuh 1/5/9/1 sampel (≤ 0,010%) |
