#!/usr/bin/env bash
# Sinkronisasi artefak produsen -> konsumen. Jangan copy manual (monorepo CLAUDE.md).
#
#   bash scripts/export_artifacts.sh            # model -> firmware saja (default)
#   bash scripts/export_artifacts.sh --laporan  # + figure -> laporan/*/gambar/
#
# Langkah figure DIMATIKAN secara default: laporan/ read-only tanpa konfirmasi.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="$ROOT/model"
PY="$([ -x "$MODEL_DIR/.venv/bin/python" ] && echo "$MODEL_DIR/.venv/bin/python" || echo python)"

# 1) model_int8.tflite -> firmware/include/model_int8.h (+ scale & zero_point)
echo "==> model -> firmware/include/model_int8.h"
(cd "$MODEL_DIR" && "$PY" scripts/export_model_h.py)

# 2) figure final -> laporan/<projek>/gambar/   (opt-in)
if [[ "${1:-}" == "--laporan" ]]; then
  DEST="$ROOT/laporan/proposal-pa/gambar"
  echo "==> figure -> $DEST"
  mkdir -p "$DEST"
  for f in fase1_100 fase1_segment_100 fase5_training fase6_confusion_fp32 fase7_confusion_int8; do
    src="$MODEL_DIR/artifacts/metrics/$f.png"
    [[ -f "$src" ]] && cp -v "$src" "$DEST/" || echo "    lewat: $f.png belum ada"
  done
else
  echo "==> figure -> laporan/: DILEWATI (pakai --laporan untuk menyalin)"
fi

# 3) diagrams/src/*.mmd -> render -> laporan/  : TODO, belum ada sumber .mmd
echo "==> selesai."
