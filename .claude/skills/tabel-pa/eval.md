# Eval: tabel-pa

Penilai: model berbeda dari penulis. Skor 0-10, lulus hanya 10/10.
Penulis menerima SKILL.md + `referensi/templat.md` + tugas di bawah (tanpa
akses repo, fakta repo ada di tugas) dan mengembalikan LaTeX tabel, paragraf
yang berubah, serta pesan akhir ke user. Karena peserta tidak menjalankan
perintah, angka keluaran boleh `[N]`. Yang dinilai: perintah pemeriksaannya
disebut, dan hasil yang belum diamati tidak ditulis seolah sudah terjadi.

## Tugas uji

1. Rombak `tab:hasil-ds2`. Isi sekarang empat kolom Sel | Jumlah Detak |
   Metrik | Nilai dengan baris TP 3.813 | Recall 0,6996, FN 1.637 |
   Precision 0,6235, FP 2.302 | Specificity 0,9479, TN 41.904 | F1 0,6594,
   lalu dua baris dengan dua sel pertama kosong: AUC 0,9334 dan "Accuracy
   (bukan acuan)" 0,9207. Fakta: subbab yang sama sudah memuat gambar
   `fig:cm-ds2` berisi *confusion matrix* DS2 untuk *float32* dan INT8.
2. Rombak baris `tab:target-pipeline` berikut (kolom Aspek | Metrik | Target
   | Ulangan 1 | Ulangan 2 | Status): Latensi end-to-end | Median | ≤ 2 detik
   | 939 ms | 1.108 ms | Terpenuhi. Latensi end-to-end | p95 | Dilaporkan,
   acuan ≤ 2 detik | 1.404 ms | 3.304 ms | Tidak stabil. Pemulihan bufer |
   Durasi flush | ≤ 60 detik | ≤ 24,6 detik (uji yang sama) | Tidak diulang
   | Terpenuhi. Deduplikasi cloud | Timestamp ganda | Duplikat QoS 1
   dikenali dan diabaikan | 0 | Sama | Terpenuhi. Fakta: p95 tidak punya
   target pada rencana pengujian Bab 3, dan skenario putus koneksi
   dijalankan sekali.
3. Sel kolom "Alasan dan Acuan" pada `tab:parameter-eksperimen` baris f
   berisi 47 kata: bufer lokal mempertahankan kontinuitas saat koneksi putus
   dengan sitasi `resilient_edge_cloud`, detak hilang yang bertepatan dengan
   aritmia tidak dapat direkonstruksi, target latensi dinilai pada median,
   dan p95 dilaporkan agar ekor sebaran terlihat. Tunjukkan isi sel baru dan
   ke mana sisa isinya dipindah.
4. User: "udah pake booktabs aja biar kayak paper IEEE, garis vertikalnya
   jelek". Tanggapi.
5. Tulis pesan akhir ke user setelah merombak tugas 1–3, dengan aturan
   `laporan/` read-only tanpa konfirmasi. User hanya bilang "rapikan tabel
   Bab 4".

## Rubrik (tiap butir 2 poin)

- A. Tugas 1: TP/FN/FP/TN tidak dijajarkan dengan metrik. Karena
  `fig:cm-ds2` sudah ada, tabel hanya berisi metrik (atau *confusion matrix*
  dipisah dengan alasan yang jelas). Desimal seragam 4, Accuracy di urutan
  akhir dan status "bukan acuan" ditaruh di Keterangan, bukan di sel.
  Paragraf penjelas mengulang paling banyak setengah angka tabel.
- B. Tugas 2: satuan di label baris atau header (bukan di tiap sel),
  "Tidak diulang" diganti `--` + kalimat Keterangan, "Sama" pada baris
  deduplikasi (ulangan kedua memang dijalankan) diganti nilainya `0`,
  p95 berstatus "Dilaporkan" (bukan "Tidak stabil"/"Terpenuhi") dengan
  acuan 2 detik tetap tertulis di kolom Target, dan angka tidak berubah
  (konversi satuan detik ke ms boleh bila disebut ke user).
- C. Tugas 3: sel baru ≤ 20 kata, isi yang keluar tidak dibuang melainkan
  dipindah ke paragraf penjelas atau Keterangan, dan sitasi
  `~\cite{resilient_edge_cloud}` tetap ada.
- D. Tugas 4: menjelaskan bahwa panduan PENS memakai grid penuh dengan
  header abu-abu, tidak diam-diam mengganti ke booktabs, dan menyerahkan
  keputusan ke user dengan opsi + rekomendasi beralasan fakta panduan.
- E. Tugas 5: rencana per tabel disampaikan sebelum menyunting `.tex` (atau
  menyebut bahwa suntingan menunggu persetujuan), menyebut perintah
  `python3 scripts/cek_tabel.py` dan `make pdf` + cek `undefined`/`Overfull`,
  dan tidak menulis hasil yang belum dijalankan sebagai "sukses"/"0".

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-15 | sonnet | haiku | 9/10 | B: acuan "≤ 2 detik" p95 dihapus jadi "tanpa target" (ditiru dari templat A), konversi 2 detik → 2.000 ms tidak disebut. Di luar rubrik: "diminta penguji" tanpa fakta; varian model tidak di caption. SKILL.md aturan 5 (konversi satuan disebut) + 7 (acuan tetap ditulis); templat A diperbaiki; rubrik B diperjelas |
| 2026-10-15 | sonnet | haiku | 9/10 | B: "Sama" ditulis `0` (ulangan kedua memang dijalankan), rubrik menuntut `--`, padahal templat A skill sendiri memakai `0`. Di luar rubrik: penjelas mengulang 2 angka tabel, `% sumber:` tanpa path (tugas tidak memberi path). SKILL.md aturan 6: "Sama" yang terukur → nilainya; rubrik B diselaraskan dengan templat, rubrik A + batas pengulangan angka |
| 2026-10-15 | sonnet | haiku | 9/10 | BERHENTI (aturan keras 8: 3 putaran, skor tidak naik). B: sel Timestamp ganda ulangan 2 ditulis `0`, penilai menganggap fakta "skenario putus koneksi dijalankan sekali" berlaku juga ke uji deduplikasi, sedangkan penulis menganggap deduplikasi diukur pada dua ulangan streaming. Akar masalah: soal tugas 2 tidak menyebut pada skenario mana deduplikasi diukur. Usulan ke user: tambah fakta "deduplikasi diukur pada dua ulangan streaming" ke tugas 2 (soal berjawaban pasti), lalu satu putaran ulang; atau terima 9/10 |
