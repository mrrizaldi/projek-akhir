import ast
import difflib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

if sys.version_info < (3, 12):
    sys.exit("renames.py needs Python >= 3.12 (f-string tokenizing)")

MAP = Path("scripts/rename_map.tsv")
SCOPED = Path("scripts/rename_map_scoped.tsv")
GLOSSARY = Path("scripts/glossary.tsv")
SKIP = (
    "laporan/",
    "presentasi/",
    "model/data/",
    "model/artifacts/",
    ".claude/skills-arsip/",
    "scripts/rename_map.tsv",
    "scripts/rename_map_scoped.tsv",
    "scripts/glossary.tsv",
    "docs/2026-11-22-english-codebase.md",
    "firmware/include/model_int8.h",
)
TEXT_SUFFIXES = {".md", ".sh", ".yml", ".yaml", ".ini", ".json", ".txt", ".inc", ""}
DEV_DOC_DIRS = ("model/data/", "model/artifacts/")
INFO_DIRS = ("laporan/", "presentasi/", ".claude/skills-arsip/")
ONE_OFF = ("scripts/rename_map.tsv", "scripts/rename_map_scoped.tsv", "scripts/glossary.tsv", "docs/2026-11-22-english-codebase.md")
C_SUFFIXES = {".cpp", ".h", ".c"}
FROZEN = {"WIFI_DAFTAR", "BROKER_DAFTAR"}
C_TOKEN = re.compile(r'#include "[^"]+"|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|[A-Za-z_]\w*')
WORD = re.compile(r"\w+")
BIN = Path.home() / ".platformio/packages/toolchain-xtensa-esp32s3/bin"
OBJDUMP = str(BIN / "xtensa-esp32s3-elf-objdump")
OBJCOPY = str(BIN / "xtensa-esp32s3-elf-objcopy")
CPPFILT = str(BIN / "xtensa-esp32s3-elf-c++filt")
SRC_FLAGS = re.compile(r"^build_src_flags = .*?-D([A-Z_]+)=.*$", re.M)
OBJ_DIR = "firmware/.pio/build/esp32-s3/src"


def read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def load_pairs(path, chain=True):
    explicit = {}
    if Path(path).exists():
        for number, line in enumerate(read(path).split("\n"), 1):
            line = line.rstrip("\r")
            if not line.strip():
                continue
            if line.count("\t") != 1:
                sys.exit(f"{path}:{number}: need exactly one TAB")
            old, new = line.split("\t")
            if old in explicit:
                sys.exit(f"{path}:{number}: duplicate key {old}")
            explicit[old] = new
    derived = {}
    for old, new in explicit.items():
        old_stem, old_ext = os.path.splitext(old)
        new_stem, new_ext = os.path.splitext(new)
        if old_ext and old_ext == new_ext and "/" not in old and " " not in old:
            if old_stem in explicit and explicit[old_stem] != new_stem:
                sys.exit(f"{path}: key {old_stem} shadows the stem of {old}")
            if derived.get(old_stem, new_stem) != new_stem:
                sys.exit(f"{path}: conflicting stems for {old_stem}")
            derived[old_stem] = new_stem
    pairs = {**derived, **explicit}
    targets = list(pairs.values())
    clashes = {t for t in targets if targets.count(t) > 1}
    if clashes:
        sys.exit(f"map is not one-to-one: {sorted(clashes)}")
    if chain and set(pairs) & set(targets):
        sys.exit(f"map has chained renames: {sorted(set(pairs) & set(targets))}")
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
    lines = io.StringIO(text).readlines()
    for token in reversed(hits):
        row, col = token.start
        line = lines[row - 1]
        lines[row - 1] = line[:col] + pairs[token.string] + line[token.end[1]:]
    return "".join(lines)


def apply_text(text, pairs):
    safe = {k: v for k, v in pairs.items() if not re.fullmatch(r"[A-Za-z]+", k)}
    if not safe:
        return text
    pattern = re.compile(r"(?:(?<=-D)|(?<![\w-]))(" + "|".join(map(re.escape, sorted(safe, key=len, reverse=True))) + r")(?![\w-])")
    return pattern.sub(lambda m: safe[m.group(1)], text)


def is_skipped(name):
    if name.startswith(DEV_DOC_DIRS) and name.endswith("README.md"):
        return False
    return name.startswith(SKIP)


def is_informational(name):
    return name.startswith(INFO_DIRS) or (name.startswith(DEV_DOC_DIRS) and not name.endswith("README.md"))


def tracked(paths, skip=True, quiet=False):
    raw = subprocess.run(["git", "ls-files", "-z", "--", *paths], capture_output=True, check=True).stdout
    found = []
    for name in raw.decode("utf-8", "surrogateescape").split("\0"):
        if not name or (skip and is_skipped(name)) or not Path(name).is_file():
            continue
        if is_text(name):
            found.append(name)
        elif not quiet:
            print(f"skipped (non-utf8): {name}")
    return found


