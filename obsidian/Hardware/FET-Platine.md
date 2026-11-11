---
tags:
  - typ/hardware
---

# FET-Platine

Selbst gelötete Lochrasterplatine **30 × 24,5 mm** (Version 4). Darauf sitzen zwei P-Kanal-MOSFETs **AO3401A** (−30 V, −4 A, SOT-23, Reichelt, 0,34 € für 2 Stück):

- **Q1** schaltet die 5 V des [[COB-LED-Streifen|LED-Streifens]] (High-Side), angesteuert über einen BC547B an GPIO18.
- **Q2** ist der Akku-Schalter zusammen mit dem [[Ein-Aus-Schalter]].

Weitere Teile: Widerstände 10 kΩ, 4,7 kΩ, 2 × 47 kΩ, Elko 470 µF / 25 V (liegt, zeigt nach rechts, weg vom Display). Die Platine liegt auf zwei Leisten im Mittelstreifen, direkt vor dem [[TC4056-Lader]].

Das früher geplante fertige GERUI-FET-Modul (Low-Side, 6,49 €) ist **gestrichen**. Bestückungsplan und 3-D-Ansichten (aus [[Blender]]) stehen im [[Bautagebuch]] und in der [[Anleitung]] (Kapitel 7b/7c).

Siehe auch: [[Vorkalkulation]], [[Regensensor LM393]].
