# 07 — Adaptasi pola ke PA kita

PA kita: *Implementasi Sistem Monitoring Detak Jantung Kontinu Berbasis IoT
Edge Computing untuk Deteksi Dini Aritmia*. ESP32-S3 + AD8232,
*preprocessing* dan CNN INT8 di perangkat, *pipeline* MQTT resilien ke
ThingsBoard.

File 01–06 adalah pola korpus apa adanya. File ini menerangkan **pola mana
yang dipakai langsung, mana yang harus diubah, dan apa yang perlu ditambah**
karena PA kita berbeda jauh dari korpus. Rencana rinci Bab 4 ada di
[08-bab4-pa-kita.md](08-bab4-pa-kita.md).

Fakta proyek diambil 10 Okt 2026 dari `model/CLAUDE.md`, `README.md`,
`laporan/proposal-pa/`, `model/docs/`, memori PCB. Cek ulang sebelum menulis.

---

## 1. Seberapa beda PA kita dari korpus

| Dimensi | Korpus | PA kita | Akibat bagi laporan |
|---|---|---|---|
| Jenis kontribusi | 5 dari 6 software murni (aplikasi, UX, refactoring, backend). Hanya AFIB yang punya hardware | ML + embedded + IoT sekaligus | Pola software tidak cukup. Pola hardware praktis hanya dari AFIB |
| Model ML | AFIB: SVM, pelaporan tipis. Lainnya tidak melatih model | CNN dua cabang 6.417 param, inter-patient, ablasi multi-seed (Fase A–G), PTQ INT8 | Butuh pola pelaporan eksperimen ML yang **lebih ketat** dari korpus |
| Jumlah eksperimen | 3–7 uji per laporan | Fase 0–8, 6b, 6c, A–G, HW-1 sampai HW-7 | Bab 4 akan jauh lebih besar dari rata-rata korpus. Perlu pengelompokan yang tegas (08 §2) |
| Kebenaran deploy | tidak ada | golden reference C vs Python, cocok per beat | Pola baru: tabel kesetaraan PC vs perangkat (08) |
| Data subjek manusia | AFIB subjek sehat, ISYARAT wawancara | rekaman AD8232 pada subjek sehat | Perlu Batasan dan catatan etika yang tegas |
| Ketergantungan fisik | AFIB saja | elektroda, header modul, PCB rev1 → rev2 | Uji akuisisi sempat tertahan masalah fisik (sambungan header modul) sebelum tervalidasi. Pola progres yang jujur (01 §4) tetap wajib |
| Pembimbing | — | **Pembimbing 1 dan 2 sama dengan AFIB** | AFIB adalah pendahulu langsung yang sudah dibaca pembimbing. Lihat §3 |
| Produk bersama | OFFLINE dan GDD adalah dua PA pada satu produk (Work Fusion) | **PA individu**. PCB rev1 dirancang rekan, bukan penulis | Tidak perlu pembagian lingkup antarpenulis. Cukup kredit untuk rancangan PCB (§5) |

## 2. Peta analog: bagian PA kita → contoh korpus → modifikasi

| Bagian PA kita | Analog terdekat | Pola yang diambil | Modifikasi untuk PA kita |
|---|---|---|---|
| Rancangan perangkat keras | AFIB 3.2.2 (komponen a–e + gambar rancangan) | daftar komponen + fungsi masing-masing | tambah tabel pin map, jalur daya, dan riwayat versi (breadboard → PCB rev1 → rev2) |
| Uji sensor/akuisisi | AFIB 4.6.1 dan 4.6.3 | skematik → uji fungsional → kondisi awal belum ideal + perbaikan → validasi kuantitatif terhadap alat acuan | wasit kualitas sinyal = **ayunan ADC absolut** dalam counts dan mV, bukan flag LO (jebakan di `model/CLAUDE.md`). Acuan HR dari alat lain bila ada (pola Tabel 4.5 AFIB) |
| Data latih vs data perangkat | AFIB 4.2 (data latih, data uji real-time, penyelarasan fitur) | tiga bagian yang sama | "penyelarasan" kita jauh lebih kuat: filter kausal identik, *group delay* +4, R di indeks 132, golden test |
| Evaluasi model | ISYARAT (rumus + substitusi), CODACY (sebelum/sesudah), BYOM (metrik dibenarkan dengan sitasi) | definisi metrik → angka → tafsir | inter-patient, threshold dari VAL, **tanpa accuracy**, per kelas AAMI, per pasien, rerata ± rentang 3 seed |
| Ablasi dan keputusan desain | BYOM 4.7.1 (trade-off terukur) | kelemahan terukur → sumbernya → kenapa diterima | tabel ablasi + tabel keputusan terkunci (LR 1e-3 dipertahankan walau S turun, dilaporkan) |
| Kuantisasi | CODACY (tabel sebelum/sesudah) | baseline vs sesudah + selisih | float32 vs INT8 per metrik + cerita varian deploy (op MEAN) |
| Kesetaraan C vs Python | tidak ada | — | pola baru (08 §4.6.2 f) |
| Pipeline resilien | OFFLINE 4.6.2–4.6.4 (uji offline, sync latar belakang, log retry) + AFIB 4.6.5 (tabel PDSR) | skenario per kondisi jaringan + log sebagai bukti | 6 target dari tabel rencana Bab 3, 2 ulangan, dekomposisi latensi |
| Arsitektur edge-cloud | BYOM 3.2 | high-level → komponen → alur bernomor | sudah ada di proposal, sinkronkan dengan realisasi |
| Dashboard | AFIB 4.6.6 | tangkapan layar + 3 poin hasil | sama |
| Ketercapaian | GDD Tabel 4.5 + BYOM 4.7.3 | status per tujuan + justifikasi | dipakai penuh (08 §6) |
| Temuan progres | OFFLINE 5.1 ("Pertama/Kedua/Ketiga") | temuan teknis yang belum banyak diperhatikan | bahan sangat kaya di `model/CLAUDE.md` bagian Jebakan (§4 Bab 5) |

