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

## 09.11.2026 – Schritt 2: Waage (HX711) anschließen

- HX711 lag quer auf dem Steckbrett: Alle Pins einer Leiste steckten in derselben Reihe → Kurzschluss VCC–GND, CYD ging aus. Lösung: HX711 um 90° gedreht, jeder Pin in eigener Reihe.
- Danach meldet die Firmware weiterhin „HX711 antwortet nicht“. Ursache: keine Stiftleiste angelötet, die Kabel stecken lose in den Löchern → kein sicherer Kontakt.
- Nächster Schritt: Stiftleiste anlöten (Lötkolben besorgen), danach Waage testen und kalibrieren (`kalib`).
- Vorbereitet: WLAN-Zugangsdaten werden aus `secrets.h` gelesen (Vorlage `wokwi/secrets.example.h`, Datei ist in `.gitignore`). Ohne `secrets.h` bleibt „Wokwi-GUEST“ für die Simulation.
- **2026-11-09:** HX711 nach dem Löten erkannt (Rohwert 68194), reagiert auf Druck. Gramm-Anzeige noch falsch (Wokwi-Faktor). Kalibrierung mit neuen Serial-Befehlen `tara` / `eichen <gramm>` folgt.
- **2026-11-09:** Display ging aus, weil GPIO35 (Akku-ADC) offen floatete und die Firmware Unterspannung sah. Fix: `AKKU_ANGESCHLOSSEN=false` (Schutz/Warnungen aus, Anzeige „USB (kein Akku)“); unter 2,8 V gilt weiter „Messung offen“.

## 09.11.2026 – Schritt 3: Regensensor (LM393) testen

- Aufbau ohne Löten über CN1: 3V3 → VCC, GND → GND, IO27 → DO, AO frei; Sensorplatte mit 2 Kabeln am Modul (Plan: `fotos/schritt3_regensensor.png`).
- Testprogramm `tests/regensensor_test` liest IO27 (INPUT_PULLUP) alle 0,5 s und gibt „trocken“ / „NASS“ aus.
- Ergebnis: Power-LED an. Mit Wassertropfen auf der Platte geht die zweite LED am Modul an, und der ESP32 meldet „NASS“. **Test bestanden.**
- Im fertigen Gerät kommt DO an GPIO19 (SD-Slot, muss gelötet werden).

## 09.11.2026 – Lötplan

Ein Bild pro Lötschritt, alle Pins und Werte aus `gehaeuse/ANLEITUNG.md` (Abschnitt 7c) und `wokwi/README.md` (Pin-Tabelle):

1. `fotos/loeten/loeten_1_hx711.png` – HX711: Stiftleisten, Wägezelle (Rot E+, Schwarz E−, Weiß A−, Grün A+), CN1 (VCC 3V3, SCK IO22, DT IO27, GND)
2. `fotos/loeten/loeten_2_sd_slot.png` – microSD-Slot: Pin 5 CLK = GPIO18 (FET), Pin 3 CMD/MOSI = GPIO23 (LED-DIN), Pin 7 DAT0/MISO = GPIO19 (Regensensor)
3. `fotos/loeten/loeten_3_akku_lader.png` – Akku an TC4056 B+/B−, OUT+/OUT− weiter
4. `fotos/loeten/loeten_4_stromweg.png` – TC4056 → Q2 + Ein/Aus-Schalter → Pololu S13V10F5 → CYD und FET-Platine, Akku-Teiler 2 × 10 kΩ an GPIO35
5. `fotos/loeten/loeten_5_fet_platine.png` – FET-Platine H1: Q1 AO3401A, BC547B, 10 kΩ, 4,7 kΩ, 47 kΩ, Elko 470 µF/25 V
6. `fotos/loeten/loeten_6_led_regensensor.png` – LED-Streifen (470 Ω in DIN) und Regensensor (DO an GPIO19)

Laut Doku noch offen: an welchem CYD-Anschluss die 5 V vom Pololu ankommen und wo der Regensensor seine 3,3 V abgreift.

