#!/usr/bin/env python3
import ast
import io
import os
import re
import subprocess
import sys
import tokenize

C_EXTENSIONS = (".c", ".cpp", ".h", ".hpp")
CODING_PATTERN = re.compile(r"^[ \t\f]*#.*?coding[:=]")
HEREDOC_PATTERN = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
MAKE_TARGET_PATTERN = re.compile(r"^[^\t#=:][^=]*?:(?!=)")


def c_comments(teks):
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


def python_comments(teks):
    temuan = []
    for tok in tokenize.generate_tokens(io.StringIO(teks).readline):
        if tok.type != tokenize.COMMENT:
            continue
        no = tok.start[0]
        if no == 1 and tok.string.startswith("#!"):
            continue
        if no <= 2 and CODING_PATTERN.match(tok.line):
            continue
        temuan.append(no)
    for syntax_node in ast.walk(ast.parse(teks)):
        if not isinstance(syntax_node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if syntax_node.body and isinstance(syntax_node.body[0], ast.Expr):
            nilai = syntax_node.body[0].value
            if isinstance(nilai, ast.Constant) and isinstance(nilai.value, str):
                temuan.append(nilai.lineno)
    return temuan


def hash_position(baris, quote_char, word_starts):
    i = 0
    while i < len(baris):
        c = baris[i]
        if quote_char == "'":
            if c == "'":
                quote_char = None
        elif quote_char == '"':
            if c == "\\":
                i += 1
            elif c == '"':
                quote_char = None
        elif c == "\\":
            i += 1
        elif c in "'\"":
            quote_char = c
        elif c == "#" and (word_starts is None or i == 0 or baris[i - 1] in word_starts):
            return i, quote_char
        i += 1
    return -1, quote_char


def shell_comments(teks):
    temuan = []
    quote_char, terminator = None, None
    for no, baris in enumerate(teks.splitlines(), 1):
        if terminator is not None:
            if baris.strip() == terminator:
                terminator = None
            continue
        if no == 1 and baris.startswith("#!"):
            continue
        quote_start = quote_char
        pos, quote_char = hash_position(baris, quote_char, " \t;&|()")
        if pos >= 0:
            temuan.append(no)
        if quote_start is None and quote_char is None:
            heredoc = HEREDOC_PATTERN.search(baris if pos < 0 else baris[:pos])
            if heredoc:
                terminator = heredoc.group(2)
    return temuan


def ini_comments(teks):
    return [no for no, baris in enumerate(teks.splitlines(), 1) if baris.lstrip().startswith((";", "#")) or re.search(r"\s[;#]", baris)]


def makefile_comments(teks):
    temuan = []
    for no, baris in enumerate(teks.splitlines(), 1):
        if baris.startswith("\t"):
            pos, _ = hash_position(baris, None, " \t;&|()")
        else:
            pos = next((i for i, c in enumerate(baris) if c == "#" and baris[i - 1 : i] != "\\"), -1)
        if pos < 0:
            continue
        target_description = baris.startswith("##", pos) and MAKE_TARGET_PATTERN.match(baris[:pos])
        if not target_description:
            temuan.append(no)
    return temuan


def jenis(path):
    bagian = path.split("/")
    nama = bagian[-1]
    if bagian[0] in ("laporan", "docs") or "arsip" in bagian[:-1] or nama.endswith((".md", ".tex")):
        return None
    if nama.endswith(C_EXTENSIONS):
        return c_comments
    if nama.endswith(".py"):
        return python_comments
    if nama.endswith(".sh") or bagian[0] == ".githooks":
        return shell_comments
    if nama == "platformio.ini":
        return ini_comments
    if nama == "Makefile" or nama.endswith(".mk"):
        return makefile_comments
    return None


def list_files(argumen):
    base_dir = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
    argumen = [os.path.abspath(a) for a in argumen] or [base_dir]
    os.chdir(base_dir)
    hasil = []
    for arg in argumen:
        if os.path.isdir(arg) and os.path.commonpath([arg, base_dir]) == base_dir:
            keluaran = subprocess.run(["git", "ls-files", "--", arg], capture_output=True, text=True, check=True).stdout
            hasil.extend(keluaran.splitlines())
        elif os.path.isdir(arg):
            for folder, _, file_names in os.walk(arg):
                hasil.extend(os.path.join(folder, n) for n in file_names)
        elif os.path.isfile(arg):
            hasil.append(os.path.relpath(arg))
    return hasil


def periksa(berkas):
    violations = []
    for path in berkas:
        checker = jenis(path.replace(os.sep, "/"))
        if checker is None:
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            teks = f.read()
        try:
            nomor = checker(teks)
        except (SyntaxError, tokenize.TokenError) as fault:
            violations.append(f"{path}:0: cannot parse: {fault}")
            continue
        baris = teks.splitlines()
        for no in sorted(set(nomor)):
            isi = baris[no - 1].strip() if 0 < no <= len(baris) else ""
            violations.append(f"{path}:{no}: {isi}")
    return violations


def uji():
    c = 'int a = 1; // satu\nconst char *u = "http://x/*y*/";\nchar s = \'/\';\nchar q = \'"\';\n/* blok\n  dua */ int b;\nconst char *e = "a\\"//b";\n'
    assert c_comments(c) == [1, 5], c_comments(c)
    assert c_comments('x = a / b; y = c /d;\n') == []

    py = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""modul"""\nx = "# bukan"\ny = 1  # komentar\ndef f():\n    """doc"""\n    return \'#\'\nclass K:\n    z = "a"\n'
    assert python_comments(py) == [5, 3, 7], python_comments(py)
    assert python_comments('def g():\n    return "x"\n') == []

    sh = '#!/bin/sh\n# komentar\necho "a # b" \'c # d\' x#y $# ${#v}\nls  # akhir\necho "baris\n# masih string"\ncat <<EOF\n# isi heredoc\nEOF\n'
    assert shell_comments(sh) == [2, 4], shell_comments(sh)

    ini = '[env]\n; komentar\n# pagar\nbuild_flags = -I test\nlib = a  ; inline\nx = a;b\n'
    assert ini_comments(ini) == [2, 3, 5], ini_comments(ini)

    mk = 'PY := python\nREC ?= 100  # catatan\nX := "a#b"\nY := a\\#b\n## seksi\nhelp:\n\t@grep -E \'^[a-z]+:.*?##\' x\ndata:  ## unduh data\n# komentar\nprep: a.py ## rakit\n\techo hai # sh\n'
    assert makefile_comments(mk) == [2, 3, 5, 9, 11], makefile_comments(mk)

    assert jenis("laporan/buku-pa/Makefile") is None
    assert jenis("model/artifacts/arsip/x.py") is None
    assert jenis("docs/a.py") is None
    assert jenis("firmware/src/a.cpp") is c_comments
    assert jenis(".githooks/pre-commit") is shell_comments
    print("self-test passed")


def main():
    argumen = sys.argv[1:]
    if argumen == ["--self-test"]:
        uji()
        return 0
    violations = periksa(list_files(argumen))
    for p in violations:
        print(p)
    if violations:
        print(f"{len(violations)} comments found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
