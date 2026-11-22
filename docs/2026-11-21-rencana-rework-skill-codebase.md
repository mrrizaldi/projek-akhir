# Rework skill dan codebase repo PA

> **Untuk agen pelaksana:** WAJIB memakai sub-skill
> superpowers:subagent-driven-development (dianjurkan) atau
> superpowers:executing-plans. Langkah memakai kotak centang (`- [ ]`).

**Tujuan:** skill repo PA ditulis ulang dengan standar skill-creator, skill
yang generik diekstrak ke repo skill user berbahasa Inggris, eval pindah ke
format `evals/` + `triggers/`, validator struktur skill masuk CI, dan docs
serta kode dibersihkan dari riwayat tertulis, kode mati, dan pola tulisan AI.

**Arsitektur:** mengikuti rework finance-project 21 Nov 2026
(`docs/2026-11-21-riset-rework-skill.md` (dihapus; isi di git `0fc2777`)). Skill user tinggal di
`~/dev/<nama>` (repo git sendiri, symlink ke `~/.claude/skills/<nama>`);
skill repo PA menjadi lapisan tipis yang kalimat pertamanya menyuruh memuat
skill user, atau skill penuh bila terikat format PENS. Gelombang subagen
paralel hanya untuk pekerjaan yang tidak berbagi berkas.

**Tech stack:** Python 3 stdlib (validator), skill-creator `scripts.run_eval`
(uji pemicu, `uv run`), git, GitHub CLI (hanya bila user meminta push).

## Keputusan user (21 Nov 2026)

1. Skill yang diekstrak ke scope user ditulis bahasa Inggris. Skill repo PA,
   kode, docs, dan laporan tetap bahasa Indonesia.
2. Diekstrak: `tautan-lokal`, `batas-tidak-diam`, `tulis-tanpa-slop`,
   `kicad-pcb-pa` (bagian umum), `ingest-word` (bagian umum);
   `tanpa-komentar-kode` dilebur ke `no-code-comments` yang sudah ada.
   Tetap di repo: `deck-pa`, `struktur-pa`, `tabel-pa`, `buku-ikut-proposal`.
3. Riwayat tertulis dipangkas seperti finance-project: dokumen menjelaskan
   kondisi kini, riwayat ada di git; `docs/arsip/` dan `model/docs/arsip/`
   dikosongkan bertahap sesudah fakta operasional dipisahkan.
4. Format eval skill-creator: `evals/<kasus>/` + `triggers/evals.json` +
   validator CI; skor eval di pesan commit, bukan tabel di repo.

## Batas

- Push, pembuatan repo GitHub, dan penghapusan massal (gelombang 4) hanya
  sesudah user menyetujui daftarnya.
- `laporan/**/*.tex` tidak disentuh rework ini.
- `~/dev/no-code-comments` dipakai juga oleh finance-project: perubahan di
  sana hanya penambahan aturan generik, commit lokal, tanpa push.
- Uji pemicu memakai `CLAUDE_CONFIG_DIR` terpisah; berhenti bila muncul
  berkas `*-skill-*` di `~/.claude/commands`.

## Peta berkas

| Berkas | Gelombang | Isi |
|---|---|---|
| `CLAUDE.md`, `laporan/CLAUDE.md`, `model/CLAUDE.md` | 0 | Aturan keras 8 (format eval), Dokumentasi (pangkas riwayat), tabel "Skill, muat sebelum mulai" |
| `scripts/check_skills.py` (baru), `.github/workflows/checks.yml`, `.gitignore` | 0 | validator struktur skill, pengecualian `triggers/evals.json` |
| `scripts/trigger_eval.sh` (baru) | 0 | runner uji pemicu terisolasi |
| `~/dev/{local-file-links,firmware-bounded-limits,indonesian-antislop-writing,kicad-mcp-pcb,wordcraft-latex-ingest}` (baru) | 1 | repo skill user |
| `~/dev/no-code-comments` | 1 | aturan generik dari `tanpa-komentar-kode` yang belum ada |
| `.claude/skills/*` | 2 | skill repo ditulis ulang, `eval.md` diganti `evals/` + `triggers/` |
| `docs/`, `docs/arsip/`, `model/docs/`, `model/docs/arsip/`, README | 4 | pangkas riwayat |
| kode `model/`, `firmware/`, `scripts/`, `dashboard/`, `presentasi/` | 4 | laporan `deadcode`, pembersihan |
| `.agents/`, `AGENTS.md` | 4 | salinan Codex: dihapus atau dibangkitkan ulang (keputusan user) |

