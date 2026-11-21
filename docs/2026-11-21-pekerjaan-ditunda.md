# Pekerjaan ditunda (pipeline Word, anti-slop, rilis, skill)

Daftar tunggal pekerjaan dari sesi 21 Nov 2026 yang belum dieksekusi, beserta
dokumen yang memuat rinciannya. Pekerjaan perangkat keras dan model tetap di
`model/CLAUDE.md` §Pekerjaan terbuka.

| # | Pekerjaan | Status | Rincian |
|---|---|---|---|
| 2 | Lingkungan WordCraft: `rustup target add wasm32-unknown-unknown` lalu `cargo xtask ci` di `~/dev/wordcraft` (test `swiss_german_and_portugal_portuguese_keep_their_languages_rules` gagal juga di `main` karena data craft-i18n tidak ada), dan aplikasi GUI dibangun dari branch `fix/latex-env-scopes-declarations` | ditunda user; nilainya rendah selama branch tidak di-PR dan suntingan lewat `make docx` | `laporan/CLAUDE.md` §DOCX Notes |
| 3 | Penyetelan `tulis-tanpa-slop` dengan aturan `narasi-pa` yang belum punya padanan | aturan 1, 2, 3, 6, 10 sudah masuk lapisan PA; sisanya diputuskan tidak masuk (alasan di riwayat commit 0fd0e25) | `.claude/skills/tulis-tanpa-slop/SKILL.md` |
| 4 | Perluasan gaya `tulis-tanpa-slop` ke progres-pa-1 Bab 1, Bab 5, abstrak, dan ke buku-pa | ditahan user ("jangan dulu") | `docs/2026-11-21-skill-anti-slop.md` §Sisa pekerjaan |
| 5 | Cek visual DOCX terhadap PDF (`make cek-docx`), float dan pemotongan baris diterima sebagai keterbatasan | menunggu user | `laporan/CLAUDE.md` §DOCX Notes |
| 6 | Push repo PA (commit lokal sejak sesi 21 Nov 2026, termasuk tag `rilis/*` yang memang tidak di-push) | menunggu perintah user | — |
| 7 | Path `% sumber:` di `laporan/{buku-pa,progres-pa-1}/bab/bab3.tex` dan `bab4.tex` (18 komentar) serta `gambar/daftar-placeholder.md:121` masih menunjuk dokumen arsip yang sudah dihapus; tujuan barunya `hardware/mainboard/README.md`, `model/CLAUDE.md`, `model/docs/jitter-walkthrough.md` §5, `model/docs/README.md` §Eksperimen, `model/docs/train-walkthrough.md` §6b | menunggu izin user (laporan read-only) | daftar baris di pesan commit `deb3412` |
| 8 | Repo GitHub private untuk lima skill user (`local-file-links`, `firmware-bounded-limits`, `indonesian-antislop-writing`, `kicad-mcp-pcb`, `wordcraft-latex-ingest`) dan LICENSE-nya; push perubahan lokal `~/dev/no-code-comments` | menunggu perintah user | `.claude/skills/README.md` |
| 9 | `wordcraft-latex-ingest`: opsi "stash" saat guard menolak tidak bisa jalan karena perubahan `.tex` sudah ter-commit (aturan pohon bersih); alternatif sync di worktree pada commit asal DOCX lalu digabung | menunggu keputusan user | `~/dev/wordcraft-latex-ingest/SKILL.md` langkah guard |