def is_text(name):
    try:
        read(name)
        return True
    except UnicodeDecodeError:
        return False


def parameter_names(function):
    spec = function.args
    return {a.arg for a in spec.posonlyargs + spec.args + spec.kwonlyargs}


def collect_parameters(tree, accepts):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            accepts.setdefault(node.name, set()).update(parameter_names(node))
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and member.name == "__init__":
                    accepts.setdefault(node.name, set()).update(parameter_names(member))


def terminal_name(func):
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def guard(sources, every_py, pairs):
    ids = identifiers(pairs)
    errors = []
    strings, accepts = set(), {}
    for text in every_py.values():
        strings |= py_strings(text)
        collect_parameters(ast.parse(text), accepts)
    pool = {"c": set(), "py": set()}
    used_all = {"c": set(), "py": set()}
    for path, text in sorted(sources.items()):
        language = "py" if path.endswith(".py") else "c"
        present = py_names(text) if language == "py" else c_names(text)
        used = {k for k in ids if k in present}
        taken = {ids[k] for k in used} & (present - used)
        if taken:
            errors.append(f"{path}: target names already used {sorted(taken)}")
        pool[language] |= present
        used_all[language] |= used
        if language == "py":
            in_strings = used & strings
            if in_strings:
                errors.append(f"{path}: names also in string literals {sorted(in_strings)}")
            for node in ast.walk(ast.parse(text)):
                if isinstance(node, ast.Call):
                    callee = terminal_name(node.func)
                    for keyword in node.keywords:
                        if keyword.arg in used and keyword.arg not in accepts.get(callee, set()):
                            errors.append(f"EXTERNAL-KWARG {path}:{keyword.lineno} {keyword.arg}")
    for language in pool:
        clash = {ids[k] for k in used_all[language]} & pool[language]
        if clash:
            errors.append(f"global collision ({language}): targets already exist {sorted(clash)}")
    return errors


def report_stale(pairs):
    keys = [k for k in pairs if not WORD.fullmatch(k)]
    hits = 0
    if not keys:
        return hits
    pattern = re.compile(r"(?:(?<=-D)|(?<![\w-]))(" + "|".join(map(re.escape, sorted(keys, key=len, reverse=True))) + r")(?![\w-])")
    for name in tracked(["."], skip=False, quiet=True):
        if name in ONE_OFF:
            continue
        label = "stale-info" if is_informational(name) else "stale"
        for number, line in enumerate(read(name).split("\n"), 1):
            for match in pattern.finditer(line):
                print(f"{label} {name}:{number} {match.group(1)}")
                hits += label == "stale"
    return hits


def stale(paths):
    sys.exit(1 if report_stale(load_pairs(MAP)) else 0)


def apply(paths):
    pairs = load_pairs(MAP)
    ids = identifiers(pairs)
    texts = {name: read(name) for name in tracked(paths)}
    sources = {n: t for n, t in texts.items() if Path(n).suffix in C_SUFFIXES or n.endswith(".py")}
    every_py = {n: read(n) for n in tracked(["."], quiet=True) if n.endswith(".py")}
    errors = guard(sources, every_py, pairs)
    if errors:
        for error in errors:
            print(f"REFUSED {error}")
        sys.exit(1)
    for name, text in texts.items():
        path = Path(name)
        if path.suffix in C_SUFFIXES:
            new = apply_c(text, pairs)
        elif path.suffix == ".py":
            new = apply_py(text, ids)
        elif path.suffix in TEXT_SUFFIXES or path.name == "Makefile":
            new = apply_text(text, pairs)
        else:
            continue
        if new != text:
            write(name, new)
            print(f"renamed {name}")
    sys.exit(1 if report_stale(pairs) else 0)


def leftovers(paths):
    words = set(load_pairs(GLOSSARY, chain=False))
    found = False
    for name in tracked(paths):
        path = Path(name)
        if path.suffix in C_SUFFIXES:
            names = c_names(read(name))
        elif path.suffix == ".py":
            names = py_names(read(name))
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
    return subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, check=True).stdout.decode("utf-8")


def python_files(rev):
    raw = subprocess.run(["git", "ls-tree", "-r", "-z", "--name-only", rev], capture_output=True, check=True).stdout
    names = raw.decode("utf-8").split("\0")
    return [n for n in names if n.endswith(".py") and not n.startswith(SKIP)]


def counterpart(old, pairs):
    return str(Path(old).with_name(pairs.get(Path(old).name, Path(old).name)))


