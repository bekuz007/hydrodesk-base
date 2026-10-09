# HydroDesk Base – Gehäuse zum 3D-Drucken

Diese Anleitung erklärt alles, was du brauchst, um das Gehäuse drucken zu lassen und zusammenzubauen.
Du musst **nichts konstruieren**: Die STL-Dateien sind fertig zum Drucken.

---

## 1. Was ist was? (Dateien)

| Datei | Was ist das? | Wie oft drucken? |
|---|---|---|
| `stl/base.stl` | **Bodenwanne**: Boden mit allen Haltern, Lichtkammer für den LED-Streifen vorne (mit Falz für den Diffusor), USB-Öffnungen hinten, Mulden für die Gummifüße | **1×** |
| `stl/cover.stl` | **Deckel**: mit Display-Fenster und Öffnung für das Pad | **1×** |
| `stl/pad.stl` | **Flaschen-Pad**: 90 × 90 mm Platte, liegt nur auf der Wägezelle | **1×** |
| `stl/kappe_usb.stl` | **Abdeckkappe**: steckbarer Deckel für die breite USB-Öffnung des Displays hinten (Programmier-Anschluss) | **1×** (am besten 2×, falls eine verloren geht) |
| `stl/diffusor_led.stl` | **Diffusor-Leiste**: 166,7 × 16,7 × 1 mm, wird vorne in den Falz vor den LED-Streifen gesetzt und macht aus den einzelnen LEDs eine gleichmäßige Lichtlinie | **1×** (weißes PLA oder naturfarbenes PETG, siehe Abschnitt 3) |
| `stl/schalter_keile.stl` | **2 Klemmkeile** (je 7,6 mm lang, 1,1 mm dick) für den Ein/Aus-Schalter: werden von oben hinter den Schalter gedrückt und halten ihn in seiner Tasche (Abschnitt 7b) | **1×** (= 2 Keile; am besten 2× drucken, dann hast du Ersatz) |
| `hydrodesk_base.scad` | Die „Bauzeichnung“ für OpenSCAD. Hier stehen alle Maße oben als Zahlen. Nur nötig, wenn etwas geändert werden muss. | – |
| `preview/*.png` | Vorschaubilder (Zusammenbau, Explosionsansicht, Draufsicht, Einzelteile, Abdeckkappe `kappe_eingesteckt.png` / `kappe_offen.png`, Diffusor `17_teil_diffusor_druckLage.png`, `diffusor_eingesetzt.png`, `diffusor_offen.png`, Schnitt durch die Lichtkammer `18_led_kammer_schnitt.png`, Klemmkeile `19_teil_keile_druckLage.png`, Ein/Aus-Schalter von außen `20_schalter_links_aussen.png`, Schnitt durch die Schaltertasche `21_schalter_tasche_schnitt.png`, Tasche mit Schalter und Keilen `22_schalter_tasche_innen.png`, Einsetzen `23_schalter_einsetzen.png`, FET-Platine `24_fet_platine.png`) | – |
| `quellen/` | Maßzeichnungen, die für die Konstruktion benutzt wurden (CYD, Wägezelle) | – |
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

Für alle Teile gilt (Ausnahme Diffusor, siehe unten):

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
| base | Boden nach unten (offene Seite oben) | nein | ca. 5 h 20 min*** | ca. 80 g*** |
| cover | **Oberseite nach unten** (schöne glatte Sichtfläche) | nein | ca. 1 h 06 min | ca. 16 g |
| pad | flache Unterseite nach unten, Rand oben | nein | ca. 1 h 26 min | ca. 27 g |
| kappe_usb | **Sichtseite (Flansch) nach unten**, Stopfen zeigt nach oben | nein | ca. 10 min** | ca. 1 g** |
| diffusor_led | **flach** liegend (1 mm dünne Platte) | nein | ca. 15 min** | ca. 4 g** |
| schalter_keile | **flach** liegend (die Keilform ist von oben zu sehen) | nein | ca. 5 min** | unter 1 g** |

