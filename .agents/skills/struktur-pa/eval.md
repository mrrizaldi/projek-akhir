# Eval: struktur-pa

Penilai: model berbeda dari penulis. Skor 0-10, lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah (tanpa akses repo, fakta repo ada
di tugas) dan mengembalikan rencana suntingan, LaTeX, tabel temuan, atau
pesan ke user. Angka keluaran perintah boleh `[N]` karena peserta tidak
menjalankan perintah. Yang dinilai: perintah pemeriksaannya disebut, dan
hasil yang belum diamati tidak ditulis seolah sudah terjadi.

## Tugas uji

1. User: "tambah 4.8 Dokumentasi Penelitian buat foto-foto, terus
   Keterbatasan pindahin ke Bab 5 aja biar Bab 4 ga kepanjangan". Fakta:
   buku full, Bab 4 sudah punya 4.7.5 Keterbatasan dan Status Proof of
   Concept, foto rakitan dan elektroda masih placeholder. Tanggapi.
2. Audit benang merah. Fakta: Rencana Pengujian Bab 3 memuat target recall
   kelas aritmia "tinggi", konsumsi daya "hemat", latensi *end-to-end*
   median ≤ 2 detik, dan uji putus koneksi 3 skenario. Bab 4 melaporkan
   recall 0,6996 pada DS2, latensi median 939 dan 1.108 ms (dua ulangan,
   *replay*), daya belum diukur, dan uji putus koneksi hanya 1 skenario
   tanpa penjelasan. Pembanding yang tersedia untuk target indikatif:
   recall kelas aritmia *inter-patient* biner pada penelitian terkait tidak
   ada, sedangkan untuk daya ada arus puncak 8,6 mA (28,38 mW) pada
   Chowdhury dan Chattopadhyay 2023. Draf 5.1 berbunyi "seluruh tujuan yang dirumuskan pada
   Bab 1 telah tercapai". Draf juga memakai judul "4.6.1 Jalur
   Preprocessing *Real-Time* (Tujuan 1)" dan "4.7.1 Ketercapaian Tujuan 1",
   pembuka 4.6.2 berbunyi "Subbab ini menjawab Tujuan 2 pada
   Subbab~\ref{sec:tujuan}, yaitu ...", 5.1 dibuka "Tujuan pertama tercapai
   sebagian.", dan pembuka 4.6 memuat "Tabel 4.6 Perubahan rancangan dari
   proposal" (aspek, proposal, realisasi, alasan). Draf Bab 4 dibuka
   paragraf "Bab ini memaparkan eksperimen untuk memvalidasi tiga jalur
   yang dirancang pada Bab~\ref{chap:deskripsi-sistem}, ..." sebelum 4.1,
   subbab Tujuan Bab 1 ditutup kalimat "Kriteria keberhasilan setiap tujuan
   dirumuskan pada Subbab~\ref{sec:rencana-pengujian}, dan ketercapaiannya
   dianalisis pada Bab~\ref{chap:eksperimen}." sesudah daftar tujuan, dan
   4.6.1 memuat "Sumber \textit{replay} dipilih dari menu Sumber sinyal
   (Subbab~\ref{subsec:antarmuka-perangkat})." Tulis tabel per tujuan
   (target, hasil, status, yang harus diubah), suntingan kalimat 5.1, dan
   suntingan judul, pembuka 4.6.2, tabel perubahan itu, pembuka Bab 4,
   penutup Tujuan, dan kalimat 4.6.1.
3. Pasang gambar *state machine* gerbang kalibrasi di 4.6.3 a. Fakta:
   keadaan `calibrating` → `running`, syarat masuk RR 10 detak berturut
   dalam rentang 300–2.000 ms dan ayunan ADC di atas ambang, kembali ke
   `calibrating` bila ayunan jatuh di bawah ambang 5 detik, sumber kebenaran
   `firmware/src/ecg_mqtt.cpp`. Tulis paragraf pengantar, blok gambar, dan
   paragraf penjelas.
