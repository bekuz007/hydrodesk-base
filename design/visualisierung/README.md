# HydroDesk Base – Visualisierung

Gerenderte Bilder der HydroDesk Base, im Stil einer technischen Explosionszeichnung.
**Seit 10.11.2026 sind die vier Bilder unten aus dem realistischen 3D-Modell** (`design/3d_modell/realistisch/hydrodesk_realistisch.blend`) gerendert:
Gehäuse aus den echten Druck-STLs, alle Module mit echten Maßen und Fototexturen, jede Litze als Kabel nach dem Lötplan.
Kameras, Bildaufbau, Auflösung und Beschriftung entsprechen den früheren Bildern (die vorher aus dem vereinfachten Modell kamen).
Weitere Ansichten des realistischen Modells (Draufsicht, Detail SD/FET, …) liegen in `realistisch/`.

| Datei | Inhalt |
|---|---|
| `hydrodesk_explosion.png` | Explosionsansicht von unten nach oben: Gummifüße, davor Diffusor-Leiste und COB-LED-Streifen (26 LEDs) nach vorne unten herausgezogen → Unterschale → Akku + 5-V-Wandler Pololu S13V10F5 → Wägezelle, HX711, Lader, FET-Platine (2× AO3401A), LM393, Regensensor, links der Ein/Aus-Schalter mit den 2 Klemmkeilen → Display-Board (etwas höher gezeichnet, damit alle Hinweislinien frei bleiben) mit der nach hinten herausgezogenen USB-Abdeckkappe → Flaschenplatte → Silikonmatte → Deckel |
| `hydrodesk_innen.png` | Innenansicht ohne Deckel und Platte. Alle Module mit Kabeln (auch FET-Platine und Ein/Aus-Schalter in der linken Wand), das Display-Board ist angehoben gezeichnet |
| `hydrodesk_teile.png` | Teileübersicht: alle 20 Teile (inkl. USB-Abdeckkappe, Diffusor-Leiste, Ein/Aus-Schalter und Klemmkeilen) maßstäblich auf einer Schneidematte (Raster 1 cm) mit nummerierter Legende; ohne Litzen, Schrumpfschlauch, Lötzinn und den 2 × 10-kΩ-Teiler |
| `hydrodesk_produkt.png` | Produktbild: geschlossenes Gerät, Display mit Tagesfortschritt, vorne eine gleichmäßig blau leuchtende Lichtlinie (COB-LED-Streifen hinter dem milchigen Diffusor, keine einzelnen Lichtpunkte), Flasche nur angedeutet |

## So entstehen die Bilder

1. **Blender 4.5 (Cycles)** baut das realistische Modell aus den STL-Dateien (`src/stl/`, Einbaulage aus OpenSCAD) und den nachgebauten Modulen
   (`realistisch/src/real_scene.py`, Maße und Quellen: `design/3d_modell/realistisch/README.md`) und rendert die Ansichten `v_produkt`, `v_explosion`, `v_innen`, `v_teile`
   (`realistisch/src/real_views.py`: gleiche Kameras wie früher, Hilfslinien, angedeutete Flasche im Produktbild, Schneidematte mit Rastermaß in der Teileübersicht).
   Zu jedem Bild schreibt das Skript die Bildpunkte der Bauteile (`.json`).
2. **Python/PIL** (`realistisch/src/real_final.py`) setzt Titel, deutsche Beschriftungen und Hinweislinien darüber. Die Linien zeigen genau auf sichtbare Punkte der Bauteile.

Neu rendern (nach einer Änderung am Modell oder an den STL-Dateien):

```bash
cd design/visualisierung/src
for p in base cover pad cap diff keil; do openscad -o stl/$p.stl w_$p.scad; done   # STL in Einbaulage
cd ../realistisch
./render_readme.sh          # braucht Blender 4.x mit Cycles (Pfad über BLENDER=... setzen), schreibt die 4 Bilder hierher
```

Auflösung: 2560 × 1440 px, 128 Samples. Rendern dauert auf 8 CPU-Kernen ca. 20 Minuten (Innenansicht mit den Kabeln am längsten).

Die ältere Pipeline mit dem vereinfachten Modell (`src/scene.py`, `src/final.py`, `src/render_all.sh`) bleibt zum Nachschlagen im Repo.
**Achtung:** `src/render_all.sh` schreibt dieselben vier Dateinamen und würde die realistischen Bilder wieder überschreiben.

Hinweis: Elektronik-Bauteile sind Nachbauten (richtige Größe, Lage und Farbe nach Händlerangaben, aber keine echten Bauteil-CAD-Daten, Details siehe Maßtabelle im Modell-README).
Gehäuse-Farben (PLA grau, Pad blau) und die Flasche sind Platzhalter. Die Renderbilder sind **kein Foto**.
