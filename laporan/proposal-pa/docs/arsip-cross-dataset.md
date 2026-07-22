# Arsip: Pembandingan / Generalisasi Lintas-Dataset (non-MIT-BIH)

**Tanggal arsip:** 2026-07-03
**Status:** Dinonaktifkan sementara (bukan dihapus). Menunggu pertimbangan lebih lanjut.
**File terdampak:** `proposal-pa/bab/bab3.tex`, `proposal-pa/referensi.bib`

## Konteks & alasan

Draft Bab 3 saat ini merencanakan validasi *cross-database* model klasifikasi
aritmia terhadap dua basis data selain MIT-BIH Arrhythmia Database, yaitu
**St. Petersburg INCART 12-lead Arrhythmia Database** dan
**MIT-BIH Supraventricular Arrhythmia Database (SVDB)**, dengan penyeragaman
frekuensi sampling (*resample* ke 360 Hz) dan pemetaan anotasi standar AAMI.

Atas permintaan penulis, seluruh pembahasan yang mengandalkan dataset selain
MIT-BIH **diarsipkan dulu** karena masih ada pertimbangan lebih lanjut (mis.
ketersediaan data, ruang lingkup pengujian, dan konsistensi klaim). Teks tidak
dihapus permanen agar mudah diaktifkan kembali.

## Ringkasan yang diarsipkan

| # | Lokasi (subbab) | Bentuk | Cara arsip |
|---|-----------------|--------|-----------|
| A | 3.2.2 → *Dataset dan Pelabelan* | Paragraf rencana validasi cross-database (INCART, SVDB) | `\iffalse ... \fi` |
| B1 | 3.2.6 → *Pengujian Model* | Paragraf pengujian lintas-basis-data pada INCART/SVDB | `\iffalse ... \fi` |
| B2 | 3.2.6 → kalimat pengantar Tabel 3.4 | Frasa "dan generalisasi lintas-basis-data" | Dihapus dari kalimat (agar sinkron dgn tabel) |
| B3 | 3.2.6 → Tabel *Rencana pengukuran pada pengujian model* | Baris "Generalisasi lintas-basis-data" | Di-`%`-comment (5 baris) |

### Catatan bibliografi
- Cite key **`goldberger_2000_physionet`** (PhysioNet/PhysioBank) hanya dipakai di
  blok A yang kini diarsipkan, sehingga kini menjadi entri tak-tersitasi. Entri
  **tetap dibiarkan** di `referensi.bib` (baris ~269) karena `%` tidak berfungsi
  sebagai komentar di BibTeX dan entri tak-tersitasi bersifat inert (tidak muncul
  di Daftar Pustaka, tidak menimbulkan error). Aktifkan kembali blok A untuk
  memunculkannya lagi.
- Tidak ada cite key khusus INCART/SVDB — keduanya hanya disebut naratif.

### Yang TIDAK diarsipkan (sengaja dipertahankan)
Kata "generalisasi" di tempat lain **bukan** soal dataset non-MIT-BIH, jadi tetap:
- `bab3.tex` — *inter-patient split* DS1/DS2 (generalisasi ke pasien baru, masih MIT-BIH).
- `bab2.tex:301, 379, 449` — pembahasan generalisasi pada penelitian lain (Zambrano, MIMIC-III, dll).

## Cara mengaktifkan kembali

1. **Blok A & B1:** hapus baris `\iffalse` dan `\fi` (beserta banner komentar `% ARSIP...` bila mau) yang membungkus paragraf terkait.
2. **B2:** kembalikan kalimat pengantar Tabel 3.4 menjadi
   "...mulai dari kualitas klasifikasi, dampak kuantisasi, dan generalisasi lintas-basis-data hingga performa perangkat keras,..."
3. **B3:** hapus tanda `%` di lima baris row tabel yang dikomentari.
4. `referensi.bib`: tidak perlu diapa-apakan (entri masih ada).
5. `make pdf` untuk verifikasi.

---

## Salinan verbatim teks asli (cadangan)

### A — Paragraf validasi cross-database (subbab *Dataset dan Pelabelan*)

> Untuk menguji generalisasi model secara lebih menyeluruh, selain MIT-BIH Arrhythmia
> Database sebagai dataset utama (pelatihan DS1 dan pengujian DS2 secara antar-pasien),
> penelitian ini juga merencanakan validasi *cross-database*
> menggunakan dua basis data pelengkap [goldberger_2000_physionet]. Pertama, St.
> Petersburg INCART 12-lead Arrhythmia Database yang memuat proporsi detak ventrikular
> jauh lebih besar sehingga menguji ketahanan deteksi kelas ventrikular pada kondisi
> akuisisi yang berbeda. Kedua, MIT-BIH Supraventricular Arrhythmia Database (SVDB) yang
> secara khusus memperkaya sampel detak supraventrikular (kelas S), sehingga menjadi
> pengujian langsung terhadap efektivitas cabang ritme yang dirancang untuk membedakan
> detak supraventrikular. Ketiga basis data memiliki frekuensi sampling yang berbeda
> (MIT-BIH 360 Hz, INCART 257 Hz, SVDB 128 Hz), sehingga seluruh rekaman terlebih dahulu
> diselaraskan (*resample*) ke frekuensi seragam 360 Hz agar konsisten dengan ukuran
> *window* 250 sampel dan pipeline Pan-Tompkins. Pemetaan anotasi mengikuti standar
> AAMI yang sama pada ketiga basis data sehingga skema klasifikasi biner tetap berlaku.

### B1 — Paragraf pengujian lintas-basis-data (subbab *Pengujian Model*)

> Selain evaluasi pada DS2, model diuji ulang secara lintas-basis-data pada INCART dan
> SVDB (setelah *resample* ke 360 Hz) untuk mengukur generalisasi terhadap kondisi
> akuisisi dan distribusi kelas yang berbeda. SVDB secara khusus digunakan untuk menilai
> *recall* kelas supraventrikular sebagai pembuktian manfaat cabang ritme RR.

### B3 — Baris tabel *Rencana pengukuran pada pengujian model*

| Aspek | Metrik | Cara Pengukuran | Target Indikatif |
|-------|--------|-----------------|------------------|
| Generalisasi lintas-basis-data | *Recall* dan F1-*score* per kelas | Evaluasi pada INCART dan SVDB setelah *resample* ke 360 Hz | *Recall* supraventrikular terjaga pada SVDB |
