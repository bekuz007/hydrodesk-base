# 3D-Lötpläne (Blender)

Headless-Skripte für die 3D-Ansichten im Stil von `loeten_5c_fet_3d_oben.png` / `_unten.png`
(Cycles, AgX, Beschriftung mit PIL).

| Datei | Inhalt |
|---|---|
| `loeten_4b_stromweg_3d.png` | Lötschritt 4: Stromweg (TC4056 → Q2 + Schalter → Pololu → CYD / FET-Platine) |
| `loeten_6b_led_regen_3d.png` | Lötschritt 6: LED-Streifen (470 Ω in DIN) und Regensensor LM393 |

Die fertigen Bilder liegen unter `projektdokumentation/fotos/loeten/`.
Verbindungen nur nach `loeten_4_stromweg.png`, `loeten_6_led_regensensor.png`,
`gehaeuse/ANLEITUNG.md` (7b/7c) und `design/loetplan/make.py`.

```bash
# im Repo, Blender 4.2 im PATH oder über $BLENDER
./design/loetplan/3d/render.sh          # 64 Samples, Cycles
./design/loetplan/3d/render.sh 16 eevee # schnelle Vorschau
```
