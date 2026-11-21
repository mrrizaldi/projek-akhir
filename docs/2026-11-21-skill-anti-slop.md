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
2. Paragraf di bawah penanda `% MANUAL` adalah teks penulis dan tidak boleh
   ditulis ulang (`laporan/CLAUDE.md`).
3. Larangan titik dua, titik koma, dan em dash di paragraf sudah ada di
   `laporan/CLAUDE.md` dan diperiksa `scripts/cek_tabel.py`.
4. Struktur paragraf sudah diatur skill `narasi-pa`.

## Rencana aksi (belum diputuskan user)

1. Ambil SKILL.md naskah-id dan katalog pola humanizer-indonesia, baca isinya
   dan skrip yang dibawa.
2. Bandingkan dengan `narasi-pa` dan `laporan/CLAUDE.md`, daftar pola yang
   belum tercakup.
3. Usulkan tambahan ke `narasi-pa` ke user. Pola yang bisa dideteksi mesin
   menjadi pemeriksaan di `scripts/cek_tabel.py` (Aturan keras 6).
4. Skill yang diubah menjalani eval sesuai Aturan keras 8.

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

