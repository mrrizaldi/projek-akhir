#!/usr/bin/env python3
import re
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CODE_SPAN = re.compile(r"`[^`]*`")
EXTERNAL = ("http://", "https://", "mailto:", "#")


def tracked_markdown(root):
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.split("\n")
    return [p for p in out if p and not p.startswith("laporan/") and "/evals/" not in p]


def missing_targets(root, page):
    found = []
    base = (root / page).parent
    in_fence = False
    for number, line in enumerate((root / page).read_text(encoding="utf-8").split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in LINK.findall(CODE_SPAN.sub("", line)):
            if target.startswith(EXTERNAL):
                continue
            path = target.split("#", 1)[0]
            if path and not (base / path).exists():
                found.append(f"{page}:{number}: missing target {target}")
    return found


def main():
    root = Path(subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    ).stdout.strip())
    problems = [m for page in tracked_markdown(root) for m in missing_targets(root, page)]
    for problem in problems:
        print(problem)
    print(f"{len(problems)} missing link targets")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
