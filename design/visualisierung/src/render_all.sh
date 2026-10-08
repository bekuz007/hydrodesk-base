#!/bin/bash
# Rendert alle Visualisierungen (Blender 4.5 LTS, Cycles CPU) und beschriftet sie (PIL)
cd "$(dirname "$0")"
B=${BLENDER:-/opt/blender-dl/blender-4.5.14-linux-x64/blender}
SAMPLES=${SAMPLES:-128}
mkdir -p ../raw
python3 textures.py
for m in explosion innen teile produkt; do
  start=$(date +%s)
  $B -b -P scene.py -- $m "$(pwd)/../raw/$m.png" $SAMPLES 100 > ../raw/$m.log 2>&1
  echo "$m exit=$? $(( $(date +%s) - start ))s"
done
python3 final.py ../raw/ ../
