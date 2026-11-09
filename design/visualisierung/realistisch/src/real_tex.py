# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE
# Selbst gezeichnete Platinen-Aufdrucke und Etiketten (PIL). Keine Produktfotos als Textur
# (Fotos nur als Vorlage, siehe README), damit das Repo frei von fremden Bildrechten bleibt.
import os, sys, math, random
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cyd_layout as L
OUT = os.path.join(HERE, 'tex')
os.makedirs(OUT, exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONTN = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTC = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
from PIL import ImageFont
_fc = {}
def font(px, f=FONT):
    k = (px, f)
    if k not in _fc: _fc[k] = ImageFont.truetype(f, max(6, int(px)))
    return _fc[k]

class Board:
    """Zeichenflaeche in mm (Ursprung oben links, v nach unten)."""
    def __init__(self, w, l, ppm, col):
        self.w, self.l, self.k = w, l, ppm
        self.im = Image.new('RGB', (int(w*ppm), int(l*ppm)), col); self.d = ImageDraw.Draw(self.im)
    def P(self, u, v): return (u*self.k, v*self.k)
    def rect(self, u, v, du, dv, col, outline=None, w=0.12):
        self.d.rectangle([*self.P(u, v), *self.P(u+du, v+dv)], fill=col, outline=outline, width=max(1, int(w*self.k)) if outline else 0)
    def crect(self, u, v, du, dv, col, **kw): self.rect(u-du/2, v-dv/2, du, dv, col, **kw)
    def circ(self, u, v, r, col, outline=None, w=0.12):
        self.d.ellipse([*self.P(u-r, v-r), *self.P(u+r, v+r)], fill=col, outline=outline, width=max(1, int(w*self.k)) if outline else 0)
    def line(self, pts, col, w=0.25):
        self.d.line([self.P(*p) for p in pts], fill=col, width=max(1, int(w*self.k)), joint='curve')
    def text(self, u, v, s, h, col=(245, 245, 240), anchor='la', f=FONT, rot=0):
        if rot == 0:
            self.d.text(self.P(u, v), s, font=font(h*self.k, f), fill=col, anchor=anchor); return
        fn = font(h*self.k, f); bb = fn.getbbox(s); tw, th = bb[2]+4, bb[3]+4
        t = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); ImageDraw.Draw(t).text((2, 2), s, font=fn, fill=col)
        t = t.rotate(rot, expand=True); x, y = self.P(u, v)
        self.im.paste(t, (int(x - t.width/2), int(y - t.height/2)), t)
    def save(self, name, blur=0.0):
        im = self.im.filter(ImageFilter.GaussianBlur(blur)) if blur else self.im
        im.save(os.path.join(OUT, name)); print('tex', name, im.size)

def traces(b, col, n, seed, box, w=0.22):
    """zufaellige, aber rechtwinklige Leiterbahnen (nur Optik)"""
    rnd = random.Random(seed); u0, v0, u1, v1 = box
    for _ in range(n):
        u, v = rnd.uniform(u0, u1), rnd.uniform(v0, v1); pts = [(u, v)]
        for _ in range(rnd.randint(2, 4)):
            if rnd.random() < 0.5: u = min(u1, max(u0, u + rnd.uniform(-12, 12)))
            else: v = min(v1, max(v0, v + rnd.uniform(-12, 12)))
            if rnd.random() < 0.4:
                dd = rnd.uniform(-3, 3); u = min(u1, max(u0, u+dd)); v = min(v1, max(v0, v+abs(dd)))
            pts.append((u, v))
        b.line(pts, col, w)
        b.circ(*pts[-1], 0.28, col)

