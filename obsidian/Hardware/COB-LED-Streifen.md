---
tags:
  - typ/hardware
---

# COB-LED-Streifen

**BTF-LIGHTING WS2812B FCOB**, 5 V, 5 mm breit, 160 LEDs/m (Amazon, 16,99 € je 1 m). Gebraucht werden **26 LEDs** (13 Segmente à 12,5 mm = 162,5 mm). Der Streifen klebt an der Rückwand der Lichtkammer in der [[Bodenwanne]], davor sitzt die [[Diffusor-Leiste]].

Farben der [[Firmware]]:

- blau = trinken (Erinnerung)
- grün = Ziel erreicht
- rot = Akku niedrig oder Fehler
- weiß blinkend = Bluetooth-Suche, zweimal lila = verbunden

Seit Version 4 bekommt der Streifen nur Strom, wenn er leuchtet ([[FET-Platine]], Q1 an GPIO18). Bei Wasser bleibt er dunkel. In die Datenleitung gehört ein Widerstand **470 Ω** direkt am Eingang (DIN). Die Firmware nutzt GPIO23 als Datenleitung.

**Test am 09.11.2026:** Die ersten 10 LEDs und der ganze Meter leuchteten (provisorisch mit 3,3 V vom [[CYD ESP32-Display]], deshalb gedimmt). Im fertigen Gerät kommen 5 V vom [[Pololu-Wandler]] über den FET.

Siehe auch: [[Vorkalkulation]], [[Bautagebuch]].
