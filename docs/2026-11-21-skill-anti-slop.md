# Skill penulisan laporan tanpa pola tulisan AI

Tujuan: teks `laporan/buku-pa` dan `laporan/progres-pa-1` tidak terbaca sebagai
keluaran model bahasa (frasa klise, ritme seragam, pola tiga butir, kalimat
penutup yang merangkum ulang).

## Kandidat skill luar

| Skill | Kecocokan | Catatan |
|---|---|---|
| naskah-id (nothinx) | Paling cocok | Karya ilmiah (skripsi, laporan penelitian), EYD V dan KBBI, tidak mengubah angka, hasil, dan sitasi |
| humanizer-indonesia (adhiprib) | Sebagian | Katalog pola tulisan AI berbahasa Indonesia; mode kerjanya menyunting ulang teks, jadi yang diambil hanya katalognya |
| opencraftdev/humanizer | Tidak dipakai | Cakupan skripsi sempit, tumpang tindih dengan naskah-id, format ZIP claude.ai |
| Indonesia EYD Writing Skill (ClaudSkills) | Belum | Sumber agregator, repo asal belum diketahui |
| blader/humanizer, hardikpandya/stop-slop | Tidak dipakai | Pola bahasa Inggris |
| coreyhaines31/marketingskills | Tidak dipakai | Marketing dan SEO |
| alvinindra/bahasa-skills | Acuan pembanding | Paket penulisan bahasa Indonesia dari nol |

Keberadaan dan isi repo di atas belum diperiksa langsung (daftar berasal dari
riset chat, 21 Nov 2026).

## Benturan dengan aturan repo

Skill luar tidak dipasang mentah karena berbenturan dengan aturan yang berlaku:

1. Istilah teknis tetap bahasa Inggris dan miring (`\textit{board}`, bukan
   "papan"), keputusan user 20 Okt 2026. Skill EYD cenderung membakukan istilah.
2. Kalimat penulis tidak ditulis ulang tanpa konfirmasi (`laporan/CLAUDE.md`
   §Ingest suntingan WordCraft).
3. Larangan titik dua, titik koma, dan em dash di paragraf sudah ada di
   `laporan/CLAUDE.md` dan diperiksa `scripts/cek_tabel.py`.
4. Struktur paragraf semula diatur skill `narasi-pa`, yang dinonaktifkan 21 Nov
   2026 (lihat Keputusan posisi skill).

## Keputusan posisi skill

Rencana distilasi ke `narasi-pa` tidak dipakai: user memutuskan 21 Nov 2026 bahwa `tulis-tanpa-slop` menggantikan `narasi-pa`.

## Urutan kerja (keputusan user 21 Nov 2026)

Pekerjaan anti-slop dimulai dari kode (skill `antislop-code` untuk komentar
kode WordCraft dan skrip yang disentuh). Skill penulisan laporan dibahas
terpisah sesudahnya; diskusi kandidat di atas dilanjutkan nanti.

## Hasil riset dan uji coba (21 Nov 2026)

Katalog riset (74 pola, profil dan lisensi sumber, konflik dengan aturan
rumah, celah): `2026-11-21-skill-anti-slop/katalog.md`. Atas keputusan user,
`narasi-pa` diabaikan untuk uji coba ini dan dibuat skill baru
`tulis-tanpa-slop` beserta pemeriksa `scripts/cek_slop.py`. Uji coba hanya di
`laporan/progres-pa-1` Bab 2 sampai Bab 4; Bab 1, bagian depan, dan Bab 5
tidak disentuh. Cadangan sebelum uji coba: tag git
`backup/pra-antislop-20261121-1127` dan arsip
`~/backups/projek-akhir/progres-pa-1-20261121-1127.tar.gz`.

Baseline `cek_slop.py --ringkas` sebelum penyuntingan:

| Bab | Kata | Rerata kalimat (sb) | galat | tinjau | karena itu sisipan | paragraf yaitu ≥ 2 |
|---|---|---|---|---|---|---|
| 2 | 4.545 | 20,3 (7,9) | 8 | 8 | 1 | 2 |
| 3 | 7.472 | 17,2 (7,8) | 2 | 37 | 18 | 10 |
| 4 | 7.674 | 16,3 (8,1) | 7 | 41 | 25 | 7 |