# ---------------- CYD Rueckseite (orange Loetstopplack) ----------------
OR = (236, 140, 28); OR_T = (247, 160, 45); TIN = (205, 205, 200); SILK = (250, 250, 245)
def cyd_back():
    b = Board(L.PCB_W, L.PCB_L, 24, OR)
    traces(b, OR_T, 150, 7, (1, 1, 49, 85), 0.25)
    for (name, typ, u, v, du, dv, h) in L.PARTS:
        if typ in ('jst4v', 'jst4h', 'jst2'):
            b.rect(u-0.3, v-0.3, du+0.6, dv+0.6, TIN)
        elif typ == 'sd':
            b.rect(u-0.4, v-0.4, du+0.8, dv+0.8, (200, 120, 20))
            for i in range(8):
                vv = L.SD_PIN1_V + i*L.SD_PITCH; b.rect(L.SD_TAIL_U-0.7, vv-0.3, 1.4, 0.6, TIN)
        elif typ != 'esp':
            b.rect(u-0.3, v-0.3, du+0.6, dv+0.6, TIN)
    for (u, v, q) in L.PASSIVES:
        if q: b.crect(u, v-0.75, 0.9, 0.7, TIN); b.crect(u, v+0.75, 0.9, 0.7, TIN)
        else: b.crect(u-0.75, v, 0.7, 0.9, TIN); b.crect(u+0.75, v, 0.7, 0.9, TIN)
    # U4 (leer): SOIC-8-Pads
    u, v, du, dv = L.U4
    b.rect(u, v, du, dv, None, outline=SILK, w=0.15)
    for i in range(4):
        b.crect(u+0.9, v+1.6+i*1.27*1.6, 1.4, 0.6, TIN); b.crect(u+du-0.9, v+1.6+i*1.27*1.6, 1.4, 0.6, TIN)
    b.text(u+du/2, v+dv/2, 'U4', 1.4, anchor='mm')
    for n, (u, v) in L.TESTPADS.items():
        b.circ(u, v, 0.8, TIN); b.text(u-1.2, v, n, 1.1, anchor='rm')
    # Montageloecher-Ringe
    for (u, v) in [(4, 4), (46, 4), (4, 82), (46, 82)]:
        b.circ(u, v, 3.0, TIN)
    # Aufdruck
    b.text(44.6, 10.9, 'GND', 1.2, anchor='rm'); b.text(44.6, 12.9, 'IO35', 1.2, anchor='rm')
    b.text(44.6, 14.9, 'IO22', 1.2, anchor='rm'); b.text(44.6, 16.9, 'IO21', 1.2, anchor='rm')
    b.text(44.6, 27.0, 'GND', 1.2, anchor='rm'); b.text(44.6, 29.0, 'IO22', 1.2, anchor='rm')
    b.text(44.6, 31.0, 'IO27', 1.2, anchor='rm'); b.text(44.6, 33.0, '3.3V', 1.2, anchor='rm')
    b.text(48.0, 9.6, 'P3', 1.3, anchor='mm'); b.text(48.0, 25.7, 'CN1', 1.3, anchor='mm')
    b.text(2.0, 64.2, 'SPEAK', 1.2, anchor='lm'); b.text(2.0, 54.6, 'P4', 1.2, anchor='lm')
    b.text(8.2, 8.8, 'RST', 1.1, anchor='lm'); b.text(8.2, 12.9, 'BOOT', 1.1, anchor='lm')
    b.text(10.6, 80.4, 'VIN', 1.1, anchor='rm'); b.text(10.6, 81.9, 'TX', 1.1, anchor='rm')
    b.text(10.6, 83.4, 'RX', 1.1, anchor='rm'); b.text(10.6, 84.9, 'GND', 1.1, anchor='rm')
    b.text(35.2, 25.0, 'HW-458', 2.0, rot=90); b.text(41.0, 38.8, 'V12', 1.3, anchor='mm')
    b.text(12.0, 47.0, 'ESP32-2432S028', 2.2, col=(250, 235, 200), rot=90)
    b.text(34.0, 1.2, 'U2', 1.3); b.text(14.0, 0.8, 'U1', 1.2)
    b.text(14.0, 72.5, 'JP3', 1.1, rot=90); b.text(22.6, 72.5, 'JP0', 1.1, rot=90)
    # Recycling-Dreieck + Pb-Kreis (nur angedeutet)
    b.line([(17, 37), (27, 37), (22, 46), (17, 37)], SILK, 0.25)
    b.circ(22, 52, 3.6, None, outline=SILK, w=0.25); b.text(22, 52, 'Pb', 2.4, anchor='mm')
    b.line([(19.5, 49.5), (24.5, 54.5)], SILK, 0.25)
    b.save('cyd_back.png', 0.6)