\* Schätzung von PrusaSlicer 2.9 mit einem allgemeinen PLA-Profil (0,2 mm, 20 %, 3 Wände).
Dein Drucker kann schneller oder langsamer sein.
\*\* Kappe und Diffusor: grob aus dem Volumen geschätzt (Kappe 0,57 cm³, Diffusor 2,78 cm³ bei 100 % Füllung), nicht gesliced.
\*\*\* Bodenwanne mit der neuen Lichtkammer: aus dem Volumen hochgerechnet (+4,5 % gegenüber der gesliceten Version), nicht neu gesliced.
Die Schaltertasche (V4) macht die Bodenwanne noch einmal um 0,51 cm³ (+0,7 %) schwerer – das ändert an Zeit und Gewicht praktisch nichts.
Keile: 0,1 cm³ zusammen, ebenfalls nur aus dem Volumen geschätzt.

**Klemmkeile – Hinweise:** Die Teile sind sehr klein. Am besten zusammen mit der Abdeckkappe drucken,
Füllung egal (sie sind so dünn, dass sie ohnehin massiv werden). Falls sie sich vom Bett lösen: Brim 3 mm.

**Diffusor-Leiste – andere Einstellungen:**
* Material **weißes PLA** oder **naturfarbenes (milchiges) PETG** – kein farbiges oder schwarzes Filament, sonst kommt kein Licht durch.
* **1,0 mm dick, 100 % Füllung** (Infill 100 %), damit das Licht gleichmäßig durchscheint und keine Wabenmuster zu sehen sind.
* Flach auf das Druckbett legen (die STL liegt schon richtig). Die Seite, die auf dem Druckbett lag, ist glatter → sie zeigt später nach außen.

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
| – | Doppelseitiges Klebeband (Schaumstoff) und/oder Heißkleber | Akku, Module, LED-Streifen festkleben; 2–4 kleine Klebepunkte (Glue Dots) für den Diffusor |
| – | Kabelbinder (klein), dünne Litze | Kabel ordnen |
| 1 | **Widerstand 470 Ω** (330–470 Ω geht) | in die Datenleitung direkt am Streifen-Eingang (DIN) löten |
| 1 | **Schiebeschalter C&K OS102011MS2QN1** (1× Um, 8,6 × 4,3 mm, Raster 2 mm) | Ein/Aus-Schalter in der linken Wand (Abschnitt 7b) |
| 1 | **Lochrasterplatine** (zuschneiden auf 30 × 24,5 mm) + Bauteile der Schaltung aus Abschnitt 7c | FET-Platine: LED-Strom-Schalter (H1) und Akku-Schalter (H2) |

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
| FET-Platine (Lochraster, selbst gelötet) | **30 × 24,5 mm**, 1,6 mm dick, liegt auf 1,5 mm hohen Leisten; höchstes Bauteil der stehende SOT-23-Adapter / BC547B, der Elko (Ø 10 × 16 mm) liegt | `mos_w`, `mos_l`, `fb_*`, `elko_*` |
| Ein/Aus-Schalter C&K OS102011MS2QN1 | Gehäuse 8,6 × 4,3 mm, **Höhe 4,0 mm angenommen** (Datenblatt-Zeichnung unklar: 3,5–4,7 mm, Händler: 4 mm), Schieber 2,0 × 2,0 mm, 4,0 mm hoch, Weg 2,0 mm | `sw_l`, `sw_w`, `sw_h`, `sw_act*` |
| 5-V-Wandler Pololu S13V10F5 | 12,1 × 8,9 × 4,2 mm (das Fach ist 37 × 17 mm groß, der Wandler wird darin mit Klebeband fixiert) | `pol_w`, `pol_l`, `pol_h` (Fach: `boost_w`, `boost_l`) |
| Regensensor FC-37 / YL-83 | 40 × 54 mm | `rs_w`, `rs_l` |
| Regensensor-Auswertemodul (LM393) | 16 × 30 mm | `cmp_w`, `cmp_l` |
| COB-LED-Streifen BTF-LIGHTING WS2812B FCOB (5 V, 160 LEDs/m) | **5 mm breit**, 13 Segmente à 12,5 mm = **162,5 mm lang, 26 LEDs**; Dicke mit Klebeband **2,5 mm angenommen** | `cob_w`, `cob_len`, `cob_t` |
| Diffusor-Leiste (gedruckt) | 1,0 mm dick; Falz in der Lichtkammer 1,2 mm tief | `diff_t`, `falz_t` |

