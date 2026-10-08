# HydroDesk Base – Blender-Szenen fuer Visualisierungen (Cycles)
# Aufruf: blender -b -P scene.py -- <modus> <out_png> [samples]
import bpy, bmesh, sys, json, math
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--')+1:]
MODE = argv[0]; OUT = argv[1]; SAMPLES = int(argv[2]) if len(argv) > 2 else 96
PCT = int(argv[3]) if len(argv) > 3 else 100
RES = (2560, 1440)
import os
HERE = os.path.dirname(os.path.abspath(__file__)) + '/'

# ---------------- Masse aus hydrodesk_base.scad ----------------
W, D, H = 180, 100, 25
floor_t = 2.0; base_h = 23
cyd_x, cyd_y, cyd_w, cyd_l = 4.4, 10.8, 50, 86
cyd_cx, cyd_cy = cyd_x + cyd_w/2, cyd_y + cyd_l/2
cyd_pcb_z, cyd_pcb_t = 18.4, 1.5
lcd_top_z = 23.5
cyd_holes = [(8.4, 14.8), (8.4, 92.8), (50.4, 14.8), (50.4, 92.8)]
bat = (12.15, 41.0, 2.0, 34.5, 56, 10.3)
boost = (10.9, 19.0, 3.0, 37, 17)
tc = (56, 71.6, 3.5, 17, 26)
fet = (56, 37.5, 2.0, 17, 30)
cmp_ = (56, 5.3, 2.0, 16, 30)
hx = (136, 60, 2.0, 34, 21)
rs = (75.5, 20, 1.2, 40, 54)
pad_cx, pad_cy = 126, 50
lc_x0, lc_y0, lc_z0 = pad_cx - 6.35, 10, 5
pad_top_z = 22.3
cov_bosses = [(77, 7), (77, 93), (175.5, 20), (175.5, 80)]
led_x0, led_x1 = 6.5, 173.5
feet_pos = [(11, 11), (169, 11), (11, 89), (169, 89)]

# ---------------- Szene leeren ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = SAMPLES
scn.cycles.use_adaptive_sampling = True
scn.cycles.use_denoising = True
scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.cycles.max_bounces = 8
scn.cycles.transmission_bounces = 12
scn.cycles.transparent_max_bounces = 16
scn.render.resolution_x, scn.render.resolution_y = RES
scn.render.resolution_percentage = PCT
scn.render.film_transparent = True
scn.render.threads_mode = 'AUTO'
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Medium High Contrast'
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'
scn.render.image_settings.color_depth = '8'

# ---------------- Materialien ----------------
MATS = {}
def mat(name, col, rough=0.5, metal=0.0, emis=None, estr=0.0, coat=0.0, trans=0.0, ior=1.45, alpha=1.0, spec=0.5):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Transmission Weight'].default_value = trans
    b.inputs['IOR'].default_value = ior
    b.inputs['Alpha'].default_value = alpha
    b.inputs['Specular IOR Level'].default_value = spec
    if emis:
        b.inputs['Emission Color'].default_value = (*emis, 1)
        b.inputs['Emission Strength'].default_value = estr
    MATS[name] = m; return m

