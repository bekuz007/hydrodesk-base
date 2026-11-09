#!/bin/bash
# Rendert alle 5 Ansichten (Cycles, 112 Samples + Denoiser) und speichert .blend/.glb
B=${BLENDER:-blender}; S=${1:-112}; cd "$(dirname "$0")/src"
for v in "a_offen offen" "b_iso iso" "c_explosion explosion" "d_detail_sd_fet detail" "e_produkt produkt"; do
  set -- $v; $B -b -P real_scene.py -- $2 ../hydrodesk_real_$1.png $S 100 || exit 1
done
$B -b -P real_scene.py -- save ../../../3d_modell/realistisch/hydrodesk_realistisch.blend,../../../3d_modell/realistisch/hydrodesk_realistisch.glb
