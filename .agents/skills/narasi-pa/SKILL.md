---
name: narasi-pa
description: Wajib dipakai saat menulis, menyunting, atau meninjau paragraf laporan PA (laporan/buku-pa, progres, proposal), terutama paragraf pengantar dan penjelas tabel/gambar, hasil dan analisis Bab 4, serta permintaan "perbaiki narasi", "rapikan bahasa", atau "review bab". Temuan dulu, klaim sebanding bukti, kalimat pendek, satu paragraf satu fungsi.
---

# Narasi PA

Kegagalan yang ditangkap user (15 Okt 2026): narasi laporan "harus
dipertimbangkan". Hasil `python3 scripts/cek_tabel.py` pada buku-pa saat itu:
- 18 paragraf penjelas di Bab 4 dibuka "Berdasarkan Tabel~\ref{...}," dan 15
  di antaranya berurutan dengan pembuka yang sama. Polanya ditiru mekanis
  dari pola korpus "Berdasarkan Tabel X.Y, ..." (bedah laporan PENS, kini
  arsip `docs/arsip/2026-10-10-pola-laporan-pa/`).
- Penjelas `tab:beban-komputasi` mengulang 7 dari 11 angka tabel, dan
  penjelas `tab:dekomposisi-latensi` mengulang 8 dari 15. Paragrafnya membaca
  ulang tabel, bukan menyimpulkan.
- "sehingga" 82 kali di Bab 4 (8,0 per 1.000 kata) dan 83 kali di Bab 3
  (10,8 per 1.000 kata). Ada 59 kalimat Bab 4 yang lebih dari 35 kata,
  terpanjang 70 kata, sebagian besar berupa rantai "..., sehingga ...,
  sedangkan ..., sehingga ...".
- Penjelas `tab:ablasi` 234 kata dan `tab:dekomposisi-latensi` 129 kata
  mencampur hasil, mekanisme, dan keputusan rancangan dalam satu paragraf.

Asal aturan: diadaptasi dari `evaluate` dan `polish` (minhuw/Codex-writer),
`academic-writing` (David-Saeteros/Codex-skills), dan `writing_standards.md`
(lishix520/academic-paper-skills), lalu disesuaikan dengan
`laporan/AGENTS.md` dan bedah enam laporan PA PENS (arsip
`docs/arsip/2026-10-10-pola-laporan-pa/`). Skill ini **tidak mengulang**
aturan gaya di `laporan/AGENTS.md` (titik koma, titik dua, em dash, istilah
asing, desimal, `~\cite`, label kerja internal) maupun kerangka bab di skill
`struktur-pa`. Keduanya tetap berlaku penuh dan diperiksa bersamaan.

| Dari skill Inggris | Keputusan | Bentuk di sini |
|---|---|---|
| *topic sentence* di awal paragraf | diambil | aturan 1, temuan dulu |
| *causal language on correlational data*, "significant" non-statistik | diambil | aturan 4, tangga klaim |
| *reverse outline*, satu paragraf satu tujuan | diambil | aturan 6 dan mode Audit |
| skor 0–100 per dimensi dengan "+n poin" | diganti | tabel temuan berprioritas. Skor tanpa rubrik PENS tidak bisa dibandingkan antarsesi |
| *bad-first*, hanya saran yang bermakna | diambil | mode Audit |
| *polish for non-native English* | tidak relevan | laporan berbahasa Indonesia baku |
| pola korpus "Berdasarkan Tabel X.Y, ..." | **dilonggarkan** | pola korpus, bukan kewajiban. Pembuka divariasikan (aturan 2) |

## Aturan

