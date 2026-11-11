---
tags:
  - typ/software
---

# Stromsparmodus

Umgesetzt in der [[Firmware]] **Version 4**, beschrieben im Stromsparplan (`doku/Stromsparplan_HydroDesk.md`) und in der [[Wokwi]]-Anleitung (Kapitel 18).

- Display: nach **30 s** gedimmt, nach **2 min** aus (Zustand RUHE); nachts (22–7 Uhr) schon nach **15 s** aus. Die erste Berührung weckt nur, sie löst keine Taste aus.
- In RUHE schläft der ESP32 per `esp_light_sleep_start()`; die [[Wägezelle]] wird weiter 10-mal pro Sekunde gelesen.
- [[Bluetooth LE]] nur in kurzen Fenstern, [[WLAN und NTP|WLAN]] nur zum Uhr-Abgleich.
- CPU auf **80 MHz**.
- Der [[COB-LED-Streifen]] bekommt nur Strom, wenn er leuchtet ([[FET-Platine]]).
- [[Akku]]-Schutz bei 3,30 V.

Geschätzte Laufzeit im 24-h-Tag: ca. **27–54 h** (vorher ohne diese Maßnahmen ca. 6–12 h). Die Werte sind **noch nicht gemessen** – siehe [[Offen]]. Mit `stromsparen 0` verhält sich das Gerät wie Version 3 (zum Vergleich).

Siehe auch: [[Ein-Aus-Schalter]], [[Pololu-Wandler]].
