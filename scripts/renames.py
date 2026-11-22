import ast
import difflib
import io
import keyword
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
INTROSPECTION = {"locals", "vars", "globals", "dir", "eval", "exec", "__name__", "__qualname__", "__code__", "__dict__", "inspect", "pickle", "joblib", "dill"}
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
    py_rows = python_rows(load_scoped(pairs), every_py, pairs)
    errors = guard(sources, every_py, pairs) + scoped_guard(py_rows, every_py, working_texts)
    if errors:
        for error in errors:
            print(f"REFUSED {error}")
        sys.exit(1)
    for name, text in texts.items():
        path = Path(name)
        if path.suffix in C_SUFFIXES:
            new = apply_c(text, pairs)
        elif path.suffix == ".py":
            new = apply_py(text, {**ids, **py_rows.get(name, {})})
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
    py_rows = python_rows(load_scoped(pairs), sources, pairs)
    failed = False
    for error in guard(sources, sources, pairs) + scoped_guard(py_rows, sources, lambda: revision_texts(rev_b)):
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
        a = ast.dump(Renamer({**ids, **py_rows.get(old, {})}).visit(ast.parse(sources[old])), indent=1)
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
    dump = run([OBJDUMP, "-dr", "-s", "-h", "-t", str(stripped)]) + run([OBJDUMP, "-r", str(stripped)])
    lines = [line for line in dump.splitlines() if "file format" not in line]
    text = re.sub(r"(_Z\w+)(\.str\d+\.\d+)", r"\1 \2", "\n".join(lines).replace("._Z", ". _Z"))
    text = re.sub(r"(_GLOBAL__sub_[ID]_)(?=[A-Za-z_])", r"\1 ", text)
    text = re.sub(r"(_Z[A-Za-z0-9_]+?)(\$\w+\$\d+)", r"\1 \2", text)
    return run([CPPFILT], stdin=text)


HEX_ROW = re.compile(r"^ [0-9a-f]{4,} ")


def renamed(text, ids):
    if not ids:
        return text
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, sorted(ids, key=len, reverse=True))) + r")\b")
    return "\n".join(
        line if HEX_ROW.match(line) else pattern.sub(lambda m: ids[m.group(1)], line) for line in text.splitlines()
    )


def firmware_sources():
    found = set()
    for pattern in ("firmware/src/*.cpp", "firmware/include/*.h", "firmware/test/**/*"):
        found |= {p.name for p in Path(".").glob(pattern) if p.is_file()}
    return found


def load_scoped(pairs=None):
    scoped = {}
    if not SCOPED.exists():
        return scoped
    pairs = load_pairs(MAP) if pairs is None else pairs
    forbidden = set(pairs) | set(pairs.values())
    sources = firmware_sources()
    python_sources = {n for n in tracked(["."], quiet=True) if n.endswith(".py")}
    for number, line in enumerate(read(SCOPED).split("\n"), 1):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        if line.count("\t") != 2:
            sys.exit(f"{SCOPED}:{number}: need exactly two TABs")
        source, old, new = line.split("\t")
        if source not in sources | python_sources:
            sys.exit(f"{SCOPED}:{number}: {source} is not a firmware source file or a tracked Python path")
        if source in python_sources and (old in pairs or not new.isidentifier() or keyword.iskeyword(new)):
            sys.exit(f"{SCOPED}:{number}: {source}: {old} is a global key or {new} is not a Python name")
        rows = scoped.setdefault(source, {})
        if old in rows:
            sys.exit(f"{SCOPED}:{number}: duplicate {source} {old}")
        if new in rows.values():
            sys.exit(f"{SCOPED}:{number}: {source}: two names become {new}")
        if new in forbidden:
            sys.exit(f"{SCOPED}:{number}: scoped target {new} equals a global key or target")
        rows[old] = new
    return scoped


