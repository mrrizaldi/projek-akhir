# 03 — Pola paragraf

Satuan analisis: paragraf sebagai "langkah" dalam argumen. Setiap arketipe
ditulis sebagai urutan fungsi kalimat (K1, K2, ...), lalu templat buatan
sendiri dengan slot `{...}`. Templat sudah disesuaikan dengan aturan gaya kita
di `laporan/CLAUDE.md` (tanpa titik dua pengantar daftar di tengah paragraf,
tanpa titik koma, tanpa em dash, tanpa penomoran inline "(1)", istilah teknis
Inggris dimiringkan, desimal pakai koma). Di Markdown, miring ditandai `*...*`.

Ukuran: median paragraf korpus 45–100 kata (perkiraan), umumnya 3–6 kalimat.
Bab 1–2 lebih panjang (70–100), Bab 3–4 lebih pendek (45–70).

---

## Bagian A — Arketipe paragraf

### P1. Pembuka bab

- **Fungsi**: memberi peta bab sebelum subbab pertama. Diwajibkan Panduan
  untuk Bab 2 dan Bab 3, dan dipakai sebagian besar dokumen untuk Bab 4.
- **Urutan** (Bab 2, BYOM p.15): K1 masalah utama dalam ranah masalahnya → K2
  akibatnya bagi sistem yang ada → K3 apa yang akan dikupas di teori penunjang
  → K4 penelitian terkait dipakai untuk menguatkan orisinalitas.
- **Urutan** (Bab 4, CODACY p.41, BYOM p.41): K1 apa yang divalidasi bab ini →
  K2 komponen/objek uji → K3 daftar aspek yang dipaparkan sesuai urutan subbab
  → K4 fokus analisis.
- **Templat Bab 2**: "{Masalah utama} masih menjadi kendala dalam {ranah
  masalah}, terutama karena {penyebab utama}. Bab ini menguraikan teori
  penunjang yang mendasari {komponen solusi}, kemudian meninjau penelitian
  terkait yang menangani masalah serupa untuk menegaskan posisi dan keunikan
  penelitian ini."
- **Templat Bab 4**: "Bab ini memaparkan eksperimen untuk memvalidasi {objek}
  yang telah dirancang pada Bab 3. Pembahasan mencakup parameter eksperimen,
  karakteristik data, tempat dan waktu ujicoba, spesifikasi peralatan, hasil
  eksperimen, dan analisis yang dikaitkan kembali dengan tujuan penelitian."
- **Kesalahan**: menulis ulang isi Bab 1; langsung loncat ke 2.1 tanpa pembuka
  (AFIB, OFFLINE).

### P2. Paragraf urgensi berangka

- **Fungsi**: membuktikan masalah itu penting dan nyata.
- **Urutan**: K1 klaim umum → K2 angka statistik + sitasi → K3 angka kedua atau
  akibat klinis/bisnis + sitasi → K4 kesimpulan "sehingga {X} menjadi kebutuhan
  mendesak".
- **Lokasi**: AFIB p.21 par 2; BYOM p.9 par 1; GDD p.11 par 3.
- **Templat**: "{Fenomena} merupakan {posisi masalah} dengan {angka 1}~[n].
  Kondisi ini {akibat terukur, angka 2}~[m]. Karena {sifat masalah, mis. sering
  tanpa gejala}, {kebutuhan} menjadi semakin mendesak."
- **Catatan**: angka tanpa sitasi melemahkan paragraf (ISYARAT p.11 menyebut
  data WHO tanpa nomor rujukan).

### P3. Paragraf kontras eksisting vs kekurangan

- **Fungsi**: menunjukkan solusi yang ada belum cukup.
- **Urutan**: K1 "Saat ini, {solusi eksisting} telah {kemampuan}" → K2 "Namun,
  {keterbatasan}" + sitasi → K3 rincian keterbatasan → K4 dampaknya.
- **Lokasi**: AFIB p.21–22; BYOM p.9 par 2.
- **Templat**: "Saat ini, {solusi} telah menyediakan {fitur}. Namun, {solusi}
  umumnya bersifat {kelemahan}~[n]. Akibatnya, {pihak} tidak dapat {aktivitas
  yang terhambat}, sehingga {dampak}."

### P4. Paragraf gap riset

