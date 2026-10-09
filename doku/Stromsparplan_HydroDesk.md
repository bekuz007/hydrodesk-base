# HydroDesk Base – Stromsparplan (umgesetzt in Version 4)

Stand: 08.10.2026 · Grundlage: `wokwi/sketch.ino` (Version 3, identisch in `/workspace/HydroDesk/wokwi` und im Repo `hydrodesk-base/wokwi`), Arduino-ESP32-Kern 3.3.12, NimBLE-Arduino 2.5.1, XPT2046_Touchscreen 1.4, HX711 (Rob Tillaart) 0.6.5.

> **Status 09.10.2026: umgesetzt (V4).** Deine Entscheidung: Software-Stromsparmodus + H1 (LED-FET, High-Side) + H2 (Schiebeschalter). Firmware: Commit `9e66c64`, Gehäuse/Schaltung: Commit `71570e4`, Doku/Kosten: siehe Kapitel 11. Was gebaut wurde und **was noch gemessen werden muss**, steht in **Kapitel 11**. Die Kapitel 0–10 sind der ursprüngliche Plan (Stand 08.10.2026) und bleiben als Begründung stehen.
>
> **Hinweis zum Plan:** Alle Stromwerte ohne Quelle sind **Schätzungen**. Alle Stromwerte ohne Quelle sind **Schätzungen** und mit „(S)“ markiert. Werte mit Quelle sind mit [Nummer] belegt (Liste am Ende). Die echten Werte liefert erst die Messung am Gerät (Kapitel 9).

---

## 0. Kurzfassung

- **Heute** laufen Display (immer volle Helligkeit), WLAN (immer verbunden) und CPU (240 MHz, kein Schlaf) ununterbrochen. Neu und grob von unten gerechnet ergibt das **ca. 6 bis 12 h** Laufzeit (S).
  - Die früheren „3–4 h“ beruhten auf 0,25–0,35 A für das CYD. Das war der **Spitzenwert fürs Strombudget** des Wandlers (WLAN-Sendespitzen eingerechnet), nicht der Durchschnitt.
  - Der einzige veröffentlichte Gesamtwert für das CYD liegt bei **ca. 115 mA** [9][10], allerdings ohne Angabe der Bedingungen.
- **Plan (nur Software):**
  - 4 Energiezustände: AKTIV → GEDIMMT (nach 30 s) → RUHE (Display aus, nach 2 min), dazu eine optionale NACHT-Variante.
  - WLAN nur noch zum Uhr-Abgleich (beim Start, dann alle 6 h).
  - Bluetooth nur in kurzen Fenstern.
  - CPU auf 80 MHz.
  - In RUHE manueller Light-Sleep mit Aufwachen alle 100 ms, damit die Waage weiter 10× pro Sekunde gelesen wird und die Trink-Erkennung **unverändert** bleibt.
  - → **ca. 18–32 h** bei Dauernutzung am Schreibtisch, **ca. 20–36 h** im 24-h-Tag (S). Damit hält das Gerät sicher einen ganzen Tag. Laden etwa jede Nacht bis jeden zweiten Tag.
- **Plan + 1 Hardware-Änderung** (5 V des LED-Streifens per FET abschalten, solange er dunkel ist): **ca. 24–47 h** bei Dauernutzung bzw. **ca. 27–54 h** im 24-h-Tag (S).
- **Wichtigste Entdeckung:** Der Pololu S13V10F5 braucht laut Hersteller selbst bei 3,7 V Eingang schon **ca. 9–10 mA ohne Last** [6]. Er hat **keinen Enable-Eingang** [6]. Ein echtes „Aus“ ist per Software also unmöglich. Dafür braucht es einen **Schalter** (offene Entscheidung, Kapitel 7).

---

## 1. Ist-Analyse: Wer verbraucht Strom und wie steuert der Sketch ihn?

| # | Verbraucher | So steuert der Sketch ihn heute (Zeilen in `sketch.ino`) | Bewertung |
|---|---|---|---|
| 1 | **Hintergrundlicht** (GPIO21) | `pinMode(21, OUTPUT); digitalWrite(21, HIGH)` in `anzeigeInit()` (Z. 498–499). **Kein PWM**, wird **nie** gedimmt oder ausgeschaltet. | größter Einzelverbraucher (S) |
| 2 | **CPU** | Keine Einstellung im Sketch → Board-Standard „ESP32 Dev Module“ = **240 MHz** (`boards.txt`: `esp32.build.f_cpu=240000000L`). `loop()` endet mit `delay(5)` (Z. 2011), **kein Schlafmodus**. | |
| 3 | **Display-Neuzeichnen** | `drawUI()` höchstens 5× pro Sekunde (Z. 1776), zeichnet nur geänderte Bereiche (`geaendert()`, Z. 1476). Läuft immer, auch wenn niemand hinschaut. | wenig Strom, aber unnötig, solange das Display aus ist |
| 4 | **WLAN** | `uhrStarten()` (Z. 646–652): `WIFI_STA` + `WiFi.begin()`, wird **nie abgeschaltet**. Standard im Kern: Modem-Sleep `WIFI_PS_MIN_MODEM` (WiFiGeneric.cpp). SNTP gleicht alle **3 h** ab (`CONFIG_LWIP_SNTP_UPDATE_DELAY=10800000`). Ohne erreichbares WLAN versucht der Kern immer wieder neu zu verbinden (Auto-Reconnect). | dauerhafter Verbrauch, ohne WLAN noch höher (S) |
| 5 | **Bluetooth (NimBLE)** | Nur bei `HYDRO_BLE 1`: `bleStarten()` beim Start (Z. 1308–1329). 120 s Werbung (Advertising) beim Start und nach jeder Trennung (Z. 1347–1358, 1389–1394). **Danach bleibt der BLE-Stack eingeschaltet**, er wirbt nur nicht mehr. | blockiert Light-Sleep (Kap. 2) |
| 6 | **Waage HX711** | `waageLesen()` liest 10× pro Sekunde (Z. 788), sobald `is_ready()`. **Nie `power_down()`**. | laut Datenblatt < 1,5 mA [7] plus Speisestrom der Wägezelle (S) |
| 7 | **LED-Streifen (26 × WS2812-COB)** | Im Normalbetrieb schwarz (`setup()` Z. 1948–1951). Sendet nur bei Farbwechsel (Z. 1465). **Erinnerung = Dauer-Blau, bis getrunken wird** (Z. 1142–1147, 1457), das kann Stunden dauern. | auch „aus“ braucht jeder LED-Chip Ruhestrom: ca. 0,45–0,6 mA pro LED [8] |
| 8 | **Akku-Messung** (GPIO35) | `analogRead` alle 500 ms (Z. 966–969). Prozent **linear** 3,0–4,2 V (Z. 973–974), dadurch kommt die Warnung „unter 20 %“ erst bei ca. 3,24 V. Echt: Teiler aus 2 × 10 kΩ (Einkaufsliste Pos. 14) zieht dauerhaft ca. 0,19 mA aus dem Akku (3,7 V / 20 kΩ). | Prozentanzeige bei LiPo zu optimistisch (Kap. 5) |
| 9 | **Nässe-Sensor** (GPIO19) | `digitalRead` in jeder Schleife (Z. 951–964). Das Modul (Komparator + Power-LED) ist immer an. | ca. 1–4 mA (S) |
| 10 | **Touch XPT2046** | `XPT2046_Touchscreen touch(33, 36)`, IRQ an **GPIO36** (Z. 484). Die Bibliothek hängt einen FALLING-Interrupt an GPIO36 und schaltet den Chip nach jeder Messung wieder in Power-down **mit aktivem PENIRQ** (letzter Befehl `0xD0`, XPT2046_Touchscreen.cpp Z. 143). | Grundlage für „Touch weckt auf“ |
| 11 | **CYD-Platine selbst** | AMS1117-3,3-V-Regler (Ruhestrom 5 mA typ., 10 mA max [11]), CH340C (USB-Seriell), Verstärker SC8002B, LDR-Teiler, Logik von ILI9341 und XPT2046 [12]. Der Sketch beeinflusst sie nicht. | Grundlast ca. 8–20 mA (S), **muss gemessen werden** |
| 12 | **Pololu S13V10F5** | – | Ruhestrom ca. 8–13 mA bei 2,8–4,0 V Eingang (Herstellergrafik) [6], Wirkungsgrad bei 3,3–5 V Eingang und 0,1–0,3 A ca. 88–93 % [6] |

