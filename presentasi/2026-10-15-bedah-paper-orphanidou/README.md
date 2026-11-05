# Deck bedah paper Orphanidou dkk. 2015 (SQI untuk ECG dan PPG)

Deck bimbingan 10 menit, 10 slide. Sumber isi: `laporan/pustaka/orphanidou_2015.pdf`
(DOI 10.1109/JBHI.2014.2338351, open access di IEEE; folder `laporan/pustaka/`
di-ignore git, unduh ulang lewat `scripts/unduh_pustaka.py` atau tautan DOI).

Gambar slide 4, 5, dan 8 dipotong dari halaman paper, bukan digambar. Bangun ulang:

```bash
cd presentasi/2026-10-15-bedah-paper-orphanidou
P=../../laporan/pustaka/orphanidou_2015.pdf
pdftoppm -png -r 200 -f 3 -l 3 -x 855 -y 165 -W 790 -H 830 $P output/fig1 && mv output/fig1-3.png output/fig1_flowchart.png
pdftoppm -png -r 200 -f 4 -l 4 -x 93  -y 165 -W 740 -H 418 $P output/fig2 && mv output/fig2-4.png output/fig2_template.png
pdftoppm -png -r 200 -f 6 -l 6 -x 93  -y 583 -W 740 -H 362 $P output/fig6 && mv output/fig6-6.png output/fig6_mae.png
NODE_PATH=~/.local/lib/node_modules node deck.js
deckcraft-cli convert output/deck.pptx output/deck.pdf
pdftoppm -png -r 60 output/deck.pdf output/slide
```

Hasil: `output/deck.pptx`, `output/deck.pdf`, `output/slide-NN.png` (semua di-ignore git).
