# HydroDesk Base – Gehäuse zum 3D-Drucken

Diese Anleitung erklärt alles, was du brauchst, um das Gehäuse drucken zu lassen und zusammenzubauen.
Du musst **nichts konstruieren**: Die STL-Dateien sind fertig zum Drucken.

---

## 1. Was ist was? (Dateien)

| Datei | Was ist das? | Wie oft drucken? |
|---|---|---|
| `stl/base.stl` | **Bodenwanne**: Boden mit allen Haltern, LED-Rille vorne, USB-Öffnungen hinten, Mulden für die Gummifüße | **1×** |
| `stl/cover.stl` | **Deckel**: mit Display-Fenster und Öffnung für das Pad | **1×** |
| `stl/pad.stl` | **Flaschen-Pad**: 90 × 90 mm Platte, liegt nur auf der Wägezelle | **1×** |
| `stl/kappe_usb.stl` | **Abdeckkappe**: steckbarer Deckel für die breite USB-Öffnung des Displays hinten (Programmier-Anschluss) | **1×** (am besten 2×, falls eine verloren geht) |
| `hydrodesk_base.scad` | Die „Bauzeichnung“ für OpenSCAD. Hier stehen alle Maße oben als Zahlen. Nur nötig, wenn etwas geändert werden muss. | – |
| `preview/*.png` | Vorschaubilder (Zusammenbau, Explosionsansicht, Draufsicht, Einzelteile, Abdeckkappe `kappe_eingesteckt.png` / `kappe_offen.png`) | – |
| `QUELLEN.md` | Links zu den Maßzeichnungen/Datenblättern, die für die Konstruktion benutzt wurden (CYD, Wägezelle) | – |
| `render.sh` | Skript, das die Vorschaubilder neu erzeugt (nur für Fortgeschrittene) | – |

**Abstandshalter für die Wägezelle musst du nicht extra drucken** – sie sind schon eingebaut
(Sockel im Boden + Sockel unter dem Pad).

---

## 2. Maße des fertigen Geräts

* **180 mm breit × 100 mm tief × 25 mm hoch** (mit Gummifüßen ca. 3 mm höher)
* Links: Display (Hochformat), rechts: Flaschen-Pad 90 × 90 mm
* Höhe 25 mm statt 20 mm, weil die Wägezelle allein schon 12,7 mm hoch ist:
  Boden 2 + Sockel 3 + Wägezelle 12,7 + Pad 4,6 + Tropfrand 2,3 = 24,6 mm.
  Mit 20 mm geht es nicht.
* Tiefe 100 mm statt 95 mm, weil das Pad 90 mm groß ist und rundherum 1 mm Luft
  und ein Deckelrand von 4 mm gebraucht werden (90 + 2 + 8 = 100).

---

## 3. Druckeinstellungen (für dich oder für die Druckerei)

Für alle Teile gilt:

| Einstellung | Wert |
|---|---|
| Material | **PLA** |
| Düse | 0,4 mm |
| Schichthöhe | **0,2 mm** |
| Füllung (Infill) | **20 %** |
| Wände (Perimeter) | **3** |
| Stützmaterial (Supports) | **Nein** – bei keinem Teil nötig |
| Druckbett-Haftung | normal (kein Brim nötig; bei Problemen Brim 5 mm) |

Wie die Teile auf dem Druckbett liegen – **die STL-Dateien sind schon richtig gedreht**, einfach so lassen:

| Teil | Lage auf dem Druckbett | Supports | Geschätzte Druckzeit* | Filament* |
|---|---|---|---|---|
| base | Boden nach unten (offene Seite oben) | nein | ca. 5 h 12 min | ca. 78 g |
| cover | **Oberseite nach unten** (schöne glatte Sichtfläche) | nein | ca. 1 h 06 min | ca. 16 g |
| pad | flache Unterseite nach unten, Rand oben | nein | ca. 1 h 26 min | ca. 27 g |
| kappe_usb | **Sichtseite (Flansch) nach unten**, Stopfen zeigt nach oben | nein | ca. 10 min** | ca. 1 g** |

