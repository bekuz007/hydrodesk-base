---
tags:
  - typ/software
---

# Kalibrierung

Die [[Firmware]] rechnet das Gewicht der Flasche in Milliliter um (**1 g ≈ 1 ml**). Auf dem Touch-Display (und im Kalibrier-Bildschirm) gibt es die Tasten **„Leer“** und **„Voll“**:

1. Leere Flasche auf das [[Flaschen-Pad]] stellen und **Leer** tippen (Gewicht ca. 1 s ruhig).
2. Volle Flasche aufstellen und **Voll** tippen.
3. Inhalt = aktuelles Gewicht − Leergewicht. Anzeige „Flasche x/y ml“.

Fehler (kein Leer, Voll ≤ Leer, unruhige Waage) erscheinen auf Deutsch auf dem Display. Die Werte liegen in den Preferences. Über die serielle Schnittstelle gibt es außerdem `kalib`, `leer`, `voll` sowie `tara` und `eichen <gramm>`.

**Stand:** Der [[HX711]] liefert Rohwerte und reagiert auf Druck, aber die Gramm-Anzeige benutzt noch den Wokwi-Faktor. Die Eichung mit einem bekannten Gewicht ist noch [[Offen]].

Siehe auch: [[Wägezelle]], [[Wokwi]].
