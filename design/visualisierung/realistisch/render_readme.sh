#!/bin/bash
# Rendert die 4 Bilder fuer das Haupt-README (Produkt, Explosion, Innen, Teile) aus dem realistischen Modell
# und beschriftet sie (deutsche Texte, Hinweislinien). Ergebnis: ../hydrodesk_{produkt,explosion,innen,teile}.png
# Aufruf: render_readme.sh [Samples]   (Standard 128; braucht Blender 4.5 mit Cycles, Pfad ueber BLENDER=... setzen)
B=${BLENDER:-/opt/blender-dl/blender-4.5.4-linux-x64/blender}; S=${1:-128}
cd "$(dirname "$0")/src"; mkdir -p ../raw
for v in produkt explosion innen teile; do
  $B -b -P real_scene.py -- v_$v "$(pwd)/../raw/$v.png" $S 100 > ../raw/$v.log 2>&1 || { echo "Fehler bei $v, siehe raw/$v.log"; exit 1; }
  echo "$v fertig"
done
python3 real_final.py ../raw/ ../../