def tex_mat(name, img, emis=0.0, rough=0.4, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(HERE + 'tex/' + img)
    t.interpolation = 'Cubic'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if emis:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emis
    return m

LED_STR = {'produkt': 4.0, 'explosion': 4.0, 'innen': 4.0, 'teile': 3.0}.get(MODE, 4.0)
M = dict(
    pla=mat('PLA grau', (0.50, 0.51, 0.52), 0.55, spec=0.4),
    pad=mat('PLA blau', (0.05, 0.25, 0.75), 0.45),
    sil=mat('Silikon', (0.035, 0.037, 0.04), 0.85, spec=0.3),
    pcb_y=mat('PCB gelb', (0.80, 0.55, 0.02), 0.35, coat=0.3),
    pcb_g=mat('PCB gruen', (0.02, 0.30, 0.08), 0.35, coat=0.3),
    pcb_b=mat('PCB blau', (0.02, 0.10, 0.55), 0.35, coat=0.3),
    pcb_r=mat('PCB rot', (0.62, 0.03, 0.03), 0.35, coat=0.3),
    pcb_p=mat('PCB lila', (0.25, 0.06, 0.45), 0.35, coat=0.3),
    pcb_t=mat('PCB petrol', (0.01, 0.30, 0.30), 0.35, coat=0.3),
    black=mat('Chip', (0.02, 0.02, 0.022), 0.35),
    lcd=mat('LCD Rahmen', (0.01, 0.01, 0.012), 0.25, coat=0.6),
    alu=mat('Alu', (0.80, 0.81, 0.83), 0.28, metal=1.0),
    steel=mat('Stahl', (0.62, 0.62, 0.64), 0.22, metal=1.0),
    gold=mat('Gold', (0.95, 0.70, 0.30), 0.25, metal=1.0),
    white=mat('Weiss', (0.85, 0.85, 0.83), 0.45),
    rubber=mat('Gummi', (0.03, 0.03, 0.03), 0.9, spec=0.2),
    potblue=mat('Poti', (0.05, 0.25, 0.80), 0.4),
    flex=mat('Flex', (0.75, 0.38, 0.05), 0.35, coat=0.5),
    tape=mat('Akkuband', (0.80, 0.62, 0.30), 0.5),
    bat=mat('Akku', (0.06, 0.065, 0.07), 0.35, coat=0.3),
    term=mat('Klemme', (0.05, 0.45, 0.25), 0.45),
    led_on=mat('LED', (0.1, 0.4, 1.0), 0.2, emis=(0.0, 0.22, 1.0), estr=LED_STR),
    glass=mat('Glas', (0.95, 0.97, 1.0), 0.03, trans=1.0, ior=1.06),
    water=mat('Wasser', (0.55, 0.80, 1.0), 0.08, trans=1.0, ior=1.08),
    cap=mat('Deckel Flasche', (0.85, 0.87, 0.9), 0.35, metal=0.6),
    guide=mat('Hilfslinie', (0.0, 0.0, 0.0), 1.0, emis=(0.12, 0.13, 0.15), estr=1.0),
    w_red=mat('Kabel rot', (0.75, 0.03, 0.02), 0.4), w_blk=mat('Kabel schwarz', (0.03, 0.03, 0.03), 0.4),
    w_yel=mat('Kabel gelb', (0.9, 0.7, 0.02), 0.4), w_grn=mat('Kabel gruen', (0.03, 0.5, 0.12), 0.4),
    w_wht=mat('Kabel weiss', (0.85, 0.85, 0.85), 0.4), w_blu=mat('Kabel blau', (0.03, 0.2, 0.8), 0.4),
)
WC = {'r': M['w_red'], 'k': M['w_blk'], 'y': M['w_yel'], 'g': M['w_grn'], 'w': M['w_wht'], 'b': M['w_blu']}

# ---------------- Geometrie-Helfer ----------------
coll = scn.collection
def link(obj, m=None):
    coll.objects.link(obj)
    if m is not None: obj.data.materials.append(m)
    return obj

def mesh_from(name, verts, faces, m, smooth=False, uvs=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if uvs is not None:
        uv = me.uv_layers.new()
        for p in me.polygons:
            for li in p.loop_indices:
                uv.data[li].uv = uvs[me.loops[li].vertex_index]
    return link(bpy.data.objects.new(name, me), m)

def bevel(o, w=0.3, seg=3, angle=50):
    b = o.modifiers.new('bev', 'BEVEL'); b.width = w; b.segments = seg
    b.limit_method = 'ANGLE'; b.angle_limit = math.radians(angle); b.harden_normals = False
    for p in o.data.polygons: p.use_smooth = True
    try: o.data.set_sharp_from_angle(angle=math.radians(40))
    except Exception: pass
    return o

def box(name, x0, y0, z0, w, l, h, m, bev=0.25, seg=2):
    v = [(x0, y0, z0), (x0+w, y0, z0), (x0+w, y0+l, z0), (x0, y0+l, z0),
         (x0, y0, z0+h), (x0+w, y0, z0+h), (x0+w, y0+l, z0+h), (x0, y0+l, z0+h)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = mesh_from(name, v, f, m)
    if bev > 0: bevel(o, bev, seg)
    return o

def rrect_pts(x0, y0, w, l, r, n=8):
    pts = []
    for cx, cy, a0 in [(x0+w-r, y0+r, -90), (x0+w-r, y0+l-r, 0), (x0+r, y0+l-r, 90), (x0+r, y0+r, 180)]:
        for i in range(n+1):
            a = math.radians(a0 + 90*i/n); pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return pts

def prism(name, pts, z0, h, m, bev=0.0, uv_box=None):
    n = len(pts)
    v = [(x, y, z0) for x, y in pts] + [(x, y, z0+h) for x, y in pts]
    f = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    f += [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    uvs = None
    if uv_box:
        x0, y0, w, l = uv_box; uvs = [((x-x0)/w, (y-y0)/l) for x, y, z in v]
    o = mesh_from(name, v, f, m, uvs=uvs)
    if bev > 0: bevel(o, bev, 3)
    return o

def rbox(name, x0, y0, z0, w, l, h, r, m, bev=0.0):
    return prism(name, rrect_pts(x0, y0, w, l, r), z0, h, m, bev)

def cyl(name, cx, cy, z0, d, h, m, n=40, bev=0.0, d2=None):
    d2 = d if d2 is None else d2
    v = []
    for i in range(n):
        a = 2*math.pi*i/n; v.append((cx + d/2*math.cos(a), cy + d/2*math.sin(a), z0))
    for i in range(n):
        a = 2*math.pi*i/n; v.append((cx + d2/2*math.cos(a), cy + d2/2*math.sin(a), z0+h))
    f = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))] + [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    o = mesh_from(name, v, f, m)
    for p in o.data.polygons: p.use_smooth = True
    o.data.set_sharp_from_angle(angle=math.radians(40))
    if bev > 0: bevel(o, bev, 2)
    return o

def plane(name, x0, y0, z, w, l, m):
    v = [(x0, y0, z), (x0+w, y0, z), (x0+w, y0+l, z), (x0, y0+l, z)]
    return mesh_from(name, v, [(0, 1, 2, 3)], m, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])

def lathe(name, prof, m, n=72, cx=0, cy=0, z0=0):
    v = []; f = []
    for (r, z) in prof:
        for i in range(n):
            a = 2*math.pi*i/n; v.append((cx + r*math.cos(a), cy + r*math.sin(a), z0+z))
    for j in range(len(prof)-1):
        for i in range(n):
            a = j*n+i; b = j*n+(i+1) % n
            f.append((a, b, b+n, a+n))
    if prof[0][0] > 0:
        v.append((cx, cy, z0+prof[0][1])); c = len(v)-1
        for i in range(n): f.append((c, (i+1) % n, i))
    if prof[-1][0] > 0:
        v.append((cx, cy, z0+prof[-1][1])); c = len(v)-1; o = (len(prof)-1)*n
        for i in range(n): f.append((c, o+i, o+(i+1) % n))
    return mesh_from(name, v, f, m, smooth=True)

def catmull(pts, k=10):
    P = [Vector(p) for p in pts]; P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P)-2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        for s in range(k):
            t = s/k
            out.append(0.5*((2*p1) + (-p0+p2)*t + (2*p0-5*p1+4*p2-p3)*t*t + (-p0+3*p1-3*p2+p3)*t**3))
    out.append(P[-2]); return out

def wire(name, pts, m, r=0.45):
    cd = bpy.data.curves.new(name, 'CURVE'); cd.dimensions = '3D'
    cd.bevel_depth = r; cd.bevel_resolution = 3; cd.use_fill_caps = True
    sp = cd.splines.new('POLY'); P = catmull(pts); sp.points.add(len(P)-1)
    for i, p in enumerate(P): sp.points[i].co = (p.x, p.y, p.z, 1)
    o = bpy.data.objects.new(name, cd); coll.objects.link(o); cd.materials.append(m); return o