**Nebenbefund, ohne Stromsparen schon ein Fehler:** Nach den 2 min Suche gibt es am echten Gerät **keinen Weg**, Bluetooth erneut sichtbar zu schalten. Das geht nur über den Seriellen Befehl `bt suchen`. Ohne Laptop kann sich die App danach nicht mehr verbinden. Der Plan löst das mit (Kap. 3, M6).

### 1.1 Geschätzte Ströme je Baustein (5-V-Seite)

| Baustein | günstig | ungünstig | Grundlage |
|---|---|---|---|
| CYD-Grundlast (Regler, CH340C, Verstärker, LCD-/Touch-Logik) | 8 mA | 20 mA | AMS1117 Iq 5 mA typ. [11], Rest (S) |
| ESP32 240 MHz + WLAN verbunden (Modem-Sleep) | 35 mA | 75 mA | Datenblatt Modem-Sleep 240 MHz 30–68 mA [1] + Beacon-Empfang (S) |
| ESP32 80 MHz, Funk aus | 20 mA | 31 mA | Datenblatt [1] |
| ESP32 Light-Sleep, 10× pro s kurz wach | 1 mA | 3 mA | Light-Sleep 0,8 mA [1] + Wachanteil (S) |
| ESP32 80 MHz + BLE wirbt/verbunden (kein Light-Sleep möglich) | 25 mA | 45 mA | (S) |
| ESP32 beim WLAN-Abgleich (ca. 15 s) | 100 mA | 160 mA | (S), Empfang laut Datenblatt ca. 95–100 mA [1] |
| Hintergrundlicht 100 % | 40 mA | 80 mA | (S), **keine Messung gefunden** |
| Hintergrundlicht gedimmt (ca. 20 % PWM) | 8 mA | 16 mA | (S), etwa proportional zum Tastgrad |
| HX711 + Wägezelle | 3 mA | 6 mA | HX711 1,4 mA analog [7] + Brücke ca. 1 kΩ (S) |
| Nässe-Modul | 1 mA | 4 mA | (S) |
| 26 LEDs „aus“ (Ruhestrom) | 12 mA | 16 mA | 0,45–0,6 mA je LED [8]; ob der FCOB-Chip gleich viel braucht, ist **unbekannt** |
| 26 LEDs blau, Helligkeit 60 | +60 mA | +80 mA | 26 × ca. 12 mA × 60/255 [8b] (S) |
| 26 LEDs blau, Sparhelligkeit 15 | +15 mA | +20 mA | dieselbe Rechnung mit 15/255 (S) |

---

## 2. Was die Quellen festlegen (und was das für uns heißt)

1. **Automatischer Light-Sleep geht mit der Arduino-IDE nicht.**
   - Im fertig gebauten Kern 3.3.12 ist `CONFIG_PM_ENABLE` **nicht gesetzt** (lokal geprüft in `esp32-libs/3.3.12/sdkconfig`).
   - Ohne `CONFIG_FREERTOS_USE_TICKLESS_IDLE` meldet `esp_pm_configure()` den Fehler `ESP_ERR_NOT_SUPPORTED` [3].
   - Außerdem hält Bluetooth auf dem ESP32 eine „kein Light-Sleep“-Sperre, solange kein externer 32-kHz-Quarz verbaut ist [3]. Das CYD hat keinen; im sdkconfig steht `CONFIG_BTDM_CTRL_LPCLK_SEL_MAIN_XTAL=y`.
   - → Wir nutzen **manuellen** Light-Sleep (`esp_light_sleep_start()`). Das ist eine normale API ohne besondere Konfiguration [2].
2. **Vor jedem Light-Sleep müssen WLAN und Bluetooth aus sein.** Verbindungen bleiben im Light-Sleep nicht bestehen [2].
   - → In RUHE: WLAN aus, BLE-Stack beendet (`NimBLEDevice::deinit(false)`; mit `false` bleiben Server und Characteristic erhalten und funktionieren nach erneutem `init()` weiter, laut NimBLEDevice.cpp).
3. **Aufwecken per GPIO-Pegel geht im Light-Sleep an jedem Pin** (`gpio_wakeup_enable()` + `esp_sleep_enable_gpio_wakeup()`) [2].
   - → Touch-IRQ GPIO36 (LOW = Berührung) und Nässe GPIO19 (LOW = nass) können wecken, dazu ein Timer (100 ms).
