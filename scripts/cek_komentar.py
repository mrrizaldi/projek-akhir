#!/usr/bin/env python3
import ast
import io
import os
import re
import subprocess
import sys
import tokenize

EKSTENSI_C = (".c", ".cpp", ".h", ".hpp")
POLA_CODING = re.compile(r"^[ \t\f]*#.*?coding[:=]")
POLA_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
POLA_TARGET_MAKE = re.compile(r"^[^\t#=:][^=]*?:(?!=)")


def komentar_c(teks):
    temuan = []
    i, n, baris = 0, len(teks), 1
    while i < n:
        c = teks[i]
        if c == "\n":
            baris += 1
            i += 1
        elif c in "\"'":
            i += 1
            while i < n and teks[i] != c and teks[i] != "\n":
                i += 2 if teks[i] == "\\" else 1
            i += 1
        elif teks.startswith("//", i):
            temuan.append(baris)
            while i < n and teks[i] != "\n":
                i += 1
        elif teks.startswith("/*", i):
            temuan.append(baris)
            akhir = teks.find("*/", i + 2)
            akhir = n if akhir < 0 else akhir + 2
            baris += teks.count("\n", i, akhir)
            i = akhir
        else:
            i += 1
    return temuan


def komentar_python(teks):
    temuan = []
    for tok in tokenize.generate_tokens(io.StringIO(teks).readline):
        if tok.type != tokenize.COMMENT:
            continue
        no = tok.start[0]
        if no == 1 and tok.string.startswith("#!"):
            continue
        if no <= 2 and POLA_CODING.match(tok.line):
            continue
        temuan.append(no)
    for simpul in ast.walk(ast.parse(teks)):
        if not isinstance(simpul, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if simpul.body and isinstance(simpul.body[0], ast.Expr):
            nilai = simpul.body[0].value
            if isinstance(nilai, ast.Constant) and isinstance(nilai.value, str):
                temuan.append(nilai.lineno)
    return temuan


def posisi_pagar(baris, kutip, awal_kata):
    i = 0
    while i < len(baris):
        c = baris[i]
        if kutip == "'":
            if c == "'":
                kutip = None
        elif kutip == '"':
            if c == "\\":
                i += 1
            elif c == '"':
                kutip = None
        elif c == "\\":
            i += 1
        elif c in "'\"":
            kutip = c
        elif c == "#" and (awal_kata is None or i == 0 or baris[i - 1] in awal_kata):
            return i, kutip
        i += 1
    return -1, kutip


def komentar_shell(teks):
    temuan = []
    kutip, penutup = None, None
    for no, baris in enumerate(teks.splitlines(), 1):
        if penutup is not None:
            if baris.strip() == penutup:
                penutup = None
            continue
        if no == 1 and baris.startswith("#!"):
            continue
        mulai_kutip = kutip
        pos, kutip = posisi_pagar(baris, kutip, " \t;&|()")
        if pos >= 0:
            temuan.append(no)
        if mulai_kutip is None and kutip is None:
            heredoc = POLA_HEREDOC.search(baris if pos < 0 else baris[:pos])
            if heredoc:
                penutup = heredoc.group(2)
    return temuan


def komentar_ini(teks):
    return [no for no, baris in enumerate(teks.splitlines(), 1) if baris.lstrip().startswith((";", "#")) or re.search(r"\s[;#]", baris)]


def komentar_makefile(teks):
    temuan = []
    for no, baris in enumerate(teks.splitlines(), 1):
        if baris.startswith("\t"):
            pos, _ = posisi_pagar(baris, None, " \t;&|()")
        else:
            pos = next((i for i, c in enumerate(baris) if c == "#" and baris[i - 1 : i] != "\\"), -1)
        if pos < 0:
            continue
        deskripsi_target = baris.startswith("##", pos) and POLA_TARGET_MAKE.match(baris[:pos])
        if not deskripsi_target:
            temuan.append(no)
    return temuan


def jenis(path):
    bagian = path.split("/")
    nama = bagian[-1]
    if bagian[0] in ("laporan", "docs") or "arsip" in bagian[:-1] or nama.endswith((".md", ".tex")):
        return None
    if nama.endswith(EKSTENSI_C):
        return komentar_c
    if nama.endswith(".py"):
        return komentar_python
    if nama.endswith(".sh") or bagian[0] == ".githooks":
        return komentar_shell
    if nama == "platformio.ini":
        return komentar_ini
    if nama == "Makefile" or nama.endswith(".mk"):
        return komentar_makefile
    return None


def daftar_berkas(argumen):
    akar = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
    argumen = [os.path.abspath(a) for a in argumen] or [akar]
    os.chdir(akar)
    hasil = []
    for arg in argumen:
        if os.path.isdir(arg) and os.path.commonpath([arg, akar]) == akar:
            keluaran = subprocess.run(["git", "ls-files", "--", arg], capture_output=True, text=True, check=True).stdout
            hasil.extend(keluaran.splitlines())
        elif os.path.isdir(arg):
            for folder, _, nama_berkas in os.walk(arg):
                hasil.extend(os.path.join(folder, n) for n in nama_berkas)
        elif os.path.isfile(arg):
            hasil.append(os.path.relpath(arg))
    return hasil


def periksa(berkas):
    pelanggaran = []
    for path in berkas:
        pemeriksa = jenis(path.replace(os.sep, "/"))
        if pemeriksa is None:
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            teks = f.read()
        try:
            nomor = pemeriksa(teks)
        except (SyntaxError, tokenize.TokenError) as galat:
            pelanggaran.append(f"{path}:0: tidak bisa diurai: {galat}")
            continue
        baris = teks.splitlines()
        for no in sorted(set(nomor)):
            isi = baris[no - 1].strip() if 0 < no <= len(baris) else ""
            pelanggaran.append(f"{path}:{no}: {isi}")
    return pelanggaran


def uji():
    c = 'int a = 1; // satu\nconst char *u = "http://x/*y*/";\nchar s = \'/\';\nchar q = \'"\';\n/* blok\n  dua */ int b;\nconst char *e = "a\\"//b";\n'
    assert komentar_c(c) == [1, 5], komentar_c(c)
    assert komentar_c('x = a / b; y = c /d;\n') == []

    py = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""modul"""\nx = "# bukan"\ny = 1  # komentar\ndef f():\n    """doc"""\n    return \'#\'\nclass K:\n    z = "a"\n'
    assert komentar_python(py) == [5, 3, 7], komentar_python(py)
    assert komentar_python('def g():\n    return "x"\n') == []

    sh = '#!/bin/sh\n# komentar\necho "a # b" \'c # d\' x#y $# ${#v}\nls  # akhir\necho "baris\n# masih string"\ncat <<EOF\n# isi heredoc\nEOF\n'
    assert komentar_shell(sh) == [2, 4], komentar_shell(sh)

    ini = '[env]\n; komentar\n# pagar\nbuild_flags = -I test\nlib = a  ; inline\nx = a;b\n'
    assert komentar_ini(ini) == [2, 3, 5], komentar_ini(ini)

    mk = 'PY := python\nREC ?= 100  # catatan\nX := "a#b"\nY := a\\#b\n## seksi\nhelp:\n\t@grep -E \'^[a-z]+:.*?##\' x\ndata:  ## unduh data\n# komentar\nprep: a.py ## rakit\n\techo hai # sh\n'
    assert komentar_makefile(mk) == [2, 3, 5, 9, 11], komentar_makefile(mk)

    assert jenis("laporan/buku-pa/Makefile") is None
    assert jenis("model/artifacts/arsip/x.py") is None
    assert jenis("docs/a.py") is None
    assert jenis("firmware/src/a.cpp") is komentar_c
    assert jenis(".githooks/pre-commit") is komentar_shell
    print("uji lulus")


def main():
    argumen = sys.argv[1:]
    if argumen == ["--uji"]:
        uji()
        return 0
    pelanggaran = periksa(daftar_berkas(argumen))
    for p in pelanggaran:
        print(p)
    if pelanggaran:
        print(f"{len(pelanggaran)} komentar ditemukan", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
