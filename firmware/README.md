# Firmware

> **Folgt.** Die Firmware wird mit **PlatformIO** (Arduino-Framework) für das ESP32-2432S028R
> („Cheap Yellow Display“) entwickelt.

Geplante Module:

* Wägezelle über HX711 (Tara, Kalibrierung, Umrechnung Gewicht → ml)
* Touch-Oberfläche (ILI9341, 320 × 240): Presets Leer / 300 / 500 / 750 / 1000 / 1500 ml / Voll, Tagesziel, Fortschritt
* WS2812-LED-Leiste (blau = trinken, grün = Ziel, rot = Akku/Fehler, amber = Wasser)
* Nässe-Erkennung (Regensensor) → FET-Modul schaltet Strom ab, Sperrbildschirm „WASSER ERKANNT · STROM AUS“
* WLAN/NTP, optional Telegram-Bot (`/status`, `/ziel`, `/hilfe`)
* Bluetooth Low Energy (BLE): Gerät „HydroDesk“, Status-Symbol neben dem Akku, LEDs weiß blinkend
  beim Suchen und 2× lila beim Verbinden (Logik schon fertig in [`../wokwi/sketch.ino`](../wokwi/sketch.ino), Version 3)

## Bluetooth (BLE) – Hinweise für die echte Firmware

Stand aus der Wokwi-Simulation V3 (dort hinter dem Schalter `#define HYDRO_BLE 1`):

* **Bibliothek:** [NimBLE-Arduino](https://github.com/h2zero/NimBLE-Arduino) (getestet 2.5.1 mit
  Arduino-ESP32-Kern 3.3.12). PlatformIO: `lib_deps = h2zero/NimBLE-Arduino@^2.5.1`.
  Die eingebaute Bluedroid-BLE-Bibliothek ist zu groß (schon ein Minimal-Test mit WLAN + BLE:
  1,62 MB = 123 % der Standard-App-Partition).
* **Partition:** WLAN + NimBLE + Display + Waage belegt **96 %** der Standard-Partition
  (1,25 MB App). Für Reserve (Telegram/TLS) die Partition **Huge APP** nehmen (dann 40 %):
  * PlatformIO: `board_build.partitions = huge_app.csv`
  * Arduino-IDE: *Werkzeuge → Partition Scheme → Huge APP (3MB No OTA/1MB SPIFFS)*
  * Mit OTA-Updates: `min_spiffs.csv` (1,9 MB App)
* **GATT:** Dienst `4f9a0001-6c1e-4b8e-9d6a-2b7c1e0a4d10`, Characteristic
  `4f9a0002-6c1e-4b8e-9d6a-2b7c1e0a4d10` (lesen + notify, Text „heute/Ziel ml“, z. B. `1250/2750 ml`).
* **Ablauf:** Beim Start 2 min Advertising (`BT_SUCH_TIMEOUT_MS`), danach Stopp („nicht verbunden“).
  Bei Trennung wird die Suche neu gestartet. Die Callbacks setzen nur einen Merker, ausgewertet wird
  im `loop()`.
* **Noch auf echter Hardware zu testen:** Verbinden mit Handy (z. B. nRF Connect), Notify, WLAN +
  BLE gleichzeitig (Coexistence), Stromverbrauch.

## Zugangsdaten

Zugangsdaten gehören **niemals** ins Repository.
`secrets.example.h` nach `secrets.h` kopieren und dort die echten Werte eintragen –
`secrets.h` ist per `.gitignore` ausgeschlossen.

```bash
cp secrets.example.h secrets.h
```
