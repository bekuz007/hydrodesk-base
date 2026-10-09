# Quellen der Maße (Gehäuse-Konstruktion)

Die Maßzeichnungen und Datenblätter, die für die Konstruktion des Gehäuses benutzt wurden,
stammen von Dritten und liegen deshalb **nicht** in diesem Repository. Hier die Originalquellen:

## ESP32-2432S028R („Cheap Yellow Display“, CYD)

Repository: <https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display>

* **Maßzeichnung** (Platine 50 × 86 mm, Löcher 42 × 78 mm, Ø 3,2 mm):
  [`OriginalDocumentation/3-Structure_Diagram`](https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display/tree/main/OriginalDocumentation/3-Structure_Diagram)
  (Datei `Dimensions.png`)
* **3D-Modell (STEP)** (Gesamtdicke 9,8 mm: Bauteile 4,7 | PCB 1,5 | LCD + Touch 3,6):
  [`3dModels/Havenview_CYD_CAD`](https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display/tree/main/3dModels/Havenview_CYD_CAD)
  (Datei `Cheap Yellow Display v16.step`)

## Wägezelle TAL220 (Straight Bar, 80 × 12,7 × 12,7 mm)

* **Datenblatt (SparkFun):** <https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/TAL220M4M5Update.pdf>
* Produktseite SparkFun: <https://www.sparkfun.com/load-cell-10kg-straight-bar-tal220.html>

Benutzte Maße: 80 × 12,7 × 12,7 mm, Löcher 5 mm und 20 mm von jedem Ende, 2× M4 an einem Ende, 2× M5 am anderen.
Die verbaute 5-kg-Zelle (DIYmalls-Set) hat die gleiche Bauform – trotzdem vor dem Druck nachmessen
(siehe [ANLEITUNG.md](ANLEITUNG.md), Abschnitt 5).

## Akku EEMB LP103454 (2000 mAh)

Maße laut Herstellerdatenblatt: 34,5 × 55 × 10,3 mm (mit Kabelende ca. 56 mm).

## Ein/Aus-Schalter C&K OS102011MS2QN1 (Schiebeschalter, 1× Um, nicht überlappend)

* **Datenblatt (C&K / Littelfuse, OS-Serie):** <https://xonstorage.z8.web.core.windows.net/pdf/ck_os102011ms2qn1_apr22_xonlink.pdf>

Benutzte Werte: Gehäuse 8,6 × 4,3 mm, Schieber 2,0 mm breit / 4,0 mm hoch, Weg 2,0 mm, Pin-Raster 2,0 mm,
0,1 A bei 12 V DC, Kontaktwiderstand ≤ 20 mΩ, 10 000 Schaltzyklen. Die Gehäusehöhe ist in der Zeichnung nicht
eindeutig (3,5–4,7 mm, Händler: 4 mm) → im Modell 4,0 mm, **nachmessen** (ANLEITUNG.md, Abschnitt 5).

## P-MOSFET AO3401A (FET-Platine, H1 + H2)

* **Datenblatt (Alpha & Omega, Rev 3.1, Dez. 2023):** <https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf>

Benutzte Werte: U_DS −30 V, I_D −4 A, U_GS ±12 V, U_GS(th) −0,5 … −1,3 V, R_DS(on) ≤ 60 mΩ (−4,5 V) / ≤ 85 mΩ (−2,5 V).
