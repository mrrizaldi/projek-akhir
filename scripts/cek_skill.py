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
        masalah.append(f"{jalur}: tidak terbaca ({e})")
        return None


def periksa_skill_md(akar, masalah):
    jalur = akar / "SKILL.md"
    teks = baca(jalur, masalah)
    if teks is None:
        return
    isi, badan = pisah_frontmatter(teks)
    if isi is None:
        masalah.append(f"{jalur}: frontmatter tidak ada")
        return
    lebih = set(isi) - KUNCI_FRONTMATTER
    if lebih:
        masalah.append(f"{jalur}: kunci frontmatter selain name/description: {sorted(lebih)}")
    nama = isi.get("name", "")
    if nama != akar.name:
        masalah.append(f"{jalur}: name '{nama}' harus sama dengan nama folder '{akar.name}'")
    deskripsi = isi.get("description", "")
    if not deskripsi:
        masalah.append(f"{jalur}: description kosong atau tidak satu baris")
    elif len(deskripsi) > BATAS_DESKRIPSI:
        masalah.append(f"{jalur}: description {len(deskripsi)} karakter, maksimum {BATAS_DESKRIPSI}")
    if not badan.strip():
        masalah.append(f"{jalur}: badan kosong")
    elif len(badan.strip("\n").split("\n")) >= BATAS_BARIS_BADAN:
        masalah.append(f"{jalur}: badan {len(badan.splitlines())} baris, harus di bawah {BATAS_BARIS_BADAN}")


def periksa_kasus(kasus, masalah):
    prompt = kasus / "prompt.md"
    if not prompt.is_file():
        masalah.append(f"{prompt}: tidak ada")
    else:
        teks = baca(prompt, masalah)
        if teks is not None:
            isi, badan = pisah_frontmatter(teks)
            if isi is None:
                masalah.append(f"{prompt}: frontmatter tidak ada")
            if not badan.strip():
                masalah.append(f"{prompt}: teks prompt kosong")

    yaml = kasus / "case.yaml"
    if not yaml.is_file():
        masalah.append(f"{yaml}: tidak ada")
    else:
        teks = baca(yaml, masalah)
        if teks is not None:
            if not re.search(r'^schema_version:\s*"1\.1"\s*$', teks, re.M):
                masalah.append(f'{yaml}: perlu schema_version: "1.1"')
            m = re.search(r"^name:\s*(\S+)\s*$", teks, re.M)
            if not m or m.group(1).strip("\"'") != kasus.name:
                masalah.append(f"{yaml}: name harus sama dengan nama folder '{kasus.name}'")
            if not re.search(r"^expected_outcome:", teks, re.M):
                masalah.append(f"{yaml}: expected_outcome tidak ada")

    penilai = sorted((kasus / "graders").glob("*.md"))
    if not penilai:
        masalah.append(f"{kasus / 'graders'}: perlu minimal satu penilai *.md")
    for berkas in penilai:
        teks = baca(berkas, masalah)
        if teks is None:
            continue
        isi, badan = pisah_frontmatter(teks)
        if isi is None:
            masalah.append(f"{berkas}: frontmatter tidak ada")
            continue
        for kunci in KUNCI_PENILAI:
            if not isi.get(kunci):
                masalah.append(f"{berkas}: frontmatter tanpa '{kunci}'")
        if not badan.strip():
            masalah.append(f"{berkas}: pernyataan kosong")


def periksa_evals(akar, masalah):
    folder = akar / "evals"
    if not folder.is_dir():
        masalah.append(f"{folder}: tidak ada")
        return
    kasus = sorted(p for p in folder.iterdir() if p.is_dir())
    if not kasus:
        masalah.append(f"{folder}: tanpa kasus")
    for k in kasus:
        periksa_kasus(k, masalah)


def periksa_pemicu(akar, masalah):
    jalur = akar / "triggers" / "evals.json"
    if not jalur.is_file():
        masalah.append(f"{jalur}: tidak ada")
        return
    try:
        data = json.loads(jalur.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        masalah.append(f"{jalur}: JSON tidak valid ({e})")
        return
    if not isinstance(data, list):
        masalah.append(f"{jalur}: harus berupa daftar JSON")
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
            masalah.append(f"{jalur}[{i}]: harus {{query: str, should_trigger: bool}}")
        else:
            kelas.add(item["should_trigger"])
    if kelas != {True, False}:
        masalah.append(f"{jalur}: perlu entri should_trigger true dan false")


def periksa_skill(akar):
    masalah = []
    periksa_skill_md(akar, masalah)
    if (akar / "eval.md").is_file():
        masalah.append(f"{akar / 'eval.md'}: eval.md lama, pindahkan ke evals/ dan triggers/")
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
        assert any("harus sama dengan nama folder" in m for m in masalah), masalah
        assert any("selain name/description" in m for m in masalah), masalah

        tulis(akar / "namasalah" / "SKILL.md", f"---\nname: namasalah\ndescription: {'x' * (BATAS_DESKRIPSI + 1)}\n---\nisi\n")
        assert any("karakter, maksimum" in m for m in periksa_skill(akar / "namasalah"))

        tulis(akar / "namasalah" / "SKILL.md", "---\nname: namasalah\ndescription: x\n---\n" + "baris\n" * BATAS_BARIS_BADAN)
        assert any("harus di bawah" in m for m in periksa_skill(akar / "namasalah"))

        buat_skill_valid(akar, "tanpapemicu")
        (akar / "tanpapemicu" / "triggers" / "evals.json").unlink()
        assert any("evals.json: tidak ada" in m for m in periksa_skill(akar / "tanpapemicu"))

        tulis(akar / "tanpapemicu" / "triggers" / "evals.json", json.dumps([{"query": "a", "should_trigger": True}]))
        assert any("true dan false" in m for m in periksa_skill(akar / "tanpapemicu"))

        buat_skill_valid(akar, "tanpapenilai")
        (akar / "tanpapenilai" / "evals" / "k1" / "graders" / "g1.md").unlink()
        assert any("penilai" in m for m in periksa_skill(akar / "tanpapenilai"))

        buat_skill_valid(akar, "yamlsalah")
        tulis(akar / "yamlsalah" / "evals" / "k1" / "case.yaml", "name: lain\n")
        assert len(periksa_skill(akar / "yamlsalah")) == 3

        tulis(akar / "lama" / "SKILL.md", "---\nname: lama\ndescription: x\n---\nisi\n")
        tulis(akar / "lama" / "eval.md", "eval lama\n")
        assert any("eval.md lama" in m for m in periksa_skill(akar / "lama"))

        tulis(akar / "polos" / "SKILL.md", "---\nname: polos\ndescription: x\n---\nisi\n")
        assert len(periksa_skill(akar / "polos")) == 2
    print("uji lulus")


def main():
    parser = argparse.ArgumentParser(description="Pemeriksa struktur skill di .claude/skills (SKILL.md, evals/, triggers/).")
    parser.add_argument("--uji", action="store_true", help="uji mandiri pemeriksa")
    args = parser.parse_args()
    if args.uji:
        uji()
        return 0
    akar_skill, masalah = periksa_semua(FOLDER_SKILL)
    for m in masalah:
        print(f"GALAT {m}", file=sys.stderr)
    if masalah:
        print(f"{len(masalah)} masalah di {len(akar_skill)} skill", file=sys.stderr)
        return 1
    print(f"ok {len(akar_skill)} skill")
    return 0


if __name__ == "__main__":
    sys.exit(main())