1. **Paragraf penjelas tabel/gambar: Temuan → Bukti → Makna.**
   - Kalimat pertama adalah temuan utama dalam satu kalimat, dengan rujukan
     tabel/gambar di dalam kalimat atau di kurung akhir. Contoh pola:
     "{Objek} {memenuhi/tidak memenuhi/berubah} {arah} pada {kondisi}
     (Tabel~\ref{..})."
   - Bukti: paling banyak **lima angka di seluruh paragraf**, termasuk
     ambang, target, dan selisih yang dipakai sebagai pembanding. Pilih
     angka tabel yang paling menentukan, dan setiap angka **dibandingkan**
     dengan sesuatu (target, acuan, kondisi lain) atau **dijelaskan**
     sebabnya. Angka tanpa pembanding adalah transkripsi, termasuk selisih
     kecil ("F1 naik 0,0010" saja salah, "F1 naik 0,0010, jauh di bawah
     ambang 0,02" benar). Angka yang tidak bisa diberi pembanding dibuang. Hitung angkanya
     sebelum menyerahkan, dan tulis jumlahnya dengan benar.
   - Makna: satu kalimat penutup yang mengaitkan ke target, tujuan, atau
     keputusan rancangan.
   - Opsional: anomali atau keterbatasan yang terlihat di tabel, satu sampai
     dua kalimat. Bila lebih panjang, jadikan paragraf sendiri.

2. **Pembuka bervariasi.** "Berdasarkan Tabel" paling banyak 3 kali per bab
   dan tidak pernah pada dua penjelas berurutan. Pola pembuka lain, dipilih
   sesuai isi:
   - temuan langsung: "Seluruh target pengiriman terpenuhi pada kedua ulangan
     (Tabel~\ref{..})."
   - perbandingan: "Dibandingkan {acuan}, {objek} {naik/turun} {besaran}
     (Tabel~\ref{..})."
   - pengecualian: "Seluruh selisih berada di bawah ambang kecuali {metrik},
     yang ..."
   - titik terpenting: "Angka yang paling menentukan pada Tabel~\ref{..}
     adalah {besaran}, karena ..."
   - lanjutan dari paragraf sebelumnya: "Kerugian {X} tersebut seluruhnya
     berasal dari ..."
   - "Tabel~\ref{..} memperlihatkan bahwa ..." (dihitung bersama
     "Berdasarkan Tabel" dalam batas 3 per bab)

3. **Jangan membaca ulang tabel.** Paragraf penjelas mengulang paling banyak
   setengah angka tabel (`N-ULANG` pada skrip). Bila paragraf terpaksa
   menyusuri setiap baris agar bermakna, yang salah adalah desain tabelnya.
   Kembalikan ke skill `tabel-pa`, misalnya dengan menambah kolom Status atau
   Selisih.

4. **Klaim sebanding bukti.** Kekuatan kata kerja mengikuti kekuatan bukti:

   | Bukti | Kata yang boleh |
   |---|---|
   | satu pengukuran, satu kondisi | "menunjukkan", "terukur", "pada uji ini" |
   | berulang (≥ 2 ulangan atau ≥ 3 *seed*), kondisi disebut | "konsisten", "memenuhi target" |
   | seluruh lingkup klaim diuji (mis. semua tahap uji data acuan lulus) | "terbukti", "setara" |
   | tidak diukur langsung, hanya dari mekanisme | "diperkirakan", "diduga", "kemungkinan besar" |
   | pembanding statistik (uji hipotesis) | "signifikan" |

   - "Signifikan" tanpa uji statistik diganti "bermakna di atas ambang
     {nilai}" atau "selisih {nilai}".
   - Hubungan sebab-akibat hanya dari ablasi terkendali (satu pengaturan
     diubah, ≥ 3 *seed*). Pengamatan bersamaan ditulis "bertepatan dengan"
     atau "diikuti", bukan "menyebabkan".
   - Kondisi uji selalu menempel pada klaim, mis. sumber sinyal *replay*
     vs sinyal tubuh, jumlah ulangan, dan data uji (DS2, SVDB, INCART).
     Klaim tentang sinyal tubuh tidak boleh berdasar uji *replay*.
   - "Menjamin", "selalu", "pasti", dan "sangat" dihapus kecuali dibuktikan
     di seluruh lingkupnya.
   - Metrik tanpa target (mis. p95) ditulis "dilaporkan" dan tidak
     diposisikan terhadap ambang metrik lain ("melampaui batas median").
     Bila rencana menyebut angka acuan untuknya, bandingkan dengan acuan
     itu dan sebut sebagai acuan, bukan target: "p95 3.304~ms, di atas acuan
     2 detik yang tidak dijadikan target".
   - Tidak menambah fakta yang tidak ada di sumber (tabel, artefak, atau
     tugas), misalnya "tertinggi di antara seluruh varian" atau "memenuhi
     anggaran perangkat" tanpa angkanya. Ini berlaku juga untuk kerangka
     kalimat berisi slot: jangan menulis slot klaim peringkat seperti
     "tertinggi/terendah [N] di antara varian" bila peringkat itu tidak ada
     di sumber. Yang tidak diketahui ditulis `[N]`
     atau `\PlaceholderData{...}`.

5. **Kalimat 15–30 kata, pecah di atas 35.** Paling banyak satu "sehingga"
   per kalimat, dan jangan merangkai "..., sehingga ..., sedangkan ...,
   sehingga ...". Cara memecah:
   - sebab dan akibat jadi dua kalimat. Kalimat kedua dibuka
     "Akibatnya," / "Karena itu," / "Dampaknya," / subjek baru, dan
     pembukanya dirotasi.
   - keterangan syarat ("bila ...", "dengan ...") yang panjang jadi kalimat
     tersendiri.
   - daftar lebih dari tiga butir jadi `enumerate`/`itemize`, atau pindah ke
     tabel.
   Target per bab: "sehingga" ≤ 5 per 1.000 kata (`N-SEHINGGA`).

6. **Satu paragraf satu fungsi, 60–150 kata.** Fungsi yang tidak dicampur:
   hasil (apa yang terukur, 4.6), mekanisme (mengapa, 4.7 atau Bab 3),
   keputusan rancangan (apa yang dipilih dan atas bukti apa), dan
   keterbatasan. Paragraf di atas 180 kata dipecah per fungsi
   (`N-PANJANG`). Kalimat pertama setiap paragraf menyatakan klaim utama
   paragraf itu sesuai fungsinya (temuan untuk hasil, pernyataan mekanisme
   untuk mekanisme, keputusan untuk keputusan), bukan rincian atau
   pengantar. Uji cepat: setiap paragraf bisa diberi judul 3–5 kata yang
   jujur. Bila judulnya butuh "dan", pecah.

7. **Tanpa pembuka meta di subbab dan butir** (keputusan user 19 Okt 2026,
   gaya buku AFIB). Bab tidak memiliki paragraf pembuka "Bab ini ..."
   (keputusan user 20 Okt 2026, skill `struktur-pa` aturan 1). Subbab
   dan butir langsung masuk ke isi: tidak dibuka "Subbab ini memaparkan
   ...", "Butir ini bertujuan ...", atau "Bagian ini menguraikan ...", dan
   tidak menyebut tujuan bernomor ("menjawab Tujuan 2"). Tujuan uji ditulis
   sebagai pernyataan isi: "Kode C di ESP32-S3 harus menghitung hal yang
   sama dengan Python.", "Kemampuan model diukur pada pasien yang tidak
   pernah dilihat saat pelatihan." Diperiksa `cek_tabel.py` (N-META,
   N-TUJUAN).

