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
   tanpa penjelasan. Draf 5.1 berbunyi "seluruh tujuan yang dirumuskan pada
   Bab 1 telah tercapai". Tulis tabel per tujuan (target, hasil, status,
   yang harus diubah) dan suntingan kalimat 5.1.
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
- B. Tugas 2: target "tinggi" dan "hemat" ditandai tidak bisa divonis dan
  diberi perlakuan (angka atau indikatif + pembanding), daya ditulis belum
  diukur (Sebagian tercapai / Belum), skenario putus koneksi yang hilang
  ditulis eksplisit belum dilakukan + perlu alasan, dan "seluruh tujuan
  tercapai" dihapus atau dibatasi sesuai tabel.
- C. Tugas 3: tidak ada diagram buatan sendiri (tanpa TikZ/Mermaid/SVG),
  kartu spesifikasi lengkap (jenis, pesan, elemen, alur baca, teks, bahan
  repo, ukuran) di komentar `%`, `\label` dan caption final, penjelas hanya
  menyebut elemen yang ada di kartu, dan tidak memakai "di atas/di bawah".
- D. Tugas 4: abstrak ditulis ulang sebagai hasil dengan angka yang sama
  persis dengan fakta Bab 4, "diharapkan"/"direncanakan" dan "proposal ini"
  dihapus, daya ditulis belum diukur (tidak diklaim hemat), dan disebut
  bahwa *Abstract* Inggris harus memuat angka yang sama.
- E. Tugas 5: menyebut `make pdf` + `undefined`, grep frasa progres dan
  "proposal ini", grep placeholder, `cek_tabel.py`, dan tidak menulis
  hasil yang belum dijalankan sebagai sukses atau 0.

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-15 | -- | -- | belum dijalankan | skill baru |
