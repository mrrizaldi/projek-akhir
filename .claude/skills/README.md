# Skill repo PA

Skill di repo ini adalah lapisan tipis. Aturan umum tinggal sekali di skill
user (`~/.claude/skills/`); skill repo menyebut skill user yang dimuat lebih
dulu, lalu menambahkan hanya yang khusus PA (path, perintah, nama konstanta,
jebakan). Muat lapisan user, lalu lapisan repo. Aturan keras 7–8 di
`CLAUDE.md` root: setiap kegagalan yang ditangkap user menjadi skill hari itu
juga, dan setiap skill punya eval yang dinilai model berbeda, maksimal 3
putaran.

## Skill repo

| Skill | Kapan | Skill user yang dimuat |
|---|---|---|
| `batas-tidak-diam` | firmware dengan buffer, durasi, atau kapasitas terbatas, atau operasi lambat di `loop()` | `firmware-bounded-limits` |
| `kicad-pcb-pa` | PCB atau skematik KiCad mainboard, DRC, rute, Gerber | `kicad-mcp-pcb` |
| `ingest-word` | suntingan DOCX dari teman dimasukkan kembali ke LaTeX | `wordcraft-latex-ingest` |
| `tanpa-komentar-kode` | menulis atau menyunting kode, prompt ke subagen penulis kode | `no-code-comments` |
| `tulis-tanpa-slop` | paragraf laporan agar tidak terbaca ditulis AI | `indonesian-antislop-writing` |
| `struktur-pa` | kerangka bab, benang merah, placeholder gambar, QA sebelum kumpul | tidak ada |
| `tabel-pa` | tabel LaTeX laporan | tidak ada |
| `buku-ikut-proposal` | Bab 1 buku mengikuti proposal, pertanyaan ke user soal isi buku | tidak ada |
| `deck-pa` | deck presentasi PA (PPTX) | tidak ada |

`narasi-pa` nonaktif dan disimpan di
`.claude/skills-arsip/narasi-pa/` sebagai rujukan.

## Skill user

Tiap skill user berupa repo lokal `~/dev/<nama>` dengan symlink
`~/.claude/skills/<nama>`. Repo GitHub belum dibuat; saat ini hanya repo
lokal. Setelah ada remote, pasang di mesin lain dengan
`git clone <url> ~/dev/<nama> && ln -s ~/dev/<nama> ~/.claude/skills/<nama>`.

| Skill user | Repo lokal | Dipakai untuk |
|---|---|---|
| `local-file-links` | `~/dev/local-file-links` | dokumen yang menautkan berkas lokal (indeks rujukan di `laporan/pustaka/`, daftar bukti dari `model/artifacts`) |
| `firmware-bounded-limits` | `~/dev/firmware-bounded-limits` | batas firmware tidak membuang data diam-diam |
| `indonesian-antislop-writing` | `~/dev/indonesian-antislop-writing` | menyunting prosa Indonesia, dengan `check_slop.py` |
| `kicad-mcp-pcb` | `~/dev/kicad-mcp-pcb` | PCB KiCad lewat MCP, pcbnew, kicad-cli, Freerouting |
| `wordcraft-latex-ingest` | `~/dev/wordcraft-latex-ingest` | DOCX ke LaTeX |
| `no-code-comments` | `~/dev/no-code-comments` | kode tanpa komentar, dengan `check_comments.py` |
| `shared-worktree` | `~/dev/shared-worktree` | keamanan git saat beberapa sesi memakai satu klon |

## Layout skill

```
<skill>/
  SKILL.md                  aturan, frontmatter name + description
  evals/<kasus>/
    prompt.md               teks tugas uji
    case.yaml               schema_version: "1.1", name, expected_outcome
    graders/NN-*.md         satu pernyataan yang dapat dinilai lulus/gagal
  triggers/evals.json       daftar {query, should_trigger}, kelas true dan false
  referensi/                opsional, detail yang dimuat bila perlu
```

Konvensi `SKILL.md` (format skill-creator):

- Frontmatter hanya `name` (sama dengan nama folder) dan `description`.
- `description` satu baris, paling banyak 1.024 karakter, agak memaksa:
  menyebut kapan dipakai dengan frasa yang diketik user, dan batasnya.
- Tiap aturan disertai alasan satu kalimat.
- Tanpa riwayat, tanpa catatan revisi, badan kurang dari 500 baris.
- Detail yang hanya berlaku pada kondisi tertentu pindah ke `referensi/`.

## Prosedur eval

Dua agen terpisah per putaran, dari Agent tool atau sesi terpisah.

1. **Penulis** (model A) hanya diberi `SKILL.md` (lapisan user dan repo,
   plus `referensi/`) dan `prompt.md` tiap kasus. Ia tidak membuka
   `case.yaml` atau `graders/`, tidak menjalankan perintah, dan menulis satu
   berkas jawaban dengan heading `## <kasus>` per kasus.
2. **Penilai** (model B, berbeda dari A) diberi `SKILL.md`, `case.yaml` dan
   `graders/` tiap kasus, dan berkas jawaban. Ia menilai tiap pernyataan
   lulus atau gagal dengan kutipan bukti, dan menulis tabel
   `Kasus | Penilai | Lulus | Bukti`, baris `Lulus: X/Y`, dan paling banyak
   tiga pelanggaran `SKILL.md` di luar penilai.
3. Belum semua lulus: perbaiki aturan yang ambigu di `SKILL.md` atau
   penilai yang ambigu, lalu putaran berikutnya dengan penulis baru (bukan
   melanjutkan agen lama).
4. Berhenti saat semua lulus, pada putaran ke-3, atau bila hasil tidak naik
   dua putaran berturut-turut; yang belum lulus ditanyakan ke user.
5. Skor dan tabel lulus ditulis di pesan commit. Tidak ada berkas riwayat
   skor; `git log` adalah riwayatnya. Setiap perubahan `SKILL.md` sesudah
   lulus mewajibkan putaran baru.

## Pemeriksa

- Struktur: `python3 scripts/cek_skill.py` (tanpa opsi; `--uji` untuk
  swauji). Jalan di CI.
- Pemicu: `scripts/uji_pemicu.sh <folder skill>` mengukur apakah deskripsi
  memicu pada kueri `triggers/evals.json` (`scripts/README.md`).
- Laporan: `python3 scripts/cek_tabel.py`, `python3 scripts/cek_slop.py`.
