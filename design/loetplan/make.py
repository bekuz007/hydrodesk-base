from PIL import Image, ImageDraw, ImageFont
import os
OUT = os.environ.get("LOETEN_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "projektdokumentation", "fotos", "loeten"))
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def F(s, bold=True): return ImageFont.truetype(FB if bold else FR, s)
W, H = 1600, 1200
C = dict(red=(215,30,30), black=(20,20,20), white=(250,250,250), green=(20,150,60), yellow=(235,190,0),
         blue=(30,90,220), grey=(150,150,150), pcb=(30,120,70), orange=(240,130,0), purple=(140,60,190),
         teal=(0,150,150), solder=(185,185,195), dark=(40,40,40), lightgrey=(235,235,235), brown=(150,90,40))

class Img:
    def __init__(s, title):
        s.im = Image.new("RGB", (W, H), "white"); s.d = ImageDraw.Draw(s.im)
        s.d.rectangle([0,0,W,84], fill=(25,60,110))
        s.d.text((30,16), title, font=F(44), fill="white")
    def text(s, xy, t, size=26, fill=C['black'], anchor="la", bold=True, bg=None):
        f = F(size, bold)
        if bg is not None:
            bb = s.d.multiline_textbbox(xy, t, font=f, anchor=anchor, spacing=6, align="center" if anchor[0]=="m" else "left")
            s.d.rectangle([bb[0]-6,bb[1]-4,bb[2]+6,bb[3]+4], fill=bg)
        s.d.multiline_text(xy, t, font=f, fill=fill, anchor=anchor, spacing=6, align="center" if anchor[0]=="m" else "left")
    def wire(s, pts, col, w=7):
        if col == C['white']:
            s.d.line(pts, fill=C['grey'], width=w+4, joint="curve")
        s.d.line(pts, fill=col, width=w, joint="curve")
        for p in pts: s.d.ellipse([p[0]-w//2,p[1]-w//2,p[0]+w//2,p[1]+w//2], fill=col)
    def dot(s, p, r=9, col=C['black']): s.d.ellipse([p[0]-r,p[1]-r,p[0]+r,p[1]+r], fill=col)
    def box(s, xy, fill, outline=C['dark'], w=3, r=14): s.d.rounded_rectangle(xy, r, fill=fill, outline=outline, width=w)
    def res(s, c, label, vertical=False, size=24, lpos="r"):
        x,y=c
        if vertical: s.d.rectangle([x-14,y-40,x+14,y+40], fill=(245,225,180), outline=C['dark'], width=3)
        else: s.d.rectangle([x-40,y-14,x+40,y+14], fill=(245,225,180), outline=C['dark'], width=3)
        if label:
            if vertical: s.text((x+24,y) if lpos=="r" else (x-24,y), label, size, anchor="lm" if lpos=="r" else "rm")
            else: s.text((x,y-22), label, size, anchor="md")
    def steps(s, lines, top=800):
        s.box([30,top,W-30,1100], (245,248,252), outline=(25,60,110))
        y = top+18
        for i,l in enumerate(lines,1):
            s.d.ellipse([50,y,92,y+42], fill=(25,60,110)); s.text((71,y+21), str(i), 26, fill="white", anchor="mm")
            s.text((108,y+4), l, 28)
            y += (1100-top-30)//len(lines)
    def warn(s, t="Beim Löten kein Strom drauf"):
        s.d.rectangle([0,1115,W,1200], fill=(200,20,20))
        x=40; s.d.polygon([(x,1180),(x+30,1128),(x+60,1180)], fill=(255,210,0)); s.text((x+30,1165),"!",30,anchor="mm")
        s.text((120,1157), t, 34, fill="white", anchor="lm")
    def save(s, n): s.im.save(os.path.join(OUT,n)); print("ok", n)

# ---------- 1 HX711 ----------
m = Img("Lötschritt 1: HX711 (Waage) anlöten")
bx0,by0,bx1,by1 = 130,300,1080,580
m.box([bx0,by0,bx1,by1], C['pcb'])
m.text(((bx0+bx1)//2,(by0+by1)//2), "HX711\n(Bauteil-Seite oben = hier löten)", 28, fill="white", anchor="mm")
top = ["E+","E−","A−","A+","B−","B+"]
tcol = [("Rot",C['red']),("Schwarz",C['black']),("Weiß",C['white']),("Grün",C['green']),("frei",None),("frei",None)]
xs = [bx0+90+i*154 for i in range(6)]
for x,p,(cn,cc) in zip(xs,top,tcol):
    m.dot((x,by0+40),16,C['solder']); m.dot((x,by0+40),7,C['dark'])
    m.text((x,by0+66),p,26,fill="white",anchor="mt")
    if cc: m.wire([(x,by0+24),(x,175)],cc)
    m.text((x,165), cn, 26, fill=C['grey'] if not cc else C['black'], anchor="md")
m.text((xs[0]-40,100), "Wägezelle-Kabel:", 26, anchor="la")
m.text((xs[4]-40,100), "B− / B+: nichts dran", 24, fill=C['grey'], anchor="la")
bot = ["VCC","SCK","DT","GND"]
bcol = [("Rot\n3V3",C['red']),("Blau\nIO22",C['blue']),("Gelb\nIO27",C['yellow']),("Schwarz\nGND",C['black'])]
xs2 = [bx0+180+i*200 for i in range(4)]
for x,p,(cn,cc) in zip(xs2,bot,bcol):
    m.dot((x,by1-40),16,C['solder']); m.dot((x,by1-40),7,C['dark'])
    m.text((x,by1-66),p,26,fill="white",anchor="md")
    m.wire([(x,by1-24),(x,650)],cc)
    m.text((x,660), cn, 24, anchor="ma")
m.text(((xs2[0]+xs2[-1])//2,745), "↑ Kabel vom CYD-Stecker CN1", 24, anchor="ma")
# inset side view
ix=1120; m.box([ix,150,1575,690],(250,250,250),outline=C['grey'])
m.text((1360,165),"Von der Seite:",26,anchor="ma")
m.d.rectangle([ix+60,380,ix+310,400], fill=C['pcb'])
m.text((ix+335,390),"Platine",22,anchor="lm",fill=C['pcb'])
for k in range(3):
    px=ix+120+k*90
    m.d.rectangle([px-5,340,px+5,580], fill=(200,170,40))
    m.d.polygon([(px-24,380),(px+24,380),(px+6,345),(px-6,345)], fill=C['solder'])
m.d.rectangle([ix+80,410,ix+290,440], fill=C['black'])
m.text((ix+185,300),"Lötzinn-Kegel oben",22,anchor="mm")
m.text((ix+335,428),"Plastik",22,anchor="lm")
m.text((ix+185,610),"kurze Seite oben\nlange Seite unten",22,anchor="mm")
m.steps(["Stiftleisten: kurze Seite von unten durch, OBEN anlöten (Plastik bleibt unten).",
         "Wägezelle oben: Rot → E+, Schwarz → E−, Weiß → A−, Grün → A+.",
         "B− und B+ bleiben frei (kein Kabel dran).",
         "Unten: VCC Rot (3V3), SCK Blau (IO22), DT Gelb (IO27), GND Schwarz.",
         "Zum Schluss prüfen: kein Zinn zwischen zwei Pins (keine Brücke)!"])
m.warn("Beim Löten kein Strom drauf (CN1-Kabel und USB ab)")
m.save("loeten_1_hx711.png")

# ---------- 2 SD slot ----------
m = Img("Lötschritt 2: Drähte am microSD-Slot (GPIO18/19/23)")
m.text((800,112),"microSD-Slot am CYD – Lötfahnen 1 bis 8 (Schema, keine echte Lage)",26,anchor="mm")
pins = [("1","DAT2",None,None),("2","CS","GPIO5",None),("3","CMD/MOSI","GPIO23",C['orange']),("4","VDD","3,3 V",None),
        ("5","CLK/SCK","GPIO18",C['purple']),("6","VSS","GND",None),("7","DAT0/MISO","GPIO19",C['teal']),("8","DAT1",None,None)]
m.box([90,230,1510,400],(205,205,210))
for i,(n,nm,g,col) in enumerate(pins):
    x = 175+i*178
    m.text((x,150),nm,22,anchor="ma",fill=C['black'] if col else C['grey'])
    m.text((x,182),(g or "–"),24,anchor="ma",fill=col if col else C['grey'])
    m.d.rectangle([x-26,250,x+26,400], fill=(220,190,60) if col else (190,190,190), outline=C['dark'], width=2)
    if col: m.d.ellipse([x-30,270,x+30,330], fill="white", outline=col, width=8)
    m.text((x,300),n,30,anchor="mm")
    if not col: m.text((x,415),"nicht\nlöten",20,anchor="ma",fill=C['grey'])
dest = {2:"470 Ω → LED-Streifen\nDIN (Schritt 6)",4:"FET-Platine: 4,7 kΩ\n→ Basis BC547B\n(Schritt 5)",6:"Regensensor DO\n(Schritt 6)"}
for i,t in dest.items():
    x=175+i*178; col=pins[i][3]; b=(x-168,560,x+168,720)
    m.wire([(x,400),(x,560)],col,7)
    m.box(b,(250,250,250),outline=col,w=5)
    m.text((x,640),pins[i][2]+" →\n"+t,23,anchor="mm")
m.text((800,755),"Lage unsicher? Multimeter auf Durchgang: Pin 6 piept mit GND (CN1 Schwarz), Pin 4 mit 3V3 (CN1 Rot).",22,anchor="mm",fill=C['red'])
m.steps(["Keine SD-Karte einstecken – der Slot bleibt leer.",
         "Mit dem Durchgangsprüfer Pin 6 (GND) finden → so weißt du, wo Pin 1 ist.",
         "Je einen dünnen Draht an Pin 3, 5 und 7 löten – kurz, wenig Zinn.",
         "Pin 1, 2, 4, 6 und 8 NICHT anlöten. Drahtfarben aufschreiben.",
         "Danach prüfen: kein Durchgang zum Nachbar-Pin (keine Brücke)."], top=790)
m.warn("Beim Löten kein Strom drauf (USB ab, Akku ab, CN1 ab)")
m.save("loeten_2_sd_slot.png")

# ---------- 3 Akku -> TC4056 ----------
m = Img("Lötschritt 3: Akku an den Lader TC4056")
m.box([50,240,390,560],(70,70,80)); m.text((220,360),"LiPo-Akku\nEEMB 2000 mAh",28,fill="white",anchor="mm")
m.text((220,480),"3,7 V",28,fill="white",anchor="mm")
m.box([620,220,1040,600],(30,80,170)); m.text((830,410),"TC4056",34,fill="white",anchor="mm")
m.d.rounded_rectangle([780,170,880,240],10,fill=(180,180,180),outline=C['dark'],width=3)
m.text((900,175),"USB-C (Laden)",24,anchor="la")
m.text((830,560),"Beschriftung auf der Platine lesen",20,anchor="mm",fill="white")
for n,y,col,cn in [("B+",320,C['red'],"Rot"),("B−",480,C['black'],"Schwarz")]:
    m.wire([(390,y),(640,y)],col,9)
    m.d.rectangle([640,y-32,730,y+32],fill=C['solder'],outline=C['dark'],width=2); m.text((685,y),n,28,anchor="mm")
    m.text((515,y-16),cn,26,anchor="md",fill=col)
for n,y,col,t in [("OUT+",320,C['red'],"→ Source Q2\n(Schritt 4)"),("OUT−",480,C['black'],"→ GND gemeinsam\n(Schritt 4)")]:
    m.wire([(1030,y),(1200,y)],col,9)
    m.d.rectangle([920,y-32,1030,y+32],fill=C['solder'],outline=C['dark'],width=2); m.text((975,y),n,26,anchor="mm")
    m.text((1215,y),t,26,anchor="lm")
m.box([60,620,640,770],(255,235,235),outline=C['red'],w=5)
m.text((350,695),"ACHTUNG Polarität!\nRot = +   ·   Schwarz = −\nvorher mit Multimeter messen",26,anchor="mm",fill=C['red'])
m.box([700,640,1540,750],(245,245,245),outline=C['grey'])
m.text((1120,695),"Rote LED = lädt   ·   blau/grün = voll",26,anchor="mm")
m.steps(["Polarität am Akku-Stecker messen: Rot muss + sein (Händler warnt).",
         "Akku-Kabel nur EINZELN kürzen – nie beide auf einmal (Kurzschluss!).",
         "Rot an B+, Schwarz an B− löten, mit Schrumpfschlauch isolieren.",
         "An OUT+ und OUT− je eine Litze löten – die gehen in Schritt 4 weiter.",
         "Test: USB-A→C-Kabel rein (C→C lädt nicht) → rote LED."])
m.warn("Beim Löten kein Strom drauf – USB ab, Akku-Drähte nie berühren lassen")
m.save("loeten_3_akku_lader.png")

def gnd(m,p):
    x,y=p; m.d.line([(x,y),(x,y+12)],fill=C['black'],width=5)
    for k,w in enumerate([26,17,8]): m.d.line([(x-w,y+12+k*8),(x+w,y+12+k*8)],fill=C['black'],width=4)
def chip(m,xy,name,pins,fill=(60,60,70)):
    m.box(xy,fill); x0,y0,x1,y1=xy
    m.text(((x0+x1)//2,(y0+y1)//2),name,24,fill="white",anchor="mm")
    for lab,(px,py),anc in pins: m.text((px,py),lab,24,fill="white",anchor=anc)

# ---------- 4 Stromweg ----------
BAT=C['red']; SW=C['orange']; V5=(200,0,120); GT=(90,90,160)
m = Img("Lötschritt 4: Stromweg – Akku → Schalter → 5-V-Wandler")
RY=730
m.box([40,170,250,430],(30,80,170)); m.text((145,300),"TC4056",28,fill="white",anchor="mm")
m.text((240,232),"OUT+",22,fill="white",anchor="rm"); m.text((240,380),"OUT−",22,fill="white",anchor="rm")
m.wire([(250,232),(420,232)],BAT)
m.wire([(250,380),(275,380),(275,RY)],C['black'])
m.dot((300,232),9,BAT); m.dot((360,232),9,BAT)
# Q2
chip(m,[420,175,640,290],"Q2\nAO3401A",[("S",(432,232),"lm"),("D",(628,232),"rm"),("G",(530,280),"md")])
m.wire([(530,290),(530,560)],GT)
m.wire([(360,232),(360,420),(530,420)],GT); m.dot((530,420),9,GT)
m.res((360,325),"",vertical=True); m.text((384,325),"47 kΩ",22,anchor="lm")
# switch
m.box([410,560,660,670],(200,200,205))
for lab,x in [("AUS",450),("Mitte",530),("AN",615)]:
    m.dot((x,560),8,C['dark']); m.text((x,580),lab,20,anchor="ma")
m.text((535,640),"Ein/Aus-Schalter",20,anchor="mm")
m.wire([(450,560),(450,515),(300,515),(300,232)],BAT)
m.wire([(615,560),(615,515),(720,515),(720,RY)],C['black'])
# drain -> pololu
m.wire([(640,232),(900,232)],SW); m.dot((800,232),9,SW)
m.wire([(800,232),(800,640),(800,RY)],SW,5)
m.res((800,365),"",vertical=True); m.text((824,365),"10 kΩ",22,anchor="lm")
m.res((800,580),"",vertical=True); m.text((824,580),"10 kΩ",22,anchor="lm")
m.dot((800,445),9,C['dark']); m.wire([(800,445),(880,445)],C['dark'],4)
m.text((890,445),"GPIO35 (CYD-Stecker P3)",22,anchor="lm")
m.text((770,190),"Akku-Teiler",22,anchor="md")
# pololu
m.box([900,170,1150,340],(0,110,90))
m.text((1025,255),"Pololu\nS13V10F5\n(kein EN-Pin)",22,fill="white",anchor="mm")
m.text((910,205),"VIN",20,fill="white",anchor="lm"); m.text((1140,205),"VOUT",20,fill="white",anchor="rm")
m.text((1025,330),"GND",20,fill="white",anchor="md")
m.wire([(1025,340),(1025,380)],C['black']); m.wire([(1025,380),(1025,RY)],C['black'])
m.wire([(1150,232),(1270,232)],V5); m.dot((1240,232),9,V5)
m.wire([(1240,232),(1240,430),(1290,430)],V5)
m.box([1290,170,1540,300],(245,215,0)); m.text((1415,235),"CYD 5 V\n(Anschluss\nlaut Doku offen)",21,anchor="mm")
m.box([1290,370,1540,500],(30,120,70)); m.text((1415,435),"FET-Platine:\nSource Q1 + Elko\n(Schritt 5)",21,fill="white",anchor="mm")
m.wire([(1540,270),(1568,270),(1568,RY)],C['black']); m.wire([(1540,480),(1568,480)],C['black'])
m.wire([(275,RY),(1568,RY)],C['black'])
m.text((1150,RY+12),"GND (alle zusammen)",22,anchor="ma")
m.text((330,RY+12),"OUT− = GND",20,anchor="ma")
for t,p,c in [("Akku +",(330,205),BAT),("geschaltet",(720,205),SW),("5 V",(1195,205),V5)]: m.text(p,t,20,anchor="mm",fill=c)
m.steps(["Schalter messen: welcher Außenpin ist bei Schieber OBEN mit Mitte verbunden = „AN“.",
         "Schalter: Mitte → Gate Q2, „AN“ → GND, „AUS“ → Source Q2. 47 kΩ zwischen G und S.",
         "TC4056 OUT+ → Source Q2. Drain Q2 → Pololu VIN.",
         "Akku-Teiler: 10 kΩ + 10 kΩ von Drain Q2 nach GND, Mitte → GPIO35.",
         "Pololu VOUT → CYD 5 V und FET-Platine. Alle GND verbinden."])
m.warn("Beim Löten kein Strom drauf – Akku ab, USB ab, Schalter auf AUS")
m.save("loeten_4_stromweg.png")

# ---------- 5 FET-Platine ----------
m = Img("Lötschritt 5: FET-Platine (LED-Strom-Schalter H1)")
m.box([25,100,490,780],(250,250,250),outline=C['grey'])
m.text((257,115),"Bauteile richtig herum",24,anchor="ma")
m.box([90,170,250,300],(130,60,170)); m.d.rectangle([145,215,195,255],fill=C['black'])
for k,(n,l) in enumerate([("1","G"),("2","S"),("3","D")]):
    x=120+k*50; m.d.rectangle([x-4,300,x+4,350],fill=(200,170,40)); m.text((x,358),n+"\n"+l,22,anchor="ma")
m.text((270,175),"AO3401A\nauf SOT-23-\nAdapter\n(Q1 und Q2)",20,anchor="la")
m.text((257,455),"Das sind die Chip-Beine 1/2/3, nicht die\nAdapter-Stifte 1–10! Am Adapter: G = Stift 2,\nS = Stift 4, D = Stift 8 (siehe Plan 5b)",16,anchor="mm",fill=C['red'])
m.d.pieslice([110,490,230,610],180,360,fill=C['black']); m.d.rectangle([110,549,230,600],fill=C['black'])
m.text((170,570),"BC547B",18,fill="white",anchor="mm")
for k,l in enumerate(["C","B","E"]):
    x=135+k*35; m.d.rectangle([x-3,600,x+3,680],fill=(200,170,40)); m.text((x,690),l,24,anchor="ma")
m.text((270,520),"BC547B\nflache Seite\nzu dir,\nBeine unten",20,anchor="la")
# schematic
RY=170
m.wire([(560,RY),(1080,RY)],V5)
m.text((560,150),"5 V von Pololu VOUT (Schritt 4)",22,anchor="ld",fill=V5)
m.wire([(620,RY),(620,250)],V5); m.d.rectangle([590,250,650,340],fill=(40,70,160),outline=C['dark'],width=3)
m.d.rectangle([635,250,650,340],fill=(200,200,210)); m.text((612,262),"+",24,fill="white",anchor="mt")
m.wire([(620,340),(620,380)],C['black']); gnd(m,(620,380))
m.text((665,280),"Elko\n470 µF / 25 V",20,anchor="la")
m.text((665,335),"Streifen = −",18,anchor="la",fill=C['grey'])
chip(m,[980,240,1180,340],"Q1\nAO3401A",[("S",(1080,250),"mt"),("D",(1170,290),"rm"),("G",(990,290),"lm")])
m.wire([(1080,RY),(1080,240)],V5)
m.wire([(1180,290),(1320,290)],V5); m.text((1330,290),"→ LED-Streifen +\n(Schritt 6)",22,anchor="lm")
m.wire([(900,RY),(900,430)],GT); m.wire([(900,290),(980,290)],GT); m.dot((900,290),9,GT); m.dot((900,RY),9,V5)
m.res((900,230),"",vertical=True); m.text((876,230),"10 kΩ",22,anchor="rm")
m.box([840,430,1010,550],(60,60,70)); m.text((940,490),"BC547B",22,fill="white",anchor="mm")
for lab,(px,py),anc in [("C",(900,436),"mt"),("B",(848,490),"lm"),("E",(900,544),"md")]: m.text((px,py),lab,22,fill="white",anchor=anc)
m.wire([(900,550),(900,600)],C['black']); gnd(m,(900,600))
m.wire([(840,490),(560,490),(560,690)],GT); m.dot((760,490),9,GT)
m.res((660,490),"4,7 kΩ"); m.wire([(760,490),(760,630)],GT,5); m.res((760,575),"",vertical=True)
m.text((784,575),"47 kΩ",22,anchor="lm"); gnd(m,(760,630))
m.text((575,700),"GPIO18 (SD-Slot Pin 5, Schritt 2)",22,anchor="la")
m.box([1080,430,1570,690],(245,245,245),outline=C['grey'])
m.text((1325,560),"Q2 (Ein/Aus) kommt auch\nauf diese Platine –\nVerdrahtung: Schritt 4.\nAnordnung auf dem Lochraster\nlaut Doku offen (30 × 24,5 mm)",20,anchor="mm")
m.steps(["AO3401A auf die SOT-23-Adapter löten (2×): Chip-Bein 1 = G, 2 = S, 3 = D.",
         "Q1: S an 5 V, D an LED-Streifen +, 10 kΩ zwischen G und S.",
         "BC547B: C an G (Q1), E an GND, B über 4,7 kΩ an GPIO18.",
         "47 kΩ von B nach GND. Elko: + an 5 V, Streifen-Seite (−) an GND.",
         "Mit Multimeter prüfen: kein Kurzschluss zwischen 5 V und GND."])
m.warn("Beim Löten kein Strom drauf – Akku ab, USB ab")
m.save("loeten_5_fet_platine.png")

# ---------- 6 LED + Regensensor ----------
m = Img("Lötschritt 6: LED-Streifen und Regensensor")
m.text((400,110),"LED-Streifen (Eingang)",26,anchor="ma")
m.box([420,170,760,460],(245,245,240))
for k in range(4): m.d.ellipse([560+k*45,300,590+k*45,330],fill=(255,240,180),outline=C['grey'])
m.text((630,390),"Pfeil →",24,anchor="mm")
pads=[("5V",220,C['red'],"5 V ← Drain Q1\n(Schritt 5)"),("DIN",315,C['green'],"GPIO23\n(SD Pin 3)"),("GND",410,C['white'],"GND")]
for n,y,col,t in pads:
    m.d.rectangle([420,y-24,500,y+24],fill=C['solder'],outline=C['dark'],width=2); m.text((460,y),n,22,anchor="mm")
    m.wire([(230,y),(420,y)],col); m.text((40,y),t,22,anchor="lm")
m.res((340,315),"470 Ω")
m.text((340,350),"direkt am\nStreifen",18,anchor="ma")
m.text((40,520),"Kabelfarben am Streifen: Rot 5 V,\nGrün DIN, Weiß GND (Pads prüfen)",20,anchor="la")
m.d.line([(800,110),(800,760)],fill=C['grey'],width=2)
m.text((1180,110),"Regensensor (LM393-Modul)",26,anchor="ma")
m.box([1070,170,1300,480],(30,90,200)); m.text((1215,330),"LM393",24,fill="white",anchor="mm")
mp=[("VCC",210,C['red'],"3,3 V *"),("GND",290,C['black'],"GND"),("DO",370,C['teal'],"GPIO19\n(SD Pin 7)"),("AO",450,None,"frei")]
for n,y,col,t in mp:
    m.d.rectangle([1070,y-20,1140,y+20],fill=C['solder'],outline=C['dark'],width=2); m.text((1105,y),n,20,anchor="mm")
    if col: m.wire([(960,y),(1070,y)],col)
    m.text((950,y),t,22,anchor="rm",fill=col if col==C['teal'] else (C['grey'] if not col else C['black']))
m.box([1400,180,1560,470],(60,60,60))
for k in range(6): m.d.line([(1420,200+k*45),(1540,200+k*45)],fill=(220,190,60),width=6)
m.wire([(1300,280),(1400,280)],C['dark'],5); m.wire([(1300,370),(1400,370)],C['dark'],5)
m.text((1480,490),"Platte: 2 Kabel,\negal wie rum",20,anchor="ma")
m.text((830,560),"* 3,3-V-Abgriff am CYD laut Doku offen\n  (im Test: CN1 Rot)",20,anchor="la")
m.text((830,640),"Modul-Kabel direkt anlöten,\nnicht höher als ca. 12 mm",20,anchor="la")
m.steps(["LED-Streifen: den EINGANG benutzen (Pfeil zeigt vom Eingang weg).",
         "470 Ω direkt am Streifen in die Datenleitung: GPIO23 → 470 Ω → DIN.",
         "Streifen 5V an Drain Q1 (nicht an 3,3 V!), GND an GND.",
         "Regensensor: VCC an 3,3 V, GND an GND, DO an GPIO19, AO frei.",
         "Lötstellen mit Schrumpfschlauch isolieren."])
m.warn("Beim Löten kein Strom drauf – Akku ab, USB ab")
m.save("loeten_6_led_regensensor.png")
