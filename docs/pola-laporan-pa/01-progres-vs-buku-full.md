# 01 — Perbedaan sistemik: Progres 1 vs Buku Full

Kesimpulan utama: **struktur bab sama, yang berbeda adalah kemasan dan lingkup
klaim.** Dokumen PA tumbuh secara akretif: proposal (Bab 1–3) → progres (Bab
1–3 disunting ringan + Bab 4–5 tahap awal) → buku full (Bab 1–3 nyaris tetap +
Bab 4–5 diperluas + front/back matter resmi). Karena tumbuh dengan cara
ditambal, sisa versi lama sering tertinggal (lihat §7 dan
[06-anti-pola.md](06-anti-pola.md)).

## 1. Matriks perbedaan

| Aspek | Progres 1 (OFFLINE, GDD, CODACY, BYOM) | Buku full (AFIB, ISYARAT) |
|---|---|---|
| Label sampul | "PROGRES" di atas "PROYEK AKHIR" (4/4) | "PROYEK AKHIR" saja, sampul dicetak dua kali (sampul + halaman judul dalam) |
| Halaman pengesahan | tidak ada | ada (ISYARAT: lembar bertanda tangan dicetak dari sistem MIS, p.3; AFIB: templat belum diisi, p.3) |
| Pernyataan orisinalitas, pengalihan hak cipta | tidak ada | AFIB punya keduanya (p.5–6) |
| Abstrak | 1 bahasa (Indonesia), 3/4 punya (BYOM tidak punya); isi = tujuan + rencana + harapan | Abstrak + Abstract (Inggris), masing-masing dengan Kata Kunci/Keywords; isi = masalah → metode → **angka hasil** |
| Kata pengantar | tidak ada | ada, setelah abstrak (AFIB) atau sebelum abstrak (ISYARAT) |
| Daftar Isi/Gambar/Tabel | ada | ada |
| Bab 1–3 | lengkap, diwarisi dari proposal | sama, diwarisi dari proposal/progres |
| Bab 4 | lengkap 4.1–4.7, dengan **pembatas lingkup**: "tahap progres ini", "fase pertama", MVP, data dummy, lingkungan pengembangan lokal, batas tanggal pengambilan data | lengkap 4.1–4.7 (+4.8 Dokumentasi di ISYARAT), validasi kuantitatif penuh: percobaan berulang, MAE, PDSR, confusion matrix, validasi ke pengguna/komunitas |
| Bab 5 | Kesimpulan = temuan sementara / status ketercapaian; Saran = **roadmap fase berikutnya** (PA2, semester berikutnya) | Kesimpulan = penutupan terhadap tujuan ("seluruh tujuan tercapai"); Saran = pengembangan di luar lingkup proyek |
| Lampiran, biodata | tidak ada | Lampiran (AFIB kosong; ISYARAT foto validasi), Biodata (ISYARAT) |
| Panjang | 61–106 halaman A4 | 135 (A4), 97 (A5) |
| Bab mulai di halaman ganjil | ya (4/4) | ya (2/2) |

## 2. Front matter dan back matter (urutan nyata)

**Progres** (OFFLINE, GDD, CODACY; BYOM tanpa Abstrak):

```
Sampul "PROGRES PROYEK AKHIR"   (judul, nama, NRP, 2–3 pembimbing + NIP, prodi, departemen, PENS, tahun)
(halaman sengaja dikosongkan)
Abstrak + Kata Kunci            [i]
(halaman sengaja dikosongkan)   [ii]
Daftar Isi                      [iii–iv]
Daftar Gambar                   [v]
(halaman sengaja dikosongkan)
Daftar Tabel                    [vii]
(halaman sengaja dikosongkan)
BAB 1 ... BAB 5                 [arab, mulai 1]
Daftar Pustaka
```

**Buku full** (gabungan AFIB dan ISYARAT):

```
Sampul "PROYEK AKHIR"
Halaman judul dalam (isi = sampul)
Halaman Pengesahan              (pembimbing + penguji + koordinator prodi, tanda tangan)
Pernyataan Orisinalitas          [i]   (AFIB)
Pernyataan Pengalihan Hak Cipta  [ii]  (AFIB)
Abstrak + Kata Kunci             [iii–iv]
Abstract + Keywords              [v–vi]
Kata Pengantar                   [vii–viii]
Daftar Isi, Daftar Gambar, Daftar Tabel
BAB 1 ... BAB 5
Daftar Pustaka
Lampiran
Biodata Peneliti                 (ISYARAT)
```

Jumlah pembimbing di sampul: 2 (OFFLINE, ISYARAT) atau 3 (AFIB, GDD, CODACY,
BYOM). Penguji baru muncul di lembar pengesahan buku full.

## 3. Abstrak: struktur kalimat

**Buku full = abstrak hasil.** Urutan fungsi kalimat AFIB (p.7–8), sekitar 12
kalimat:

