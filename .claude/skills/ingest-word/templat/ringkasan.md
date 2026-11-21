<!-- Layar konfirmasi langkah 3. Salin, isi, sajikan ke user, lalu tunggu "ya".
     Bagian tanpa isi ditulis "tidak ada", jangan dihapus. Belum ada yang
     ditulis ke .tex saat layar ini disajikan: jangan menulis bahwa perubahan
     sudah diterapkan. -->
## Ingest <projek>: ringkasan dry-run

Sumber: `output/suntingan-<stempel>.docx` (salinan `output/main.docx`).

### Perubahan per berkas

| Berkas | changed | inserted | deleted |
|---|---|---|---|
| `bab/<berkas>.tex` | <n> | <n> | <n> |

Cuplikan, satu baris per perubahan:
- `bab/<berkas>.tex`: "<sebelum>" → "<sesudah>"

### Judul yang dikembalikan ke huruf sumber

- `\section{<KAPITAL DARI SYNC>}` akan ditulis `\section{<Kapitalisasi Sumber>}`

### Dilewati sync (dipindah manual sesudah sync)

| Butir | Alasan sync | Rencana |
|---|---|---|
| <teks butir> | <alasan persis dari keluaran skipped> | <baris sumber yang disunting, atau pertanyaan di bawah> |

Pertanyaan untuk entri Daftar Isi/Gambar/Tabel: entri "<teks>" dibangkitkan
dari judul atau caption. Apakah judul/caption sumbernya yang diubah menjadi
"<teks baru>"?

### Komentar Word

<n> komentar.
- "<isi komentar>" (<nama>, <tanggal>), di `bab/<berkas>.tex`: <rencana tindakan>

Balas "ya" untuk menjalankan `make sync`, lalu perbaikan judul, pemindahan
butir skipped, dan pengerjaan komentar di atas.
