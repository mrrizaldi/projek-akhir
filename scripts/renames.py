import ast
import difflib
import io
import os
import re
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

MAP = Path("scripts/rename_map.tsv")
GLOSSARY = Path("scripts/glossary.tsv")
SKIP = (
    "laporan/",
    "presentasi/",
    "model/data/",
    "model/artifacts/",
    ".claude/skills-arsip/",
    "scripts/rename_map.tsv",
    "scripts/glossary.tsv",
    "docs/2026-11-22-english-codebase.md",
    "firmware/include/model_int8.h",
)
TEXT_SUFFIXES = {".md", ".sh", ".yml", ".yaml", ".ini", ".json", ".txt", ".inc", ""}
FROZEN = {"WIFI_DAFTAR", "BROKER_DAFTAR"}
C_TOKEN = re.compile(r'#include "[^"]+"|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|[A-Za-z_]\w*')
WORD = re.compile(r"\w+")
BIN = Path.home() / ".platformio/packages/toolchain-xtensa-esp32s3/bin"
OBJDUMP = str(BIN / "xtensa-esp32s3-elf-objdump")
OBJCOPY = str(BIN / "xtensa-esp32s3-elf-objcopy")
CPPFILT = str(BIN / "xtensa-esp32s3-elf-c++filt")
SRC_FLAGS = re.compile(r"^build_src_flags = .*?-D([A-Z_]+)=.*$", re.M)
OBJ_DIR = "firmware/.pio/build/esp32-s3/src"


def load_pairs(path):
    pairs = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                old, new = line.split("\t")
                pairs[old] = new
                old_stem, old_ext = os.path.splitext(old)
                new_stem, new_ext = os.path.splitext(new)
                if old_ext and old_ext == new_ext and "/" not in old and " " not in old:
                    pairs.setdefault(old_stem, new_stem)
    targets = list(pairs.values())
    clashes = {t for t in targets if targets.count(t) > 1}
    if clashes:
        sys.exit(f"map is not one-to-one: {sorted(clashes)}")
    return pairs


def identifiers(pairs):
    return {k: v for k, v in pairs.items() if WORD.fullmatch(k)}


def c_names(text):
    return {m.group(0) for m in C_TOKEN.finditer(text) if m.group(0)[0] not in "#\"'"}


def py_names(text):
    return {t.string for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type == tokenize.NAME}


def py_strings(text):
    found = set()
    for t in tokenize.generate_tokens(io.StringIO(text).readline):
        if t.type in (tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)):
            found |= set(WORD.findall(t.string.replace("-", "_")))
    return found


def apply_c(text, pairs):
    def swap(match):
        token = match.group(0)
        if token.startswith("#include"):
            name = token[10:-1]
            return f'#include "{pairs.get(name, name)}"'
        if token[0] in "\"'":
            return token
        return pairs.get(token, token)

    return C_TOKEN.sub(swap, text)


def apply_py(text, pairs):
    hits = [t for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type == tokenize.NAME and t.string in pairs]
    lines = text.splitlines(keepends=True)
    for token in reversed(hits):
        row, col = token.start
        line = lines[row - 1]
        lines[row - 1] = line[:col] + pairs[token.string] + line[token.end[1]:]
    return "".join(lines)


def apply_text(text, pairs):
    safe = {k: v for k, v in pairs.items() if not re.fullmatch(r"[A-Za-z]+", k)}
    if not safe:
        return text
    pattern = re.compile(r"(?<![\w.-])(" + "|".join(map(re.escape, sorted(safe, key=len, reverse=True))) + r")(?![\w-])")
    return pattern.sub(lambda m: safe[m.group(1)], text)


def tracked(paths):
    files = subprocess.run(["git", "ls-files", *paths], capture_output=True, text=True, check=True).stdout.split()
    return [f for f in files if not f.startswith(SKIP) and Path(f).is_file() and is_text(Path(f))]


def is_text(path):
    try:
        path.read_text()
        return True
    except UnicodeDecodeError:
        return False


def apply(paths):
    pairs = load_pairs(MAP)
    ids = identifiers(pairs)
    refused = False
    for name in tracked(paths):
        path = Path(name)
        text = path.read_text()
        if path.suffix in {".cpp", ".h", ".c"}:
            present, new = c_names(text), apply_c(text, pairs)
            strings = set()
        elif path.suffix == ".py":
            present, new = py_names(text), apply_py(text, ids)
            strings = py_strings(text)
        elif path.suffix in TEXT_SUFFIXES or path.name == "Makefile":
            new = apply_text(text, pairs)
            if new != text:
                path.write_text(new)
                print(f"renamed {name}")
            continue
        else:
            continue
        used = {k for k in ids if k in present}
        taken = {ids[k] for k in used} & (present - used)
        from_strings = used & strings
        if taken or from_strings:
            refused = True
            print(f"REFUSED {name}: target names already used {sorted(taken)}; names also in string literals {sorted(from_strings)}")
            continue
        if new != text:
            path.write_text(new)
            print(f"renamed {name}")
    sys.exit(1 if refused else 0)


def leftovers(paths):
    words = set(load_pairs(GLOSSARY))
    found = False
    for name in tracked(paths):
        path = Path(name)
        if path.suffix in {".cpp", ".h", ".c"}:
            names = c_names(path.read_text())
        elif path.suffix == ".py":
            names = py_names(path.read_text())
        else:
            continue
        for token in sorted(names - FROZEN):
            parts = re.split(r"_|(?<=[a-z])(?=[A-Z])", token)
            if any(p.lower() in words for p in parts):
                found = True
                print(f"{name}: {token}")
    sys.exit(1 if found else 0)


