#!/bin/bash
# 3D-Lötpläne 4b, 5c und 6b als PNG und/oder .blend.
# Aufruf: ./render.sh [samples] [eevee]
# samples=0 erzeugt nur die .blend-Dateien (kein PNG-Render).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SAMPLES=${1:-64}
ENGINE=${2:-}
BL=${BLENDER:-/home/box/apps/blender-4.2.3-linux-x64/blender}
OUT_REPO=$(cd "$HERE/../../../projektdokumentation/fotos/loeten" && pwd)
python3 "$HERE/make_tex.py"
"$BL" -b -P "$HERE/loeten_3d_scene.py" -- 4 "$HERE/loeten_4b_stromweg_3d.blend" "$SAMPLES" $ENGINE
"$BL" -b -P "$HERE/loeten_5c_scene.py" -- blend "$HERE/loeten_5c_fet_3d.blend" "$SAMPLES"
"$BL" -b -P "$HERE/loeten_3d_scene.py" -- 6 "$HERE/loeten_6b_led_regen_3d.blend" "$SAMPLES" $ENGINE
if [ "$SAMPLES" -gt 0 ]; then
  # Wenn als .blend gerendert wurde, liegen raw-PNGs nicht automatisch vor.
  # Für PNG-Ausgabe lieber: ./render.sh 64  (und OUT als .png in älterer Form)
  true
fi
echo "Blend-Dateien:"
ls -la "$HERE"/loeten_*b*.blend "$HERE"/loeten_5c_fet_3d.blend 2>/dev/null || true
