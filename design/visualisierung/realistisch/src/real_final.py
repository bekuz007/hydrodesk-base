# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE
# Beschriftet die Renderbilder aus real_scene.py (Modi v_*) und schreibt die 4 README-Bilder.
# Aufruf: python3 real_final.py <raw-Ordner> <Ausgabeordner> [ansicht,ansicht,...]
# Ansichten: explosion, innen, teile, produkt, loetteile
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../src'))   # annotate.py, fonts.py (alte Pipeline)
from PIL import Image, ImageDraw
from annotate import title, footer, labels, INK, SUB, LINE
from fonts import F
RAW = sys.argv[1]; OUT = sys.argv[2]
FOOT = 'HydroDesk Base · 180 × 100 × 25 mm · gerendert (Blender Cycles) aus dem realistischen 3D-Modell'

def load(name):
    img = Image.open(RAW + name + '.png').convert('RGB'); J = json.load(open(RAW + name + '.json')); W, H = img.size
    A = {k: [v[0]*W, v[1]*H, 0] for k, v in J['anchors'].items()}
    bb = [J['bbox'][0]*W, J['bbox'][1]*H, J['bbox'][2]*W, J['bbox'][3]*H]
    return img, A, bb, W/2560

def explosion():
    img, A, (x0, y0, x1, y1), k = load('explosion'); W, H = img.size
    specs = [
        ('cover', 'L', 'Deckel', '5-mm-Rahmen, Fenster für Display und Platte'),
        ('cap', 'L', 'Abdeckkappe USB', 'steckbar, verdeckt den Programmier-Anschluss'),
        ('cyd', 'L', 'Display-Board ESP32 „CYD“ 2,8″', 'Touch-Display + Prozessor, 50 × 86 mm'),
        ('tc', 'R', 'Lademodul TC4056', 'USB-C-Buchse an der Rückwand'),
        ('fet', 'L', 'FET-Platine (2× AO3401A)', 'Lochraster: schaltet LED-Strom (GPIO18) und Akku'),
        ('sw', 'L', 'Ein/Aus-Schalter', 'links in der Wand, schaltet über den FET den Akku'),
        ('keil', 'L', 'Klemmkeile (2×)', 'gedruckt, halten den Schalter in seiner Tasche'),
        ('cmp', 'L', 'LM393-Auswertung', 'wertet den Regensensor aus'),
        ('bat', 'L', 'LiPo-Akku 3,7 V / 2000 mAh', '34,5 × 56 × 10,3 mm, liegt unter dem Display'),
        ('boost', 'L', '5-V-Wandler Pololu S13V10F5', '12 × 9 mm, im Fach neben dem Akku'),
        ('base_l', 'L', 'Unterschale', '3D-Druck PLA, 180 × 100 × 23 mm'),
        ('led', 'L', 'COB-LED-Streifen WS2812B (26 LEDs)', '5 mm breit, auf die Rückwand der Lichtkammer geklebt'),
        ('diff', 'L', 'Diffusor-Leiste', '1 mm weißes PLA im Falz vorne, macht eine gleichmäßige Lichtlinie'),
        ('feet', 'R', 'Gummifüße (4×)', 'Ø 10 × 4,5 mm, in die Mulden unten geklebt'),
        ('m3', 'R', 'Senkschrauben M3 × 12 (8×)', 'halten Deckel und Display-Board'),
        ('mat', 'R', 'Silikonmatte 86 × 86 mm', 'rutschfest, auf die Platte geklebt'),
        ('m4', 'R', 'Senkschrauben M4 × 10 (2×)', 'Platte ans freie Ende der Wägezelle'),
        ('pad', 'R', 'Flaschenplatte 90 × 90 mm', 'liegt nur auf der Wägezelle (1 mm Spalt)'),
        ('lc', 'R', 'Wägezelle 5 kg', 'Biegebalken: hinten fest, vorne frei'),
        ('hx', 'R', 'HX711 Messverstärker', 'macht aus der Wägezelle ein Gewicht'),
        ('rs', 'R', 'Regensensor', 'in der Bodenmulde, erkennt Wasser'),
        ('m5', 'R', 'Senkschrauben M5 × 12 (2×)', 'Wägezelle von unten an die Schale'),
    ]
    colL = x0 - int(70*k); colR = x1 + int(70*k)
    labels(img, A, specs, k, colL, colR, int(190*k), H - int(125*k), gap=int(76*k))
    d = ImageDraw.Draw(img)
    title(d, k, 'HydroDesk Base – Explosionsansicht', 'So wird das Gerät von unten nach oben zusammengebaut')
    footer(d, k, W, H, FOOT)
    img.save(OUT + 'hydrodesk_explosion.png')