\* Schätzung von PrusaSlicer 2.9 mit einem allgemeinen PLA-Profil (0,2 mm, 20 %, 3 Wände).
Dein Drucker kann schneller oder langsamer sein.
\*\* Kappe: grob aus dem Volumen geschätzt (0,57 cm³), nicht gesliced.

Hinweise:
* Der Boden ist 180 × 100 mm groß → das Druckbett muss mindestens ca. 190 × 110 mm haben (fast alle Drucker schaffen das).
* Unter dem Pad gibt es einen 15 mm breiten Kanal (über der Wägezelle). Das ist eine kurze „Brücke“ und
  druckt ohne Stützen. Falls ein Slicer davor warnt: ignorieren.

---

## 4. Einkaufsliste (Schrauben und Kleinteile)

| Anzahl | Teil | Wofür |
|---|---|---|
| 8 | **M3 × 12 Senkkopfschraube** (DIN 965 / ISO 7046, Kreuz oder Torx) | Deckel festschrauben. 4 davon gehen durch die Ecklöcher des Displays in die Abstandshalter und halten das Display gleich mit fest. |
| 2 | **M5 × 12 Senkkopfschraube** (DIN 7991, Innensechskant) | Wägezelle von **unten** am Boden festschrauben (feste Seite, M5-Löcher) |
| 2 | **M4 × 10 Senkkopfschraube** (DIN 7991, Innensechskant) | Pad von **oben** an der Wägezelle festschrauben (freie Seite, M4-Löcher) |
| 4 | **Gummifüße selbstklebend, Ø 12 mm** (max. 13 mm) | in die runden Mulden unten kleben |
| 1 | Silikonmatte, **auf 86 × 86 mm zuschneiden** (1–1,5 mm dick) | oben in das Pad kleben (innerhalb des Rands) |
| – | Doppelseitiges Klebeband (Schaumstoff) und/oder Heißkleber | Akku, Module, LED-Streifen festkleben |
| – | Kabelbinder (klein), dünne Litze | Kabel ordnen |

Die M3-Schrauben drehen sich selbst ein Gewinde in den Kunststoff (Löcher 2,5 mm).
**Nicht zu fest anziehen**, sonst dreht das Gewinde im PLA durch.
(Wer lieber Gewindeeinsätze zum Einschmelzen benutzt: in der .scad-Datei `screw_pilot = 4.0` setzen
und neu exportieren – oder den Assistenten darum bitten.)

---

## 5. VOR dem Drucken: Bauteile nachmessen!

Händler-Angaben stimmen nicht immer. Bitte mit einem **Messschieber** nachmessen und mit dieser Tabelle vergleichen.
Wenn etwas um mehr als ca. 0,5 mm abweicht: die Zahl oben in `hydrodesk_base.scad` ändern
(oder dem Assistenten die gemessenen Werte schicken – er passt es an).

