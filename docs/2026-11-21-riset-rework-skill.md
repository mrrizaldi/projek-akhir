# Riset rework skill dan codebase (acuan finance-project)

Sumber: sesi Claude finance-project 21 Nov 2026 (`89330e1a`, `0a813169`,
`ad7186b7`), commit `c0cefa8`, `93516b2`, `8a8c055`, `287261d`, `0eeb01f` di
`~/dev/finance-project`, dan repo skill user di `~/dev/` (`no-code-comments`,
`shared-worktree`, `adb-phone-control`, `process-death-safe-results`,
`before-after`).

## Yang dikerjakan di finance-project

1. Daftar semua skill repo, lalu tiga keputusan user: nama dan isi skill ke
   bahasa Inggris, eval ke format skill-creator, satu putaran eval per skill.
2. Skill generik naik ke scope user (`shared-worktree`, `no-code-comments`,
   `process-death-safe-results`, `adb-phone-control`); skill repo menjadi
   lapisan tipis berisi path, perintah, dan jebakan proyek, dan kalimat
   pertamanya menyuruh memuat skill user.
3. Rencana tertulis, lalu gelombang subagen paralel: satu penulis per skill,
   koordinator meninjau dan commit satu skill per commit.
4. Eval perilaku satu putaran per skill (penulis sonnet, penilai haiku),
   skor di pesan commit.
5. Riwayat tertulis dipangkas (dokumen menjelaskan kondisi kini saja,
   riwayat ada di git), audit `deadcode` (laporan dulu), rencana selesai
   dihapus.
6. Sapuan bahasa Inggris di kode, log, pesan error, README.
7. Skill user dijadikan repo GitHub private `mrrizaldi/<nama>`, di-clone ke
   `~/dev/<nama>`, di-symlink ke `~/.claude/skills/<nama>`; tiap repo punya
   `SKILL.md`, `README.md`, `CLAUDE.md`, `evals/`, `triggers/evals.json`,
   `scripts/check_skill.py`, `.github/workflows/tests.yml`.
8. Validator struktur skill di CI (`scripts/check_skills.py`) dan tabel
   "Skills — load before you start" di `CLAUDE.md`.

Skill `antislop*` tidak dipakai di finance-project; "pembersihan" di sana
berupa bahasa Inggris, pangkas riwayat, dan `deadcode`.

## Konvensi skill yang dipakai

- Frontmatter hanya `name` (sama dengan folder) dan `description`.
- Description satu paragraf, maksimal 1.024 karakter, menyebut apa yang
  dikerjakan dan frasa konkret kapan dipakai, sengaja agak memaksa karena
  Claude cenderung kurang memicu skill.
- Isi kalimat perintah dengan alasan, tanpa huruf kapital ALWAYS/NEVER, di
  bawah 500 baris; skill repo nyata 68–197 baris.
- Setiap aturan lama dipetakan ke skill user, skill repo, atau dibuang
  dengan alasan usang.
- Tanpa riwayat di skill (tanpa tabel skor, tanpa insiden bertanggal).
- Eval: `evals/<kasus>/prompt.md`, `case.yaml`, `graders/NN-*.md` (satu
  pernyataan per berkas); prompt menyatakan penjawab tidak menjalankan
  perintah.
- Pemicu: `triggers/evals.json`, 20 kueri (10 harus memicu, 10 mirip tetapi
  tidak), campuran Indonesia dan Inggris.

## Temuan yang perlu dibawa

1. Uji pemicu (`run_eval` skill-creator) menulis berkas `~/.claude/commands`
   global; wajib `CLAUDE_CONFIG_DIR` terpisah. Baseline: skill hanya memicu
   1–4 dari 10 kueri yang seharusnya, tanpa salah picu; optimasi
   description dua iterasi tidak menaikkan skor, jadi mitigasinya tabel
   pemuatan skill di `CLAUDE.md`. Biaya sekitar 220 panggilan Opus untuk 11
   skill × 20 kueri × 1 run; konfigurasi 3×3 menghabiskan kuota 5 jam.
2. Pangkas riwayat pertama ikut membuang fakta operasional yang masih
   berlaku; reviewer menangkapnya. Riwayat dan fakta operasional dipisah
   sebelum memangkas.
3. `.gitignore` yang mengabaikan `*.json` ikut membuang
   `triggers/evals.json`.
4. Runner uji pemicu (`run.sh`, `loop.sh`) hanya ada di scratchpad sesi
   finance-project dan bisa hilang.

## Perbedaan repo PA yang menentukan rencana

1. Bahasa: `CLAUDE.md` mewajibkan dokumen Indonesia; laporan Indonesia;
   nama di kode Indonesia (`AMBANG_AYUN`, `pasang_buzzer`, `cek_slop.py`).
2. Riwayat: repo PA memakai `docs/arsip/` dan `model/docs/arsip/`, bukan
   menghapus; Aturan keras 8 mencatat skor eval di `eval.md`.
3. Kode sudah nol komentar (`scripts/cek_komentar.py` di CI).
4. Skill PA (10 aktif): `batas-tidak-diam`, `buku-ikut-proposal`, `deck-pa`,
   `ingest-word`, `kicad-pcb-pa`, `struktur-pa`, `tabel-pa`,
   `tanpa-komentar-kode`, `tautan-lokal`, `tulis-tanpa-slop`;
   `.agents/skills/` salinan Codex yang tidak sinkron.

## Calon ekstraksi ke scope user

| Skill PA | Usulan | Alasan |
|---|---|---|
| `tanpa-komentar-kode` | lebur ke `no-code-comments` (sudah ada); PA tinggal lapisan tipis (path `cek_komentar.py`, penamaan konstanta firmware, dokumen tujuan) | aturan inti sama |
| `tautan-lokal` | ekstrak utuh | tidak terikat PA |
| `batas-tidak-diam` | ekstrak (firmware tertanam umum) + lapisan tipis PA (modul dan buffer PA) | pola buffer/batas berlaku di firmware mana pun |
| `tulis-tanpa-slop` | ekstrak inti tulisan akademik Indonesia + `cek_slop.py`; PA tinggal aturan rumah `laporan/CLAUDE.md` | katalog 74 pola tidak spesifik PA |
| `kicad-pcb-pa` | ekstrak alur KiCad MCP umum + lapisan tipis PA (board, net) | sebagian besar alur MCP dan Freerouting |
| `ingest-word` | ekstrak alur ingest WordCraft↔LaTeX umum + lapisan tipis PA | terikat `wordcraft-cli` branch lokal, bukan PA |
| `deck-pa`, `struktur-pa`, `tabel-pa`, `buku-ikut-proposal` | tetap di repo | terikat format PENS, proposal, dan buku |
