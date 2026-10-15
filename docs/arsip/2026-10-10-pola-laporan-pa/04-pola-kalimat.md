# 04 — Pola kalimat

Templat di bawah adalah ringkasan pola dalam kata-kata sendiri, dengan slot
`{...}`. Semua sudah mengikuti aturan gaya `laporan/CLAUDE.md`.

## 1. Ukuran kalimat

- Median 20–25 kata di hampir semua bab dan dokumen. Bab 3 paling pendek
  (18–21), karena kalimatnya prosedural.
- OFFLINE adalah pengecualian (Bab 4 median 28, Bab 5 median 35) dan memang
  terasa bertele-tele. Banyak kalimatnya menumpuk definisi istilah di tengah
  kalimat.
- Pegangan praktis: usahakan 15–30 kata, pecah bila lebih dari 35 kata atau
  bila ada lebih dari dua anak kalimat.

## 2. Pustaka kalimat-formula per fungsi

### 2.1 Bab 1

| Fungsi | Templat |
|---|---|
| Buka latar belakang | "{Teknologi/fenomena} telah berkembang menjadi {peran} yang semakin luas digunakan, khususnya untuk {kegunaan}." |
| Angka urgensi | "Data {sumber, tahun} memperkirakan {indikator} mencapai {angka}~[n]." |
| Kontras | "Saat ini, {solusi} telah menyediakan {fitur}. Namun, {kelemahan}~[n]." |
| Gap | "Kendati demikian, terdapat kesenjangan antara {A} dan {B}." |
| Usulan | "Merespons tantangan tersebut, penelitian ini mengusulkan {solusi} yang {ciri pembeda}." |
| Alasan metode | "{Metode} dipilih karena {alasan 1}, {alasan 2}, serta {alasan 3}." |
| Pengantar masalah | "Berdasarkan latar belakang tersebut, permasalahan dalam penelitian ini dirumuskan pada butir berikut." |
| Butir masalah bentuk tanya | "Bagaimana {merancang/membangun} {objek} agar {kriteria terukur}?" / "Seberapa {akurat/andal} {objek} dibandingkan {acuan}?" (AFIB p.23) |
| Butir masalah bentuk pernyataan berjudul | "**{Judul masalah}.** {Kondisi} menyebabkan {akibat}, sehingga {dampak}." (BYOM p.10–11, GDD p.12–13) |
| Klaim orisinalitas (wajib, Panduan) | "Penelitian proyek akhir ini mengajukan pendekatan baru untuk mengatasi {masalah} dengan {inti solusi}." |
| Butir tujuan | "{Kata kerja} {objek} {cara} dengan target {metrik} {pembanding} {angka}." (AFIB p.25) |
| Butir manfaat | "{Meningkatkan/Mempercepat/Memudahkan/Mengurangi} {hal} bagi {pihak} melalui {fitur}." |
| Sistematika | "Bab {N} {Judul}. Bab ini {membahas/menguraikan/menyajikan} {isi utama}, {isi kedua}, dan {isi ketiga}." |

### 2.2 Bab 2

| Fungsi | Templat |
|---|---|
| Definisi | "{Istilah} merupakan {kelas umum} yang {ciri pembeda}~[n]." |
| Daftar komponen teori | "{Istilah} terdiri atas {k1}, {k2}, dan {k3}." |
| Peran dalam penelitian (penutup 2.2.x) | "Dalam penelitian ini, {istilah} digunakan untuk {fungsi} pada {komponen}." |
| Pengantar gambar teori | "Gambar 2.X mengilustrasikan {konsep} yang terdiri atas {bagian}." |
| Buka penelitian terkait | "Penelitian ini bertujuan {tujuan mereka} dengan memanfaatkan {pendekatan}~[n]." |
| Metodologi paper | "Proses pengujian dilakukan dengan {cara} menggunakan {data/subjek}." |
| Hasil paper | "Hasil pengujian menunjukkan {metrik} sebesar {angka} {pembanding}." |
| Kesimpulan paper | "Penelitian ini menyimpulkan bahwa {temuan}, dan merekomendasikan {arah lanjut}." |
| Perbedaan | "Berbeda dengan penelitian tersebut yang berfokus pada {fokus mereka}, penelitian yang diusulkan menekankan {fokus kita}." |
| Pemosisian | "Berdasarkan tinjauan pada Tabel 2.X, penelitian ini tidak mengklaim {superioritas umum}, melainkan menawarkan {kontribusi spesifik}." (pola AFIB p.72) |

### 2.3 Bab 3

