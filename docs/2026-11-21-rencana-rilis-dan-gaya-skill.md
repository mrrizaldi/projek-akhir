# Rilis bernomor laporan, narasi-pa nonaktif, cek klaim, gaya skill

> **Untuk agen pelaksana:** WAJIB memakai sub-skill
> superpowers:subagent-driven-development (dianjurkan) atau
> superpowers:executing-plans untuk menjalankan rencana ini per tugas. Langkah
> memakai kotak centang (`- [ ]`).

**Tujuan:** PDF dan DOCX buku-pa dan progres-pa-1 bisa dibekukan sebagai rilis
bernomor yang dibandingkan berdampingan lewat `scripts/sajikan.py`,
`tulis-tanpa-slop` menggantikan `narasi-pa`, klaim tanpa angka dicek ke
sumbernya, dan skill repo ditulis ulang dengan gaya provenfix.

**Arsitektur:** `scripts/rilis.py` membangun laporan dari sebuah commit di git
worktree sementara, menyalin PDF dan DOCX ke `laporan/rilis/<proyek>/vN/`
(gitignored), membuat PDF latexdiff terhadap versi sebelumnya, dan memasang tag
git beranotasi `rilis/<proyek>/vN` sehingga setiap rilis bisa dibangun ulang.
`sajikan.py` menampilkan folder rilis dan halaman banding dua PDF berdampingan.

**Tech stack:** Python 3 stdlib, git worktree, pdflatex/bibtex lewat
`laporan/shared/Makefile.inc`, `latexpand` dan `latexdiff` 1.3.2 (terpasang),
`wordcraft-cli` branch.

Permintaan user (21 Nov 2026): `tulis-tanpa-slop` menggantikan `narasi-pa`,
`narasi-pa` dinonaktifkan tanpa dihapus, gaya baru belum diperluas ke bab
lain, klaim tanpa angka dicek benar-benar, pekerjaan opsional yang ringan
dijalankan, rilis bernomor setiap user bilang "checkpoint" dengan v0 sebelum
`tulis-tanpa-slop` dan v1 sesudahnya, serta skill repo ditulis ulang mengikuti
gaya skill provenfix (`~/dev/before-after`).

## Keputusan bawaan (bisa diubah user sebelum eksekusi)

1. **Berkas rilis tidak di-commit.** `laporan/rilis/` masuk
   `laporan/.gitignore`; yang di-commit hanya tag `rilis/<proyek>/vN`.
   Alasan: PDF sekitar 3,5 MB per buku, tiga berkas per rilis per buku akan
   membengkakkan repo, padahal tag cukup untuk membangun ulang. Alternatif:
   commit PDF rilis (repo bertambah sekitar 10 MB per checkpoint).
2. **v0 = commit `ff90c78`** (tag `backup/pra-antislop-20261121-1127`), **v1 =
   commit `39d0268`** (perubahan isi laporan terakhir) untuk kedua buku.
   buku-pa tidak disunting `tulis-tanpa-slop`; v1-nya hanya memuat judul
   DAFTAR ISI dan kalimat TinyML yang kembali tercetak.
3. **`narasi-pa` dipindah ke `.claude/skills-arsip/narasi-pa/`** lewat
   `git mv`. Claude Code hanya memuat skill di `.claude/skills/`, jadi skill
   itu tidak terpicu lagi tetapi isinya tetap bisa dirujuk.
4. **Tag tidak di-push** (push hanya atas permintaan user).

## Peta berkas

| Berkas | Tugas | Isi perubahan |
|---|---|---|
| `.claude/skills/narasi-pa/` → `.claude/skills-arsip/narasi-pa/` | 1 | `git mv` |
| `CLAUDE.md`, `README.md`, `.claude/skills/README.md`, `scripts/README.md` | 1 | rujukan `narasi-pa` → `tulis-tanpa-slop` |
| `.claude/skills/{struktur-pa,tabel-pa,buku-ikut-proposal}/SKILL.md`, `tabel-pa/referensi/templat.md` | 1 | rujukan bernomor ke aturan `narasi-pa` diarahkan ke berkas arsip |
| `.claude/skills/ingest-word/SKILL.md` | 1 | langkah format menjalankan `cek_slop.py` |
| `scripts/rilis.py` (baru) | 2 | pembuat rilis |
| `laporan/shared/Makefile.inc`, `laporan/.gitignore` | 2 | target `make rilis`, ignore `rilis/` |
| `scripts/README.md`, `laporan/CLAUDE.md`, `CLAUDE.md` | 2 | prosedur rilis, pemicu "checkpoint" |
| `scripts/sajikan.py` | 3 | tautan dan halaman `/banding` |
| `docs/2026-11-21-rencana-rilis-dan-gaya-skill/klaim.md` (baru) | 5 | laporan cek klaim |
| `laporan/progres-pa-1/bab/bab2.tex:96` | 6 | rapikan baris komentar |
| `.claude/skills/README.md` | 7 | bagian "Cara menulis skill" (gaya provenfix) |
| `.claude/skills/<nama>/` | 7–8 | SKILL.md ditulis ulang, `temuan.md`, `referensi/`, `templat/` bila perlu |