def cyd_front():
    b = Board(L.PCB_W, L.PCB_L, 16, OR)
    traces(b, OR_T, 25, 3, (1, 1, 49, 85), 0.25)
    b.text(25, 84.0, 'ESP32-2432S028R', 1.8, anchor='mm')
    b.circ(8, 83.0, 1.1, (190, 70, 40))     # LDR
    for (u, v) in [(4, 4), (46, 4), (4, 82), (46, 82)]: b.circ(u, v, 3.0, TIN)
    b.save('cyd_front.png', 0.6)

def esp_shield():
    b = Board(17, 17.4, 40, (196, 198, 202))
    b.text(8.5, 4.5, 'WiFi+BT  N4XX', 1.35, col=(70, 72, 78), anchor='mm')
    b.circ(4.8, 10.2, 1.4, None, outline=(70, 72, 78), w=0.18)
    b.text(4.8, 10.2, 'B', 1.4, col=(70, 72, 78), anchor='mm')
    b.text(10.5, 10.2, 'FC CE', 2.0, col=(70, 72, 78), anchor='mm')
    b.circ(2.0, 15.2, 0.5, (60, 60, 64))
    b.save('esp_shield.png', 0.5)

def esp_antenna():
    b = Board(18, 7.2, 40, (18, 18, 20))
    pts = [(1.5, 6.2), (1.5, 1.2)]
    x = 1.5
    for i in range(7):
        x += 2.0; pts += [(x, 1.2), (x, 5.0)] if i % 2 == 0 else [(x, 5.0), (x, 1.2)]
    b.line(pts, (190, 150, 60), 0.5)
    b.save('esp_antenna.png', 0.4)

# ---------------- TC4056 (blau-tuerkis) ----------------
def tc4056():
    TE = (22, 110, 140); TT = (30, 120, 150)
    b = Board(17, 26, 40, TE)
    traces(b, TT, 14, 11, (1, 3, 16, 23), 0.25)
    for (u, v) in [(1.6, 2.2), (15.4, 2.2)]:
        b.crect(u, v, 2.4, 2.4, TIN)
    for (u, v) in [(1.6, 23.6), (5.5, 23.6), (11.5, 23.6), (15.4, 23.6)]:
        b.crect(u, v, 2.4, 2.4, TIN)
    b.text(3.0, 5.4, '-', 1.6, anchor='mm'); b.text(14.2, 5.4, '+', 1.6, anchor='mm')
    b.text(2.3, 17.0, '4056', 1.3, rot=90)
    b.text(1.8, 20.6, 'OUT-', 1.1, rot=90); b.text(15.4, 20.6, 'OUT+', 1.1, rot=90)
    b.text(5.5, 21.6, 'B-', 1.1, anchor='mm'); b.text(11.5, 21.6, 'B+', 1.1, anchor='mm')
    for s, u, v in [('R1', 12.3, 13.0), ('R2', 12.0, 8.8), ('R3', 3.2, 9.8), ('R4', 3.6, 8.0), ('C3', 7.0, 8.0),
                    ('C4', 3.2, 12.2), ('U1', 8.0, 14.2), ('C1', 9.8, 14.4), ('R6', 4.6, 16.2), ('C2', 11.0, 16.4),
                    ('U3', 5.4, 17.6), ('U2', 11.6, 17.6), ('R5', 14.4, 15.8), ('R8', 15.6, 5.4)]:
        b.text(u, v, s, 0.9, anchor='mm')
    b.rect(7.2, 24.6, 2.6, 1.4, (255, 255, 255))   # Kerbe (weiss = wird ausgeschnitten)
    b.save('tc4056.png', 0.5)

