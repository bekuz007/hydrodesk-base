# -*- coding: utf-8 -*-
"""PIL-Beschriftung im Stil von loeten_5c (Header, Legende, Warnfuß)."""
from PIL import Image, ImageDraw, ImageFont
import json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def F(s, b=True):
    return ImageFont.truetype(FB if b else FR, s)

NAVY = (25, 60, 110)
NETC = dict(
    bat=(215, 30, 30), gnd=(25, 25, 25), gate=(90, 90, 160),
    vin=(240, 130, 0), v5=(200, 0, 120), din=(20, 150, 60),
    white=(230, 230, 230), teal=(0, 150, 150), dark=(40, 40, 40),
)
TOP = 110
SIDE = 560

def make(raw_path, json_path, out, title, sub, foot, labels, legend_lines, tag_circles=None):
    raw = Image.open(raw_path).convert("RGBA")
    A = json.load(open(json_path))
    W, H = raw.width + SIDE, raw.height + TOP + 90
    im = Image.new("RGBA", (W, H), (236, 238, 241, 255))
    d = ImageDraw.Draw(im)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=(244 - y * 20 // H, 245 - y * 20 // H, 248 - y * 18 // H))
    im.alpha_composite(raw, (0, TOP))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, TOP - 16], fill=NAVY)
    d.text((30, 16), title, font=F(34), fill="white")
    d.text((30, 62), sub, font=F(20, False), fill=(210, 220, 240))

    def P(k):
        x, y = A[k][0], A[k][1]
        return (x, y + TOP)

    def tag(xy, txt, fill=(255, 255, 255), ink=(20, 20, 20), size=23, border=NAVY):
        f = F(size)
        bb = d.multiline_textbbox(xy, txt, font=f, anchor="mm", spacing=3)
        d.rounded_rectangle([bb[0] - 11, bb[1] - 7, bb[2] + 11, bb[3] + 7], 10,
                            fill=fill, outline=border, width=3)
        d.multiline_text(xy, txt, font=f, fill=ink, anchor="mm", spacing=3, align="center")
        return bb

    for item in labels:
        key, (dx, dy), txt = item[0], item[1], item[2]
        col = item[3] if len(item) > 3 else NAVY
        ax, ay = P(key)
        tx, ty = ax + dx, ay + dy
        d.line([(ax, ay), (tx, ty)], fill=col, width=4)
        d.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], fill=col, outline="white", width=2)
        tag((tx, ty), txt, border=col if col != NAVY else NAVY)

    if tag_circles:
        for key, num, net, off in tag_circles:
            x, y = P(key)
            if off:
                d.line([(x, y), (x + off[0], y + off[1])], fill=NETC[net], width=5)
                x, y = x + off[0], y + off[1]
            d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=NETC[net], outline="white", width=3)
            d.text((x, y), str(num), font=F(22), fill="white" if net != "white" else (20, 20, 20), anchor="mm")

    # Legende
    LX = raw.width + 18
    d.rounded_rectangle([LX, TOP + 8, W - 22, TOP + raw.height - 8], 14,
                        fill=(250, 251, 253), outline=NAVY, width=3)
    y = TOP + 26
    for kind, a, b in legend_lines:
        if kind == "h":
            d.text((LX + 18, y), a, font=F(24), fill=NAVY)
            y += 40
        elif kind == "net":
            if a == "white":
                d.line([(LX + 20, y + 14), (LX + 68, y + 14)], fill=(150, 150, 150), width=14)
            d.line([(LX + 22, y + 14), (LX + 66, y + 14)], fill=NETC[a], width=10)
            d.text((LX + 80, y + 2), b, font=F(20, False), fill=(20, 20, 20))
            y += 36
        elif kind == "step":
            d.ellipse([LX + 18, y, LX + 48, y + 30], fill=NAVY)
            d.text((LX + 33, y + 15), str(a), font=F(16), fill="white", anchor="mm")
            d.multiline_text((LX + 58, y - 2), b, font=F(17, False), fill=(30, 30, 30), spacing=2)
            y += 18 * (b.count("\n") + 1) + 16
        elif kind == "t":
            d.multiline_text((LX + 18, y), a, font=F(18, False), fill=(60, 60, 60), spacing=4)
            y += 24 * (a.count("\n") + 1) + 8
        elif kind == "gap":
            y += 12

    d.rectangle([0, H - 80, W, H], fill=(200, 20, 20))
    # warning triangle
    x0 = 36
    d.polygon([(x0, H - 18), (x0 + 22, H - 62), (x0 + 44, H - 18)], fill=(255, 210, 0))
    d.text((x0 + 22, H - 34), "!", font=F(26), fill=(40, 20, 0), anchor="mm")
    d.text((100, H - 40), foot, font=F(28), fill="white", anchor="lm")
    im.convert("RGB").save(out, quality=95)
    print("ok", out, im.size)