Di luar lingkup: `.agents/skills/` dan `AGENTS.md` (salinan untuk Codex,
terakhir disalin 5 Nov 2026, sudah berbeda dari `.claude/skills/`). Dicatat di
laporan akhir, tidak disentuh.

---

### Tugas 1: Nonaktifkan `narasi-pa`, `tulis-tanpa-slop` jadi acuan paragraf

**Berkas:** lihat peta berkas, baris Tugas 1.

- [ ] **Langkah 1: Pindahkan skill**

```bash
cd /home/mrrizaldi/dev/projek-akhir
mkdir -p .claude/skills-arsip
git mv .claude/skills/narasi-pa .claude/skills-arsip/narasi-pa
ls .claude/skills | grep -c narasi-pa
```
Diharapkan: `0`.

- [ ] **Langkah 2: Ganti rujukan umum.** Di `CLAUDE.md` bagian "Menulis
  laporan", kalimat acuan menjadi:

```markdown
Acuan penulisan = empat skill di `.claude/skills/`: `struktur-pa` (kerangka
bab, benang merah, register, placeholder gambar, QA sebelum kumpul),
`tulis-tanpa-slop` (paragraf tanpa pola tulisan AI, diperiksa
`scripts/cek_slop.py`), `tabel-pa` (tabel), dan `buku-ikut-proposal` (Bab 1
dan sinkronisasi proposal). `narasi-pa` dinonaktifkan 21 Nov 2026 dan
disimpan di `.claude/skills-arsip/narasi-pa/` sebagai rujukan.
```

  `README.md:78` dan `.claude/skills/README.md:11`: `narasi-pa` diganti
  `tulis-tanpa-slop`; baris `narasi-pa` di tabel `.claude/skills/README.md`
  dihapus dan diganti satu kalimat di bawah tabel: "`narasi-pa` nonaktif,
  disimpan di `.claude/skills-arsip/` sebagai rujukan." `scripts/README.md:85`:
  "(skill `tabel-pa` dan `tulis-tanpa-slop`)".

- [ ] **Langkah 3: Rujukan bernomor.** Rujukan ke aturan atau arketipe
  bernomor `narasi-pa` yang tidak ada padanannya di `tulis-tanpa-slop` diubah
  menjadi rujukan berkas arsip, isinya tetap:
  - `struktur-pa/SKILL.md:15` → "Paragraf diatur skill `tulis-tanpa-slop`";
  - `struktur-pa/SKILL.md:51` → "(`.claude/skills-arsip/narasi-pa/SKILL.md`
    aturan 7, `cek_tabel.py` N-META)";
  - `struktur-pa/SKILL.md:211` → kolom ketiga "aturan 8, `tulis-tanpa-slop`,
    `laporan/CLAUDE.md`";
  - `tabel-pa/SKILL.md:158` → "`.claude/skills-arsip/narasi-pa/SKILL.md`
    aturan 1–3";
  - `tabel-pa/SKILL.md:179` → "(skill `tulis-tanpa-slop`)";
  - `tabel-pa/referensi/templat.md:32` → "(skill `tulis-tanpa-slop`)";
  - `tabel-pa/referensi/templat.md:193` → "(arketipe "Pemosisian" di
    `.claude/skills-arsip/narasi-pa/SKILL.md`)";
  - `buku-ikut-proposal/SKILL.md:29` → "skill `tulis-tanpa-slop`".
  `eval.md` mana pun tidak diubah (riwayat).

- [ ] **Langkah 4: `ingest-word` memakai pemeriksa baru.** Di langkah format
  `.claude/skills/ingest-word/SKILL.md` (bagian yang memeriksa titik koma),
  tambahkan perintah yang dijalankan pada setiap `.tex` yang ditulis sync:

```bash
python3 ../../scripts/cek_slop.py --ringkas bab/<berkas>.tex
```
  dengan kalimat: "Temuan `galat` diajukan ke user sebagai usulan format,
  satu usulan per temuan; kalimat penulis tidak ditulis ulang tanpa
  konfirmasi."

- [ ] **Langkah 5: Celah yang belum tertutup.** Tambahkan ke
  `docs/2026-11-21-skill-anti-slop.md` bagian "Sisa pekerjaan" butir baru:
  daftar aturan `narasi-pa` yang tidak punya padanan di `tulis-tanpa-slop`.
  Cara mendapatkannya: baca kedua SKILL.md, tulis satu baris per aturan
  `narasi-pa` (nomor, ringkasan enam kata, ada/tidak di `tulis-tanpa-slop`).
  Hapus butir 4 lama (posisi skill belum diputuskan) karena sudah diputuskan.

- [ ] **Langkah 6: Periksa**

```bash
cd /home/mrrizaldi/dev/projek-akhir
grep -rn "narasi-pa" CLAUDE.md README.md scripts/README.md .claude/skills/ | grep -v "skills-arsip\|eval.md"
```
Diharapkan: hanya baris yang menyebut `narasi-pa` sebagai skill nonaktif
(CLAUDE.md dan README skills). Tidak ada "skill `narasi-pa`" sebagai acuan aktif.

- [ ] **Langkah 7: Commit** dengan keluaran grep langkah 6 di pesan commit.

---

### Tugas 2: `scripts/rilis.py` dan target `make rilis`

**Berkas:** buat `scripts/rilis.py`; ubah `laporan/shared/Makefile.inc`,
`laporan/.gitignore`, `scripts/README.md`, `laporan/CLAUDE.md`, `CLAUDE.md`.

