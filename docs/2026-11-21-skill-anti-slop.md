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