def do_4(raw, js, out):
    make(raw, js, out,
         "Lötschritt 4b: Stromweg in 3D – Akku → Schalter → 5-V-Wandler",
         "Nur zum Verstehen, kein Druckteil  ·  gleiche Verbindungen wie loeten_4_stromweg",
         "Beim Löten kein Strom drauf – Akku ab, USB ab, Schalter auf AUS",
         [
             ("TC4056", (80, -160), "TC4056\nOUT+ / OUT−"),
             ("Q2", (110, -200), "Q2 Ein/Aus\nAO3401A auf der FET-Platine"),
             ("R47", (-240, -30), "47 kΩ\nzwischen G und S"),
             ("Schalter", (40, 130), "Ein/Aus-Schalter\nAUS · Mitte · AN"),
             ("R10o", (20, -130), "Akku-Teiler\n2 × 10 kΩ"),
             ("P3", (80, 140), "GPIO35\nCYD-Stecker P3"),
             ("Pololu", (-20, -120), "Pololu S13V10F5\n(kein EN-Pin)"),
             ("CYD", (-40, -90), "CYD 5 V\nAnschluss laut Doku offen"),
             ("Elko", (120, 155), "FET-Platine\nSource Q1 + Elko\n(Schritt 5)"),
             ("GNDbus", (-80, 80), "GND (alle zusammen)"),
         ],
         [
             ("h", "Litzenfarben", None),
             ("net", "bat", "Akku +  (OUT+ → Source Q2 / AUS)"),
             ("net", "gate", "Gate Q2  (Schalter Mitte)"),
             ("net", "vin", "geschaltet  (Drain Q2 → VIN)"),
             ("net", "v5", "5 V  (Pololu VOUT)"),
             ("net", "gnd", "GND  (OUT− und alle zusammen)"),
             ("gap", 0, 0),
             ("h", "Lötschritte", None),
             ("step", 1, "Schalter messen: Außenpin, der bei\nSchieber OBEN mit Mitte verbunden\nist, ist „AN“."),
             ("step", 2, "Mitte → Gate Q2, „AN“ → GND,\n„AUS“ → Source Q2. 47 kΩ\nzwischen G und S."),
             ("step", 3, "TC4056 OUT+ → Source Q2.\nDrain Q2 → Pololu VIN."),
             ("step", 4, "Akku-Teiler: 10 kΩ + 10 kΩ von\nDrain Q2 nach GND, Mitte → GPIO35."),
             ("step", 5, "Pololu VOUT → CYD 5 V und\nFET-Platine (Source Q1 + Elko).\nAlle GND verbinden."),
             ("gap", 0, 0),
             ("t", "Der genaue 5-V-Anschluss am CYD\nist in der Doku noch offen – deshalb\nnur als gelbe Fläche gezeigt.\n\nQ2 sitzt auf der FET-Platine\naus Schritt 5; hier vereinfacht.", None),
         ])

def do_6(raw, js, out):
    make(raw, js, out,
         "Lötschritt 6b: LED-Streifen und Regensensor in 3D",
         "Nur zum Verstehen, kein Druckteil  ·  gleiche Verbindungen wie loeten_6_led_regensensor",
         "Beim Löten kein Strom drauf – Akku ab, USB ab",
         [
             ("LED", (40, -140), "LED-Streifen (Eingang)\nPfeil zeigt vom Eingang weg"),
             ("R470", (-40, -150), "470 Ω direkt am Streifen\nin der Datenleitung"),
             ("DrainQ1", (40, -110), "5 V  ←  Drain Q1\n(Schritt 5, rot)"),
             ("GPIO23", (40, 200), "GPIO23 (SD-Pin 3)\ngrün → 470 Ω → DIN"),
             ("LEDGNDin", (380, 50), "GND (weiß)"),
             ("LM393", (-40, -130), "Regensensor-Modul\nLM393"),
             ("V33", (-90, 40), "3,3 V *  →  VCC"),
             ("GPIO19", (40, 90), "DO  →  GPIO19\n(SD-Pin 7)"),
             ("LM_AO", (80, -40), "AO frei"),
             ("Platte", (-30, -110), "Sensorplatte\n2 Kabel, egal wie rum"),
             ("Schrumpf", (160, -80), "Schrumpfschlauch\nüber den Lötstellen"),
         ],
         [
             ("h", "Kabelfarben LED-Streifen", None),
             ("net", "bat", "Rot  ·  5 V  (von Drain Q1)"),
             ("net", "din", "Grün  ·  DIN  (GPIO23 über 470 Ω)"),
             ("net", "white", "Weiß  ·  GND  (Pads prüfen)"),
             ("gap", 0, 0),
             ("h", "Regensensor (LM393)", None),
             ("net", "bat", "VCC an 3,3 V *"),
             ("net", "gnd", "GND an GND"),
             ("net", "teal", "DO an GPIO19 (SD-Pin 7)"),
             ("t", "AO bleibt frei.\nPlatte: 2 Kabel, egal wie rum.", None),
             ("gap", 0, 0),
             ("h", "Lötschritte", None),
             ("step", 1, "Den EINGANG des Streifens benutzen\n(Pfeil zeigt vom Eingang weg)."),
             ("step", 2, "470 Ω direkt am Streifen:\nGPIO23 → 470 Ω → DIN."),
             ("step", 3, "Streifen 5 V an Drain Q1\n(nicht an 3,3 V!), GND an GND."),
             ("step", 4, "Regensensor: VCC an 3,3 V,\nGND an GND, DO an GPIO19,\nAO frei."),
             ("step", 5, "Lötstellen mit Schrumpfschlauch\nisolieren. Modul-Kabel direkt\nanlöten, nicht höher als ca. 12 mm."),
             ("gap", 0, 0),
             ("t", "* 3,3-V-Abgriff am CYD laut Doku\noffen (im Test: CN1 Rot).", None),
         ])

if __name__ == "__main__":
    import sys
    rawdir = sys.argv[1] if len(sys.argv) > 1 else HERE
    outdir = sys.argv[2] if len(sys.argv) > 2 else HERE
    do_4(os.path.join(rawdir, "raw_4.png"), os.path.join(rawdir, "raw_4.json"),
         os.path.join(outdir, "loeten_4b_stromweg_3d.png"))
    do_6(os.path.join(rawdir, "raw_6.png"), os.path.join(rawdir, "raw_6.json"),
         os.path.join(outdir, "loeten_6b_led_regen_3d.png"))
