---
tags:
  - typ/software
---

# Firmware

Dieselbe Quelle wie die [[Wokwi]]-Simulation (`wokwi/sketch.ino`). [[VS Code und PlatformIO]] in `firmware/` baut sie mit `HYDRO_CYD=1` und `HYDRO_BLE=1` für das [[CYD ESP32-Display]]. Partition **Huge APP** (sonst ist WLAN + NimBLE + Display + Waage zu groß). Seit dem **09.11.2026** läuft sie auf dem echten Display.

Wichtige Teile:

- [[Wägezelle]] über [[HX711]] (Tara, [[Kalibrierung]], Gewicht → ml)
- Touch-Oberfläche (ILI9341, 240 × 320): Presets, Tagesziel, Fortschritt, Tasten „Leer“ und „Voll“
- [[COB-LED-Streifen]] (26 LEDs) und Nässe-Erkennung über den [[Regensensor LM393]]
- [[Bluetooth LE]], [[WLAN und NTP]], [[Stromsparmodus]] (Version 4)
- optionale Telegram-Befehle `/status`, `/ziel`, `/hilfe`

WLAN-Daten gehören in die gitignorierte Datei `firmware/secrets.h` (Vorlage `secrets.example.h`), niemals ins Repository.

Siehe auch: [[HydroDesk Base]], [[Bautagebuch]], [[GitHub]].