- **Fungsi**: menyatakan apa yang belum dijawab literatur.
- **Urutan**: K1 "Berbagai penelitian telah {capaian}" → K2 "Kendati demikian,
  terdapat kesenjangan antara {A} dan {B}" → K3 sebab kesenjangan + sitasi → K4
  "Oleh karena itu, {hal yang perlu diuji/dibangun}".
- **Lokasi**: AFIB p.22 par 4; OFFLINE p.12 par 4.

### P5. Paragraf usulan

- **Fungsi**: memperkenalkan solusi dan alasan pemilihan metode.
- **Urutan**: K1 "Merespons tantangan tersebut, penelitian ini mengusulkan
  {solusi}" → K2 komponen utama → K3 alur kerja singkat → K4 "{Metode} dipilih
  karena {alasan 1}, {alasan 2}, dan {alasan 3}" → K5 cara validasi.
- **Lokasi**: AFIB p.22 par 5.
- **Varian penutup Bab 1.1**: kalimat yang memuat judul lengkap dalam tanda
  kutip lalu harapan kontribusi (AFIB p.22–23).

### P6. Paragraf tujuan berklaim orisinalitas

- **Fungsi**: kalimat pertama 1.3 sesuai Panduan.
- **Urutan**: K1 "Penelitian proyek akhir ini mengajukan pendekatan baru untuk
  mengatasi {masalah} dengan {inti solusi}" → K2 "Untuk mencapai hal tersebut,
  penelitian ini memiliki tujuan spesifik yang menjawab setiap permasalahan"
  → daftar tujuan (enumerate).
- **Lokasi**: OFFLINE p.13; BYOM p.11 (dua-duanya memakai rumus Panduan nyaris
  kata per kata).
- **Aturan butir**: satu tujuan per masalah, diawali kata kerja ("Merancang",
  "Membangun", "Memvalidasi", "Mengevaluasi"), memuat target terukur bila
  memungkinkan (AFIB p.25).

### P7. Paragraf definisi teori + peran

- **Fungsi**: isi baku setiap subbab 2.2.x.
- **Urutan**: K1 definisi + sitasi → K2 karakteristik/komponen utama → K3
  (opsional) rujukan gambar → K4 penjelasan gambar → K5 **"Dalam penelitian
  ini, {teori} berperan sebagai/digunakan untuk {fungsi spesifik}"**.