| Bauteil | Benutzte Maße | Parameter in der .scad |
|---|---|---|
| CYD ESP32-2432S028R (Platine) | 50 × 86 mm, 4 Löcher Ø 3,2 mm im Abstand **42 × 78 mm** (4 mm vom Rand) | `cyd_w`, `cyd_l`, `cyd_hole_in` |
| CYD Dicke | Bauteile hinten 4,7 mm + Platine 1,5 mm + Display/Touch 3,6 mm = 9,8 mm | `cyd_back_h`, `cyd_pcb_t`, `cyd_front_h` |
| CYD sichtbare Fläche | 43,2 × 57,6 mm, Mitte ca. 3,5 mm vom Platinen-Mittelpunkt weg vom USB-Ende | `cyd_aa_*`, `cyd_aa_shift` |
| CYD USB-Buchse(n) | an der kurzen Seite; Öffnung hinten 32 × 7,6 mm (passt für Micro-USB **und** USB-C) | `cyd_usb_w`, `cyd_usb_h` |
| Akku EEMB 2000 mAh (LP103454) | 34,5 × 56 × 10,3 mm (Datenblatt: 34,5 × 55 × 10,3, mit Kabelende 56) | `bat_w`, `bat_l`, `bat_h` |
| TC4056 USB-C Lader | 17 × 26 mm, USB-C mittig an der kurzen Kante | `tc_w`, `tc_l` |
| Wägezelle 5 kg | 80 × 12,7 × 12,7 mm; Löcher 5 mm und 20 mm von jedem Ende; 2× M4 an einem Ende, 2× M5 am anderen | `lc_*` |
| HX711 | 34 × 21 mm (kleinere Versionen passen auch) | `hx_w`, `hx_l` |
| MOSFET-Modul | 30 × 17 mm | `mos_w`, `mos_l` |
| Boost-Wandler MT3608 (optional) | 37 × 17 mm, max. ca. 8 mm hoch | `boost_w`, `boost_l` |
| Regensensor FC-37 / YL-83 | 40 × 54 mm | `rs_w`, `rs_l` |
| Regensensor-Auswertemodul (LM393) | 16 × 30 mm | `cmp_w`, `cmp_l` |
| LED-Streifen WS2812 | 10 mm breit, 10 LEDs bei 60 LED/m = 167 mm lang | `led_*` |

**Besonders wichtig beim CYD:** Prüfe, wo genau die USB-Buchse(n) sitzen und wie tief die Bauteile auf der
Rückseite sind. Die Öffnung hinten ist absichtlich breit, damit beide bekannten Varianten passen.

---

## 6. Wo sitzt was? (Innen, von oben gesehen)

* **Linke Zone:** CYD-Display auf 4 Abstandshaltern, USB-Buchse zeigt **nach hinten** (zum Programmieren erreichbar).
  **Unter** dem Display: der Akku (hinten) und der Boost-Wandler (vorne).
* **Streifen zwischen Display und Pad:** TC4056-Lader an der Rückwand (USB-C zum Laden zeigt nach hinten),
  davor das MOSFET-Modul, ganz vorne das Auswertemodul des Regensensors.
* **Rechte Zone (unter dem Pad):** Wägezelle längs (von vorne nach hinten) in der Mitte,
  rechts daneben der HX711, links daneben der Regensensor in einer flachen Mulde.
* Zwischen den Zonen gibt es keine Trennwand → Kabel können frei verlegt werden.
* Hinten gibt es also **zwei** Öffnungen: links die breite für das CYD (Programmieren),
  rechts daneben die kleine USB-C-Öffnung für den Lader.
  Die kleine Öffnung hat außen eine Mulde, damit auch dicke Stecker ganz hineinpassen.
* Die breite CYD-Öffnung wird im fertigen Gerät mit der **Abdeckkappe** verschlossen (siehe Abschnitt 7a).
  Zum Programmieren Kappe abziehen, danach wieder einstecken. Die USB-C-Ladebuchse bleibt immer offen.

**Wasser-Erkennung (einfache Lösung):** Das Pad hat einen Tropfrand. Auf der linken Seite (zum Display hin)
hat der Rand eine kleine **Kerbe**. Läuft Wasser auf dem Pad über, läuft es dort ab, tropft durch den
**3-mm-Schlitz** im Deckel direkt auf den **Regensensor**, der darunter in einer Mulde im Boden liegt.
Der Sensor meldet „nass“ → das ESP32 kann warnen. Danach Sensor und Mulde trocken wischen.
Tipp: Beim Regensensor die Stiftleiste abgewinkelt lassen oder Kabel direkt anlöten (nicht höher als ca. 12 mm).

---

## 7. Zusammenbau – Schritt für Schritt