**Besonders wichtig beim CYD:** Prüfe, wo genau die USB-Buchse(n) sitzen und wie tief die Bauteile auf der
Rückseite sind. Die Öffnung hinten ist absichtlich breit, damit beide bekannten Varianten passen.

**Besonders wichtig beim COB-Streifen:** Die Dicke `cob_t` (Streifen + Klebeband) ist mit 2,5 mm als ungünstigster Fall
angenommen – **nach Lieferung nachmessen!** Aus `cob_t` wird die Tiefe der Lichtkammer berechnet
(`led_d` = Falz 1,2 + Mischabstand 2,0 + `cob_t` = 5,7 mm). Ist der Streifen dünner, wird der Abstand zum Diffusor
etwas größer – das schadet nicht, das Licht wird nur noch gleichmäßiger.

**Besonders wichtig beim Ein/Aus-Schalter:** Die Gehäusehöhe `sw_h` (Wand → Rückseite mit den Pins) **nachmessen**.
Die Keile gleichen bis ca. 0,5 mm Unterschied aus (bei 3,5 mm sitzen sie 1,5 mm tiefer, bei mehr als 4,3 mm passen sie nicht
mehr) – bei größerer Abweichung `sw_h` ändern und Bodenwanne + Keile neu exportieren.

---

## 6. Wo sitzt was? (Innen, von oben gesehen)

* **Linke Zone:** CYD-Display auf 4 Abstandshaltern, USB-Buchse zeigt **nach hinten** (zum Programmieren erreichbar).
  **Unter** dem Display: der Akku (hinten) und der 5-V-Wandler Pololu S13V10F5 (vorne, im Fach 37 × 17 mm).
* **Streifen zwischen Display und Pad:** TC4056-Lader an der Rückwand (USB-C zum Laden zeigt nach hinten),
  davor die **FET-Platine** (30 × 24,5 mm, Elko rechts liegend), ganz vorne das Auswertemodul des Regensensors.
* **Linke Wand vorne (Y = 27 mm, zwischen den Anschlägen des Wandler-Fachs):** der **Ein/Aus-Schalter** in seiner Tasche.
  Außen sieht man nur den Schieber im Schlitz 2,6 × 4,6 mm, darüber eingraviert **„AN“**, darunter **„AUS“**.
  Schieber **oben = AN**. Er sitzt weit weg vom Pad, damit kein Wasser hinkommt.
* **Rechte Zone (unter dem Pad):** Wägezelle längs (von vorne nach hinten) in der Mitte,
  rechts daneben der HX711, links daneben der Regensensor in einer flachen Mulde.
* **Vorne über die ganze Breite:** die Lichtkammer (167 mm lang, 5,7 mm tief). Der COB-LED-Streifen klebt an ihrer
  Rückwand, vorne sitzt die Diffusor-Leiste im Falz. Alle Module halten dazu Abstand (in OpenSCAD geprüft:
  `part = "parts_check"`, `part = "diff_check"` und `part = "keil_check"` sind leer).
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
   Mit einem Tropfen Heißkleber sichern. Die fertig gelötete **FET-Platine** (Abschnitt 7c) davor auf die zwei Leisten legen
   und mit doppelseitigem Klebeband fixieren (der liegende Elko zeigt nach rechts, weg vom Display).
   **Ein/Aus-Schalter** mit angelöteten Litzen einsetzen und mit den 2 Klemmkeilen sichern (Abschnitt 7b).