Aturan kode (skill `tanpa-komentar-kode`): nol komentar dan docstring, literal
numerik selain 0/1 diberi nama, argumen CLI lewat argparse.
Pemeriksa: `python3 scripts/cek_komentar.py scripts/rilis.py`.

- [ ] **Langkah 1: Tulis `scripts/rilis.py`**

```python
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AKAR = Path(__file__).resolve().parent.parent
FOLDER_RILIS = AKAR / "laporan" / "rilis"
PROYEK = ("buku-pa", "progres-pa-1")
POLA_TAG = re.compile(r"^rilis/(?P<proyek>[^/]+)/v(?P<nomor>\d+)$")
POLA_GALAT_LOG = re.compile(r"undefined|Overfull")


def git(*argumen, cwd=AKAR):
    hasil = subprocess.run(["git", *argumen], cwd=cwd, capture_output=True, text=True)
    if hasil.returncode:
        gagal(f"git {' '.join(argumen)}: {hasil.stderr.strip()}")
    return hasil.stdout.strip()


def gagal(pesan):
    print(pesan, file=sys.stderr)
    sys.exit(1)


def versi_ada(proyek):
    hasil = {}
    for tag in git("tag", "--list", f"rilis/{proyek}/v*").splitlines():
        cocok = POLA_TAG.match(tag)
        if cocok:
            hasil[int(cocok["nomor"])] = tag
    return hasil


def make(folder, *target):
    hasil = subprocess.run(["make", *target], cwd=folder, capture_output=True, text=True)
    return hasil.returncode == 0


def bangun(pohon, proyek):
    folder = pohon / "laporan" / proyek
    if not make(folder, "pdf") or not make(folder, "docx"):
        gagal(f"build {proyek} gagal di {folder}")
    return folder / "output"


def jumlah_halaman(pdf):
    for baris in subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout.splitlines():
        if baris.startswith("Pages:"):
            _, nilai = baris.split()
            return int(nilai)
    return 0


def galat_log(log):
    return sum(1 for baris in log.read_text(errors="replace").splitlines() if POLA_GALAT_LOG.search(baris))


def datarkan(folder):
    return subprocess.run(["latexpand", "main.tex"], cwd=folder, capture_output=True, text=True).stdout


def banding(pohon_lama, pohon_baru, proyek, tujuan):
    lama = pohon_lama / "laporan" / proyek
    baru = pohon_baru / "laporan" / proyek
    (baru / "datar-lama.tex").write_text(datarkan(lama))
    (baru / "datar-baru.tex").write_text(datarkan(baru))
    hasil = subprocess.run(
        ["latexdiff", "--math-markup=0", "datar-lama.tex", "datar-baru.tex"],
        cwd=baru, capture_output=True, text=True,
    )
    if hasil.returncode:
        return None
    (baru / "banding.tex").write_text(hasil.stdout)
    make(baru, "pdf", "MAIN=banding")
    pdf = baru / "output" / "banding.pdf"
    if not pdf.exists():
        return None
    shutil.copy(pdf, tujuan)
    return tujuan


def main():
    parser = argparse.ArgumentParser(
        description="Bekukan PDF dan DOCX laporan sebagai rilis bernomor (tag git rilis/<proyek>/vN)."
    )
    parser.add_argument("proyek", choices=PROYEK)
    parser.add_argument("--rev", default="HEAD", help="commit yang dibekukan (bawaan HEAD)")
    parser.add_argument("--catatan", default="", help="isi pesan tag")
    args = parser.parse_args()

    rev = git("rev-parse", "--short", f"{args.rev}^{{commit}}")
    if args.rev == "HEAD" and git("status", "--porcelain", "--", "laporan"):
        gagal("laporan/ punya perubahan yang belum di-commit; rilis dibangun dari commit, commit dulu")
    ada = versi_ada(args.proyek)
    nomor = max(ada) + 1 if ada else 0
    jalur_isi = [f"laporan/{args.proyek}", "laporan/shared"]
    if ada and not git("diff", "--name-only", ada[max(ada)], rev, "--", *jalur_isi):
        gagal(f"tidak ada perubahan {args.proyek} sejak {ada[max(ada)]}")
    nama = f"{args.proyek}-v{nomor}"
    tujuan = FOLDER_RILIS / args.proyek / f"v{nomor}"
    if tujuan.exists():
        gagal(f"{tujuan} sudah ada")

    with tempfile.TemporaryDirectory(prefix="rilis-") as sementara:
        pohon_baru = Path(sementara, "baru")
        git("worktree", "add", "--detach", str(pohon_baru), rev)
        try:
            keluaran = bangun(pohon_baru, args.proyek)
            tujuan.mkdir(parents=True)
            shutil.copy(keluaran / "main.pdf", tujuan / f"{nama}.pdf")
            shutil.copy(keluaran / "main.docx", tujuan / f"{nama}.docx")
            halaman = jumlah_halaman(tujuan / f"{nama}.pdf")
            galat = galat_log(keluaran / "main.log")
            print(f"versi=v{nomor}\nrev={rev}\npdf={tujuan / f'{nama}.pdf'}\nhalaman={halaman}\ngalat_log={galat}")
            if ada:
                sebelumnya = max(ada)
                pohon_lama = Path(sementara, "lama")
                git("worktree", "add", "--detach", str(pohon_lama), ada[sebelumnya])
                try:
                    pdf_banding = banding(
                        pohon_lama, pohon_baru, args.proyek,
                        tujuan / f"banding-v{sebelumnya}-v{nomor}.pdf",
                    )
                finally:
                    git("worktree", "remove", "--force", str(pohon_lama))
                print(f"banding={pdf_banding}" if pdf_banding else "warn=latexdiff gagal, banding tidak dibuat")
        finally:
            git("worktree", "remove", "--force", str(pohon_baru))

    pesan = f"{args.catatan}\n\nhalaman={halaman} galat_log={galat}".strip()
    git("tag", "-a", f"rilis/{args.proyek}/v{nomor}", rev, "-m", pesan)
    print(f"tag=rilis/{args.proyek}/v{nomor}")


if __name__ == "__main__":
    main()
```

