import json, sys
from PIL import Image, ImageDraw
from annotate import compose, content_bbox, title, footer, labels, INK, SUB, LINE
from fonts import F
RAW = sys.argv[1] if len(sys.argv) > 1 else '../raw/'
OUT = sys.argv[2] if len(sys.argv) > 2 else '../'
PFX = sys.argv[3] if len(sys.argv) > 3 else ''
FOOT = 'HydroDesk Base · 180 × 100 × 25 mm · gerendert aus dem OpenSCAD-Modell'

def load(name):
    img, raw = compose(RAW + PFX + name + '.png', dark=(name == 'produkt'))
    A = json.load(open(RAW + PFX + name + '.json'))
    return img, raw, A, img.size[0]/2560

def explosion():
    img, raw, A, k = load('explosion')
    x0, y0, x1, y1 = content_bbox(raw); W, H = img.size
    specs = [
        ('cover', 'L', 'Deckel', '5-mm-Rahmen, Fenster für Display und Platte'),
        ('cap', 'L', 'Abdeckkappe USB', 'steckbar, verdeckt den Programmier-Anschluss'),
        ('cyd', 'L', 'Display-Board ESP32 „CYD“ 2,8″', 'Touch-Display + Prozessor, 50 × 86 mm'),
        ('tc', 'L', 'Lademodul TC4056', 'USB-C-Buchse an der Rückwand'),
        ('fet', 'L', 'FET-Schaltmodul', 'trennt den Strom, wenn Wasser erkannt wird'),
        ('cmp', 'L', 'LM393-Auswertung', 'wertet den Regensensor aus'),
        ('bat', 'L', 'LiPo-Akku 3,7 V / 2000 mAh', '34 × 55 × 10 mm, liegt unter dem Display'),
        ('boost', 'L', '5-V-Wandler Pololu S13V10F5', '12 × 9 mm, im Fach neben dem Akku'),
        ('base_l', 'L', 'Unterschale', '3D-Druck PLA, 180 × 100 × 23 mm'),
        ('led', 'L', 'COB-LED-Streifen WS2812B (26 LEDs)', '5 mm breit, auf die Rückwand der Lichtkammer geklebt'),
        ('diff', 'L', 'Diffusor-Leiste', '1 mm weißes PLA im Falz vorne, macht eine gleichmäßige Lichtlinie'),
        ('feet', 'R', 'Gummifüße (4×)', 'in die Mulden unten geklebt'),
        ('m3', 'R', 'Schrauben M3 × 12 (8×)', 'halten Deckel und Display-Board'),
        ('mat', 'R', 'Silikonmatte 86 × 86 mm', 'rutschfest, auf die Platte geklebt'),
        ('m4', 'R', 'Schrauben M4 (2×)', 'Platte ans freie Ende der Wägezelle'),
        ('pad', 'R', 'Flaschenplatte 90 × 90 mm', 'liegt nur auf der Wägezelle (1 mm Spalt)'),
        ('lc', 'R', 'Wägezelle 5 kg', 'Biegebalken: hinten fest, vorne frei'),
        ('hx', 'R', 'HX711 Messverstärker', 'macht aus der Wägezelle ein Gewicht'),
        ('rs', 'R', 'Regensensor', 'in der Bodenmulde, erkennt Wasser'),
        ('m5', 'R', 'Schrauben M5 (2×)', 'Wägezelle von unten an die Schale'),
    ]
    colL = x0 - int(70*k); colR = x1 + int(70*k)
    labels(img, A, specs, k, colL, colR, int(190*k), H - int(90*k), gap=int(76*k))
    d = ImageDraw.Draw(img)
    title(d, k, 'HydroDesk Base – Explosionsansicht', 'So wird das Gerät von unten nach oben zusammengebaut')
    footer(d, k, W, H, FOOT)
    img.convert('RGB').save(OUT + 'hydrodesk_explosion.png')