def innen():
    img, A, (x0, y0, x1, y1), k = load('innen'); W, H = img.size
    specs = [
        ('cyd', 'L', 'Display-Board (angehoben gezeigt)', 'sitzt später auf 4 Abstandshaltern über dem Akku'),
        ('bat', 'L', 'LiPo-Akku 2000 mAh', 'unter dem Display-Board'),
        ('boost', 'L', '5-V-Wandler Pololu S13V10F5', 'macht aus 3,7 V die 5 V fürs Board'),
        ('cmp', 'L', 'LM393-Auswertung', 'Signal „nass / trocken“ an den ESP32'),
        ('diff', 'L', 'Diffusor-Leiste + COB-LED-Streifen', '26 LEDs hinter dem Diffusor, Litzen links nach innen'),
        ('base_l', 'L', 'Unterschale (ohne Deckel)', '3D-Druck PLA'),
        ('tc', 'R', 'Lademodul TC4056', 'USB-C-Buchse hinten zum Laden'),
        ('fet', 'L', 'FET-Platine', 'schaltet LED-Strom (GPIO18) und Akku (Ein/Aus)'),
        ('sw', 'L', 'Ein/Aus-Schalter + Klemmkeile', 'links an der Wand, Pins nach Lötplan'),
        ('boss', 'R', 'Schraubdom', 'hier wird der Deckel verschraubt'),
        ('hx', 'R', 'HX711 Messverstärker', 'liest die Wägezelle aus'),
        ('lc', 'R', 'Wägezelle 5 kg', 'trägt später die Flaschenplatte'),
        ('rs', 'R', 'Regensensor', 'in der Bodenmulde unter dem Ablaufschlitz'),
        ('cables', 'R', 'Litzen', '34 Litzen nach Lötplan, farbig nach Funktion'),
    ]
    colL = x0 - int(70*k); colR = x1 + int(70*k)
    labels(img, A, specs, k, colL, colR, int(220*k), H - int(110*k), gap=int(82*k))
    d = ImageDraw.Draw(img)
    title(d, k, 'HydroDesk Base – Innenansicht', 'Unterschale ohne Deckel und Flaschenplatte, alle Module mit Verkabelung')
    footer(d, k, W, H, FOOT)
    img.save(OUT + 'hydrodesk_innen.png')