- [ ] **Langkah 2: Makefile dan gitignore.** Di `laporan/shared/Makefile.inc`
  tambahkan baris bantuan sesudah baris `make cek-docx`:

```make
##   make rilis   — bekukan PDF+DOCX dari HEAD jadi rilis bernomor (scripts/rilis.py)
```
  tambahkan `rilis` ke `.PHONY`, dan target sesudah `cek-docx`:

```make
rilis:
	python3 ../../scripts/rilis.py $(notdir $(CURDIR)) --catatan "$(CATATAN)"
```
  Di `laporan/.gitignore` tambahkan:

```
# Rilis bernomor (dibangun ulang dari tag rilis/<proyek>/vN)
rilis/
```

- [ ] **Langkah 3: Periksa komentar dan bantuan**

```bash
cd /home/mrrizaldi/dev/projek-akhir
python3 scripts/cek_komentar.py scripts/rilis.py; echo rc=$?
python3 scripts/rilis.py --help | head -3
python3 scripts/rilis.py surat-magang; echo rc=$?
```
Diharapkan: `rc=0`; teks bantuan argparse; pilihan ditolak argparse dengan
`rc=2`.

- [ ] **Langkah 4: Uji penolakan pohon kotor.** Buat perubahan sementara,
  jalankan, kembalikan:

```bash
cd /home/mrrizaldi/dev/projek-akhir
echo "" >> laporan/progres-pa-1/main.tex
python3 scripts/rilis.py progres-pa-1; echo rc=$?
git checkout -- laporan/progres-pa-1/main.tex
```
Diharapkan: pesan "laporan/ punya perubahan yang belum di-commit ..." dan
`rc=1`, tanpa tag baru (`git tag --list 'rilis/*'` kosong).

- [ ] **Langkah 5: Dokumentasi.** `scripts/README.md` bagian baru "rilis.py"
  berisi prosedur bernomor:
  1. commit semua perubahan laporan;
  2. `cd laporan/<proyek> && make rilis CATATAN="..."` atau
     `python3 scripts/rilis.py <proyek> --rev <commit> --catatan "..."`;
  3. keluaran `versi=`, `rev=`, `pdf=`, `halaman=`, `galat_log=`, `banding=`
     atau `warn=`, `tag=`;
  4. hasil di `laporan/rilis/<proyek>/vN/` (`<proyek>-vN.pdf`, `.docx`,
     `banding-vM-vN.pdf`), tampil di `sajikan.py`;
  5. membangun ulang rilis yang folder-nya hilang: `git worktree add --detach
     /tmp/r rilis/<proyek>/vN && cd /tmp/r/laporan/<proyek> && make pdf docx`,
     lalu `git worktree remove /tmp/r`.
  Penolakan: pohon `laporan/` kotor, tidak ada perubahan sejak rilis terakhir,
  folder versi sudah ada.

  `laporan/CLAUDE.md` bagian baru "### Rilis bernomor" berisi ringkasan dua
  kalimat dan rujukan ke `scripts/README.md`. `CLAUDE.md` root bagian Build
  menambah satu baris: "User bilang **checkpoint** → commit dulu, lalu `make
  rilis` di `laporan/buku-pa` dan `laporan/progres-pa-1` (yang ditolak karena
  tidak berubah dilewati), laporkan `versi=` dan `banding=`. Tag rilis tidak
  di-push."

- [ ] **Langkah 6: Commit** dengan keluaran langkah 3–4 di pesan commit.

---

### Tugas 3: Halaman banding di `sajikan.py`

**Berkas:** ubah `scripts/sajikan.py`; `scripts/README.md` bagian sajikan.

- [ ] **Langkah 1: Tambahkan import dan konstanta** di `scripts/sajikan.py`:

```python
import re
from urllib.parse import parse_qsl, quote, urlsplit

POLA_RILIS = re.compile(r"^laporan/rilis/(?P<proyek>[^/]+)/v(?P<nomor>\d+)$")
```
  (baris `from urllib.parse import quote` lama diganti baris di atas).

- [ ] **Langkah 2: Fungsi tautan dan halaman banding**

```python
def pdf_rilis(proyek, nomor):
    return f"laporan/rilis/{proyek}/v{nomor}/{proyek}-v{nomor}.pdf"


