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
    hasil = subprocess.run(["make", *target], cwd=folder, capture_output=True, text=True, errors="replace")
    return hasil.returncode == 0


def bangun(pohon, proyek):
    folder = pohon / "laporan" / proyek
    if not make(folder, "pdf") or not make(folder, "docx"):
        gagal(f"build of {proyek} failed in {folder}")
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
        description="Freeze the report PDF and DOCX as a numbered release (git tag rilis/<project>/vN)."
    )
    parser.add_argument("proyek", choices=PROYEK)
    parser.add_argument("--rev", default="HEAD", help="commit to freeze (default HEAD)")
    parser.add_argument("--catatan", default="", help="tag message body")
    args = parser.parse_args()

    rev = git("rev-parse", "--short", f"{args.rev}^{{commit}}")
    if args.rev == "HEAD" and git("status", "--porcelain", "--", "laporan"):
        gagal("laporan/ has uncommitted changes; the release is built from a commit, commit first")
    ada = versi_ada(args.proyek)
    nomor = max(ada) + 1 if ada else 0
    jalur_isi = [f"laporan/{args.proyek}", "laporan/shared"]
    if ada and not git("diff", "--name-only", ada[max(ada)], rev, "--", *jalur_isi):
        gagal(f"no changes in {args.proyek} since {ada[max(ada)]}")
    nama = f"{args.proyek}-v{nomor}"
    tujuan = FOLDER_RILIS / args.proyek / f"v{nomor}"
    if tujuan.exists():
        gagal(f"{tujuan} already exists")

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
            print(f"version=v{nomor}\nrev={rev}\npdf={tujuan / f'{nama}.pdf'}\npages={halaman}\nlog_errors={galat}")
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
                print(f"diff={pdf_banding}" if pdf_banding else "warn=latexdiff failed, comparison not built")
        finally:
            git("worktree", "remove", "--force", str(pohon_baru))

    pesan = f"{args.catatan}\n\npages={halaman} log_errors={galat}".strip()
    git("tag", "-a", f"rilis/{args.proyek}/v{nomor}", rev, "-m", pesan)
    print(f"tag=rilis/{args.proyek}/v{nomor}")


if __name__ == "__main__":
    main()
