import html
import os
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

AKAR = Path(__file__).resolve().parent.parent
EKSTENSI = {".pdf", ".docx", ".pptx"}
LEWATI = {".git", ".venv", "node_modules", ".pio", "__pycache__"}
GAYA = (
    "body{font:15px/1.5 system-ui,sans-serif;max-width:56rem;margin:auto;padding:1rem;"
    "background:#fff;color:#222}h2{font-size:1rem;margin:1.5rem 0 .3rem;color:#555}"
    "ul{margin:0;padding-left:1.2rem}small{color:#888;margin-left:.5rem}"
    "@media(prefers-color-scheme:dark){body{background:#181818;color:#ddd}h2{color:#aaa}a{color:#8ab4f8}}"
)


def cari_berkas():
    hasil = []
    for folder, subfolder, berkas in os.walk(AKAR):
        subfolder[:] = [d for d in subfolder if d not in LEWATI]
        for nama in berkas:
            jalur = Path(folder, nama)
            if jalur.suffix.lower() in EKSTENSI:
                hasil.append(jalur.relative_to(AKAR))
    return hasil


def waktu(rel):
    return (AKAR / rel).stat().st_mtime


def halaman_indeks():
    kelompok = {}
    for rel in cari_berkas():
        kelompok.setdefault(rel.parent.as_posix(), []).append(rel)
    urutan = sorted(kelompok.items(), key=lambda kv: max(map(waktu, kv[1])), reverse=True)
    bagian = []
    for folder, daftar in urutan:
        baris = "".join(
            f'<li><a href="/{quote(r.as_posix())}">{html.escape(r.name)}</a>'
            f'<small>{time.strftime("%d %b %Y %H:%M", time.localtime(waktu(r)))}</small></li>'
            for r in sorted(daftar, key=waktu, reverse=True)
        )
        bagian.append(f"<h2>{html.escape(folder)}</h2><ul>{baris}</ul>")
    return (
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        f'<base target="_blank"><title>Berkas PA</title><style>{GAYA}</style>'
        f"<h1>Berkas PA</h1>{''.join(bagian)}"
    )


class Penangan(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            return super().do_GET()
        isi = halaman_indeks().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(isi)))
        self.end_headers()
        self.wfile.write(isi)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8700
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Penangan, directory=str(AKAR)))
    print(f"http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