def innen():
    img, raw, A, k = load('innen')
    x0, y0, x1, y1 = content_bbox(raw); W, H = img.size
    specs = [
        ('cyd', 'L', 'Display-Board (angehoben gezeigt)', 'sitzt auf 4 Abstandshaltern über dem Akku'),
        ('bat', 'L', 'LiPo-Akku 2000 mAh', 'unter dem Display-Board'),
        ('boost', 'L', '5-V-Wandler Pololu S13V10F5', 'macht aus 3,7 V die 5 V fürs Board'),
        ('cmp', 'L', 'LM393-Auswertung', 'Signal „nass / trocken“ an den ESP32'),
        ('diff', 'L', 'Diffusor-Leiste + COB-LED-Streifen', '26 LEDs hinter dem Diffusor, Kabel links nach innen'),
        ('base_l', 'L', 'Unterschale (ohne Deckel)', '3D-Druck PLA'),
        ('tc', 'R', 'Lademodul TC4056', 'USB-C-Buchse hinten zum Laden'),
        ('fet', 'L', 'FET-Schaltmodul', 'Strom aus, wenn Wasser erkannt wird'),
        ('boss', 'R', 'Schraubdom', 'hier wird der Deckel verschraubt'),
        ('hx', 'R', 'HX711 Messverstärker', 'liest die Wägezelle aus'),
        ('lc', 'R', 'Wägezelle 5 kg', 'trägt später die Flaschenplatte'),
        ('rs', 'R', 'Regensensor', 'in der Bodenmulde unter dem Ablaufschlitz'),
        ('cables', 'R', 'Kabel', 'rot +, schwarz −, gelb/weiß/grün Signal'),
    ]
    colL = x0 - int(70*k); colR = x1 + int(70*k)
    labels(img, A, specs, k, colL, colR, int(220*k), H - int(110*k), gap=int(82*k))
    d = ImageDraw.Draw(img)
    title(d, k, 'HydroDesk Base – Innenansicht', 'Unterschale ohne Deckel und Flaschenplatte, alle Module an ihrem Platz')
    footer(d, k, W, H, FOOT)
    img.convert('RGB').save(OUT + 'hydrodesk_innen.png')

