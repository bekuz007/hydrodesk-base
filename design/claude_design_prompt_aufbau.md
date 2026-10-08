# Claude Design Prompt – Aufbau & Einzelteile (HydroDesk Base)

Diesen Block komplett in Claude Design einfügen.

```
Create a technical product presentation (multiple boards/pages) that explains HOW the device "HydroDesk Base" is built and assembled. Style: clean technical illustration like an IKEA/Apple teardown manual, light grey background, isometric and top views, every part labeled with a thin leader line. All labels and texts in GERMAN.

HARD RULES (do not break):
- The housing is a RECTANGLE, landscape: 180 mm wide × 100 mm deep × 25 mm high, corner radius 8 mm. NOT round, NOT square.
- The touch display is on the LEFT side, portrait orientation.
- The bottle pad (90 × 90 mm, blue) is on the RIGHT side, next to the display. The bottle stands on the pad, never on the display.
- No bottle is part of the product. Show any generic bottle only as a transparent ghost on the pad.

TOP VIEW LAYOUT:
+----------------------------------------------------------+
|  [ DISPLAY  ]  |  middle  |  [                       ]   |
|  [ portrait ]  |  strip   |  [   BOTTLE PAD 90x90    ]   |
|  [  ~80 mm  ]  |          |  [   (blue, floating)    ]   |
|  [   zone   ]  |          |  [                       ]   |
+----------------------------------------------------------+
|  LED strip groove along the whole FRONT edge (10 LEDs)   |
USB openings are on the BACK edge (left half): the wide programming opening of the display board is closed by a small removable plug-in cap, the USB-C charging opening stays open.

PARTS (show each one separately on a "Teileübersicht" board, with name, size and one-line function):
1. Unterschale (base): 3D-printed PLA tub, 180×100×23 mm, internal standoffs, pockets for all modules, 4 rubber-feet recesses underneath.
2. Deckel (cover): thin 5 mm frame, display window on the left, large opening on the right for the pad, 8 countersunk M3 screws.
3. Flaschenplatte (pad): 90×90×7 mm, blue, small drip rim, rests ONLY on the load cell (1 mm gap all around, it floats).
4. Silikonmatte: 86×86 mm, dark grey, glued on top of the pad.
5. ESP32-Touch-Display-Board ("Cheap Yellow Display", 2.8", 50×86 mm, yellow PCB, screen on top): brain + touchscreen in one, mounted portrait on 4 standoffs in the LEFT zone, USB end facing the back.
6. LiPo-Akku 3.7 V 2000 mAh (34×55×10 mm): lies UNDER the display board.
7. 5V-Step-up-Wandler (37×17 mm): next to the battery under the display.
8. TC4056 USB-C-Lademodul (26×17 mm): middle strip, against the back wall at the USB-C opening.
9. FET-Schaltmodul (30×17 mm): middle strip, in front of the charger – cuts the power when water is detected.
10. Regensensor (LM393 comparator board + sensor plate 40×54 mm): sensor plate in a floor pocket under a 3 mm slit next to the pad; overflow from the pad's drip notch drips onto it.
11. Wägezelle 5 kg (aluminium bar 80×12.7×12.7 mm, silver): centred under the pad, fixed at the BACK end to the base (2× M5 from below), the pad is screwed to the FRONT free end (2× M4) – cantilever, so it can bend.
12. HX711 (34×21 mm, green): next to the load cell under the pad.
13. WS2812-LED-Leiste (10 LEDs, 167 mm): glued into the groove along the front edge.
14. Gummifüße ×4, Schrauben (8× M3×12, 2× M5×12, 2× M4×10).
15. Abdeckkappe USB (cap): small 3D-printed PLA plug-in cap, 35×10.6×3.4 mm, same colour as the housing, pressed into the wide USB opening at the back (covers the display board's programming port), pull notch at the bottom.

BOARDS TO CREATE:
A) "Produkt" – hero isometric of the closed device: display on the left showing "1.250 / 2.000 ml" with a progress bar, ghost bottle on the right pad, LED strip glowing blue.
B) "Teileübersicht" – all 15 parts laid out flat, labeled, roughly to scale.
C) "Explosionsansicht" – vertical exploded view in this order from bottom to top: Gummifüße → Unterschale → Akku + Step-up → Display-Board / Wägezelle + HX711 / Lademodul + FET + Regensensor → Flaschenplatte → Silikonmatte → Deckel. Dashed lines show where each part goes.
D) "Innenansicht" – top view of the open base WITHOUT cover: where every module sits (color code: display yellow, load cell silver, HX711 green, charger blue, FET red, rain sensor teal, battery dark grey), cable paths as thin colored lines.
E) "Aufbau in 6 Schritten" – six numbered small isometric panels:
   1. Gummifüße unten aufkleben
   2. Wägezelle hinten mit 2× M5 an der Unterschale festschrauben, HX711 daneben
   3. Akku, Step-up, Lademodul, FET-Modul und Regensensor einsetzen
   4. Display-Board auf die Abstandshalter links legen, Kabel anstecken
   5. Flaschenplatte vorne mit 2× M4 auf die Wägezelle schrauben, Silikonmatte aufkleben, LED-Leiste vorne einkleben
   6. Deckel auflegen und mit 8× M3 verschrauben (4 Schrauben halten gleichzeitig das Display-Board), Abdeckkappe hinten einstecken
F) "Schnitt" – side cross-section through the pad showing: floor → load cell (fixed back, free front) → pad floating with 1 mm gap → silicone mat; and through the display zone: battery under the display board under the cover window.
G) "Verkabelung" – simple block diagram: ESP32-Display-Board in the centre, connected to HX711 (→ Wägezelle), WS2812 LED-Leiste, Regensensor, FET-Schaltmodul (→ Stromversorgung), Akku → TC4056 → Step-up → Board. Use arrows and short German labels.
H) "Bedienung" – three display screens in portrait: (1) Flaschengröße wählen: Leer / 300 / 500 / 750 / 1000 / 1500 ml / Voll; (2) Tagesfortschritt with ml and goal; (3) red warning screen "WASSER ERKANNT · STROM AUS". Plus an LED color legend: blau = trinken, grün = Ziel erreicht, rot = Akku/Fehler, amber = Wasser erkannt.

SELF-CHECK before finishing: Is the body a 180×100 rectangle? Is the display on the LEFT? Is the pad on the RIGHT next to it? Is the load cell under the pad only? Are all labels German? If any answer is no, fix it.
```

Korrektur-Satz, falls es wieder rund wird:
`Wrong: the body must be a 180 × 100 mm rectangle, display LEFT, bottle pad RIGHT – redo all boards.`
