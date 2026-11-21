#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

PEMERIKSA = Path.home() / ".claude/skills/indonesian-antislop-writing/scripts/check_slop.py"
OPSI = {"--ringkas": "--summary", "--banding": "--compare", "--uji": "--self-test"}


def main():
    if not PEMERIKSA.is_file():
        print(f"skill user indonesian-antislop-writing tidak terpasang: {PEMERIKSA} tidak ada", file=sys.stderr)
        return 2
    argumen = [OPSI.get(a, a) for a in sys.argv[1:]]
    return subprocess.call([sys.executable, str(PEMERIKSA), *argumen])


if __name__ == "__main__":
    sys.exit(main())
