# Obsidian-Vault: HydroDesk Base

Dieser Ordner ist ein **Obsidian-Vault** für das Schulprojekt **HydroDesk Base**.
Die Notizen sind kurz, miteinander per Wikilinks (`[[Notizname]]`) verknüpft und bilden in der Graphansicht ein Wissensnetz.

## Vault öffnen

1. [Obsidian](https://obsidian.md) installieren (falls noch nicht vorhanden).
2. Obsidian starten und **„Ordner als Vault öffnen“** wählen.
3. Genau diesen Ordner `obsidian` auswählen (im Repository `hydrodesk-base/obsidian`, auf dem Mac typischerweise `/Users/bekuzfx/HydroDesk/Obsidian_HydroDesk`).
4. Die Graphansicht öffnen: **⌘ + G** (macOS) bzw. **Strg + G** (Windows/Linux), oder über die linke Leiste das Graph-Symbol.

Beim ersten Öffnen stellt Obsidian den dunklen Standardlook ein. Farben der Knoten kommen aus den Schlagwörtern (`tags` im Frontmatter); die Zuordnung steht in `.obsidian/graph.json`. Schlagwörter selbst werden im Graphen nicht als eigene Knoten angezeigt (`showTags` ist aus).

Eine statische Vorschau des Netzes liegt unter `graph_vorschau.png`.

## Was steckt drin?

Die Notizen enthalten nur Angaben aus dem Repository (README, Anleitung, Bautagebuch, Firmware, Apps, Vorkalkulation, Einkaufsliste, Lizenz). Nichts ist frei erfunden.

| Ordner | Inhalt |
|---|---|
| *(Wurzel)* | Startnotiz **HydroDesk Base**, dazu **Projektteam** |
| `Hardware/` | CYD, Wägezelle, HX711, Sensoren, Akku, Strom, FET, Schalter |
| `Gehäuse/` | Bodenwanne, Deckel, Pad, Kappe, Diffusor, Klemmkeile |
| `Software/` | Firmware, Stromsparen, BLE, WLAN, Kalibrierung, Apps, Supabase, Design |
| `Dokumentation/` | Vorkalkulation, Einkaufsliste, Bautagebuch, Anleitung, Lizenz |
| `Werkzeuge/` | VS Code/PlatformIO, Xcode, Android Studio, OpenSCAD, Blender, GitHub, Wokwi |
| `Status/` | Erledigt, Offen, verworfene Entscheidung Spritzschutz |

Startpunkt: die Notiz **HydroDesk Base** öffnen und den Links folgen – oder direkt die Graphansicht nutzen.

## Farben im Graphen

| Schlagwort | Bedeutung | Farbe |
|---|---|---|
| `typ/projekt` | das Gesamtprojekt | Blau |
| `typ/hardware` | elektronische Bauteile | Orange |
| `typ/gehaeuse` | gedruckte Gehäuseteile | Sand |
| `typ/software` | Firmware, Apps, Datenbank | Türkis |
| `typ/doku` | Dokumente und Listen | Grau-Blau |
| `typ/werkzeug` | Programme und Plattformen | Grün |
| `typ/status` | erledigt / offen | Gelb |
| `typ/entscheidung` | festgehaltene Entscheidung | Rot |
| `typ/team` | Aufgabenverteilung | Rosa |

## Hinweise

- Zugangsdaten (WLAN, Supabase-Schlüssel) stehen bewusst **nicht** in diesen Notizen.
- Arbeitsdateien von Obsidian (z. B. `workspace.json`) gehören nicht ins Git.
