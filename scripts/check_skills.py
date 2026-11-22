#!/usr/bin/env python3
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

DESCRIPTION_LIMIT = 1024
BODY_LINE_LIMIT = 500
GRADER_KEYS = ("type", "focus", "weight")
FRONTMATTER_KEYS = {"name", "description"}
SKILLS_FOLDER = Path(__file__).resolve().parent.parent / ".claude" / "skills"


def split_frontmatter(teks):
    baris = teks.split("\n")
    pertama, *_ = baris or [""]
    if pertama.strip() != "---":
        return None, teks
    for i in range(1, len(baris)):
        if baris[i].strip() == "---":
            isi = {}
            for b in baris[1:i]:
                m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", b)
                if m:
                    isi[m.group(1)] = m.group(2).strip()
            return isi, "\n".join(baris[i + 1:])
    return None, teks


def baca(jalur, problems):
    try:
        return jalur.read_text(encoding="utf-8")
    except OSError as e:
        problems.append(f"{jalur}: unreadable ({e})")
        return None


def check_skill_md(base_dir, problems):
    jalur = base_dir / "SKILL.md"
    teks = baca(jalur, problems)
    if teks is None:
        return
    isi, badan = split_frontmatter(teks)
    if isi is None:
        problems.append(f"{jalur}: frontmatter missing")
        return
    lebih = set(isi) - FRONTMATTER_KEYS
    if lebih:
        problems.append(f"{jalur}: frontmatter keys other than name/description: {sorted(lebih)}")
    nama = isi.get("name", "")
    if nama != base_dir.name:
        problems.append(f"{jalur}: name '{nama}' must equal folder name '{base_dir.name}'")
    description_text = isi.get("description", "")
    if not description_text:
        problems.append(f"{jalur}: description empty or not on one line")
    elif len(description_text) > DESCRIPTION_LIMIT:
        problems.append(f"{jalur}: description {len(description_text)} characters, maximum {DESCRIPTION_LIMIT}")
    if not badan.strip():
        problems.append(f"{jalur}: body empty")
    elif len(badan.strip("\n").split("\n")) >= BODY_LINE_LIMIT:
        problems.append(f"{jalur}: body {len(badan.splitlines())} lines, must be below {BODY_LINE_LIMIT}")


def check_case(case_dir, problems):
    prompt = case_dir / "prompt.md"
    if not prompt.is_file():
        problems.append(f"{prompt}: missing")
    else:
        teks = baca(prompt, problems)
        if teks is not None:
            isi, badan = split_frontmatter(teks)
            if isi is None:
                problems.append(f"{prompt}: frontmatter missing")
            if not badan.strip():
                problems.append(f"{prompt}: prompt text empty")

    yaml = case_dir / "case.yaml"
    if not yaml.is_file():
        problems.append(f"{yaml}: missing")
    else:
        teks = baca(yaml, problems)
        if teks is not None:
            if not re.search(r'^schema_version:\s*"1\.1"\s*$', teks, re.M):
                problems.append(f'{yaml}: needs schema_version: "1.1"')
            m = re.search(r"^name:\s*(\S+)\s*$", teks, re.M)
            if not m or m.group(1).strip("\"'") != case_dir.name:
                problems.append(f"{yaml}: name must equal folder name '{case_dir.name}'")
            if not re.search(r"^expected_outcome:", teks, re.M):
                problems.append(f"{yaml}: expected_outcome missing")

    graders = sorted((case_dir / "graders").glob("*.md"))
    if not graders:
        problems.append(f"{case_dir / 'graders'}: needs at least one grader *.md")
    for berkas in graders:
        teks = baca(berkas, problems)
        if teks is None:
            continue
        isi, badan = split_frontmatter(teks)
        if isi is None:
            problems.append(f"{berkas}: frontmatter missing")
            continue
        for kunci in GRADER_KEYS:
            if not isi.get(kunci):
                problems.append(f"{berkas}: frontmatter without '{kunci}'")
        if not badan.strip():
            problems.append(f"{berkas}: statement empty")


def check_evals(base_dir, problems):
    folder = base_dir / "evals"
    if not folder.is_dir():
        problems.append(f"{folder}: missing")
        return
    case_dir = sorted(p for p in folder.iterdir() if p.is_dir())
    if not case_dir:
        problems.append(f"{folder}: no cases")
    for k in case_dir:
        check_case(k, problems)


