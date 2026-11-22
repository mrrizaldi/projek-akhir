import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASES_FOLDER = REPO_ROOT / "laporan" / "rilis"
PROJECTS = ("buku-pa", "progres-pa-1")
TAG_PATTERN = re.compile(r"^rilis/(?P<proyek>[^/]+)/v(?P<nomor>\d+)$")
LOG_ERROR_PATTERN = re.compile(r"undefined|Overfull")


def git(*git_args, cwd=REPO_ROOT):
    result = subprocess.run(["git", *git_args], cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        gagal(f"git {' '.join(git_args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def gagal(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def existing_versions(proyek):
    result = {}
    for tag in git("tag", "--list", f"rilis/{proyek}/v*").splitlines():
        tag_match = TAG_PATTERN.match(tag)
        if tag_match:
            result[int(tag_match["nomor"])] = tag
    return result


def make(folder, *target):
    result = subprocess.run(["make", *target], cwd=folder, capture_output=True, text=True, errors="replace")
    return result.returncode == 0


def build_in_tree(worktree_dir, proyek):
    folder = worktree_dir / "laporan" / proyek
    if not make(folder, "pdf") or not make(folder, "docx"):
        gagal(f"build of {proyek} failed in {folder}")
    return folder / "output"


def page_count(pdf):
    for line in subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout.splitlines():
        if line.startswith("Pages:"):
            _, value = line.split()
            return int(value)
    return 0


def count_log_errors(log):
    return sum(1 for line in log.read_text(errors="replace").splitlines() if LOG_ERROR_PATTERN.search(line))


def flatten(folder):
    return subprocess.run(["latexpand", "main.tex"], cwd=folder, capture_output=True, text=True).stdout


def banding(old_tree, new_tree, proyek, out_dir):
    lama = old_tree / "laporan" / proyek
    baru = new_tree / "laporan" / proyek
    (baru / "datar-lama.tex").write_text(flatten(lama))
    (baru / "datar-baru.tex").write_text(flatten(baru))
    result = subprocess.run(
        ["latexdiff", "--math-markup=0", "datar-lama.tex", "datar-baru.tex"],
        cwd=baru, capture_output=True, text=True,
    )
    if result.returncode:
        return None
    (baru / "banding.tex").write_text(result.stdout)
    make(baru, "pdf", "MAIN=banding")
    pdf = baru / "output" / "banding.pdf"
    if not pdf.exists():
        return None
    shutil.copy(pdf, out_dir)
    return out_dir


def main():
    parser = argparse.ArgumentParser(
        description="Freeze the report PDF and DOCX as a numbered release (git tag rilis/<project>/vN)."
    )
    parser.add_argument("proyek", choices=PROJECTS)
    parser.add_argument("--rev", default="HEAD", help="commit to freeze (default HEAD)")
    parser.add_argument("--catatan", default="", help="tag message body")
    args = parser.parse_args()

    rev = git("rev-parse", "--short", f"{args.rev}^{{commit}}")
    if args.rev == "HEAD" and git("status", "--porcelain", "--", "laporan"):
        gagal("laporan/ has uncommitted changes; the release is built from a commit, commit first")
    versions = existing_versions(args.proyek)
    nomor = max(versions) + 1 if versions else 0
    content_paths = [f"laporan/{args.proyek}", "laporan/shared"]
    if versions and not git("diff", "--name-only", versions[max(versions)], rev, "--", *content_paths):
        gagal(f"no changes in {args.proyek} since {versions[max(versions)]}")
    release_name = f"{args.proyek}-v{nomor}"
    out_dir = RELEASES_FOLDER / args.proyek / f"v{nomor}"
    if out_dir.exists():
        gagal(f"{out_dir} already exists")

    with tempfile.TemporaryDirectory(prefix="rilis-") as scratch:
        new_tree = Path(scratch, "baru")
        git("worktree", "add", "--detach", str(new_tree), rev)
        try:
            build_dir = build_in_tree(new_tree, args.proyek)
            out_dir.mkdir(parents=True)
            shutil.copy(build_dir / "main.pdf", out_dir / f"{release_name}.pdf")
            shutil.copy(build_dir / "main.docx", out_dir / f"{release_name}.docx")
            pages = page_count(out_dir / f"{release_name}.pdf")
            fault = count_log_errors(build_dir / "main.log")
            print(f"version=v{nomor}\nrev={rev}\npdf={out_dir / f'{release_name}.pdf'}\npages={pages}\nlog_errors={fault}")
            if versions:
                previous = max(versions)
                old_tree = Path(scratch, "lama")
                git("worktree", "add", "--detach", str(old_tree), versions[previous])
                try:
                    diff_pdf = banding(
                        old_tree, new_tree, args.proyek,
                        out_dir / f"banding-v{previous}-v{nomor}.pdf",
                    )
                finally:
                    git("worktree", "remove", "--force", str(old_tree))
                print(f"diff={diff_pdf}" if diff_pdf else "warn=latexdiff failed, comparison not built")
        finally:
            git("worktree", "remove", "--force", str(new_tree))

    msg = f"{args.catatan}\n\nhalaman={pages} galat_log={fault}".strip()
    git("tag", "-a", f"rilis/{args.proyek}/v{nomor}", rev, "-m", msg)
    print(f"tag=rilis/{args.proyek}/v{nomor}")


if __name__ == "__main__":
    main()