---

## Gelombang 0: aturan dan alat (berurutan, satu agen)

### Tugas 0.1: aturan repo mengikuti keputusan

- [ ] `CLAUDE.md` Aturan keras 8 diganti:

```markdown
8. **Setiap skill punya eval** dalam format skill-creator
   (`.claude/skills/<nama>/evals/<kasus>/{prompt.md,case.yaml,graders/}`) dan
   set pemicu `triggers/evals.json`, dinilai model berbeda dari penulis,
   target lulus semua grader, **maksimal 3 putaran**. Belum lulus sesudah
   putaran ke-3 → berhenti, tulis skor terbaik dan temuannya di pesan
   commit, lalu tanya user. Soal eval sempit dan berjawaban pasti
   (kegagalan aslinya). Skor yang tidak naik dua putaran berturut-turut =
   berhenti lebih awal. Skor tidak disimpan sebagai tabel di repo.
```

- [ ] Bagian "Dokumentasi": butir `docs/arsip/` dan "Riwayat masuk arsip"
  diganti satu butir: "**Riwayat ada di git, bukan di dokumen.** Rencana dan
  catatan yang selesai dihapus sesudah hasilnya tercatat di dokumen yang
  berlaku; fakta operasional yang masih berlaku (lokasi data, cara
  memulihkan, nilai konfigurasi) dipindah dulu ke README atau walkthrough
  komponennya." Butir lain yang menyebut arsip sebagai tujuan pemindahan
  disesuaikan (alat sekali pakai dihapus).
- [ ] Tabel baru di `CLAUDE.md` sesudah "Aturan keras":
  `| Pekerjaan | Muat skill |` satu baris per skill (repo dan user), mengikuti
  `~/dev/finance-project/CLAUDE.md` bagian "Skills — load before you start".
  Diisi ulang di gelombang 2 sesudah nama skill final.
- [ ] Periksa `grep -n "arsip" CLAUDE.md laporan/CLAUDE.md model/CLAUDE.md`
  dan sesuaikan rujukan yang menyuruh memindah ke arsip.
- [ ] Commit dengan diff aturan di badan pesan.

### Tugas 0.2: validator struktur skill

- [ ] Port `~/dev/finance-project/scripts/check_skills.py` (163 baris,
  stdlib) ke `scripts/check_skills.py`: nama fungsi dan pesan bahasa
  Indonesia, perilaku sama (frontmatter `name` = nama folder, `description`
  ≤ 1.024 karakter tanpa baris baru, body < 500 baris, `evals/<kasus>/`
  berisi `prompt.md`, `case.yaml`, `graders/*.md`, `triggers/evals.json`
  berbentuk daftar `{query, should_trigger}` dengan dua kelas). Tambahan
  khusus PA: `.claude/skills/*/eval.md` tidak boleh ada lagi. Opsi
  `--uji` untuk swauji seperti `check_slop.py --uji`.
- [ ] `.github/workflows/checks.yml`: langkah `python3 scripts/check_skills.py`.
  Selama gelombang 2 belum selesai, validator dijalankan dengan
  `--lewati-eval-lama` supaya CI tetap hijau; opsi itu dihapus di akhir
  gelombang 2.
- [ ] `.gitignore`: pastikan `.claude/skills/*/triggers/evals.json` tidak
  terabaikan (`git check-ignore -v` harus rc=1).
- [ ] Periksa: `python3 scripts/check_comments.py scripts/check_skills.py`,
  `python3 scripts/check_skills.py --uji`. Commit.

### Tugas 0.3: runner uji pemicu

