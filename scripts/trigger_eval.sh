#!/usr/bin/env bash
set -u
MODEL=claude-opus-5-5
KREDENSIAL="$HOME/.claude/.credentials.json"
FOLDER_PERINTAH="$HOME/.claude/commands"

[ $# -ge 1 ] || { echo "pakai: $0 <folder-skill>..." >&2; exit 2; }
command -v uv >/dev/null || { echo "uv tidak ada" >&2; exit 2; }
[ -f "$KREDENSIAL" ] || { echo "kredensial tidak ada, jalankan claude login" >&2; exit 2; }

RUN_EVAL=$(find "$HOME/.claude/skills" -path '*/.trash' -prune -o -path '*skill-creator/scripts/run_eval.py' -print | head -n 1)
[ -n "$RUN_EVAL" ] || { echo "skill-creator tidak ditemukan di ~/.claude/skills" >&2; exit 2; }
SC=$(dirname "$(dirname "$RUN_EVAL")")

bocor() { ls "$FOLDER_PERINTAH" 2>/dev/null | grep -q -- '-skill-'; }
bocor && { echo "LEAK: $FOLDER_PERINTAH sudah memuat *-skill-*" >&2; exit 3; }

T=$(mktemp -d)
trap 'rm -rf "$T/config"' EXIT
mkdir -p "$T/config" "$T/proj/.claude" "$T/out"
cp "$KREDENSIAL" "$T/config/.credentials.json"

for s in "$@"; do
  s=$(cd "$s" && pwd)
  n=$(basename "$s")
  (cd "$T/proj" && CLAUDE_CONFIG_DIR="$T/config" PYTHONPATH="$SC" uv run -q --no-project --with pyyaml python -m scripts.run_eval --eval-set "$s/triggers/evals.json" --skill-path "$s" --runs-per-query 1 --num-workers 4 --timeout 60 --model "$MODEL" > "$T/out/$n.json" 2> "$T/out/$n.err")
  hasil=$(python3 -c 'import json,sys; r=json.load(open(sys.argv[1]))["summary"]; print(str(r["passed"]) + "/" + str(r["total"]))' "$T/out/$n.json" 2>/dev/null) || hasil="gagal"
  echo "nama=$n benar=$hasil"
  echo "json=$T/out/$n.json"
done

bocor && { echo "LEAK" >&2; exit 3; }
exit 0
