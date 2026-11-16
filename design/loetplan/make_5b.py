# Lochraster-Bestückungsplan FET-Platine (H1 + H2) für 3x7-cm-Platine, 10 Spalten (01-10) x 24 Reihen (A-X)
from PIL import Image, ImageDraw, ImageFont
import math, os
OUT = os.environ.get("LOETEN_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "projektdokumentation", "fotos", "loeten"))
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def F(s, b=True): return ImageFont.truetype(FB if b else FR, s)
ROWS = "ABCDEFGHIJKLMNOPQRSTUVWX"
P = 92                    # px pro 2,54 mm
MM = P/2.54
W, H = 2010, 1580
BX, BY = 90, 175          # Platinen-Ecke
MX, MY = 62, 40           # Rand bis erstes Loch
NR = 11                   # gezeigte Reihen A..K
NAVY = (25,60,110)
NET = dict(v5=(215,30,30), gnd=(25,25,25), g1=(30,90,220), b=(140,60,190), io18=(20,150,60),
           led=(210,0,150), bat=(150,85,30), g2=(0,155,160), vin=(240,130,0))
def rc(s):  # "F04" -> (col,row)
    return int(s[1:]), ROWS.index(s[0])+1

# ---- Verbindungen (Unterseite) ----
BRIDGES = [  # (net, [holes in chain])
    ('v5',  ["E04","F04","G04","H04"]),
    ('g1',  ["E02","F02","F03","G03"]),
    ('b',   ["G02","H02","H03"]),
    ('io18',["G01","H01"]),
    ('gnd', ["I01","I02","I03","J03","J04"]),
    ('gnd', ["J01","J02","J03"]),
    ('g2',  ["E07","F07","F06"]),
    ('bat', ["E09","F09","F08"]),
    ('bat', ["F09","F10"]),
]
JUMPERS = [('led', "B03", "F01"), ('vin', "B08", "F05")]
PADS = [  # nr, hole, net, kurz, lang
    (1, "G04", 'v5',  "5 V",          "5 V  ← Pololu VOUT"),
    (2, "J02", 'gnd', "GND",          "GND  ← Pololu GND (= TC4056 OUT−)"),
    (3, "F01", 'led', "LED +",        "LED +  → Streifen 5 V / +"),
    (4, "J01", 'gnd', "LED GND",      "LED GND  → Streifen GND"),
    (5, "H01", 'io18',"GPIO18",       "GPIO18  ← SD-Slot Kontakt 5"),
    (6, "F09", 'bat', "TC4056 OUT+",  "TC4056 OUT+  (Akku +)"),
    (7, "F06", 'g2',  "Schalter Mitte","Schalter Mitte"),
    (8, "F10", 'bat', "Schalter AUS", "Schalter AUS (Außenpin unten)"),
    (9, "I01", 'gnd', "Schalter AN",  "Schalter AN (Außenpin oben) = GND"),
    (10,"F05", 'vin', "Pololu VIN",   "Pololu VIN  (+ Akku-Teiler oben)"),
]
ADAPT = [("Q1", 1, {"E02":"G","E04":"S","B03":"D"}), ("Q2", 6, {"E07":"G","E09":"S","B08":"D"})]
RES = [("R1","10 kΩ","F03","F04"), ("R2","4,7 kΩ","G01","G02"), ("R3","47 kΩ","H02","I02"), ("R4","47 kΩ","F07","F08")]
T1 = {"G03":"C","H03":"B","I03":"E"}
ELKO = {"H04":"+","J04":"−"}

def pinno(h, c0):
    """Adapter-Stiftnummer (1-10) fuer Loch h; Stift 1 = Reihe E, erste Spalte des Adapters; 10..6 laufen in Reihe B zurueck"""
    r, c = h[0], int(h[1:])
    return c - c0 + 1 if r == "E" else 10 - (c - c0)

class Board:
    def __init__(s, title, mirror=False):
        s.mirror = mirror
        s.im = Image.new("RGBA", (W, H), "white"); s.d = ImageDraw.Draw(s.im)
        s.d.rectangle([0,0,W,86], fill=NAVY)
        s.d.text((30,18), title, font=F(40), fill="white")
    def xy(s, c, r):
        if s.mirror: c = 11 - c
        return BX + MX + (c-1)*P, BY + MY + (r-1)*P
    def hxy(s, h): return s.xy(*rc(h))
    def t(s, xy, txt, size=22, fill=(20,20,20), anchor="la", b=True, bg=None, d=None):
        d = d or s.d; f = F(size, b)
        if bg is not None:
            bb = d.multiline_textbbox(xy, txt, font=f, anchor=anchor, spacing=5)
            d.rounded_rectangle([bb[0]-6,bb[1]-4,bb[2]+6,bb[3]+4], 6, fill=bg)
        d.multiline_text(xy, txt, font=f, fill=fill, anchor=anchor, spacing=5)
    def overlay(s):
        ov = Image.new("RGBA", s.im.size, (0,0,0,0)); return ov, ImageDraw.Draw(ov)
    def comp(s, ov): s.im.alpha_composite(ov); s.d = ImageDraw.Draw(s.im)
    def board(s):
        bw, bh = 2*MX + 9*P, 2*MY + (NR-1)*P
        # Platine läuft nach unten weiter (Reihe L..X), hier abgeschnitten gezeichnet
        s.d.rectangle([BX,BY,BX+bw,BY+bh+40], fill=(28,110,64), outline=(15,70,40), width=3)
        ov, od = s.overlay()
        yA = s.xy(1,1)[1]; yK = s.xy(1,11)[1]
        od.rectangle([BX,BY,BX+bw,yA], fill=(255,255,255,150))
        od.rectangle([BX,yK,BX+bw,BY+bh+40], fill=(255,255,255,150))
        s.comp(ov)
        # Abrisskante unten (Platine geht weiter bis X)
        pts = [(BX-4, BY+bh+40)] + [(BX + i*bw/12, BY+bh+40 + (10 if i%2 else -6)) for i in range(13)] + [(BX+bw+4, BY+bh+40)]
        s.d.polygon(pts + [(BX+bw+4, BY+bh+70), (BX-4, BY+bh+70)], fill="white")
        for r in range(1,NR+1):
            for c in range(1,11):
                x,y = s.xy(c,r)
                s.d.ellipse([x-19,y-19,x+19,y+19], fill=(200,200,205), outline=(140,140,150), width=2)
                s.d.ellipse([x-7,y-7,x+7,y+7], fill=(60,60,60))
        for c in range(1,11):
            x,_ = s.xy(c,1)
            s.t((x, BY-14), "%02d" % c, 28, anchor="md")
        for r in range(1,NR+1):
            _,y = s.xy(1,r)
            col = (20,20,20) if 2 <= r <= 10 else (160,160,160)
            s.t((BX-18, y), ROWS[r-1], 30, fill=col, anchor="rm")
            s.t((BX+bw+18, y), ROWS[r-1], 30, fill=col, anchor="lm")
        for r in (1, 11):
            _,y = s.xy(1,r)
            x = BX-10
            while x < BX+bw+10:
                s.d.line([x,y,min(x+22,BX+bw+10),y], fill=(220,20,20), width=5); x += 36
        _,yA = s.xy(1,1); _,yK = s.xy(1,11)
        s.t((BX+bw/2, yA-0), "✂  durch Lochreihe A schneiden", 22, fill=(200,20,20), anchor="mm", bg=(255,255,255))
        s.t((BX+bw/2, BY+bh+100), "✂  rote Linie unten: durch Lochreihe K schneiden (Reihe L – X nicht gebraucht)", 22, fill=(200,20,20), anchor="mm", bg=(255,255,255))
        s.bw, s.bh = bw, bh
    def overview(s, x0, y0, p=19):
        # ganze Platine 10 x 24, benutzter Teil markiert
        w, h = 9*p + 30, 23*p + 30
        s.d.rounded_rectangle([x0,y0,x0+w,y0+h], 6, fill=(28,110,64))
        for r in range(1,25):
            for c in range(1,11):
                cc = 11-c if s.mirror else c
                x = x0+15+(cc-1)*p; y = y0+15+(r-1)*p
                s.d.ellipse([x-4,y-4,x+4,y+4], fill=(200,200,205) if 2<=r<=10 else (120,150,130))
        ya = y0+15 + 0.5*p - p; yb = y0+15 + 9.5*p
        s.d.rectangle([x0-4, y0+15+0.5*p, x0+w+4, yb], outline=(255,200,0), width=4)
        for r, yy in ((1, y0+15), (11, y0+15+10*p)):
            s.d.line([x0-10, yy, x0+w+10, yy], fill=(220,20,20), width=3)
            s.t((x0+w+16, yy), "✂ " + ROWS[r-1], 18, fill=(200,20,20), anchor="lm")
        s.t((x0+w+16, y0+15+5*p), "B – J\nbenutzt\n= 30 × 24,5 mm", 18, fill=NAVY, anchor="lm")
        s.t((x0+w+16, y0+15+17*p), "L – X\nRest", 18, fill=(120,120,120), anchor="lm")
        s.t((x0, y0-8), "Ganze Platine 3 × 7 cm", 18, fill=NAVY, anchor="ld")
    def chain(s, pts, col, w=7, dash=False):
        for a,b in zip(pts, pts[1:]):
            if not dash:
                s.d.line([a,b], fill=col, width=w)
            else:
                L = math.dist(a,b); n = max(1,int(L//16))
                for i in range(n):
                    if i % 2: continue
                    t0, t1 = i/n, min(1,(i+1)/n)
                    s.d.line([(a[0]+(b[0]-a[0])*t0, a[1]+(b[1]-a[1])*t0),(a[0]+(b[0]-a[0])*t1, a[1]+(b[1]-a[1])*t1)], fill=col, width=w)
    def jumper_pts(s, h1, h2, bend):
        (x1,y1),(x2,y2) = s.hxy(h1), s.hxy(h2)
        mx, my = (x1+x2)/2 + bend[0], (y1+y2)/2 + bend[1]
        pts = []
        for i in range(21):
            t = i/20
            pts.append(((1-t)**2*x1 + 2*(1-t)*t*mx + t*t*x2, (1-t)**2*y1 + 2*(1-t)*t*my + t*t*y2))
        return pts
    def badge(s, h, nr, net):
        x,y = s.hxy(h)
        s.d.ellipse([x-24,y-24,x+24,y+24], fill=NET[net], outline="white", width=4)
        s.t((x,y), str(nr), 26, fill="white", anchor="mm")
    def rot_text(s, center, txt, size, fill, angle=90):
        f = F(size); bb = s.d.textbbox((0,0), txt, font=f)
        tw, th = bb[2]-bb[0]+8, bb[3]-bb[1]+8
        im = Image.new("RGBA", (tw,th), (0,0,0,0)); ImageDraw.Draw(im).text((4-bb[0],4-bb[1]), txt, font=f, fill=fill)
        im = im.rotate(angle, expand=True)
        s.im.alpha_composite(im, (int(center[0]-im.width/2), int(center[1]-im.height/2))); s.d = ImageDraw.Draw(s.im)

def legend_box(b, x0, y0, x1, y1, title):
    b.d.rounded_rectangle([x0,y0,x1,y1], 12, fill=(247,249,252), outline=NAVY, width=3)
    b.t((x0+16,y0+12), title, 24, fill=NAVY)


LX = 1125; RX = W - 25
def footer(b, txt):
    b.d.rectangle([0, H-70, W, H], fill=(200,20,20))
    b.t((40, H-35), "⚠  " + txt, 30, fill="white", anchor="lm")

# ================== OBERSEITE ==================
b = Board("Lötschritt 5b: FET-Platine auf dem 3×7-Lochraster – Bauteilseite (oben)")
b.board()
for net, ch in BRIDGES: b.chain([b.hxy(h) for h in ch], NET[net], 7, dash=True)
b.chain(b.jumper_pts("B03","F01",(-70,0)), NET['led'], 7, dash=True)
b.chain(b.jumper_pts("B08","F05",(-50,20)), NET['vin'], 7, dash=True)
ov, od = b.overlay()
for name, c0, pins in ADAPT:
    x0,y0 = b.xy(c0,2); x1,y1 = b.xy(c0+4,5)
    od.rounded_rectangle([x0-P*0.5+3, y0-0.51*P, x1+P*0.5-3, y1+0.51*P], 10, fill=(150,60,170,90), outline=(110,30,130,255), width=5)
b.comp(ov)
for name, c0, pins in ADAPT:
    for c in range(c0, c0+5):
        for r in (2,5):
            h = "%s%02d" % (ROWS[r-1], c); x,y = b.xy(c,r)
            if h in pins: b.d.rectangle([x-15,y-15,x+15,y+15], fill=(20,20,20))
            else: b.d.rectangle([x-10,y-10,x+10,y+10], fill=(125,125,125))
    cx = b.xy(c0+2,2)[0]; cy = (b.xy(c0,3)[1]+b.xy(c0,4)[1])/2
    b.d.rectangle([cx-62,cy-34,cx+62,cy+34], fill=(30,30,30))
    for dx in (-38, 38): b.d.rectangle([cx+dx-9, cy+34, cx+dx+9, cy+52], fill=(190,190,190))
    b.d.rectangle([cx-9, cy-52, cx+9, cy-34], fill=(190,190,190))
    b.t((cx,cy), "AO3401A", 20, fill="white", anchor="mm")
    b.t((cx-38, cy+66), "G", 16, fill="white", anchor="mm"); b.t((cx+38, cy+66), "S", 16, fill="white", anchor="mm")
    b.t((cx+26, cy-46), "D", 16, fill="white", anchor="mm")
    b.t((b.xy(c0,3)[0]-8, (b.xy(c0,3)[1]+b.xy(c0,4)[1])/2), name, 34, fill="white", anchor="lm")
    for c in range(c0, c0+5):
        for r in (2,5):
            h = "%s%02d" % (ROWS[r-1], c); x,y = b.xy(c,r); n = pinno(h, c0)
            b.t((x, y+(30 if r == 5 else -30)), str(n), 18, fill=(255,255,255), anchor="mm", bg=(70,30,90) if n != 1 else (200,20,20))
    for h, lab in pins.items():
        x,y = b.hxy(h)
        b.t((x+30, y+2), lab, 26, fill="white", anchor="lm", bg=(110,30,130))
b.t((b.xy(3,1)[0], BY-50), "H1 · LED-Strom", 22, fill=NAVY, anchor="mm")
b.t((b.xy(8,1)[0], BY-50), "H2 · Ein/Aus", 22, fill=NAVY, anchor="mm")
# Elko
ov, od = b.overlay()
xa = b.xy(4,9)[0] + 0.6*P; xb = b.xy(10,9)[0] + 0.9*P; yc = b.xy(4,9)[1]; rr = 5*MM
od.rounded_rectangle([xa, yc-rr, xb, yc+rr], 22, fill=(40,90,200,175), outline=(20,40,120,255), width=5)
od.rectangle([xa+16, yc+rr-34, xb-8, yc+rr-8], fill=(225,225,235,235))
b.comp(ov)
for i in range(6): b.t((xa+70+i*85, yc+rr-21), "−", 24, fill=(20,40,120), anchor="mm")
b.t(((xa+xb)/2, yc-22), "C1  Elko 470 µF / 25 V", 26, fill="white", anchor="mm")
b.t(((xa+xb)/2, yc+16), "liegt flach · Streifen = −", 20, fill="white", anchor="mm", b=False)
for h, sgn in ELKO.items():
    x,y = b.hxy(h)
    b.d.line([xa, y, x, y], fill=(175,175,175), width=7)
    b.d.ellipse([x-11,y-11,x+11,y+11], fill=(175,175,175))
    b.t((xa+26, y), sgn, 30, fill="white", anchor="mm", bg=(20,40,120))
# Widerstände stehend
for ref, val, h1, h2 in RES:
    (x1,y1),(x2,y2) = b.hxy(h1), b.hxy(h2)
    vert = abs(x1-x2) < 2
    box = [x1-24, y1-18, x1+24, y2+18] if vert else [min(x1,x2)-18, y1-24, max(x1,x2)+18, y1+24]
    b.d.rounded_rectangle(box, 22, fill=(245,225,180), outline=(90,70,40), width=3)
    if vert: b.rot_text(((x1+x2)/2, (y1+y2)/2), ref + "  " + val, 19, (40,30,10))
    else: b.t(((x1+x2)/2, y1), ref + "  " + val, 19, fill=(40,30,10), anchor="mm")
# BC547B
xs, ys = b.hxy("G03"); _, ye = b.hxy("I03")
xf = xs - 1.6*MM; xr = xs + 2.1*MM; ym = (ys+ye)/2; hh = (ye-ys)/2 + 0.42*P
b.d.chord([xf-(xr-xf), ym-hh, xr, ym+hh], -90, 90, fill=(35,35,35))
b.d.line([xf, ym-hh+6, xf, ym+hh-6], fill=(210,210,210), width=4)
for h, lab in T1.items():
    x,y = b.hxy(h); b.d.ellipse([x-9,y-9,x+9,y+9], fill=(190,190,190))
    b.t((x+26, y), lab, 22, fill="white", anchor="mm")
b.t((xs+14, ym-hh-2), "T1 BC547B", 18, fill="white", anchor="md", bg=(35,35,35))
b.rot_text((xf+11, ym), "flach", 15, (255,255,255,255))
for nr, h, net, kurz, lang in PADS: b.badge(h, nr, net)

# Legende
legend_box(b, LX, 105, RX, 500, "Bauteile")
items = [("Q1", "AO3401A auf SOT-23-Adapter · LED-Strom (H1)"),
         ("Q2", "AO3401A auf SOT-23-Adapter · Ein/Aus (H2)"),
         ("T1", "BC547B · flache Seite nach links (zu Spalte 02)"),
         ("R1", "10 kΩ · F03–F04 · Gate–Source Q1"),
         ("R2", "4,7 kΩ · G01–G02 · Basis → GPIO18"),
         ("R3", "47 kΩ · H02–I02 · Basis → GND"),
         ("R4", "47 kΩ · F07–F08 · Gate–Source Q2"),
         ("C1", "Elko 470 µF / 25 V · + in H04, − in J04")]
y = 154
for ref, txt in items:
    b.t((LX+20, y), ref, 22, fill=NAVY); b.t((LX+80, y), txt, 22, b=False); y += 36
b.t((LX+20, y+4), "Widerstände stehend (ein Bein umgebogen). Graue Stifte\n= Adapter-Stifte ohne Funktion: nur festlöten.", 18, fill=(90,90,90), b=False)

legend_box(b, LX, 515, RX, 1015, "Anschlüsse (Litze von oben einstecken)")
y = 558
for nr, h, net, kurz, lang in PADS:
    b.d.ellipse([LX+20, y-2, LX+54, y+32], fill=NET[net], outline="white", width=2)
    b.t((LX+37, y+15), str(nr), 18, fill="white", anchor="mm")
    b.t((LX+68, y+3), h, 22)
    b.t((LX+130, y+3), lang, 22, b=False)
    y += 40
b.t((LX+20, y+6), "Akku-Teiler 2 × 10 kΩ → GPIO35 passt nicht mehr drauf:\nfrei verdrahten wie Schritt 4 (Mitte direkt an GPIO35).", 18, fill=(170,30,30))

legend_box(b, LX, 1030, RX, 1240, "Gestrichelt = Verbindung UNTEN (siehe Bild Unterseite)")
nets = [('v5',"5 V"),('gnd',"GND"),('g1',"Gate Q1"),('b',"Basis T1"),('io18',"GPIO18"),
        ('led',"LED + (Draht)"),('bat',"Akku + (OUT+)"),('g2',"Gate Q2"),('vin',"VIN (Draht)")]
for i,(net,name) in enumerate(nets):
    cx = LX + 20 + (i % 3) * 290; cy = 1078 + (i // 3) * 46
    b.chain([(cx, cy+12), (cx+56, cy+12)], NET[net], 7, dash=True)
    b.t((cx+68, cy), name, 20, b=False)
b.overview(LX+30, 1280, p=0)  if False else None
legend_box(b, LX, 1255, RX, 1495, "Einbau")
notes = ["Fertig 30 × 24,5 mm: Spalte 01–10, Reihe B–J.",
         "Im Gehäuse: Reihe B zum Display (links), Elko rechts.",
         "AO3401A mittig auf den Adapter löten: 2 Beinchen (G, S)",
         "zu Reihe E, das einzelne Bein (D) zu Reihe B. Danach messen!"]
y = 1300
for n in notes: b.t((LX+20, y), n, 21, b=False); y += 44
b.d.rounded_rectangle([BX, 1330, LX-40, 1495], 12, fill=(247,249,252), outline=NAVY, width=3)
b.t((BX+16, 1342), "SOT-23-Adapter einsetzen (Bauteilseite oben)", 22, fill=NAVY)
for i, ln in enumerate(["Stift 1 (rote Zahl „1“, Quadrat-Pad) unten links: Reihe E, Spalte 01 bzw. 06.",
                        "Stifte 1–5 stecken in Reihe E, Stifte 10→6 in Reihe B (Stift 10 über Stift 1).",
                        "Chip: Gate = Stift 2, Source = Stift 4, Drain = Stift 8. Stift 4 muss bestückt sein!",
                        "Stifte 1, 3, 5, 6, 7, 9, 10 halten nur fest – nichts anschließen."]):
    b.t((BX+16, 1382+i*27), ln, 19, b=False)
footer(b, "Beim Löten kein Strom drauf – Akku ab, USB ab, Schalter auf AUS")
b.im.convert("RGB").save(os.path.join(OUT, "loeten_5b_lochraster_layout.png")); print("ok top")

# ================== UNTERSEITE ==================
u = Board("Lötschritt 5b: Unterseite (Lötseite) – Platine umgedreht, Spalten gespiegelt", mirror=True)
u.board()
ov, od = u.overlay()
for name, c0, pins in ADAPT:
    xa_, ya_ = u.xy(c0,2); xb_, yb_ = u.xy(c0+4,5)
    od.rounded_rectangle([min(xa_,xb_)-P*0.5+3, ya_-0.51*P, max(xa_,xb_)+P*0.5-3, yb_+0.51*P], 10, outline=(255,255,255,150), width=3)
    od.text(((xa_+xb_)/2, (ya_+yb_)/2), name + " (oben)", font=F(26), fill=(255,255,255,170), anchor="mm")
xa2 = u.xy(4,9)[0] - 0.6*P; xb2 = u.xy(10,9)[0] - 0.9*P
od.rounded_rectangle([xb2, yc-rr, xa2, yc+rr], 22, outline=(255,255,255,150), width=3)
od.text(((xa2+xb2)/2, yc), "Elko liegt oben", font=F(26), fill=(255,255,255,170), anchor="mm")
u.comp(ov)
for net, ch in BRIDGES:
    pts = [u.hxy(h) for h in ch]
    u.chain(pts, (235,235,240), 30); u.chain(pts, NET[net], 14)
for net, h1, h2 in JUMPERS:
    bend = (70,0) if h1 == "B03" else (50,20)
    pts = u.jumper_pts(h1, h2, bend)
    u.chain(pts, (255,255,255), 22); u.chain(pts, NET[net], 14)
labels = {}
for name, c0, pins in ADAPT:
    for c in range(c0, c0+5):
        for r in (2,5):
            h = "%s%02d" % (ROWS[r-1], c)
            labels[h] = (name+" "+pins[h]+" · Stift %d" % pinno(h, c0)) if h in pins else "·%d" % pinno(h, c0)
for h, l in T1.items(): labels[h] = "T1 " + l
for ref, val, h1, h2 in RES: labels[h1] = ref; labels[h2] = ref
for h, sgn in ELKO.items(): labels[h] = "C1 " + sgn
for h, l in labels.items():
    x,y = u.hxy(h)
    if l.startswith("·"):
        u.d.ellipse([x-15,y-15,x+15,y+15], fill=(120,120,120)); u.t((x,y), l[1:], 15, fill="white", anchor="mm"); continue
    u.d.ellipse([x-19,y-19,x+19,y+19], fill=(225,225,232), outline=(60,60,60), width=2)
    dy = -34 if h[0] in "BG" else 34
    if h in ("H02","H03","I02","I03"): dy = 0
    if dy == 0:
        u.d.ellipse([x-26,y-26,x+26,y+26], fill=(225,225,232), outline=(60,60,60), width=2)
        u.t((x, y), l, 15, fill=(20,20,20), anchor="mm")
    else: u.t((x, y+dy), l, 16, fill="white", anchor="mm", bg=(30,30,30))
for nr, h, net, kurz, lang in PADS: u.badge(h, nr, net)
u.t((BX + u.bw/2, BY-50), "← Spalte 10 … Spalte 01 →   (gespiegelt, weil umgedreht)", 22, fill=NAVY, anchor="mm")

legend_box(u, LX, 110, RX, 700, "So verbinden (von unten)")
rows_ = [('v5', "5 V", "E04 – F04 – G04 – H04"),
         ('g1', "Gate Q1", "E02 – F02 – F03 – G03"),
         ('b', "Basis T1", "G02 – H02 – H03"),
         ('io18', "GPIO18", "G01 – H01"),
         ('gnd', "GND", "I01 – I02 – I03 – J03 – J04\nJ01 – J02 – J03"),
         ('g2', "Gate Q2", "E07 – F07 – F06"),
         ('bat', "Akku +", "E09 – F09 – F08  und  F09 – F10"),
         ('led', "LED +", "isolierter Draht B03 → F01"),
         ('vin', "VIN", "isolierter Draht B08 → F05")]
y = 156
for net, name, txt in rows_:
    u.chain([(LX+20, y+13), (LX+74, y+13)], NET[net], 14)
    u.t((LX+88, y), name, 22)
    u.t((LX+220, y), txt, 22, b=False)
    y += 76 if "\n" in txt else 46
u.t((LX+20, y+6), "Dicke Linie = Lötbrücke (Zinn zwischen Nachbar-Pads)\noder Stück blanker Draht. Graue Punkte = Adapter-\nStifte ohne Funktion: festlöten, nichts anschließen.", 19, fill=(70,70,70), b=False)

legend_box(u, LX, 720, RX, 1080, "NICHT verbinden (Kurzschluss!)")
nots = ["F03 – F04,  G01 – G02,  H02 – I02,  F07 – F08", "   (das sind die 2 Beine eines Widerstands)",
        "F04 – F05,  F05 – F06  (VIN neben 5 V und Gate Q2)", "G03 – G04,  H03 – H04  (T1 neben 5 V)",
        "G02 – G03,  F02 – G02  (Basis neben Kollektor / Gate Q1)",
        "F01 – F02  (LED + neben Gate Q1)",
        "H01 – H02,  H01 – I01  (GPIO18 neben Basis / GND)",
        "E02 – E03 – E04  (Stift 3 des Adapters liegt zwischen G und S)",
        "J03 – I04 – H04  (C1 − und + nicht verbinden)"]
y = 760
for n in nots: u.t((LX+20, y), ("" if n.startswith("   ") else "✗  ") + n, 20, fill=(170,20,20), b=False); y += 34

legend_box(u, LX, 1100, RX, 1480, "Prüfen mit Multimeter (Durchgang)")
checks = ["Darf NICHT piepen: 1 ↔ 2,  6 ↔ 2,  10 ↔ 1,  5 ↔ 2",
          "Muss piepen: 2 ↔ 4 ↔ 9 (alles GND)",
          "Muss piepen: 6 ↔ 8 (Akku +),  C1 − ↔ 2",
          "Muss piepen: Q1 G ↔ T1 C,  Q2 G ↔ 7",
          "Erst dann die Litzen anlöten."]
y = 1146
for n in checks: u.t((LX+20, y), n, 22, b=False); y += 60
u.d.rounded_rectangle([BX, 1330, LX-40, 1495], 12, fill=(247,249,252), outline=NAVY, width=3)
u.t((BX+16, 1342), "Adapter-Chip vorher / nachher prüfen (Multimeter)", 22, fill=NAVY)
for i, ln in enumerate(["Vor dem Einlöten in die Platine, am einzelnen Adapter: Diodentest, rot an Stift 8,",
                        "schwarz an Stift 4 → ca. 0,5–0,7 V; vertauscht → nichts. Gate (Stift 2) ↔ andere: nichts.",
                        "Nach dem Einlöten: Gate ↔ Source zeigt ca. 10 kΩ (Q1) bzw. 47 kΩ (Q2) – das ist normal.",
                        "Der Durchgangsprüfer piepst dabei nicht (Widerstand), das ist kein Fehler."]):
    u.t((BX+16, 1382+i*27), ln, 19, b=False)
footer(u, "Kurz löten (2–3 s) · Lötbrücken nur da, wo eingezeichnet")
u.im.convert("RGB").save(os.path.join(OUT, "loeten_5b_lochraster_unterseite.png")); print("ok bottom")
