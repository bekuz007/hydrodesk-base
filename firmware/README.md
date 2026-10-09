# Firmware

> **Folgt.** Die Firmware wird mit **PlatformIO** (Arduino-Framework) für das ESP32-2432S028R
> („Cheap Yellow Display“) entwickelt.

Geplante Module:

* Wägezelle über HX711 (Tara, Kalibrierung, Umrechnung Gewicht → ml)
* Touch-Oberfläche (ILI9341, 320 × 240): Presets Leer / 300 / 500 / 750 / 1000 / 1500 ml / Voll, Tagesziel, Fortschritt
* COB-LED-Streifen WS2812B (26 LEDs) hinter der gedruckten Diffusor-Leiste (blau = trinken, grün = Ziel, rot = Akku/Fehler).
  Seit V4 bekommt der Streifen nur Strom, wenn er leuchtet (P-MOSFET AO3401A an GPIO18), bei Wasser ist er dunkel
* Nässe-Erkennung (Regensensor) → LED-Strom-FET aus, Sperrbildschirm „WASSER ERKANNT · STROM AUS“
* WLAN/NTP (V4: nur kurz zum Uhr-Abgleich), optional Telegram-Bot (`/status`, `/ziel`, `/hilfe`)
* Bluetooth Low Energy (BLE): Gerät „HydroDesk“, Status-Symbol neben dem Akku, LEDs weiß blinkend
  beim Suchen und 2× lila beim Verbinden (Logik schon fertig in [`../wokwi/sketch.ino`](../wokwi/sketch.ino), Version 4)
* Stromsparmodus (V4): Display dimmen/aus, Light-Sleep, Bluetooth in Fenstern, Akku-Schutz (siehe unten)

## Bluetooth (BLE) – Hinweise für die echte Firmware

Stand aus der Wokwi-Simulation V4 (dort hinter dem Schalter `#define HYDRO_BLE 1`):

* **Bibliothek:** [NimBLE-Arduino](https://github.com/h2zero/NimBLE-Arduino) (getestet 2.5.1 mit
  Arduino-ESP32-Kern 3.3.12). PlatformIO: `lib_deps = h2zero/NimBLE-Arduino@^2.5.1`.
  Die eingebaute Bluedroid-BLE-Bibliothek ist zu groß (schon ein Minimal-Test mit WLAN + BLE:
  1,62 MB = 123 % der Standard-App-Partition).
* **Partition (Pflicht seit V4):** WLAN + NimBLE + Display + Waage + Stromsparen ist **682 Byte
  zu groß** für die Standard-Partition (1 311 402 B von 1 310 720 B). Darum die Partition
  **Huge APP** nehmen (dann 41 %):
  * PlatformIO: `board_build.partitions = huge_app.csv`
  * Arduino-IDE: *Werkzeuge → Partition Scheme → Huge APP (3MB No OTA/1MB SPIFFS)*
  * Mit OTA-Updates: `min_spiffs.csv` (1,9 MB App)
* **GATT:** Dienst `4f9a0001-6c1e-4b8e-9d6a-2b7c1e0a4d10`, Characteristic
  `4f9a0002-6c1e-4b8e-9d6a-2b7c1e0a4d10` (lesen + notify, Text „heute/Ziel ml“, z. B. `1250/2750 ml`).
* **Ablauf (V4, Option A):** Bluetooth ist nur in **Fenstern** sichtbar: beim Start 2 min
  (`BT_SUCH_TIMEOUT_MS`), nach **Antippen des Bluetooth-Symbols** 2 min und **60 s still** nach jedem
  erkannten Trinken/Nachfüllen (`BT_SYNC_FENSTER_MS`). Bei Trennung startet ein Fenster derselben
  Art. Danach Werbung aus und **`NimBLEDevice::deinit(true)`**; das nächste Fenster legt Server,
  Dienst und Werbung neu an (nach `deinit(false)` registriert NimBLE 2.5.1 den GATT-Dienst nicht neu).
  Die Callbacks setzen nur einen Merker, ausgewertet wird im `loop()`.
  **Für die App:** verbinden, sobald „HydroDesk“ in der Werbung auftaucht, Wert lesen, wieder trennen.
* **Noch auf echter Hardware zu testen:** Verbinden mit Handy (z. B. nRF Connect), Notify, WLAN +
  BLE gleichzeitig (Coexistence), 20× `deinit`/`init` im Wechsel, Stromverbrauch.

## Stromsparen (V4) – Hinweise für die echte Firmware

Vollständig beschrieben in [`../wokwi/README.md`](../wokwi/README.md), Kapitel 18, und im
Stromsparplan (`doku/Stromsparplan_HydroDesk.md`). Kurz:

* **Kein automatischer Light-Sleep:** Der Arduino-Kern 3.3.12 ist ohne `CONFIG_PM_ENABLE` gebaut.
  Der Sketch schläft darum **von Hand** (`esp_light_sleep_start()`), nur in RUHE und nur mit
  `HYDRO_CYD 1` (`HYDRO_LIGHTSLEEP`). Vorher sind WLAN und BLE aus. Wecken: Timer bis zur nächsten
  Waagen-Messung (≤ 100 ms, die Waage misst weiter 10×/s), GPIO19 LOW (Nässe), GPIO36 LOW (Touch).
* **Pins im Schlaf:** GPIO18 (LED-Strom-FET), 21 (Licht), 22 (HX711-SCK), 23 (DIN) werden mit
  `gpio_hold_en()` gehalten (`RUHE_PINS_HALTEN`), nach dem Wecken freigegeben.
* **Display:** Licht per LEDC-PWM an GPIO21 (255 / 40 / 0), in RUHE `DISPOFF` + `SLPIN`.
* **Touch:** Die XPT2046-Bibliothek läuft **ohne** IRQ-Pin (`XPT2046_Touchscreen touch(33)`). Der
  Sketch liest GPIO36 selbst (HIGH = sicher nicht berührt) und bestätigt per Druckmessung (Errata
  GPIO36). Die erste Berührung im gedimmten/dunklen Zustand weckt nur.
* **WLAN:** nur zum Uhr-Abgleich (Start, alle 6 h, Befehl `sync`, Timeout 20 s), Abweichung im Protokoll.
  Telegram später: kurz verbinden, senden, wieder aus.
* **CPU:** 80 MHz (`setCpuFrequencyMhz(80)`).
* **Akku:** Prozent per LiPo-Tabelle (typische Kurve, nach eigener Entlademessung ersetzen),
  Schutz: 60 s unter 3,30 V → Meldung → Tiefschlaf (15-min-Timer), Neustart erst ab 3,60 V.
* **Hardware dazu:** LED-Strom-Schalter (AO3401A + BC547B an GPIO18) und Ein/Aus-Schalter in der
  Akku-Leitung, siehe `../gehaeuse/ANLEITUNG.md`.
* `stromsparen 0` (Serial) bzw. `#define STROMSPAREN 0` = Verhalten wie V3 zum Vergleichen.

## Zugangsdaten

Zugangsdaten gehören **niemals** ins Repository.
`secrets.example.h` nach `secrets.h` kopieren und dort die echten Werte eintragen –
`secrets.h` ist per `.gitignore` ausgeschlossen.

```bash
cp secrets.example.h secrets.h
```
