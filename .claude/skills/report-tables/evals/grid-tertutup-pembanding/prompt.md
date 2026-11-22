---
tags: [report-tables]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Skill, Write]
---

Repo `/home/mrrizaldi/dev/projek-akhir`, buku `laporan/buku-pa`, lebar teks A4. User mengizinkan menyunting tabel yang disebut.

Tabel di Bab 2, `\label{tab:perbandingan-penelitian}`, berupa `longtable` dengan spesifikasi `{cL{3.5cm}L{2.0cm}L{2.0cm}L{1.8cm}L{2.8cm}}`, `\toprule`/`\midrule` di header berulang, `\rowcolor{headgray}` di header, dan `\bottomrule` di `\endfoot`. User: "untuk tabel penelitian terkait, pake tabel tertutup aja bukan terbuka, tapi plain gausah ada style atau filling color". Tulis spesifikasi kolom, header berulang, akhir satu baris data, dan `\endfoot` hasilnya. Sebutkan juga apakah tabel spesifikasi komponen tiga garis di Bab 3 ikut berubah.

Kamu tidak bisa menjalankan perintah atau menyunting repo. Tulis LaTeX hasilnya, paragraf yang berubah, dan pesan akhir ke user; bila butuh keluaran perintah yang belum kamu lihat, tulis [N].
