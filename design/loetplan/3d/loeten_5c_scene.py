# -*- coding: utf-8 -*-
# Blender: 3D-Ansicht FET-Platine (Lötschritt 5c, Layout loeten_5b).
# Aufruf: blender -b -P loeten_5c_scene.py -- [oben|unten|blend] [out.png] [samples]
import bpy, sys, math, json, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from loeten_3d_common import prepare_fresh_scene, group_by_prefix, pack_and_save, set_view_to_camera

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['blend']
MODE = argv[0] if argv else 'blend'
OUT = argv[1] if len(argv) > 1 else os.path.join(HERE, 'loeten_5c_fet_3d.blend')
SAMPLES = int(argv[2]) if len(argv) > 2 else 0
scn = prepare_fresh_scene('Loetschritt_5c_FET_Platine')
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = SAMPLES if SAMPLES > 0 else 64
scn.cycles.use_denoising = True; scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.render.resolution_x, scn.render.resolution_y = 2000, 1500
scn.render.film_transparent = True
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
coll = scn.collection
ROWS = "ABCDEFGHIJ"
PI = 2.54
def hp(h):  # "F04" -> (x,y)
    c = int(h[1:]); r = ROWS.index(h[0])
    return ((c-1)*PI, -(r-1)*PI)   # Reihe B = 0

