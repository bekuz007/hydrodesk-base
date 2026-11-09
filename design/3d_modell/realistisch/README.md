# HydroDesk Base – realistisches 3D-Modell mit Verkabelung

Dieses Modell zeigt das Gerät so, wie es mit den **gekauften Teilen** (Einkaufsliste im Haupt-README) aufgebaut wird:
Gehäuse aus den echten Druck-STLs, alle Platinen mit echten Maßen und Fototexturen, und **jede Litze als gebogenes Kabel in ihrer echten Farbe** nach dem Lötplan.

| Datei | Inhalt |
|---|---|
| `hydrodesk_realistisch.blend` | Blender-4.5-Szene (Texturen eingepackt), Collections **Gehäuse**, **Elektronik**, **Kabel** |
| `hydrodesk_realistisch.glb` | dasselbe als glTF (Meter, Y-oben) – z. B. im Browser oder Windows-3D-Viewer öffnen |
| `../../visualisierung/realistisch/hydrodesk_real_a_offen.png` | Draufsicht, Deckel ab, Display halb durchsichtig |
| `../../visualisierung/realistisch/hydrodesk_real_b_iso.png` | Schrägansicht, Deckel ab, Display angehoben |
| `../../visualisierung/realistisch/hydrodesk_real_c_explosion.png` | Explosionsansicht |
| `../../visualisierung/realistisch/hydrodesk_real_d_detail_sd_fet.png` | Nahaufnahme: Litzen am SD-Slot des CYD und FET-Platine |
| `../../visualisierung/realistisch/hydrodesk_real_e_produkt.png` | Fertiges Gerät, geschlossen |

Neu erzeugen (Blender 4.5): `design/visualisierung/realistisch/render_all.sh [Samples]`
(Quellcode: `src/real_scene.py`, CYD-Rückseite: `src/cyd_layout.py`, Texturen: `src/real_tex.py`).
Prüfung: `blender -b -P src/real_scene.py -- check x` meldet Kabel, die durch Teile/Wände gehen oder sich überschneiden – aktueller Stand: **34 Litzen, 0 Kollisionen, 0 Überlappungen, zusammen ca. 2,33 m Litze**.

## Maßtabelle

„Quelle“ = Maß steht im Datenblatt / auf der Händlerseite. „geschätzt“ = aus Produktfotos abgelesen oder typischer Wert der Bauform – **vor dem Druck mit dem Messschieber nachmessen**. Ich habe kein Teil selbst in der Hand gemessen.

