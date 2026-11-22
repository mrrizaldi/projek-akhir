#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PAGE_SIGNATURE_WORDS = 6
EXCERPT_MAX_CHARS = 70
SHOW_DIFF_MAX = 5
CHAPTER_PATTERN = re.compile(r"^\s*(BAB [0-9]+|DAFTAR PUSTAKA|LAMPIRAN)\s*$", re.M)
PAGE_NUMBER_PATTERN = re.compile(r"^(?:[0-9]+|[ivxlcdm]+)$")
PAGE_SEPARATOR = "\f"


def pdf_pages(pdf):
    keluaran = subprocess.run(["pdftotext", "-q", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    pages = keluaran.split(PAGE_SEPARATOR)
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def page_words(page_text):
    joined = re.sub(r"-\n(?=\w)", "", page_text)
    words = [re.sub(r"\W", "", k.lower()) for k in joined.split()]
    return [k for k in words if k and not PAGE_NUMBER_PATTERN.match(k)]


def signature(page_text):
    return page_words(page_text)[:PAGE_SIGNATURE_WORDS]


def chapter_starts(pages):
    chapter_start = {}
    for page_number, page_text in enumerate(pages, start=1):
        chapter_match = CHAPTER_PATTERN.search(page_text)
        if chapter_match and chapter_match.group(1) not in chapter_start:
            chapter_start[chapter_match.group(1)] = page_number
    return chapter_start


def page_excerpt(page_text):
    return " ".join(page_text.split())[:EXCERPT_MAX_CHARS]


def render_docx(docx, wordcraft, folder):
    keluaran = Path(folder) / "docx.pdf"
    subprocess.run([wordcraft, "convert", str(docx), str(keluaran)], capture_output=True, check=True)
    return keluaran


def bandingkan(pdf_latex, docx, wordcraft):
    with tempfile.TemporaryDirectory() as folder:
        latex_pages = pdf_pages(pdf_latex)
        docx_pages = pdf_pages(render_docx(docx, wordcraft, folder))
    latex_chapters, docx_chapters = chapter_starts(latex_pages), chapter_starts(docx_pages)
    print(f"Pages: PDF {len(latex_pages)}, DOCX {len(docx_pages)}")
    print(f"{'Section':<16}{'PDF':>6}{'DOCX':>6}{'Delta':>9}")
    for chapter, page_count_at in latex_chapters.items():
        docx_page = docx_chapters.get(chapter)
        offset = "-" if docx_page is None else f"{docx_page - page_count_at:+d}"
        print(f"{chapter:<16}{page_count_at:>6}{docx_page if docx_page else '-':>6}{offset:>9}")
    differing = [n for n, (a, b) in enumerate(zip(latex_pages, docx_pages), start=1) if signature(a) != signature(b)]
    matching = min(len(latex_pages), len(docx_pages)) - len(differing)
    print(f"Pages with matching start: {matching} of {len(latex_pages)}")
    for page_number in differing[:SHOW_DIFF_MAX]:
        print(f"  p{page_number} PDF : {page_excerpt(latex_pages[page_number - 1])}")
        print(f"  p{page_number} DOCX: {page_excerpt(docx_pages[page_number - 1])}")
    return not differing and len(latex_pages) == len(docx_pages)


def main():
    parser = argparse.ArgumentParser(description="Compare per-page content of the LaTeX PDF with the WordCraft DOCX (re-rendered to PDF).")
    parser.add_argument("pdf", help="PDF produced by pdfLaTeX, e.g. output/main.pdf")
    parser.add_argument("docx", help="DOCX produced by make docx, e.g. output/main.docx")
    args = parser.parse_args()
    wordcraft = os.environ.get("WORDCRAFT", "wordcraft-cli")
    sys.exit(0 if bandingkan(args.pdf, args.docx, wordcraft) else 1)


if __name__ == "__main__":
    main()