MATS = {}
def mat(name, col, rough=0.5, metal=0.0, coat=0.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    MATS[name] = m; return m
def srgb(c): return tuple(((v/255)**2.2) for v in c)
NETC = dict(v5=(215,30,30), gnd=(25,25,25), g1=(30,90,220), b=(140,60,190), io18=(20,150,60),
            led=(210,0,150), bat=(150,85,30), g2=(0,155,160), vin=(240,130,0))
M = dict(pcb=mat('pcb', srgb((30,110,60)), 0.45, coat=0.4), tin=mat('tin', (0.78,0.78,0.80), 0.22, 1.0),
         hole=mat('hole', (0.02,0.02,0.02), 0.8), purple=mat('adapter', srgb((105,40,140)), 0.4, coat=0.4),
         gold=mat('gold', (0.95,0.70,0.30), 0.25, 1.0), black=mat('black', (0.02,0.02,0.022), 0.4),
         plastic=mat('plastic', (0.03,0.03,0.03), 0.5), res=mat('res', srgb((120,170,220)), 0.45),
         elko=mat('elko', srgb((30,70,170)), 0.35, coat=0.5), stripe=mat('stripe', srgb((210,215,225)), 0.4),
         alu=mat('alu', (0.8,0.81,0.83), 0.3, 1.0), rubber=mat('rubber', (0.04,0.04,0.04), 0.9),
         lead=mat('lead', (0.75,0.75,0.77), 0.25, 1.0), chiptxt=mat('chiptxt', (0.6,0.6,0.6), 0.5))
BAND = {0:(0,0,0),1:(120,60,20),2:(220,0,0),3:(255,120,0),4:(255,210,0),5:(0,150,0),6:(0,0,220),7:(130,40,190),
        'gold':(200,160,60)}
def link(o, m=None):
    coll.objects.link(o)
    if m is not None: o.data.materials.append(m)
    return o
def mesh(name, v, f, m, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return link(bpy.data.objects.new(name, me), m)
def box(name, x0, y0, z0, w, l, h, m):
    v = [(x0,y0,z0),(x0+w,y0,z0),(x0+w,y0+l,z0),(x0,y0+l,z0),(x0,y0,z0+h),(x0+w,y0,z0+h),(x0+w,y0+l,z0+h),(x0,y0+l,z0+h)]
    return mesh(name, v, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], m)
def cbox(name, cx, cy, z0, w, l, h, m): return box(name, cx-w/2, cy-l/2, z0, w, l, h, m)
def cyl(name, cx, cy, z0, d, h, m, n=32, axis='z'):
    v = []
    for z in (0, h):
        for i in range(n):
            a = 2*math.pi*i/n; v.append((d/2*math.cos(a), d/2*math.sin(a), z))
    f = [tuple(range(n-1,-1,-1)), tuple(range(n,2*n))] + [(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
    o = mesh(name, v, f, m, smooth=True)
    if axis == 'x': o.rotation_euler = (0, math.pi/2, 0)
    o.location = (cx, cy, z0)
    return o
def tube(name, pts, m, r=0.3):
    cd = bpy.data.curves.new(name, 'CURVE'); cd.dimensions = '3D'; cd.bevel_depth = r; cd.bevel_resolution = 4
    cd.use_fill_caps = True
    sp = cd.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]; bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cd); coll.objects.link(o); cd.materials.append(m); return o
def sphere(name, c, r, m, sz=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=c, segments=24, ring_count=12)
    o = bpy.context.active_object; o.scale = (1,1,sz); o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    return o

# ---------- Layout (identisch zu make_5b.py) ----------
BRIDGES = [('v5',["E04","F04","G04","H04"]),('g1',["E02","F02","F03","G03"]),('b',["G02","H02","H03"]),
           ('io18',["G01","H01"]),('gnd',["I01","I02","I03","J03","J04"]),('gnd',["J01","J02","J03"]),
           ('g2',["E07","F07","F06"]),('bat',["E09","F09","F08"]),('bat',["F09","F10"])]
JUMPERS = [('led',"B03","F01"),('vin',"B08","F05")]
PADS = [(1,"G04",'v5'),(2,"J02",'gnd'),(3,"F01",'led'),(4,"J01",'gnd'),(5,"H01",'io18'),
        (6,"F09",'bat'),(7,"F06",'g2'),(8,"F10",'bat'),(9,"I01",'gnd'),(10,"F05",'vin')]
RES = [("R1",(1,0,3),"F03","F04"),("R2",(4,7,2),"G01","G02"),("R3",(4,7,3),"I02","H02"),("R4",(4,7,3),"F08","F07")]
T1 = ["G03","H03","I03"]

T = 1.6   # Platinendicke, Oberseite z=0
x0b, x1b = -3.57, 22.86+3.57; y1b, y0b = 2.09, -20.32-2.09
box('Lochrasterplatine', x0b, y0b, -T, x1b-x0b, y1b-y0b, T, M['pcb'])
ANCH = {}
legs = set()
for r in "BCDEFGHIJ":
    for c in range(1,11):
        h = "%s%02d" % (r,c); x,y = hp(h)
        for z, s in ((0.0,1), (-T,-1)):
            cyl('pad', x, y, z if s>0 else z-0.035, 1.8, 0.035, M['tin'], 20)
            cyl('loch', x, y, z+0.036 if s>0 else z-0.07, 0.95, 0.001+0.0, M['hole'], 16)

def leg_end(h, zt):   # Bein durch Loch + Lötkegel unten
    x,y = hp(h); legs.add(h)
    tube('bein', [(x,y,-T-1.0),(x,y,zt)], M['lead'], 0.25)
# ---------- SOT-23-Adapter ----------
ADAPT = [("Q1",1,{"E02":"G","E04":"S","B03":"D"}),("Q2",6,{"E07":"G","E09":"S","B08":"D"})]
ZA = 2.5
for name, c0, pins in ADAPT:
    xa, _ = hp("B%02d" % c0); xb, _ = hp("B%02d" % (c0+4)); cx = (xa+xb)/2
    yB = hp("B01")[1]; yE = hp("E01")[1]; cy = (yB+yE)/2
    cbox(name+'_Adapter', cx, cy, ZA, 12.7, 10.2, 1.6, M['purple'])
    for yy in (yB, yE):
        cbox('Stiftleiste', cx, yy, 0, 12.7, 2.5, ZA, M['plastic'])
        for c in range(c0, c0+5):
            x,_ = hp("B%02d" % c)
            cbox('Stift', x, yy, -T-1.2, 0.64, 0.64, ZA+1.6+1.2+T+1.0, M['gold'])
            sphere('Zinn', (x,yy,ZA+1.6), 0.55, M['tin'], 0.5)
            legs.add("%s%02d" % ("B" if yy==yB else "E", c))
    # Chip SOT-23: 2 Beine nach Reihe E (−y), 1 Bein nach Reihe B
    zc = ZA+1.6
    for i in range(5):
        for yy in (cy-1.6, cy+1.6):
            cbox('smdpad', cx-1.9+i*0.95, yy, zc, 0.5, 1.2, 0.04, M['gold'])
    cbox(name+'_Chip', cx, cy, zc+0.1, 2.9, 1.6, 1.0, M['black'])
    for dx, s in ((-0.95,-1),(0.95,-1),(0,1)):
        cbox('sotbein', cx+dx, cy+s*1.15, zc+0.04, 0.4, 0.9, 0.12, M['lead'])
    ANCH[name] = (cx, cy, zc+1.2)
    for h, lab in pins.items():
        x,y = hp(h); ANCH[name+lab] = (x, y, ZA+1.6+1.0)
# ---------- Widerstände stehend ----------
for ref, bands, hb, hl in RES:
    xb_, yb_ = hp(hb); xl, yl = hp(hl)
    z0, L = 1.0, 6.0
    cyl(ref, xb_, yb_, z0+0.4, 2.3, L-0.8, M['res'])
    sphere(ref+'k1', (xb_,yb_,z0+0.5), 1.25, M['res'], 0.55); sphere(ref+'k2', (xb_,yb_,z0+L-0.5), 1.25, M['res'], 0.55)
    zz = [z0+0.9, z0+1.7, z0+2.5, z0+4.6]
    cols = [BAND[bands[0]], BAND[bands[1]], BAND[bands[2]], BAND['gold']]
    # Erstes Band oben (gut lesbar von oben)
    for k,(zb, cc) in enumerate(zip(reversed(zz[:3]) if False else [z0+L-1.0, z0+L-1.8, z0+L-2.6, z0+1.3], cols)):
        cyl(ref+'band', xb_, yb_, zb, 2.36, 0.5, mat('band%s'%str(cc), srgb(cc), 0.5))
    tube(ref+'b1', [(xb_,yb_,-T-1.0),(xb_,yb_,z0+0.5)], M['lead'], 0.25)
    tube(ref+'b2', [(xb_,yb_,z0+L-0.4),(xb_,yb_,z0+L+1.0),((xb_+xl)/2,(yb_+yl)/2,z0+L+1.8),(xl,yl,z0+L+0.8),(xl,yl,2.0),(xl,yl,-T-1.0)], M['lead'], 0.25)
    legs.add(hb); legs.add(hl)
    ANCH[ref] = (xb_, yb_, z0+L+1.5)
# ---------- BC547B ----------
xs, ys = hp("G03"); _, ye = hp("I03"); ym = (ys+ye)/2
zt0, zt1 = 3.0, 7.6
pts = []
xf = xs-1.6
for i in range(25):
    a = -math.pi/2 + math.pi*i/24
    pts.append((xf + 3.7*math.cos(a), ym + 2.3*math.sin(a)))
pts = [(xf, ym-2.3)] + pts + [(xf, ym+2.3)]
n = len(pts)
v = [(x,y,zt0) for x,y in pts] + [(x,y,zt1) for x,y in pts]
f = [tuple(range(n-1,-1,-1)), tuple(range(n,2*n))] + [(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)]
o = mesh('T1_BC547B', v, f, M['black'])
cbox('T1_Schrift', xf-0.01, ym, zt0+1.4, 0.02, 3.0, 1.6, M['chiptxt'])
for h in T1:
    x,y = hp(h); tube('t1bein', [(x,y,-T-1.0),(x,y,0.5),(x,y,zt0+0.2)], M['lead'], 0.22); legs.add(h)
ANCH['T1'] = (xs+0.5, ym, zt1)
# ---------- Elko liegend ----------
yI = hp("I01")[1]; xe0, xe1 = 3.6*PI, 3.6*PI+16.0; ze = 5.0
cyl('Elko_C1', xe0+0.6, yI, ze, 10.0, 16.0-1.2, M['elko'], 48, 'x')
cyl('Elko_C1_Boden', xe0, yI, ze, 9.6, 0.6, M['rubber'], 48, 'x')
cyl('Elko_C1_Deckel', xe1-0.6, yI, ze, 9.4, 0.62, M['alu'], 48, 'x')
# Minus-Streifen: Teilzylinder auf der Seite zu Reihe J (−y)
nn = 16; v = []; f = []
for i in range(nn+1):
    a = math.radians(-150 + 60*i/nn)
    for x in (xe0+1.0, xe1-1.0):
        v.append((x, yI + 5.03*math.cos(a+math.pi/2)*-1 if False else yI + 5.03*math.sin(a), ze + 5.03*math.cos(a)))
for i in range(nn):
    f.append((2*i, 2*i+1, 2*i+3, 2*i+2))
mesh('Elko_C1_Streifen', v, f, M['stripe'], True)
for i in range(5):
    xm = xe0+2.5+i*2.8; a = math.radians(-120)
    cbox('minus', xm, yI + 5.06*math.sin(a), ze + 5.06*math.cos(a), 1.2, 0.05, 0.35, M['elko']).rotation_euler = (a,0,0)
for h, dy in (("H04", 2.54), ("J04", -2.54)):
    x,y = hp(h)
    tube('c1bein', [(xe0, yI+dy*0.98, ze+ (0 if True else 0)), (xe0-1.0, y, ze), (x, y, ze-2.0), (x, y, 0.5), (x, y, -T-1.0)], M['lead'], 0.25)
    legs.add(h)
ANCH['C1'] = ((xe0+xe1)/2, yI, ze+5.2)
ANCH['C1+'] = (hp("H04")[0], hp("H04")[1], ze)
# ---------- Anschluss-Litzen (oben) ----------
DIRS = {"F01":(-1,0),"H01":(-1,0),"I01":(-1,0),"J01":(-1,0.3),"J02":(0,-1),"G04":(0,-1),
        "F05":(0,1),"F06":(0,1),"F09":(0,1),"F10":(1,0)}
for nr, h, net in PADS:
    x,y = hp(h); dx,dy = DIRS[h]; legs.add(h)
    m = mat('litze'+net, srgb(NETC[net]), 0.45)
    if h == "G04":
        P = [(x,y,0.2),(x,y,9.5),(x-2,y+0.5,11.5),(x-10,y+1.5,11.5),(x-20,y+1.5,11.5)]
    elif h in ("F05","F06","F09"):
        P = [(x,y,0.2),(x,y,6.5),(x,y+2.5,8.5),(x,y+10,8.5),(x,y+16,8.5)]
    else:
        P = [(x,y,0.2),(x,y,3.0),(x+dx*3,y+dy*3,4.5),(x+dx*14,y+dy*14,4.5)]
    tube('Litze_%d'%nr, P, m, 0.55)
    tube('Ader_%d'%nr, [(x,y,-T-0.8),(x,y,0.3)], M['tin'], 0.3)
    e = P[-1]; ANCH['P%d'%nr] = e
    cyl('Litzenende', e[0], e[1], e[2], 0.5, 0.01, M['tin'])

# ---------- Unterseite: Lötstellen, Brücken, Drähte ----------
for h in legs:
    x,y = hp(h)
    sphere('Lötstelle', (x,y,-T-0.05), 0.95, M['tin'], 0.55)
for net, ch in BRIDGES:
    m = mat('bruecke'+net, tuple(0.9*c+0.06 for c in srgb(NETC[net])), 0.25, 0.85)
    for a, b in zip(ch, ch[1:]):
        (xa,ya),(xb,yb) = hp(a), hp(b)
        tube('Loetbruecke', [(xa,ya,-T-0.35),(xb,yb,-T-0.35)], m, 0.55)
for net, ha, hb in JUMPERS:
    (xa,ya),(xb,yb) = hp(ha), hp(hb)
    m = mat('draht'+net, srgb(NETC[net]), 0.4)
    mx, my = (xa+xb)/2 - 2.0, (ya+yb)/2
    tube('Draht_isoliert', [(xa,ya,-T-0.6),(xa,ya,-T-1.4),(mx,my,-T-1.6),(xb,yb,-T-1.4),(xb,yb,-T-0.6)], m, 0.45)
    ANCH['J'+net] = (mx, my, -T-2.1)

# Raster-Beschriftung
for c in range(1,11): ANCH['col%02d'%c] = ((c-1)*PI, y1b+1.8, 0 if MODE=='oben' else -T)
for r in "BCDEFGHIJ":
    ANCH['row'+r] = (x0b-1.8, hp(r+"01")[1], 0 if MODE=='oben' else -T)
for k in ("R1","R2","R3","R4"): pass


# ---------- 3D-Beschriftung, Licht, zwei Kameras, .blend speichern ----------
FONT_OBJ = FONT
def text3d(name, txt, loc, size=2.4, rot=(0, 0, 0)):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = txt
    cu.size = size
    cu.extrude = 0.06
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    try:
        cu.font = bpy.data.fonts.load(FONT_OBJ)
    except Exception:
        pass
    o = bpy.data.objects.new(name, cu)
    o.location = loc
    o.rotation_euler = rot
    coll.objects.link(o)
    if 'chiptxt' in M:
        cu.materials.append(M['chiptxt'])
    return o

# Bauteilnamen auf der Platine (liegen flach, von oben lesbar)
text3d('Beschriftung_Q1', 'Q1 LED-Strom', ANCH['Q1'], 2.2)
text3d('Beschriftung_Q2', 'Q2 Ein/Aus', ANCH['Q2'], 2.2)
text3d('Beschriftung_T1', 'T1 BC547B', ANCH['T1'], 2.0)
text3d('Beschriftung_R1', 'R1  10 kΩ', ANCH['R1'], 1.8)
text3d('Beschriftung_R2', 'R2  4,7 kΩ', ANCH['R2'], 1.8)
text3d('Beschriftung_R3', 'R3  47 kΩ', ANCH['R3'], 1.8)
text3d('Beschriftung_R4', 'R4  47 kΩ', ANCH['R4'], 1.8)
text3d('Beschriftung_C1', 'C1 Elko 470 µF', ANCH['C1'], 2.0)
for nr, h, net in PADS:
    if ('P%d' % nr) in ANCH:
        lab = {1:'5 V',2:'GND',3:'LED +',4:'LED GND',5:'GPIO18',
               6:'TC4056 OUT+',7:'Schalter Mitte',8:'Schalter AUS',
               9:'Schalter AN',10:'Pololu VIN'}[nr]
        x,y,z = ANCH['P%d'%nr]
        text3d('Beschriftung_Litze_%d' % nr, '%d  %s' % (nr, lab), (x, y, z+2.0), 1.8)

world = bpy.data.worlds.new('w'); scn.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75,0.77,0.8,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7

def light(name, loc, energy, size=30, aim=Vector((11.4, -10.2, 2.0))):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size
    o = bpy.data.objects.new(name, ld); coll.objects.link(o); o.location = loc
    o.rotation_euler = (aim - Vector(loc)).to_track_quat('-Z','Y').to_euler()
    return o

def make_cam(name, cen, cam_dir, scale=56):
    cd = bpy.data.cameras.new(name); cd.type = 'ORTHO'; cd.ortho_scale = scale
    cd.clip_start = 1; cd.clip_end = 2000
    cam = bpy.data.objects.new(name, cd); coll.objects.link(cam)
    cam.location = cen + cam_dir.normalized()*150
    cam.rotation_euler = (cen - cam.location).to_track_quat('-Z','Y').to_euler()
    return cam

cen_o = Vector((11.4, -10.2, 2.0))
cen_u = Vector((11.4, -10.2, -1.0))
# Licht von oben und unten, damit beide Kameras eine helle Ansicht haben
light('Licht_Haupt_Oben', (-30,-60,90), 90000, 30, cen_o)
light('Licht_Fuell_Oben', (70,40,60), 35000, 30, cen_o)
light('Licht_Kante_Oben', (10,60,40), 20000, 30, cen_o)
light('Licht_Haupt_Unten', (-30,-60,-90), 90000, 30, cen_u)
light('Licht_Fuell_Unten', (70,40,-60), 35000, 30, cen_u)
light('Licht_Kante_Unten', (10,60,-40), 20000, 30, cen_u)

cam_oben = make_cam('Kamera_Oben', cen_o, Vector((-0.45, -0.85, 1.55)))
cam_unten = make_cam('Kamera_Unten', cen_u, Vector((-0.45, 0.85, -1.55)))
# Standardansicht: Oberseite
scn.camera = cam_oben if MODE != 'unten' else cam_unten
bpy.context.view_layer.update()

# optional rendern (nur wenn eine PNG-Datei und Samples > 0 angegeben sind)
if SAMPLES > 0 and OUT.lower().endswith('.png'):
    scn.render.filepath = OUT
    json.dump({k: (world_to_camera_view(scn, scn.camera, Vector(p)).x*scn.render.resolution_x,
                    (1-world_to_camera_view(scn, scn.camera, Vector(p)).y)*scn.render.resolution_y)
               for k,p in ANCH.items()},
              open(OUT.replace('.png','.json'),'w'))
    bpy.ops.render.render(write_still=True)

group_by_prefix([
    ('Lochrasterplatine', ['Lochrasterplatine', 'pad', 'loch', 'Pad', 'Loch']),
    ('Q1_LED_Strom', ['Q1_']),
    ('Q2_Ein_Aus', ['Q2_']),
    ('T1_BC547B', ['T1_', 't1bein']),
    ('Widerstaende', ['R1', 'R2', 'R3', 'R4']),
    ('Elko_C1', ['Elko_', 'c1bein', 'minus']),
    ('Litzen', ['Litze_', 'Ader_', 'Litzenende']),
    ('Loetseite', ['Loetbruecke', 'Draht_isoliert', 'Lötstelle', 'Loetstelle']),
    ('Licht', ['Licht_']),
    ('Kamera', ['Kamera_']),
    ('Beschriftung', ['Beschriftung_']),
])
# Q1_Chip / Q2_Chip umbenennen in sprechende Namen
for old, new in (('Q1_Chip', 'Q1_LED_Strom'), ('Q2_Chip', 'Q2_Ein_Aus')):
    o = bpy.data.objects.get(old)
    if o:
        o.name = new

set_view_to_camera()
blend = os.path.join(HERE, 'loeten_5c_fet_3d.blend')
if OUT.lower().endswith('.blend'):
    blend = os.path.abspath(OUT)
pack_and_save(blend)