def teile():
    img, raw, A, k = load('teile')
    W, H = img.size; d = ImageDraw.Draw(img)
    parts = [
        ('cover', 'Deckel', '180 × 100 × 5 mm', 'Öffnungen für Display und Platte'),
        ('base', 'Unterschale', '180 × 100 × 23 mm', 'Gehäuse mit Haltern und Lichtkammer vorne'),
        ('pad', 'Flaschenplatte', '90 × 90 × 7 mm', 'hier steht die Flasche'),
        ('cyd', 'Display-Board ESP32 CYD', '50 × 86 mm, 2,8″', 'Gehirn + Touchscreen'),
        ('bat', 'LiPo-Akku', '34 × 55 × 10 mm', '3,7 V, 2000 mAh'),
        ('mat', 'Silikonmatte', '86 × 86 mm', 'rutschfest, dämpft'),
        ('rs', 'Regensensor', '40 × 54 mm', 'erkennt verschüttetes Wasser'),
        ('lc', 'Wägezelle 5 kg', '80 × 12,7 × 12,7 mm', 'misst das Gewicht'),
        ('hx', 'HX711', '34 × 21 mm', 'Messverstärker für die Wägezelle'),
        ('tc', 'Lademodul TC4056', '26 × 17 mm', 'lädt den Akku über USB-C'),
        ('fet', 'FET-Schaltmodul', '30 × 17 mm', 'schaltet den Strom ab'),
        ('cmp', 'LM393-Auswertung', '30 × 16 mm', 'gehört zum Regensensor'),
        ('boost', '5-V-Wandler Pololu S13V10F5', '12,1 × 8,9 mm', '3,7 V → 5 V'),
        ('led', 'COB-LED-Streifen WS2812B', '162,5 × 5 mm', '26 LEDs (13 Segmente)'),
        ('screws', 'Schrauben', '8× M3×12, 2× M4×10, 2× M5×12', 'Deckel, Platte, Wägezelle'),
        ('feet', 'Gummifüße', '4×, Ø 13 mm', 'rutschfest unten'),
        ('cap', 'Abdeckkappe USB', '35 × 10,6 × 3,4 mm', 'steckbar, verdeckt den USB-Ausschnitt'),
        ('diff', 'Diffusor-Leiste', '166,7 × 16,7 × 1 mm', 'gedruckt, verteilt das LED-Licht'),
    ]
    r = int(19*k); fB = F(int(22*k), 700)
    for i, (key, name, size, fn) in enumerate(parts):
        n = str(i+1)
        x, y = A[key+'_tl'][:2]
        cx, cy = x - int(4*k), y - int(4*k)
        if key in ('screws', 'feet', 'led', 'cap', 'diff'): cx, cy = x - int(26*k), y + int(10*k)
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(250, 250, 250), outline=INK, width=max(2, int(2.5*k)))
        d.text((cx, cy+1), n, font=fB, fill=INK, anchor='mm')
    # Legende rechts
    mx = A['mat_br_corner'][0]; lx = int(mx + 60*k); ly = int(150*k)
    d.text((lx, int(60*k)), 'Teileübersicht', font=F(int(46*k), 700), fill=INK)
    d.text((lx, int(116*k)), 'Alle Teile der HydroDesk Base, maßstäblich (Raster 1 cm)', font=F(int(21*k), 450), fill=SUB)
    step = (H - ly - int(70*k)) / len(parts)
    for i, (key, name, size, fn) in enumerate(parts):
        yy = int(ly + i*step + 24*k)
        d.ellipse([lx, yy-r, lx+2*r, yy+r], fill=(250, 250, 250), outline=INK, width=max(2, int(2.5*k)))
        d.text((lx+r, yy+1), str(i+1), font=fB, fill=INK, anchor='mm')
        d.text((lx+2*r+int(14*k), yy-int(11*k)), name, font=F(int(27*k), 650), fill=INK, anchor='lm')
        txt = size + '  ·  ' + fn; fs = int(20*k)
        while fs > int(11*k) and d.textlength(txt, font=F(fs, 450)) > W - (lx+2*r+int(14*k)) - int(24*k): fs -= 1
        d.text((lx+2*r+int(14*k), yy+int(16*k)), txt, font=F(fs, 450), fill=SUB, anchor='lm')
    img.convert('RGB').save(OUT + 'hydrodesk_teile.png')

def produkt():
    img, raw, A, k = load('produkt')
    W, H = img.size; d = ImageDraw.Draw(img)
    X = int(140*k); Y = int(420*k)
    d.text((X, Y), 'HydroDesk Base', font=F(int(104*k), 750), fill=(245, 247, 250))
    d.text((X+int(4*k), Y+int(140*k)), 'Der smarte Untersetzer für deinen Schreibtisch.', font=F(int(36*k), 450), fill=(190, 198, 208))
    feats = ['Misst jeden Schluck – mit jeder Flasche (Leer / Voll)', '2,8″ Touch-Display mit Tagesziel',
             'Leuchtlinie vorne erinnert nur, wenn du hinterherhängst', 'Wasserschutz, Akku, USB-C und Bluetooth']
    for i, f in enumerate(feats):
        yy = Y + int((235 + i*58)*k)
        d.ellipse([X+int(6*k), yy-int(7*k), X+int(20*k), yy+int(7*k)], fill=(40, 140, 255))
        d.text((X+int(38*k), yy), f, font=F(int(29*k), 450), fill=(220, 226, 234), anchor='lm')
    d.text((X, H-int(70*k)), '180 × 100 × 25 mm  ·  Flasche nur angedeutet (nicht im Lieferumfang)', font=F(int(22*k), 450), fill=(140, 148, 160))
    img.convert('RGB').save(OUT + 'hydrodesk_produkt.png')

for f in (sys.argv[4].split(',') if len(sys.argv) > 4 else ['explosion', 'innen', 'teile', 'produkt']):
    globals()[f]()
print('ok')