def teile():
    img, A, bb, k = load('teile'); W, H = img.size; d = ImageDraw.Draw(img)
    parts = [
        ('cover', 'Deckel', '180 × 100 × 5 mm', 'Öffnungen für Display und Platte'),
        ('base', 'Unterschale', '180 × 100 × 23 mm', 'Gehäuse mit Haltern und Lichtkammer vorne'),
        ('pad', 'Flaschenplatte', '90 × 90 × 7 mm', 'hier steht die Flasche'),
        ('cyd', 'Display-Board ESP32 CYD', '50 × 86 mm, 2,8″', 'Gehirn + Touchscreen'),
        ('bat', 'LiPo-Akku', '34,5 × 56 × 10,3 mm', '3,7 V, 2000 mAh'),
        ('mat', 'Silikonmatte', '86 × 86 × 1,2 mm', 'rutschfest, dämpft'),
        ('rs', 'Regensensor', '40 × 54 mm', 'erkennt verschüttetes Wasser'),
        ('lc', 'Wägezelle 5 kg', '80 × 12,7 × 12,7 mm', 'misst das Gewicht'),
        ('hx', 'HX711', '34 × 20 mm', 'Messverstärker für die Wägezelle'),
        ('tc', 'Lademodul TC4056', '17 × 27 mm', 'lädt den Akku über USB-C'),
        ('fet', 'FET-Platine', '25 × 30 mm', 'Lochraster mit 2× AO3401A, BC547B, Elko'),
        ('cmp', 'LM393-Auswertung', '30 × 16 mm', 'gehört zum Regensensor'),
        ('pol', '5-V-Wandler Pololu S13V10F5', '12,1 × 8,9 mm', '3,7 V → 5 V'),
        ('led', 'COB-LED-Streifen WS2812B', '162,5 × 5 mm', '26 LEDs'),
        ('screws', 'Senkschrauben DIN 7991', '8× M3×12, 2× M4×10, 2× M5×12', 'Deckel, Platte, Wägezelle'),
        ('feet', 'Gummifüße', '4×, Ø 10 × 4,5 mm', 'rutschfest unten'),
        ('cap', 'Abdeckkappe USB', '35 × 10,6 × 3,4 mm', 'steckbar, verdeckt den USB-Ausschnitt'),
        ('diff', 'Diffusor-Leiste', '166,7 × 16,7 × 1 mm', 'gedruckt, verteilt das LED-Licht'),
        ('sw', 'Ein/Aus-Schalter', '8,6 × 4,3 × 4 mm', 'Schiebeschalter ON-ON'),
        ('keil', 'Klemmkeile (2×)', '7,6 × 7,4 × 1,1 mm', 'gedruckt, halten den Schalter'),
    ]
    r = int(19*k); fB = F(int(22*k), 700)
    for i, (key, name, size, fn) in enumerate(parts):
        n = str(i+1)
        x, y = A[key+'_tl'][:2]
        cx, cy = x - int(4*k), y - int(4*k)
        if key in ('screws', 'feet', 'led', 'cap', 'diff', 'sw', 'keil'): cx, cy = x - int(26*k), y + int(10*k)
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(250, 250, 250), outline=INK, width=max(2, int(2.5*k)))
        d.text((cx, cy+1), n, font=fB, fill=INK, anchor='mm')
    mx = A['mat_br_corner'][0]; lx = int(mx + 60*k); ly = int(150*k)
    d.text((lx, int(60*k)), 'Teileübersicht', font=F(int(46*k), 700), fill=INK)
    d.text((lx, int(116*k)), 'Alle Teile der HydroDesk Base, maßstäblich (Raster 1 cm)', font=F(int(21*k), 450), fill=SUB)
    step = (H - ly - int(95*k)) / len(parts)
    for i, (key, name, size, fn) in enumerate(parts):
        yy = int(ly + i*step + 24*k)
        d.ellipse([lx, yy-r, lx+2*r, yy+r], fill=(250, 250, 250), outline=INK, width=max(2, int(2.5*k)))
        d.text((lx+r, yy+1), str(i+1), font=fB, fill=INK, anchor='mm')
        d.text((lx+2*r+int(14*k), yy-int(11*k)), name, font=F(int(27*k), 650), fill=INK, anchor='lm')
        txt = size + '  ·  ' + fn; fs = int(20*k)
        while fs > int(11*k) and d.textlength(txt, font=F(fs, 450)) > W - (lx+2*r+int(14*k)) - int(24*k): fs -= 1
        d.text((lx+2*r+int(14*k), yy+int(16*k)), txt, font=F(fs, 450), fill=SUB, anchor='lm')
    d.text((lx, H - int(62*k)), 'Nicht gezeigt: Litzen, Schrumpfschlauch, Lötzinn, 2 × 10-kΩ-Teiler', font=F(int(19*k), 450), fill=SUB)
    d.text((W - int(40*k), H - int(24*k)), 'gerendert (Blender Cycles) aus dem realistischen 3D-Modell', font=F(int(17*k), 450), fill=SUB, anchor='rs')
    img.save(OUT + 'hydrodesk_teile.png')