- [ ] `scripts/trigger_eval.sh` dari pola runner finance-project (disalin di
  `docs/2026-11-21-riset-rework-skill.md` (dihapus; isi di git `0fc2777`) §Temuan butir 4): argumen
  `<folder skill>...`; `T=$(mktemp -d)`; `config/` berisi salinan kredensial
  Claude Code saja (`~/.claude/.credentials.json`, tanyakan user bila
  berkasnya tidak ada); `proj/` folder kosong dengan `.claude/` sendiri;
  `CLAUDE_CONFIG_DIR=$T/config PYTHONPATH=<skill-creator> uv run -q
  --no-project --with pyyaml python -m scripts.run_eval --eval-set
  <skill>/triggers/evals.json --skill-path <skill> --runs-per-query 1
  --num-workers 4 --timeout 60`; berhenti dengan exit 3 bila
  `~/.claude/commands` memuat `*-skill-*`; ringkasan `nama=… benar=…/20`.
  Path skill-creator dicari dengan
  `find ~/.claude/skills -path '*skill-creator/scripts/run_eval.py'`.
- [ ] Tanpa komentar (aturan keras 5). Uji dengan satu skill yang sudah
  punya set pemicu: `~/dev/no-code-comments`. Catat biaya (jumlah panggilan)
  di `scripts/README.md`. Commit.

## Gelombang 1: skill user (paralel, satu agen per repo)

Brief tiap agen memuat: SKILL.md lama, `eval.md` lama, struktur acuan
`~/dev/no-code-comments` (`SKILL.md`, `README.md`, `CLAUDE.md`, `evals/`,
`triggers/evals.json`, `scripts/check_skill.py`, `.github/workflows/tests.yml`),
konvensi di `docs/2026-11-21-riset-rework-skill.md` (dihapus; isi di git `0fc2777`) §Konvensi, dan aturan
"setiap aturan lama dipetakan: skill user, skill repo, atau dibuang dengan
alasan usang".

| Repo baru | Dari | Isi user (Inggris) | Sisa di repo PA |
|---|---|---|---|
| `~/dev/local-file-links` | `tautan-lokal` | seluruhnya | tidak ada (skill repo dihapus) |
| `~/dev/firmware-bounded-limits` | `batas-tidak-diam` | batas buffer, antrean, durasi, kapasitas; operasi lambat di loop | modul PA (LittleFS, PSRAM, nama berkas firmware) |
| `~/dev/indonesian-antislop-writing` | `tulis-tanpa-slop` + `scripts/check_slop.py` | katalog pola, prinsip, prosedur, pemeriksa (nama skrip Inggris, pola tetap Indonesia) | aturan rumah `laporan/CLAUDE.md`, path buku |
| `~/dev/kicad-mcp-pcb` | `kicad-pcb-pa` | alur KiCad 9 MCP, Freerouting, baca pad, cek board | board PA, net, `cek_board.py` |
| `~/dev/wordcraft-latex-ingest` | `ingest-word` | alur cadang → dry-run → konfirmasi → sync → rapikan → build | path buku, `make pdf-bersih`, binary branch lokal |

Langkah per agen:
- [ ] `git init ~/dev/<repo>`, tulis berkas mengikuti acuan, `check_skill.py`
  dan `check_comments.py` hijau, commit lokal.
- [ ] Eval satu kasus atau lebih dari kegagalan asli (soal `eval.md` lama
  dikonversi), satu putaran (penulis sonnet, penilai haiku, dijalankan
  koordinator), skor di pesan commit.
- [ ] `triggers/evals.json` 20 kueri (10 memicu, 10 mirip tidak memicu,
  campuran Indonesia dan Inggris).
- [ ] Koordinator: `ln -s ~/dev/<repo> ~/.claude/skills/<repo>`, peta
  invarian oleh peninjau berbeda model, lalu commit di repo PA untuk
  lapisan tipisnya (gelombang 2).
- [ ] `tanpa-komentar-kode`: aturan generik yang belum ada di
  `~/dev/no-code-comments` (literal numerik bernama, indeks bernama, grep
  nama sebelum menamai, dokumen tujuan) ditambahkan di sana, commit lokal.

## Gelombang 2: skill repo PA (paralel, satu agen per skill)

