#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

CHECKER_PATH = Path.home() / ".claude/skills/indonesian-antislop-writing/scripts/check_slop.py"


def main():
    if not CHECKER_PATH.is_file():
        print(f"user skill indonesian-antislop-writing is not installed: {CHECKER_PATH} does not exist", file=sys.stderr)
        return 2
    return subprocess.call([sys.executable, str(CHECKER_PATH), *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())
