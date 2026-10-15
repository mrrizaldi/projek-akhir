# Pola Laporan PA: Progres 1 vs Buku Full

Bedah pola enam laporan PA D4 Teknik Informatika PENS (dua buku full, empat
laporan progres 1) supaya laporan progres dan buku PA kita bisa ditulis
mengikuti pola yang sudah terbukti lolos, sekaligus menghindari kesalahan yang
berulang di dokumen-dokumen itu.

Dibuat 10 Okt 2026. Sumber: enam PDF di `~/Downloads` (tidak di-commit).

## Korpus

Kode dipakai di seluruh folder ini supaya rujukan pendek.

| Kode | Jenis | Topik (ringkas) | Thn | Hal. PDF | Kertas | Kata | Gambar | Tabel | Pustaka | Berkas |
|---|---|---|---|---|---|---|---|---|---|---|
| AFIB | Buku full | Smart wearable IoT deteksi AFib, SVM, cloud | 2026 | 135 | A4 | 24,7 rb | 43 | ±13 | 23 | `Buku Final_RANCANG BANGUN SMART WEARABLE ... CLOUD.pdf` |
| ISYARAT | Buku full | Penerjemah suara/teks/video ke BISINDO, NLP | 2025 | 97 | A5 | 17,0 rb | 22 | 13 | 16 | `1. Buku Full.pdf` |
| OFFLINE | Progres 1 (Revisi 5) | Arsitektur offline-first Flutter, sinkronisasi, ISO | 2025 | 106 | A4 | 26,9 rb | 24 | 5 | 22 | `Alga - Sidang Progress_Revisi_5.pdf` |
| GDD | Progres 1 (Rev 4) | UX + SQA Work Fusion, Goal-Directed Design, McCall | 2025 | 90 | A4 | 15,6 rb | 27 | 6 | 33 | `Rev 4 - 5-1 - Progrerss PA_Rakha ....pdf` |
| CODACY | Progres 1 (Rev 5) | Maintainability backend FoodLAB, Codacy, refactoring | 2025 | 65 | A4 | 15,3 rb | 23 | 4 | 22 | `Dukhaan_Progres_PA_SarjanaTerapan_A4_Rev(5).pdf` |
| BYOM | Progres 1 (revisi) | Backend edge-cloud, Bring-Your-Own-Model, DAG | 2025 | 61 | A4 | 16,0 rb | 16 | 2 | 26 | `Revisi Progres PA Nedo Vision Jhiven.pdf` |

Catatan baca:
- **Rujukan halaman `p.N` = urutan halaman di berkas PDF**, bukan nomor yang
  tercetak di kaki halaman (romawi dan arab beda offset).
- "Kata" dihitung dari seluruh teks hasil `pdftotext` (termasuk front matter).
  Angka per bab ada di [02-pola-per-bab.md](02-pola-per-bab.md).
- Keempat progres adalah versi **revisi** (Rev 4, Revisi 5, Rev 5, "Revisi"),
  artinya dokumen progres lazim bolak-balik direvisi beberapa kali setelah
  sidang progres. Rencanakan waktunya.

## Peta isi

| Berkas | Isi | Level |
|---|---|---|
| [01-progres-vs-buku-full.md](01-progres-vs-buku-full.md) | Perbedaan sistemik progres vs buku full, dan resep transformasi progres → buku | dokumen |
| [02-pola-per-bab.md](02-pola-per-bab.md) | Kerangka baku tiap bab, matriks per dokumen, proporsi, benang merah antarbab | bab |
| [03-pola-paragraf.md](03-pola-paragraf.md) | 19 arketipe paragraf, urutan paragraf dalam subbab, perangkat kohesi antarparagraf | paragraf |
| [04-pola-kalimat.md](04-pola-kalimat.md) | Pustaka kalimat-formula per fungsi, register "progres" vs "final", panjang kalimat, sitasi, istilah | kalimat |
| [05-gambar-tabel-persamaan.md](05-gambar-tabel-persamaan.md) | Inventaris jenis gambar/tabel per bab, pola "sandwich", **aturan placeholder gambar** | elemen |
| [06-anti-pola.md](06-anti-pola.md) | Kesalahan nyata di korpus beserta cara mencegahnya | QA |
| [07-penerapan-ke-pa-kita.md](07-penerapan-ke-pa-kita.md) | **Adaptasi ke PA kita**: beda PA kita dari korpus, peta analog per bagian, posisi terhadap AFIB (pembimbing sama), penyesuaian Bab 1–3 dan 5, hal khusus hardware/biomedis, keputusan terbuka | aksi |
| [08-bab4-pa-kita.md](08-bab4-pa-kita.md) | **Rencana Bab 4 PA kita**: 4.6 disusun per tujuan, format tiap tabel, angka kunci berlabel sumber, draf ketercapaian, gambar yang sudah ada vs placeholder | aksi |

## Ringkasan temuan (paling penting dulu)