## 3. Posisi terhadap AFIB (pembimbing sama)

Ini penyesuaian yang paling menentukan.

**Format yang sudah diterima pembimbing kita (terlihat di AFIB), ditiru:**
- Bab 1 punya **Batasan Masalah** (AFIB 1.3 a–f). Proposal kita belum punya.
- Butir **Tujuan bertarget angka** (AFIB 1.4). Target kita saat ini baru ada
  di tabel rencana Bab 3.
- **Manfaat per pemangku kepentingan** (tenaga medis, masyarakat, mahasiswa).
- Tabel State of the Art dengan baris terakhir *proposed system*. Sudah ada di
  proposal kita (Tabel Perbandingan Penelitian Terkait, 13 baris).
- Bab 4.1 dikelompokkan per kategori (a–d), 4.7 ditutup subbab
  "Keterbatasan Sistem dan Identifikasi *Proof of Concept*".

**Kelemahan AFIB yang pasti diingat pembimbing, dihindari (06 §D):**
- Target di Tujuan yang tidak diukur dengan metrik yang dijanjikan.
- Confusion matrix yang dideskripsikan kira-kira.
- Hanya melaporkan akurasi.
- Klaim "seluruh tujuan tercapai" tanpa tabel ketercapaian.

**Risiko terbesar: angka kita terlihat lebih jelek dari AFIB.** AFIB
melaporkan akurasi 98,04%. Kita melaporkan F1 sekitar 0,66 dan AUC sekitar
0,93. Tanpa penjelasan, penguji membaca ini sebagai kemunduran. Cara
mencegahnya:

1. Di Bab 2, tambah kolom **"Protokol evaluasi"** pada tabel perbandingan, atau
   tabel kecil tersendiri. Isinya pembagian data (per beat vs inter-patient),
   unit (beat vs window), kelas, dan metrik. Proposal kita sudah menyinggung
   ini untuk dua paper (pembagian per detak = metrik berpotensi optimistis).
   Jadikan sistematis untuk semua baris.
2. Di Bab 4.1, tulis alasan **accuracy tidak dipakai**. Dengan 89,7% beat
   Normal, menebak "Normal" terus sudah memberi accuracy sekitar 0,89.
   Keputusan ini sudah terkunci di `model/CLAUDE.md`.
3. Di Bab 4.7, satu paragraf P16 (03) yang membandingkan secara adil:
   protokol berbeda, angka tidak bisa dibandingkan langsung.

**Nada:** "melanjutkan penelitian terdahulu di laboratorium dan bimbingan
yang sama", bukan menjatuhkan. Pakai pola pemosisian AFIB sendiri (P9 di 03).
Setiap keunggulan yang diklaim atas AFIB harus punya angka di Bab 4:

| Klaim beda dari AFIB | Bukti yang harus ada di Bab 4 |
|---|---|
| Inferensi di perangkat, bukan di cloud | latensi inferensi per detak dan duty cycle di ESP32-S3 |
| Evaluasi inter-patient | tabel split DS1/DS2 + angka DS2 dibuka sekali |
| Preprocessing di MCU setara dengan pelatihan | tabel kesetaraan golden (C vs Python) |
| Pipeline tahan putus koneksi | PDSR, data hilang, waktu *flush* pada skenario putus paksa |
| Model kecil | ukuran INT8 dan RAM/arena |

## 4. Penyesuaian per bab

### Bab 1

