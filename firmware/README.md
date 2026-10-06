# Firmware

> **Folgt.** Die Firmware wird mit **PlatformIO** (Arduino-Framework) für das ESP32-2432S028R
> („Cheap Yellow Display“) entwickelt.

Geplante Module:

* Wägezelle über HX711 (Tara, Kalibrierung, Umrechnung Gewicht → ml)
* Touch-Oberfläche (ILI9341, 320 × 240): Presets Leer / 300 / 500 / 750 / 1000 / 1500 ml / Voll, Tagesziel, Fortschritt
* WS2812-LED-Leiste (blau = trinken, grün = Ziel, rot = Akku/Fehler, amber = Wasser)
* Nässe-Erkennung (Regensensor) → FET-Modul schaltet Strom ab, Sperrbildschirm „WASSER ERKANNT · STROM AUS“
* WLAN/NTP, optional Telegram-Bot (`/status`, `/ziel`, `/hilfe`)

## Zugangsdaten

Zugangsdaten gehören **niemals** ins Repository.
`secrets.example.h` nach `secrets.h` kopieren und dort die echten Werte eintragen –
`secrets.h` ist per `.gitignore` ausgeschlossen.

```bash
cp secrets.example.h secrets.h
```