def tautan_banding(folder):
    cocok = POLA_RILIS.match(folder)
    if not cocok or int(cocok["nomor"]) == 0:
        return ""
    proyek, nomor = cocok["proyek"], int(cocok["nomor"])
    lama, baru = pdf_rilis(proyek, nomor - 1), pdf_rilis(proyek, nomor)
    return (
        f' <a href="/banding?lama={quote(lama)}&amp;baru={quote(baru)}">'
        f"banding v{nomor - 1} dan v{nomor}</a>"
    )


def pdf_aman(rel):
    jalur = (AKAR / rel).resolve()
    return jalur.suffix == ".pdf" and jalur.is_file() and AKAR in jalur.parents


def halaman_banding(kueri):
    param = dict(parse_qsl(kueri))
    lama = param.get("lama", "")
    baru = param.get("baru", "")
    if not (pdf_aman(lama) and pdf_aman(baru)):
        return None
    bingkai = "".join(
        f'<section><h2>{html.escape(rel)}</h2><iframe src="/{quote(rel)}"></iframe></section>'
        for rel in (lama, baru)
    )
    return (
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<title>Banding rilis</title><style>"
        "body{margin:0;font:14px system-ui,sans-serif;background:#fff;color:#222}"
        "main{display:flex;height:100vh}section{flex:1;display:flex;flex-direction:column}"
        "h2{font-size:.9rem;margin:.3rem .5rem}iframe{flex:1;border:0;border-left:1px solid #ccc}"
        "@media(max-width:48rem){main{flex-direction:column;height:auto}iframe{height:80vh}}"
        "@media(prefers-color-scheme:dark){body{background:#181818;color:#ddd}}"
        f"</style><main>{bingkai}</main>"
    )
```

- [ ] **Langkah 3: Pasang di indeks dan penangan.** Di `halaman_indeks`, baris
  judul grup menjadi:

```python
        bagian.append(f"<h2>{html.escape(folder)}{tautan_banding(folder)}</h2><ul>{baris}</ul>")
```
  Kelas `Penangan` menjadi:

```python
class Penangan(SimpleHTTPRequestHandler):
    def kirim_html(self, isi):
        data = isi.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        alamat = urlsplit(self.path)
        if alamat.path == "/":
            return self.kirim_html(halaman_indeks())
        if alamat.path == "/banding":
            isi = halaman_banding(alamat.query)
            if isi is None:
                return self.send_error(404)
            return self.kirim_html(isi)
        return super().do_GET()