| Subbab | Status di proposal | Penyesuaian untuk progres |
|---|---|---|
| 1.1 | ada | cek ulang angka epidemiologi + sitasi |
| 1.2 | 3 pertanyaan "Bagaimana ...?" (pola AFIB) | pertahankan |
| **Batasan Masalah** | **tidak ada** | **tambah** (draf di bawah) |
| 1.3 | klaim orisinalitas + 3 tujuan | tambahkan kriteria terukur per tujuan, atau rujukan eksplisit ke tabel rencana Bab 3 |
| 1.4 | 3 butir umum | pertimbangkan pola per pemangku (gaya AFIB) |
| 1.5 | rencana | tulis ulang Bab 4–5 sesuai realisasi tahap progres |

Draf butir Batasan Masalah, semua diturunkan dari keputusan yang sudah
terkunci. Disetujui user 10 Okt 2026 (tidak ada keberatan). Keamanan
transport **tidak dibahas sama sekali** di laporan, termasuk tidak dijadikan
butir batasan.
1. Klasifikasi biner Normal/Aritmia. Penamaan jenis aritmia (V/S/F) tidak
   termasuk keluaran, karena aturan tahap 2 tidak lolos sertifikasi VAL.
2. Data latih MIT-BIH Arrhythmia Database (mitdb), satu sadapan MLII, dibagi
   inter-patient DS1/DS2. svdb dan incartdb hanya untuk uji lintas basis data.
3. Akuisisi *single-lead* AD8232, konfigurasi Lead II, elektroda *wet-gel*.
4. Pengujian perangkat pada subjek sehat yang dianonimkan, dalam lingkungan
   laboratorium non-klinis. Bukan alat diagnosis dan bukan uji klinis (pola
   AFIB 1.3 f).
5. Ketahanan *pipeline* diuji dalam batas kapasitas *ring buffer* PSRAM.
   Kehilangan daya perangkat di luar cakupan (catatan kaki bab3 proposal).
