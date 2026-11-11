---
tags:
  - typ/werkzeug
---

# Wokwi

Browservシミュレーション der Geräte-Logik auf [wokwi.com](https://wokwi.com), Ordner `wokwi/`. So lässt sich die [[Firmware]] testen, bevor alle Teile gekauft sind. Aktuell **Version 4** (inkl. [[Stromsparmodus]], Bluetooth-Symbol und LED-Status). Im README des Ordners steht, welche echten Teile durch Regler und Schalter nachgebildet werden.

Der Sketch ist derselbe wie auf dem echten [[CYD ESP32-Display]]. Unterschiede: kapazitiver Touch statt XPT2046, Gewicht per Schieberegler, Gast-WLAN „Wokwi-GUEST“. Alle Varianten kompiliert, PC-Logiktest in Ordnung; auf wokwi.com nachtesten.

Siehe auch: [[Kalibrierung]], [[Bluetooth LE]], [[VS Code und PlatformIO]].