1. **Drucken** und Teile säubern (Fäden entfernen).
2. **Gummifüße** unten in die 4 runden Mulden kleben.
3. **Wägezelle einbauen:** Die Seite mit dem **Kabel und den M5-Löchern** kommt **hinten** auf den Sockel im Boden.
   Von **unten** mit 2× M5 × 12 Senkkopf festschrauben. Der Pfeil auf der Wägezelle muss **nach unten** zeigen.
   Die vordere Hälfte der Zelle darf den Boden nicht berühren (ca. 3 mm Luft).
4. **HX711** rechts neben die Wägezelle kleben (Anschläge im Boden zeigen den Platz), Kabel anlöten.
5. **Regensensor** in die flache Mulde links neben der Wägezelle legen und mit wenig Heißkleber an den Ecken fixieren.
   Das LM393-Modul vorne in den Streifen kleben.
6. **TC4056** von vorne zwischen die beiden Leisten an der Rückwand schieben, bis die USB-C-Buchse in der Öffnung sitzt.
   Mit einem Tropfen Heißkleber sichern. **MOSFET-Modul** davor kleben.
7. **Akku** hinten links in die Anschläge legen (doppelseitiges Klebeband), **Boost-Wandler** davor.
   Akku-Kabel zum TC4056 führen. Achtung Polarität!
8. **LED-Streifen** (10 LEDs) vorne in die Rille kleben (der Streifen hat meist schon Klebeband).
   Das Kabel geht am **linken Ende** durch das kleine Loch nach innen.
9. Alle Kabel an das **CYD** anstecken (Stecker P3, CN1, P1 usw. sitzen auf der Rückseite an den Längskanten –
   neben dem Akku ist dafür Platz). Kabel mit Kabelbindern ordnen.
10. **CYD** mit dem Bildschirm nach oben und der USB-Buchse nach hinten auf die 4 Abstandshalter legen.
11. **Deckel** auflegen (der Rand innen zentriert ihn). Mit 8× M3 × 12 Senkkopf festschrauben:
    4 Schrauben gehen durch die Ecklöcher des CYD in die Abstandshalter, 4 in die Dome im Boden.
    **Gefühlvoll anziehen.**
12. **Pad** von oben in die Öffnung legen. Die zwei Senklöcher müssen vorne über den M4-Löchern der Wägezelle liegen.
    Mit 2× M4 × 10 Senkkopf festschrauben. Prüfen: Das Pad darf **nirgends** den Deckel berühren
    (rundherum ca. 1 mm Spalt) – sonst misst die Waage falsch.
13. **Silikonmatte** auf 86 × 86 mm zuschneiden und innen in das Pad kleben (deckt die Schraubenköpfe ab).
14. **Abdeckkappe** hinten in die breite USB-Öffnung drücken, bis der Flansch an der Wand anliegt
    (die Kerbe im Flansch zeigt nach **unten**).
15. Fertig! Waage in der Software tarieren und kalibrieren (z. B. mit einer vollen 0,5-l-Flasche = ca. 500 g Wasser + Flasche).

### 7a. Abdeckkappe für den USB-Anschluss

| Maß | Wert |
|---|---|
| Flansch (außen sichtbar) | 35 × 10,6 mm, 1,2 mm dick, Ecken R 3,5, Kante 0,5 mm gefast – steht 1,2 mm über die Rückwand |
| Stopfen (steckt in der Wand) | 31,7 × 7,3 mm, 2,2 mm tief, hohl mit 1 mm Wand |
| Spiel Stopfen ↔ Öffnung (32 × 7,6 mm) | **0,15 mm je Seite** |
| Halt | 10 Quetschrippen (4 oben, 4 unten, je 1 links/rechts), 0,3 mm hoch → **0,15 mm Übermaß** je Seite; die Rippen drücken sich beim ersten Einstecken etwas zusammen und klemmen die Kappe |
| Abziehen | Kerbe 8 mm breit unten in der Flansch-Rückseite: Fingernagel hineinstecken und Kappe heraushebeln |
| Abstand zur USB-Buchse | Der Stopfen endet 0,2 mm **vor** der Wand-Innenseite und ist hohl. Die Buchse(n) liegen in der Höhe innerhalb des Hohlraums → keine Berührung (in OpenSCAD geprüft: `part = "cap_check_cyd"` ist leer) |