def produkt():
    img, A, bb, k = load('produkt'); W, H = img.size; d = ImageDraw.Draw(img)
    X = int(140*k); Y = int(420*k)
    d.text((X, Y), 'HydroDesk Base', font=F(int(104*k), 750), fill=(245, 247, 250))
    d.text((X+int(4*k), Y+int(140*k)), 'Der smarte Untersetzer für deinen Schreibtisch.', font=F(int(36*k), 450), fill=(190, 198, 208))
    feats = ['Misst jeden Schluck – mit jeder Flasche (Leer / Voll)', '2,8″ Touch-Display mit Tagesziel',
             'Leuchtlinie vorne erinnert nur, wenn du hinterherhängst', 'Wasserschutz, Akku mit Ein/Aus-Schalter, USB-C und Bluetooth']
    for i, f in enumerate(feats):
        yy = Y + int((235 + i*58)*k)
        d.ellipse([X+int(6*k), yy-int(7*k), X+int(20*k), yy+int(7*k)], fill=(40, 140, 255))
        d.text((X+int(38*k), yy), f, font=F(int(29*k), 450), fill=(220, 226, 234), anchor='lm')
    d.text((X, H-int(70*k)), '180 × 100 × 25 mm  ·  Flasche nur angedeutet (nicht im Lieferumfang)', font=F(int(22*k), 450), fill=(140, 148, 160))
    img.save(OUT + 'hydrodesk_produkt.png')


