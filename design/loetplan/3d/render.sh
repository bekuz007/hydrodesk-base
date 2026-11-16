#!/bin/bash
# 3D-Lötpläne 4b und 6b rendern (Blender 4.2, headless).
# Aufruf: ./render.sh [samples] [eevee]
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SAMPLES=${1:-64}
ENGINE=${2:-}
BL=${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}
OUT_REPO=$(cd "$HERE/../../../projektdokumentation/fotos/loeten" && pwd)
python3 "$HERE/make_tex.py"
"$BL" -b -P "$HERE/loeten_3d_scene.py" -- 4 "$HERE/raw_4.png" "$SAMPLES" $ENGINE
"$BL" -b -P "$HERE/loeten_3d_scene.py" -- 6 "$HERE/raw_6.png" "$SAMPLES" $ENGINE
python3 "$HERE/annotate_loeten_3d.py" "$HERE" "$HERE"
cp -f "$HERE/loeten_4b_stromweg_3d.png" "$OUT_REPO/"
cp -f "$HERE/loeten_6b_led_regen_3d.png" "$OUT_REPO/"
echo "fertig: $OUT_REPO/loeten_4b_stromweg_3d.png"
echo "fertig: $OUT_REPO/loeten_6b_led_regen_3d.png"
