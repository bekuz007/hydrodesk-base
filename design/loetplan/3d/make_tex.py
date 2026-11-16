#!/usr/bin/env python3
"""Board textures with large, readable pad labels for Lötschritt 4b/6b."""
from PIL import Image, ImageDraw, ImageFont
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex")
os.makedirs(OUT, exist_ok=True)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def F(s, b=True):
    return ImageFont.truetype(FB if b else FR, s)

def save(im, name):
    path = os.path.join(OUT, name)
    im.save(path)
    print("tex", path, im.size)

def rounded(d, xy, r, fill, outline=None, w=0):
    d.rounded_rectangle(xy, r, fill=fill, outline=outline, width=w)

# ---- TC4056 17x26 mm, 20 px/mm -> 340x520 ----
def tc4056():
    s = 20
    W, H = 17*s, 26*s
    im = Image.new("RGB", (W, H), (20, 85, 155))
    d = ImageDraw.Draw(im)
    # faint traces
    d.line([(40, 80), (40, 380), (180, 380), (180, 120), (280, 120)], fill=(40, 110, 175), width=3)
    d.line([(300, 80), (300, 300), (120, 300)], fill=(40, 110, 175), width=3)
    # USB silhouette at top
    rounded(d, [70, 8, 270, 70], 16, (180, 185, 190), (80, 80, 85), 2)
    rounded(d, [90, 22, 250, 56], 10, (25, 25, 28))
    d.text((W//2, 90), "TC4056", font=F(36), fill="white", anchor="mt")
    # pads at bottom: OUT- B- B+ OUT+
    pads = [("OUT−", 1.6), ("B−", 5.5), ("B+", 11.5), ("OUT+", 15.4)]
    for name, xmm in pads:
        cx = xmm * s
        cy = 23.6 * s
        rounded(d, [cx-22, cy-22, cx+22, cy+22], 4, (200, 200, 205), (40, 40, 40), 2)
        # label above pad, rotated conceptually just as text
        d.text((cx, cy-36), name, font=F(22), fill="white", anchor="mm")
    save(im, "tc4056.png")

# ---- Pololu 8.9 x 12.1 mm, 30 px/mm -> 267x363 ----
def pololu():
    s = 30
    W, H = int(8.9*s), int(12.1*s)
    im = Image.new("RGB", (W, H), (0, 115, 70))
    d = ImageDraw.Draw(im)
    d.text((W//2, 28), "S13V10F5", font=F(28), fill="white", anchor="mt")
    d.text((W//2, 62), "Pololu", font=F(22, False), fill=(220, 240, 230), anchor="mt")
    d.text((W//2, H//2-10), "(kein EN-Pin)", font=F(18, False), fill=(210, 230, 220), anchor="mm")
    # pads along bottom: VOUT GND VIN at 1.91, 4.45, 6.99
    for name, xmm in (("VOUT", 1.91), ("GND", 4.45), ("VIN", 6.99)):
        cx = xmm * s
        cy = (12.1-1.27) * s
        d.ellipse([cx-22, cy-22, cx+22, cy+22], fill=(200, 160, 50), outline=(40, 40, 40), width=2)
        d.ellipse([cx-10, cy-10, cx+10, cy+10], fill=(15, 15, 15))
        d.text((cx, cy-36), name, font=F(20), fill="white", anchor="mm")
    save(im, "pololu.png")

# ---- LM393 16x30 mm, 20 px/mm -> 320x600 ----
def lm393():
    s = 20
    W, H = 16*s, 30*s
    im = Image.new("RGB", (W, H), (25, 70, 175))
    d = ImageDraw.Draw(im)
    # sensor pads at top
    for xmm in (6.73, 9.27):
        cx = xmm * s
        cy = 2.4 * s
        rounded(d, [cx-16, cy-16, cx+16, cy+16], 3, (195, 195, 200), (40, 40, 40), 2)
    d.text((W//2, 80), "LM393", font=F(36), fill="white", anchor="mt")
    d.text((W//2, 126), "Regensensor", font=F(20, False), fill=(210, 220, 240), anchor="mt")
    # pads at bottom: VCC GND DO AO at 4.19+i*2.54, y=28
    pads = ["VCC", "GND", "DO", "AO"]
    for i, name in enumerate(pads):
        cx = (4.19 + i*2.54) * s
        cy = 28 * s
        rounded(d, [cx-18, cy-18, cx+18, cy+18], 3, (195, 195, 200), (40, 40, 40), 2)
        d.text((cx, cy-32), name, font=F(20), fill="white", anchor="mm")
    save(im, "lm393.png")

# ---- Rain plate 40x54 mm, 12 px/mm -> 480x648 ----
def rain():
    s = 12
    W, H = 40*s, 54*s
    im = Image.new("RGB", (W, H), (28, 28, 30))
    d = ImageDraw.Draw(im)
    d.text((W//2, 18), "MH-RD", font=F(28), fill=(220, 220, 220), anchor="mt")
    # interdigitated traces
    m = 36
    x0, x1 = 28, W-28
    y0, y1 = 70, H-70
    n = 16
    gap = (y1-y0)/n
    for i in range(n):
        y = y0 + i*gap + 4
        if i % 2 == 0:
            d.rectangle([x0, y, x1-18, y+gap*0.45], fill=(210, 190, 80))
        else:
            d.rectangle([x0+18, y, x1, y+gap*0.45], fill=(210, 190, 80))
    d.rectangle([x0, y0, x0+8, y1], fill=(210, 190, 80))
    d.rectangle([x1-8, y0, x1, y1], fill=(210, 190, 80))
    # mounting holes
    for cx, cy in ((28, 28), (W-28, 28), (28, H-28), (W-28, H-28)):
        d.ellipse([cx-14, cy-14, cx+14, cy+14], fill=(80, 80, 85), outline=(180, 180, 185), width=3)
    d.text((W//2, H-22), "Sensorplatte", font=F(22, False), fill=(200, 200, 200), anchor="md")
    save(im, "rain_plate.png")

# ---- COB LED input end + short strip top texture 90x5 mm, 20 px/mm ----
def cob():
    s = 20
    W, H = 90*s, 5*s
    im = Image.new("RGB", (W, H), (235, 232, 220))
    d = ImageDraw.Draw(im)
    # pads at left: 5V, DIN, GND stacked along width (H is width)
    # looking at top: along the 5mm width, three pads
    labels = [("5V", (215, 30, 30)), ("DIN", (20, 150, 60)), ("GND", (40, 40, 40))]
    for i, (name, col) in enumerate(labels):
        cy = 16 + i * 28
        rounded(d, [8, cy-12, 70, cy+12], 3, (200, 175, 60), (60, 50, 20), 2)
        # label to the right of pad in dark
        d.rectangle([76, cy-11, 150, cy+11], fill=col)
        d.text((113, cy), name, font=F(16), fill="white", anchor="mm")
    # arrow
    d.polygon([(400, 20), (520, 50), (400, 80), (420, 50)], fill=(40, 40, 40))
    d.text((700, H//2), "Eingang  →", font=F(28), fill=(40, 40, 40), anchor="mm")
    # cut marks
    for x in range(200, W, 250):
        d.rectangle([x, 4, x+4, H-4], fill=(180, 180, 170))
    save(im, "cob_top.png")

# ---- CYD 5V stub 28x20 mm ----
def cyd5v():
    s = 16
    W, H = 28*s, 20*s
    im = Image.new("RGB", (W, H), (235, 200, 20))
    d = ImageDraw.Draw(im)
    d.text((W//2, 28), "CYD 5 V", font=F(36), fill=(30, 30, 20), anchor="mt")
    d.text((W//2, 80), "Anschluss", font=F(22, False), fill=(50, 40, 10), anchor="mt")
    d.text((W//2, 112), "laut Doku offen", font=F(20, False), fill=(50, 40, 10), anchor="mt")
    # pad
    cx, cy = W//2, H-50
    d.ellipse([cx-28, cy-28, cx+28, cy+28], fill=(200, 160, 50), outline=(40, 40, 40), width=3)
    d.ellipse([cx-12, cy-12, cx+12, cy+12], fill=(20, 20, 20))
    d.text((cx, cy-44), "5 V", font=F(22), fill=(30, 30, 20), anchor="mm")
    save(im, "cyd5v.png")

# ---- FET Q1+Elko destination board 28x20 ----
def fet_q1():
    s = 16
    W, H = 28*s, 20*s
    im = Image.new("RGB", (W, H), (25, 110, 60))
    d = ImageDraw.Draw(im)
    d.text((W//2, 24), "FET-Platine", font=F(28), fill="white", anchor="mt")
    d.text((W//2, 64), "Source Q1 + Elko", font=F(22), fill=(220, 240, 225), anchor="mt")
    d.text((W//2, 96), "(Schritt 5)", font=F(18, False), fill=(200, 230, 210), anchor="mt")
    cx, cy = W//2 - 40, H-50
    d.ellipse([cx-26, cy-26, cx+26, cy+26], fill=(200, 160, 50), outline=(40, 40, 40), width=2)
    d.ellipse([cx-10, cy-10, cx+10, cy+10], fill=(20, 20, 20))
    d.text((cx, cy-40), "5 V", font=F(18), fill="white", anchor="mm")
    save(im, "fet_q1.png")

# ---- P3 header plate ----
def p3():
    s = 20
    W, H = 22*s, 12*s
    im = Image.new("RGB", (W, H), (50, 50, 55))
    d = ImageDraw.Draw(im)
    d.text((W//2, 16), "CYD-Stecker P3", font=F(26), fill="white", anchor="mt")
    d.text((W//2, 56), "GPIO35", font=F(32), fill=(255, 220, 80), anchor="mt")
    d.text((W//2, H-20), "Akku-Teiler Mitte", font=F(16, False), fill=(200, 200, 200), anchor="md")
    save(im, "p3.png")

# ---- simplified Q2 board silkscreen 28x22 mm ----
def q2board():
    s = 18
    W, H = 28*s, 22*s
    im = Image.new("RGB", (W, H), (28, 115, 62))
    d = ImageDraw.Draw(im)
    d.text((16, 14), "FET-Platine  ·  Q2 Ein/Aus", font=F(22), fill="white", anchor="lt")
    save(im, "q2board.png")

# ---- switch top label 12x20 (enlarged feel) ----
def sw():
    s = 24
    W, H = 10*s, 20*s
    im = Image.new("RGB", (W, H), (70, 70, 75))
    d = ImageDraw.Draw(im)
    d.text((W//2, 16), "Ein/Aus", font=F(22), fill="white", anchor="mt")
    for name, y in (("AN", 70), ("Mitte", 240), ("AUS", 410)):
        d.text((W//2, y), name, font=F(26), fill=(255, 230, 80) if name!="Mitte" else "white", anchor="mm")
    save(im, "switch.png")

if __name__ == "__main__":
    tc4056(); pololu(); lm393(); rain(); cob(); cyd5v(); fet_q1(); p3(); q2board(); sw()
