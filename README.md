# 💧 HydroDesk Base

**Smarter Trinkmengen-Untersetzer für den Schreibtisch** – ESP32 mit Touch-Display, Wägezelle und LED-Lichtlinie.
Schulprojekt im Ausbildungsberuf Fachinformatiker/-in für Anwendungsentwicklung (FI-AE), 2 Auszubildende.

HydroDesk Base ist ein flaches, rechteckiges Gerät (180 × 100 × 25 mm), auf das man **jede beliebige Wasserflasche** stellt.
Eine 5-kg-Wägezelle misst das Gewicht und rechnet es in getrunkene Milliliter um.
Das eingebaute 2,8"-Touch-Display zeigt Tagesziel, Fortschritt und Erinnerungen – eine gleichmäßig leuchtende Lichtlinie an der Vorderkante (COB-LED-Streifen hinter einem gedruckten Diffusor) erinnert ans Trinken.

![HydroDesk Base – Produktbild](design/visualisierung/hydrodesk_produkt.png)

## ✨ Funktionen

- **Jede Flasche passt** – keine teure Smart-Flasche nötig
- **Gewicht → ml**: 5-kg-Wägezelle + HX711 unter einem schwimmend gelagerten 90 × 90 mm Flaschen-Pad
- **Flaschen-Kalibrierung per Touch-Tasten „Leer“ und „Voll“**: leere Flasche auflegen → Leer, volle Flasche → Voll; Inhalt = aktuelles Gewicht − Leergewicht
- **Tagesziel, Fortschritt und nächste Erinnerung** immer sichtbar auf dem Display
- **LED-Lichtlinie** an der Vorderkante: COB-LED-Streifen WS2812B (26 einzeln ansteuerbare LEDs, 5 mm breit) hinter einer gedruckten Diffusor-Leiste – keine einzelnen Lichtpunkte, sondern eine durchgehende Linie:
  - 🔵 blau = trinken
  - 🟢 grün = Ziel erreicht
  - 🔴 rot = Akku niedrig / Fehler
  - bei Wasser bleibt der Streifen dunkel (ab V4 ohne Strom)
- **Wasser-Sicherheitsabschaltung**: Regensensor erkennt Nässe, ein P-MOSFET (AO3401A, High-Side) schaltet die 5 V des LED-Streifens ab → Sperrbildschirm **„WASSER ERKANNT · STROM AUS“**
- **Akkubetrieb**: LiPo 2000 mAh, Laden per USB-C (TC4056), 5-V-Wandler Pololu S13V10F5
- **Ein/Aus-Schalter (V4)** in der linken Wand (Gravur AN/AUS): schaltet über einen zweiten AO3401A den Akku wirklich ab; Laden geht in beiden Stellungen
- **Stromsparmodus (Firmware V4)**: Display dimmt nach 30 s und geht nach 2 min aus (nachts nach 15 s),
  Light-Sleep, Bluetooth nur in kurzen Fenstern, WLAN nur zum Uhr-Abgleich, Akku-Schutz bei 3,30 V;
  der LED-Streifen bekommt nur Strom, wenn er leuchtet
- **Akkulaufzeit (geschätzt, noch nicht gemessen)**: ca. 27–54 h im 24-h-Tag (vorher ca. 6–12 h) – Rechnung und Messplan im [Stromsparplan](doku/Stromsparplan_HydroDesk.md)
- **Optional: Telegram-Bot** für Erinnerungen und Status (`/status`, `/ziel`, `/hilfe`)
- **3D-gedrucktes Gehäuse** (OpenSCAD, parametrisch, sechs Druckdateien: Bodenwanne, Deckel, Pad, steckbare USB-Abdeckkappe, Diffusor-Leiste, 2 Klemmkeile für den Schalter; ohne Stützmaterial druckbar)
- **Android-App** ([`app-android/`](app-android/)): Login (Supabase), Bluetooth-LE-Verbindung zum Gerät,
  Tagesziel aus Körperdaten, Verlauf mit Wochendiagramm, offline-fähig mit Sync, Admin-Übersicht, Demo-Modus

## 📐 Aufbau / Layout

