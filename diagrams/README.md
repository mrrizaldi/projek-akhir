# diagrams/ — diagram laporan

Folder ini disediakan untuk sumber (`src/`) dan hasil render (`render/`) diagram
ilustrasi laporan. Keduanya kosong.

Kebijakan gambar (dari [`CLAUDE.md`](../CLAUDE.md) root):

- Diagram dan gambar ilustrasi digambar oleh penulis. Claude tidak membuat
  diagram (Mermaid, TikZ, PlantUML, Graphviz, SVG/draw.io, skrip gambar, gambar
  AI) dan tidak menambah berkas ke `src/`.
- Di posisi gambar, laporan memuat placeholder beserta kartu spesifikasi isi.
  Templat: `docs/pola-laporan-pa/05-gambar-tabel-persamaan.md` §Placeholder gambar.
  Daftar placeholder tersisa: `grep -rn "PLACEHOLDER-GAMBAR" laporan/`.
- Plot data eksperimen (confusion matrix, kurva, grafik latensi) bukan ilustrasi;
  sumbernya `model/artifacts/metrics/` dan disalin lewat
  `scripts/export_artifacts.sh --laporan`.
- Label requirement `RM1..RM4` tidak boleh muncul di diagram apa pun.