def bundle(name, pts, cols, sp=1.0, r=0.45):
    P = catmull(pts, 6); n = len(cols); objs = []
    for k, c in enumerate(cols):
        off = (k - (n-1)/2) * sp; Q = []
        for i in range(len(P)):
            t = (P[min(i+1, len(P)-1)] - P[max(i-1, 0)]); t2 = Vector((t.x, t.y, 0))
            nrm = Vector((-t2.y, t2.x, 0)).normalized() if t2.length > 1e-3 else Vector((1, 0, 0))
            if t2.length < 0.25*t.length: nrm = Vector((1, 0, 0)) if abs(t.x) < abs(t.y) else Vector((0, 1, 0))
            Q.append(P[i] + nrm*off)
        cd = bpy.data.curves.new(name+str(k), 'CURVE'); cd.dimensions = '3D'
        cd.bevel_depth = r; cd.bevel_resolution = 3; cd.use_fill_caps = True
        s = cd.splines.new('POLY'); s.points.add(len(Q)-1)
        for i, p in enumerate(Q): s.points[i].co = (p.x, p.y, p.z, 1)
        o = bpy.data.objects.new(name+str(k), cd); coll.objects.link(o); cd.materials.append(WC[c]); objs.append(o)
    return objs

def import_stl(name, path, m):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]; o.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    o.data.set_sharp_from_angle(angle=math.radians(32))
    o.data.materials.clear(); o.data.materials.append(m)
    return o

# ---------------- Gruppen (Empty als Eltern) ----------------
GROUPS = {}; ANCH = {}
def group(gname, objs, pivot=None):
    if pivot is None:
        mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
        for o in objs:
            for c in o.bound_box:
                p = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, p)); mx = Vector(map(max, mx, p))
        pivot = (mn + mx) / 2
    e = bpy.data.objects.new('G_'+gname, None); e.location = pivot; coll.objects.link(e)
    bpy.context.view_layer.update()
    for o in objs:
        o.parent = e; o.matrix_parent_inverse = e.matrix_world.inverted()
    GROUPS[gname] = e; return e

def anchor(name, gname, p):
    ANCH[name] = (gname, Vector(p))

def gbbox(gname):
    bpy.context.view_layer.update()
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
    for o in GROUPS[gname].children:
        if o.hide_render: continue
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, p)); mx = Vector(map(max, mx, p))
    return mn, mx

# ---------------- Bauteile ----------------
def pins(name, x0, y0, z0, n, axis='x', pitch=2.54, m_plastic=None):
    objs = []
    for i in range(n):
        x = x0 + (i*pitch if axis == 'x' else 0); y = y0 + (i*pitch if axis == 'y' else 0)
        objs.append(box(name+'p%d' % i, x-0.32, y-0.32, z0, 0.64, 0.64, 6.0, M['gold'], 0.05, 1))
    L = (n-1)*pitch + 2.54
    if axis == 'x': objs.append(box(name+'pl', x0-1.27, y0-1.27, z0, L, 2.54, 2.5, M['black'], 0.15))
    else: objs.append(box(name+'pl', x0-1.27, y0-1.27, z0, 2.54, L, 2.5, M['black'], 0.15))
    return objs

def make_cyd():
    o = []
    o.append(prism('CYD PCB', rrect_pts(cyd_x, cyd_y, cyd_w, cyd_l, 3), cyd_pcb_z, cyd_pcb_t, M['pcb_y'], 0.2))
    for i, (hx_, hy_) in enumerate(cyd_holes):
        o.append(cyl('CYD ring%d' % i, hx_, hy_, cyd_pcb_z-0.03, 6.0, cyd_pcb_t+0.06, M['gold'], 32))
        o.append(cyl('CYD loch%d' % i, hx_, hy_, cyd_pcb_z-0.06, 3.2, cyd_pcb_t+0.12, M['black'], 24))
    ly0 = cyd_cy - 0.7 - 34.6
    o.append(box('LCD', cyd_cx-25, ly0, cyd_pcb_z+cyd_pcb_t, 50, 69.2, 3.4, M['lcd'], 0.35))
    o.append(box('Flex', cyd_cx-11, ly0-3.2, cyd_pcb_z+cyd_pcb_t, 22, 3.6, 0.15, M['flex'], 0.0))
    scr = tex_mat('Screen UI', 'screen_ui.png', emis=1.6, rough=0.15, coat=1.0)
    o.append(plane('Screen', cyd_cx-21.6, cyd_cy-3.5-28.8, lcd_top_z+0.01, 43.2, 57.6, scr))
    # Rueckseite: ESP32-Modul, USB, JST-Stecker, SD-Slot
    o.append(box('ESP32 PCB', 12.4, 60.8, cyd_pcb_z-0.9, 18, 25.5, 0.9, M['black'], 0.1))
    o.append(box('ESP32 Schirm', 13.2, 61.4, cyd_pcb_z-3.2, 16.4, 18, 2.3, M['steel'], 0.3))
    o.append(box('Micro-USB', cyd_cx+4.5, 89.8, cyd_pcb_z-3.2, 9, 7.6, 3.2, M['steel'], 0.5))
    o.append(box('USB-C CYD', cyd_cx-12, 90.0, cyd_pcb_z-3.2, 9, 7.4, 3.2, M['steel'], 0.8))
    o.append(box('SD', cyd_cx-7, cyd_y+1, cyd_pcb_z-2.2, 15, 15, 2.2, M['steel'], 0.2))
    for i, (x, y) in enumerate([(49.6, 63), (49.6, 47), (49.6, 31), (5.2, 37), (5.2, 22)]):
        o.append(box('JST%d' % i, x, y, cyd_pcb_z-4.0, 4.0, 7.0, 4.0, M['white'], 0.2))
    # Vorderseite: Bauteile auf dem gelben Streifen hinten
    o.append(box('Chip1', 12, 89.5, cyd_pcb_z+cyd_pcb_t, 5, 4, 1.0, M['black'], 0.1))
    o.append(box('Chip2', 40, 90, cyd_pcb_z+cyd_pcb_t, 3, 3, 0.8, M['black'], 0.1))
    o.append(box('RGB-LED', 20, 90.5, cyd_pcb_z+cyd_pcb_t, 5, 5, 1.4, M['white'], 0.2))
    for i, x in enumerate([28.5, 34.5]):
        o.append(box('Taster%d' % i, x, 89.5, cyd_pcb_z+cyd_pcb_t, 4.5, 3.5, 1.6, M['steel'], 0.2))
        o.append(box('Tknopf%d' % i, x+1.25, 90.25, cyd_pcb_z+cyd_pcb_t+1.6, 2, 2, 0.6, M['black'], 0.1))
    for i in range(6):
        o.append(box('R%d' % i, 14 + i*4.6, 14, cyd_pcb_z+cyd_pcb_t, 1.6, 0.8, 0.5, M['black'] if i % 2 else M['white'], 0.05))
    g = group('cyd', o)
    anchor('cyd', 'cyd', (cyd_cx-14, cyd_cy+18, lcd_top_z)); anchor('cyd_esp', 'cyd', (21, 72, cyd_pcb_z-3.2))
    return g