```
+----------------------------------------------------------+
|  [ DISPLAY  ]  |  Mittel-  |  [                       ]  |
|  [ Hochform.]  |  streifen |  [   FLASCHEN-PAD 90x90  ]  |
|  [  2,8"    ]  |           |  [   (schwimmend auf der ]  |
|  [  Touch   ]  |           |  [    Wägezelle)         ]  |
+----------------------------------------------------------+
|  Lichtlinie vorne: COB-LED-Streifen (26 LEDs) + Diffusor |
```

- **Links:** ESP32-Touch-Display („Cheap Yellow Display“ ESP32-2432S028R) im Hochformat, darunter Akku und 5-V-Wandler (Pololu S13V10F5)
- **Mitte:** TC4056-USB-C-Lader an der Rückwand, FET-Platine (30 × 24,5 mm, 2 × AO3401A + BC547B), Auswertemodul des Regensensors
- **Links außen:** Ein/Aus-Schiebeschalter (C&K OS102011MS2QN1) in einer Tasche der Seitenwand, gehalten von 2 Klemmkeilen
- **Rechts:** 90 × 90 mm Flaschen-Pad, liegt nur auf der Wägezelle (1 mm Spalt rundherum); darunter Wägezelle, HX711 und Regensensor
- **Hinten:** USB-Öffnungen – Programmier-Öffnung des CYD mit **steckbarer Abdeckkappe**, USB-C zum Laden offen; **vorne:** Lichtkammer über fast die ganze Breite – der COB-Streifen klebt an ihrer Rückwand, davor sitzt die 1 mm dünne Diffusor-Leiste in einem Falz

| Explosionsansicht | Innenansicht ohne Deckel |
|---|---|
| ![Explosionsansicht](design/visualisierung/hydrodesk_explosion.png) | ![Innenansicht ohne Deckel](design/visualisierung/hydrodesk_innen.png) |

![Alle Einzelteile](design/visualisierung/hydrodesk_teile.png)

| Abdeckkappe eingesteckt | Abdeckkappe herausgezogen |
|---|---|
| ![Abdeckkappe eingesteckt](gehaeuse/preview/kappe_eingesteckt.png) | ![Abdeckkappe offen](gehaeuse/preview/kappe_offen.png) |

| Diffusor-Leiste herausgezogen (COB-Streifen dahinter) | Schnitt durch die Lichtkammer |
|---|---|
| ![Diffusor offen](gehaeuse/preview/diffusor_offen.png) | ![Schnitt Lichtkammer](gehaeuse/preview/18_led_kammer_schnitt.png) |

| Ein/Aus-Schalter links (V4) | FET-Platine (V4) |
|---|---|
| ![Ein/Aus-Schalter](gehaeuse/preview/20_schalter_links_aussen.png) | ![FET-Platine](gehaeuse/preview/24_fet_platine.png) |

Renderbilder: [`design/visualisierung/`](design/visualisierung/) · 3D-Modell zum Drehen (GLB/STL/3MF): [`design/3d_modell/`](design/3d_modell/) · technische OpenSCAD-Vorschauen: [`gehaeuse/preview/`](gehaeuse/preview/)

Details zu Druck, Schrauben und Zusammenbau: [`gehaeuse/ANLEITUNG.md`](gehaeuse/ANLEITUNG.md)

## 🧰 Hardware / Stückliste

Zusammenfassung aus der [Vorkalkulation](doku/Vorkalkulation_HydroDesk_Base.xlsx). Die Preise sind inkl. MwSt. von Amazon.de, Berrybase.de, Reichelt.de, alleschrauben.de und AliExpress, Stand 08.10.2026 (neue V4-Teile Pos. 5 und 24–34: 09.10.2026), und können sich ändern. Der Preisvergleich mit allen Alternativen steht in der [Einkaufsliste](doku/Einkaufsliste_HydroDesk_guenstig.xlsx).