def check_triggers(base_dir, problems):
    jalur = base_dir / "triggers" / "evals.json"
    if not jalur.is_file():
        problems.append(f"{jalur}: missing")
        return
    try:
        data = json.loads(jalur.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        problems.append(f"{jalur}: invalid JSON ({e})")
        return
    if not isinstance(data, list):
        problems.append(f"{jalur}: must be a JSON list")
        return
    kelas = set()
    for i, item in enumerate(data):
        sah = (
            isinstance(item, dict)
            and isinstance(item.get("query"), str)
            and item["query"].strip()
            and isinstance(item.get("should_trigger"), bool)
        )
        if not sah:
            problems.append(f"{jalur}[{i}]: must be {{query: str, should_trigger: bool}}")
        else:
            kelas.add(item["should_trigger"])
    if kelas != {True, False}:
        problems.append(f"{jalur}: needs entries with should_trigger true and false")


def check_skill(base_dir):
    problems = []
    check_skill_md(base_dir, problems)
    if (base_dir / "eval.md").is_file():
        problems.append(f"{base_dir / 'eval.md'}: legacy eval.md, move it to evals/ and triggers/")
        return problems
    check_evals(base_dir, problems)
    check_triggers(base_dir, problems)
    return problems


def check_all(folder):
    skill_dirs = sorted(p for p in folder.iterdir() if p.is_dir())
    problems = []
    for base_dir in skill_dirs:
        problems += check_skill(base_dir)
    return skill_dirs, problems


def tulis(jalur, isi):
    jalur.parent.mkdir(parents=True, exist_ok=True)
    jalur.write_text(isi, encoding="utf-8")


def make_valid_skill(base_dir, nama):
    tulis(base_dir / nama / "SKILL.md", f"---\nname: {nama}\ndescription: satu baris\n---\nisi\n")
    case_dir = base_dir / nama / "evals" / "k1"
    tulis(case_dir / "prompt.md", "---\nid: k1\n---\ntanya\n")
    tulis(case_dir / "case.yaml", 'schema_version: "1.1"\nname: k1\nexpected_outcome: ok\n')
    tulis(case_dir / "graders" / "g1.md", "---\ntype: rubric\nfocus: x\nweight: 1\n---\npernyataan\n")
    triggers = [{"query": "a", "should_trigger": True}, {"query": "b", "should_trigger": False}]
    tulis(base_dir / nama / "triggers" / "evals.json", json.dumps(triggers))


def uji():
    with tempfile.TemporaryDirectory() as tmp:
        base_dir = Path(tmp)
        make_valid_skill(base_dir, "valid")
        _, problems = check_all(base_dir)
        assert problems == [], problems

        make_valid_skill(base_dir, "namasalah")
        tulis(base_dir / "namasalah" / "SKILL.md", "---\nname: lain\ndescription: x\nextra: y\n---\nisi\n")
        _, problems = check_all(base_dir)
        assert any("must equal folder name" in m for m in problems), problems
        assert any("other than name/description" in m for m in problems), problems

        tulis(base_dir / "namasalah" / "SKILL.md", f"---\nname: namasalah\ndescription: {'x' * (DESCRIPTION_LIMIT + 1)}\n---\nisi\n")
        assert any("characters, maximum" in m for m in check_skill(base_dir / "namasalah"))

        tulis(base_dir / "namasalah" / "SKILL.md", "---\nname: namasalah\ndescription: x\n---\n" + "baris\n" * BODY_LINE_LIMIT)
        assert any("must be below" in m for m in check_skill(base_dir / "namasalah"))

        make_valid_skill(base_dir, "tanpapemicu")
        (base_dir / "tanpapemicu" / "triggers" / "evals.json").unlink()
        assert any("evals.json: missing" in m for m in check_skill(base_dir / "tanpapemicu"))

        tulis(base_dir / "tanpapemicu" / "triggers" / "evals.json", json.dumps([{"query": "a", "should_trigger": True}]))
        assert any("true and false" in m for m in check_skill(base_dir / "tanpapemicu"))

        make_valid_skill(base_dir, "tanpapenilai")
        (base_dir / "tanpapenilai" / "evals" / "k1" / "graders" / "g1.md").unlink()
        assert any("grader" in m for m in check_skill(base_dir / "tanpapenilai"))

        make_valid_skill(base_dir, "yamlsalah")
        tulis(base_dir / "yamlsalah" / "evals" / "k1" / "case.yaml", "name: lain\n")
        assert len(check_skill(base_dir / "yamlsalah")) == 3

        tulis(base_dir / "lama" / "SKILL.md", "---\nname: lama\ndescription: x\n---\nisi\n")
        tulis(base_dir / "lama" / "eval.md", "eval lama\n")
        assert any("legacy eval.md" in m for m in check_skill(base_dir / "lama"))

        tulis(base_dir / "polos" / "SKILL.md", "---\nname: polos\ndescription: x\n---\nisi\n")
        assert len(check_skill(base_dir / "polos")) == 2
    print("self-test passed")


def main():
    parser = argparse.ArgumentParser(description="Structure checker for skills in .claude/skills (SKILL.md, evals/, triggers/).")
    parser.add_argument("--self-test", action="store_true", help="run the checker self-test")
    args = parser.parse_args()
    if args.self_test:
        uji()
        return 0
    skill_dirs, problems = check_all(SKILLS_FOLDER)
    for m in problems:
        print(f"ERROR {m}", file=sys.stderr)
    if problems:
        print(f"{len(problems)} problems in {len(skill_dirs)} skills", file=sys.stderr)
        return 1
    print(f"ok {len(skill_dirs)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
