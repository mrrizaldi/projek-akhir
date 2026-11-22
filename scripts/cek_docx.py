#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KATA_TANDA_HALAMAN = 6
CUPLIKAN_MAKS_HURUF = 70
TAMPIL_BEDA_MAKS = 5
POLA_BAB = re.compile(r"^\s*(BAB [0-9]+|DAFTAR PUSTAKA|LAMPIRAN)\s*$", re.M)
POLA_NOMOR_HALAMAN = re.compile(r"^(?:[0-9]+|[ivxlcdm]+)$")
PEMISAH_HALAMAN = "\f"


def halaman_pdf(pdf):
    keluaran = subprocess.run(["pdftotext", "-q", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    halaman = keluaran.split(PEMISAH_HALAMAN)
    if halaman and not halaman[-1].strip():
        halaman.pop()
    return halaman


def kata_halaman(teks):
    sambung = re.sub(r"-\n(?=\w)", "", teks)
    kata = [re.sub(r"\W", "", k.lower()) for k in sambung.split()]
    return [k for k in kata if k and not POLA_NOMOR_HALAMAN.match(k)]


def tanda(teks):
    return kata_halaman(teks)[:KATA_TANDA_HALAMAN]


def awal_bab(halaman):
    awal = {}
    for nomor, teks in enumerate(halaman, start=1):
        cocok = POLA_BAB.search(teks)
        if cocok and cocok.group(1) not in awal:
            awal[cocok.group(1)] = nomor
    return awal


def cuplikan(teks):
    return " ".join(teks.split())[:CUPLIKAN_MAKS_HURUF]


def render_docx(docx, wordcraft, folder):
    keluaran = Path(folder) / "docx.pdf"
    subprocess.run([wordcraft, "convert", str(docx), str(keluaran)], capture_output=True, check=True)
    return keluaran


def bandingkan(pdf_latex, docx, wordcraft):
    with tempfile.TemporaryDirectory() as folder:
        hal_latex = halaman_pdf(pdf_latex)
        hal_docx = halaman_pdf(render_docx(docx, wordcraft, folder))
    bab_latex, bab_docx = awal_bab(hal_latex), awal_bab(hal_docx)
    print(f"Pages: PDF {len(hal_latex)}, DOCX {len(hal_docx)}")
    print(f"{'Section':<16}{'PDF':>6}{'DOCX':>6}{'Delta':>9}")
    for nama, hal in bab_latex.items():
        hal_d = bab_docx.get(nama)
        selisih = "-" if hal_d is None else f"{hal_d - hal:+d}"
        print(f"{nama:<16}{hal:>6}{hal_d if hal_d else '-':>6}{selisih:>9}")
    beda = [n for n, (a, b) in enumerate(zip(hal_latex, hal_docx), start=1) if tanda(a) != tanda(b)]
    sama = min(len(hal_latex), len(hal_docx)) - len(beda)
    print(f"Pages with matching start: {sama} of {len(hal_latex)}")
    for nomor in beda[:TAMPIL_BEDA_MAKS]:
        print(f"  p{nomor} PDF : {cuplikan(hal_latex[nomor - 1])}")
        print(f"  p{nomor} DOCX: {cuplikan(hal_docx[nomor - 1])}")
    return not beda and len(hal_latex) == len(hal_docx)


def main():
    parser = argparse.ArgumentParser(description="Compare per-page content of the LaTeX PDF with the WordCraft DOCX (re-rendered to PDF).")
    parser.add_argument("pdf", help="PDF produced by pdfLaTeX, e.g. output/main.pdf")
    parser.add_argument("docx", help="DOCX produced by make docx, e.g. output/main.docx")
    args = parser.parse_args()
    wordcraft = os.environ.get("WORDCRAFT", "wordcraft-cli")
    sys.exit(0 if bandingkan(args.pdf, args.docx, wordcraft) else 1)


if __name__ == "__main__":
    main()
