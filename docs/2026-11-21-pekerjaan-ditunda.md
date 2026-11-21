# Pekerjaan ditunda (pipeline Word, anti-slop, rilis, skill)

Daftar tunggal pekerjaan dari sesi 21 Nov 2026 yang belum dieksekusi, beserta
dokumen yang memuat rinciannya. Pekerjaan perangkat keras dan model tetap di
`model/CLAUDE.md` §Pekerjaan terbuka.

| # | Pekerjaan | Status | Rincian |
|---|---|---|---|
| 1 | Gaya skill provenfix untuk sembilan skill lain | menunggu tinjauan pilot `ingest-word`; akan dilebur ke rework skill dan codebase | `docs/2026-11-21-rencana-rilis-dan-gaya-skill.md` §Tindak lanjut user butir 1 |
| 2 | Lingkungan WordCraft: target wasm, `cargo xtask ci`, GUI dari branch | ditunda user | rencana yang sama, butir 2; `docs/2026-11-21-pipeline-word-latex.md` §Sisa pekerjaan |
| 3 | Eval `ingest-word`: langkah 2 meminta kalimat bahwa berkas berubah sesudah DOCX dibuat | usulan, 9/10 | `.claude/skills/ingest-word/eval.md` baris putaran 4 |
| 4 | Penyetelan `tulis-tanpa-slop` dengan aturan `narasi-pa` yang belum punya padanan (7 dari 12) | belum dimulai | `docs/2026-11-21-skill-anti-slop.md` §Sisa pekerjaan |
| 5 | Perluasan gaya `tulis-tanpa-slop` ke progres-pa-1 Bab 1, Bab 5, abstrak, dan ke buku-pa | ditahan user ("jangan dulu") | `docs/2026-11-21-skill-anti-slop.md` §Sisa pekerjaan |
| 6 | Prosedur skill yang masih `make pdf` untuk bukti diganti `make pdf-bersih` (`struktur-pa`, `buku-ikut-proposal`, `tabel-pa`, `tulis-tanpa-slop`) | belum, ikut rework skill | `docs/2026-11-21-rencana-rilis-dan-gaya-skill.md` §Temuan saat eksekusi |
| 7 | `.agents/skills/` dan `AGENTS.md` (salinan untuk Codex, terakhir 5 Nov 2026) tidak sinkron dengan `.claude/skills/` dan masih menunjuk `narasi-pa` | belum diputuskan | — |
| 8 | Cek visual DOCX terhadap PDF (`make cek-docx`), float dan pemotongan baris diterima sebagai keterbatasan | menunggu user | `docs/2026-11-21-pipeline-word-latex.md` §Sisa pekerjaan |
| 9 | Push repo PA (commit lokal sejak sesi 21 Nov 2026, termasuk tag `rilis/*` yang memang tidak di-push) | menunggu perintah user | — |