4. **Errata GPIO36/39:**
   - Beim Einschalten von SAR-ADC (Akku-Messung an GPIO35!) oder durch WLAN-Stromsparen kann GPIO36 ca. 80 ns lang LOW gehen. Das löst falsche Flanken-Interrupts aus [5].
   - → Ein Weck- oder IRQ-Signal von GPIO36 gilt nur als **Hinweis**. Erst die Druckmessung (`touch.touched()` mit Druckschwelle) entscheidet, ob wirklich berührt wurde.
5. **Uhr im Light-Sleep:**
   - Wach läuft die Systemzeit über den Quarz.
   - Im Light-Sleep läuft sie über den internen RC-Oszillator (90–150 kHz), und der **driftet mit der Temperatur** [4]. Espressif nennt keine Zahl.
   - → Drift beim Abgleich messen und protokollieren, Abgleich-Abstand danach festlegen (Start: 6 h).
6. **HX711:**
   - Power-down: weniger als 1 µA.
   - Nach dem Einschalten braucht er bei 10 SPS **400 ms Einschwingzeit** [7].
   - → Ein `power_down()` zwischen den Messungen würde die 10 Messungen pro Sekunde und damit die Trink-Erkennung (Ruhezeit 1,5 s, Glättung) verändern. **Am Tag nicht empfohlen**, nur nachts als Option (M11).
7. **Pololu S13V10F5** [6]:
   - Ruhestrom laut Grafik bei 2,8 V ca. 13 mA, bei ca. 4 V ca. 8 mA, bei 3,7 V abgelesen ca. 9,5 mA.
   - **Kein Enable-Pin** (Spezifikation „Optional enable input: –“).
   - Eine Kurve für 3,7 V gibt es nicht. Zwischen den Kurven für 3,3 V und 5 V liegt der Wirkungsgrad bei 0,05 A bei ca. 80–85 % und bei 0,1–0,3 A bei ca. 88–93 %.
8. **Wokwi** [13][14]:
   - Bluetooth wird **nicht** simuliert.
   - Der RTC-Teil wird nur teilweise simuliert (nur Pull-Widerstände). Light-Sleep und GPIO-Wakeup sind dort also **nicht verlässlich testbar**.
   - Der Backlight-Pin `LED` des ILI9341 wird nicht simuliert, LEDC-PWM dagegen schon.

---

## 3. Energiezustände (neu, zusätzlich zum bestehenden Zustandsautomaten)

Die bestehenden Zustände (IDLE, MESSEN, ERINNERUNG, ZIEL_ERREICHT, NAESSE_SPERRE, KALIBRIERUNG) bleiben **unverändert**. Neu kommt ein zweiter, unabhängiger kleiner Automat `Energie` dazu (wie heute schon der Bluetooth-Automat).

| Zustand | Display | CPU | Waage | Erinnerung / Uhr / Nässe | WLAN | BLE |
|---|---|---|---|---|---|---|
| **AKTIV** | Licht `LCD_HELL` (Vorschlag 255 = 100 %), Neuzeichnen wie heute | 80 MHz, `delay(5)` | 10×/s | laufen | aus (außer Abgleich) | nur im Fenster |
| **GEDIMMT** | Licht `LCD_GEDIMMT` (Vorschlag 40 von 255 ≈ 16 %), Neuzeichnen wie heute | 80 MHz | 10×/s | laufen | aus | nur im Fenster |
| **RUHE** | Licht **0**, kein Neuzeichnen (optional ILI9341 `DISPOFF`/`SLPIN`, M3) | **Light-Sleep**, Wecken alle 100 ms + Touch + Nässe | 10×/s (bei jedem Wecken) | laufen bei jedem Wecken | aus | aus (Stack beendet) |
| **NACHT** (optional) | wie RUHE, nur schneller aus | wie RUHE | wie RUHE (optional langsamer, M11) | Erinnerungen sind in der Ruhezeit 22–7 Uhr ohnehin gesperrt | aus | aus |

### 3.1 Zeitgrenzen (neue benannte Konstanten, Vorschläge)

| Konstante | Vorschlag | Bedeutung |
|---|---|---|
| `STROMSPAREN` | `1` | Hauptschalter (0 = Verhalten wie heute, für Fehlersuche) |
| `ANZEIGE_DIMMEN_NACH_MS` | 30 000 | 30 s ohne Aktivität → GEDIMMT |
| `ANZEIGE_AUS_NACH_MS` | 120 000 | 2 min ohne Aktivität → RUHE |
| `ANZEIGE_AUS_NACH_MS_NACHT` | 15 000 | in der Ruhezeit (22–7 Uhr) schneller aus (optional) |
| `LCD_HELL` / `LCD_GEDIMMT` | 255 / 40 | PWM-Wert 0–255 für GPIO21 |
| `LCD_PWM_FREQ_HZ` / `LCD_PWM_BITS` | 5000 / 8 | LEDC am GPIO21 (Kern 3.x: `ledcAttach(21, 5000, 8)`, `ledcWrite(21, wert)`) |
| `RUHE_WECKTAKT_MS` | 100 | Timer-Wecken im Light-Sleep, passend zu 10 SPS des HX711 → Trink-Logik bleibt gleich |
| `CPU_MHZ` | 80 | `setCpuFrequencyMhz(80)` in `setup()`; „80 MHz (WiFi/BT)“ ist eine offizielle Board-Option |
| `WLAN_ABGLEICH_ALLE_MS` | 6 h | WLAN kurz an, NTP holen, wieder aus |
| `WLAN_ABGLEICH_TIMEOUT_MS` | 20 000 | danach aufgeben (spart Strom ohne WLAN) |
| `BT_SYNC_FENSTER_MS` | 60 000 | BLE kurz sichtbar nach jedem erkannten Trinken/Nachfüllen (falls Option A) |
| `BT_SUCH_TIMEOUT_MS` | 120 000 (wie heute) | beim Start und nach Tippen auf das BT-Symbol |
| `LED_ERINNERUNG_HELL_MS` | 120 000 | so lange leuchtet die Erinnerung voll blau, danach ruhiges **Sparblau** |
| `LED_HELLIGKEIT_SPAR` | 15 | Sparblau (Dauerlicht, **kein** Blinken, passt zur LED-Regel) |
| `AKKU_ABSCHALT_V` / `AKKU_ABSCHALT_MS` | 3,30 V (S) / 60 000 | Schutz bei leerem Akku (Kap. 5); Wert nach der Entlademessung anpassen |

### 3.2 Übergänge