1. Konteks penyakit/domain + urgensi (penyebab kematian, sering asimtomatik).
2. Kekurangan solusi komersial (tertutup, mahal, tanpa akses sinyal mentah).
3. Gap riset (performa dataset offline vs sensor murah yang bising).
4. Tujuan penelitian (merancang dan mengimplementasikan ...).
5. Perangkat keras dan sensor.
6. Alur pemrosesan di edge.
7. Platform cloud dan basis data.
8. Model, kernel, dataset latih.
9. Nilai tambah pendekatan (arsitektur terbuka, dashboard, notifikasi).
10. **Hasil kuantitatif** (latensi < 1 detik, akurasi 98,04%, presisi, recall).
11. Hasil uji integrasi end-to-end (30 menit, tanpa false positive).
12. Penegasan kesiapan untuk tahap berikutnya.

ISYARAT (p.5) mengikuti pola yang sama dengan proporsi lebih banyak ke hasil:
masalah → diperparah oleh → tujuan → fungsi ganda sistem → teknologi →
pendekatan → preprocessing → **tiga baris angka hasil** (WER, CER, F1, waktu
proses sebelum/sesudah).

**Progres = abstrak rencana.** OFFLINE (p.3), GDD (p.3): masalah →
tantangan/dampak → "penelitian ini diharapkan dapat menghasilkan ..." /
"pengujian direncanakan melalui ..." → prinsip/metode → harapan kontribusi.
Tidak ada angka hasil. CODACY (p.3) campuran: menyebut "hasil ... menunjukkan
peningkatan signifikan" tanpa angka, lalu ditutup "diharapkan". BYOM tidak
punya abstrak sama sekali.

Implikasi: abstrak progres boleh rencana, tetapi abstrak buku full **wajib**
memuat angka utama yang sama persis dengan Bab 4 dan Bab 5, plus versi Inggris.

## 4. Bab 4: penanda "tahap progres"

