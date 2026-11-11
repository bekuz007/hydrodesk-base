---
tags:
  - typ/hardware
---

# Akku

**EEMB-LiPo 3,7 V, 2000 mAh** (LP103454), Amazon 10,99 €. Maße laut Anleitung: **34,5 × 56 × 10,3 mm**. Er liegt hinten links unter dem [[CYD ESP32-Display]], das Laden läuft über den [[TC4056-Lader]] (USB-C). Die 5 V für Display und LEDs erzeugt der [[Pololu-Wandler]]. Der [[Ein-Aus-Schalter]] (Q2 auf der [[FET-Platine]]) trennt den Akku wirklich; Laden geht in beiden Schalterstellungen.

Die [[Firmware]] rechnet den Füllstand über eine typische LiPo-Tabelle (nach eigener Entlademessung zu ersetzen). Schutz: 60 s unter **3,30 V** → Meldung → Tiefschlaf; Neustart erst ab **3,60 V**. Die geschätzte Laufzeit im 24-h-Tag liegt bei ca. **27–54 h** (noch nicht gemessen) – siehe [[Stromsparmodus]].

**Aktueller Aufbau:** Der Akku ist noch nicht fest eingelötet. In der Firmware steht `AKKU_ANGESCHLOSSEN=false` (Anzeige „USB (kein Akku)“), damit der Schutz beim Testen über USB nicht eingreift. Das Anlöten ist noch [[Offen]].

Siehe auch: [[Anleitung]], [[Vorkalkulation]].