| Pos. | Bauteil | Produkt | Shop | Packung | Preis |
|---:|---|---|---|---|---:|
| 1 | ESP32 + Touch-Display | Fastsaw ESP32 mit 2,8" ILI9341 Touch (ESP32-2432S028R, ASIN B0G1N16Q16) | Amazon | 1 Stk. | 17,99 € |
| 2 | Wägezelle + Verstärker | DIYmalls Wägezelle 5 kg + HX711 | Amazon | 1 Set | 8,97 € |
| 3 | LED-Streifen (COB) | BTF-LIGHTING WS2812B FCOB, 1 m, 160 LED/m, 5 V, 5 mm (ASIN B0H41MCVSW; 26 LEDs werden gebraucht) | Amazon | 1 m | 16,99 € |
| 4 | Feuchtigkeitssensor | Regensensor LM393 (digital + analog) | Berrybase | 1 Set | 1,80 € |
| 5 | LED-Strom + Ein/Aus (P-MOSFET) | Alpha & Omega AO3401A, P-Kanal, −30 V, −4 A, SOT-23 | Reichelt | 2 Stk. | 0,34 € |
| 6 | Akku | EEMB LiPo 3,7 V 2000 mAh (LP103454) | Amazon | 1 Stk. | 10,99 € |
| 7 | Lademodul | TC4056 USB-C Lademodul mit Schutz | Amazon | 10 Stk. | 6,99 € |
| 8 | 5-V-Wandler | Pololu S13V10F5, 5 V 1 A Step-Up/Step-Down | Berrybase | 1 Stk. | 9,95 € |
| 9 | Gummifüße | FIX&FASTEN Ø10 mm, selbstklebend | Berrybase | 4 Stk. | 0,60 € |
| 10 | Flaschen-Pad | FICOFISE Silikonmatte 40 × 30 cm (auf 86 × 86 mm zuschneiden) | Amazon | 1 Stk. | 7,59 € |
| 11 | Schrauben | Senkkopf M3×12 DIN 7991 A2 | alleschrauben.de | 10 Stk. | 2,50 € |
| 12 | Schrauben | Senkkopf M4×10 DIN 7991 A2 | alleschrauben.de | 2 Stk. | 1,12 € |
| 13 | Schrauben | Senkkopf M5×12 DIN 7991 A2 | alleschrauben.de | 2 Stk. | 1,24 € |
| 14 | Widerstände | 10 kΩ Metallschicht (Akku-Spannungsteiler) | Berrybase | 2 Stk. | 0,10 € |
| 15 | Litze | Vierlingslitze 4 × 0,14 mm² | Berrybase | 5 m | 3,50 € |
| 16 | Schrumpfschlauch | Set 100-teilig | Berrybase | 1 Set | 2,80 € |
| 17 | Klebeband | TESA doppelseitig 12 mm | Berrybase | 1 Rolle | 2,90 € |
| 18 | Kabelbinder | 100 × 2,5 mm | Berrybase | 100 Stk. | 0,60 € |
| 19 | JST-Kabel CYD | Micro JST 1,25 mm, 4-polig (**nur AliExpress**, ab-Preis) | AliExpress | 1 Set | 1,49 € |
| 20 | microSD-Sniffer | für GPIO 18/19/23 am SD-Slot (**nur AliExpress**, ab-Preis) | AliExpress | 1 Stk. | 2,39 € |
| 21 | Gehäuse-Material | SUNLU PLA 1,75 mm | Amazon | 1 kg | 14,99 € |
| 22 | Abdeckkappe | gedruckt aus Pos. 21 (ca. 1 g) | – | 1 Stk. | 0,00 € |
| 23 | Diffusor-Leiste | gedruckt aus weißem PLA oder naturfarbenem PETG (ca. 4 g, 1 mm, 100 % Füllung) | – | 1 Stk. | 0,00 € |
| 24 | Treiber-Transistor | BC547B, NPN, TO-92 | Berrybase | 1 Stk. | 0,17 € |
| 25 | Widerstand | 470 Ω Metallschicht (Datenleitung DIN) | Berrybase | 1 Stk. | 0,05 € |
| 26 | Widerstand | 4,7 kΩ Metallschicht (GPIO18 → Basis) | Berrybase | 1 Stk. | 0,06 € |
| 27 | Widerstände | 47 kΩ Metallschicht (Basis→GND, Gate→Source Q2) | Berrybase | 2 Stk. | 0,10 € |
| 28 | Widerstand | 10 kΩ Metallschicht (Gate→Source Q1) | Berrybase | 1 Stk. | 0,05 € |
| 29 | SOT-23-Adapter | SMD-Breakout-Adapter SOT23/SSOP10/MSOP10 | Berrybase | 2 Stk. | 0,64 € |
| 30 | Elko | 470 µF / 25 V, radial Ø 10 × 16 mm | Berrybase | 1 Stk. | 0,10 € |
| 31 | Lochrasterplatine | einseitig Kupfer, auf 30 × 24,5 mm zuschneiden | Berrybase | 1 Stk. | 1,10 € |
| 32 | Ein/Aus-Schalter | Schiebeschalter C&K OS102011MS2QN1 (ON-ON, Printmontage) | Berrybase | 1 Stk. | 0,70 € |
| 33 | Klemmkeile | gedruckt aus Pos. 21 (unter 1 g) | – | 2 Stk. | 0,00 € |
| 34 | Stiftleiste | 1 × 20-polig, RM 2,54 mm (für die SOT-23-Adapter) | Berrybase | 1 Stk. | 0,20 € |
| | **Summe Bauteile** | | | | **119,01 €** |
| | Versand (Amazon 0,00 € ab 49 €, Berrybase 4,95 €, Reichelt 5,95 €) | | | | 10,90 € |
| | Puffer 10 % (Verschnitt, Ersatz, unbekannter Versand) | | | | 11,90 € |
| | **Gesamt geplant** | | | | **141,81 €** |
| | Gesamt ohne PLA (falls die Schule druckt) | | | | 125,32 € |