Penanda lingkup yang muncul di progres dan nyaris hilang di buku full
(frekuensi per 10.000 kata, regex "tahap progres | progres ini | fase
pertama | fase/tahap berikutnya | semester berikutnya | PA2"):

| AFIB | ISYARAT | OFFLINE | GDD | CODACY | BYOM |
|---|---|---|---|---|---|
| 1,2 | 0,6 | 4,5 | **10,9** | 0,7 | 4,4 |

CODACY rendah karena isinya memang sudah "selesai" untuk satu modul (studi
sebelum/sesudah refactoring), sehingga bab 4–5 nya berbunyi seperti buku full.

Bentuk konkret pembatas lingkup di progres:

| Bentuk | Contoh lokasi |
|---|---|
| Lingkup eksperimen dibatasi ke modul yang sudah jadi | OFFLINE 4.1.1 p.77; GDD 4.1 p.43; BYOM pembuka Bab 4 p.41 |
| Subbab eksplisit "Keterbatasan Scope" | GDD 4.1.4 p.44 |
| Metrik direncanakan tetapi belum diukur, disebut terang | OFFLINE 4.1.4 p.79 (TTF, MTBF, Uptime "masih tahap perancangan") |
| Data uji dummy/eksplorasi pengembang | OFFLINE 4.2.1 p.81 |
| Batas tanggal pengambilan data karena tenggat dokumen progres | OFFLINE 4.4 p.83 (6 Des 2025); GDD 4.4 p.47 (5 Des 2025) |
| Lingkungan uji = mesin pengembangan lokal / rumah, disertai alasan | OFFLINE 4.3; GDD 4.3; BYOM 4.3 p.44 |
| Hasil kualitatif diberi label jujur | OFFLINE 4.6.7 "(Kualitatif)" p.96 |
| Implementasi parsial disebut + keterbatasannya | BYOM 4.6.1 p.45–46 (BYOM baru RF-DETR) |
| Target fungsional "MVP" | BYOM 4.6.5 p.50 |
| Tabel ketercapaian per tujuan (Tercapai / Sebagian / Belum) | GDD Tabel 4.5 p.80–81 |
| Evaluasi per tujuan dengan catatan "pengujian skala penuh belum dilakukan" | BYOM 4.7.3 p.55 |

Buku full menggantinya dengan validasi kuantitatif: AFIB 10 kali percobaan per
sensor dengan MAE (p.112–115), PDSR (p.117–118), confusion matrix + ROC +
latensi (p.119–123); ISYARAT rumus + substitusi angka per skenario (p.60–84) +
validasi ke komunitas pengguna (p.85–87).

## 5. Bab 5: dua rezim

| | Progres | Buku full |
|---|---|---|
| Bentuk kesimpulan | Temuan sementara bernomor "Pertama/Kedua/Ketiga" (OFFLINE p.101), atau blok Pencapaian / Batasan & Progress / Kontribusi (GDD p.83–84), atau klaim bernomor + bukti "fase pertama" (BYOM p.57) | Narasi 4–5 paragraf: urgensi → orisinalitas → hasil vs target → penutup "seluruh tujuan tercapai" (AFIB p.127–128); ISYARAT narasi + butir angka (p.91–92) |
| Isi saran | Pekerjaan yang belum selesai di proyek ini: fitur belum jadi, metrik belum diukur, uji pengguna nyata, perluasan model | Riset lanjutan di luar lingkup: uji klinis, multi-kelas, PCB/miniaturisasi, keamanan, interoperabilitas, mobile app |
| Penanda | "fase berikutnya", "PA2", "semester berikutnya", "tahap selanjutnya" | "pengembangan selanjutnya", "di masa mendatang" |

## 6. Register waktu per bab (bukan per jenis dokumen)

Frekuensi per 1.000 kata. "akan" = rencana, "hasil" = berhasil/terbukti/
membuktikan.

| Dok | B1 akan | B3 akan | B4 akan | B4 hasil | B5 hasil |
|---|---|---|---|---|---|
| AFIB | 0,0 | **4,5** | 1,2 | 3,5 | 6,5 |
| ISYARAT | 5,4 | **9,0** | 4,2 | 2,6 | 4,3 |
| OFFLINE | 1,6 | **7,7** | 0,9 | 4,3 | 2,8 |
| GDD | 1,5 | **5,7** | 0,6 | 0,5 | 2,1 |
| CODACY | 2,0 | **6,2** | 0,3 | 6,9 | 6,0 |
| BYOM | 1,2 | **9,0** | 1,7 | 4,3 | **14,7** |

Bab 3 adalah puncak "akan" di keenam dokumen, termasuk di buku full. Jadi
**Bab 3 di buku full tidak perlu diubah ke kala lampau**: dia tetap "rancangan",
sedangkan realisasinya dilaporkan di Bab 4. Yang wajib dibersihkan adalah sisa
kata "proposal" dan rujukan ke elemen yang sudah dihapus.

## 7. Resep transformasi progres → buku full

Urutan kerja yang disimpulkan dari selisih kedua jenis dokumen:

1. **Sampul**: hapus label "PROGRES", tambah halaman judul dalam.
2. **Front matter baru**: Halaman Pengesahan (pembimbing + penguji +
   koordinator), Pernyataan Orisinalitas, Pernyataan Pengalihan Hak Cipta
   (jika diminta templat), Abstract (Inggris) + Keywords, Kata Pengantar.
3. **Abstrak**: tulis ulang dari rencana menjadi hasil. Angka di abstrak =
   angka di Bab 4 = angka di Bab 5 (cek silang).
4. **Bab 1**: ganti "proposal ini" menjadi "proyek akhir ini"; perbarui
   Sistematika Penulisan agar isi Bab 4–5 sesuai realisasi; pertimbangkan
   menambah Batasan Masalah bila lingkup final menyempit (AFIB menambahkan 1.3
   Batasan Masalah a–f, p.23–25).
5. **Bab 2**: biasanya tetap; tambahkan penelitian terkait baru bila ada; pastikan
   nomor sitasi sinkron dengan daftar pustaka.
6. **Bab 3**: biarkan sebagai rancangan; buang subbab yang tidak relevan untuk
   buku (Jadwal Pelaksanaan) **beserta semua rujukannya** (AFIB lupa, 4.4 p.102
   masih merujuk "Tabel 3.2 Jadwal"); sinkronkan rancangan dengan yang benar-benar
   dibangun atau beri catatan perubahan di Bab 4.
7. **Bab 4**: hapus pembatas "tahap progres"; ganti hasil kualitatif dengan
   angka; tambahkan validasi yang dijanjikan di Bab 3; tutup 4.7 dengan analisis
   per tujuan dan keterbatasan.
8. **Bab 5**: ubah "temuan sementara" menjadi kesimpulan per tujuan; ubah saran
   dari roadmap internal menjadi arah riset lanjutan.
9. **Back matter**: Lampiran (dokumentasi uji, data mentah ringkas), Biodata.
10. **QA akhir**: perbarui semua field/daftar isi (tidak boleh ada "Error!
    Bookmark not defined."), cek penomoran gambar/tabel/persamaan unik, cek
    setiap "Gambar/Tabel X.Y" dirujuk sebelum muncul.

## 8. Implikasi untuk progres 1 kita

- Tulis progres 1 sebagai **buku lima bab penuh**, bukan proposal yang
  ditempeli lampiran.
- Bab 4 progres harus jujur soal lingkup: sebut apa yang sudah terukur, apa
  yang baru fungsional, apa yang belum, dan kapan data diambil. Pakai tabel
  ketercapaian per tujuan.
- Bab 5 progres = temuan nyata (bukan pengulangan rencana) + roadmap konkret.
- Siapkan sejak awal hal yang kelak diwajibkan buku full (Abstract Inggris,
  lampiran dokumentasi) supaya transformasinya tinggal sunting.