def python_rows(scoped, files, pairs):
    found = {}
    for name in files:
        rows = {**scoped.get(name, {}), **scoped.get(counterpart(name, pairs), {})}
        if rows:
            found[name] = rows
    return found


def scope_bindings(nodes):
    found = set()
    pending = list(nodes)
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.add(node.name)
            continue
        if isinstance(node, ast.Lambda):
            continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            found.add(node.id)
        elif isinstance(node, ast.alias):
            found.add((node.asname or node.name).split(".")[0])
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            found.add(node.name)
        pending.extend(ast.iter_child_nodes(node))
    return found


def module_level(tree):
    declared = {n for node in ast.walk(tree) if isinstance(node, ast.Global) for n in node.names}
    return scope_bindings(tree.body) | declared


def class_members(tree):
    return {n for node in ast.walk(tree) if isinstance(node, ast.ClassDef) for n in scope_bindings(node.body)}


def bound_names(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            found.add(node.id)
        elif isinstance(node, ast.arg):
            found.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.add(node.name)
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            found.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            found.add(node.rest)
        elif isinstance(node, ast.alias):
            found.add((node.asname or node.name).split(".")[0])
    return found


def is_fixture(function):
    for decorator in function.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if terminal_name(target) == "fixture":
            return True
    return False


def fixture_names(trees):
    found = set()
    for path, tree in trees.items():
        if Path(path).name == "conftest.py":
            found |= module_level(tree)
        found |= {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_fixture(n)}
    return found


def introspection_hits(tree, names):
    attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    return sorted((names - {"__name__"} | attributes) & INTROSPECTION)


def shape_problem(old, new):
    if new.startswith("__"):
        return f"{new} starts with a double underscore"
    if old.startswith("_") != new.startswith("_"):
        return "the leading underscore changes"
    if old.startswith("test") != new.startswith("test"):
        return "the test prefix changes (pytest collection)"
    return None


def working_texts():
    return {n: read(n) for n in tracked(["."], quiet=True) if is_doc_text(n)}


def revision_texts(rev):
    raw = subprocess.run(["git", "ls-tree", "-r", "-z", "--name-only", rev], capture_output=True, check=True).stdout
    names = [n for n in raw.decode("utf-8").split("\0") if n and not is_skipped(n) and is_doc_text(n)]
    found = {}
    for name in names:
        text = revision_text(rev, name)
        if text is not None:
            found[name] = text
    return found


def is_doc_text(name):
    path = Path(name)
    return path.suffix in TEXT_SUFFIXES or path.name.startswith("Makefile")


def text_references(word, texts):
    pattern = re.compile(rf"(?<!\w){re.escape(word)}(?!\w)")
    return [f"{name}:{number}" for name, text in sorted(texts.items()) for number, line in enumerate(text.split("\n"), 1) if pattern.search(line)]


def module_stem(path):
    path = Path(path)
    return path.parent.name if path.stem == "__init__" else path.stem


def import_facts(tree):
    imported, module_parts = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            module_parts |= set(module.split("."))
            imported += [(module.rpartition(".")[2], alias.name) for alias in node.names]
        elif isinstance(node, ast.Import):
            module_parts |= {part for alias in node.names for part in alias.name.split(".")}
    return imported, module_parts


def scoped_guard(rows_by_file, every_py, load_texts):
    if not rows_by_file:
        return []
    trees = {p: ast.parse(t) for p, t in every_py.items()}
    names = {p: py_names(t) for p, t in every_py.items()}
    facts = {p: import_facts(tree) for p, tree in trees.items()}
    modules = {part for p in every_py for part in Path(p).with_suffix("").parts}
    repo_stems = {module_stem(p) for p in every_py}
    fixtures = fixture_names(trees)
    every_string = set().union(*(py_strings(t) for t in every_py.values()))
    texts = None
    attrs, kwargs = set(), {}
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                attrs.add(node.attr)
            elif isinstance(node, ast.MatchClass):
                attrs.update(node.kwd_attrs)
            elif isinstance(node, (ast.Call, ast.ClassDef)):
                func = node.func if isinstance(node, ast.Call) else None
                for item in node.keywords:
                    kwargs.setdefault(item.arg, []).append((path, item.lineno, func))
    errors = []
    for path, rows in sorted(rows_by_file.items()):
        active = {old: new for old, new in rows.items() if old in names.get(path, ())}
        if not active:
            continue
        tree = trees[path]
        top, members, bound = module_level(tree), class_members(tree), bound_names(tree)
        accepts = {n.name: parameter_names(n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        imported, module_parts = facts[path]
        imported_names = {(a.asname or a.name).split(".")[0] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
        external = {name for last, name in imported if last not in repo_stems}
        stem = module_stem(path)
        importers = {g for g, (their, _) in facts.items() if g != path and any(last == stem for last, _ in their)}
        strings = py_strings(every_py[path]).union(*(py_strings(every_py[g]) for g in importers))
        if any(name == "*" for _, name in imported):
            errors.append(f"SCOPED-STAR-IMPORT {path}: scoped rows need explicit imports")
        introspection = introspection_hits(tree, names[path])
        if introspection:
            errors.append(f"SCOPED-INTROSPECTION {path}: the file uses {introspection}, so no scoped rows")
        for old, new in sorted(active.items()):
            where = f"{path}: {old} -> {new}"
            shape = shape_problem(old, new)
            module_level_name = old in top
            checks = (
                (new in names[path], "SCOPED-TARGET-TAKEN", f"{new} already appears in the file"),
                (old not in bound, "SCOPED-UNBOUND", f"{old} is never bound in the file (builtin or external name)"),
                (old in external, "SCOPED-EXTERNAL-IMPORT", f"{old} is imported from a module outside the repo"),
                (shape is not None, "SCOPED-SHAPE", shape),
                (old in fixtures, "SCOPED-FIXTURE", f"{old} is a pytest fixture or a conftest.py name"),
                (old in attrs, "SCOPED-ATTRIBUTE", f"{old} is an attribute name somewhere in the repo"),
                (old in members, "SCOPED-CLASS-MEMBER", f"{old} is bound in a class body"),
                (old in modules | module_parts, "SCOPED-MODULE-NAME", f"{old} is a module or package name"),
                (old in strings, "SCOPED-STRING", f"{old} appears in a string literal of the file or of a file importing it"),
                (module_level_name and old in every_string, "SCOPED-STRING", f"module-level {old} appears in a string literal of the repo"),
            )
            errors += [f"{label} {where}: {reason}" for hit, label, reason in checks if hit]
            for other, line, func in kwargs.get(old, []):
                callee = func.id if isinstance(func, ast.Name) else None
                local = other == path and callee not in imported_names and old in accepts.get(callee, set())
                if not local:
                    errors.append(f"SCOPED-KWARG {where}: keyword {old}= at {other}:{line} is not a call to a module-level function of {path}")
            if not module_level_name:
                continue
            texts = load_texts() if texts is None else texts
            errors += [f"SCOPED-TEXT-REF {ref} {where}: update the reference or pick another name" for ref in text_references(old, texts)]
            for other, (their, _) in sorted(facts.items()):
                linked = other in importers and ((stem, old) in their or (stem, "*") in their)
                linked = linked or (other != path and (module_stem(other), old) in imported)
                if linked and rows_by_file.get(other, {}).get(old) != new:
                    errors.append(f"SCOPED-UNLINKED {where}: {other} shares the module-level name without the same row")
    return errors


def scoped_ids(scoped, name, pairs):
    stem = name[:-2]
    merged = {}
    for source in (stem, pairs.get(stem, stem)):
        merged.update(scoped.get(source, {}))
    return merged


def same_firmware(rev_a, rev_b):
    pairs = load_pairs(MAP)
    ids = identifiers(pairs)
    scoped = load_scoped(pairs)
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
            if [" ".join(l.split()) for l in a.splitlines() if l.strip()] == [" ".join(l.split()) for l in b.splitlines() if l.strip()]:
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


TOKEN = re.compile(r'#include\s*"[^"]+"|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|[A-Za-z_]\w*|\S')


def revision_text(rev, path):
    done = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else None


def revision_sources(rev):
    listing_ = run(["git", "ls-tree", "-r", "--name-only", rev, "--", "firmware/src", "firmware/include", "firmware/test"])
    return [n for n in listing_.split() if n.endswith((".cpp", ".h")) and not n.endswith("model_int8.h")]


def counterpart_path(path, pairs):
    parts = Path(path).parts
    return "/".join(pairs.get(part, part) if i < len(parts) - 1 else pairs.get(part, part) for i, part in enumerate(parts))


def mapped_tokens(text, mapping, pairs):
    out = []
    for match in TOKEN.finditer(text):
        token = match.group(0)
        if token.startswith("#include"):
            name = re.search(r'"([^"]+)"', token).group(1)
            out.append(f'#include "{pairs.get(name, name)}"')
        elif token[0] in "\"\'":
            out.append(token)
        else:
            out.append(mapping.get(token, token))
    return out


def same_tokens(rev_a, rev_b):
    pairs = load_pairs(MAP)
    ids = identifiers(pairs)
    scoped = load_scoped(pairs)
    failed = False
    paired = set()
    for old in revision_sources(rev_a):
        new = counterpart_path(old, pairs)
        paired.add(new)
        text_a, text_b = revision_text(rev_a, old), revision_text(rev_b, new)
        if text_b is None:
            failed = True
            print(f"UNPAIRED {old} -> {new}")
            continue
        base_old, base_new = Path(old).name, Path(new).name
        mapping = {**ids, **scoped.get(base_old, {}), **scoped.get(base_new, {})}
        tokens_a = mapped_tokens(text_a, mapping, pairs)
        tokens_b = [m.group(0) for m in TOKEN.finditer(text_b)]
        if tokens_a != tokens_b:
            failed = True
            where = next((i for i, (x, y) in enumerate(zip(tokens_a, tokens_b)) if x != y), min(len(tokens_a), len(tokens_b)))
            print(f"DIFF {old} -> {new} at token {where}: {tokens_a[where:where + 6]} vs {tokens_b[where:where + 6]}")
            continue
        names_a = [m.group(0) for m in TOKEN.finditer(text_a) if WORD.fullmatch(m.group(0)) and not m.group(0)[0].isdigit()]
        names_b = [m.group(0) for m in TOKEN.finditer(text_b) if WORD.fullmatch(m.group(0)) and not m.group(0)[0].isdigit()]
        forward, backward = {}, {}
        for x, y in zip(names_a, names_b):
            forward.setdefault(x, set()).add(y)
            backward.setdefault(y, set()).add(x)
        broken = [(k, v) for k, v in {**forward, **backward}.items() if len(v) > 1]
        if broken:
            failed = True
            print(f"BIJECTION-FAIL {new}: {broken[:4]}")
            continue
        print(f"same {old} -> {new}")
    for extra in revision_sources(rev_b):
        if extra not in paired:
            failed = True
            print(f"UNPAIRED {extra}")
    sys.exit(1 if failed else 0)


COMMANDS = {
    "apply": lambda args: apply(args or ["."]),
    "leftovers": lambda args: leftovers(args or ["."]),
    "stale": stale,
    "python": lambda args: same_python(*args),
    "firmware": lambda args: same_firmware(*args),
    "tokens": lambda args: same_tokens(*args),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit("usage: renames.py apply [paths] | stale | leftovers [paths] | python <rev-a> <rev-b> | firmware <rev-a> <rev-b> | tokens <rev-a> <rev-b>")
    COMMANDS[sys.argv[1]](sys.argv[2:])
