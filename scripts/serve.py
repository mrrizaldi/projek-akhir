import html
import os
import re
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTENSIONS = {".pdf", ".docx", ".pptx"}
RELEASE_PATTERN = re.compile(r"^laporan/rilis/(?P<proyek>[^/]+)/v(?P<nomor>\d+)$")
SKIPPED_DIRS = {".git", ".venv", "node_modules", ".pio", "__pycache__"}
STYLE = (
    "body{font:15px/1.5 system-ui,sans-serif;max-width:56rem;margin:auto;padding:1rem;"
    "background:#fff;color:#222}h2{font-size:1rem;margin:1.5rem 0 .3rem;color:#555}"
    "ul{margin:0;padding-left:1.2rem}small{color:#888;margin-left:.5rem}"
    "@media(prefers-color-scheme:dark){body{background:#181818;color:#ddd}h2{color:#aaa}a{color:#8ab4f8}}"
)


def find_files():
    hasil = []
    for folder, subfolder, berkas in os.walk(REPO_ROOT):
        subfolder[:] = [d for d in subfolder if d not in SKIPPED_DIRS]
        for nama in berkas:
            jalur = Path(folder, nama)
            if jalur.suffix.lower() in EXTENSIONS:
                hasil.append(jalur.relative_to(REPO_ROOT))
    return hasil


def waktu(rel):
    return (REPO_ROOT / rel).stat().st_mtime


def release_pdf(proyek, nomor):
    return f"laporan/rilis/{proyek}/v{nomor}/{proyek}-v{nomor}.pdf"


def diff_link(folder):
    cocok = RELEASE_PATTERN.match(folder)
    if not cocok or int(cocok["nomor"]) == 0:
        return ""
    proyek, nomor = cocok["proyek"], int(cocok["nomor"])
    lama, baru = release_pdf(proyek, nomor - 1), release_pdf(proyek, nomor)
    return (
        f' <a href="/banding?lama={quote(lama)}&amp;baru={quote(baru)}">'
        f"compare v{nomor - 1} and v{nomor}</a>"
    )


def is_safe_pdf(rel):
    jalur = (REPO_ROOT / rel).resolve()
    return jalur.suffix == ".pdf" and jalur.is_file() and REPO_ROOT in jalur.parents


def compare_page(query_text):
    param = dict(parse_qsl(query_text))
    lama = param.get("lama", "")
    baru = param.get("baru", "")
    if not (is_safe_pdf(lama) and is_safe_pdf(baru)):
        return None
    bingkai = "".join(
        f'<section><h2>{html.escape(rel)}</h2><iframe src="/{quote(rel)}"></iframe></section>'
        for rel in (lama, baru)
    )
    return (
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<title>Release comparison</title><style>"
        "body{margin:0;font:14px system-ui,sans-serif;background:#fff;color:#222}"
        "main{display:flex;height:100vh}section{flex:1;display:flex;flex-direction:column}"
        "h2{font-size:.9rem;margin:.3rem .5rem}iframe{flex:1;border:0;border-left:1px solid #ccc}"
        "@media(max-width:48rem){main{flex-direction:column;height:auto}iframe{height:80vh}}"
        "@media(prefers-color-scheme:dark){body{background:#181818;color:#ddd}}"
        f"</style><main>{bingkai}</main>"
    )


def index_page():
    folder_groups = {}
    for rel in find_files():
        folder_groups.setdefault(rel.parent.as_posix(), []).append(rel)
    urutan = sorted(folder_groups.items(), key=lambda kv: max(map(waktu, kv[1])), reverse=True)
    bagian = []
    for folder, daftar in urutan:
        baris = "".join(
            f'<li><a href="/{quote(r.as_posix())}">{html.escape(r.name)}</a>'
            f'<small>{time.strftime("%d %b %Y %H:%M", time.localtime(waktu(r)))}</small></li>'
            for r in sorted(daftar, key=waktu, reverse=True)
        )
        bagian.append(f"<h2>{html.escape(folder)}{diff_link(folder)}</h2><ul>{baris}</ul>")
    return (
        '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        f'<base target="_blank"><title>PA files</title><style>{STYLE}</style>'
        f"<h1>PA files</h1>{''.join(bagian)}"
    )


class PageHandler(SimpleHTTPRequestHandler):
    def send_html(self, isi):
        data = isi.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        alamat = urlsplit(self.path)
        if alamat.path == "/":
            return self.send_html(index_page())
        if alamat.path == "/banding":
            isi = compare_page(alamat.query)
            if isi is None:
                return self.send_error(404)
            return self.send_html(isi)
        return super().do_GET()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8700
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(PageHandler, directory=str(REPO_ROOT)))
    print(f"http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
