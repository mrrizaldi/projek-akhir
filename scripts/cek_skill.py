#!/usr/bin/env python3
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

BATAS_DESKRIPSI = 1024
BATAS_BARIS_BADAN = 500
KUNCI_PENILAI = ("type", "focus", "weight")
KUNCI_FRONTMATTER = {"name", "description"}
FOLDER_SKILL = Path(__file__).resolve().parent.parent / ".claude" / "skills"


def pisah_frontmatter(teks):
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


def baca(jalur, masalah):
    try:
        return jalur.read_text(encoding="utf-8")
    except OSError as e:
        masalah.append(f"{jalur}: unreadable ({e})")
        return None


def periksa_skill_md(akar, masalah):
    jalur = akar / "SKILL.md"
    teks = baca(jalur, masalah)
    if teks is None:
        return
    isi, badan = pisah_frontmatter(teks)
    if isi is None:
        masalah.append(f"{jalur}: frontmatter missing")
        return
    lebih = set(isi) - KUNCI_FRONTMATTER
    if lebih:
        masalah.append(f"{jalur}: frontmatter keys other than name/description: {sorted(lebih)}")
    nama = isi.get("name", "")
    if nama != akar.name:
        masalah.append(f"{jalur}: name '{nama}' must equal folder name '{akar.name}'")
    deskripsi = isi.get("description", "")
    if not deskripsi:
        masalah.append(f"{jalur}: description empty or not on one line")
    elif len(deskripsi) > BATAS_DESKRIPSI:
        masalah.append(f"{jalur}: description {len(deskripsi)} characters, maximum {BATAS_DESKRIPSI}")
    if not badan.strip():
        masalah.append(f"{jalur}: body empty")
    elif len(badan.strip("\n").split("\n")) >= BATAS_BARIS_BADAN:
        masalah.append(f"{jalur}: badan {len(badan.splitlines())} lines, must be below {BATAS_BARIS_BADAN}")


def periksa_kasus(kasus, masalah):
    prompt = kasus / "prompt.md"
    if not prompt.is_file():
        masalah.append(f"{prompt}: missing")
    else:
        teks = baca(prompt, masalah)
        if teks is not None:
            isi, badan = pisah_frontmatter(teks)
            if isi is None:
                masalah.append(f"{prompt}: frontmatter missing")
            if not badan.strip():
                masalah.append(f"{prompt}: prompt text empty")

    yaml = kasus / "case.yaml"
    if not yaml.is_file():
        masalah.append(f"{yaml}: missing")
    else:
        teks = baca(yaml, masalah)
        if teks is not None:
            if not re.search(r'^schema_version:\s*"1\.1"\s*$', teks, re.M):
                masalah.append(f'{yaml}: needs schema_version: "1.1"')
            m = re.search(r"^name:\s*(\S+)\s*$", teks, re.M)
            if not m or m.group(1).strip("\"'") != kasus.name:
                masalah.append(f"{yaml}: name must equal folder name '{kasus.name}'")
            if not re.search(r"^expected_outcome:", teks, re.M):
                masalah.append(f"{yaml}: expected_outcome missing")

    penilai = sorted((kasus / "graders").glob("*.md"))
    if not penilai:
        masalah.append(f"{kasus / 'graders'}: needs at least one grader *.md")
    for berkas in penilai:
        teks = baca(berkas, masalah)
        if teks is None:
            continue
        isi, badan = pisah_frontmatter(teks)
        if isi is None:
            masalah.append(f"{berkas}: frontmatter missing")
            continue
        for kunci in KUNCI_PENILAI:
            if not isi.get(kunci):
                masalah.append(f"{berkas}: frontmatter without '{kunci}'")
        if not badan.strip():
            masalah.append(f"{berkas}: statement empty")


def periksa_evals(akar, masalah):
    folder = akar / "evals"
    if not folder.is_dir():
        masalah.append(f"{folder}: missing")
        return
    kasus = sorted(p for p in folder.iterdir() if p.is_dir())
    if not kasus:
        masalah.append(f"{folder}: no cases")
    for k in kasus:
        periksa_kasus(k, masalah)


