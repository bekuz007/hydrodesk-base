# 3D-Lötpläne (Blender)

Headless-Skripte für die 3D-Ansichten im Stil von `loeten_5c_fet_3d_oben.png` / `_unten.png`
(Cycles, AgX, Beschriftung mit PIL). Zusätzlich selbstständige `.blend`-Dateien
(Texturen sind eingepackt, Kamera und Licht sind gesetzt, Objekte auf Deutsch benannt,
Beschriftungen als 3D-Text).

| Datei | Inhalt |
|---|---|
| `loeten_4b_stromweg_3d.blend` / `.png` | Lötschritt 4: Stromweg (TC4056 → Q2 + Schalter → Pololu → CYD / FET-Platine) |
| `loeten_5c_fet_3d.blend` | Lötschritt 5c: FET-Platine, Kameras *Kamera_Oben* und *Kamera_Unten* |
| `loeten_6b_led_regen_3d.blend` / `.png` | Lötschritt 6: LED-Streifen (470 Ω in DIN) und Regensensor LM393 |

Die fertigen PNG-Bilder liegen unter `projektdokumentation/fotos/loeten/`.
Die `.blend`-Dateien liegen in diesem Ordner und können direkt in Blender 4.2 geöffnet werden
(Numpad 0 = Kamerasicht; in 5c zwischen *Kamera_Oben* und *Kamera_Unten* umschalten).
Verbindungen nur nach `loeten_4_stromweg.png`, `loeten_5b_*.png`, `loeten_6_led_regensensor.png`,
`gehaeuse/ANLEITUNG.md` (7b/7c) und `design/loetplan/make.py`.

```bash
# im Repo, Blender 4.2 im PATH oder über $BLENDER
./design/loetplan/3d/render.sh          # 64 Samples, Cycles, plus .blend speichern
./design/loetplan/3d/render.sh 16 eevee # schnelle PNG-Vorschau, plus .blend
./design/loetplan/3d/render.sh 0        # nur die .blend-Dateien erzeugen
```