| Teil | Maße im Modell (mm) | Quelle | Art |
|---|---|---|---|
| CYD ESP32-2432S028R (Fastsaw) – Platine | 50 × 86 × 1,6, Ecken R 3 | https://www.amazon.de/dp/B0G1N16Q16 (Maßbild im Listing) | Quelle |
| CYD – Lochabstand | 42 × 78 (im Gehäuse) | Listing-Maßbild zeigt ca. 42,5 × 79 | **geschätzt – nachmessen** |
| CYD – TFT-Modul 2,8" | 3,6 dick | typisch ILI9341-Modul | geschätzt |
| CYD – Bauteile Rückseite (ESP32-Modul 18 × 25,5 × 3,1, microSD-Slot, JST 1,25 mm P1/P3/CN1, Testpads S1/S3) | Lage aus Produktfoto (ca. 10 px/mm, ±0,5) | https://www.amazon.de/dp/B0G1N16Q16 | geschätzt |
| EEMB LiPo LP103454 2000 mAh | 34,5 × 56 × 10,3, Kabel ca. 50 mm, JST-2.0 | https://www.amazon.de/dp/B08214DJLJ (Typ 103454 = 10 × 34 × 54 nominal + Schutzplatine) | Quelle |
| Pololu S13V10F5 | 8,9 × 12,1, Bauteile oben 1,8 / unten 1,4, Löcher Ø 1,02 im 2,54-Raster | https://www.pololu.com/product/4083 + Maßzeichnung (referenz/pololu_s13vxf5_dimensions.pdf), https://www.berrybase.de/pololu-s13v10f5-5v-1a-step-up-step-down-converter | Quelle |
| TC4056 USB-C Lademodul mit Schutz | 17 × 26 (27 mit USB-C-Überstand) × 1,6 | https://www.amazon.de/dp/B0F67KYB4F | Quelle (Händler), Bauteilhöhen geschätzt |
| FET-Platine (Lochraster 3 × 7 cm, zugeschnitten) | wie Lötplan A–K, 1,6 dick, Raster 2,54 | https://www.berrybase.de/lochrasterplatine-doppelseitig-3x7cm-10-stueck | Quelle |
| SOT-23-Adapter (AO3401A) | Platine ca. 10 × 12 | https://www.berrybase.de/smd-breakout-adapter-fuer-sot23-ssop10-msop10-10-pin-0-50mm-0-95mm | geschätzt (Foto) |
| BC547B | TO-92: 4,6 × 3,7 × 4,6 | https://www.berrybase.de/bc547b-bipolarer-transistor-npn-45v-100ma-to-92-3-pin | Quelle (Bauform) |
| Widerstände 0207 (470 Ω, 4,7 k, 10 k, 47 k) | Ø 2,3 × 6,3 | https://www.berrybase.de/metallschichtwiderstand-10-0-kohm-1-4w-1-0207-axial-durchsteckmontage | Quelle |
| Elko 470 µF / 25 V | Ø 10 × 16 | https://www.berrybase.de/elektrolytkondensator-470-f-25v-1050c-1-radial-tht | Quelle |
| Regenplatte MH-RD | 40 × 54 × 1,6, abgewinkelte 2er-Stiftleiste | https://www.berrybase.de/regensensor-mit-digitalem-und-analogem-ausgang | Quelle (Bauform FC-37), Stiftlage geschätzt |
| LM393-Auswertemodul | 16 × 30 × 1,6, Poti blau | gleiche Seite | geschätzt (Foto) |
| Wägezelle 5 kg (DIYmalls) | 80 × 12,7 × 12,7, Kabel rot/schwarz/weiß/grün | https://www.amazon.de/dp/B0B9H3YMT2 (TAL220-Bauform) | Quelle (Bauform) |
| HX711-Modul (grün) | ca. 34 × 20 × 1,6 | gleiche Seite | geschätzt (Foto) |
| COB-LED-Streifen BTF FCOB WS2812B | 162,5 lang (26 LEDs), 5 breit, FPC 0,3 + COB 1,5 | https://www.amazon.de/dp/B0H41MCVSW (Variante 160 LED/m, 5 mm – die Seite öffnet manchmal die 10-mm-Variante) | Breite Quelle, Höhe **geschätzt** |
| Schiebeschalter ON-ON | 8,6 × 4,3 × 4, Pins Raster 2 | https://www.berrybase.de/schiebeschalter-printmontage-on-on-2-stellig-8.6x4.3x4mm-gerade | Quelle |
| Vierlingslitze 4 × 0,14 mm² | Ader Ø ca. 0,9 (Modell 0,9) | https://www.berrybase.de/vierlingslitze-isoliert-4x0-14mm-5m-farbe-blau-gelb-rot-gruen | Querschnitt Quelle, Außen-Ø geschätzt |
| JST 1,25 mm 4-polig (CYD-Kabel) | Stecker 5,0 × 3,4 × 3,4 | AliExpress (Pos. 19) | geschätzt |
| Schrumpfschlauch | Ø 1,6 / 2,4 geschrumpft | https://www.berrybase.de/schrumpfschlauch-set-100-teilig-in-sortimentsbox-schwarz | geschätzt |
| Gummifüße FIX&FASTEN | Ø 10 unten / 9,5 oben × 4,5 | https://www.berrybase.de/fix-fasten-selbstklebender-fuss-rund-oben-9-5mm-unten-10mm-hoehe-4-5mm-gummi-schwarz | Quelle |
| Silikonmatte (Flaschen-Pad) | 86 × 86 × 1,2 (zugeschnitten) | https://www.amazon.de/dp/B0GVNMS4DZ („1,2 mm Stärke“) | Quelle |
| Senkschrauben DIN 7991 | M3 × 12 (8×), M4 × 10 (2×), M5 × 12 (2×) | Einkaufsliste Pos. 11–13 (alleschrauben.de), Kopfmaße nach DIN 7991 | Quelle |
| Gehäuse, Deckel, Pad, Kappe, Diffusor, Keile | exakt aus `design/visualisierung/src/stl` | eigene CAD-Daten | Quelle |