class Renamer(ast.NodeTransformer):
    FIELDS = ("id", "arg", "name", "attr", "asname", "module")

    def __init__(self, pairs):
        self.pairs = pairs

    def generic_visit(self, node):
        for field in self.FIELDS:
            value = getattr(node, field, None)
            if isinstance(value, str):
                setattr(node, field, ".".join(self.pairs.get(p, p) for p in value.split(".")))
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            node.names = [self.pairs.get(n, n) for n in node.names]
        return super().generic_visit(node)


def show(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True, check=True).stdout


def python_pairs(rev_a, rev_b, pairs):
    out = subprocess.run(
        ["git", "diff", "--name-status", "-M", rev_a, rev_b, "--", "*.py"], capture_output=True, text=True, check=True
    ).stdout
    matched, added, deleted = [], [], []
    for line in out.splitlines():
        status, *paths = line.split("\t")
        if status.startswith("R"):
            matched.append((paths[0], paths[1]))
        elif status == "M":
            matched.append((paths[0], paths[0]))
        elif status == "A":
            added.append(paths[0])
        elif status == "D":
            deleted.append(paths[0])
    for old in deleted:
        new = str(Path(old).with_name(pairs.get(Path(old).name, Path(old).name)))
        if new in added:
            added.remove(new)
            matched.append((old, new))
        else:
            matched.append((old, None))
    return matched + [(None, new) for new in added]


def same_python(rev_a, rev_b):
    pairs = load_pairs(MAP)
    ids = identifiers(pairs)
    failed = False
    for old, new in python_pairs(rev_a, rev_b, pairs):
        if old is None or new is None:
            failed = True
            print(f"UNPAIRED {old} -> {new}")
            continue
        a = ast.dump(Renamer(ids).visit(ast.parse(show(rev_a, old))), indent=1)
        b = ast.dump(ast.parse(show(rev_b, new)), indent=1)
        if a == b:
            print(f"same {old} -> {new}")
        else:
            failed = True
            print(f"DIFF {old} -> {new}")
            print("\n".join(list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))[:20]))
    sys.exit(1 if failed else 0)


def run(cmd, cwd=None, env=None, stdin=None):
    done = subprocess.run(cmd, cwd=cwd, env=env, input=stdin, capture_output=True, text=True)
    if done.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{done.stdout[-2000:]}{done.stderr[-2000:]}")
    return done.stdout


def build(root, rev, where):
    run(["git", "-C", root, "worktree", "add", "-q", "--detach", where, rev])
    firmware = Path(where) / "firmware"
    secrets = Path(root) / "firmware/include/wifi_secrets.h"
    (firmware / "include/wifi_secrets.h").write_bytes(secrets.read_bytes())
    ini = firmware / "platformio.ini"
    ini.write_text(SRC_FLAGS.sub(lambda m: f'build_src_flags = -D{m.group(1)}=\\"pin\\"', ini.read_text()))
    run(["pio", "run", "-s"], cwd=firmware, env=dict(os.environ, SOURCE_DATE_EPOCH="0"))
    return {o.name: o for o in (Path(where) / OBJ_DIR).glob("*.o")}


def listing(obj):
    stripped = obj.with_name(obj.name + ".nodebug")
    run([OBJCOPY, "--strip-debug", "-R", ".comment", str(obj), str(stripped)])
    lines = [line for line in run([OBJDUMP, "-dr", "-s", str(stripped)]).splitlines() if "file format" not in line]
    return run([CPPFILT], stdin="\n".join(lines).replace("._Z", ". _Z"))


HEX_ROW = re.compile(r"^ [0-9a-f]{4,} ")


def renamed(text, ids):
    if not ids:
        return text
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, sorted(ids, key=len, reverse=True))) + r")\b")
    return "\n".join(
        line if HEX_ROW.match(line) else pattern.sub(lambda m: ids[m.group(1)], line) for line in text.splitlines()
    )


def same_firmware(rev_a, rev_b):
    pairs = load_pairs(MAP)
    ids = identifiers(pairs)
    root = run(["git", "rev-parse", "--show-toplevel"]).strip()
    work = Path(tempfile.mkdtemp())
    trees = [work / "a", work / "b"]
    try:
        objs_a = build(root, rev_a, str(trees[0]))
        objs_b = build(root, rev_b, str(trees[1]))
        expected = {name: pairs.get(name[:-2], name[:-2]) + ".o" for name in objs_a}
        failed = False
        for name in sorted(objs_a):
            target = expected[name]
            if target not in objs_b:
                failed = True
                print(f"MISSING {name} -> {target}")
                continue
            a = renamed(listing(objs_a[name]), ids)
            b = listing(objs_b[target])
            if a == b:
                print(f"same {name} -> {target}")
            else:
                failed = True
                print(f"DIFF {name} -> {target}")
                print("\n".join(list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))[:20]))
        for name in sorted(set(objs_b) - set(expected.values())):
            failed = True
            print(f"EXTRA {name}")
        sys.exit(1 if failed else 0)
    finally:
        for tree in trees:
            subprocess.run(["git", "-C", root, "worktree", "remove", "--force", str(tree)], capture_output=True)


COMMANDS = {
    "apply": lambda args: apply(args or ["."]),
    "leftovers": lambda args: leftovers(args or ["."]),
    "python": lambda args: same_python(*args),
    "firmware": lambda args: same_firmware(*args),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit("usage: renames.py apply [paths] | leftovers [paths] | python <rev-a> <rev-b> | firmware <rev-a> <rev-b>")
    COMMANDS[sys.argv[1]](sys.argv[2:])