| Fungsi | Templat |
|---|---|
| Buka deskripsi solusi | "Untuk menjawab {masalah}, penelitian ini mengusulkan {solusi} yang diterapkan melalui pendekatan pada butir berikut." |
| Butir fitur solusi | "**{Nama fitur}.** {Fitur} {melakukan apa} sehingga {masalah X} dapat diatasi." |
| Pengantar desain | "Subbab ini menyajikan {rancangan} sebagai representasi {alur/hubungan} {sistem}." |
| Rujuk diagram | "Gambar 3.X menunjukkan hubungan antarkomponen utama yang membentuk sistem." |
| Komponen | "{Komponen} berfungsi sebagai {peran} yang {menerima apa} dan {menghasilkan apa}." |
| Alur flowchart | "Alur dimulai ketika {pemicu}. Sistem kemudian {langkah}. Jika {kondisi}, {cabang ya}. Jika tidak, {cabang tidak}." |
| Persamaan | "{Besaran} dirumuskan pada Persamaan (3.X)." lalu "dengan {simbol} adalah {arti}." |
| Alasan teknologi | "{Teknologi} dipilih karena {sifat} yang sesuai dengan kebutuhan {kebutuhan}." |
| Rencana uji | "Pengujian ini bertujuan memastikan {sifat} dengan target {metrik} {ambang}. Penetapan ambang tersebut didasarkan pada {acuan}." |

### 2.4 Bab 4

| Fungsi | Templat |
|---|---|
| Buka parameter | "Parameter eksperimen ditetapkan untuk mengukur ketercapaian tujuan penelitian secara objektif." |
| Pembatas progres | "Pada tahap progres ini, pengujian difokuskan pada {modul yang sudah jadi}, sedangkan {yang belum} akan diukur pada tahap berikutnya." |
| Alasan metrik (dengan sitasi) | "Metrik ini dipilih karena lazim digunakan pada penelitian {bidang}~[n], sehingga hasilnya dapat dibandingkan secara langsung." (BYOM p.41) |
| Karakteristik data | "Data yang digunakan terdiri atas {jenis 1} sebagai {fungsi} dan {jenis 2} sebagai {fungsi}." |
| Tempat | "Ujicoba dilaksanakan di {lokasi}. Lokasi ini dipilih karena {alasan}." |
| Waktu | "Ujicoba dilaksanakan pada {Sprint n} ({tanggal}) hingga {Sprint m} ({tanggal})." + "Pengambilan data dibatasi sampai {tanggal} menyesuaikan batas penyusunan dokumen progres." |
| Spesifikasi | "Spesifikasi peralatan disajikan pada Tabel 4.X dan Tabel 4.Y." |
| Tujuan uji | "Pengujian ini bertujuan memastikan {objek} mampu {kemampuan} sebelum {tahap berikut}." |
| Observasi | "Berdasarkan hasil pengamatan, {objek} berhasil {capaian} yang ditunjukkan oleh {bukti}." |
| Kondisi awal tak ideal | "Pada tahap awal, {gejala} masih ditemukan akibat {penyebab}." |
| Perbaikan | "Untuk mengatasinya, dilakukan {tindakan}, sehingga {hasil}." |
| Vonis | "Berdasarkan hasil tersebut, {objek} dinilai telah memenuhi {kriteria} dan dapat digunakan pada {tahap berikut}." |
| Hasil angka | "{Metrik} mencapai {angka}, {di atas/di bawah} target {ambang} yang ditetapkan pada Subbab 3.X." |
| Kegagalan jujur | "Dari {n} kasus uji, {p} berhasil dan {f} gagal. Kegagalan terjadi pada {area}, yang ditindaklanjuti dengan {tindakan}." |
| Trade-off | "{Pendekatan} lebih lambat {x}% dibanding {pembanding}. Selisih ini berasal dari {sumber}, bukan dari {yang dicurigai}, dan masih dapat diterima karena {konteks target}." |
| Analisis per tujuan | "Tujuan {n}, yaitu {ringkasan tujuan}, {tercapai/sebagian tercapai/belum tercapai} karena {bukti}." |

### 2.5 Bab 5

| Fungsi | Templat |
|---|---|
| Buka kesimpulan final | "Penelitian ini berhasil {merancang dan mengimplementasikan} {sistem} yang {menjawab masalah}." |
| Hasil vs tujuan | "Seluruh tujuan yang dirumuskan pada Bab 1 telah tercapai, ditunjukkan oleh {angka 1}, {angka 2}, dan {angka 3}." (pakai hanya bila benar) |
| Buka kesimpulan progres | "Berdasarkan perancangan, implementasi, dan eksperimen tahap progres, diperoleh beberapa temuan berikut." |
| Temuan | "Pertama, {temuan teknis} menunjukkan bahwa {wawasan}, sehingga {implikasi desain}." |
| Pengantar saran progres | "Saran untuk fase berikutnya disusun berdasarkan keterbatasan yang ditemukan pada tahap ini." |
| Butir saran | "**{Judul}.** {Kondisi sekarang}. Disarankan {tindakan} agar {manfaat}." |

## 3. Register "progres" vs "final"