```

- [ ] **Langkah 4: Periksa** (sesudah Tugas 4 membuat v0 dan v1; bila Tugas 3
  dikerjakan lebih dulu, buat dua PDF palsu di
  `laporan/rilis/uji/v0/uji-v0.pdf` dan `v1/uji-v1.pdf` dengan `cp` dari
  `laporan/progres-pa-1/output/main.pdf`, lalu hapus sesudahnya):

```bash
cd /home/mrrizaldi/dev/projek-akhir
python3 scripts/cek_komentar.py scripts/sajikan.py; echo rc=$?
python3 scripts/sajikan.py 8702 & PID=$!; sleep 1
curl -s http://127.0.0.1:8702/ | grep -o 'banding v0 dan v1' | head -2
curl -s -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:8702/banding?lama=laporan/rilis/progres-pa-1/v0/progres-pa-1-v0.pdf&baru=laporan/rilis/progres-pa-1/v1/progres-pa-1-v1.pdf"
curl -s -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:8702/banding?lama=../../etc/passwd&baru=x.pdf"
kill $PID
```
Diharapkan: `rc=0`; `banding v0 dan v1` (sekali per buku); `200`; `404`.
Lalu buka halaman banding dengan Playwright MCP, ambil tangkapan layar, dan
pastikan dua PDF tampil berdampingan (bukti visual untuk pesan commit).

- [ ] **Langkah 5: Dokumentasi** satu paragraf di bagian sajikan
  `scripts/README.md`: folder `laporan/rilis/<proyek>/vN` dengan N > 0 punya
  tautan "banding vN-1 dan vN" yang membuka dua PDF berdampingan; parameter
  `lama`/`baru` hanya menerima PDF di dalam repo.

- [ ] **Langkah 6: Commit** dengan keluaran langkah 4.

---

### Tugas 4: Rilis v0 dan v1 kedua buku

- [ ] **Langkah 1: v0**

```bash
cd /home/mrrizaldi/dev/projek-akhir
python3 scripts/rilis.py progres-pa-1 --rev ff90c78 --catatan "v0: sebelum tulis-tanpa-slop"
python3 scripts/rilis.py buku-pa --rev ff90c78 --catatan "v0: sebelum tulis-tanpa-slop"
```
Diharapkan: `versi=v0`, `galat_log=0`, `tag=rilis/<proyek>/v0`, tanpa baris
`banding=`. `halaman=` dicatat (pembanding: sesudah uji coba progres-pa-1 125
dan buku-pa 139). `galat_log` bukan 0 → berhenti dan laporkan.

- [ ] **Langkah 2: v1**

```bash
python3 scripts/rilis.py progres-pa-1 --rev 39d0268 --catatan "v1: Bab 2-4 tulis-tanpa-slop, judul DAFTAR ISI, empat syarat uji"
python3 scripts/rilis.py buku-pa --rev 39d0268 --catatan "v1: judul DAFTAR ISI, kalimat TinyML tercetak"
```
Diharapkan: `versi=v1`, `banding=.../banding-v0-v1.pdf`, `tag=...v1`.
Bila `warn=latexdiff gagal`: jalankan latexdiff manual di worktree untuk
membaca galatnya, perbaiki opsi di `banding()` (mis. `--exclude-textcmd`
untuk perintah yang memecah, atau `--config PICTUREENV=...`), uji ulang dengan
menghapus folder dan tag v1 (`rm -r laporan/rilis/<proyek>/v1 && git tag -d
rilis/<proyek>/v1`). Maksimal 3 percobaan; masih gagal → rilis tanpa banding,
catat galatnya di laporan akhir.

- [ ] **Langkah 3: Periksa isi banding**

```bash
pdftotext laporan/rilis/progres-pa-1/v1/banding-v0-v1.pdf - | grep -c "Akibatnya\|sehingga mewakili" 
pdftotext laporan/rilis/buku-pa/v1/banding-v0-v1.pdf - | grep -o "TinyML memungkinkan model" | head -1
git tag --list 'rilis/*'
```
Diharapkan: angka > 0, satu baris TinyML, empat tag.

- [ ] **Langkah 4: Bukti visual.** Jalankan `sajikan.py`, buka indeks dan
  halaman banding progres-pa-1 dengan Playwright MCP, simpan tangkapan layar
  ke scratchpad. Tidak ada commit (berkas rilis gitignored, tag sudah
  dibuat); keluaran langkah 1–3 masuk laporan akhir.

---

### Tugas 5: Cek klaim tanpa angka

Hanya membaca dan menulis laporan; naskah laporan tidak disunting di tugas
ini.

- [ ] **Langkah 1: Brief subagen riset** (satu subagen, model sonnet) dengan
  isi:
  - Klaim yang dicek, di `laporan/progres-pa-1/bab/` dan padanannya di
    `laporan/buku-pa/bab/` (temukan dengan grep):
    1. bab2: akurasi Mulyawan ditulis "tinggi";
    2. bab2: "baru sedikit yang dibuktikan";
    3. bab2: "salah satu dari sedikit studi";
    4. bab2: "dua keperluan yang berbeda" (hanya satu diuraikan);
    5. bab3: "menekan jumlah parameter secara drastis";
    6. bab3: "model yang telah teruji akurat".
  - Untuk tiap klaim: baca paragrafnya, baris `% sumber:` di dekatnya, dan
    `\cite` yang dipakai; cari kunci sitasi di `laporan/shared/*.bib` atau
    `.bib` proyek, buka PDF-nya di `laporan/pustaka/` (Read dengan `pages=`).
  - Laporkan per klaim: lokasi `berkas:baris` di kedua buku, kutipan kalimat
    naskah, kutipan sumber verbatim dengan nomor halaman, vonis (didukung
    angka / didukung tanpa angka / tidak didukung / sumber tidak tersedia),
    dan satu usulan kalimat pengganti yang mematuhi `laporan/CLAUDE.md`
    (tanpa titik dua, titik koma, em dash; istilah Inggris miring; desimal
    koma; `~\cite{}`). Untuk klaim 2 dan 3, sebut berapa studi di tinjauan
    pustaka buku ini yang memang mengukur hal tersebut.
  - Larangan: tidak menyunting berkas apa pun selain laporan hasil; tidak
    mengirim email user ke layanan mana pun (Unpaywall, API penerbit); bila
    PDF tidak ada di `laporan/pustaka/`, cukup tulis "sumber tidak tersedia".
  - Keluaran ditulis ke
    `docs/2026-11-21-rencana-rilis-dan-gaya-skill/klaim.md`.

- [ ] **Langkah 2: Verifikasi silang.** Ambil dua kutipan sumber secara acak
  dari `klaim.md`, buka halaman PDF yang disebut, pastikan kutipannya ada
  persis. Satu saja tidak cocok → seluruh laporan dikembalikan ke subagen.

- [ ] **Langkah 3: Commit** `klaim.md` dengan hasil verifikasi silang di
  pesan commit, lalu sajikan tabel vonis ke user. Penyuntingan naskah hanya
  sesudah user memilih usulan per klaim (gate), diterapkan ke kedua buku,
  dengan `cek_slop.py --banding` (boleh berubah hanya kalimat klaim), `make
  pdf` 0 undefined/Overfull, satu commit.

---

### Tugas 6: Rapikan sisa teks di baris komentar progres-pa-1 bab2

- [ ] **Langkah 1:** di `laporan/progres-pa-1/bab/bab2.tex:96`, buang sisa
  teks " TinyML memungkinkan model kecerdasan buatan" di ujung baris
  `% sumber:` (kalimat prosa yang sama sudah ada di baris berikutnya).
  Pastikan dulu dengan `sed -n 94,100p`.
- [ ] **Langkah 2: Periksa**

```bash
cd /home/mrrizaldi/dev/projek-akhir/laporan/progres-pa-1
make pdf >/dev/null 2>&1; grep -cE "undefined|Overfull" output/main.log
pdftotext output/main.pdf - | tr '\n' ' ' | grep -o "TinyML memungkinkan model" | wc -l
```
Diharapkan: `0` dan `1`.
- [ ] **Langkah 3: Commit** dengan keluaran langkah 2.

---

### Tugas 7: Gaya skill provenfix, pilot `ingest-word`

Gaya sumber: `~/dev/before-after/SKILL.md`, `references/findings.md`,
`templates/`, `benchmarks/triggers/README.md`. Subagen pelaksana membaca
keempatnya sebelum mulai.

- [ ] **Langkah 1: Tulis panduan gaya** di `.claude/skills/README.md` bagian
  baru "## Cara menulis skill":

```markdown
## Cara menulis skill

Gaya mengikuti skill provenfix (`~/dev/before-after/SKILL.md`).

1. **Description** menyebut apa yang dikerjakan, kapan dipakai (frasa pemicu
   seperti yang diketik user, Indonesia dan Inggris), bukan untuk apa, dan apa
   yang tidak dilakukannya.
2. **Pembuka** satu atau dua kalimat tentang hasil akhir.
3. **`## Aturan dasar`** dibuka "Tiap aturan ada karena melanggarnya pernah
   menggagalkan pekerjaan." Tiap butir diawali frasa tebal, lalu alasan
   singkat yang merujuk `temuan.md` (`temuan #3`).
4. **`## Rujukan`** berupa tabel `| Berkas | Baca bila |`. SKILL.md hanya
   memuat aturan dasar dan prosedur; detail yang berlaku pada kondisi
   tertentu pindah ke `referensi/`.
5. **`## Prosedur`** bernomor mulai 0 (persiapan). Tiap langkah memuat
   perintah persis di blok kode, keluaran yang diharapkan, dan kondisi
   berhenti ("gagal → berhenti, kutip alasannya").
6. **Satu layar konfirmasi** sebelum skill menulis berkas milik user; sesudah
   "ya", lanjut tanpa bertanya lagi kecuali ada langkah yang gagal.
7. **`temuan.md`** daftar bernomor, dibuka "Tiap butir pernah menggagalkan
   satu pekerjaan." Isinya kegagalan nyata: asal skill dan pelajaran dari
   riwayat eval.
8. **`templat/`** untuk keluaran berbentuk tetap (laporan ke user, pesan
   commit).
9. **`eval.md`** tetap (Aturan keras 8).

Isi aturan tidak berubah saat gaya ditulis ulang: setiap aturan lama
dipetakan ke tempat barunya, dan eval dijalankan ulang satu putaran dengan
skor minimal sama dengan skor terbaik sebelumnya.
```

- [ ] **Langkah 2: Tulis ulang `ingest-word`** sesuai panduan: SKILL.md,
  `temuan.md` (dari bagian asal dan riwayat `eval.md`), `templat/ringkasan.md`
  (ringkasan dry-run untuk user). Sekaligus terapkan usulan soal di
  `eval.md` putaran 3: tugas 1 meminta "perintah yang dijalankan sebelum
  menunggu user", rubrik A disesuaikan.

- [ ] **Langkah 3: Peta invarian.** Subagen peninjau (model berbeda dari
  penulis) menerima SKILL.md lama (`git show HEAD:.claude/skills/ingest-word/SKILL.md`)
  dan berkas baru, lalu menulis tabel: aturan lama → lokasi baru. Aturan
  tanpa lokasi baru = gagal, kembalikan ke penulis.

- [ ] **Langkah 4: Eval putaran 4** (izin user 21 Nov 2026): penulis sonnet
  menerima SKILL.md baru + referensi + soal tanpa rubrik, penilai haiku
  menerima soal + rubrik + jawaban. Catat di `eval.md`. Skor < 9 → kembalikan
  SKILL.md lama (`git checkout HEAD -- .claude/skills/ingest-word`) dan
  laporkan.

- [ ] **Langkah 5: Commit** dengan tabel peta invarian dan skor eval, lalu
  **berhenti**: user meninjau pilot sebelum Tugas 8.

---

### Tugas 8: Gaya provenfix untuk skill lain (sesudah user menyetujui pilot)

Skill: `tautan-lokal`, `batas-tidak-diam`, `buku-ikut-proposal`, `deck-pa`,
`kicad-pcb-pa`, `struktur-pa`, `tabel-pa`, `tanpa-komentar-kode`,
`tulis-tanpa-slop`. Tidak termasuk `narasi-pa` (nonaktif).

- [ ] **Langkah 1:** per skill, ulangi Tugas 7 langkah 2–5 tanpa perubahan
  soal eval. Tiga skill per gelombang paralel (subagen penulis berbeda per
  skill), satu commit per skill.
- [ ] **Langkah 2:** skor eval turun dari skor terbaik di `eval.md` → skill
  itu dikembalikan ke versi lama, dicatat, lanjut ke skill berikutnya.
- [ ] **Langkah 3:** sesudah semua, `.claude/skills/README.md` tabel skill
  diperbarui bila description berubah; laporan akhir memuat tabel skill,
  skor lama, skor baru.

---

### Tugas 9 (opsional, paling akhir): lingkungan WordCraft

- [ ] **Langkah 1:** `rustup target add wasm32-unknown-unknown`, lalu
  `cargo xtask ci` di `~/dev/wordcraft` branch
  `fix/latex-env-scopes-declarations`. Catat langkah yang masih gagal
  (test craft-i18n diketahui gagal juga di `main`).
- [ ] **Langkah 2:** bangun aplikasi GUI dari branch (perintah dari
  `~/dev/wordcraft/README.md` atau `AGENTS.md`, dibaca dulu), pasang
  berdampingan dengan versi lama, buka `laporan/progres-pa-1/main.tex`,
  ambil tangkapan layar halaman Daftar Isi. Tidak push, tidak commit di
  WordCraft.
- [ ] **Langkah 3:** perbarui `docs/2026-11-21-pipeline-word-latex.md`
  §Sisa pekerjaan butir 1 dan 3, commit di repo PA.

---

## Urutan dan paralelisme

| Gelombang | Tugas | Catatan |
|---|---|---|
| 1 | 1, 2, 5 (subagen riset), 6 | tidak saling menyentuh berkas; 5 berjalan di latar |
| 2 | 3, 4 | 4 butuh 2; 3 diperiksa dengan hasil 4 |
| 3 | 7 | pilot, berhenti untuk tinjauan user |
| 4 | 8 | sesudah pilot disetujui |
| 5 | 9 | opsional |

Gate user: usulan klaim (Tugas 5 langkah 3), pilot gaya skill (Tugas 7
langkah 5). Semua tugas lain jalan tanpa konfirmasi per langkah; commit
sesudah pemeriksaan hijau, tanpa push.

## Temuan saat eksekusi

1. Build bersih progres-pa-1 dan buku-pa memuat 2 Overfull yang sudah ada
   sejak sebelum uji coba (v0 juga 2): caption Bab 2 dengan daftar sensor
   "AD8232/MAX30102/MLX90614" (5,4 pt, garis miring tidak dipenggal) dan sel
   tabel Bab 4 sekitar baris 868 "Penelitian pendahulu~\cite" (1,2 pt).
   Laporan "0 Overfull" sebelumnya berasal dari `make pdf` inkremental.
   `laporan/CLAUDE.md` kini meminta `make pdf-bersih` untuk bukti; prosedur
   skill yang masih `make pdf` (ingest-word, struktur-pa, buku-ikut-proposal,
   tabel-pa, tulis-tanpa-slop) ikut diganti saat Tugas 7–8 menulis ulang
   skill. Perbaikan dua Overfull menunggu persetujuan user (format saja).
2. v1 kedua buku diambil dari `a516a18` (HEAD saat rilis), bukan `39d0268`,
   supaya checkpoint berikutnya tidak menghasilkan rilis yang hanya berisi
   perubahan komentar dan Makefile. Isi tercetak sama.

## Status (21 Nov 2026)

| Tugas | Status | Commit |
|---|---|---|
| 1 `narasi-pa` nonaktif | selesai | `5c2e7c1`, `33698b6` |
| 2 `rilis.py`, `make rilis` | selesai | `a516a18`, `154ea14` (`make pdf-bersih`) |
| 3 halaman banding `sajikan.py` | selesai | `746222f` |
| 4 rilis v0 dan v1 kedua buku | selesai (tag `rilis/*`, berkas di `laporan/rilis/`) | tanpa commit |
| 5 cek klaim | selesai; user menyetujui keenam usulan, diterapkan ke kedua buku | `cbae792` |
| 6 komentar bab2 | selesai | `4d57449` |
| 7 pilot gaya provenfix `ingest-word` | selesai, eval 9/10, peta invarian LULUS | `a773121` |
| 8 gaya provenfix skill lain | ditunda user | |
| 9 lingkungan WordCraft | ditunda user | |

## Tindak lanjut user

1. **Pilot gaya skill (Tugas 8).** Yang ditinjau user:
   - buka `.claude/skills/ingest-word/SKILL.md` (baru) dan bandingkan dengan
     versi lama `git show a773121^:.claude/skills/ingest-word/SKILL.md`;
   - panjang SKILL.md 108 menjadi 177 baris karena tiap langkah memuat
     perintah, keluaran yang diharapkan, dan kondisi berhenti;
   - skill dipecah empat berkas: `SKILL.md`, `temuan.md` (kegagalan asal
     aturan), `referensi/sync.md` (detail kondisional), `templat/ringkasan.md`
     (layar konfirmasi dry-run);
   - description memuat frasa pemicu bahasa Inggris dan daftar "bukan untuk";
   - dua konfirmasi (dry-run, lalu perbaikan format) dipertahankan walau
     panduan menyebut satu layar konfirmasi.
   Keputusan: setujui lalu terapkan ke sembilan skill lain (tiap skill
   peninjau invarian dan satu putaran eval, sekitar tiga subagen per skill),
   ubah panduan dulu, atau terapkan hanya ke skill tertentu. Usulan eval
   tersisa untuk `ingest-word`: langkah 2 meminta kalimat eksplisit bahwa
   berkas berubah sesudah DOCX dibuat (rubrik C, putaran 4).
2. **Lingkungan WordCraft (Tugas 9).** Target wasm, `cargo xtask ci`, dan
   build GUI dari branch ditunda. Nilainya rendah selama branch tidak
   di-PR ke upstream dan user menyunting lewat `make docx` (DOCX dari
   importer baru); GUI lama hanya berpengaruh bila `main.tex` dibuka
   langsung di aplikasi WordCraft.
