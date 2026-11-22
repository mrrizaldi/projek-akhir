#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
for page in "$@"; do
  { grep -oE '`[A-Za-z0-9_./-]+\.(cpp|h|py|sh|ini|yml|md):[0-9]+(-[0-9]+)?|`(([A-Za-z0-9_./-]+/)?Makefile):[0-9]+(-[0-9]+)?' "$page" | cut -d'`' -f2 | sort -u || true; } |
  while IFS=: read -r ref range; do
    line=${range%%-*}
    if [ -f "$ref" ]; then
      matches=$ref
    else
      matches=$(git ls-files | grep -E "(^|/)${ref//./\\.}$" || true)
    fi
    count=$(printf '%s' "$matches" | grep -c . || true)
    if [ "$count" -eq 0 ]; then
      printf '%s\t%s:%s\tMISSING\n' "$page" "$ref" "$range"
    elif [ "$count" -gt 1 ]; then
      printf '%s\t%s:%s\tAMBIGUOUS %s\n' "$page" "$ref" "$range" "$(echo $matches)"
    elif [ "$line" -gt "$(wc -l < "$matches")" ]; then
      printf '%s\t%s:%s\tOUT_OF_RANGE\n' "$page" "$matches" "$range"
    else
      printf '%s\t%s:%s\t%s\n' "$page" "$matches" "$range" "$(sed -n "${line}p" "$matches" | sed 's/^[[:space:]]*//' | cut -c1-100)"
    fi
  done
done