7. **Akku** hinten links in die Anschläge legen (doppelseitiges Klebeband), den **5-V-Wandler (Pololu S13V10F5)** davor ins Fach kleben.
   Akku-Kabel zum TC4056 führen. Achtung Polarität!
8. **COB-LED-Streifen** (26 LEDs = 13 Segmente, 162,5 mm; nur an den markierten Schnittstellen alle 12,5 mm schneiden)
   vorbereiten: 3 Litzen (5 V, GND, Daten) an den **Eingang** (Pfeil zeigt vom Kabel weg) löten,
   in die Datenleitung direkt am Streifen einen **Widerstand 470 Ω** setzen.
   Die 5-V-Litze kommt später an den **Drain von Q1** auf der FET-Platine (nicht direkt an den Wandler), siehe 7c.
   Den Streifen mit seinem Klebeband an die **Rückwand der Lichtkammer** kleben, mittig (links und rechts je ca. 2 mm Platz),
   die LEDs zeigen nach vorne.
   Die Kabel gehen **um das linke Streifenende herum** durch das kleine Loch (Ø 5 mm) nach innen –
   das Loch liegt direkt hinter dem Streifenanfang, deshalb die Litzen vor dem Aufkleben durchstecken.
9. **Diffusor-Leiste** vorne in den Falz setzen (glatte Seite nach außen): 2–4 kleine Klebepunkte (Glue Dots) oder
   ein Hauch Kleber an den Rand, dann leicht andrücken. Sie liegt 0,2 mm vertieft in der Front.
   Wenn sie ohne Kleber stramm sitzt, reicht leichtes Eindrücken.
10. Alle Kabel an das **CYD** anstecken (Stecker P3, CN1, P1 usw. sitzen auf der Rückseite an den Längskanten –
   neben dem Akku ist dafür Platz). Kabel mit Kabelbindern ordnen.
11. **CYD** mit dem Bildschirm nach oben und der USB-Buchse nach hinten auf die 4 Abstandshalter legen.
12. **Deckel** auflegen (der Rand innen zentriert ihn). Mit 8× M3 × 12 Senkkopf festschrauben:
    4 Schrauben gehen durch die Ecklöcher des CYD in die Abstandshalter, 4 in die Dome im Boden.
    **Gefühlvoll anziehen.**
13. **Pad** von oben in die Öffnung legen. Die zwei Senklöcher müssen vorne über den M4-Löchern der Wägezelle liegen.
    Mit 2× M4 × 10 Senkkopf festschrauben. Prüfen: Das Pad darf **nirgends** den Deckel berühren
    (rundherum ca. 1 mm Spalt) – sonst misst die Waage falsch.
14. **Silikonmatte** auf 86 × 86 mm zuschneiden und innen in das Pad kleben (deckt die Schraubenköpfe ab).
15. **Abdeckkappe** hinten in die breite USB-Öffnung drücken, bis der Flansch an der Wand anliegt
    (die Kerbe im Flansch zeigt nach **unten**).
16. Fertig! Waage in der Software tarieren und kalibrieren (z. B. mit einer vollen 0,5-l-Flasche = ca. 500 g Wasser + Flasche).

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

### 7b. Ein/Aus-Schalter einsetzen

Warum ein Schalter? Der 5-V-Wandler (Pololu S13V10F5) hat **keinen Enable-Eingang** und braucht auch ohne Last ca. 9–10 mA.
Ohne Schalter wäre der Akku auch im „Tiefschlaf“ nach einigen Tagen leer. Der kleine Schiebeschalter schaltet aber
**nicht** den Akku-Strom selbst (er verträgt nur 0,1 A), sondern nur das Gate eines P-MOSFET (Q2, Abschnitt 7c).
Durch den Schalter fließen nur ca. 0,08 mA.