- **AKTIV → GEDIMMT** nach `ANZEIGE_DIMMEN_NACH_MS` ohne Aktivität.
- **GEDIMMT → RUHE** nach `ANZEIGE_AUS_NACH_MS` ohne Aktivität (gezählt ab der letzten Aktivität).
- **jeder Zustand → AKTIV** bei „Aktivität“:
  - echte Berührung (Druck bestätigt),
  - Flasche abgehoben oder abgestellt,
  - Trinken oder Nachfüllen erkannt,
  - Wechsel nach ERINNERUNG, ZIEL_ERREICHT, NAESSE_SPERRE oder KALIBRIERUNG,
  - Handy verbindet oder trennt,
  - erste Akku-Warnung beim Unterschreiten (Wiederholungen alle 10 min nur per LED),
  - Serieller Befehl.
- **RUHE ist gesperrt** (Gerät bleibt mindestens GEDIMMT bzw. wach), solange:
  - NAESSE_SPERRE aktiv ist (Display bleibt hell, Sicherheit geht vor; der Nässe-Pegel würde sonst ohnehin sofort wieder wecken),
  - KALIBRIERUNG läuft,
  - ein Blinkmuster läuft (Akku rot, lila 2×, BT weiß; die Zeitsteuerung läuft in `loop()`),
  - ein WLAN-Abgleich oder ein BLE-Fenster/eine Verbindung läuft (Light-Sleep würde die Verbindung trennen [2]),
  - der Finger noch auf dem Display liegt.

### 3.3 Weckquellen in RUHE

| Quelle | Pin / Art | Zweck | Hinweis |
|---|---|---|---|
| Timer | 100 ms | Waage lesen, Zustandsautomat, Erinnerung, Uhr, Tageswechsel, Akku | ändert die Trink-Logik nicht |
| Touch | GPIO36 LOW (PENIRQ) | Display an | Errata [5]: erst Druckmessung, dann zählen. Vor dem Schlafen `detachInterrupt(36)`, danach wieder anhängen (Bibliothek nutzt FALLING) – **auf Hardware testen** |
| Nässe | GPIO19 LOW | sofort Sperre | reagiert sonst spätestens nach 100 ms |
| Ladegerät | – | – | kein freier Pin; Erkennung nur über steigende Akkuspannung (optional) |
| UART (optional) | RX | Serielle Befehle in RUHE | das erste Zeichen geht verloren; sonst `STROMSPAREN 0` zum Debuggen |

Vor dem Schlafen: `Serial.flush()`, Hintergrundlicht 0, LED-Daten-Pin LOW. Der FET-Pin (GPIO18) muss **seinen Pegel halten** (umgesetzt in V4: HIGH = LED-Streifen hat Strom, LOW = aus). Dafür `gpio_hold_en()` und nach dem Aufwachen `gpio_hold_dis()`. **Auf Hardware prüfen (Test H8).**

---

## 4. Maßnahmen

### 4.1 Nur Software

| Nr | Maßnahme | Ersparnis (5-V-Seite) | Risiko / Prüfpunkt | Priorität |
|---|---|---|---|---|
| M1 | **Hintergrundlicht per PWM** (LEDC an GPIO21): gedimmt nach 30 s, aus nach 2 min | gedimmt ca. 30–65 mA, aus ca. 40–80 mA (S) | Wokwi zeigt das Display-Licht nicht [14], dort eine Hilfs-LED an GPIO21 | **1** |
| M2 | **WLAN nur zum Abgleich**: nach NTP-Empfang `WiFi.disconnect(true)` + `WiFi.mode(WIFI_OFF)`; alle 6 h und per Befehl kurz wieder an, mit Timeout 20 s | dauerhaft ca. 10–40 mA (S) weniger, ohne erreichbares WLAN deutlich mehr | Uhr-Drift (M2b), Telegram später nur „bei Bedarf verbinden“ | **1** |
| M2b | Abweichung bei jedem Abgleich ins Protokoll schreiben (`[UHR] Abgleich: Abweichung x s`) | – | entscheidet über den Abstand 6 h | 1 |
| M3 | **Neuzeichnen aus** in RUHE; optional ILI9341 `DISPOFF` (0x28) + `SLPIN` (0x10), beim Aufwachen `SLPOUT` (0x11) + 120 ms warten + `DISPON` (0x29) | Logik des Displays (S, Größe unbekannt → messen) | Wartezeiten aus dem ILI9341-Datenblatt einhalten; erst messen, ob es sich lohnt | 2 |
| M4 | **CPU 80 MHz** (`setCpuFrequencyMhz(80)`) | wach ca. 10–37 mA weniger (Datenblatt 240 MHz 30–68 mA vs. 80 MHz 20–31 mA [1]) | Display baut langsamer auf (SPI bleibt 26,7 MHz, da APB 80 MHz) → ansehen | **1** |
| M5 | **Manueller Light-Sleep in RUHE**, Timer 100 ms + GPIO-Wecken | ca. 20–30 mA (S) gegenüber wach mit 80 MHz | `millis()` läuft weiter (esp_timer wird nachgeführt), auf Hardware prüfen; nur echte Hardware (Wokwi: nein) | **1** |
| M6 | **Bluetooth nur in Fenstern** + `deinit` danach (Option A/B/C in Kap. 7); dazu **Tippen auf das BT-Symbol = 2 min sichtbar** (behebt den Nebenbefund) | ermöglicht erst M5; Dauer-BLE kostet ca. 25–45 mA (S) | Re-`init` nach `deinit(false)` auf Hardware testen; die App muss mit Fenstern umgehen | **1** |
| M7 | **Erinnerungs-LED**: 2 min voll blau, danach ruhiges Sparblau (Helligkeit 15), bis getrunken wird | ca. 45–60 mA (S), solange die Erinnerung offen ist | Gestaltungsentscheidung (bleibt Dauerlicht, kein Blinken) | 2 |
| M8 | **Touch weckt nur**: in GEDIMMT/RUHE zählt die erste Berührung nicht als Tastendruck (Leer/Voll würden sonst die Kalibrierung überschreiben). Langdruck zählt erst nach dem Loslassen | – | Entscheidung, ob das auch für GEDIMMT gilt (Vorschlag: ja) | **1** |
| M9 | **Akku-Prozent per Tabelle** statt linear (aus eigener Entlademessung, Test H5) + Schutz bei leerem Akku (Kap. 5) | – (schützt den Akku) | Tabelle erst nach der Messung | 2 |
| M10 | Akku-ADC in RUHE nur alle 5 s statt 500 ms | sehr klein (S) | weniger GPIO36-Störungen [5] | 3 |
| M11 | **Nacht (optional)**: HX711 `power_down()` zwischen Messungen alle 2 s (400 ms Einschwingen [7]), nur wenn **keine** Flasche steht | ca. 2–5 mA nachts (S) | ändert die Mess-Logik nachts → nur nach Test, eher weglassen | 3 |

