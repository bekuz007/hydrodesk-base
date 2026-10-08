# HydroDesk Base – Visualisierung

Gerenderte Bilder der HydroDesk Base, im Stil einer technischen Explosionszeichnung.
Alle Maße kommen direkt aus dem OpenSCAD-Modell `gehaeuse/hydrodesk_base.scad`.

| Datei | Inhalt |
|---|---|
| `hydrodesk_explosion.png` | Explosionsansicht von unten nach oben: Gummifüße, davor Diffusor-Leiste und COB-LED-Streifen (26 LEDs) nach vorne unten herausgezogen → Unterschale → Akku + 5-V-Wandler Pololu S13V10F5 → Wägezelle, HX711, Lader, FET, LM393, Regensensor → Display-Board (etwas höher gezeichnet, damit alle Hinweislinien frei bleiben) mit der nach hinten herausgezogenen USB-Abdeckkappe → Flaschenplatte → Silikonmatte → Deckel |
| `hydrodesk_innen.png` | Innenansicht ohne Deckel und Platte. Alle Module mit Kabeln, das Display-Board ist angehoben gezeichnet |
| `hydrodesk_teile.png` | Teileübersicht: alle 18 Teile (inkl. USB-Abdeckkappe und Diffusor-Leiste) maßstäblich auf einer Schneidematte (Raster 1 cm) mit nummerierter Legende |
| `hydrodesk_produkt.png` | Produktbild: geschlossenes Gerät, Display mit Tagesfortschritt, vorne eine gleichmäßig blau leuchtende Lichtlinie (COB-LED-Streifen hinter dem milchigen Diffusor, keine einzelnen Lichtpunkte), Flasche nur angedeutet |

## So entstehen die Bilder

1. **OpenSCAD** exportiert Unterschale, Deckel, Flaschenplatte, USB-Abdeckkappe und Diffusor-Leiste als STL in Einbaulage (`src/w_*.scad`).
2. **Blender 4.5 (Cycles)** baut die Elektronik als vereinfachte 3D-Modelle in Originalgröße nach
   (`src/scene.py`), lädt die STL-Dateien und rendert jede Ansicht.
3. **Python/PIL** setzt die Bilder auf den Hintergrund und zeichnet die deutschen Beschriftungen
   mit Hinweislinien (`src/final.py`). Die Linien zeigen genau auf die 3D-Punkte der Bauteile.

Neu rendern (nach einer Änderung am Modell):

```bash
cd design/visualisierung/src
for p in base cover pad cap diff; do openscad -o stl/$p.stl w_$p.scad; done   # STL in Einbaulage
./render_all.sh            # braucht Blender 4.x mit Cycles (Pfad über BLENDER=... setzen)
```

Auflösung: 2560 × 1440 px, 128 Samples. Rendern dauert auf 8 CPU-Kernen ca. 15 Minuten.

Hinweis: Elektronik-Bauteile sind vereinfacht (richtige Größe, Lage und Farbe, aber keine echten Bauteil-CAD-Daten).
Die Farben der Platinen sind zur Unterscheidung gewählt, die echten Module können andere Farben haben.