def loetteile():
    img, A, bb, k = load('loetteile'); W, H = img.size; d = ImageDraw.Draw(img)
    # Masse aus teile() bzw. design/3d_modell/realistisch/README.md (Widerstände 0207).
    parts = [
        ('hx', 'HX711', '34 × 20 mm', 'Messverstärker für die Wägezelle'),
        ('lc', 'Wägezelle 5 kg', '80 × 12,7 × 12,7 mm', '4 Drähte: Rot, Schwarz, Weiß, Grün'),
        ('cyd', 'Display-Board ESP32 CYD', '50 × 86 mm, 2,8″', 'Anschlussboard, microSD-Slot löten'),
        ('bat', 'LiPo-Akku', '34,5 × 56 × 10,3 mm', '3,7 V, 2000 mAh'),
        ('tc', 'Lademodul TC4056', '17 × 27 mm', 'lädt den Akku über USB-C'),
        ('sw', 'Ein/Aus-Schalter', '8,6 × 4,3 × 4 mm', 'Schiebeschalter ON-ON'),
        ('pol', '5-V-Wandler Pololu S13V10F5', '12,1 × 8,9 mm', '3,7 V → 5 V'),
        ('r10a', 'Widerstände 2 × 10 kΩ', 'Ø 2,3 × 6,3 mm', 'Spannungsteiler an GPIO35'),
        ('fet', 'FET-Platine', '25 × 30 mm', 'Lochraster mit 2× AO3401A, BC547B, Elko'),
        ('led', 'COB-LED-Streifen WS2812B', '162,5 × 5 mm', '26 LEDs; 5 V von Drain Q1, DIN über 470 Ω'),
        ('rs', 'Regensensor', '40 × 54 mm', 'erkennt verschüttetes Wasser'),
        ('cmp', 'LM393-Auswertung', '30 × 16 mm', 'VCC 3,3 V, GND, DO an GPIO19'),
        ('r470', 'Widerstand 470 Ω', 'Ø 2,3 × 6,3 mm', 'in die Datenleitung (DIN) des LED-Streifens'),
    ]
    groups = [
        ('s1', 'Schritt 1', 'HX711 und Wägezelle', ['hx', 'lc']),
        ('s2', 'Schritt 2', 'microSD-Slot am Display-Board', ['cyd']),
        ('s34', 'Schritt 3 und 4', 'Stromweg', ['bat', 'tc', 'pol', 'sw', 'r10a']),
        ('s5', 'Schritt 5', 'FET-Platine', ['fet']),
        ('s6', 'Schritt 6', 'LED-Streifen und Regensensor', ['led', 'rs', 'cmp', 'r470']),
    ]
    r = int(19*k); fB = F(int(22*k), 700)
    # Nummern auf der Matte, in der Reihenfolge der Legende (nach Lötschritt)
    num_of = {}
    n = 0
    for _g, _t, _s, keys in groups:
        for key in keys:
            n += 1; num_of[key] = n
            x, y = A[key+'_tl'][:2]
            cx, cy = x - int(4*k), y - int(4*k)
            if key in ('led', 'sw', 'r10a', 'r10b', 'r470', 'pol'):
                cx, cy = x - int(26*k), y + int(10*k)
            if key == 'r10a':
                # ein Kreis links neben dem Paar
                cx, cy = x - int(26*k), y + int(8*k)
            d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(250, 250, 250), outline=INK, width=max(2, int(2.5*k)))
            d.text((cx, cy+1), str(n), font=fB, fill=INK, anchor='mm')
    # Gruppenbeschriftung auf der Matte
    for gkey, title, sub, _keys in groups:
        tl = A.get('frm_%s_tl' % gkey)
        if not tl: continue
        tx, ty = tl[0] + int(10*k), tl[1] + int(16*k)
        d.text((tx+1, ty+1), title, font=F(int(22*k), 650), fill=(20, 30, 24), anchor='lt')
        d.text((tx, ty), title, font=F(int(22*k), 650), fill=(245, 248, 242), anchor='lt')
    # Legende rechts
    mx = A['mat_br_corner'][0]; lx = int(mx + 60*k); ly = int(150*k)
    d.text((lx, int(52*k)), 'Lötübersicht', font=F(int(46*k), 700), fill=INK)
    d.text((lx, int(104*k)), 'Was noch gelötet werden muss, nach Lötschritt', font=F(int(19*k), 450), fill=SUB)
    d.text((lx, int(126*k)), 'maßstäblich (Raster 1 cm)', font=F(int(19*k), 450), fill=SUB)
    # gemischte Zeilen: Überschrift + Teile
    rows = []
    for gkey, title, sub, keys in groups:
        rows.append(('h', None, '%s  ·  %s' % (title, sub), ''))
        for key in keys:
            rec = next(p for p in parts if p[0] == key)
            rows.append(('p', rec[0], rec[1], rec[2] + '  ·  ' + rec[3]))
    weights = [0.62 if kind == 'h' else 1.0 for kind, *_ in rows]
    total_w = sum(weights)
    step = (H - ly - int(100*k)) / total_w
    acc = 0.0
    for (kind, key, name, txt), w in zip(rows, weights):
        yy = int(ly + (acc + w*0.5)*step)
        acc += w
        if kind == 'h':
            d.text((lx, yy), name, font=F(int(22*k), 700), fill=INK, anchor='lm')
            continue
        d.ellipse([lx, yy-r, lx+2*r, yy+r], fill=(250, 250, 250), outline=INK, width=max(2, int(2.5*k)))
        d.text((lx+r, yy+1), str(num_of[key]), font=fB, fill=INK, anchor='mm')
        d.text((lx+2*r+int(14*k), yy-int(11*k)), name, font=F(int(27*k), 650), fill=INK, anchor='lm')
        fs = int(19*k)
        while fs > int(11*k) and d.textlength(txt, font=F(fs, 450)) > W - (lx+2*r+int(14*k)) - int(24*k):
            fs -= 1
        d.text((lx+2*r+int(14*k), yy+int(16*k)), txt, font=F(fs, 450), fill=SUB, anchor='lm')
    d.text((lx, H - int(62*k)), 'Außerdem nötig: Litzen, Schrumpfschlauch, Lötzinn', font=F(int(19*k), 450), fill=SUB)
    d.text((W - int(40*k), H - int(24*k)), 'gerendert (Blender Cycles) aus dem realistischen 3D-Modell', font=F(int(17*k), 450), fill=SUB, anchor='rs')
    img.save(OUT + 'loeten_teileuebersicht.png')

for f in (sys.argv[3].split(',') if len(sys.argv) > 3 else ['explosion', 'innen', 'teile', 'produkt']):
    globals()[f]()
print('ok')