**Nicht geplant:** automatischer Light-Sleep (geht mit Arduino-IDE nicht, Kap. 2), Deep-Sleep im Alltag (RAM und Zustände gehen verloren, die Waage würde nicht gelesen).

### 4.2 Hardware (braucht deine Entscheidung, kostet Teile/Zeit)

| Nr | Änderung | Ersparnis | Aufwand / Hinweise |
|---|---|---|---|
| H1 | **LED-Streifen-5 V per FET schalten** (High-Side, P-Kanal, z. B. AO3401, wie in der Vorkalkulation) und nur einschalten, wenn die LEDs leuchten sollen | ca. 12–16 mA dauerhaft (S) = größter Hardware-Hebel | Passt zur offenen „FET High-Side“-Frage. Möglich wäre, den vorhandenen Last-Ausgang GPIO18 so zu definieren, dass er den Streifen versorgt; die Nässe-Abschaltung bleibt dann erhalten. Wenn der Streifen aus ist, muss DIN LOW sein (sonst Fehlspeisung über die Datenleitung); der 330–470-Ω-Widerstand begrenzt das. Nach dem Einschalten die Farbe neu senden |
| H2 | **Schiebeschalter** in der Akku-Leitung (nach TC4056-OUT, vor Pololu **und** vor dem Spannungsteiler) | „Aus“ = 0 mA statt ca. 9,5 mA Pololu-Ruhestrom + CYD-Grundlast | Gehäuse-Öffnung → SCAD/STL/Renders ändern. Ohne Schalter leert sich der Akku auch „aus“ in einigen Tagen (S) |
| H3 | Power-LED am Nässe-Modul ablöten | ca. 1–3 mA (S) | 5 min Lötarbeit; vorher messen, ob sich das lohnt |
| H4 | Spannungsteiler 2 × 100 kΩ statt 2 × 10 kΩ | 0,19 mA → 0,02 mA | 100 kΩ waren bei Berrybase nicht lieferbar; klein, nur für Lagerung wichtig |

---

## 5. Sonderfälle

1. **Erinnerung bei dunklem Display:** Der Wechsel nach ERINNERUNG gilt als Aktivität → Display AKTIV + LEDs blau. Danach laufen die normalen Zeitgrenzen; die LEDs bleiben blau (nach 2 min Sparblau), bis getrunken wird.
2. **Trinken bei dunklem Display:** Die Waage wird in RUHE weiter 10× pro Sekunde gelesen (Wecken alle 100 ms). `trinkenAuswerten()` läuft unverändert. Abheben oder Abstellen weckt das Display, damit man die neue Menge sieht.
3. **Wecken per Touch löst keine Taste aus** (M8). Zusätzlich muss die Druckschwelle passen (Errata GPIO36 [5]).
4. **Nässe:** Der GPIO-Pegel weckt sofort. Danach wie heute: 100 ms entprellen → Sperre → FET aus. In der Sperre kein Light-Sleep, das Display bleibt hell.
5. **Laden:** Es gibt keinen freien Pin für das Lade-Signal des TC4056. Optional: steigende Spannung über 10 min → Symbol „lädt“. Sonst normaler Betrieb, kein Sonderfall nötig.
6. **Akku leer:**
   - Heute warnt das Gerät erst bei linear „20 %“, das sind ca. 3,24 V, und ein LiPo ist dann schon fast leer.
   - Plan: Prozent per Tabelle (M9). Unter `AKKU_ABSCHALT_V` 60 s lang → Bildschirm „Akku leer – bitte laden“ 10 s → LEDs aus, WLAN/BLE aus, Hintergrundlicht aus.
   - Dann `esp_deep_sleep` mit Timer (z. B. 15 min), der prüft, ob geladen wird. Der Tageszähler und die Kalibrierung liegen schon im NVS und bleiben erhalten.
   - **Grenze:** Pololu (ca. 9,5 mA) und die CYD-Grundlast laufen weiter. Nur ein Schalter (H2) schützt den Akku wirklich. Ob das Lademodul einen Tiefentladeschutz hat, ist **ungeprüft**.
7. **BLE-Abgleich mit der App:** Die App bekommt nur in BLE-Fenstern Daten. Siehe Entscheidung 1 in Kap. 7. Werte gehen nicht verloren, die App liest beim nächsten Fenster den aktuellen Stand.
8. **Tageswechsel um Mitternacht in RUHE:** `uhrVerwalten()` läuft bei jedem Wecken mit, der Reset passiert wie heute.
9. **Kalibrierung:** In KALIBRIERUNG kein Dimmen und kein RUHE (oder erst nach 5 min).
10. **Serielle Befehle in RUHE:** Sie kommen nur an, wenn UART-Wecken eingebaut ist (erstes Zeichen geht verloren) oder mit `STROMSPAREN 0`.
11. **Wokwi:**
    - Light-Sleep, GPIO-Wecken, Bluetooth und das Display-Licht lassen sich dort nicht echt simulieren [13][14].
    - Plan: `HYDRO_LIGHTSLEEP` ist nur bei `HYDRO_CYD 1` aktiv. In Wokwi läuft derselbe Energie-Automat ohne echten Schlaf. Das Display wird in RUHE schwarz gezeichnet, und eine Hilfs-LED „LICHT“ an GPIO21 zeigt Hell/Gedimmt/Aus über PWM.
    - So lassen sich alle Zeitgrenzen und Weckregeln in Wokwi testen, nur der Strom nicht.

---

## 6. Laufzeit-Rechnung

**Formeln** (alle Zahlen dieses Kapitels sind Schätzungen):

- Nutzbare Energie: `E = 2000 mAh × 90 % × 3,7 V = 6,66 Wh`.
- Leistung aus dem Akku: `P_ein = 5 V × I_5V / 0,92 + 3,7 V × 9,5 mA + 3,7 V × 0,185 mA`.
  - 0,92 ist der Schaltwirkungsgrad aus der Pololu-Grafik bei mittlerer Last; 9,5 mA ist der Ruhestrom aus der Pololu-Grafik bei 3,7 V [6]; der letzte Summand ist der Spannungsteiler.
  - Dieses Modell ergibt bei 0,3 A ca. 90 %, bei 0,05 A ca. 82 % und bei 0,02 A ca. 70 %. Das passt zur Herstellergrafik [6].