# ---------------- HX711 (gruen, 34 x 20) ----------------
GR = (20, 135, 60); GT = (28, 146, 68)
def hx711():
    b = Board(34, 20, 30, GR)
    traces(b, GT, 30, 5, (6, 2, 28, 18), 0.3)
    b.rect(2.6, 2.0, 2.8, 16.4, None, outline=SILK, w=0.18)
    for i, s in enumerate(['E+', 'E-', 'A-', 'A+', 'B-', 'B+']):
        v = 3.7 + i*2.54; b.circ(4.0, v, 0.85, TIN); b.circ(4.0, v, 0.45, (30, 30, 30)); b.text(2.2, v, s, 1.2, anchor='rm')
    b.text(4.0, 1.3, 'J1', 1.2, anchor='mm')
    b.rect(28.6, 5.0, 2.8, 10.2, None, outline=SILK, w=0.18)
    for i, s in enumerate(['GND', 'DT', 'SCK', 'VCC']):
        v = 6.4 + i*2.54; b.circ(30.0, v, 0.85, TIN); b.circ(30.0, v, 0.45, (30, 30, 30)); b.text(32.0, v, s, 1.0, anchor='lm')
    for (u, v) in [(30.0, 2.7), (30.0, 17.5)]: b.circ(u, v, 1.9, TIN); b.circ(u, v, 1.45, (120, 121, 124))
    b.text(15.5, 2.0, 'U7', 1.2, anchor='mm'); b.text(15.0, 18.5, 'MH', 1.4, anchor='mm')
    for s, u, v in [('Q2', 11.2, 1.6), ('C6', 23.8, 2.5), ('R12', 8.6, 12.0), ('R13', 11.0, 12.0), ('R8', 8.6, 16.4),
                    ('C4', 11.0, 16.4), ('C8', 15.0, 15.0), ('C7', 20.6, 15.0), ('C5', 22.8, 9.6), ('R9', 25.4, 9.6)]:
        b.text(u, v, s, 0.9, anchor='mm')
    b.save('hx711.png', 0.5)

# ---------------- LM393-Modul (blau, 16 x 30) ----------------
def lm393():
    BL = (20, 60, 170); BT = (28, 70, 182)
    b = Board(16, 30, 30, BL)
    traces(b, BT, 10, 2, (1, 4, 15, 26), 0.25)
    for (u, v) in [(2.0, 2.0), (14.0, 2.0)]: b.circ(u, v, 1.5, (120, 121, 124))
    for i, s in enumerate(['VCC', 'GND', 'DO', 'AO']):
        u = 4.19 + i*2.54; b.crect(u, 28.0, 1.7, 1.7, TIN); b.text(u, 25.6, s, 0.85, anchor='mm', rot=90)
    for i in range(2):
        u = 6.73 + i*2.54; b.crect(u, 2.4, 1.7, 1.7, TIN)
    b.text(3.0, 19.0, 'PWR-LED', 0.8, rot=90); b.text(13.0, 19.0, 'DO-LED', 0.8, rot=90)
    b.save('lm393.png', 0.5)

def rain_plate():
    b = Board(40, 54, 24, (22, 22, 24))
    S = (222, 222, 215)
    b.rect(2.0, 6.0, 36.0, 1.0, S); b.rect(2.0, 6.0, 1.0, 46.0, S)          # linker Kamm
    b.rect(37.0, 8.0, 1.0, 44.0, S)                                       # rechter Kamm
    for i in range(12):
        v = 8.5 + i*3.6
        b.rect(3.0, v, 33.0, 0.9, S)
        if v + 1.8 < 51.5: b.rect(4.0, v+1.8, 33.0, 0.9, S)
    b.rect(2.0, 51.0, 36.0, 1.0, S)
    for (u, v) in [(2.2, 2.2), (37.8, 2.2), (2.2, 51.8), (37.8, 51.8)]: b.circ(u, v, 1.6, S); b.circ(u, v, 1.0, (40, 40, 40))
    b.text(13.0, 3.0, 'MH-RD', 1.7, col=S, anchor='mm')
    b.text(20.0, 53.0, 'Raindrops module', 1.4, col=S, anchor='mm')
    b.save('rain_plate.png', 0.5)