def make_battery():
    x, y, z, w, l, h = bat; o = []
    o.append(box('Akku', x, y+1.5, z, w, l-1.5, h, M['bat'], 1.6, 4))
    o.append(box('Akku Band', x+2, y, z+2.2, w-4, 2.0, h-4.4, M['tape'], 0.4))
    o.append(plane('Akku Label', x+3, y+8, z+h+0.02, w-6, 40, tex_mat('Akkulabel', 'battery_label.png', rough=0.5)))
    o[-1].rotation_euler = (0, 0, 0)
    # Label um 90 Grad drehen (Text laeuft entlang Y)
    me = o[-1].data; uv = me.uv_layers[0]
    for li, lp in enumerate(me.loops):
        u, v = uv.data[li].uv; uv.data[li].uv = (v, 1-u)
    o += bundle('Akku Kabel', [(x+w/2, y+0.5, z+5), (x+w/2, y-2, z+3), (x+w/2+3, y-4.5, z+1.5)], 'rk', 1.1, 0.5)
    g = group('bat', o); anchor('bat', 'bat', (x+w/2, y+l*0.6, z+h)); return g

def make_boost():
    x, y, z, w, l = boost; o = []
    o.append(box('Boost PCB', x, y, z, w, l, 1.2, M['pcb_p'], 0.15))
    o.append(box('Spule', x+14, y+4.5, z+1.2, 8, 8, 4.0, M['black'], 0.6))
    o.append(box('MT3608', x+24, y+6, z+1.2, 3, 3, 1.0, M['black'], 0.1))
    o.append(box('Poti', x+4, y+9.5, z+1.2, 9.5, 4.5, 4.5, M['potblue'], 0.3))
    o.append(cyl('Poti Schraube', x+5.2, y+11.7, z+3.5, 1.8, 2.3, M['gold'], 16))
    for i, (px, py) in enumerate([(x+1, y+1.2), (x+1, y+l-4.2), (x+w-4, y+1.2), (x+w-4, y+l-4.2)]):
        o.append(box('Pad%d' % i, px, py, z+1.2, 3, 3, 0.15, M['gold'], 0.0))
    o.append(box('C1', x+6, y+3, z+1.2, 3.2, 1.6, 1.4, M['tape'], 0.1))
    o.append(box('C2', x+27, y+11, z+1.2, 3.2, 1.6, 1.4, M['tape'], 0.1))
    g = group('boost', o); anchor('boost', 'boost', (x+18, y+8.5, z+5)); return g

def make_tc():
    x, y, z, w, l = tc; o = []
    o.append(box('TC PCB', x, y, z, w, l, 1.6, M['pcb_b'], 0.15))
    o.append(box('USB-C', x+w/2-4.5, D-2.4-7.3, z+1.6, 9, 7.3, 3.2, M['steel'], 1.2, 3))
    o.append(box('TC4056', x+5, y+9, z+1.6, 5, 4, 1.5, M['black'], 0.1))
    o.append(box('LED r', x+2, y+14, z+1.6, 1.6, 0.8, 0.6, mat('led r', (1, .1, .1), .3, emis=(1, .05, .02), estr=2)))
    o.append(box('LED b', x+13, y+14, z+1.6, 1.6, 0.8, 0.6, mat('led b', (.1, .3, 1), .3, emis=(.05, .2, 1), estr=2)))
    for i, px in enumerate([x+1, x+5, x+10, x+14]):
        o.append(box('TCpad%d' % i, px, y+0.8, z+1.6, 2.4, 3, 0.15, M['gold'], 0.0))
    g = group('tc', o); anchor('tc', 'tc', (x+w/2, y+12, z+3)); anchor('usbc', 'tc', (x+w/2, D-2.4, z+3.2)); return g

def make_fet():
    x, y, z, w, l = fet; o = []
    o.append(box('FET PCB', x, y, z, w, l, 1.6, M['pcb_r'], 0.15))
    o.append(box('MOSFET', x+5, y+11, z+1.6, 7, 6.5, 2.3, M['black'], 0.2))
    o.append(box('MOSFET Tab', x+6.5, y+17.5, z+1.6, 4, 2.5, 0.6, M['steel'], 0.1))
    o.append(box('Klemme1', x+1.5, y+0.5, z+1.6, 14, 7.5, 6.4, M['term'], 0.4))
    o.append(box('Klemme2', x+1.5, y+l-8, z+1.6, 14, 7.5, 6.4, M['term'], 0.4))
    for k, yy in enumerate([y+0.5, y+l-8]):
        for j in range(3):
            o.append(cyl('Kschr%d%d' % (k, j), x+3.8+j*5, yy+3.75, z+7.9, 3, 0.25, M['steel'], 16))
    g = group('fet', o); anchor('fet', 'fet', (x+w/2, y+14, z+3.9)); return g

def make_cmp():
    x, y, z, w, l = cmp_; o = []
    o.append(box('LM393 PCB', x, y, z, w, l, 1.6, M['pcb_t'], 0.15))
    o.append(box('LM393', x+4.5, y+13, z+1.6, 5, 4, 1.4, M['black'], 0.1))
    o.append(box('Poti2', x+4.5, y+20, z+1.6, 7, 7, 4.5, M['potblue'], 0.4))
    o.append(cyl('Poti2 Kopf', x+8, y+23.5, z+6.1, 4, 0.5, M['white'], 20))
    o.append(box('LED1', x+2, y+9, z+1.6, 1.6, 0.8, 0.6, mat('led g', (.1, 1, .2), .3, emis=(.1, 1, .2), estr=2)))
    o += pins('H4', x+w/2-3.81, y+l-1.8, z+1.6, 4, 'x')
    o += pins('H2', x+w-1.8, y+3.5, z+1.6, 2, 'y')
    g = group('cmp', o); anchor('cmp', 'cmp', (x+w/2, y+12, z+3)); return g

