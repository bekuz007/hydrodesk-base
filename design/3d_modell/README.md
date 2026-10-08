# HydroDesk Base – komplettes 3D-Modell

Das ganze Gerät als 3D-Modell: Gehäuse **und** Elektronik, Schrauben, Gummifüße, LED-Leiste und Silikonmatte.
Maßstab 1:1 (180 × 100 × 25 mm, mit Gummifüßen 27,2 mm hoch, mit eingesteckter Abdeckkappe 101,2 mm tief).

| Datei | Inhalt |
|---|---|
| `hydrodesk_komplett.glb` | Zusammengebautes Gerät mit Farben und Display-Bild. 19 einzeln benannte Teile (Abdeckkappe eingesteckt) |
| `hydrodesk_komplett.stl` | Dasselbe Gerät als ein einziges Netz ohne Farben, Einheit mm. Nur zum Anschauen |
| `hydrodesk_komplett.3mf` | Zusammengebautes Gerät, 19 Teile, Einheit mm, Farben pro Fläche |
| `hydrodesk_explosion.glb` | Explosionsansicht (Teile auseinandergezogen wie im Bild `design/visualisierung/hydrodesk_explosion.png`, Abdeckkappe nach hinten herausgezogen) |
| `hydrodesk_explosion.stl` | Explosionsansicht als ein Netz, Einheit mm |
| `vorschau_komplett.png` | Kontrollbild: die GLB-Datei neu importiert und gerendert |

**Teile (Objektnamen):** Unterschale, Deckel, Abdeckkappe_USB, Flaschenplatte, Silikonmatte, Display-Board, Akku, Step-up, TC4056,
FET-Modul, LM393, Regensensor, Waegezelle, HX711, LED-Leiste, Schrauben_M3, Schrauben_M4, Schrauben_M5, Gummifuesse.

## Öffnen

- **Mac:** `.glb` und `.stl` im Finder markieren und Leertaste drücken (Quick Look), oder mit **Vorschau** öffnen.
- **Browser:** <https://gltf-viewer.donmccurdy.com>, dann die `.glb`-Datei hineinziehen. Drehen geht mit der Maus.
- **Blender:** Datei → Importieren → glTF 2.0 (`.glb`) oder STL. Jedes Teil ist ein eigenes Objekt.
- `.3mf` öffnet z. B. in PrusaSlicer, Bambu Studio oder Windows 3D-Viewer.

## Wichtig

- Die **Elektronik ist vereinfacht** nachgebaut: richtige Größe, Lage und Farbe, aber keine echten Bauteil-CAD-Daten.
  Platinenfarben sind zur Unterscheidung gewählt.
- Diese Dateien sind **keine Druckdateien**. Zum 3D-Drucken nur `gehaeuse/stl/` verwenden
  (`base.stl`, `cover.stl`, `pad.stl`, `kappe_usb.stl`, dort schon richtig auf dem Druckbett ausgerichtet).

## Neu erzeugen

```bash
cd design/visualisierung/src
HD_NO_RENDER=1 HD_OUT=../../3d_modell/hydrodesk_komplett  blender -b -P export.py -- produkt   /tmp/x.png 1 10
HD_NO_RENDER=1 HD_OUT=../../3d_modell/hydrodesk_explosion blender -b -P export.py -- explosion /tmp/x.png 1 10
python3 make_3mf.py ../../3d_modell/hydrodesk_komplett.glb ../../3d_modell/hydrodesk_komplett.3mf
```