4. Draf abstrak buku full: "Penelitian ini diharapkan menghasilkan
   prototipe monitoring aritmia berbasis TinyML di ESP32-S3 yang hemat daya
   dan andal. Pengujian direncanakan pada data MIT-BIH dan sinyal tubuh."
   Bab 1.4 draf: "Manfaat yang diharapkan dari proposal ini adalah ...".
   Bab 3.2 draf: "Desain PCB rev1 disusun oleh rekan, sedangkan revisi rev2
   sedang dikerjakan. Revisi rev2 memindahkan buzzer ke GPIO 13 dan
   mencatu semua modul GPIO dari 3V3." 
   Fakta Bab 4: F1 0,6594 dan AUC 0,9334 pada DS2 *inter-patient*, INT8
   22,94 KB, 26,6 ms per detak, PDSR 100% dan 99,2%, daya belum diukur.
   Sebutkan yang harus diubah dan tulis ulang abstraknya.
5. Pesan akhir ke user setelah tugas 2–4, termasuk pemeriksaan sebelum
   kumpul.

## Rubrik (tiap butir 2 poin)

- A. Tugas 1: kerangka 4.1–4.7 dipertahankan, Keterbatasan tetap di 4.7
  (Bab 5 tanpa temuan baru), 4.8 tidak ditambah diam-diam melainkan
  dijelaskan sebagai opsional atas keputusan user dengan rekomendasi
  (foto dokumentasi masuk 4.5 atau lampiran), dan placeholder foto tidak
  dibuatkan gambar.
- B. Tugas 2: target "tinggi" dan "hemat" keduanya berstatus "Belum dapat
  divonis (target tanpa angka)" dan diberi perlakuan (angka atau indikatif
  + pembanding), daya ditulis belum diukur, skenario putus koneksi yang hilang
  ditulis eksplisit belum dilakukan + perlu alasan, dan "seluruh tujuan
  tercapai" dihapus atau dibatasi sesuai tabel. Judul dan kalimat diganti
  menjadi nama isi tanpa label bernomor ("Jalur Preprocessing *Real-Time*",
  "Analisis Jalur ...", "Subbab ini memaparkan hasil ..."), 5.1 tidak
  dibuka "Tujuan pertama", kolom tabel ketercapaian tanpa "Tujuan 1", dan
  tabel perubahan dari proposal dihapus (bukan dipertahankan atau dipindah
  ke lampiran). Paragraf pembuka Bab 4 dihapus seluruhnya (bab langsung ke
  4.1, tidak diganti paragraf pembuka lain), kalimat sesudah daftar Tujuan
  dihapus, dan "(Subbab~\ref{...})" dibuang dari 4.6.1 tanpa menyisakan
  penunjuk bab/subbab lain di kalimat laporan (`.tex`) yang ditulis.
  Pesan, rencana, dan catatan ke user boleh menyebut nomor bab dan subbab.
- C. Tugas 3: tidak ada diagram buatan sendiri (tanpa TikZ/Mermaid/SVG),
  kartu spesifikasi lengkap (jenis, pesan, elemen, alur baca, teks, bahan
  repo, ukuran) di komentar `%`, `\label` dan caption final, bagian
  pembacaan gambar di penjelas hanya menyebut elemen/label/alur yang ada
  di kartu (kalimat makna penutup boleh mengaitkan ke tujuan, tanpa penunjuk subbab),
  dan posisi gambar tidak disebut
  "di atas/di bawah" ("di atas ambang" untuk besaran tidak dihitung).
- D. Tugas 4: abstrak ditulis ulang sebagai hasil dengan angka yang sama
  persis dengan fakta Bab 4, "diharapkan"/"direncanakan" dan "proposal ini"
  dihapus, daya ditulis belum diukur (tidak diklaim hemat), dan disebut
  bahwa *Abstract* Inggris harus memuat angka yang sama. Draf Bab 3.2 diganti
  rancangan akhir tanpa rev1/rev2 dan tanpa "disusun oleh rekan"
  (mis. "Seluruh komponen yang menyentuh GPIO dicatu dari 3V3 ..."), dan
  informasi pin akhir (buzzer GPIO 13) tetap ada.