### Bestückungsplan FET-Platine (Lochraster 3 × 7 cm)

- `fotos/loeten/loeten_5b_lochraster_layout.png` – Bauteilseite: Q1/Q2 (AO3401A auf SOT-23-Adapter, Reihe B–E), T1 BC547B, R1 10 kΩ, R2 4,7 kΩ, R3/R4 47 kΩ (stehend), Elko C1 liegend (+ H04, − J04), Anschlusspunkte 1–10
- `fotos/loeten/loeten_5b_lochraster_unterseite.png` – Lötseite gespiegelt: Lötbrücken, 2 isolierte Drähte (B03 → F01 LED +, B08 → F05 VIN), Prüfliste
- Die 3 × 7-cm-Platine hat 10 Spalten (01–10) × 24 Reihen (A–X). Benutzt werden Reihe B–J (10 × 9 Löcher); durch Lochreihe A und K schneiden ergibt ca. 30 × 24,5 mm wie im Gehäuse (`mos_w`/`mos_l`). Der Kommentar „10 x 12 Loecher“ im .scad passt nicht zu diesem Raster (auf 30 mm liegen nur 10 Löcher).
- Annahme Adapter: AO3401A mittig auf der 0,95-mm-Seite (G/S auf Pad 2/4, D auf dem mittleren Pad gegenüber) → G/S/D an Stift 2/4/8. Vor dem Einlöten mit dem Multimeter prüfen.
- Akku-Teiler 2 × 10 kΩ (GPIO35) passt nicht mehr auf die Platine (im Gehäusemodell auch nur 4 Widerstände) und wird frei verdrahtet wie in Schritt 4.
- `fotos/loeten/loeten_5c_fet_3d_oben.png` / `loeten_5c_fet_3d_unten.png` – 3D-Ansicht (Blender) der fertig bestückten FET-Platine nach diesem Plan, nur zum Verstehen (kein Druckteil)

## 09.11.2026 – WLAN und Uhrzeit

- WLAN-Zugangsdaten in der gitignorierten `secrets.h` eingetragen (nicht im Repo), Firmware hochgeladen.
- CYD verbindet sich mit dem WLAN und holt die Uhrzeit per NTP (pool.ntp.org). Danach wird das WLAN zum Stromsparen wieder abgeschaltet.
- Beim ersten Abgleich nach dem Start kam innerhalb von 10 s keine NTP-Antwort (Ersatzuhr gelb), mit dem Befehl `sync` klappte es sofort.
- Wägezelle war bei diesem Test abgesteckt (Rohwert 0), Eichung folgt.

## 09.11.2026 – Probemontage Gehäuse: Pad-Löcher versetzt

- Problem beim Zusammenbau: Wägezelle von unten mit M5 im Boden festgeschraubt, Pad von oben mit M4 angeschraubt, Deckel drauf. Die Pad-Löcher passten nur, wenn man das Pad zur Seite schiebt. Dann lag das Pad auf der Display-Seite auf dem Deckelrand auf, auf der anderen Seite war ein breiter Spalt (HX711 sichtbar). So misst die Waage falsch.
- Gemessen: Mit dem Pad mittig in der Öffnung liegen die M4-Gewinde der Wägezelle ca. 3 mm neben den Pad-Löchern, Richtung Display/Regensensor (−X).
- Änderung im Modell (`gehaeuse/hydrodesk_base.scad`, Parameter `pad_hole_dx = -3` und `pad_hole_slot = 0,5`): Die zwei Pad-Löcher samt Senkung sind jetzt Langlöcher von X = 122,5 bis 126 mm (3,5 mm lang, zur Kerbe/Display-Seite hin). Die neue Lage passt, die alte bleibt nutzbar, ±1 mm Spielraum.
- Neu gedruckt werden muss **nur** `gehaeuse/stl/pad.stl`. Boden und Deckel bleiben unverändert. Vorschaubilder 13/14 sind neu gerendert.