**Erst eine Kappe zur Probe drucken!** Jeder Drucker druckt etwas anders.
* Kappe zu locker → in der .scad `cap_rib_h` auf 0.35–0.4 erhöhen (mehr Übermaß).
* Kappe zu stramm → `cap_rib_h` auf 0.2 senken oder `cap_clr` auf 0.2 erhöhen.
* Eine Außenmulde für einen bündigen Flansch gibt es absichtlich nicht: Die Rückwand ist nur 2,4 mm dick,
  daneben blieben bei der breiten Öffnung nur ca. 1 mm Material stehen.

---

## 8. Drucken lassen – so geht’s

**Möglichkeit A – Schule / FabLab / Makerspace (meist am günstigsten):**
Die vier Dateien `base.stl`, `cover.stl`, `pad.stl`, `kappe_usb.stl` auf einen USB-Stick kopieren und diese Anleitung
(Abschnitt 3 Druckeinstellungen) zeigen. Material: PLA.

**Möglichkeit B – Craftcloud (craftcloud3d.com):**
1. Webseite öffnen → „Upload“ und die vier STL-Dateien hochladen.
2. Material wählen: **PLA** (Verfahren FDM). Farbe nach Wunsch (z. B. Hellgrau / Weiß, Pad Blau).
3. Anzahl jeweils **1**.
4. Die Seite zeigt nun Angebote verschiedener Druckereien mit Preis und Lieferzeit → vergleichen und bestellen.

**Möglichkeit C – JLC3DP (jlc3dp.com):**
1. „Upload“ / „Instant Quote“ → STL-Dateien hochladen.
2. Verfahren **FDM**, Material **PLA** wählen.
3. Der Preis wird nach dem Hochladen angezeigt. Versandkosten und Lieferzeit (aus China) beachten.

Preise werden erst **nach dem Hochladen** angezeigt – sie hängen von Material, Farbe, Anbieter und Versand ab.

---

## 9. Etwas ändern? (nur bei Bedarf)

1. OpenSCAD installieren (kostenlos, openscad.org).
2. `hydrodesk_base.scad` öffnen. Oben stehen alle Maße mit Kommentaren.
3. Zahl ändern → **F6** (Rendern) → `Datei > Exportieren > STL`.
4. Ganz oben `part = "base";` (oder `"cover"`, `"pad"`, `"cap"`) einstellen, um das jeweilige Teil zu exportieren.
   `"assembly"` zeigt alles zusammengebaut, `"exploded"` die Explosionsansicht, `"inside"` das Innere ohne Deckel,
   `"section"` einen Schnitt. `cap_pull = 14` zieht die Abdeckkappe in der Vorschau heraus.

Oder einfach dem Assistenten die gemessenen Werte schicken – er erzeugt neue STL-Dateien.

---

## 10. Quellen der Maße

* CYD-Maßzeichnung und 3D-Modell: github.com/witnessmenow/ESP32-Cheap-Yellow-Display
  (`OriginalDocumentation/3-Structure_Diagram/Dimensions.png`, `3dModels/Havenview_CYD_CAD/Cheap Yellow Display v16.step`)
* Wägezelle: Datenblatt TAL220 (SparkFun, HTC Sensor) – 80 × 12,7 × 12,7 mm, Löcher bei 5/20 mm, 2× M4 + 2× M5
* Akku: Datenblatt EEMB LP103454 (2000 mAh): 34,5 × 55 (56) × 10,3 mm