Die Produktfotos und Händlerseiten, die ich benutzt habe, liegen lokal in `HydroDesk/realistisch/referenz/` (88 Dateien, nicht im Repo wegen Urheberrecht).

## Annahmen (bitte prüfen)

1. **SD-Slot** öffnet zur rechten Platinenkante (+X); die drei Litzen (GPIO18/19/23 → SD-Lötfahnen 3/5/7) sind an die Lötfahnen innen am Slot gelötet und laufen über die Akku-Oberseite nach vorne.
2. **P1 (UART) ist von der Rückwand verdeckt**: Pololu VOUT/GND gehen deshalb an die Testpads **S3 (5 V) / S1 (GND)** auf der CYD-Rückseite.
3. **Regensensor 3,3 V und GND** sind am CN1-Kabel (rot/schwarz) kurz hinter dem Stecker abgezweigt, mit Schrumpfschlauch.
4. **HX711 und LM393**: Litzen direkt angelötet (keine Stiftleisten wie im Lötplan) – sonst wird es unter dem Deckel zu hoch (< 12 mm).
5. **Regenplatte**: die abgewinkelte Stiftleiste bleibt drauf, die orange/gelbe Dupont-Litze ist abgeschnitten und an die Stiftspitzen gelötet.
6. **Schalter**: oberer Pin = AN, mittlerer = gemeinsam, unterer = AUS – **mit dem Durchgangsprüfer nachmessen**.
7. **Spannungsteiler 2 × 10 kΩ** liegt in Schrumpfschlauch auf dem Boden bei x ≈ 51; oben an Pololu VIN, Mitte an P3 IO35, unten an P3 GND. Die freien P3-Adern IO22/IO21 sind isoliert (Schrumpfschlauch-Kappe).
8. **COB-Streifen** sitzt 1,85 mm rechts von der Mitte, damit die Litzen ins Kabelloch (x 8,5–12) reichen.
9. **Akkukabel** kommen vorne rechts aus der Schutzplatine; im Modell 53–55 mm lang (Herstellerangabe ca. 50 ± 3).
10. **Farben der Vierlingslitze**: rot = Plus, blau = GND, gelb/grün = Signale (Lötplan-Farben).
11. **Pololu** um 180° gedreht, Lötlöcher zeigen nach hinten.
12. **PLA-Farbe grau** und **Pad blau** sind Platzhalter – die echten Filamentfarben können anders sein.
13. **Gummifüße** wie gekauft Ø 10 (die ANLEITUNG nennt noch Ø 12); **Deckelschrauben** wie gekauft DIN 7991 (die ANLEITUNG nennt DIN 965).

## Was vereinfacht ist

- Kleine SMD-Bauteile (Widerstände, Kondensatoren, ICs) auf den gekauften Modulen sind Quader mit Fototextur, keine echten Bauteilmodelle.
- Lötstellen sind gleichmäßige Zinnkugeln, Kabel ohne verdrillte Litzendrähte; die Kabelwege sind ein sinnvoller Vorschlag, nicht „wie du es später wirklich legst“.
- In der Explosionsansicht sind die Kabel zwischen den Teilen gestreckt (in echt wären sie dafür zu kurz).
- Die Renderbilder sind sauber und echt beleuchtet, aber **kein Foto** – Staub, Flussmittelreste, Kratzer usw. fehlen.
