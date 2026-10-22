## ============================================================
## shared/Makefile.inc — texdocs
## Include di masing-masing projek: include ../shared/Makefile.inc
##
## Variabel yang bisa di-override per projek:
##   MAIN   — nama file tex tanpa ekstensi (default: main)
##   OUTDIR — folder output (default: output)
##
## Ukuran kertas: TETAP per projek (diset di main.tex via documentclass +
## \input ../shared/size-aX). Tidak ada switch a4/a5 saat compile.
##
## Targets:
##   make pdf     — compile PDF
##   make docx    — konversi ke DOCX via WordCraft (wordcraft-cli; format dari ../wordcraft.toml)
##   make view    — buka PDF
##   make clean   — hapus folder output
##   make rebuild — clean + pdf
##   make check   — cek tool tersedia
## ============================================================

MAIN      ?= main
OUTDIR    ?= output
WORDCRAFT ?= wordcraft-cli

PDFLATEX = pdflatex -jobname=$(MAIN) -output-directory=$(OUTDIR) -interaction=nonstopmode

.PHONY: pdf docx view clean rebuild check

pdf:
	mkdir -p $(OUTDIR)
	$(PDFLATEX) $(MAIN).tex
	-bibtex $(OUTDIR)/$(MAIN)
	$(PDFLATEX) $(MAIN).tex
	$(PDFLATEX) $(MAIN).tex
	@echo "PDF tersimpan di $(OUTDIR)/$(MAIN).pdf"

docx:
	mkdir -p $(OUTDIR)
	$(WORDCRAFT) convert $(MAIN).tex $(OUTDIR)/$(MAIN).docx
	@echo "DOCX tersimpan di $(OUTDIR)/$(MAIN).docx (jalankan make pdf dulu agar output/$(MAIN).bbl ada)"

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
