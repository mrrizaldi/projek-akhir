# Deck bedah paper Lueken dkk. 2023 (penilaian kualitas sinyal ECG single-lead untuk skrining AF)

Deck bimbingan 10 menit, 10 slide. Sumber isi: `laporan/pustaka/lueken_2023.pdf`
(DOI 10.3390/s23125618, Sensors, open access CC BY; folder `laporan/pustaka/`
di-ignore git, unduh ulang lewat tautan DOI atau `scripts/unduh_pustaka.py`).
Deck ini menggantikan `presentasi/2026-10-15-bedah-paper-orphanidou/` (paper
2015) atas permintaan user agar rujukan 2020 ke atas.

Gambar slide 4, 5, 6, dan 8 dipotong dari halaman paper (A4, 200 dpi), bukan digambar. Bangun ulang:

```bash
cd presentasi/2026-10-15-bedah-paper-lueken
P=../../laporan/pustaka/lueken_2023.pdf
pdftoppm -png -r 200 -f 8  -l 8  -x 446 -y 1087 -W 1124 -H 264  $P output/fig6  && mv output/fig6-8.png   output/fig6_rantai.png
pdftoppm -png -r 200 -f 9  -l 9  -x 446 -y 701  -W 1108 -H 1274 $P output/fig7  && mv output/fig7-9.png   output/fig7_artefak.png
pdftoppm -png -r 200 -f 11 -l 11 -x 446 -y 257  -W 1108 -H 912  $P output/fig8  && mv output/fig8-11.png  output/fig8_prototipe.png
pdftoppm -png -r 200 -f 16 -l 16 -x 446 -y 1122 -W 1108 -H 830  $P output/fig13 && mv output/fig13-16.png output/fig13_roc.png
NODE_PATH=~/.local/lib/node_modules node deck.js
python3 ~/.claude/plugins/cache/anthropic-agent-skills/document-skills/dbd4588f9e10/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf --outdir output output/deck.pptx
pdftoppm -png -r 60 output/deck.pdf output/slide
```

Hasil: `output/deck.pptx`, `output/deck.pdf`, `output/slide-NN.png` (semua di-ignore git).