- Laufzeit: `t = E / P_ein` (Durchschnitt über das Tagesprofil).

**Tagesprofil-Annahmen:**

- 8 h am Schreibtisch: ca. 40 Aktivitäten (Trinken, Tippen, Erinnerungen) × 30 s AKTIV = 20 min AKTIV, × 90 s = 60 min GEDIMMT, Rest RUHE.
- BLE-Fenster: 16 Fenster × 1 min pro Tag.
- WLAN-Abgleich: 4 × 15 s pro Tag.
- Erinnerungs-LEDs: heute 30 min pro Tag voll blau; im Plan 8 min voll + 22 min Sparblau.
- 16 h abwesend/Nacht: RUHE.

| Zustand (5-V-Strom) | ohne H1 | mit H1 (LED-FET) | Akku-Strom bei 3,7 V ohne H1 |
|---|---|---|---|
| IST (heute, dauernd) | 99–201 mA | – | 155–305 mA |
| AKTIV | 84–157 mA | 72–141 mA | 133–240 mA |
| GEDIMMT | 52–93 mA | 40–77 mA | 86–146 mA |
| RUHE | 25–49 mA | 13–33 mA | 46–82 mA |
| RUHE mit BLE an | 49–91 mA | 37–75 mA | 82–143 mA |

| Szenario | Ø Akku-Strom | **Laufzeit** |
|---|---|---|
| **Heute** (alles dauernd an) | 157–307 mA | **ca. 6–12 h** |
| **Plan Software**, 24-h-Tag (8 h Nutzung + 16 h Ruhe) | 51–89 mA | **ca. 20–36 h** |
| Plan Software, nur Schreibtisch-Nutzung am Stück | 56–98 mA | **ca. 18–32 h** |
| Plan Software, aber BLE dauernd an (Option C) | 84–146 mA | ca. 12–22 h |
| **Plan + H1 (LED-FET)**, 24-h-Tag | 33–66 mA | **ca. 27–54 h** |
| Plan + H1, nur Schreibtisch-Nutzung am Stück | 39–75 mA | ca. 24–47 h |
| Plan + H1, BLE dauernd an | 66–123 mA | ca. 15–27 h |
| Nur Pololu-Ruhestrom + Teiler (alles andere 0) | ca. 9,7 mA | ca. 7,7 Tage (zeigt: „Aus“ ohne Schalter ist nicht „aus“) |

**Unsicherheiten:**

- CYD-Grundlast, Hintergrundlicht und Ruhestrom der FCOB-Chips sind **nicht gemessen**. Das sind die drei größten Unsicherheiten.
- Die Zahl der Aktivitäten pro Tag hängt vom Nutzer ab.
- Die Kapazität eines echten Akkus kann unter 2000 mAh liegen.
- Die Spannungsgrenze, ab der der Akku als leer gilt, steht noch nicht fest.

---

## 7. Offene Entscheidungen für dich

1. **Bluetooth-Strategie** (beeinflusst auch die App):
   - **A (Vorschlag):** BLE sichtbar beim Start (2 min), beim Tippen auf das BT-Symbol (2 min) und 60 s nach jedem erkannten Trinken. Die App verbindet sich, sobald sie das Gerät sieht.
   - **B:** zusätzlich feste Fenster alle 15 min für 30 s (+ ca. 48 min BLE pro Tag).
   - **C:** BLE dauernd an → kein Light-Sleep, Laufzeit ca. 12–22 h.
2. **Zeitgrenzen:** dimmen nach 30 s, aus nach 2 min, nachts nach 15 s – passt das?
3. **Touch im gedimmten Zustand:** nur aufwecken (Vorschlag) oder gleich als Tastendruck werten?
4. **Erinnerungs-LED:** nach 2 min auf ruhiges Sparblau (Vorschlag) oder voll blau lassen, bis getrunken wird?
5. **WLAN:** nur alle 6 h zum Uhr-Abgleich (Vorschlag)? Telegram später nur „kurz verbinden, senden, aus“.
6. **Nacht-Modus** (schneller aus, optional HX711 drosseln): ja oder nein?
7. **Hardware H1** (LED-FET, high-side): ja/nein. Das hängt mit der offenen FET-Frage zusammen (Was genau schaltet „Last“ an GPIO18?).
8. **Hardware H2** (Schiebeschalter): ja/nein. Bei ja ändern sich Gehäuse, STLs, Renders, Vorkalkulation und Einkaufsliste.
9. **Hardware H3/H4** (LED am Nässe-Modul, 100-kΩ-Teiler): erst nach der Messung entscheiden.

---

## 8. Umsetzung (erst nach deiner Freigabe) und betroffene Dateien

**Reihenfolge:**

1. **Phase 1:** M1, M2, M4, M8, Energie-Automat (ohne Schlaf).
2. **Phase 2:** M5 + M6 (Light-Sleep + BLE-Fenster, nur Hardware).
3. **Phase 3:** M3, M7, M9, M10, ggf. M11.
4. **Hardware:** nach Entscheidung.

| Datei | Änderung |
|---|---|
| `wokwi/sketch.ino` (beide Orte: `/workspace/HydroDesk/wokwi` + Repo `wokwi/`) | Energie-Automat, Konstanten, PWM, WLAN-Abgleich, BLE-Fenster, Light-Sleep (`#if HYDRO_CYD`), Touch-Wecken, LED-Sparblau, Akku-Tabelle/-Schutz; Version 4 |
| `wokwi/diagram.json` + `wokwi/verdrahtung.png` | Hilfs-LED „LICHT“ an GPIO21 (nur Simulation) |
| `wokwi/README.md` | neues Kapitel „Stromsparen“, neue Tests, Grenzen von Wokwi |
| `wokwi/HydroDesk_Wokwi.zip`, `wokwi_vscode/HydroDesk_Wokwi_VSCode.zip` | neu packen |
| `firmware/README.md` | Stromsparen, Hinweis: kein automatischer Light-Sleep mit Arduino-IDE, BLE-Fenster |
| `README.md` (Repo) | Feature „Stromsparmodus“, Laufzeit (nach Messung) |
| `Steckbrief_HydroDesk_Base.docx` | Laufzeit-Ziel, Stromsparmodus, ggf. Schalter |
| `Vorkalkulation_HydroDesk_Base.xlsx`, `Einkaufsliste_HydroDesk_guenstig.*` | nur bei H1/H2/H4 (FET, Schalter, Widerstände) |
| `gehaeuse/*.scad`, STLs, 3D-Modelle, Renders | nur bei H2 (Schalter-Öffnung) |
| `app-android` (Doku/Code) | nur bei BLE-Option A/B: Verbinden, sobald Werbung gesehen wird |
| `Stromsparplan_HydroDesk.md` | Messwerte eintragen, Tabelle aktualisieren |