| Kategori | Kata/frasa | Dipakai di |
|---|---|---|
| Rencana | akan, direncanakan, dirancang untuk, target | Bab 3 (semua dokumen), abstrak progres |
| Harapan | diharapkan, berpotensi | Bab 1 akhir latar belakang, abstrak progres |
| Lingkup progres | pada tahap progres ini, fase pertama, MVP, sebagian, belum, masih dalam tahap pengembangan | Bab 4–5 progres |
| Capaian | berhasil, terbukti, membuktikan, mencapai | Bab 4–5 (keduanya, lebih kuat di final) |
| Vonis | dinilai telah memenuhi, layak, tercapai / sebagian tercapai / belum tercapai | 4.6 akhir, 4.7 |
| Pengakuan | menyadari keterbatasan, belum melibatkan, belum dilakukan | 4.7 akhir, 5.1 progres |

Catatan kalibrasi klaim:
- "terbukti" hanya bila ada angka dan pembanding. AFIB memakai "terbukti
  robust" hanya dari tidak adanya *false positive* pada subjek sehat (p.122),
  klaim yang mudah diserang.
- "berhasil" tanpa angka di abstrak progres (CODACY p.3) terbaca kosong.
- Di progres, kalimat pengakuan justru menaikkan kredibilitas (GDD, BYOM).

## 4. Sitasi dalam kalimat

- Gaya numerik IEEE `[n]` dipakai 5/6 dokumen. ISYARAT memakai nama-tahun di
  teks tetapi daftar pustaka bernomor, tidak konsisten.
- Posisi: di akhir klausa yang didukung, sebelum titik ("... asimtomatik [1].").
  Banyak sumber dalam satu titik: "[11], [14]". OFFLINE menderetkan tujuh nomor
  berurutan satu per satu (p.25). Untuk deret berurutan, gaya IEEE yang lebih
  ringkas adalah rentang "[12]–[18]".
- Kalimat perbandingan antarkelompok studi mengumpulkan sitasi per kelompok
  ("... secara simulasi *offline* [3], [19] atau ... [2]", AFIB p.72).
- Bab 3–5 hampir tanpa sitasi. Pengecualian yang baik: sitasi untuk
  membenarkan metrik dan ambang (BYOM 4.1, p.41–42).
- Kutipan langsung bahasa Inggris dalam tanda petik dipakai OFFLINE (p.34–35)
  untuk klaim kunci paper. Menurut Panduan, kutipan langsung pendek ditulis
  miring dalam petik ganda + sitasi.

## 5. Istilah asing

Tiga gaya di korpus:

| Gaya | Contoh lokasi | Catatan |
|---|---|---|
| Istilah Inggris lalu definisi aposisi "yaitu ..." di tengah kalimat | OFFLINE p.11–12 (offline-first, latency, access point, fault tolerance) | sangat padat, membuat kalimat > 40 kata |
| Istilah Indonesia lalu padanan Inggris dalam kurung | AFIB ("kotak hitam (black-box)", "data sinyal mentah (raw signal data)") | rapi, mudah dibaca |
| Istilah Inggris lalu terjemahan dalam kurung | GDD, BYOM ("kontrol akses berbasis peran (role-based access control)") | rapi |

Aturan kita (`laporan/CLAUDE.md`): istilah teknis ditulis dalam bahasa
Inggris dan dimiringkan, terjemahan Indonesia boleh muncul **sekali** di dalam
kurung saat pertama disebut. Pengecualian kosakata yang ditulis tegak:
preprocessing, single-lead, flowchart, bufer. Untuk definisi panjang, pindahkan
ke kalimat sendiri, jangan diselipkan sebagai aposisi.

## 6. Angka dan satuan

- Korpus campur: AFIB menulis "98,04%" tetapi juga "0.12°C" dan "0.3%"; BYOM
  "2.31 FPS". Aturan kita: desimal koma, spasi antara angka dan satuan kecuali
  persen ("0,12 °C", "2,31 FPS", "98,04%").
- Rentang pakai tanda pisah pendek: "0,5–40 Hz", "10–30 detik".
- Angka hasil di teks selalu disertai rujukan sumbernya ("pada Tabel 4.X").

## 7. Kalimat caption

| Jenis | Pola | Contoh lokasi |
|---|---|---|
| Gambar rancangan | {Jenis diagram} {Objek} | "Desain Arsitektur Sistem", "Flowchart Sistem IoT", "Use Case Sistem ..." (AFIB) |
| Gambar layar | {Halaman/Layar} {Nama} | "Mockup Login", "Halaman Form Builder dengan Drag-and-Drop" (GDD) |
| Gambar uji | Pengujian {Objek} (a) {panel a}; (b) {panel b} | AFIB p.105–109 |
| Gambar pinjaman | {Objek} + baris Sumber terpisah | AFIB, OFFLINE |
| Tabel hasil | Hasil {Komparasi/Pengujian} {Objek} terhadap {Acuan} | "Hasil Komparasi Sensor ... terhadap Thermogun Medis" (AFIB) |
| Tabel struktur | Struktur {Tabel/Entitas} {Nama} | "Struktur Tabel sensor_data" (AFIB) |
| Tabel rencana | {Rencana pengukuran/Metrik} {Objek} | OFFLINE Tabel 3.1 |
| Tabel pembanding | Perbandingan Penelitian Terkait / State of the Art | 6/6 |

Caption berupa frasa benda, tanpa titik akhir, tanpa kata kerja.
