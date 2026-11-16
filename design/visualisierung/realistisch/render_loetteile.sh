#!/bin/bash
# Rendert die Lötübersicht (nur die zu lötenden Teile, nach Lötschritt) aus dem realistischen Modell
# und beschriftet sie. Ergebnis: projektdokumentation/fotos/loeten/loeten_teileuebersicht.png
# Aufruf: render_loetteile.sh [Samples]   (Standard 128)
set -euo pipefail
B=${BLENDER:-/opt/blender-dl/blender-4.5.4-linux-x64/blender}
if [ ! -x "$B" ]; then
  for c in /home/box/apps/blender-4.2.3-linux-x64/blender blender; do
    if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then B=$c; break; fi
  done
fi
S=${1:-128}
HERE="$(cd "$(dirname "$0")" && pwd)"
RAW="$HERE/raw"
SRC="$HERE/src"
OUT="$(cd "$HERE/../../../projektdokumentation/fotos/loeten" && pwd)/"
mkdir -p "$RAW"
echo "Blender: $B  Samples: $S"
"$B" -b -P "$SRC/real_scene.py" -- v_loetteile "$RAW/loetteile.png" "$S" 100 > "$RAW/loetteile.log" 2>&1 || {
  echo "Fehler beim Rendern, siehe $RAW/loetteile.log"
  tail -40 "$RAW/loetteile.log"
  exit 1
}
echo "Render fertig"
python3 "$SRC/real_final.py" "$RAW/" "$OUT" loetteile
cp -f "${OUT}loeten_teileuebersicht.png" /workspace/loeten_teileuebersicht.png 2>/dev/null || true
echo "geschrieben: ${OUT}loeten_teileuebersicht.png"