def same_python(rev_a, rev_b):
    pairs = load_pairs(MAP)
    ids = identifiers(pairs)
    files_a, files_b = python_files(rev_a), python_files(rev_b)
    sources = {name: show(rev_a, name) for name in files_a}
    failed = False
    for error in guard(sources, sources, pairs):
        failed = True
        print(f"REFUSED {error}")
    claimed = set()
    compared = 0
    for old in files_a:
        new = counterpart(old, pairs)
        if new not in files_b or new in claimed:
            failed = True
            print(f"UNPAIRED {old} -> None")
            continue
        claimed.add(new)
        compared += 1
        a = ast.dump(Renamer(ids).visit(ast.parse(sources[old])), indent=1)
        b = ast.dump(ast.parse(show(rev_b, new)), indent=1)
        if a == b:
            print(f"same {old} -> {new}")
        else:
            failed = True
            print(f"DIFF {old} -> {new}")
            print("\n".join(list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))[:20]))
    for new in sorted(set(files_b) - claimed):
        failed = True
        print(f"UNPAIRED None -> {new}")
    print(f"compared {compared} files")
    sys.exit(1 if failed or compared == 0 else 0)


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
    write(ini, SRC_FLAGS.sub(lambda m: f'build_src_flags = -D{m.group(1)}=\\"pin\\"', read(ini)))
    run(["pio", "run", "-s"], cwd=firmware, env=dict(os.environ, SOURCE_DATE_EPOCH="0"))
    return {o.name: o for o in (Path(where) / OBJ_DIR).glob("*.o")}


def listing(obj):
    stripped = obj.with_name(obj.name + ".nodebug")
    run([OBJCOPY, "--strip-debug", "-R", ".comment", str(obj), str(stripped)])
    lines = [line for line in run([OBJDUMP, "-dr", "-s", "-h", "-t", str(stripped)]).splitlines() if "file format" not in line]
    text = re.sub(r"(_Z\w+)(\.str\d+\.\d+)", r"\1 \2", "\n".join(lines).replace("._Z", ". _Z"))
    text = re.sub(r"(_GLOBAL__sub_[ID]_)(_Z\w+)", r"\1 \2", text)
    return run([CPPFILT], stdin=text)


HEX_ROW = re.compile(r"^ [0-9a-f]{4,} ")


def renamed(text, ids):
    if not ids:
        return text
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, sorted(ids, key=len, reverse=True))) + r")\b")
    return "\n".join(
        line if HEX_ROW.match(line) else pattern.sub(lambda m: ids[m.group(1)], line) for line in text.splitlines()
    )


def load_scoped():
    scoped = {}
    if SCOPED.exists():
        for number, line in enumerate(read(SCOPED).split("\n"), 1):
            if not line.strip():
                continue
            if line.count("\t") != 2:
                sys.exit(f"{SCOPED}:{number}: need exactly two TABs")
            source, old, new = line.split("\t")
            scoped.setdefault(source, {})[old] = new
    return scoped


def scoped_ids(scoped, name, pairs):
    stem = name[:-2]
    merged = {}
    for source in (stem, pairs.get(stem, stem)):
        merged.update(scoped.get(source, {}))
    return merged


def same_firmware(rev_a, rev_b):
    pairs = load_pairs(MAP)
    ids = identifiers(pairs)
    scoped = load_scoped()
    root = run(["git", "rev-parse", "--show-toplevel"]).strip()
    work = Path(tempfile.mkdtemp())
    trees = [work / "a", work / "b"]
    try:
        objs_a = build(root, rev_a, str(trees[0]))
        objs_b = build(root, rev_b, str(trees[1]))
        if not objs_a:
            sys.exit("no objects built")
        expected = {name: pairs.get(name[:-2], name[:-2]) + ".o" for name in objs_a}
        failed = False
        for name in sorted(objs_a):
            target = expected[name]
            if target not in objs_b:
                failed = True
                print(f"MISSING {name} -> {target}")
                continue
            a = renamed(listing(objs_a[name]), {**ids, **scoped_ids(scoped, name, pairs)})
            b = listing(objs_b[target])
            if a.splitlines() == b.splitlines():
                print(f"same {name} -> {target}")
            else:
                failed = True
                print(f"DIFF {name} -> {target}")
                print("\n".join(list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm=""))[:20]))
        for name in sorted(set(objs_b) - set(expected.values())):
            failed = True
            print(f"EXTRA {name}")
        print(f"compared {len(objs_a)} objects")
        sys.exit(1 if failed else 0)
    finally:
        for tree in trees:
            subprocess.run(["git", "-C", root, "worktree", "remove", "--force", str(tree)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)


COMMANDS = {
    "apply": lambda args: apply(args or ["."]),
    "leftovers": lambda args: leftovers(args or ["."]),
    "stale": stale,
    "python": lambda args: same_python(*args),
    "firmware": lambda args: same_firmware(*args),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit("usage: renames.py apply [paths] | stale | leftovers [paths] | python <rev-a> <rev-b> | firmware <rev-a> <rev-b>")
    COMMANDS[sys.argv[1]](sys.argv[2:])