def pololu():
    PG = (30, 140, 55)
    b = Board(8.9, 12.1, 60, PG)
    for i, s in enumerate(['VOUT', 'GND', 'VIN']):
        u = 1.91 + i*2.54
        b.circ(u, 12.1-1.27, 0.85, (210, 170, 80)); b.circ(u, 12.1-1.27, 0.5, (25, 25, 25))
        b.text(u, 8.9, s, 0.75, anchor='mm', rot=90)
    b.circ(0.8, 0.8, 0.45, (210, 170, 80))
    b.text(4.45, 7.0, '*', 1.6, anchor='mm')
    b.save('pololu.png', 0.4)

def lipo_label():
    # Etikett im Stil des EEMB LP103454 (Text aus dem Datenblatt/Shop, Logo nur als Schrift)
    b = Board(34.5, 46.0, 30, (214, 216, 220))
    K = (25, 25, 28)
    b.rect(2.0, 2.0, 8.5, 3.2, K); b.text(6.25, 3.6, 'EEMB', 2.2, col=(214, 216, 220), anchor='mm')
    b.text(2.0, 7.2, 'Rechargeable Li-ion Polymer Battery', 1.45, col=K, f=FONTN)
    b.text(2.0, 10.0, 'LP103454', 2.4, col=K)
    b.text(2.0, 13.8, '3.7V  2000mAh  7.4Wh', 1.9, col=K)
    b.text(2.0, 16.8, 'Red (+)  Black (-)   (1ICP11/35/55)', 1.2, col=K, f=FONTN)
    b.line([(2.0, 19.0), (32.5, 19.0)], K, 0.12)
    for i, s in enumerate(['Do not disassemble or modify,', 'short-circuit, dispose in fire,', 'expose to high temperature.']):
        b.text(4.0, 20.0 + i*1.6, s, 1.0, col=K, f=FONTN)
    b.d.polygon([b.P(2.0, 22.6), b.P(3.4, 20.2), b.P(2.0+2.8, 22.6)], outline=K)
    b.text(20.0, 27.5, 'CE', 4.2, col=K, anchor='mm')
    # Muelltonne durchgestrichen
    b.rect(28.0, 21.0, 3.0, 3.8, None, outline=K, w=0.15); b.line([(27.6, 20.6), (31.4, 25.2)], K, 0.15); b.line([(31.4, 20.6), (27.6, 25.2)], K, 0.15)
    b.text(2.0, 30.0, 'Made in China', 1.1, col=K, f=FONTN)
    b.save('lipo_label.png', 0.4)

def lochraster_silk():
    b = Board(30, 24.5, 30, (25, 120, 60))
    b.save('lochraster.png', 0.3)

def sot23_adapter():
    b = Board(12.7, 10.2, 60, (25, 130, 60))
    b.text(6.35, 1.2, 'SOT23', 1.0, anchor='mm'); b.text(1.0, 1.1, '1', 0.9, anchor='mm'); b.text(11.7, 1.1, '10', 0.9, anchor='mm')
    b.text(1.0, 9.1, '5', 0.9, anchor='mm'); b.text(11.7, 9.1, '6', 0.9, anchor='mm')
    b.text(6.35, 9.1, '0.95MM', 0.9, anchor='mm')
    b.save('sot23_adapter.png', 0.3)

def lc_label():
    b = Board(80, 12.7, 20, (238, 238, 232)); K = (20, 20, 20)
    b.rect(0.6, 0.6, 78.8, 11.5, None, outline=K, w=0.15)
    b.text(6, 4.2, '5kg', 3.2, col=K, anchor='lm'); b.text(6, 9.2, 'TAL220', 1.8, col=K, anchor='lm', f=FONTN)
    b.line([(24, 3.0), (24, 10.0)], K, 0.5); b.d.polygon([b.P(22.4, 9.0), b.P(25.6, 9.0), b.P(24, 11.4)], fill=K)
    b.text(30, 6.4, 'Rated output 1.0 mV/V   Red E+  Black E-  Green A+  White A-', 1.45, col=K, anchor='lm', f=FONTN)
    b.save('lc_label.png', 0.3)

if __name__ == '__main__':
    lc_label()
    cyd_back(); cyd_front(); esp_shield(); esp_antenna(); tc4056(); hx711(); lm393(); rain_plate(); pololu(); lipo_label(); sot23_adapter()