def periksa_pemicu(akar, masalah):
    jalur = akar / "triggers" / "evals.json"
    if not jalur.is_file():
        masalah.append(f"{jalur}: missing")
        return
    try:
        data = json.loads(jalur.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        masalah.append(f"{jalur}: invalid JSON ({e})")
        return
    if not isinstance(data, list):
        masalah.append(f"{jalur}: must be a JSON list")
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
            masalah.append(f"{jalur}[{i}]: must be {{query: str, should_trigger: bool}}")
        else:
            kelas.add(item["should_trigger"])
    if kelas != {True, False}:
        masalah.append(f"{jalur}: needs entries with should_trigger true and false")


def periksa_skill(akar):
    masalah = []
    periksa_skill_md(akar, masalah)
    if (akar / "eval.md").is_file():
        masalah.append(f"{akar / 'eval.md'}: legacy eval.md, move it to evals/ and triggers/")
        return masalah
    periksa_evals(akar, masalah)
    periksa_pemicu(akar, masalah)
    return masalah


def periksa_semua(folder):
    akar_skill = sorted(p for p in folder.iterdir() if p.is_dir())
    masalah = []
    for akar in akar_skill:
        masalah += periksa_skill(akar)
    return akar_skill, masalah


def tulis(jalur, isi):
    jalur.parent.mkdir(parents=True, exist_ok=True)
    jalur.write_text(isi, encoding="utf-8")


def buat_skill_valid(akar, nama):
    tulis(akar / nama / "SKILL.md", f"---\nname: {nama}\ndescription: satu baris\n---\nisi\n")
    kasus = akar / nama / "evals" / "k1"
    tulis(kasus / "prompt.md", "---\nid: k1\n---\ntanya\n")
    tulis(kasus / "case.yaml", 'schema_version: "1.1"\nname: k1\nexpected_outcome: ok\n')
    tulis(kasus / "graders" / "g1.md", "---\ntype: rubric\nfocus: x\nweight: 1\n---\npernyataan\n")
    pemicu = [{"query": "a", "should_trigger": True}, {"query": "b", "should_trigger": False}]
    tulis(akar / nama / "triggers" / "evals.json", json.dumps(pemicu))


def uji():
    with tempfile.TemporaryDirectory() as tmp:
        akar = Path(tmp)
        buat_skill_valid(akar, "valid")
        _, masalah = periksa_semua(akar)
        assert masalah == [], masalah

        buat_skill_valid(akar, "namasalah")
        tulis(akar / "namasalah" / "SKILL.md", "---\nname: lain\ndescription: x\nextra: y\n---\nisi\n")
        _, masalah = periksa_semua(akar)
        assert any("must equal folder name" in m for m in masalah), masalah
        assert any("other than name/description" in m for m in masalah), masalah

        tulis(akar / "namasalah" / "SKILL.md", f"---\nname: namasalah\ndescription: {'x' * (BATAS_DESKRIPSI + 1)}\n---\nisi\n")
        assert any("characters, maximum" in m for m in periksa_skill(akar / "namasalah"))

        tulis(akar / "namasalah" / "SKILL.md", "---\nname: namasalah\ndescription: x\n---\n" + "baris\n" * BATAS_BARIS_BADAN)
        assert any("must be below" in m for m in periksa_skill(akar / "namasalah"))

        buat_skill_valid(akar, "tanpapemicu")
        (akar / "tanpapemicu" / "triggers" / "evals.json").unlink()
        assert any("evals.json: missing" in m for m in periksa_skill(akar / "tanpapemicu"))

        tulis(akar / "tanpapemicu" / "triggers" / "evals.json", json.dumps([{"query": "a", "should_trigger": True}]))
        assert any("true and false" in m for m in periksa_skill(akar / "tanpapemicu"))

        buat_skill_valid(akar, "tanpapenilai")
        (akar / "tanpapenilai" / "evals" / "k1" / "graders" / "g1.md").unlink()
        assert any("grader" in m for m in periksa_skill(akar / "tanpapenilai"))

        buat_skill_valid(akar, "yamlsalah")
        tulis(akar / "yamlsalah" / "evals" / "k1" / "case.yaml", "name: lain\n")
        assert len(periksa_skill(akar / "yamlsalah")) == 3

        tulis(akar / "lama" / "SKILL.md", "---\nname: lama\ndescription: x\n---\nisi\n")
        tulis(akar / "lama" / "eval.md", "eval lama\n")
        assert any("legacy eval.md" in m for m in periksa_skill(akar / "lama"))

        tulis(akar / "polos" / "SKILL.md", "---\nname: polos\ndescription: x\n---\nisi\n")
        assert len(periksa_skill(akar / "polos")) == 2
    print("self-test passed")


def main():
    parser = argparse.ArgumentParser(description="Structure checker for skills in .claude/skills (SKILL.md, evals/, triggers/).")
    parser.add_argument("--self-test", action="store_true", help="run the checker self-test")
    args = parser.parse_args()
    if args.self_test:
        uji()
        return 0
    akar_skill, masalah = periksa_semua(FOLDER_SKILL)
    for m in masalah:
        print(f"ERROR {m}", file=sys.stderr)
    if masalah:
        print(f"{len(masalah)} problems in {len(akar_skill)} skills", file=sys.stderr)
        return 1
    print(f"ok {len(akar_skill)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
