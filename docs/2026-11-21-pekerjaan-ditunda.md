# Pekerjaan ditunda (pipeline Word, anti-slop, rilis, skill)

Daftar tunggal pekerjaan dari sesi 21 Nov 2026 yang belum dieksekusi, beserta
dokumen yang memuat rinciannya. Pekerjaan perangkat keras dan model tetap di
`model/CLAUDE.md` §Pekerjaan terbuka.

| # | Pekerjaan | Status | Rincian |
|---|---|---|---|
| 1 | Gaya skill provenfix untuk sembilan skill lain | digantikan rework skill (format skill-creator, keputusan user 21 Nov 2026) | `docs/2026-11-21-rencana-rework-skill-codebase.md` |
| 2 | Lingkungan WordCraft: `rustup target add wasm32-unknown-unknown` lalu `cargo xtask ci` di `~/dev/wordcraft` (test `swiss_german_and_portugal_portuguese_keep_their_languages_rules` gagal juga di `main` karena data craft-i18n tidak ada), dan aplikasi GUI dibangun dari branch `fix/latex-env-scopes-declarations` | ditunda user; nilainya rendah selama branch tidak di-PR dan suntingan lewat `make docx` | `laporan/CLAUDE.md` §DOCX Notes |
| 3 | Penyetelan `tulis-tanpa-slop` dengan aturan `narasi-pa` yang belum punya padanan (7 dari 12) | belum dimulai | `docs/2026-11-21-skill-anti-slop.md` §Sisa pekerjaan |
| 4 | Perluasan gaya `tulis-tanpa-slop` ke progres-pa-1 Bab 1, Bab 5, abstrak, dan ke buku-pa | ditahan user ("jangan dulu") | `docs/2026-11-21-skill-anti-slop.md` §Sisa pekerjaan |
| 5 | Cek visual DOCX terhadap PDF (`make cek-docx`), float dan pemotongan baris diterima sebagai keterbatasan | menunggu user | `laporan/CLAUDE.md` §DOCX Notes |
| 6 | Push repo PA (commit lokal sejak sesi 21 Nov 2026, termasuk tag `rilis/*` yang memang tidak di-push) | menunggu perintah user | — |