---

## 9. Tests

### 9.1 Wokwi (mit `WOKWI_DEMO_ERINNERUNG 1`)

| Test | Vorgehen | Erwartung |
|---|---|---|
| S1 | 30 s nichts tun | `[ENERGIE] AKTIV -> GEDIMMT`, Hilfs-LED dunkler |
| S2 | weitere 90 s | `-> RUHE`, Display schwarz, Hilfs-LED aus |
| S3 | in RUHE auf die Taste „Leer“ tippen | Display an, **keine** Kalibrier-Meldung, Leergewicht unverändert |
| S4 | in RUHE Flasche abheben, leichter zurückstellen | Schluck wird gezählt (wie heute) + Display AKTIV |
| S5 | Erinnerung in RUHE auslösen | Display AKTIV, LEDs blau, nach `LED_ERINNERUNG_HELL_MS` Sparblau |
| S6 | NÄSSE in RUHE nach rechts | sofort NAESSE_SPERRE, LAST aus, Display hell, kein RUHE |
| S7 | Start mit Wokwi-GUEST | NTP → `[UHR] WLAN aus`; Befehl `sync` → WLAN an, NTP, aus, Abweichung im Protokoll |
| S8 | `zeit 23:59` + RUHE | um 00:00 Tageszähler 0 |
| S9 | `bt suchen` / simuliertes Trinken | Fenster-Logik im Protokoll (BLE selbst ist nicht simulierbar) |
| S10 | alle bisherigen Tests aus `wokwi/README.md` | unverändert bestanden (Regression) |
| S11 | `STROMSPAREN 0` | Verhalten exakt wie Version 3 |

### 9.2 Echte Hardware (Messung)

Messgeräte: USB-Strommessgerät für die 5-V-Seite (System über USB-5 V statt Pololu versorgt) und ein Multimeter in Reihe mit dem Akku für die Akku-Seite (inkl. Pololu).

| Test | Vorgehen | Ergebnis eintragen |
|---|---|---|
| H1 | Firmware V3 (heute): 60 s mitteln | Ist-Strom 5 V und Akku |
| H2 | V4: AKTIV, GEDIMMT, RUHE, RUHE+BLE, WLAN-Abgleich je 60 s mitteln | Tabelle Kap. 6 ersetzen |
| H3 | Bausteine einzeln abziehen (LED-Streifen, HX711, Nässe-Modul) | Ruhestrom FCOB, HX711, Nässe |
| H4 | 50× Touch-Wecken, 20× Flasche heben/trinken in RUHE (mit Küchenwaage vergleichen) | keine verpasste Trinkmenge, keine Fehl-Taste |
| H5 | Entladetest: voll laden, im Alltag laufen lassen, alle 10 min Spannung + Laufzeit ins NVS schreiben | echte Laufzeit + Spannungs-Tabelle für M9 |
| H6 | 24 h ohne Abgleich, dann Abgleich | Uhr-Drift im Light-Sleep |
| H7 | BLE: `deinit`/`init` 20× im Wechsel, App verbindet im Fenster | Stabilität von NimBLE |
| H8 | Display-Licht im Light-Sleep, LED-DIN LOW, GPIO18 bleibt HIGH (Multimeter) | Pins halten ihren Pegel |

---

## 10. Quellen

1. Espressif, ESP32 Series Datasheet v5.3, Tabelle 4-2 „Power Consumption by Power Modes“: https://documentation.espressif.com/esp32_datasheet_en.html
2. ESP-IDF v5.5, Sleep Modes (WLAN/BT vor Light-Sleep aus; GPIO-Wakeup an jedem Pin; VDD_SDIO-Warnung GPIO16/17): https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32/api-reference/system/sleep_modes.html
3. ESP-IDF v5.5, Power Management (`CONFIG_PM_ENABLE`, Tickless Idle, BT-Sperre ohne 32-kHz-Quarz): https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32/api-reference/system/power_management.html
4. ESP-IDF v5.5, System Time (RC-Oszillator driftet im Light-/Deep-Sleep): https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32/api-reference/system/system_time.html
5. ESP32 Errata GPIO-3.11 (GPIO36/39 ca. 80 ns LOW): https://docs.espressif.com/projects/esp-chip-errata/en/latest/esp32/03-errata-description/esp32/gpio-inputs-pulled-down.html
6. Pololu S13V10F5 (Wirkungsgrad- und Ruhestrom-Grafik, max. 20 mA Ruhestrom, kein Enable): https://www.pololu.com/product/4083 und https://www.pololu.com/product/4083/specs
7. HX711 Datenblatt (< 1,5 mA, Power-down < 1 µA, 400 ms Einschwingzeit bei 10 SPS): https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf
8. WS2812B Ruhestrom gemessen 0,577 mA bei 5 V: https://refcircuit.com/articles/876-quiescent-current-of-addressable-led-ws2812-measurement.html · 8b: Messung ca. 11–12,75 mA pro Farbkanal, Ruhestrom ca. 0,45 mA: https://www.eevblog.com/forum/projects/ws2812b-leds-power-consumption/
9. Elektor-Test CYD („current draw … around 115 mA“): https://www.elektormagazine.com/review/cheap-yellow-display-board
10. Random Nerd Tutorials, CYD-Daten („Power consumption: approximately 115mA“): https://randomnerdtutorials.com/micropython-cheap-yellow-display-board-cyd-esp32-2432s028r/
11. AMS1117 Datenblatt (Quiescent Current 5 mA typ., 10 mA max): https://media.digikey.com/pdf/Data%20Sheets/UTD%20Semi%20PDFs/AMS1117.pdf
12. CYD-Hardwarenotizen (CH340C, SC8002B): https://github.com/radio3-network/kit-ESP32-2432S028R/blob/main/notes-ESP32-2432S028R.txt
13. Wokwi ESP32-Simulation (Bluetooth ✗, RTC nur teilweise, LEDC ✓): https://docs.wokwi.com/guides/esp32
14. Wokwi ILI9341 (Backlight-Pin nicht simuliert): https://docs.wokwi.com/parts/wokwi-ili9341
15. Lokal geprüft: `~/.arduino15/packages/esp32/tools/esp32-libs/3.3.12/sdkconfig` (`# CONFIG_PM_ENABLE is not set`, `CONFIG_BTDM_CTRL_LPCLK_SEL_MAIN_XTAL=y`, `CONFIG_LWIP_SNTP_UPDATE_DELAY=10800000`), `boards.txt` (240 MHz Standard, 80 MHz WiFi/BT-Option), `XPT2046_Touchscreen.cpp` 1.4, `NimBLEDevice.cpp` 2.5.1 (`deinit(clearAll)`), `WiFiGeneric.cpp` (Standard `WIFI_PS_MIN_MODEM`).