def make_hx():
    x, y, z, w, l = hx; o = []
    o.append(box('HX PCB', x, y, z, w, l, 1.6, M['pcb_g'], 0.15))
    o.append(box('HX711', x+11, y+6, z+1.6, 10, 6.2, 1.6, M['black'], 0.1))
    for i in range(8):
        o.append(box('HXleg%d' % i, x+11.6+i*1.2, y+5.2, z+1.6, 0.4, 0.8, 0.4, M['steel'], 0.0))
        o.append(box('HXleg2%d' % i, x+11.6+i*1.2, y+12.2, z+1.6, 0.4, 0.8, 0.4, M['steel'], 0.0))
    o.append(box('HX C', x+24, y+14, z+1.6, 3.2, 1.6, 1.2, M['tape'], 0.1))
    o.append(box('HX Q', x+5, y+14, z+1.6, 3, 3, 1.0, M['black'], 0.1))
    for i in range(4):
        o.append(box('HXpadL%d' % i, x+1, y+3+i*4, z+1.6, 2.5, 2, 0.15, M['gold'], 0.0))
    o += pins('HXH', x+w-1.6, y+3.6, z+1.6, 4, 'y')
    g = group('hx', o); anchor('hx', 'hx', (x+16, y+9, z+3.2)); return g

def make_rs():
    x, y, z, w, l = rs; o = []
    o.append(box('Regen PCB', x, y, z, w, l, 1.6, M['pcb_t'], 0.15))
    o.append(plane('Regen Kamm', x+0.4, y+0.4, z+1.62, w-0.8, l-0.8, tex_mat('Regenplatte', 'rain_plate.png', rough=0.3)))
    # Textur: unten (Bild) = vorne (kleines y) -> UV v umdrehen nicht noetig
    g = group('rs', o); anchor('rs', 'rs', (x+12, y+14, z+1.6)); return g