| Maß | Wert |
|---|---|
| Position | linke Wand, 27 mm von der Vorderkante (Mitte), Unterkante Schalter 3 mm über dem Boden |
| Schlitz außen | 2,6 × 4,6 mm (Schieber 2,0 mm + 2 × 0,3 mm Spiel, Weg 2,0 mm), Ecken R 0,6 |
| Beschriftung | „AN“ über, „AUS“ unter dem Schlitz, 2,8 mm hoch, 0,5 mm tief eingraviert |
| Tasche | Seitenwangen 1,2 mm, Stufe 1 mm (Schalter liegt darauf), 0,3 mm Spiel je Seite; 2 Pfosten mit Gegenschräge 1 : 3 |
| Halt | 2 Klemmkeile (Steigung 1 : 3) zwischen Schalter-Rückseite und Pfosten; Mitte (Pins, Litzen) bleibt frei |

Schritte:
1. **Mit dem Durchgangsprüfer** (Multimeter) herausfinden, welcher äußere Pin mit dem mittleren verbunden ist,
   wenn der Schieber **oben** steht (= später „AN“). Diesen Pin markieren.
2. 3 Litzen (ca. 8 cm) anlöten, Lötstellen mit Schrumpfschlauch isolieren. Die zwei Befestigungslaschen nicht abbrechen.
3. Schalter mit dem Schieber **zur Wand** von oben in die Tasche setzen (ca. 4,4 mm vor der Wand auf die Stufe),
   dann **zur Wand schieben**, bis der Schieber außen durch den Schlitz schaut. Der Schieber muss **oben** bei „AN“
   und **unten** bei „AUS“ einrasten. Die Litzen zeigen nach innen (zwischen den beiden Pfosten durch).
4. Die 2 Klemmkeile von oben zwischen Schalter-Rückseite und Pfosten drücken (dünnes Ende nach unten, schräge Seite
   zum Pfosten), bis sie stramm sitzen. Sie halten den Schalter gegen die Wand; nach oben halten ihn Stufe und Schlitz
   (0,3 mm Spiel). Kein Kleber nötig – so kann der Schalter getauscht werden (Keile mit einer Pinzette herausziehen).
5. Schalter wackelt noch → Keile mit einem Tropfen Sekundenkleber an den Pfosten sichern, oder `k_k`/`k_z0` im .scad anpassen.

Alle Wege sind in OpenSCAD geprüft (Einsetzen, Schieben, Keile eindrücken, Schieber in Stellung „AUS“: keine Berührung).
Die Gehäusehöhe des Schalters ist aber nur angenommen (4,0 mm) → **vorher nachmessen** (Abschnitt 5).

### 7c. Schaltung FET-Platine (LED-Strom H1 + Ein/Aus H2)

Gelötet auf ein Stück Lochraster (30 × 24,5 mm). Die zwei AO3401A sind sehr klein (SOT-23) → jeweils auf einen
**SOT-23-Adapter** löten, dann wie ein normales Bauteil einstecken. Anschlüsse AO3401A (SOT-23): **1 = Gate, 2 = Source,
3 = Drain**. BC547B (TO-92, flache Seite zu dir, Beine unten): **C – B – E**.

**H2 – Ein/Aus (Akku → Rest des Geräts):**

| Von | Nach |
|---|---|
| TC4056 **OUT+** | **Source Q2** (AO3401A) |
| **Drain Q2** | Pololu **VIN** und oberer Widerstand des Akku-Teilers (2 × 10 kΩ, Mitte → GPIO35) |
| 47 kΩ | zwischen **Gate Q2** und **Source Q2** (hält Q2 aus, solange der Schalter umschaltet) |
| Schalter **Mitte** | **Gate Q2** |
| Schalter Außenpin „**AN**“ (Schieber oben) | **GND** (TC4056 OUT−) → Gate auf GND → Q2 leitet |
| Schalter Außenpin „**AUS**“ (Schieber unten) | **Source Q2** → Gate = Source → Q2 sperrt sicher |
| TC4056 **OUT−** | gemeinsames GND (Pololu, CYD, HX711, Streifen, Regensensor) |

