---
tags:
  - typ/hardware
---

# Pololu-Wandler

**Pololu S13V10F5**, 5 V / 1 A, Step-Up/Step-Down, bei Berrybase 9,95 €. Maße **12,1 × 8,9 × 4,2 mm**. Er liegt vorne unter dem [[CYD ESP32-Display]] in einem Fach 37 × 17 mm und wird mit Klebeband fixiert.

Er erzeugt die 5 V für das Display und – über Q1 auf der [[FET-Platine]] – für den [[COB-LED-Streifen]]. Laut Hersteller braucht er schon ohne Last ca. **9–10 mA** und hat **keinen Enable-Eingang**. Ein echtes „Aus“ geht deshalb nur mit dem [[Ein-Aus-Schalter]] in der Akku-Leitung, nicht per Software. Darum gibt es den Schalter in Version 4.

Siehe auch: [[Akku]], [[Stromsparmodus]], [[Anleitung]].