1. **Progres 1 = buku utuh lima bab, bukan proposal + lampiran.** Keempat
   progres sudah memuat Bab 4 (Eksperimen dan Analisis) dan Bab 5 (Penutup)
   lengkap dengan subbab baku. Bedanya dengan buku full bukan pada struktur,
   melainkan pada **lingkup klaim** di Bab 4–5 dan **front/back matter**.
2. **Bab 4 punya kerangka beku** yang dipakai keenam dokumen: 4.1 Parameter
   Eksperimen, 4.2 Karakteristik Data, 4.3 Tempat Ujicoba, 4.4 Waktu Ujicoba,
   4.5 Spesifikasi Peralatan Ujicoba, 4.6 Hasil Eksperimen, 4.7 Analisis Hasil
   Eksperimen. Jangan diubah urutannya.
3. **Register waktu ditentukan oleh bab, bukan oleh jenis dokumen.** Bab 3
   tetap ditulis sebagai rencana ("akan", 4,5–9,0 per 1.000 kata) bahkan di
   buku full. Bab 4–5 ditulis sebagai capaian ("berhasil/terbukti"). Progres
   ditandai frasa pembatas lingkup ("pada tahap progres ini", "fase pertama",
   "fase berikutnya").
4. **Progres yang kuat mengaku jujur apa yang belum.** Pola terbaik: tabel
   ketercapaian Tercapai / Sebagian / Belum per tujuan (GDD p.80–81), daftar
   metrik yang "masih tahap perancangan" (OFFLINE p.79), test case gagal
   dilaporkan apa adanya (GDD 2 pass 3 fail), dan trade-off yang diukur lalu
   dijelaskan (BYOM lebih lambat 14%, p.52–54).
5. **Benang merah wajib bisa ditelusuri:** Permasalahan (1.2) → Tujuan (1.3)
   → Deskripsi Permasalahan (2.1) → Deskripsi Solusi (3.1) → Rencana Uji
   (akhir Bab 3) → Parameter (4.1) → Analisis per masalah/tujuan (4.7) →
   Kesimpulan (5.1). BYOM adalah contoh paling bersih (3 masalah ↔ 3 tantangan
   ↔ 3 tujuan ↔ analisis per masalah ↔ evaluasi per tujuan).
6. **Bab 1 tidak pernah punya gambar maupun tabel** (6/6). Bab 5 juga tidak.
   Gambar/tabel hidup di Bab 2 (pinjaman, ber-"Sumber"), Bab 3 (rancangan
   sendiri), Bab 4 (bukti).
7. **Sitasi menumpuk di Bab 1–2** (Bab 2 = 25–83 penanda sitasi) dan hampir
   nol di Bab 3–5. Pengecualian yang patut ditiru: BYOM mengutip literatur di
   4.1 untuk membenarkan pilihan metrik.
8. **Setiap gambar dan tabel diapit paragraf**: pengantar sebelum, penjelasan
   "Gambar X.Y menunjukkan ..." sesudah, dibaca urut sesuai alur diagram, lalu
   ditutup makna terhadap tujuan.
9. **Tabel pembanding penelitian terkait dengan baris terakhir "penelitian
   ini"** muncul di 6/6 dokumen (AFIB menyebutnya State of the Art).
10. **Bab 5 selalu pendek** (2–4 halaman, ±3–4% kata). Progres: temuan
    sementara + roadmap fase berikutnya. Buku full: penutupan terhadap tujuan +
    pengembangan di luar lingkup.
11. **Sisa versi lama adalah kesalahan paling sering**: "proposal ini" di buku
    full, "tiga bab utama" padahal lima bab, rujukan ke tabel jadwal yang sudah
    dihapus, "Error! Bookmark not defined." Lihat 06.
12. **Setiap bab dimulai di halaman ganjil** (6/6), dengan halaman pengisi
    "(halaman sengaja dikosongkan)".

## Aturan gambar untuk kerja Claude

Diagram dan gambar ilustrasi **tidak dibuat sendiri oleh Claude** (tidak ada
Mermaid, TikZ, PlantUML, SVG, atau skrip gambar baru). Claude menaruh
**placeholder** berisi spesifikasi isi gambar, lalu user yang menggambar.
Templat dan aturannya ada di
[05-gambar-tabel-persamaan.md §Placeholder](05-gambar-tabel-persamaan.md#placeholder-gambar),
dan aturannya juga tercatat di `CLAUDE.md` root serta memori proyek.

## Metode

- Teks diekstrak dengan `pdftotext` (mode raw dan layout), dibaca utuh
  keenam dokumen, lalu dianotasi per bab.
- Angka (kata per bab, penanda sitasi, panjang kalimat dan paragraf, frekuensi
  penanda kohesi) dihitung dengan skrip Python kecil di scratchpad sesi.
  Panjang paragraf adalah **perkiraan** (dideteksi dari indentasi baris
  pertama), panjang kalimat dan hitungan kata cukup akurat.
- Gaya visual diagram dicek dari render halaman contoh (arsitektur, flowchart,
  persona, diagram pipeline).
- Contoh kalimat di folder ini adalah **templat buatan sendiri** yang meringkas
  pola, bukan salinan kalimat dari dokumen sumber. Bukti ditunjuk lewat kode
  dokumen + halaman.