* AUS: Wandler, CYD **und der Akku-Teiler** sind stromlos. Die Body-Diode von Q2 zeigt vom Gerät zum Akku und sperrt.
* Laden geht in beiden Stellungen (der TC4056 sitzt vor dem Schalter).
* Strom durch Schalter + 47 kΩ bei AN: ca. 79–89 µA (3,7–4,2 V / 47 kΩ).

**H1 – LED-Strom (5 V → Streifen):**

| Von | Nach |
|---|---|
| Pololu **VOUT** (5 V) | **Source Q1** (AO3401A) und **Elko 470 µF/25 V** (+), Elko (−) an GND – der Elko sitzt **vor** dem FET |
| **Drain Q1** | Streifen **5 V / +** |
| 10 kΩ | zwischen **Gate Q1** und **Source Q1** (Streifen standardmäßig aus) |
| BC547B **Kollektor** | **Gate Q1** |
| BC547B **Emitter** | GND |
| BC547B **Basis** | 4,7 kΩ → **GPIO18**; 47 kΩ Basis → GND |
| GPIO23 | 470 Ω **direkt am Streifen** → DIN |

* GPIO18 HIGH → BC547B zieht das Gate auf GND → Streifen hat 5 V. LOW oder hochohmig (Reset, Booten, Flashen) → aus.
* Die Firmware sendet vor dem Ausschalten Schwarz und lässt DIN danach LOW (kein Strom über die Datenleitung in den
  stromlosen Streifen).
* Warum GPIO18? Laut CYD-Schaltplan (macsbug, ESP32-2432S028) haben am SD-Slot CS (GPIO5), MOSI (GPIO23), MISO (GPIO19)
  und DAT1 je einen **10-kΩ-Pull-up** (Widerstandsnetz RN2), **CLK (GPIO18) aber nicht**. Darum hält der 47-kΩ-Widerstand
  Basis→GND den Streifen beim Booten sicher aus. GPIO18 erreichst du über den microSD-Sniffer (Pin CLK/SCK) oder den
  CLK-Lötpunkt am SD-Slot; keine SD-Karte einstecken.
* Folge des Pull-ups an GPIO23 (DIN): Solange die Firmware DIN auf LOW hält, fließen ca. 0,33 mA (3,3 V / 10 kΩ) –
  im Vergleich zu den 33–66 mA Durchschnitt vernachlässigbar.

**Zum Programmieren über die USB-Buchse des CYD:** Schalter auf **AUS**. Dann versorgt nur USB das CYD, und der Akku ist
über Q2 abgetrennt. Bei **AN** und eingestecktem USB liegen Pololu-Ausgang und USB-5 V parallel am 5-V-Netz – das war
auch in V3 schon so und ist **nicht geprüft**. Einmal messen: Schalter AUS, USB an → an Pololu VIN müssen ca. 0 V liegen
(keine Rückspeisung über den Wandler).

**Datenblattwerte (geprüft):**