def make_loadcell():
    x0, y0, z0 = lc_x0, lc_y0, lc_z0; w = 12.7; l = 80; o = []
    bar = box('Waegezelle', x0, y0, z0, w, l, w, M['alu'], 0.5, 2)
    cut = []
    # Doppelbohrung entlang X (Biegebalken-Fenster) und senkrechte Gewindeloecher
    def xcyl(cx, cy, cz, d, L):
        n = 40; v = []
        for i in range(n):
            a = 2*math.pi*i/n; v.append((cx, cy + d/2*math.cos(a), cz + d/2*math.sin(a)))
        for i in range(n):
            a = 2*math.pi*i/n; v.append((cx+L, cy + d/2*math.cos(a), cz + d/2*math.sin(a)))
        f = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))] + [(i, n+i, n+(i+1) % n, (i+1) % n) for i in range(n)]
        return mesh_from('cut', v, f, M['black'])
    cut.append(xcyl(x0-2, 46.0, z0+w/2, 8.6, w+4)); cut.append(xcyl(x0-2, 54.0, z0+w/2, 8.6, w+4))
    cut.append(box('cutb', x0-2, 46.0, z0+w/2-1.6, w+4, 8.0, 3.2, M['black'], 0))
    for yy, d in [(15, 4.0), (30, 4.0), (70, 5.0), (85, 5.0)]:
        cut.append(cyl('cutv', pad_cx, yy, z0-2, d, w+4, M['black'], 32))
    bar.modifiers.clear()
    for c in cut:
        bm_ = bmesh.new(); bm_.from_mesh(c.data); bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces); bm_.to_mesh(c.data); bm_.free()
        c.hide_render = True; c.hide_viewport = True
        md = bar.modifiers.new('bool', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = c; md.solver = 'EXACT'
    o += cut
    bevel(bar, 0.5, 2)
    o.append(bar)
    o.append(box('DMS Verguss', x0+1.8, 45, z0+w, w-3.6, 10, 0.9, M['white'], 0.4, 3))
    o.append(box('DMS Verguss u', x0+1.8, 45, z0-0.9, w-3.6, 10, 0.9, M['white'], 0.4, 3))
    # 4 Kabel am festen (hinteren) Ende
    o += bundle('LC Kabel', [(pad_cx, y0+l-1, z0+w-2.5), (pad_cx+1, y0+l+4, z0+5), (pad_cx+6, y0+l+5, 4),
                             (hx[0]-3, hx[1]+hx[4]-7, 4), (hx[0]+1.2, hx[1]+hx[4]-9, hx[2]+1.8)], 'rkwg', 0.9, 0.38)
    g = group('lc', o, pivot=Vector((pad_cx, 50, z0+6)))
    anchor('lc', 'lc', (pad_cx+6.35, 52, z0+9)); anchor('lc_fix', 'lc', (pad_cx, 82, z0+w)); return g

def make_led():
    o = [box('LED-Streifen', led_x0+2, 3.1, 3.7, led_x1-led_x0-4, 0.4, 10, M['white'], 0.1)]
    for i in range(10):
        x = led_x0 + 5.8 + i*16.67
        o.append(box('LED%d' % i, x, 1.5, 6.2, 5, 1.6, 5, M['white'], 0.25))
        o.append(cyl('LEDl%d' % i, x+2.5, 1.49, 8.7, 3.6, 0.05, M['led_on'], 24))
        o[-1].rotation_euler = (0, 0, 0)
    # Lichtpunkte nach vorne drehen: Kreis in XZ statt XY
    for ob in o[1:]:
        if ob.name.startswith('LEDl'):
            me = ob.data; c = Vector((0, 0, 0))
            for v in me.vertices: c += v.co
            c /= len(me.vertices)
            for v in me.vertices:
                dx, dy = v.co.x - c.x, v.co.y - c.y; dz = v.co.z - c.z
                v.co = Vector((c.x + dx, 1.47 - dz, c.z + dy))
    g = group('led', o); anchor('led', 'led', (led_x0+5.8+1*16.67+2.5, 1.5, 11.2)); return g

def m3(name, x, y, ztop, L=12, head=6.0):
    o = [cyl(name+'k', x, y, ztop-1.7, 3.0, 1.7, M['steel'], 32, d2=head),
         cyl(name+'s', x, y, ztop-L, 2.8, L-1.6, M['steel'], 24)]
    o.append(box(name+'x1', x-head*0.32, y-0.35, ztop-0.01, head*0.64, 0.7, 0.03, M['black'], 0))
    o.append(box(name+'x2', x-0.35, y-head*0.32, ztop-0.01, 0.7, head*0.64, 0.03, M['black'], 0))
    return o

def screw_down(name, x, y, ztop, d, L, head):  # Senkkopf oben, Schaft nach unten
    o = [cyl(name+'k', x, y, ztop-d*0.55, d, d*0.55, M['steel'], 32, d2=head),
         cyl(name+'s', x, y, ztop-L, d*0.92, L-d*0.5, M['steel'], 24)]
    o.append(box(name+'x1', x-head*0.3, y-0.4, ztop-0.01, head*0.6, 0.8, 0.03, M['black'], 0))
    o.append(box(name+'x2', x-0.4, y-head*0.3, ztop-0.01, 0.8, head*0.6, 0.03, M['black'], 0))
    return o

def screw_up(name, x, y, zbot, d, L, head):     # Senkkopf unten, Schaft nach oben
    return [cyl(name+'k', x, y, zbot, head, d*0.55, M['steel'], 32, d2=d),
            cyl(name+'s', x, y, zbot+d*0.5, d*0.92, L-d*0.5, M['steel'], 24)]

def foot(name, x, y, ztop):
    return [lathe(name, [(0, -3.2), (3.5, -3.1), (5.2, -2.6), (6.0, -1.8), (6.2, 0.0), (0, 0.0)], M['rubber'], 48, x, y, ztop)]

def make_mat():
    o = rbox('Silikonmatte', 81+2.1, 5+2.1, pad_top_z, 85.8, 85.8, 3, 3.0, M['sil'], 0.0)
    o.scale = (1, 1, 1)
    me = o.data
    for v in me.vertices:
        if v.co.z > pad_top_z + 1: v.co.z = pad_top_z + 1.5
    bevel(o, 0.5, 3)
    # Noppen
    objs = [o]
    nop = 6
    for i in range(nop):
        for j in range(nop):
            x = 81+2.1+10 + i*13.16; y = 5+2.1+10 + j*13.16
            objs.append(cyl('Noppe', x, y, pad_top_z+1.5, 3.0, 0.5, M['sil'], 16, d2=2.4))
    g = group('mat', objs); anchor('mat', 'mat', (81+2.1+75, 5+2.1+80, pad_top_z+1.5)); return g

# ---------------- Licht ----------------
def sun(name, rot, s, ang=12):
    l = bpy.data.lights.new(name, 'SUN'); l.energy = s; l.angle = math.radians(ang)
    o = bpy.data.objects.new(name, l); o.rotation_euler = Euler([math.radians(a) for a in rot]); coll.objects.link(o); return o

def world(col, s):
    w = bpy.data.worlds.new('W'); w.use_nodes = True; scn.world = w
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (*col, 1); bg.inputs[1].default_value = s

def camera(target, az, el, dist, lens=100, ortho=None):
    c = bpy.data.cameras.new('Cam'); c.lens = lens; c.clip_start = 1; c.clip_end = 20000
    c.sensor_width = 36
    if ortho: c.type = 'ORTHO'; c.ortho_scale = ortho
    o = bpy.data.objects.new('Cam', c); coll.objects.link(o)
    t = Vector(target); a = math.radians(az); e = math.radians(el)
    dirv = Vector((-math.sin(a)*math.cos(e), -math.cos(a)*math.cos(e), math.sin(e)))
    o.location = t + dirv*dist
    o.rotation_euler = (t - o.location).to_track_quat('-Z', 'Y').to_euler()
    scn.camera = o; return o

def shadow_catcher(z, size=3000, col=(0.45, 0.47, 0.5)):
    p = plane('Boden', -size/2+90, -size/2+50, z, size, size, mat('Boden', col, 0.8)); p.is_shadow_catcher = True; return p

def dashed(name, p0, p1, dash=3.0, gap=2.2, r=0.25):
    p0 = Vector(p0); p1 = Vector(p1); L = (p1-p0).length; d = (p1-p0).normalized(); t = 0; objs = []
    while t < L:
        a = p0 + d*t; b = p0 + d*min(t+dash, L)
        if d.z != 0 and abs(d.x) < 1e-6 and abs(d.y) < 1e-6:
            objs.append(cyl(name, a.x, a.y, min(a.z, b.z), 2*r, abs(b.z-a.z), M['guide'], 8))
        t += dash + gap
    return objs

# ---------------- Gemeinsamer Geraeteaufbau ----------------
SRC = HERE + 'stl/'
def build_all(cables=False):
    base = import_stl('Unterschale', SRC+'base.stl', M['pla']); group('base', [base])
    anchor('base', 'base', (178, 50, 16)); anchor('base_l', 'base', (2, 40, 14)); anchor('base_f', 'base', (60, 0.5, 18)); anchor('base_in', 'base', (100, 88, floor_t))
    anchor('boss', 'base', (175.5, 80, 21))
    cover = import_stl('Deckel', SRC+'cover.stl', M['pla']); group('cover', [cover])
    anchor('cover', 'cover', (178, 60, 25)); anchor('cover_win', 'cover', (29.4, 85, 25))
    pad = import_stl('Flaschenplatte', SRC+'pad.stl', M['pad']); group('pad', [pad])
    anchor('pad', 'pad', (170, 70, 24.6)); anchor('pad_notch', 'pad', (81.5, 50, 23))
    make_mat(); make_cyd(); make_battery(); make_boost(); make_tc(); make_fet(); make_cmp()
    make_hx(); make_rs(); make_loadcell(); make_led()

def place(gname, dz=0, dx=0, dy=0):
    GROUPS[gname].location += Vector((dx, dy, dz))

def hide_group(g):
    GROUPS[g].hide_render = True
    for o in GROUPS[g].children_recursive: o.hide_render = True

PIVOT0 = {}
def snapshot_pivots():
    for k, e in GROUPS.items():
        if k not in PIVOT0: PIVOT0[k] = e.location.copy()

# =========================== MODI ===========================
extra = {}
if MODE == 'explosion':
    build_all(); snapshot_pivots()
    world((0.5, 0.52, 0.55), 0.55)
    sun('key', (50, 0, 35), 2.2, 8); sun('fill', (65, 0, -110), 0.7, 30); sun('rim', (60, 0, 200), 1.2, 15)
    Z = dict(feet=-32, m5=-54, base=0, A=36, B=80, pad=122, m4=138, mat=148, cover=174, m3=196)
    for g in ['bat', 'boost']: place(g, Z['A'])
    for g in ['lc', 'hx', 'tc', 'fet', 'cmp', 'rs']: place(g, Z['B'])
    place('cyd', Z['B']-8)
    place('led', 0, 0, -26)
    place('pad', Z['pad']); place('mat', Z['mat']); place('cover', Z['cover'])
    # Schrauben / Fuesse
    sc = []
    for i, (x, y) in enumerate(cyd_holes + cov_bosses): sc += m3('M3_%d' % i, x, y, H + Z['m3'])
    group('m3', sc); anchor('m3', 'm3', (175.5, 80, H+Z['m3']-1))
    s4 = []
    for i, yy in enumerate([15, 30]): s4 += screw_down('M4_%d' % i, pad_cx, yy, pad_top_z + Z['m4'], 4, 10, 8.4)
    group('m4', s4); anchor('m4', 'm4', (pad_cx+4, 30, pad_top_z+Z['m4']))
    s5 = []
    for i, yy in enumerate([85, 70]): s5 += screw_up('M5_%d' % i, pad_cx, yy, Z['m5'], 5, 12, 10.5)
    group('m5', s5); anchor('m5', 'm5', (pad_cx+5.2, 70, Z['m5']+1.5))
    ft = []
    for i, (x, y) in enumerate(feet_pos): ft += foot('Fuss%d' % i, x, y, Z['feet'])
    group('feet', ft); anchor('feet', 'feet', (169, 11, Z['feet']-2.5))
    snapshot_pivots()
    # Hilfslinien
    for (x, y) in cov_bosses: dashed('g', (x, y, 21), (x, y, H+Z['m3']-12))
    for (x, y) in cyd_holes:
        dashed('g', (x, y, 18.4), (x, y, cyd_pcb_z+Z['B']-8)); dashed('g', (x, y, cyd_pcb_z+Z['B']-8+1.5), (x, y, H+Z['m3']-12))
    for yy in [15, 30]: dashed('g', (pad_cx, yy, 17.7+Z['B']), (pad_cx, yy, pad_top_z+Z['m4']-10))
    for yy in [70, 85]: dashed('g', (pad_cx, yy, Z['m5']+12), (pad_cx, yy, 0))
    for (x, y) in feet_pos: dashed('g', (x, y, Z['feet']), (x, y, 0))
    cam = camera((90, 50, 93), -28, 24, 1800, lens=100)
    cam.data.shift_y = 0.0

elif MODE == 'innen':
    build_all(); snapshot_pivots()
    hide_group('cover'); hide_group('pad'); hide_group('mat')
    LIFT = 70
    place('cyd', LIFT)
    world((0.5, 0.52, 0.55), 0.6)
    sun('key', (45, 0, -40), 3.0, 10); sun('fill', (65, 0, 100), 0.9, 30); sun('rim', (55, 0, 200), 1.2, 15)
    sc = []
    for i, (x, y) in enumerate(cyd_holes): sc += m3('M3c%d' % i, x, y, cyd_pcb_z + cyd_pcb_t + LIFT + 9)
    group('m3', sc)
    for (x, y) in cyd_holes:
        dashed('g', (x, y, 18.4), (x, y, cyd_pcb_z+LIFT))
    ft = []
    for i, (x, y) in enumerate(feet_pos): ft += foot('Fuss%d' % i, x, y, 1.0)
    group('feet', ft)
    zc = cyd_pcb_z - 4.0 + LIFT   # Unterkante JST am angehobenen CYD
    # Kabel (Farben: rot +, schwarz -, gelb/gruen/weiss Signal)
    bundle('K_HX', [(hx[0]+1, hx[1]+12, 4.2), (133, 88, 3.2), (128, 95.5, 3.2), (100, 95.0, 3.0), (80, 70, 3.0),
                    (62, 69.2, 3.0), (54, 68, 5), (52.5, 66.5, 25), (51.6, 66.5, zc)], 'rkyw', 1.0)
    bundle('K_CMP', [(64, 35.4, 4.0), (57, 36.2, 4.0), (54, 39, 4.0), (53.4, 47, 5), (52.5, 50.5, 26), (51.6, 50.5, zc)], 'rky', 1.0)
    bundle('K_FET', [(60, 38, 3.9), (54, 33, 3.2), (48.6, 27.5, 4.4)], 'rk', 1.1)
    bundle('K_PWR', [(boost[0]+2, boost[1]+8.5, 4.4), (7.5, 30, 5), (7.0, 39, 22), (7.2, 40.5, zc)], 'rk', 1.1)
    bundle('K_LED', [(10.5, 5.5, 8.5), (10, 10, 4), (7.5, 18, 4), (7.0, 24, 22), (7.2, 25.5, zc)], 'rgk', 1.0)
    bundle('K_BAT', [(bat[0]+bat[3]/2+3, bat[1]-4.5, 3.5), (44, 38.5, 3.0), (53, 46, 3.0), (54, 62, 3.0), (56, 69, 3.6), (59, 73, 5.4)], 'rk', 1.1)
    bundle('K_TCF', [(68, 72.5, 5.4), (68.5, 70, 4.2), (68.5, 66.8, 4.0)], 'rk', 1.1)
    bundle('K_RS', [(95, 21, 2.9), (86, 13, 3.2), (75, 10, 4.2), (72.3, 9.9, 4.3)], 'kw', 1.0)
    shadow_catcher(-2.2)
    anchor('cables', None, (80, 70, 3.2)); anchor('k_led', None, (10, 10, 4))
    cam = camera((96, 52, 46), -25, 50, 1280, lens=100)

elif MODE == 'produkt':
    build_all(); snapshot_pivots()
    world((0.10, 0.11, 0.13), 0.6)
    sun('key', (48, 0, -38), 3.4, 6); sun('fill', (70, 0, 95), 0.8, 30); sun('rim', (60, 0, 195), 2.2, 10)
    sc = []
    for i, (x, y) in enumerate(cyd_holes + cov_bosses): sc += m3('M3_%d' % i, x, y, H)
    group('m3', sc)
    for i, yy in enumerate([15, 30]): screw_down('M4_%d' % i, pad_cx, yy, pad_top_z, 4, 10, 8.4)
    ft = []
    for i, (x, y) in enumerate(feet_pos): ft += foot('Fuss%d' % i, x, y, 1.0)
    # Geisterflasche
    zb = pad_top_z + 1.5 + 0.5; R = 33
    prof = [(0, 0), (R-3, 0), (R-0.5, 1.5), (R, 5), (R, 122), (R-5, 136), (13, 148), (12, 153), (0, 153)]
    bottle = lathe('Flasche', prof, M['glass'], 96, pad_cx, pad_cy, zb)
    lathe('Flaschendeckel', [(0, 152), (13.5, 152), (14, 153), (14, 166), (13.5, 167), (0, 167)], M['cap'], 64, pad_cx, pad_cy, zb)
    fill = 4 + 118*0.56
    lathe('Wasser', [(0, 1.5), (R-2.0, 1.5), (R-1.2, 4), (R-1.2, fill), (0, fill)], M['water'], 96, pad_cx, pad_cy, zb)
    shadow_catcher(-2.2, col=(0.03, 0.034, 0.04))
    MATS['Weiss'].node_tree.nodes['Principled BSDF']  # noqa
    strip = bpy.data.objects['LED-Streifen']; sm = mat('Streifen leuchtend', (0.6, 0.75, 1.0), 0.4, emis=(0.05, 0.3, 1.0), estr=0.9)
    strip.data.materials.clear(); strip.data.materials.append(sm)
    # Glanz fuer LEDs ueber Compositor
    scn.use_nodes = True; nt = scn.node_tree
    rl = nt.nodes['Render Layers']; comp = nt.nodes['Composite']
    gl = nt.nodes.new('CompositorNodeGlare'); gl.glare_type = 'FOG_GLOW'; gl.quality = 'HIGH'
    try: gl.size = 8
    except Exception: pass
    try: gl.threshold = 1.0
    except Exception: pass
    try: gl.mix = 0.0
    except Exception: pass
    nt.links.new(rl.outputs['Image'], gl.inputs['Image']); nt.links.new(gl.outputs['Image'], comp.inputs['Image'])
    cam = camera((100, 48, 78), -22, 20, 1320, lens=100); cam.data.shift_x = -0.16

elif MODE == 'teile':
    build_all(); snapshot_pivots()
    world((0.5, 0.52, 0.55), 0.6)
    sun('key', (35, 0, -30), 3.0, 10); sun('fill', (60, 0, 110), 0.8, 30)
    # Schneidematte 540 x 330
    MW, MH = 540, 330
    matobj = box('Schneidematte', 0, 0, -2, MW, MH, 2, None, 0.8, 3)
    matobj.data.materials.append(tex_mat('Matte', 'cutting_mat.png', rough=0.75))
    me = matobj.data; uv = me.uv_layers.new()
    for p in me.polygons:
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv = (v.x/MW, v.y/MH)
    def lay(g, x0, y0, rot=(0, 0, 0)):
        e = GROUPS[g]; e.rotation_euler = Euler([math.radians(a) for a in rot])
        mn, mx = gbbox(g); e.location += Vector((x0 - mn.x, y0 - mn.y, 0.02 - mn.z))
    lay('cover', 15, 214); lay('base', 210, 214); lay('pad', 410, 219)
    lay('cyd', 15, 102); lay('bat', 82, 118); lay('mat', 135, 100)
    lay('rs', 238, 118); lay('lc', 300, 162, (0, 0, -90)); lay('hx', 300, 112)
    lay('tc', 398, 140); lay('fet', 432, 138); lay('cmp', 466, 138); lay('boost', 398, 100)
    lay('led', 15, 36, (-90, 0, 0))
    # Schrauben liegend + Fuesse
    def lying(objs, x, y):
        g = 's%d_%d' % (x, y); group(g, objs); lay(g, x, y, (90, 0, 0)); return g
    sx = 212
    for i in range(8): lying(m3('M3t%d' % i, 0, 0, 0), sx + i*9, 28)
    for i in range(2): lying(screw_down('M4t%d' % i, 0, 0, 0, 4, 10, 8.4), sx + 80 + i*12, 28)
    for i in range(2): lying(screw_up('M5t%d' % i, 0, 0, 0, 5, 12, 10.5), sx + 110 + i*14, 28)
    for i in range(4):
        f = foot('Fusst%d' % i, 0, 0, 0); g = 'f%d' % i; group(g, f); lay(g, 370 + i*17, 30)
    anchor_list = []
    shadow_catcher(-2.05)
    bpy.context.view_layer.update()
    # Anker: obere linke Ecke jeder Gruppe (fuer Nummern) + Mitte
    TE = {}
    for g in ['cover', 'base', 'pad', 'cyd', 'bat', 'mat', 'rs', 'lc', 'hx', 'tc', 'fet', 'cmp', 'boost', 'led']:
        mn, mx = gbbox(g); TE[g] = (mn, mx)
    sx_mn = Vector((sx-1, 22, 0)); sx_mx = Vector((sx+140, 40, 6)); TE['screws'] = (sx_mn, sx_mx)
    TE['feet'] = (Vector((364, 24, 0)), Vector((370+3*17+13, 42, 3)))
    for g, (mn, mx) in TE.items():
        ANCH[g+'_tl'] = (None, Vector((mn.x, mx.y, mx.z)))
        ANCH[g+'_bc'] = (None, Vector(((mn.x+mx.x)/2, mn.y, 0)))
        ANCH[g+'_c'] = (None, Vector(((mn.x+mx.x)/2, (mn.y+mx.y)/2, mx.z)))
    ANCH['mat_tl_corner'] = (None, Vector((0, MH, 0))); ANCH['mat_br_corner'] = (None, Vector((MW, 0, 0)))
    cam = camera((MW/2 + 95, MH/2 - 4, 0), 0, 68, 3000, lens=100, ortho=760)

# Anker projizieren
bpy.context.view_layer.update()
proj = {}
for k, (g, p) in ANCH.items():
    if g is not None and g in GROUPS:
        e = GROUPS[g]
        if e.hide_render: continue
        pw = e.matrix_world @ (p - PIVOT0[g]) if g in PIVOT0 else p
    else:
        pw = p
    v = world_to_camera_view(scn, cam, pw)
    proj[k] = [v.x*RES[0]*PCT/100, (1-v.y)*RES[1]*PCT/100, v.z]
json.dump(proj, open(OUT.replace('.png', '.json'), 'w'), indent=1)
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('DONE', OUT)