8. **Kohesi lama → baru.** Kalimat dibuka dengan hal yang sudah dikenal
   pembaca dari kalimat atau paragraf sebelumnya, dan ditutup dengan
   informasi baru. Kata penunjuk selalu punya target yang jelas ("penurunan
   tersebut", bukan "hal ini" atau "pada subbab ini"). Kalimat tidak
   menunjuk ke bab, subbab, atau butir lain ("sebagaimana diuraikan pada
   Bab~\ref{..}", "(Subbab~\ref{..})", "dibahas pada butir d"), tetapi
   menyebut isinya langsung (skill `struktur-pa` aturan 11, N-PENUNJUK). Pembuka paragraf
   yang menjahit ke paragraf sebelumnya dirotasi dari lima jenis: anafora
   ("Penurunan tersebut ..."), urutan ("Pertama, ... Kedua, ..."), kontras
   ("Namun, ..." / "Sebaliknya, ..."), penambahan ("Selain itu, ..."), dan
   simpulan ("Dengan demikian, ..." hanya untuk menutup subbab). Paragraf
   terakhir subbab menyiapkan subbab berikutnya, dan paragraf yang
   memperkenalkan gambar atau tabel tidak memulai topik baru.

9. **Istilah dan singkatan konsisten.** Satu konsep satu istilah di seluruh
   buku. Contohnya, setelah memilih "pengujian rekaman resmi", jangan
   bergantian dengan "uji rekaman final". Sebelum memperkenalkan istilah,
   periksa dengan `grep -rn "istilah" laporan/buku-pa/bab`. Singkatan
   didefinisikan saat pertama muncul di setiap bab (PDSR, AUC, p95, ISR).

10. **Benang merah.** Setiap butir hasil 4.6 ditutup dengan kalimat yang
   menyatakan target pada rencana Bab 3 terpenuhi atau tidak. 4.7 menjawab
   "mengapa" dan "apa artinya", tanpa mengulang angka 4.6 kecuali sebagai
   rujukan. Bab 5 tidak memuat angka atau temuan baru. Rantai lengkapnya ada
   di skill `struktur-pa` aturan 3.

11. **Register dan kejujuran.** Bab 3 ditulis sebagai rancangan, Bab 4–5
    sebagai capaian (skill `struktur-pa` aturan 4). Yang belum
    diukur ditulis "belum diukur" atau `\PlaceholderData{...}`, tidak
    pernah dalam bentuk lampau.

12. **Sunting tidak mengubah isi.** Saat menyunting, himpunan angka,
    `\cite`, `\ref`, dan `\label` sebelum dan sesudah harus sama, kecuali
    perubahannya disengaja dan disebut ke user. Baris komentar `% sumber:`
    dipertahankan dan dipindah bersama kalimatnya.

## Arketipe paragraf per fungsi

Urutan fungsi kalimat yang terbukti di korpus laporan PENS dan tetap dipakai
di PA ini. Setiap arketipe tunduk pada aturan 1–12 di atas.

| Tempat | Urutan fungsi kalimat |
|---|---|
| Latar belakang (1.1) | konteks → urgensi berangka + sitasi → solusi eksisting dan kekurangannya ("Saat ini ... Namun ...") → gap riset → usulan + alasan metode → harapan |
| Tujuan (1.3) | kalimat klaim orisinalitas ("mengajukan pendekatan baru untuk ... dengan ...") → butir tujuan satu per masalah, diawali kata kerja, bertarget bila ada |
| Teori (2.2.x) | definisi + sitasi → komponen/ciri → (gambar) → **"Dalam penelitian ini, {teori} digunakan untuk {fungsi} pada {komponen}"** sebagai penutup wajib |
| Penelitian terkait (2.3.x) | tujuan + pendekatan + sitasi → metode uji + angka hasil → kesimpulan mereka → **relevansi dan perbedaan** ("Berbeda dengan penelitian tersebut yang berfokus pada ..., penelitian ini menekankan ...") |
| Pemosisian sesudah tabel pembanding | tinjauan tabel → beda dengan kelompok studi offline/simulasi [sitasi] → beda dengan kelompok perangkat komersial/model berat [sitasi] → pilihan rancangan + kesadaran keterbatasan → kontribusi yang terukur dan tidak mengklaim superioritas mutlak |
| Komponen rancangan (3.2.x) | fungsi → masukan dan keluaran → hubungan ke komponen berikutnya → (alasan teknologi) |
| Rencana uji (akhir Bab 3) | tujuan uji → metode/alat → metrik + ambang → **alasan ambang** → akibat bila tidak tercapai |
| Hasil uji (4.6.x) | tujuan uji sebagai pernyataan isi, tanpa "Butir ini bertujuan" → setup dan skenario → rujukan bukti → observasi faktual → kondisi awal yang belum ideal + dugaan sebab → perbaikan → hasil sesudahnya → vonis terhadap target → jembatan ke tahap berikut |
| Analisis (4.7.x) | klaim → bukti angka (rujuk tabel/gambar) → mekanisme → kaitan ke tujuan/standar → batasan. Varian trade-off: kelemahan terukur → sumbernya → mengapa diterima |
| Keterbatasan (akhir 4.7) | "Walaupun {capaian}, ..." → status prototipe → keterbatasan teknis → keterbatasan metodologis (subjek, lingkungan) → tahap lanjutan |
| Kesimpulan (5.1) | urut tujuan, dibuka isi ("Preprocessing di ESP32-S3 terbukti ..."), bukan "Tujuan pertama tercapai": klaim → bukti angka dari Bab 4, tanpa angka baru |
| Saran (5.2) | tiap butir: kondisi sekarang → tindakan yang disarankan → manfaatnya |

## Mode

- **Tulis**: draf paragraf baru mengikuti aturan 1–12. Angka hanya dari
  artefak repo atau tabel yang sudah ada, dengan komentar `% sumber:`.
- **Sunting**: tampilkan per paragraf versi sebelum (dikutip apa adanya) →
  sesudah, ditambah satu baris alasan per perubahan yang menyebut nomor
  aturan. Ubah seperlunya, dan
  jangan menulis ulang paragraf yang sudah lolos aturan. Suntingan `.tex`
  menunggu persetujuan user kecuali bab dan paragrafnya sudah disebut boleh
  diubah (`laporan/` read-only, `AGENTS.md` root). Selama belum ditulis ke
  `.tex`, pesan ke user menyebutnya "usulan", bukan "sudah dirapikan" atau
  "sudah disunting", dan status itu konsisten di seluruh pesan.
- **Audit** (read-only): jalankan `python3 scripts/cek_tabel.py`, baca
  babnya, lalu buat *reverse outline* (satu baris fungsi per paragraf).
  Laporkan paling banyak 15 temuan per bab, temuan terburuk dulu:

  | # | Prioritas | Lokasi (berkas:baris) | Masalah (nomor aturan) | Usulan konkret |
  |---|---|---|---|---|

  Tinggi: klaim melebihi bukti, angka tidak cocok dengan tabel atau artefak,
  benang merah putus, atau register salah. Sedang: penjelas membaca ulang
  tabel, paragraf mencampur fungsi, atau istilah tidak konsisten. Rendah:
  pembuka berulang, kalimat panjang, atau "sehingga". Temuan Rendah yang
  sudah tercakup keluaran skrip cukup diringkas menjadi satu baris. Tidak ada
  pujian kecuali diminta, dan tidak ada saran kosmetik yang tidak mengubah
  keterbacaan.

## Contoh (Sunting, dari buku-pa 15 Okt 2026)

Sebelum, penjelas `tab:beban-komputasi` (148 kata, 7 dari 11 angka tabel
diulang, dibuka "Berdasarkan Tabel"): paragraf menyusuri anggaran 2.778 µs,
beban 82 µs, burst 33,4 ms, antrean 13, 256, dan 12, lalu sampel hilang 0
dalam urutan baris tabel.

Sesudah (±115 kata, 4 angka tabel, temuan dulu):

```latex
Jalur preprocessing di perangkat tidak kehilangan sampel walaupun beban
sesaatnya melampaui anggaran waktu (Tabel~\ref{tab:beban-komputasi}). Secara
rata-rata pemrosesan hanya memakai 3,0\% anggaran per sampel. Beban itu
menumpuk ketika deteksi R-\textit{peak} atas bufer empat detik bertepatan
dengan inferensi detak baru, dan satu sampel dapat memakan sekitar 12 kali
anggaran. Tanpa pembacaan ADC di ISR, setiap lonjakan seperti ini akan
membuang sekitar 12 sampel dan merusak interval R-R. Antrean ISR menyerap
lonjakan tersebut dengan terisi 12 sampel, mendekati kebutuhan 13 sampel
hasil perhitungan dan jauh di bawah kapasitas 256 sampel. Keluaran perangkat
juga stabil, yaitu 11 detak per putaran \textit{replay} 6,67 detik dengan pola
probabilitas yang identik pada setiap putaran.
```

Contoh pemecahan kalimat 50 kata dari penjelas `tab:dekomposisi-latensi`:

```latex
Deteksi berjalan tiap 1 detik atas \textit{ring} 4 detik, dan detak yang
ditemukan baru boleh keluar 128 sampel atau 356~ms sesudah puncak R. Karena
itu penundaan di sisi perangkat berada di antara 356 dan 1.356~ms. Bila setiap
detak rata-rata menunggu setengah siklus deteksi, reratanya sekitar 856~ms,
sejalan dengan 869~ms yang terukur.
```

## Pemeriksaan isi sesudah menyunting

```bash
git show HEAD:laporan/buku-pa/bab/bab4.tex > /tmp/lama.tex
python3 - /tmp/lama.tex laporan/buku-pa/bab/bab4.tex <<'X'
import re, sys
pola = r"\\(?:cite|ref|label)\{[^}]*\}|\d[\d.]*(?:,\d+)?"
ambil = lambda p: sorted(re.findall(pola, open(p).read()))
lama, baru = ambil(sys.argv[1]), ambil(sys.argv[2])
hilang = [x for x in set(lama) if lama.count(x) > baru.count(x)]
tambah = [x for x in set(baru) if baru.count(x) > lama.count(x)]
print("hilang:", sorted(hilang)); print("tambah:", sorted(tambah))
X
```

Angka yang dihapus karena tidak diulang dari tabel memang wajar hilang dari
paragraf. Pastikan angka itu ada di tabel, lalu sebutkan ke user. Angka atau
sitasi yang hilang tanpa alasan dikembalikan.

## Daftar periksa akhir

- [ ] Setiap penjelas tabel/gambar yang disentuh dibuka temuan, memuat ≤ 5
      angka yang dibandingkan atau dijelaskan, dan ditutup makna.
- [ ] `cek_tabel.py`: `N-PEMBUKA`, `N-ULANG`, dan `N-PANJANG` untuk paragraf
      yang disentuh 0. `N-KALIMAT` dan `N-SEHINGGA` per bab turun dari
      sebelum suntingan, dengan angka dari keluaran yang dijalankan.
- [ ] Tidak ada "signifikan" tanpa uji statistik, dan tidak ada
      "menjamin"/"selalu" tanpa bukti di seluruh lingkup.
- [ ] Kondisi uji (*replay*/sinyal tubuh, ulangan, data uji) menempel pada
      setiap klaim hasil.
- [ ] Aturan gaya `laporan/AGENTS.md` lolos, termasuk `grep` label kerja
      internal di bagian §Larangan Label Kerja Internal.
- [ ] Pemeriksaan isi: angka, `\cite`, `\ref`, dan `\label` yang hilang
      semuanya disengaja dan disebut ke user.
- [ ] `make pdf` sukses dan `undefined` 0, dari keluaran yang dijalankan.
      Yang belum dijalankan ditulis "belum dijalankan".