**Hinweise zur Stückliste**

- **Versand:** Die Versandkosten von alleschrauben.de und AliExpress werden erst im Warenkorb angezeigt und sind noch nicht eingepreist. Der Puffer deckt sie ab.
- **AliExpress-Teile (Pos. 19/20):** Lieferzeit 1–3 Wochen. Pos. 19 entfällt, wenn beim CYD Kabel dabei sind. Pos. 20 entfällt, wenn direkt an die Lötpunkte gelötet wird.
- **LED-Streifen (Pos. 3):** Seit 08.10.2026 ein COB-Streifen statt des WS2812-ECO-Streifens mit sichtbaren Einzelpunkten (9,49 €, jetzt in der Vorkalkulation unter „Gestrichen“). Bei Amazon die Variante „1M 160LEDs/m 5mm“ wählen. Günstigste Alternative: AliExpress ab 7,59 € (Preis der Variante nicht lesbar). In die Datenleitung gehört ein Widerstand 330–470 Ω direkt am Streifen.
- **V4 (Pos. 5, 24–34):** Das GERUI-FET-Modul (Low-Side, 6,49 €) ist gestrichen. Stattdessen eine kleine FET-Platine mit 2 × AO3401A: Q1 schaltet die 5 V des LED-Streifens (über BC547B an GPIO18), Q2 ist der Akku-Schalter. Berrybase führt keinen P-MOSFET, deshalb kommt der AO3401A von Reichelt (eigener Versand 5,95 €). Schaltplan und Aufbau: [`gehaeuse/ANLEITUNG.md`](gehaeuse/ANLEITUNG.md) Kapitel 7b/7c.
- **Einkaufskörbe** (Einkaufsliste): schnell (DE-Shops) **111,04 €** + Versand alleschrauben.de, günstig (mit AliExpress) **94,98 €** – jeweils inkl. bekanntem Versand, ohne Puffer.
- **Widerstände (Pos. 14):** 2 × 10 kΩ statt 100 kΩ, weil 100 kΩ bei Berrybase nicht lieferbar ist. Das Teilerverhältnis ist gleich, die Firmware muss nicht angepasst werden.
- **Optional, nicht in der Summe:**
  - Elegoo Jumperkabel-Set (6,99 €), nur für einen Testaufbau auf dem Breadboard.
  - JST-PH-Verlängerung für den Akku (0,90 €).
