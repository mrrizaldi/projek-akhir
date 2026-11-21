import html
import os
import re
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlsplit

AKAR = Path(__file__).resolve().parent.parent
EKSTENSI = {".pdf", ".docx", ".pptx"}
POLA_RILIS = re.compile(r"^laporan/rilis/(?P<proyek>[^/]+)/v(?P<nomor>\d+)$")
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


def pdf_rilis(proyek, nomor):
    return f"laporan/rilis/{proyek}/v{nomor}/{proyek}-v{nomor}.pdf"


def tautan_banding(folder):
    cocok = POLA_RILIS.match(folder)
    if not cocok or int(cocok["nomor"]) == 0:
        return ""
    proyek, nomor = cocok["proyek"], int(cocok["nomor"])
    lama, baru = pdf_rilis(proyek, nomor - 1), pdf_rilis(proyek, nomor)
    return (
        f' <a href="/banding?lama={quote(lama)}&amp;baru={quote(baru)}">'
        f"banding v{nomor - 1} dan v{nomor}</a>"
    )


def pdf_aman(rel):
    jalur = (AKAR / rel).resolve()
    return jalur.suffix == ".pdf" and jalur.is_file() and AKAR in jalur.parents


def halaman_banding(kueri):
    param = dict(parse_qsl(kueri))
    lama = param.get("lama", "")
    baru = param.get("baru", "")
    if not (pdf_aman(lama) and pdf_aman(baru)):
        return None
    bingkai = "".join(
        f'<section><h2>{html.escape(rel)}</h2><iframe src="/{quote(rel)}"></iframe></section>'
        for rel in (lama, baru)
    )
    return (
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<title>Banding rilis</title><style>"
        "body{margin:0;font:14px system-ui,sans-serif;background:#fff;color:#222}"
        "main{display:flex;height:100vh}section{flex:1;display:flex;flex-direction:column}"
        "h2{font-size:.9rem;margin:.3rem .5rem}iframe{flex:1;border:0;border-left:1px solid #ccc}"
        "@media(max-width:48rem){main{flex-direction:column;height:auto}iframe{height:80vh}}"
        "@media(prefers-color-scheme:dark){body{background:#181818;color:#ddd}}"
        f"</style><main>{bingkai}</main>"
    )


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
        bagian.append(f"<h2>{html.escape(folder)}{tautan_banding(folder)}</h2><ul>{baris}</ul>")
    return (
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        f'<base target="_blank"><title>Berkas PA</title><style>{GAYA}</style>'
        f"<h1>Berkas PA</h1>{''.join(bagian)}"
    )


class Penangan(SimpleHTTPRequestHandler):
    def kirim_html(self, isi):
        data = isi.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        alamat = urlsplit(self.path)
        if alamat.path == "/":
            return self.kirim_html(halaman_indeks())
        if alamat.path == "/banding":
            isi = halaman_banding(alamat.query)
            if isi is None:
                return self.send_error(404)
            return self.kirim_html(isi)
        return super().do_GET()


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
