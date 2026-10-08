#!/bin/bash
# Rendert alle Vorschaubilder (benoetigt openscad + xvfb-run)
cd "$(dirname "$0")"
S=hydrodesk_base.scad; P=preview; SZ=1600,1100
r(){ xvfb-run -a openscad -D "part=\"$1\"" --imgsize=$SZ --colorscheme=Tomorrow $3 -o $P/$2.png $S >/dev/null 2>&1; echo "$2 $?"; }
r assembly 01_zusammenbau_iso      "--camera=90,50,10,55,0,25,420"
r exploded 02_explosionsansicht    "--camera=90,50,40,62,0,25,560"
r assembly 03_draufsicht           "--camera=90,50,0,0,0,0,330 --projection=o"
r inside   04_innen_ohne_deckel    "--camera=90,50,0,45,0,20,400"
r inside   05_innen_draufsicht     "--camera=90,50,0,0,0,0,330 --projection=o"
r assembly 06_rueckseite_usb       "--camera=90,50,10,70,0,200,380"
r assembly 07_front_led            "--camera=90,50,10,75,0,10,380"
r section  08_schnitt              "--camera=0,50,30,90,0,270,170 --projection=o"
r base     10_teil_base            "--render --camera=90,50,0,50,0,30,420"
r base     11_teil_base_unterseite "--render --camera=90,50,0,130,0,20,420"
r cover    12_teil_cover_druckLage "--render --camera=90,-50,0,50,0,30,420"
r pad      13_teil_pad_oben        "--render --camera=126,50,0,55,0,30,250"
r pad      14_teil_pad_unterseite  "--render --camera=126,50,0,130,0,30,250"
r assembly kappe_eingesteckt       "--camera=29,100,15,72,0,205,140"
r assembly kappe_offen             "--camera=29,104,15,72,0,205,160 -D cap_pull=14"
r cap      15_teil_kappe_druckLage "--render --camera=0,0,1.5,50,0,25,75"
r cap_check_base 16_kappe_quetschrippen "--render --camera=29,98.8,17,72,0,205,90"