- **Lokasi**: AFIB 2.2.1–2.2.14 (p.32–48); CODACY 2.2 ("Dalam konteks
  FoodLAB"); BYOM 2.2.x (kalimat penutup "Dalam penelitian ini, penerapan ...").
- **Varian AFIB**: peran ganda "sebagai konteks" dan "sebagai *enabler*"
  dalam dua paragraf terpisah (p.32–34).
- **Templat K5**: "Dalam penelitian ini, {teori} digunakan untuk {fungsi} pada
  {komponen sistem}, sehingga {manfaat langsung terhadap tujuan}."
- **Kesalahan**: teori tanpa K5 terasa seperti salinan buku teks. Teori alat
  bantu (IDE, editor) tanpa nilai argumen sebaiknya tidak dijadikan subbab.

### P8. Blok penelitian terkait (3–4 paragraf per paper)

- **Fungsi**: isi baku setiap subbab 2.3.x.
- **Urutan blok**:
  - P8a: tujuan penelitian + pendekatan + sitasi di akhir.
  - [Gambar dari paper + baris "Sumber: Penelitian "{judul}" [n]"]
  - P8b: metodologi pengujian + **angka hasil** (akurasi, jumlah subjek,
    latensi).
  - P8c: kesimpulan penulis + arah pengembangan mereka.
  - P8d: relevansi dan perbedaan dengan penelitian ini.
- **Lokasi**: AFIB 2.3.1–2.3.10 (P8a–P8c, p.50–65); BYOM 2.3.x (P8a–P8d,
  p.20–23); GDD 2.3.x versi padat (1 par ringkasan + 1 par "Kelebihan ...
  Namun, kekurangannya ...", p.30–32); ISYARAT (1 par ringkasan + 1 par
  "Perbedaan utama ...", p.21–23).
- **Templat P8d**: "Penelitian ini relevan dengan penelitian yang diusulkan
  karena keduanya {kesamaan}. Namun, terdapat perbedaan pada {aspek}.
  Penelitian tersebut berfokus pada {fokus mereka}, sedangkan penelitian yang
  diusulkan menekankan {fokus kita}."
- **Catatan**: P8d adalah paragraf yang paling dicari penguji. AFIB tidak
  menulisnya per paper dan baru membedakan di tabel + paragraf pemosisian.

### P9. Paragraf pemosisian (setelah tabel pembanding)

- **Fungsi**: menyimpulkan posisi penelitian terhadap literatur.
- **Urutan**: K1 "Berdasarkan tinjauan pada Tabel 2.x, ..." → K2 beda dengan
  kelompok studi simulasi/offline [sitasi] → K3 beda dengan kelompok perangkat
  komersial/model berat [sitasi] → K4 pilihan desain + kesadaran keterbatasan →
  K5 klaim kontribusi yang terukur dan rendah hati.
- **Lokasi**: AFIB p.71–72 (K5 menolak klaim superioritas mutlak, pilihan yang
  aman di depan penguji); CODACY p.31–32 (butir temuan literatur lalu
  "Sementara itu, penelitian ini berbeda ...").

### P10. Sandwich gambar

- **Fungsi**: setiap gambar diapit dua paragraf.
- **Urutan**: P10a pengantar satu kalimat ("Gambar X.Y berikut
  mengilustrasikan {apa}") → [GAMBAR] → P10b "Gambar X.Y menunjukkan {apa}" +
  pembacaan berurutan → P10c makna terhadap sistem/tujuan.
- **Aturan pembacaan P10b**:
  - Diagram arsitektur: per zona sesuai nomor di gambar (AFIB p.75 zona 1–4 →
    butir a–c).
  - Flowchart: dari Mulai, setiap keputusan dibaca dua cabangnya ("jika ...,
    maka ... Jika tidak, ...") sampai Selesai (AFIB p.79–81; OFFLINE p.55–60).
  - Diagram bernomor: "ditandai dengan nomor pada diagram", lalu daftar
    bernomor yang sama (BYOM p.33).
  - Tangkapan layar multi-panel: "Pada tampilan pertama (kiri atas) ... kedua
    (kanan atas) ..." (OFFLINE p.85–90).
  - Gambar a/b: sebut (a) dan (b) dalam caption dan dalam paragraf (AFIB
    p.105–109).
- **Kesalahan**: paragraf penjelas hanya "Gambar X.Y diatas merupakan gambar
  dari {objek}" tanpa pembacaan (AFIB 2.2.6–2.2.13).

### P11. Sandwich tabel

- **Urutan**: K-pengantar "... ditunjukkan pada Tabel X.Y." → [TABEL] → P11b
  "Berdasarkan Tabel X.Y, ..." + baca kolom kunci per baris atau per kelompok
  ("Pertama ... Kedua ... Terakhir ...", OFFLINE p.20) → kesimpulan.
- **Lokasi**: AFIB Tabel 2.1 + p.30; OFFLINE Tabel 2.1 + p.20; CODACY Tabel 4.3
  + p.57.

### P12. Sandwich persamaan

- **Urutan**: K1 konsep + "dirumuskan sebagai berikut" → [PERSAMAAN (N.M)] → K2
  "di mana {simbol} adalah {arti}" untuk setiap simbol → K3 makna fisik/klinis
  → K4 bagaimana dipakai dalam sistem.
- **Lokasi**: AFIB 3.2.6–3.2.7 (p.82–84), ISYARAT WER/CER (p.60–61), BYOM
  definisi metrik benchmark berupa rumus dalam teks (p.51–52).

### P13. Paragraf komponen (desain)

- **Fungsi**: menjelaskan satu komponen pada diagram.
- **Bentuk**: butir berjudul (a. {Komponen}) + 2–4 kalimat: fungsi → masukan
  dan keluaran → hubungan ke komponen berikutnya → (opsional) alasan
  teknologi.
- **Lokasi**: AFIB 3.2.1–3.2.2 (p.75–78); BYOM 3.2.2–3.2.3 (p.28–30).

### P14. Paragraf skenario uji (rencana, akhir Bab 3)

- **Urutan**: K1 tujuan uji → K2 metode/alat → K3 metrik + ambang → K4
  **alasan ambang** ("Penetapan ambang ... didasarkan pada ...") → K5 akibat bila
  ambang tidak tercapai.
- **Lokasi**: AFIB 3.3 a.1 (p.92); OFFLINE 3.3.2 (definisi → metodologi →
  butir → "Sebagai contoh, skenario ..." dengan angka konkret durasi, latensi,
  *packet loss*, p.66–74); BYOM 3.2.8 (Skenario → Metrik → Kriteria
  Keberhasilan, p.38–39).

### P15. Paragraf hasil uji (4.6.x)

- **Urutan lengkap** (AFIB 4.6.1 a, p.104–106):
  1. Tujuan uji, satu kalimat.
  2. *Setup* dan skenario.
  3. Rujukan gambar/tabel bukti.
  4. Observasi faktual ("Berdasarkan hasil pengamatan, ...").
  5. Kondisi awal yang belum ideal + dugaan penyebab.
  6. Tindakan perbaikan.
  7. Hasil sesudah perbaikan.
  8. Vonis ("dinilai telah memenuhi kebutuhan fungsional ...").
  9. Jembatan ke tahap berikut ("... dapat digunakan pada tahap ...").
- **Varian per-temuan** (CODACY p.47–51): Temuan (kutipan pesan alat) →
  Analisis → Dampak → Mengapa ini masalah → rujukan ke subbab solusi.
- **Varian per-metrik** (ISYARAT p.62–84): definisi metrik → rumus →
  substitusi angka → hasil tebal → tafsiran satu kalimat.
- **Varian kegagalan** (GDD Tabel 4.4 p.74–76): test case dengan status Failed
  ditulis apa adanya + expected vs actual.

### P16. Paragraf analisis (4.7)

- **Urutan**: K1 klaim → K2 bukti angka (rujuk Tabel/Gambar) → K3 mekanisme
  penyebab → K4 kaitan ke tujuan/standar → K5 batasan.
- **Varian trade-off** (BYOM p.53–54): K1 kelemahan terukur (lebih lambat 14%)
  → K2 dekomposisi sumber (overhead mesin 0,0045 ms, sisanya *dynamic
  dispatch* dan penyalinan data) → K3 mengapa dapat diterima (target 2–5 FPS)
  → K4 validasi hipotesis desain.
- **Varian per tujuan** (BYOM 4.7.3): subjudul "Tujuan 1/2/3", tiap tujuan dua
  sampai tiga kalimat bukti + satu kalimat batasan.

### P17. Paragraf keterbatasan

- **Urutan**: K1 "Walaupun {capaian}, penelitian ini menyadari ..." → K2 status
  prototipe/PoC → K3 keterbatasan teknis → K4 keterbatasan metodologis (subjek,
  lingkungan) → K5 tahap lanjutan yang diperlukan.
- **Lokasi**: AFIB 4.7 d (p.125); GDD p.81; OFFLINE 4.7.5 (p.97–98).

### P18. Paragraf kesimpulan

- **Buku full** (AFIB p.127–128): par 1 urgensi masalah + capaian utama → par 2
  orisinalitas dan alur sistem → par 3 hasil kinerja vs target → par 4 hasil
  model → par 5 "seluruh tujuan yang dirumuskan pada Bab 1 telah tercapai" +
  status prototipe.
- **Progres** (OFFLINE p.101): kalimat pembuka "terdapat beberapa temuan
  penting ..." → "Pertama, ..." → "Kedua, ..." → "Ketiga, ..." Setiap temuan
  adalah wawasan teknis baru (bukan ulangan rencana) + implikasinya.
- **Progres** (GDD p.83–84): blok Pencapaian Tujuan → Batasan Penelitian &
  Progress → Kontribusi.

### P19. Paragraf saran

- **Progres**: setiap butir = pekerjaan tersisa + alasan + dampaknya terhadap
  evaluasi berikutnya (OFFLINE p.102–103 "Pertama ... Keempat").
- **Buku full**: setiap butir = arah riset di luar lingkup + standar/teknologi
  yang relevan (AFIB p.128–129: uji klinis, multi-kelas, PCB, keamanan, HL7
  FHIR).

---

## Bagian B — Urutan paragraf dalam subbab

| Subbab | Urutan paragraf yang lazim |
|---|---|
| 1.1 | P2 konteks → P2 urgensi → P3 kontras → P4 gap → P5 usulan → harapan |
| 1.2 | kalimat pengantar → daftar masalah (bernomor/berjudul) → (opsional) par penegasan |
| 1.3 | P6 → enumerate tujuan |
| 2.1 | par masalah utama → par per tantangan (urutan = 1.2) → tabel/gambar bukti + P11 → par penutup "fokus utama penelitian ini adalah ..." (AFIB p.32) |
| 2.2.x | P7 (± P10) |
| 2.3 | par pengantar 2.3 → P8 × n → tabel pembanding + P9 |
| 3.1 | par pengantar → daftar fitur solusi → par penutup "Dengan pendekatan tersebut, ..." (AFIB p.74) |
| 3.2.x | par pengantar subbab → P10 (gambar) → P13 × komponen → (P12 bila ada rumus) |
| akhir Bab 3 | par pengantar tahapan uji → P14 × jenis uji |
| 4.1–4.5 | par pengantar → butir/tabel → par alasan pemilihan |
| 4.6.x | P15 |
| 4.7 | par pengantar analisis → P16 × pilar/masalah/tujuan → P17 |
| 5.1 | P18 |
| 5.2 | par pengantar → P19 × butir |

---

## Bagian C — Kohesi antarparagraf

### C1. Pembuka paragraf yang merujuk ke paragraf sebelumnya

| Jenis | Bentuk | Fungsi |
|---|---|---|
| Anafora | "Hal ini ...", "Kondisi ini ...", "Permasalahan tersebut ...", "Ketidakstabilan tersebut ..." | meneruskan topik |
| Urutan | "Pertama ... Kedua ... Ketiga ... Terakhir ...", "Tantangan pertama ... kedua ..." | memecah daftar panjang menjadi paragraf |
| Kontras | "Namun, ...", "Di sisi lain, ...", "Sebaliknya, ..." | membuka sisi lain |
| Penambahan | "Selain itu, ...", "Lebih jauh, ..." | menambah argumen sejajar |
| Simpulan | "Dengan demikian, ...", "Oleh karena itu, ...", "Secara keseluruhan, ..." | menutup subbab |
| Rujuk elemen | "Berdasarkan Tabel X.Y, ...", "Gambar X.Y menunjukkan ..." | menjahit teks dengan gambar/tabel |

Frekuensi per 10.000 kata (rentang korpus): "Selain itu" 2,5–11,2; "Hal ini"
2,6–9,8; "Dengan demikian" 0,6–8,2; "Namun" 0,7–5,8; "Berdasarkan" 1,1–8,3;
"Oleh karena itu" 0–4,1. BYOM paling sering memakai "Pertama, ... Kedua, ..."
(6,9 dan 7,5), yaitu gaya enumerasi naratif yang rapi untuk Bab 3–4.

### C2. Aturan transisi yang terlihat

1. Paragraf terakhir subbab menyiapkan subbab berikutnya (OFFLINE 2.2 pembuka
   menyebut subbab yang akan datang, p.21).
2. Paragraf yang memperkenalkan gambar tidak memulai topik baru. Topik baru
   dibuka sesudah paragraf penjelas gambar selesai.
3. Ketika daftar butir (a, b, c) muncul, paragraf sesudahnya menjahit ulang
   butir-butir itu ("Dengan pendekatan tersebut, ...", "Skema ini dirancang
   ...", AFIB p.74 dan p.88).
4. Kalimat pertama setiap subbab 4.6.x hampir selalu kalimat tujuan uji. Ini
   membuat pembaca tahu apa yang dicari sebelum melihat bukti.

### C3. Pola yang perlu disesuaikan dengan aturan gaya kita

| Pola korpus | Versi untuk laporan kita |
|---|---|
| "... sebagai berikut:" lalu daftar (sangat sering) | Akhiri kalimat pengantar dengan titik ("... diuraikan pada butir berikut.") atau pakai "yaitu"/"meliputi" lalu `enumerate` |
| Tanda pisah panjang di tengah kalimat (AFIB p.78–81, BYOM p.10) | Ganti dengan koma + "yang/sehingga/karena" |
| Penomoran inline "(1) ..., (2) ..." (AFIB p.97) | Narasi "pertama ..., kedua ..." atau `enumerate` |
| Titik koma di butir (AFIB p.11, GDD p.77) | Koma + "dan", atau kalimat terpisah |
| Desimal titik "0.12°C", "2.31 FPS" (AFIB, BYOM) | Koma: 0,12 °C, 2,31 FPS |