- Weitere Kleinteile stehen in der [Anleitung](gehaeuse/ANLEITUNG.md#4-einkaufsliste-schrauben-und-kleinteile).

## 📁 Ordnerstruktur

```
hydrodesk-base/
├── doku/
│   ├── Steckbrief_HydroDesk_Base.docx      # Projekt-Steckbrief
│   ├── Einkaufsliste_HydroDesk_guenstig.xlsx  # Preisvergleich DE-Shops / AliExpress
│   ├── Stromsparplan_HydroDesk.md          # Stromsparen: Plan, Umsetzung V4, Laufzeit, Messplan
│   └── Vorkalkulation_HydroDesk_Base.xlsx  # Kostenkalkulation / Stückliste
├── design/
│   ├── claude_design_prompt_aufbau.md      # Prompt für Aufbau-/Teile-Illustrationen
│   ├── visualisierung/                     # Gerenderte Bilder: Explosion, Innen, Teile, Produkt
│   └── 3d_modell/                          # Komplettes 3D-Modell (GLB/STL/3MF) zum Anschauen
├── gehaeuse/
│   ├── hydrodesk_base.scad                 # Parametrisches OpenSCAD-Modell
│   ├── ANLEITUNG.md                        # Druck- und Montageanleitung
│   ├── QUELLEN.md                          # Quellen der Bauteil-Maße
│   ├── render.sh                           # Erzeugt die Vorschaubilder neu
│   ├── stl/                                # Druckfertige Teile: base, cover, pad, kappe_usb, diffusor_led, schalter_keile
│   └── preview/                            # Vorschaubilder
├── firmware/                               # PlatformIO-Firmware (folgt)
│   └── secrets.example.h                   # Vorlage für Zugangsdaten
├── wokwi/                                  # Wokwi-Simulation (Sketch, Diagramm, Anleitung)
├── app-android/                            # Android-App (Kotlin, Compose) – eigene Anleitung
│   ├── README.md                           # Einrichtung Schritt für Schritt (Supabase, Android Studio)
│   └── supabase/schema.sql                 # Datenbank-Schema mit Row Level Security
├── LICENSE
└── README.md
```

## 🗺️ Status / Roadmap

| Schritt | Status |
|---|---|
| Steckbrief | ✅ fertig |
| Vorkalkulation | ✅ fertig |
| Gehäuse-CAD (OpenSCAD, STL) | ✅ Version 4 (Ein/Aus-Schalter, FET-Platine) |
| Wokwi-Simulation | ✅ Version 4 fertig (alle Varianten kompiliert, PC-Logiktest OK, auf wokwi.com testen) – inkl. Bluetooth-Symbol, LED-Status und Stromsparmodus |
| Android-App (Kotlin, Compose, Supabase) | ✅ Version 1.0 – baut (`assembleDebug`), Unit-Tests grün, Demo-Modus; BLE mit echtem Gerät noch zu testen – siehe [`app-android/README.md`](app-android/README.md) |
| Firmware (PlatformIO) | ⏳ offen |
| Bau / Integration / Tests | ⏳ offen (Strommessungen nach Stromsparplan stehen noch aus) |

## 🔐 Zugangsdaten

WLAN-Daten und der optionale Telegram-Bot-Token kommen in `firmware/secrets.h` – diese Datei ist per `.gitignore` ausgeschlossen.
Als Vorlage dient [`firmware/secrets.example.h`](firmware/secrets.example.h).

Supabase-URL und -Key der App kommen in `app-android/local.properties` (ebenfalls nicht im Git),
Vorlage: [`app-android/local.properties.example`](app-android/local.properties.example).

## 👥 Team

| Person | Schwerpunkt |
|---|---|
| Person A | Hardware, Verkabelung, Wägezelle (HX711), Feuchtigkeitssensor, Stromversorgung, Gehäuse (CAD + 3D-Druck), Zustandsautomat |
| Person B | Touch-Display und Bedienoberfläche, WLAN/NTP, optionale Telegram-Anbindung, Kalibrierungs- und Preset-Logik, Doku-Leitung |

Gemeinsam: Planung, Integration, Tests, Bericht, Präsentation.

## 📄 Lizenz

[MIT](LICENSE) © 2026 bekuz007

Die Maßzeichnungen und Datenblätter Dritter, die für die Konstruktion verwendet wurden, sind nicht Teil dieses Repositorys – siehe [`gehaeuse/QUELLEN.md`](gehaeuse/QUELLEN.md).
