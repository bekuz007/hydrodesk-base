# Bautagebuch – HydroDesk Base

## 09.11.2026 – Test LED-Streifen ✅

**Ziel:** Prüfen, ob der BTF-LIGHTING COB-Streifen (WS2812B, 1 m, 160 LEDs) mit dem CYD funktioniert.

**Aufbau (provisorisch, ohne 5-V-Wandler):**

| LED-Streifen | CYD-Stecker CN1 |
|---|---|
| Rot (5 V) | Rot (3V3) |
| Weiß (GND) | Schwarz (GND) |
| Grün (DIN) | Gelb (IO27) |

**Software:** PlatformIO in VS Code, Bibliothek FastLED, Testcode in `tests/led_test/`. Farbwechsel Rot, Grün, Blau alle 0,5 s.

**Ablauf und Ergebnis:**
1. Test mit den ersten 10 LEDs, Helligkeit 30/255: alle 10 LEDs leuchten in allen drei Farben.
2. Test mit dem ganzen Streifen (160 LEDs), Helligkeit 10/255: der ganze Streifen leuchtet bis zum Ende.

**Hinweis:** Im Test lief der Streifen nur mit 3,3 V vom CYD, deshalb gedimmt. Im fertigen Gerät bekommt er 5 V über den Pololu-Wandler.

## 09.11.2026 – Erste Firmware auf dem echten CYD ✅

**Ziel:** Die HydroDesk-Firmware (bisher nur in der Wokwi-Simulation) auf das echte CYD laden.

**Vorgehen:** PlatformIO-Projekt `firmware/platformio.ini` angelegt, das den Sketch `wokwi/sketch.ino` mit `HYDRO_CYD=1` (TFT_eSPI + XPT2046-Touch) und `HYDRO_BLE=1` (NimBLE) baut. Partition „Huge APP“. Speicher: RAM 18 %, Flash 41,6 %.

**Probleme und Lösungen:**
1. Die XPT2046-Bibliothek aus der PlatformIO-Registry kennt `begin(SPIClass&)` nicht → GitHub-Version eingebunden.
2. Die aktuelle pioarduino-Plattform „stable“ läuft nicht mit der installierten PlatformIO-Version → feste Version 53.03.13 (Arduino-Kern 3.1.3).
3. Ohne Akku misst der Akku-Eingang ca. 0,5–0,6 V. Die Firmware hat das als „Akku leer“ gewertet und wollte nach 60 s abschalten → neu: unter 2,0 V gilt „kein Akku angeschlossen“, dann kein Akku-Schutz (`AKKU_FEHLT_V`).

**Ergebnis (serieller Monitor):** Display und Touch bereit, Bluetooth „HydroDesk“ sucht, Zustand IDLE, nach 70 s keine Abschaltung. Erwartet und noch offen: „HX711 antwortet nicht“ (Waage noch nicht angeschlossen), kein WLAN (noch keine Zugangsdaten), LED-Streifen bleibt dunkel (die Firmware nutzt GPIO23, der Streifen hängt zum Testen noch an IO27).