Temuan yang tidak ada di sumber mana pun: larangan titik dua dan larangan
pembuka "Oleh karena itu" di aturan lama melahirkan kebiasaan baru, yaitu
"karena itu" yang disisipkan di tengah klausa dan "yaitu" berderet. Keduanya
masuk skill sebagai pola utama.

Hasil uji coba (commit `0852264`, `a02a466`, `57b5f8c`; tiap bab
`--banding` invarian aman, `cek_tabel` 0 galat, PDF 125 hlm 0 undefined/Overfull):

| Bab | galat | tinjau | Rerata kalimat (sb) |
|---|---|---|---|
| 2 | 8 → 0 | 8 → 2 | 20,3 (7,9) → 19,5 (7,5) |
| 3 | 2 → 0 | 37 → 7 | 17,2 (7,8) → 17,3 (7,8) |
| 4 | 7 → 0 | 41 → 8 | 16,3 (8,1) → 16,2 (8,0) |

Eval skill (penulis sonnet, penilai haiku): 8, 9, 9, 9, 10 dari 10. Putaran 4
dan 5 atas izin user; yang meluluskan adalah contoh dua kalimat untuk "karena
itu" yang merujuk ke kalimat sebelumnya. Riwayat di
`.claude/skills/tulis-tanpa-slop/eval.md`.

Temuan isi selama penyuntingan, diperbaiki di commit `39d0268`: progres-pa-1
Bab 3 menyebut "lima hal" untuk empat butir (kini "empat hal"), dan kalimat
"TinyML memungkinkan ..." di buku-pa Bab 2 tertelan baris komentar `% sumber:`
(kini di baris sendiri dan tercetak).

## Sisa pekerjaan

1. User meninjau progres-pa-1 Bab 2–4 hasil uji coba, lalu memutuskan
   dipakai atau dikembalikan
   (`git checkout backup/pra-antislop-20261121-1127 -- laporan/progres-pa-1/bab`).
2. Bila dipakai: perluasan ke progres-pa-1 Bab 1, Bab 5, abstrak, dan ke
   buku-pa. Menunggu keputusan user.
3. Klaim tanpa angka yang dibiarkan karena faktanya tidak ada di naskah.
   User menyediakan angka atau memutuskan klaimnya dilunakkan.
   - bab2: akurasi Mulyawan "tinggi";
   - bab2: "baru sedikit yang dibuktikan" dan "salah satu dari sedikit studi";
   - bab2: "dua keperluan yang berbeda", hanya satu yang diuraikan;
   - bab3: "menekan jumlah parameter secara drastis" dan "model yang telah
     teruji akurat".
4. Celah aturan. `narasi-pa` dinonaktifkan 21 Nov 2026; aturan berikut
   belum punya padanan dan menjadi bahan penyetelan `tulis-tanpa-slop`
   berikutnya.

   | Aturan narasi-pa | Ringkasan (≤ 8 kata) | Padanan di tulis-tanpa-slop |
   |---|---|---|
   | 1 | Penjelas tabel: temuan, bukti, makna | tidak ada |
   | 2 | Pembuka paragraf penjelas bervariasi | tidak ada |
   | 3 | Jangan membaca ulang isi tabel | tidak ada |
   | 4 | Kekuatan klaim sebanding bukti | ada (Frasa: S-SIGNIFIKAN, S-MUTLAK; tabel kata tidak ada) |
   | 5 | Kalimat 15–30 kata, pecah di atas 35 | ada (Kalimat: S-PANJANG, S-RANTAI-YANG) |
   | 6 | Satu paragraf satu fungsi, 60–150 kata | tidak ada |
   | 7 | Tanpa pembuka meta di subbab | ada (Paragraf: S-DOKUMEN) |
   | 8 | Kohesi lama ke baru, pembuka dirotasi | tidak ada |
   | 9 | Istilah dan singkatan konsisten | ada (Yang bukan slop: pengulangan istilah) |
   | 10 | Benang merah hasil ke target | tidak ada |
   | 11 | Register rancangan versus capaian | tidak ada |
   | 12 | Sunting tidak mengubah isi | ada (Yang tidak boleh berubah) |
5. `laporan/progres-pa-1/bab/bab2.tex:96`: baris komentar `% sumber:` masih
   memuat sisa teks "TinyML memungkinkan model kecerdasan buatan". Tidak
   tercetak, kalimatnya sudah ada di baris prosa; cukup dirapikan saat bab
   itu disunting lagi.
