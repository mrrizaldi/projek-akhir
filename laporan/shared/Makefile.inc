## ============================================================
## shared/Makefile.inc — texdocs
## Include di masing-masing projek: include ../shared/Makefile.inc
##
## Variabel yang bisa di-override per projek:
##   MAIN   — nama file tex tanpa ekstensi (default: main)
##   OUTDIR — folder output (default: output)
##   DOCX   — DOCX yang di-sync balik ke .tex (default: $(OUTDIR)/$(MAIN).docx)
##
## Ukuran kertas: TETAP per projek (diset di main.tex via documentclass +
## \input ../shared/size-aX). Tidak ada switch a4/a5 saat compile.
##
## Targets:
##   make pdf     — compile PDF
##   make docx    — konversi ke DOCX via WordCraft (wordcraft-cli; format dari ../wordcraft.toml)
##   make sync    — tulis balik perubahan paragraf dari DOCX ke .tex (wordcraft-cli latex-sync);
##                  tanpa penanda di .tex; make sync DOCX=file.docx
##   make sync-dry — sama, tapi hanya tampilkan diff, tidak menulis
##   make cek-docx — bandingkan isi per halaman PDF dengan DOCX (scripts/cek_docx.py)
##   make rilis   — bekukan PDF+DOCX dari HEAD jadi rilis bernomor (scripts/rilis.py); CATATAN="..."
##   make view    — buka PDF
##   make pdf-bersih — buang aux/toc/lof/lot/bbl lalu compile; DOCX di output/ tetap (dipakai untuk bukti)
##   make clean   — hapus folder output
##   make rebuild — clean + pdf
##   make check   — cek tool tersedia
## ============================================================

MAIN      ?= main
OUTDIR    ?= output
WORDCRAFT ?= wordcraft-cli
DOCX      ?= $(OUTDIR)/$(MAIN).docx

PDFLATEX = pdflatex -jobname=$(MAIN) -output-directory=$(OUTDIR) -interaction=nonstopmode

.PHONY: pdf pdf-bersih docx sync sync-dry cek-docx rilis view clean rebuild check

pdf:
	mkdir -p $(OUTDIR)
	$(PDFLATEX) $(MAIN).tex
	-bibtex $(OUTDIR)/$(MAIN)
	$(PDFLATEX) $(MAIN).tex
	$(PDFLATEX) $(MAIN).tex
	@echo "PDF tersimpan di $(OUTDIR)/$(MAIN).pdf"

pdf-bersih:
	rm -f $(addprefix $(OUTDIR)/$(MAIN).,aux toc lof lot bbl blg out log)
	$(MAKE) pdf

docx:
	mkdir -p $(OUTDIR)
	$(WORDCRAFT) convert $(MAIN).tex $(OUTDIR)/$(MAIN).docx
	@echo "DOCX tersimpan di $(OUTDIR)/$(MAIN).docx (jalankan make pdf dulu agar output/$(MAIN).bbl ada)"

sync:
	$(WORDCRAFT) latex-sync $(DOCX) --main $(MAIN).tex

sync-dry:
	$(WORDCRAFT) latex-sync $(DOCX) --main $(MAIN).tex --dry-run

cek-docx:
	WORDCRAFT=$(WORDCRAFT) python3 ../../scripts/cek_docx.py $(OUTDIR)/$(MAIN).pdf $(OUTDIR)/$(MAIN).docx

rilis:
	python3 ../../scripts/rilis.py $(notdir $(CURDIR)) --catatan "$(CATATAN)"

view: pdf
	xdg-open $(OUTDIR)/$(MAIN).pdf &

clean:
	rm -rf $(OUTDIR)
	@echo "Output dibersihkan"

rebuild: clean pdf

check:
	@pdflatex --version > /dev/null 2>&1 && echo "pdflatex OK" || echo "pdflatex tidak ditemukan"
	@bibtex --version > /dev/null 2>&1 && echo "bibtex OK" || echo "bibtex tidak ditemukan"
	@$(WORDCRAFT) --version > /dev/null 2>&1 && echo "wordcraft-cli OK" || echo "wordcraft-cli tidak ditemukan (WORDCRAFT=/path/ke/wordcraft-cli)"