Bahasa Indonesia, konvensi skill-creator, tanpa riwayat di skill.

- [ ] Lapisan tipis (kalimat pertama memuat skill user): `batas-tidak-diam`,
  `tulis-tanpa-slop`, `kicad-pcb-pa`, `ingest-word`, `tanpa-komentar-kode`.
- [ ] Skill penuh ditulis ulang: `deck-pa`, `struktur-pa`, `tabel-pa`,
  `buku-ikut-proposal`.
- [ ] Butir dari `docs/2026-11-21-pekerjaan-ditunda.md` ikut masuk: prosedur
  bukti memakai `make pdf-bersih` (butir 6), usulan eval `ingest-word`
  rubrik C (butir 3), aturan `narasi-pa` tanpa padanan dinilai satu per
  satu untuk `tulis-tanpa-slop` (butir 4; masuk atau dibuang dengan alasan).
- [ ] `ingest-word` hasil pilot gaya provenfix (`temuan.md`, `referensi/`,
  `templat/`) diselaraskan: alasan satu kalimat tanpa tanggal di SKILL.md,
  `temuan.md` dihapus, `templat/` dipertahankan bila masih dirujuk.
- [ ] `eval.md` tiap skill dikonversi ke `evals/<kasus>/`; tabel riwayat
  skor tidak dibawa (sudah ada di git).
- [ ] `.claude/skills/README.md` menjadi indeks + layout + prosedur eval
  (acuan `~/dev/finance-project/.claude/skills/README.md`); tabel
  "Skill, muat sebelum mulai" di `CLAUDE.md` diisi.
- [ ] Peta invarian per skill oleh peninjau berbeda model; satu commit per
  skill; akhir gelombang: opsi `--lewati-eval-lama` validator dihapus,
  `python3 scripts/check_skills.py` hijau.

## Gelombang 3: eval (koordinator)

- [ ] Eval perilaku satu putaran per skill (repo dan user) yang belum
  dinilai di gelombang 1–2; maksimal 3 putaran sesuai Aturan keras 8.
- [ ] Uji pemicu baseline sekali per skill dengan `scripts/trigger_eval.sh`
  (sekitar 20 panggilan Opus per skill, 15 skill sekitar 300 panggilan;
  dijalankan bertahap supaya tidak menghabiskan kuota). Hasil di pesan
  commit; description hanya diubah bila skor naik di atas noise.

## Gelombang 4: docs dan kode (laporan dulu, eksekusi sesudah user setuju)

- [ ] Inventaris riwayat: daftar dokumen bertanggal di `docs/`,
  `docs/arsip/`, `model/docs/arsip/`, narasi bertanggal di README dan
  walkthrough. Tiap butir diberi label `hapus` atau `pindahkan fakta ke
  <berkas>`; fakta operasional (lokasi data, cara memulihkan, nilai
  konfigurasi) tidak boleh hilang. Daftar diserahkan ke user.
- [ ] Audit `deadcode` (skill `deadcode`) atas `model/`, `firmware/`,
  `scripts/`, `dashboard/`, `presentasi/`: laporan saja, diserahkan ke
  user.
- [ ] Sapuan pola tulisan AI di README dan docs berbahasa Indonesia dengan
  `check_slop.py` (aturan rumah berlaku); kode sudah nol komentar
  (`check_comments.py`), jadi `antislop-code` hanya memeriksa teks bantuan
  CLI dan deskripsi Makefile.
- [ ] `.agents/` dan `AGENTS.md`: usulan hapus (git menyimpan) atau
  bangkitkan ulang dari `.claude/skills/`; keputusan user.
- [ ] Sesudah user menyetujui daftar: eksekusi per kategori, satu commit per
  kategori, peninjau memeriksa tidak ada fakta operasional yang hilang.

## Gelombang 5: penutup

- [ ] `docs/2026-11-21-pekerjaan-ditunda.md` diperbarui (butir yang selesai
  dihapus).
- [ ] Laporan akhir: tabel skill (lama → baru, user/repo, skor eval, skor
  pemicu), commit, dan pertanyaan push: repo PA, dan pembuatan repo GitHub
  private `mrrizaldi/<nama>` untuk lima skill user (hanya atas perintah).