6. Daya diukur, tidak dioptimasi. Rangkaian baterai/*power path* di luar
   lingkup tahap ini (doc rev2 §6).

### Bab 2

- Tabel Perbandingan Penelitian Terkait: tambah kolom/tabel Protokol Evaluasi
  (§3).
- **Perbarui baris "Proposed System"**. Klaim "< 20 KB" sudah usang: model
  deploy 22,9 KB dengan batas yang disetujui 25 KB. Klaim "hemat daya" baru
  boleh tetap setelah daya diukur (pengukuran daya belum dijalankan).
- Teori yang tumbuh karena realisasi dan layak ditambah: skema inter-patient
  de Chazal + kelas AAMI, metrik evaluasi (recall/precision/F1/AUC dan alasan
  menolak accuracy), augmentasi jitter (Dias 2021, diadopsi karena paper
  mengablasinya). TFT, buzzer, dan tombol cukup disebut di rancangan perangkat
  keras, tidak perlu subbab teori, kecuali dievaluasi.
- Pola P7 (03): setiap teori ditutup "Dalam penelitian ini, ...". Teori alat
  bantu (IDE, editor) jangan dijadikan subbab (anti-pola E6).

### Bab 3

- **Tambah subbab Perancangan Perangkat Keras.** Proposal belum punya, AFIB
  punya (3.2.2), dan proyek kita jelas proyek perangkat keras. Isinya:
  diagram blok, tabel pin map (ESP32-S3 ↔ AD8232/LO±, TFT, buzzer, tombol,
  INA219), jalur daya, riwayat versi (breadboard → PCB rev1 → rev2) beserta
  siapa perancangnya. Pin map berbeda antara breadboard dan PCB (memori PCB
  rev1), jadi sebutkan versi mana yang dipakai di tiap uji.
- Biarkan kala rencana (01 §6). **Jangan diam-diam menulis ulang Bab 3**
  agar cocok dengan hasil. Perubahan rancangan dicatat sebagai tabel di Bab 4
  (08 §4.6 pembuka). Contoh perubahan yang sudah terjadi: window 250 → 256
  sampel, threshold 0,35 → 0,80, batas ukuran model 20 → 25 KB,
  GlobalAveragePooling → DepthwiseConv1D pada varian deploy, augmentasi jitter
  yang tidak ada di rancangan awal.
- Tabel rencana pengujian (model dan *pipeline*) sudah kuat. Pertahankan,
  karena itu kontrak yang dijawab Bab 4.

### Bab 5 (versi progres)

Kandidat **temuan** bergaya OFFLINE 5.1. Semuanya sudah terdokumentasi dengan
angka di `model/CLAUDE.md`:
1. Ketidakcocokan diam-diam antara TFLite dan TFLite Micro (op MEAN, PC 0,973
   vs perangkat 0,336, tanpa error) hanya tertangkap karena ada golden
   reference. Pelajarannya: uji kesetaraan PC ↔ perangkat bukan formalitas.
2. Augmentasi jitter yang meniru galat detektor menaikkan F1 pada data
   **bersih**. Jadi augmentasi itu bekerja sebagai regularisasi, bukan sekadar
   simulasi kondisi lapangan.
3. Sekitar 89% latensi *end-to-end* ada di sisi alat (kadens deteksi), bukan
   di jaringan/broker. Arah optimasi berikutnya ada di firmware.
4. Telemetri akuisisi bisa menipu (LO 0% tanpa sinyal). Ayunan ADC absolut
   adalah wasit yang benar.
5. Model produksi ternyata hasil satu epoch. Jadwal latih harus ditinjau setiap
   ukuran data berubah.

Pilih 3–4 yang paling relevan dengan tujuan. **Saran** = roadmap konkret:
akuisisi pada PCB rev2, pengukuran daya (rancangan:
`model/docs/arsip/2026-09-16-daya-design.md`), gerbang penuh dengan sinyal tubuh, pertukaran LR (S vs F) yang dibuka lagi bila S tidak lagi jadi
fokus, kernel ESP-NN bila daya jadi kendala.

## 5. Hal khusus hardware/biomedis yang tidak ada di korpus software

| Hal | Di mana ditulis | Kenapa |
|---|---|---|
| Identitas perangkat: board id `4d_systems_esp32s3_gen4_r8n16`, versi PCB, versi firmware/model (commit) di setiap hasil | 4.5 + caption/teks hasil | hasil hardware tidak bisa diulang tanpa versi |
| Konversi satuan ADC → mV (0,757 mV/count, gain AD8232 sekitar 1100) | 4.2 atau 4.6 akuisisi | amplitudo dalam counts tidak bermakna bagi penguji |
| Kondisi fisik uji: Lead II, stabilisasi 10–15 menit, subjek diam, RSSI WiFi | 4.2/4.3 | variabel yang memengaruhi hasil |
| Validitas alat ukur: reset DTR saat membuka serial, resolusi `time()`, ohmmeter di rangkaian bertegangan | 4.5 (subbagian "validitas pengukuran") atau 4.6 | menunjukkan angka dijaga dari galat alat. Penguji teknik menghargai ini |
| Etika subjek: subjek **anonim** (kode S01, S02, ...), persetujuan, bukan alat medis | Batasan + 4.2. Nama, foto wajah, dan data identitas tidak dimuat, termasuk di lampiran | data manusia |
| Kredit rancangan PCB rev1 oleh rekan (PA tetap individu) | Bab 3 (perangkat keras, satu kalimat sumber rancangan), Kata Pengantar di buku | jujur soal asal artefak tanpa mengaburkan bahwa PA ini individu |
| Uji tanpa subjek (replay golden) sebagai pengganti sah saat elektroda buntu | 4.2 (jenis data) + 4.6 | pola "uji tetap jalan walau satu variabel fisik buntu" |

## 6. Keputusan

### Sudah diputuskan (user, 10 Okt 2026)

| Hal | Keputusan | Akibat |
|---|---|---|
| Jenis PA | individu | tidak ada pembagian lingkup antarpenulis; PCB rev1 cukup diberi kredit (§5) |
| Subjek uji | belum pasti, **anonim** | kode subjek S01, S02, ...; tanpa identitas di teks, gambar, dan lampiran |
| Tempat uji | lab (kemungkinan besar) | 4.3 ditulis "laboratorium", nama lab diisi saat pasti |
| Keamanan transport (TLS/MQTTS) | **tidak dibahas sama sekali** | tidak masuk Batasan, Keterbatasan, maupun Saran |
| Lokasi projek LaTeX | **satu projek: `laporan/buku-pa`** untuk progres dan buku | progres = tahap awal buku yang sama (01 §7 jadi penyuntingan di tempat, bukan pindah projek) |
| Butir Batasan Masalah 1–6 | dipakai sebagai draf | |

Akibat teknis keputusan satu projek:
- `laporan/buku-pa` sudah A4 `twoside,openright`, cocok dengan pola bab di
  halaman ganjil (01 §1).
- Label sampul "PROGRES" dan front matter progres vs buku perlu satu sakelar
  di `main.tex`. Mengubah berkas di `laporan/` tetap perlu konfirmasi saat
  dikerjakan.
- `scripts/export_artifacts.sh --laporan` saat ini menyalin ke
  `proposal-pa/gambar`. Nanti perlu diarahkan ke `buku-pa/gambar`.

### Masih terbuka

1. Tanggal potong data progres (untuk 4.4 dan kalimat pembatas lingkup).
2. Jumlah subjek dan ada/tidaknya alat acuan HR (oksimeter atau jam pintar)
   untuk pola validasi AFIB Tabel 4.5.
3. Nama lab.
4. Templat front matter progres yang berlaku tahun ini.