| Bauteil | Wert | Was heißt das hier? |
|---|---|---|
| AO3401A (Alpha & Omega, Datenblatt Rev 3.1, Dez. 2023) | U_DS −30 V, I_D −4 A (25 °C), U_GS max ±12 V, U_GS(th) −0,5 … −1,3 V, R_DS(on) ≤ 60 mΩ bei −4,5 V, ≤ 85 mΩ bei −2,5 V, I_DSS ≤ 1 µA | Q1 (U_GS = −5 V): bei 0,12 A ca. 7 mV Verlust. Q2 (U_GS = −3,3 … −4,2 V): bei 0,5 A Spitze ca. 43 mV / 21 mW – kein Kühlkörper nötig |
| BC547B | I_C max 100 mA, Stromverstärkung 200–450 | Basisstrom ca. 0,54 mA, Kollektorstrom nur 0,5 mA (5 V / 10 kΩ) → sicher durchgeschaltet |
| C&K OS102011MS2QN1 | 1× Um, 0,1 A bei 12 V DC, Kontaktwiderstand ≤ 20 mΩ, 10 000 Schaltzyklen | schaltet nur die 0,08 mA des Gates – weit unter der Grenze |

**Vor dem ersten Einschalten prüfen (ohne CYD):** Akku an, Schalter AUS → an Pololu VIN 0 V. Schalter AN → VIN ≈ Akkuspannung.
GPIO18-Draht kurz an 3,3 V halten → Streifen-Plus hat 5 V; offen → 0 V.

---

## 8. Drucken lassen – so geht’s

**Möglichkeit A – Schule / FabLab / Makerspace (meist am günstigsten):**
Die sechs Dateien `base.stl`, `cover.stl`, `pad.stl`, `kappe_usb.stl`, `diffusor_led.stl`, `schalter_keile.stl` auf einen USB-Stick kopieren und diese Anleitung
(Abschnitt 3 Druckeinstellungen) zeigen. Material: PLA (Diffusor: weißes PLA oder naturfarbenes PETG, 100 % Füllung).

**Möglichkeit B – Craftcloud (craftcloud3d.com):**
1. Webseite öffnen → „Upload“ und die sechs STL-Dateien hochladen.
2. Material wählen: **PLA** (Verfahren FDM). Farbe nach Wunsch (z. B. Hellgrau / Weiß, Pad Blau). **Diffusor: Weiß**, Füllung 100 %.
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
4. Ganz oben `part = "base";` (oder `"cover"`, `"pad"`, `"cap"`, `"diffusor"`) einstellen, um das jeweilige Teil zu exportieren.
   `"assembly"` zeigt alles zusammengebaut, `"exploded"` die Explosionsansicht, `"inside"` das Innere ohne Deckel,
   `"section"` einen Schnitt. `cap_pull = 14` zieht die Abdeckkappe in der Vorschau heraus, `diff_pull = 16` den Diffusor.
   `"led_section"` zeigt einen Schnitt durch die Lichtkammer.
   `"keil"` exportiert die 2 Klemmkeile (Druck-Lage), `"sw_detail"` / `"sw_detail_offen"` zeigen die Schaltertasche
   (fertig / beim Einsetzen), `"sw_section"` einen Schnitt durch die Tasche, `"keil_check"` muss leer sein.

Oder einfach dem Assistenten die gemessenen Werte schicken – er erzeugt neue STL-Dateien.

---

## 10. Quellen der Maße

* CYD-Maßzeichnung und 3D-Modell: github.com/witnessmenow/ESP32-Cheap-Yellow-Display
  (`OriginalDocumentation/3-Structure_Diagram/Dimensions.png`, `3dModels/Havenview_CYD_CAD/Cheap Yellow Display v16.step`)
* Wägezelle: Datenblatt TAL220 (SparkFun, HTC Sensor) – 80 × 12,7 × 12,7 mm, Löcher bei 5/20 mm, 2× M4 + 2× M5
* Akku: Datenblatt EEMB LP103454 (2000 mAh): 34,5 × 55 (56) × 10,3 mm
* Schiebeschalter: Datenblatt C&K OS-Serie (OS102011MS2QN1): Gehäuse 8,6 × 4,3 mm, Schieber 2,0 mm, Weg 2,0 mm, Raster 2,0 mm
* P-MOSFET: Datenblatt Alpha & Omega AO3401A Rev 3.1 (aosmd.com)