## Urutan dan paralelisme

| Gelombang | Paralel | Gate |
|---|---|---|
| 0 | tidak (aturan dan alat bersama) | — |
| 1 | lima agen, satu per repo user | — |
| 2 | tiga sampai empat agen per batch, satu per skill | — |
| 3 | koordinator, bertahap | kuota |
| 4 | dua agen (inventaris docs, audit kode) | user menyetujui daftar hapus |
| 5 | — | user memutuskan push dan repo GitHub |

## Fakta operasional di arsip yang harus dipindah sebelum gelombang 4

Ditemukan saat gelombang 1–2. Berkas arsip ini tidak boleh dihapus sebelum
faktanya ada di dokumen yang berlaku.

| Berkas arsip | Fakta yang belum ada di dokumen aktif | Tujuan |
|---|---|---|
| `model/docs/arsip/2026-10-08-pcb-rev2-adjustment.md` | divider 2k2/3k3 di keempat jalur TFT dihapus (R3, R4, R6, R8), R2/R5/R7/R9 jadi jumper atau 33 Ω peredam ringing SCK; CS TFT diikat ke GND sehingga firmware wajib `SPI_MODE3`; alasan VCC modul buzzer 3V3 bukan 5V; GPIO ESP32-S3 tidak tahan 5 V sebagai pengikat semua perubahan; opsi BLK TFT ke GPIO 12 untuk PWM | `hardware/mainboard/README.md` §Perbedaan terhadap skematik rev2 |
| `docs/arsip/2026-10-19-referensi-pra-2020.md` | rasional per entri pustaka pra-2020 | dirujuk `CLAUDE.md` bagian Menulis laporan; pindah ke dokumen laporan yang berlaku |
| `model/docs/arsip/2026-09-16-daya-design.md` | rancangan pengukuran daya | dirujuk `model/CLAUDE.md`; pindah ke walkthrough daya |
| `model/docs/arsip/2026-09-19-faseG-changelog.md` §2, `2026-09-19-faseB-changelog.md` §9 | detail ablasi learning rate dan database latih | dirujuk tabel `model/CLAUDE.md`; pindah ke walkthrough model |

## Status (22 Nov 2026)

Gelombang 0–3 selesai. Gelombang 4 bagian riwayat dokumen dieksekusi
22 Nov 2026 sesuai keputusan user atas `inventaris-riwayat.md`: fakta
operasional dipindah, `docs/arsip/` dan `model/docs/arsip/` dihapus,
dokumen kerja selesai dihapus; data uji coba `model/data/arsip/` dan
`model/artifacts/arsip/` dipertahankan. Kode mati dihapus (`pio run`,
`pio test -e native` 23/23, pytest 92 lulus), `.agents/` dan `AGENTS.md`
dihapus, dan sapuan pola tulisan AI di 27 dokumen Markdown menurunkan galat
`check_slop` dari 160 ke 43 (sisa: daftar pertanyaan latihan di walkthrough,
sengaja dibiarkan). Sisa pekerjaan di `docs/2026-11-21-pekerjaan-ditunda.md`.
Uji pemicu baseline (`scripts/trigger_eval.sh`, 1 run per kueri): semua skill
menolak 10/10 kueri yang tidak boleh memicu; memicu benar 0–3/10 (repo:
batas-tidak-diam 3, buku-ikut-proposal 3, tulis-tanpa-slop 3, deck-pa 2,
kicad-pcb-pa 2, tabel-pa 2, struktur-pa 1, tanpa-komentar-kode 1,
ingest-word 0; user: local-file-links 2, wordcraft-latex-ingest 2,
firmware-bounded-limits 1, kicad-mcp-pcb 1, indonesian-antislop-writing 0,
no-code-comments 2). Mitigasi: tabel "Skill, muat sebelum mulai" di
`CLAUDE.md`; description tidak dioptimasi (finance-project tidak mendapat
kenaikan). Push repo PA dan pembuatan repo GitHub skill user menunggu user.