- E. Tugas 5: menyebut `make pdf` + `undefined`, grep frasa progres dan
  "proposal ini", grep placeholder, `cek_tabel.py`, dan tidak menulis
  hasil yang belum dijalankan sebagai sukses atau 0.

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-15 | sonnet | haiku | 9/10 | C: kalimat makna penutup ("klasifikasi hanya dijalankan ...", rujukan subbab) dinilai di luar kartu. Di luar rubrik: 5.1 usulan tanpa rujukan ke Tujuan; keterangan dataset PDSR di abstrak. SKILL.md aturan 9 + rubrik C: pembacaan = elemen kartu, makna penutup boleh mengait keluar |
| 2026-10-15 | sonnet | haiku | 8/10 | B: "hemat" diberi "Belum tercapai" tanpa ditandai tak bisa divonis; C: penilai menghitung "di atas ambang" sebagai larangan posisi. SKILL.md aturan 3: status "Belum dapat divonis (target tanpa angka)"; aturan 8: larangan hanya untuk posisi; rubrik C diperjelas; daftar periksa: klaim suntingan konsisten |
| 2026-10-15 | sonnet | haiku | **10/10** | LULUS putaran 3. Di luar rubrik: teks kartu vs paragraf isinya sama tetapi tidak identik kata per kata; dicatat, tidak mengubah skill |
| 2026-10-19 | sonnet | haiku | 8/10 | Aturan 2 diganti: judul/kalimat menurut isi tanpa "Tujuan N", tanpa tabel perubahan dari proposal, tanpa pembuka meta subbab (gaya AFIB, keputusan user). Tugas 2 dan rubrik B ditambah kasus itu; B 2/2. A: 4.8 dijawab "boleh" tanpa rekomendasi 4.5/lampiran; C: kalimat fungsi diselipkan di pembacaan gambar. Aturan 1 (4.8 sebagai opsi + rekomendasi) dan 9 (satu kalimat makna di akhir, kata sama dengan kartu) diperjelas |
| 2026-10-19 | sonnet | haiku | **10/10** | LULUS putaran 2. Di luar rubrik: "tabel di atas" di draf 5.1, abstrak belum memuat latensi pipeline |
| 2026-10-19 | sonnet | haiku | 9/10 | Aturan 4 ditambah larangan riwayat revisi (rev1/rev2, "disusun oleh rekan"), N-REVISI. Tugas 4 dan rubrik D ditambah draf Bab 3.2; D 2/2. C: kartu tanpa baris Ukuran; templat aturan 9 memang tanpa baris Lokasi/Ukuran, ditambahkan |
| 2026-10-19 | sonnet | haiku | 9/10 | BERHENTI (skor tidak naik). D 2/2 kedua putaran: aturan baru stabil. B: pembanding "target indikatif" tidak dinamai, padahal soal tugas 2 tidak memberi nama pembanding. Akar masalah di soal, bukan skill. Usulan: tambah fakta pembanding ke tugas 2 lalu satu putaran ulang, atau terima 9/10 |
| 2026-10-20 | sonnet | haiku | 9/10 | Aturan 1 (tanpa paragraf pembuka di semua bab) dan aturan 11 (tanpa penunjuk bab/subbab/butir, Tujuan berakhir di daftar) ditambah; tugas 2 dan rubrik B ditambah kasusnya. Ketiga suntingan baru benar. B: penilai menghitung nomor bab di pesan ke user sebagai penunjuk (rubrik terlalu luas, aturan hanya untuk teks tercetak), dan pembanding target indikatif tidak dinamai karena soal tidak memberinya. Rubrik B dipersempit ke `.tex`, tugas 2 diberi fakta pembanding |
| 2026-10-20 | sonnet | haiku | **10/10** | LULUS putaran 2. Ketiga suntingan baru (pembuka Bab 4, penutup Tujuan, ref 4.6.1) benar dan .tex tanpa penunjuk. Di luar rubrik: kartu Ukuran vs kotak placeholder tidak sama, abstrak tanpa kondisi PDSR dan tanpa latensi |
