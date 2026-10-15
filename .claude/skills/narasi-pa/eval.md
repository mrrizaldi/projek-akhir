# Eval: narasi-pa

Penilai: model berbeda dari penulis. Skor 0-10, lulus hanya 10/10.
Penulis menerima SKILL.md + tugas di bawah (tanpa akses repo, fakta repo ada
di tugas) dan mengembalikan paragraf LaTeX, tabel temuan, atau pesan ke user.
Angka keluaran skrip boleh `[N]` karena peserta tidak menjalankan perintah.

## Tugas uji

1. Sunting penjelas `tab:delta-int8` berikut. Fakta tabel: Accuracy 0,9207 →
   0,9198 (−0,0009), Precision 0,6235 → 0,6169 (−0,0067), Recall 0,6996 →
   0,7105 (+0,0108), F1 0,6594 → 0,6604 (+0,0010), Specificity 0,9479 →
   0,9456 (−0,0023), AUC 0,9334 → 0,9344 (+0,0010), target
   |Δrecall| < 0,02. Paragraf sekarang: "Berdasarkan Tabel~\ref{tab:delta-int8},
   accuracy turun dari 0,9207 menjadi 0,9198, precision turun dari 0,6235
   menjadi 0,6169, recall naik dari 0,6996 menjadi 0,7105, F1 naik dari 0,6594
   menjadi 0,6604, specificity turun dari 0,9479 menjadi 0,9456, dan AUC naik
   dari 0,9334 menjadi 0,9344, sehingga kuantisasi terbukti tidak
   berpengaruh signifikan sehingga model INT8 menjamin kinerja yang sama di
   perangkat." Paragraf sebelumnya juga dibuka "Berdasarkan Tabel".
2. Tulis penjelas untuk hasil uji ini: PDSR 100,0% dan 99,2% (target ≥ 95%),
   median latensi 939 dan 1.108 ms (target ≤ 2.000 ms), p95 1.404 dan
   3.304 ms (tanpa target). Sumber sinyal *replay*, dua ulangan 180 detik,
   WiFi lokal. User ingin menulis "pipeline terbukti andal untuk pemantauan
   pasien di rumah".
3. Paragraf 210 kata berisi hasil ablasi (F1 per varian), penjelasan mengapa
   *window* 128 sampel sebelum R membantu kelas S (gelombang P dan interval
   R-R sebelumnya), dan keputusan memakai A6 untuk *deploy*. Jelaskan cara
   memecahnya. Isi lengkap tidak perlu ditulis, cukup kerangka per paragraf
   dengan kalimat pertamanya.
4. Mode Audit pada Bab 4 dengan fakta keluaran skrip: 18 pembuka "Berdasarkan
   Tabel", `N-ULANG` pada dua penjelas, 59 kalimat > 35 kata, "sehingga" 8,0
   per 1.000 kata. Fakta tambahan: satu kalimat di 4.7 menyatakan sinyal
   tubuh "berkualitas baik" padahal tabel kualitas rekaman masih
   `\PlaceholderData`. Tulis tabel temuan.
5. Pesan akhir ke user setelah menyunting tugas 1, dengan pemeriksaan isi
   dan build.

## Rubrik (tiap butir 2 poin)

- A. Tugas 1: dibuka temuan (bukan "Berdasarkan Tabel" karena paragraf
  sebelumnya sudah memakainya), ≤ 5 angka di seluruh paragraf termasuk
  ambang 0,02, tiap angka berpembanding (selisih terbesar vs ambang),
  "signifikan", "terbukti", dan "menjamin" dihapus
  atau dibenarkan, tanpa rantai "sehingga ... sehingga", dan kalimat ≤ 35
  kata.
- B. Tugas 2: klaim dibatasi pada kondisi uji (*replay*, dua ulangan, WiFi
  lokal). Menolak atau melunakkan "terbukti andal untuk pemantauan pasien di
  rumah" dengan alasan lingkup bukti. p95 dilaporkan tanpa status
  terpenuhi atau gagal.
- C. Tugas 3: dipecah per fungsi menjadi hasil, mekanisme (atau dirujuk ke
  4.7/Bab 3), dan keputusan, masing-masing ≤ 150 kata, kalimat pertama
  tiap paragraf menyatakan klaim utama paragraf itu (temuan, pernyataan
  mekanisme, atau keputusan), dan tidak ada fakta yang tidak diberikan
  tugas (mis. "tertinggi di antara seluruh varian", jumlah seed, anggaran
  perangkat).
- D. Tugas 4: temuan diurutkan terburuk dulu. Klaim "berkualitas baik" tanpa
  data ditandai prioritas Tinggi (register/klaim melebihi bukti, aturan 4
  dan 10), temuan skrip diringkas sebagai Rendah/Sedang, ≤ 15 baris, dan
  tanpa pujian.
- E. Tugas 5: menyebut pemeriksaan isi (angka/`\cite`/`\ref` hilang atau
  tambah) dan `make pdf` + `undefined`, menyebut angka yang sengaja tidak
  diulang dari tabel, tidak menulis hasil yang belum dijalankan sebagai
  sukses, dan status suntingan konsisten ("usulan" selama belum ditulis ke
  `.tex`, bukan "sudah dirapikan").

## Riwayat skor

| Tanggal | Penulis | Penilai | Skor | Catatan |
|---|---|---|---|---|
| 2026-10-15 | sonnet | haiku | 9/10 | E: "sudah saya rapikan" padahal kalimat berikutnya "belum ditulis ke bab4.tex". Di luar rubrik: "memenuhi target" untuk satu pengukuran; p95 1.404 tidak disebut. Mode Sunting: pesan memakai "usulan" selama belum ditulis; rubrik E ditambah syarat konsistensi |
| 2026-10-15 | sonnet | haiku | 8/10 | A: 6 angka (ambang ikut dihitung) dan salah hitung "5 angka"; C: kalimat pertama paragraf mekanisme/keputusan dinilai bukan temuan, fakta dikarang ("F1 tertinggi", "anggaran perangkat"). Di luar rubrik: PDSR tanpa definisi, mode Sunting tidak mengutip teks sebelum. SKILL.md: batas 5 angka termasuk ambang + hitung; larangan mengarang fakta; kalimat pertama = klaim sesuai fungsi; Sunting mengutip teks sebelum. Rubrik A dan C diperjelas |
| 2026-10-15 | sonnet | haiku | **10/10** | LULUS putaran 3. Di luar rubrik: PDSR tanpa kepanjangan di jawaban tugas 2; hanya p95 terbesar yang disebut; audit tugas 4 tanpa reverse outline (tugas tidak memberi bab). Dicatat, skill tidak diubah |
