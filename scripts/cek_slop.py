#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

PEMERIKSA = Path.home() / ".claude/skills/indonesian-antislop-writing/scripts/check_slop.py"
OPSI = {"--ringkas": "--summary", "--banding": "--compare"}


def main():
    if not PEMERIKSA.is_file():
        print(f"user skill indonesian-antislop-writing is not installed: {PEMERIKSA} does not exist", file=sys.stderr)
        return 2
    argumen = [OPSI.get(a, a) for a in sys.argv[1:]]
    return subprocess.call([sys.executable, str(PEMERIKSA), *argumen])


if __name__ == "__main__":
    sys.exit(main())