Ein Hinweis zur Vorsicht: Ein KI-generierter „Benchmark“-Artikel auf aliexpress.com (CYD „Deep Sleep 0,8 µA“) und eine Reddit-Messung an einer **anderen** CYD-Variante (ca. 40 mA im Deep-Sleep) wurden bewusst **nicht** als Zahlenquelle verwendet.

---

## 11. Umsetzung V4 (Stand 09.10.2026) und was gemessen werden muss

### 11.1 Software (Commit `9e66c64`)

- Energie-Automat AKTIV → GEDIMMT (30 s) → RUHE (2 min), nachts (22–7 Uhr) schneller aus (15 s); Hintergrundlicht per PWM an GPIO21.
- CPU 80 MHz; WLAN nur zum Uhr-Abgleich (Start, alle 6 h, Timeout 20 s).
- BLE nur in Fenstern (Start 2 min, Antippen des BT-Symbols 2 min, 60 s nach Trinken); in RUHE manueller Light-Sleep mit 100-ms-Timer + Wecken über Touch (GPIO36) und Nässe (GPIO19), nur bei `HYDRO_CYD 1`.
- Touch weckt nur (M8), Erinnerung 2 min voll blau, danach Sparblau (M7), Akku-Prozent per typischer LiPo-Tabelle + Abschaltung bei leerem Akku (M9, Grenzwert noch nicht gemessen).
- `stromsparen 0` = Verhalten wie Version 3.

### 11.2 Hardware (Commit `71570e4`)

- **H1 – LED-Strom-FET:** P-MOSFET **AO3401A** (Q1), Source an 5 V vom Pololu (+ Elko 470 µF/25 V), Drain an „+“ des LED-Streifens, 10 kΩ Gate→Source. Ein NPN **BC547B** zieht das Gate auf GND: Basis über 4,7 kΩ an **GPIO18**, 47 kΩ Basis→GND (Streifen bleibt bei Reset/Boot aus). GPIO18 HIGH = Streifen an.
  - GPIO18 ist auf dem CYD die SD-Karten-CLK; im CYD-Schaltplan sitzen die 10-kΩ-Pull-ups (RN2) an CS (IO5), MOSI (IO23), MISO (IO19) und DAT1, **nicht** an CLK. Der Streifen bleibt deshalb beim Start sicher aus.
  - Wenn DIN (GPIO23) bei abgeschaltetem Streifen LOW ist, fließen durch den 10-kΩ-Pull-up an IO23 ca. 0,33 mA (3,3 V / 10 kΩ, gerechnet). Das ist klein gegenüber dem Rest.
- **H2 – Ein/Aus-Schalter:** Schiebeschalter **C&K OS102011MS2QN1** (linke Gehäusewand, Gravur AN/AUS) steuert einen zweiten **AO3401A** (Q2) zwischen TC4056-OUT+ (Source) und Pololu-VIN + Spannungsteiler (Drain), 47 kΩ Gate→Source. AN: Gate auf GND (ca. 0,08 mA durch die 47 kΩ, gerechnet). AUS: Gate an Source, FET sperrt. Die Body-Diode zeigt von der Pololu-Seite (Drain) zum Akku (Source), sperrt also in Richtung Akku → Pololu. Laden über den TC4056 geht in **beiden** Stellungen.
  - Im Zustand AUS bleiben nur die Leckströme von Modul und FET (erwartet im µA-Bereich, **nicht gemessen**).
- H3/H4 wurden nicht umgesetzt (erst messen).

### 11.3 Tests bisher

- Alle 4 Firmware-Varianten (Wokwi, Wokwi+BLE, CYD, CYD+BLE) mit arduino-cli und Kern 3.3.12 kompiliert, ohne Fehler.
- PC-Logiktest (`wokwi_tools/logiktest_v4`): Teil 1 85 Prüfungen OK, Teil 2 101 Prüfungen OK.
- **Kein** Lauf in Wokwi selbst (kein wokwi-cli auf dem Rechner) und **noch keine** echte Hardware. Light-Sleep, BLE-Fenster und alle Ströme sind nur kompiliert bzw. geschätzt.

### 11.4 Laufzeit (weiterhin geschätzt)

Mit Software + H1 im 24-h-Tag **ca. 27–54 h** (Kapitel 6), nur Software ca. 20–36 h, V3 ca. 6–12 h. Alle Werte sind **Schätzungen**, bis Test H5 gelaufen ist.

### 11.5 Was jetzt gemessen werden muss (Reihenfolge)

| Nr | Messung | Warum |
|---|---|---|
| 1 | **USB-Rückspeisung:** Schalter auf AUS, CYD per USB anstecken, Spannung an Pololu-VIN und am Akku messen (VIN soll ca. 0 V sein) | Bei Schalter AN und USB liegen Pololu-Ausgang und USB-5 V parallel (bestand schon in V3, nicht geprüft). **Bis dahin nur bei Schalter AUS programmieren.** |
| 2 | **Schalter:** AUS → Strom aus dem Akku (Multimeter in Reihe), AN → Spannung über Q2 (Drain–Source) bei Last | Leckstrom „aus“ und Spannungsverlust „an“ |
| 3 | **LED-FET:** GPIO18 LOW → Spannung am Streifen-„+“ ca. 0 V; HIGH → Spannung über Q1 bei voller Helligkeit | Schaltet Q1 voll durch? Streifen beim Booten wirklich aus? |
| 4 | Tests **H1–H8** aus Kapitel 9.2 | ersetzt die geschätzten Werte in Kapitel 6 |
| 5 | Entladetest H5 → LiPo-Tabelle und `AKKU_ABSCHALT_V` anpassen | Prozentanzeige und Akku-Schutz |
| 6 | Ruhestrom der FCOB-Chips (H3) und des Nässe-Moduls | entscheidet über H3 |
| 7 | Uhr-Drift (H6) | Abgleich-Abstand 6 h prüfen |

