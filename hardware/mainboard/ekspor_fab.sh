#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
OUT=fab/gerber
ZIP=fab/mainboard-gerber-jlcpcb.zip
/usr/bin/python3 tata_letak.py tuang
rm -rf "$OUT" "$ZIP"
mkdir -p "$OUT"
kicad-cli pcb export gerbers -o "$OUT/" \
  -l F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  --subtract-soldermask mainboard.kicad_pcb
kicad-cli pcb export drill -o "$OUT/" --format excellon --drill-origin absolute \
  --excellon-units mm --excellon-zeros-format decimal --excellon-oval-format alternate \
  --excellon-separate-th --generate-map --map-format gerberx2 mainboard.kicad_pcb
python3 -I -c "import shutil,sys; shutil.make_archive(sys.argv[1][:-4], 'zip', sys.argv[2])" "$ZIP" "$OUT"
ls -l "$ZIP"
