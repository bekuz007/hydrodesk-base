# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE
# HydroDesk Base - realistisches Modell mit allen gekauften Teilen und der Verkabelung (Cycles).
# Aufruf: blender -b -P real_scene.py -- <modus> <ausgabe> [samples] [prozent]
#   Modi: offen | iso | explosion | detail | produkt | save | check
# Alle Masse in mm (Szene: 1 Blender-Einheit = 1 mm). Masse und Quellen: design/3d_modell/realistisch/README.md
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['check', '/tmp/x.png']
MODE = argv[0]; OUT = argv[1]; SAMPLES = int(argv[2]) if len(argv) > 2 and argv[2].isdigit() else 128
PCT = int(argv[3]) if len(argv) > 3 else 100
HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, HERE)
import cyd_layout as L
STL = HERE + '../../src/stl/'
TEX = HERE + 'tex/'
SL = '/opt/blender-dl/blender-4.5.4-linux-x64/4.5/datafiles/studiolights/world/'

# ---------------- Masse (aus hydrodesk_base.scad / ANLEITUNG) ----------------
W, D, H = 180, 100, 25
cyd_x, cyd_y, cyd_pcb_z, cyd_t = 4.4, 10.8, 18.4, 1.5
cyd_holes_uv = [(4, 4), (46, 4), (4, 82), (46, 82)]
pad_cx = 126
lc_x0, lc_y0, lc_z0 = pad_cx - 6.35, 10, 5
pad_top_z = 22.3
cov_bosses = [(77, 9.2), (77, 93), (175.5, 20), (175.5, 80)]
feet_pos = [(11, 11), (169, 11), (11, 89), (169, 89)]
cob_x0, cob_len, cob_zc = 10.6, 162.5, 8.75   # Annahme: Streifen 1,85 mm rechts von der Mitte (Litzen ins Kabelloch x 8,5-12)

# ---------------- Szene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.system = 'METRIC'; scn.unit_settings.scale_length = 0.001; scn.unit_settings.length_unit = 'MILLIMETERS'
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'
scn.cycles.samples = SAMPLES; scn.cycles.use_adaptive_sampling = True; scn.cycles.adaptive_threshold = 0.02
scn.cycles.use_denoising = True; scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.cycles.max_bounces = 10; scn.cycles.transmission_bounces = 10; scn.cycles.transparent_max_bounces = 16
scn.cycles.glossy_bounces = 6; scn.cycles.caustics_reflective = False; scn.cycles.caustics_refractive = False
scn.cycles.blur_glossy = 1.0
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.resolution_percentage = PCT
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
scn.render.image_settings.file_format = 'PNG'; scn.render.image_settings.color_mode = 'RGB'

ROOTC = scn.collection
def new_coll(name, parent=None):
    c = bpy.data.collections.new(name); (parent or ROOTC).children.link(c); return c
C_GEH = new_coll('Gehäuse'); C_EL = new_coll('Elektronik'); C_KAB = new_coll('Kabel'); C_ENV = new_coll('Umgebung')
CUR = [C_EL]

# ---------------- Materialien ----------------
MATS = {}
def srgb(c): return tuple(((v/255)**2.2) for v in c)
def mat(name, col, rough=0.5, metal=0.0, coat=0.0, emis=None, estr=0.0, trans=0.0, ior=1.45, alpha=1.0, sss=0.0, aniso=0.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = 0.08
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    b.inputs['Alpha'].default_value = alpha
    if aniso: b.inputs['Anisotropic'].default_value = aniso
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Radius'].default_value = (0.6, 0.6, 0.5)
        b.inputs['Subsurface Scale'].default_value = 0.6
    if emis:
        b.inputs['Emission Color'].default_value = (*emis, 1); b.inputs['Emission Strength'].default_value = estr
    if alpha < 1: m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    m.diffuse_color = (*col, alpha)
    MATS[name] = m; return m

def node_bump(m, kind, scale, strength, dist=0.05, coord='Object', detail=2.0, direction='Z'):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    if kind == 'wave':
        t = nt.nodes.new('ShaderNodeTexWave'); t.wave_type = 'BANDS'; t.bands_direction = direction
        t.inputs['Scale'].default_value = scale; t.inputs['Distortion'].default_value = 0.15
        t.inputs['Detail'].default_value = 0.0
    else:
        t = nt.nodes.new('ShaderNodeTexNoise'); t.inputs['Scale'].default_value = scale; t.inputs['Detail'].default_value = detail
    nt.links.new(tc.outputs[coord], t.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength; bp.inputs['Distance'].default_value = dist
    nt.links.new(t.outputs['Fac' if kind != 'wave' else 'Color'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def tex_mat(name, img, rough=0.4, coat=0.0, emis=0.0, metal=0.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(TEX + img); t.interpolation = 'Cubic'
    t.extension = 'EXTEND'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Coat Weight'].default_value = coat
    b.inputs['Coat Roughness'].default_value = 0.1; b.inputs['Metallic'].default_value = metal
    if emis:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emis
    m.diffuse_color = (0.5, 0.5, 0.5, 1)
    MATS[name] = m; return m

def milky_mat(name, glow=0.0, gcol=(0.25, 0.5, 1.0)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.93, 0.94, 0.95, 1); b.inputs['Roughness'].default_value = 0.45
    b.inputs['Subsurface Weight'].default_value = 1.0; b.inputs['Subsurface Radius'].default_value = (1.0, 1.0, 1.0)
    b.inputs['Subsurface Scale'].default_value = 1.5
    if glow:
        b.inputs['Emission Color'].default_value = (*gcol, 1); b.inputs['Emission Strength'].default_value = glow
    MATS[name] = m; return m

PLA = node_bump(mat('PLA grau', srgb((128, 131, 134)), 0.48, coat=0.0), 'wave', 1.57, 0.18, 0.03)   # Schichtlinien 0,2 mm
PLA_PAD = node_bump(mat('PLA blau (Pad)', srgb((22, 74, 168)), 0.42), 'wave', 1.57, 0.18, 0.03)
M = dict(
    pla=PLA, pad=PLA_PAD,
    tin=mat('Zinn', (0.80, 0.80, 0.82), 0.22, 1.0), gold=mat('Gold ENIG', (0.95, 0.72, 0.36), 0.25, 1.0),
    steel=mat('Edelstahl', (0.66, 0.66, 0.68), 0.28, 1.0), alu=node_bump(mat('Alu gebuerstet', (0.82, 0.83, 0.85), 0.32, 1.0, aniso=0.6), 'noise', 2.0, 0.08, 0.02),
    nickel=mat('Vernickelt', (0.74, 0.74, 0.76), 0.18, 1.0),
    epoxy=node_bump(mat('IC-Gehaeuse', (0.025, 0.025, 0.027), 0.55), 'noise', 6.0, 0.15, 0.01),
    black=mat('Kunststoff schwarz', (0.02, 0.02, 0.022), 0.45), nylon=mat('Nylon natur (JST)', srgb((226, 214, 186)), 0.5, sss=0.15),
    ferrite=mat('Ferrit', (0.06, 0.06, 0.065), 0.6),
    mlcc=mat('MLCC', srgb((150, 120, 85)), 0.5), resblk=mat('SMD-Widerstand', (0.02, 0.02, 0.02), 0.4),
    fr4=mat('FR4-Kante', srgb((190, 175, 120)), 0.6),
    pcb_or=mat('Loetstopp orange', srgb((236, 140, 28)), 0.35, coat=0.6), pcb_gr=mat('Loetstopp gruen', srgb((25, 125, 60)), 0.35, coat=0.6),
    pcb_bl=mat('Loetstopp blau', srgb((20, 60, 170)), 0.35, coat=0.6), pcb_te=mat('Loetstopp tuerkis', srgb((22, 110, 140)), 0.35, coat=0.6),
    pcb_k=mat('Loetstopp schwarz', (0.02, 0.022, 0.03), 0.35, coat=0.6),
    hole=mat('Bohrung', (0.01, 0.01, 0.01), 0.8),
    lcd_frame=mat('TFT-Rahmen', srgb((205, 207, 210)), 0.45, 0.3), lcd_glass=mat('TFT-Glas', (0.008, 0.009, 0.012), 0.06, coat=1.0),
    flex=mat('Flexkabel', srgb((200, 110, 20)), 0.35, coat=0.5), kapton=mat('Kapton', srgb((205, 140, 30)), 0.2, coat=0.8, sss=0.2),
    pouch=node_bump(mat('Akku-Folie', srgb((200, 202, 206)), 0.32, 0.85), 'noise', 0.6, 0.12, 0.05),
    rubber=mat('Gummi schwarz', (0.02, 0.02, 0.02), 0.8), sil=node_bump(mat('Silikonmatte grau', srgb((92, 94, 98)), 0.75, sss=0.1), 'noise', 3.0, 0.2, 0.02),
    potblue=mat('Poti blau', srgb((25, 70, 200)), 0.4), brass=mat('Messing', (0.85, 0.65, 0.30), 0.3, 1.0),
    pot_white=mat('Poti weiss', (0.85, 0.85, 0.82), 0.4),
    elko=mat('Elko-Huelle', (0.02, 0.02, 0.025), 0.3, coat=0.6), elko_str=mat('Elko-Streifen', srgb((150, 152, 160)), 0.35, coat=0.6),
    res_body=mat('Widerstand blau', srgb((95, 150, 210)), 0.4, coat=0.3),
    shrink=mat('Schrumpfschlauch', (0.015, 0.015, 0.017), 0.35, coat=0.3),
    cob_fpc=mat('COB-Traeger weiss', srgb((235, 235, 230)), 0.5), cob_sil=mat('COB-Silikon', srgb((248, 246, 238)), 0.3, sss=0.6),
    led_r=mat('LED rot', (0.9, 0.05, 0.03), 0.2, coat=1.0), led_g=mat('LED gruen', (0.05, 0.8, 0.1), 0.2, coat=1.0),
    led_b=mat('LED blau', (0.05, 0.2, 0.9), 0.2, coat=1.0), led_w=mat('LED 5050', srgb((245, 240, 225)), 0.3, sss=0.4),
    cell_pot=mat('DMS-Verguss', srgb((235, 235, 228)), 0.6, sss=0.3),
    backdrop=mat('Hintergrund', srgb((205, 207, 210)), 0.7),
)
WCOL = dict(r=srgb((200, 20, 15)), k=srgb((22, 22, 24)), y=srgb((240, 195, 0)), g=srgb((20, 150, 55)),
            w=srgb((235, 235, 232)), b=srgb((20, 75, 200)), o=srgb((245, 120, 10)))
def wmat(c): return mat('Litze ' + c, WCOL[c], 0.38, coat=0.25)

# ---------------- Gruppen + Geometrie-Helfer ----------------
GROUPS = {}; GCOLL = {}; G_BASEMAT = {}
CUR_G = [None]
class grp:
    """Baugruppe: Empty mit Ort/Drehung; alle Objekte darin in lokalen Koordinaten."""
    def __init__(self, name, loc=(0, 0, 0), rotz=0.0, coll=None, label=None):
        self.name = name
        c = new_coll(label or name, coll or C_EL)
        e = bpy.data.objects.new('G_' + name, None); e.empty_display_size = 5
        e.location = loc; e.rotation_euler = (0, 0, math.radians(rotz)); c.objects.link(e)
        GROUPS[name] = e; GCOLL[name] = c
        G_BASEMAT[name] = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rotz), 4, 'Z')
        self.e = e; self.c = c
    def __enter__(self): CUR_G[0] = self; return self
    def __exit__(self, *a): CUR_G[0] = None
def wpt(gname, p):   # lokaler Punkt -> Welt (Ruhelage)
    return G_BASEMAT[gname] @ Vector(p)

def link(o, m=None):
    g = CUR_G[0]
    if g: g.c.objects.link(o); o.parent = g.e
    else: CUR[0].objects.link(o)
    if m is not None and o.type in ('MESH', 'CURVE'): o.data.materials.append(m)
    return o

def mesh_from(name, verts, faces, m, smooth=False, uvs=None, mats=None, mi=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if len(faces) > 2:
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free(); me.update()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if uvs is not None:
        uv = me.uv_layers.new()
        for p in me.polygons:
            for li in p.loop_indices:
                uv.data[li].uv = uvs(p, me.vertices[me.loops[li].vertex_index].co)
    o = bpy.data.objects.new(name, me); link(o)
    if mats:
        for mm in mats: me.materials.append(mm)
        if mi:
            for p in me.polygons: p.material_index = mi(p)
    elif m is not None: me.materials.append(m)
    return o

def bevel(o, w=0.2, seg=2, angle=40):
    b = o.modifiers.new('Fase', 'BEVEL'); b.width = w; b.segments = seg
    b.limit_method = 'ANGLE'; b.angle_limit = math.radians(angle)
    for p in o.data.polygons: p.use_smooth = True
    try: o.data.set_sharp_from_angle(angle=math.radians(35))
    except Exception: pass
    return o

BOXF = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
def box(name, x0, y0, z0, w, l, h, m, bev=0.0, seg=2, top=None, bot=None):
    v = [(x0, y0, z0), (x0+w, y0, z0), (x0+w, y0+l, z0), (x0, y0+l, z0),
         (x0, y0, z0+h), (x0+w, y0, z0+h), (x0+w, y0+l, z0+h), (x0, y0+l, z0+h)]
    if top is None and bot is None:
        o = mesh_from(name, v, BOXF, m)
    else:
        def uvf(p, co):
            fx = (co.x-x0)/w; fy = (co.y-y0)/l
            return (fx, fy) if p.normal.z > 0 else (fx, 1-fy)
        def mi(p):
            if p.normal.z > 0.5 and top is not None: return 1
            if p.normal.z < -0.5 and bot is not None: return 2
            return 0
        o = mesh_from(name, v, BOXF, None, uvs=uvf, mats=[m, top or m, bot or m], mi=mi)
    if bev > 0: bevel(o, bev, seg)
    return o
def cbox(name, cx, cy, z0, w, l, h, m, bev=0.0, seg=2, **kw): return box(name, cx-w/2, cy-l/2, z0, w, l, h, m, bev, seg, **kw)

def rrect_pts(x0, y0, w, l, r, n=6):
    pts = []
    for cx, cy, a0 in [(x0+w-r, y0+r, -90), (x0+w-r, y0+l-r, 0), (x0+r, y0+l-r, 90), (x0+r, y0+r, 180)]:
        for i in range(n+1):
            a = math.radians(a0 + 90*i/n); pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return pts

def prism(name, pts, z0, h, m, bev=0.0, top=None, bot=None, uvbox=None, axis='z'):
    """Extrusion eines 2D-Umrisses. axis='z': pts=(x,y); 'y': pts=(x,z) entlang +y; 'x': pts=(y,z) entlang +x"""
    n = len(pts)
    def P(a, b, s):
        if axis == 'z': return (a, b, z0+s)
        if axis == 'y': return (a, z0+s, b)
        return (z0+s, a, b)
    v = [P(a, b, 0) for a, b in pts] + [P(a, b, h) for a, b in pts]
    if axis == 'z' or axis == 'x':
        f = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))] + [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    else:
        f = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))] + [(i, n+i, n+(i+1) % n, (i+1) % n) for i in range(n)]
    if top is None and bot is None:
        o = mesh_from(name, v, f, m)
    else:
        x0, y0, w, l = uvbox
        def uvf(p, co):
            fx = (co.x-x0)/w; fy = (co.y-y0)/l
            return (fx, fy) if p.normal.z > 0 else (fx, 1-fy)
        def mi(p):
            if p.normal.z > 0.5 and top is not None: return 1
            if p.normal.z < -0.5 and bot is not None: return 2
            return 0
        o = mesh_from(name, v, f, None, uvs=uvf, mats=[m, top or m, bot or m], mi=mi)
    if bev > 0: bevel(o, bev, 2)
    return o

def cyl(name, cx, cy, z0, d, h, m, n=32, d2=None, axis='z', bev=0.0, smooth=True):
    d2 = d if d2 is None else d2
    def P(r, a, s):
        c, si = r*math.cos(a), r*math.sin(a)
        if axis == 'z': return (cx + c, cy + si, z0 + s)
        if axis == 'x': return (z0 + s, cx + c, cy + si)      # cx=y, cy=z
        return (cx + c, z0 + s, cy + si)                       # axis y: cx=x, cy=z
    v = [P(d/2, 2*math.pi*i/n, 0) for i in range(n)] + [P(d2/2, 2*math.pi*i/n, h) for i in range(n)]
    f = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))] + [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    if axis == 'y': f = [tuple(reversed(x)) for x in f]
    o = mesh_from(name, v, f, m)
    if smooth:
        for p in o.data.polygons: p.use_smooth = True
        o.data.set_sharp_from_angle(angle=math.radians(40))
    if bev > 0: bevel(o, bev, 2)
    return o

def lathe(name, prof, m, n=48, cx=0, cy=0, z0=0):
    v = []; f = []
    for (r, z) in prof:
        for i in range(n):
            a = 2*math.pi*i/n; v.append((cx + r*math.cos(a), cy + r*math.sin(a), z0+z))
    for j in range(len(prof)-1):
        for i in range(n):
            a = j*n+i; b = j*n+(i+1) % n; f.append((a, b, b+n, a+n))
    if prof[0][0] > 0:
        v.append((cx, cy, z0+prof[0][1])); c = len(v)-1
        for i in range(n): f.append((c, (i+1) % n, i))
    if prof[-1][0] > 0:
        v.append((cx, cy, z0+prof[-1][1])); c = len(v)-1; o_ = (len(prof)-1)*n
        for i in range(n): f.append((c, o_+i, o_+(i+1) % n))
    o = mesh_from(name, v, f, m, smooth=True)
    o.data.set_sharp_from_angle(angle=math.radians(50))
    return o

class Batch:
    """viele kleine Teile (Pads, Loetstellen) in einem Mesh"""
    def __init__(self): self.bm = bmesh.new()
    def cyl(self, c, d, h, n=16, d2=None):
        d2 = d if d2 is None else d2
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=n, radius1=d/2, radius2=d2/2, depth=h,
                              matrix=Matrix.Translation(Vector(c) + Vector((0, 0, h/2))))
    def sph(self, c, r, sz=1.0, n=12):
        bmesh.ops.create_uvsphere(self.bm, u_segments=n, v_segments=max(6, n//2), radius=r,
                                  matrix=Matrix.Translation(Vector(c)) @ Matrix.Diagonal((1, 1, sz, 1)))
    def box(self, x0, y0, z0, w, l, h):
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=Matrix.Translation((x0+w/2, y0+l/2, z0+h/2)) @ Matrix.Diagonal((w, l, h, 1)))
    def make(self, name, m, smooth=True):
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        if smooth:
            for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new(name, me); link(o, m); return o

def apply_mods(o):
    dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(eo); old = o.data
    o.modifiers.clear(); o.data = me
    return o
def bool_cut(o, cutters, solver='EXACT'):
    for c in cutters:
        md = o.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = c; md.solver = solver
    apply_mods(o)
    for c in cutters: bpy.data.objects.remove(c, do_unlink=True)
    return o

def tube(name, pts, m, r=0.3, res=3, k=8, caps=True):
    cd = bpy.data.curves.new(name, 'CURVE'); cd.dimensions = '3D'
    cd.bevel_depth = r; cd.bevel_resolution = res; cd.use_fill_caps = caps
    P = catmull(pts, k) if len(pts) > 2 else [Vector(p) for p in pts]
    sp = cd.splines.new('POLY'); sp.points.add(len(P)-1)
    for i, p in enumerate(P): sp.points[i].co = (p.x, p.y, p.z, 1)
    o = bpy.data.objects.new(name, cd); link(o, m); return o

def catmull(pts, k=10):
    P = [Vector(p) for p in pts]; P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P)-2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        # zentripetale Catmull-Rom (keine Ueberschwinger)
        def tj(ti, a, b): return ti + max((b-a).length, 1e-4)**0.5
        t0 = 0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        for s in range(k):
            t = t1 + (t2-t1)*s/k
            A1 = (t1-t)/(t1-t0)*p0 + (t-t0)/(t1-t0)*p1 if t1 > t0 else p1
            A2 = (t2-t)/(t2-t1)*p1 + (t-t1)/(t2-t1)*p2
            A3 = (t3-t)/(t3-t2)*p2 + (t-t2)/(t3-t2)*p3 if t3 > t2 else p2
            B1 = (t2-t)/(t2-t0)*A1 + (t-t0)/(t2-t0)*A2
            B2 = (t3-t)/(t3-t1)*A2 + (t-t1)/(t3-t1)*A3
            out.append((t2-t)/(t2-t1)*B1 + (t-t1)/(t2-t1)*B2)
    out.append(P[-2]); return out

def import_stl(name, fn, m):
    bpy.ops.wm.stl_import(filepath=STL + fn)
    o = bpy.context.selected_objects[0]; o.name = name
    for c in o.users_collection: c.objects.unlink(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    o.data.set_sharp_from_angle(angle=math.radians(30))
    o.data.materials.clear(); link(o, m); return o

# =====================================================================
#  BAUTEILE
# =====================================================================
def smd_ic(name, u, v, du, dv, h, pins_on='u', n=4, pitch=1.27, lead=0.6, down=True, body_m=None, lw=0.4):
    """IC mit Gullwing-Beinen. pins_on='u': Beine an den Seiten u0/u0+du (Reihen entlang v)."""
    s = -1 if down else 1; z0 = 0.0
    bm_ = body_m or M['epoxy']
    if pins_on == 'u': bu, bv, bw, bl = u+lead, v, du-2*lead, dv
    else: bu, bv, bw, bl = u, v+lead, du, dv-2*lead
    zb = -h if down else 0.12
    o = [box(name, bu, bv, zb, bw, bl, h-0.12, bm_, 0.08, 1)]
    B = Batch()
    for i in range(n):
        if pins_on == 'u':
            c = bv + bl/2 + (i-(n-1)/2)*pitch
            for x0 in (u, u+du-lead):
                B.box(x0, c-lw/2, -0.25 if down else 0, lead, lw, 0.25)
        else:
            c = bu + bw/2 + (i-(n-1)/2)*pitch
            for y0 in (v, v+dv-lead):
                B.box(c-lw/2, y0, -0.25 if down else 0, lw, lead, 0.25)
    o.append(B.make(name+' Beine', M['tin'], False))
    # Pin-1-Markierung
    o.append(cyl(name+' P1', bu+0.6, bv+0.6, (zb-0.01) if down else (zb+h-0.12), 0.5, 0.012, M['black'], 12))
    return o

def passive(name, u, v, rot, kind, down=True, L_=1.6, W_=0.8, H_=0.45):
    if rot: du, dv = W_, L_
    else: du, dv = L_, W_
    z = -H_ if down else 0
    body = M['mlcc'] if kind == 'c' else M['resblk']
    o = [cbox(name, u, v, z, du, dv, H_, body, 0.05, 1)]
    e = 0.32
    if rot:
        o.append(cbox(name+'e1', u, v-dv/2+e/2, z-0.01, du+0.02, e, H_+0.02, M['tin']))
        o.append(cbox(name+'e2', u, v+dv/2-e/2, z-0.01, du+0.02, e, H_+0.02, M['tin']))
    else:
        o.append(cbox(name+'e1', u-du/2+e/2, v, z-0.01, e, dv+0.02, H_+0.02, M['tin']))
        o.append(cbox(name+'e2', u+du/2-e/2, v, z-0.01, e, dv+0.02, H_+0.02, M['tin']))
    return o

def picoblade(name, u, v, du, dv, h, face):
    """Molex PicoBlade 1,25 mm, liegend (SMD). face = Steckseite '+u', '+v', '-u'."""
    o = [box(name, u, v, -h, du, dv, h-0.05, M['nylon'], 0.12, 1)]
    inset = 0.25; dk = 0.6
    if face == '+u':
        o.append(box(name+' Oeffnung', u+du-1.4, v+0.45, -h+0.45, 1.42, dv-0.9, h-1.1, M['black']))
        n = int(round((dv-2.5)/1.25)) + 1
        for i in range(n):
            o.append(box(name+' Kontakt', u+du-1.3, v+1.25+i*1.25-0.2, -h+0.9, 1.0, 0.4, 0.5, M['tin']))
        o.append(box(name+' Lasche1', u+0.5, v-0.7, -0.2, 2.2, 0.8, 0.2, M['tin'])); o.append(box(name+' Lasche2', u+0.5, v+dv-0.1, -0.2, 2.2, 0.8, 0.2, M['tin']))
    elif face == '+v':
        o.append(box(name+' Oeffnung', u+0.45, v+dv-1.4, -h+0.45, du-0.9, 1.42, h-1.1, M['black']))
        n = int(round((du-2.5)/1.25)) + 1
        for i in range(n):
            o.append(box(name+' Kontakt', u+1.25+i*1.25-0.2, v+dv-1.3, -h+0.9, 0.4, 1.0, 0.5, M['tin']))
        o.append(box(name+' Lasche1', u-0.7, v+0.5, -0.2, 0.8, 2.2, 0.2, M['tin'])); o.append(box(name+' Lasche2', u+du-0.1, v+0.5, -0.2, 0.8, 2.2, 0.2, M['tin']))
    else:
        o.append(box(name+' Oeffnung', u-0.02, v+0.45, -h+0.45, 1.42, dv-0.9, h-1.1, M['black']))
    return o

def cyd_plug(name, u_edge, vc, npins, colors, gname):
    """PicoBlade-Stecker (4-pol.) im CYD-Anschluss; Kabel gehen nach +u heraus. Liefert Welt-Austrittspunkte."""
    w = (npins-1)*1.25 + 3.0
    o = [box(name, u_edge-1.2, vc-w/2, -3.4, 5.6, w, 3.0, M['nylon'], 0.15, 1)]
    o.append(box(name+' Rastnase', u_edge+0.8, vc-w/2+0.6, -3.55, 2.2, w-1.2, 0.2, M['nylon'], 0.05, 1))
    ex = []
    for i in range(npins):
        vv = vc + (i-(npins-1)/2)*1.25
        ex.append((u_edge+4.3, vv, -1.9))
    return o, ex

def make_cyd():
    with grp('cyd', (cyd_x, cyd_y, cyd_pcb_z), 0, C_EL, 'CYD ESP32-2432S028R') as g:
        # Platine 86 x 50 x 1,5 mit 4 Bohrungen 3,2
        pts = rrect_pts(0, 0, L.PCB_W, L.PCB_L, L.PCB_R)
        pcb = prism('CYD Platine', pts, 0, cyd_t, M['fr4'], top=tex_mat('CYD Vorderseite', 'cyd_front.png', 0.35, 0.6),
                    bot=tex_mat('CYD Rueckseite', 'cyd_back.png', 0.35, 0.6), uvbox=(0, 0, L.PCB_W, L.PCB_L))
        cut = [cyl('c', u, v, -1, 3.2, cyd_t+2, M['hole'], 24, smooth=False) for (u, v) in cyd_holes_uv]
        bool_cut(pcb, cut)
        for p in pcb.data.polygons: p.use_smooth = False
        # TFT 2,8" (ILI9341) 50 x 69,2, Glasoberkante = lcd_top_z (23,5)
        lv0 = 43 - 0.7 - 34.6
        box('TFT Rahmen', 0.1, lv0, cyd_t, 49.8, 69.2, 2.4, M['lcd_frame'], 0.3)
        box('TFT Glas', 0.25, lv0+0.15, cyd_t+2.4, 49.5, 68.9, 1.18, M['lcd_glass'], 0.25)
        scr = tex_mat('Display Inhalt', 'screen_ui.png', 0.08, 1.0, emis=1.4)
        box('TFT aktive Flaeche', 25-21.6, 39.5-28.8, cyd_t+3.58, 43.2, 57.6, 0.02, M['lcd_glass'], top=scr)
        box('TFT Flex', 14, lv0-3.0, cyd_t, 22, 3.2, 0.12, M['flex'])
        # Rueckseite
        for (nm, typ, u, v, du, dv, h) in L.PARTS:
            if typ == 'esp':
                box('ESP32 Modulplatine', u, v+7.2, -0.85, du, dv-7.2, 0.8, M['pcb_k'], 0.05, 1)
                box('ESP32 Antenne', u, v, -0.85, du, 7.2, 0.8, M['pcb_k'], 0.05, 1, bot=tex_mat('ESP32 Antenne', 'esp_antenna.png', 0.35, 0.5))
                box('ESP32 Schirmblech', u+1.0, v+7.6, -h, 16.0, 17.4, h-0.85, M['nickel'], 0.15, 1, bot=tex_mat('ESP32 Schirm', 'esp_shield.png', 0.25, 0.0, metal=0.85))
                B = Batch()
                for i in range(14):
                    vv = v + 8.5 + i*1.27
                    B.box(u-0.05, vv-0.45, -0.9, 0.5, 0.9, 0.9); B.box(u+du-0.45, vv-0.45, -0.9, 0.5, 0.9, 0.9)
                for i in range(10):
                    uu = u + du/2 + (i-4.5)*1.27; B.box(uu-0.45, v+dv-0.45, -0.9, 0.9, 0.5, 0.9)
                B.make('ESP32 Loetpads', M['tin'], False)
            elif typ == 'tact':
                box(nm+' Sockel', u+0.8, v, -1.4, du-1.6, dv, 1.35, M['black'], 0.1, 1)
                box(nm+' Blech', u+0.9, v+0.1, -1.7, du-1.8, dv-0.2, 0.3, M['steel'], 0.05, 1)
                cyl(nm+' Taster', u+du/2, v+dv/2, -h, 1.6, h-1.7, M['black'], 20)
                for x0 in (u, u+du-0.9): box(nm+' Bein', x0, v+dv/2-0.5, -0.3, 0.9, 1.0, 0.3, M['tin'])
            elif typ in ('tssop16', 'sop8', 'soic16'):
                n = {'tssop16': 8, 'sop8': 4, 'soic16': 8}[typ]; pitch = 0.65 if typ == 'tssop16' else 1.27
                on = 'v' if du > dv else 'u'
                smd_ic(nm, u, v, du, dv, h, on, n, pitch, lw=0.3 if typ == 'tssop16' else 0.4)
            elif typ == 'sot223':
                box(nm, u, v+0.9, -h, du, dv-1.8, h-0.1, M['epoxy'], 0.08, 1)
                box(nm+' Kuehlfahne', u+du/2-1.5, v, -0.25, 3.0, 1.2, 0.25, M['tin'])
                for i in range(3): box(nm+' Bein', u+du/2+(i-1)*2.3-0.35, v+dv-1.1, -0.25, 0.7, 1.1, 0.25, M['tin'])
            elif typ == 'sot23':
                box(nm, u+(0.25 if du < dv else 0), v+(0.25 if dv < du else 0), -h, du-(0.5 if du < dv else 0), dv-(0.5 if dv < du else 0), h-0.05, M['epoxy'], 0.05, 1)
            elif typ == 'led5050':
                box(nm, u, v, -h, du, dv, h-0.02, M['led_w'], 0.1, 1)
                cyl(nm+' Linse', u+du/2, v+dv/2, -h-0.01, 3.6, 0.05, mat('LED-Linse', srgb((250, 240, 200)), 0.15, coat=1, sss=0.5), 24)
            elif typ == 'sd':
                box('microSD Schirm', u, v, -h, du, dv, h-0.05, M['steel'], 0.1, 1)
                box('microSD Schlitz', u+du-0.6, v+1.2, -h+0.35, 0.62, 11.2, 0.95, M['black'])
                for i in range(3): box('microSD Sicke', u+2+i*4, v+1.5, -h-0.04, 2.6, dv-3, 0.05, M['steel'])
                B = Batch()
                for i in range(8):
                    vv = L.SD_PIN1_V + i*L.SD_PITCH; B.box(L.SD_TAIL_U-0.7, vv-0.28, -0.18, 1.4, 0.56, 0.18)
                B.make('microSD Kontaktfahnen', M['gold'], False)
                for vv in (v-0.6, v+dv-0.2): box('microSD Lasche', u+3, vv, -0.25, 3, 0.8, 0.25, M['tin'])
            elif typ == 'usbc':
                pr = rrect_pts(u, -h, du, h-0.05, 1.3, 6)
                prism('USB-C Buchse', pr, v, dv, M['nickel'], axis='y')
                prism('USB-C Innen', rrect_pts(u+0.5, -h+0.5, du-1.0, h-1.05, 0.9, 6), v+dv-1.2, 1.22, M['black'], axis='y')
                box('USB-C Zunge', u+1.7, v+dv-3.5, -h/2-0.35, du-3.4, 3.4, 0.7, M['black'])
            elif typ == 'microusb':
                pr = [(u, -0.05), (u+du, -0.05), (u+du, -h+1.0), (u+du-1.0, -h), (u+1.0, -h), (u, -h+1.0)]
                prism('Micro-USB Buchse', pr, v, dv, M['nickel'], axis='y')
                prism('Micro-USB Innen', [(u+0.5, -0.5), (u+du-0.5, -0.5), (u+du-0.5, -h+1.2), (u+du-1.3, -h+0.5), (u+1.3, -h+0.5), (u+0.5, -h+1.2)], v+dv-1.0, 1.02, M['black'], axis='y')
            elif typ == 'jst4h': picoblade(nm, u, v, du, dv, h, '+v')
            elif typ == 'jst4v': picoblade(nm, u, v, du, dv, h, '+u')
            elif typ == 'jst2': picoblade(nm, u, v, du, dv, h, '-u')
        for i, (u, v, q) in enumerate(L.PASSIVES):
            passive('SMD %d' % i, u, v, q, 'r' if i % 3 == 0 else 'c')
        # Stecker in P3 und CN1 (mitgelieferte 4-pol. Kabel)
        p3 = [p for p in L.PARTS if p[0].startswith('P3')][0]; cn = [p for p in L.PARTS if p[0].startswith('CN1')][0]
        _, ex_p3 = cyd_plug('Stecker P3', p3[2]+p3[4], p3[3]+p3[5]/2, 4, 'kbyr', 'cyd')
        _, ex_cn = cyd_plug('Stecker CN1', cn[2]+cn[4], cn[3]+cn[5]/2, 4, 'kbyr', 'cyd')
    A['p3'] = [wpt('cyd', p) for p in ex_p3]; A['cn1'] = [wpt('cyd', p) for p in ex_cn]
    sd = [wpt('cyd', (L.SD_TAIL_U-0.3, L.SD_PIN1_V + i*L.SD_PITCH, -0.12)) for i in range(8)]
    A['sd3'], A['sd5'], A['sd7'] = sd[2], sd[4], sd[6]
    A['S3'] = wpt('cyd', (*L.TESTPADS['S3'], -0.1)); A['S1'] = wpt('cyd', (*L.TESTPADS['S1'], -0.1))
A = {}

def make_battery():
    # EEMB LP103454: 34,5 x 56 x 10,3 mm, Schutzplatine (PCM) vorne unter Kapton, Kabel AWG24 nach vorne
    with grp('bat', (12.15, 41.0, 2.0), 0, C_EL, 'Akku EEMB LP103454'):
        box('Akku Zelle', 0, 4.5, 0, 34.5, 51.5, 10.3, M['pouch'], 1.6, 4)
        box('Akku Siegelnaht', 0.6, 52.0, 4.6, 33.3, 4.0, 1.0, M['pouch'], 0.3, 2)
        box('Akku PCM-Falz', 0.8, 0.6, 1.2, 32.9, 4.4, 7.8, M['pouch'], 0.8, 3)
        box('Akku Kapton', 0.5, 0.3, 0.9, 33.5, 4.6, 8.4, M['kapton'], 0.9, 3)
        box('Akku Etikett', 0.6, 8.5, 10.28, 33.3, 46.0, 0.05, M['pouch'], top=tex_mat('Akku Etikett', 'lipo_label.png', 0.45, 0.2))
    A['bat-'] = wpt('bat', (30.4, 1.2, 5.4)); A['bat+'] = wpt('bat', (32.4, 1.2, 5.4))

def make_pololu():
    # Pololu S13V10F5: 8,9 x 12,1 mm, Hoehe oben 1,8 / unten 1,4, Loecher 1,02 im 2,54-Raster (VOUT, GND, VIN)
    with grp('pol', (33.85, 33.55, 3.4), 180, C_EL, 'Pololu S13V10F5'):
        t = 1.0
        box('Pololu Platine', 0, 0, 0, 8.9, 12.1, t, M['fr4'], top=tex_mat('Pololu Oben', 'pololu.png', 0.35, 0.6), bot=M['pcb_gr'])
        B = Batch(); Bh = Batch()
        for i in range(3):
            a = 1.91 + i*2.54; B.cyl((a, 1.27, -0.02), 1.8, t+0.04, 20); Bh.cyl((a, 1.27, -0.05), 1.02, t+0.1, 16)
        B.cyl((0.8, 11.3, -0.02), 0.9, t+0.04, 12)
        B.make('Pololu Pads', M['gold'], False); Bh.make('Pololu Loecher', M['hole'], False)
        oc = [(4.45 + 2.0*math.cos(math.radians(22.5+45*i)), 6.6 + 2.0*math.sin(math.radians(22.5+45*i))) for i in range(8)]
        prism('Pololu Spule', oc, t, 1.75, M['ferrite'], 0.15)
        passive('Pololu C1', 1.6, 9.8, 1, 'c', down=False, L_=2.0, W_=1.25, H_=1.2)
        passive('Pololu C2', 7.3, 9.8, 1, 'c', down=False, L_=2.0, W_=1.25, H_=1.2)
        passive('Pololu R1', 1.5, 4.2, 1, 'r', down=False)
        # Unterseite: Regler-IC + Kondensatoren (1,4 mm)
        box('Pololu IC', 2.6, 5.0, -1.0, 3.0, 3.0, 1.0, M['epoxy'], 0.08)
        passive('Pololu C3', 7.0, 7.5, 1, 'c', down=True, L_=2.0, W_=1.25, H_=1.35)
        passive('Pololu C4', 1.4, 8.0, 1, 'c', down=True, L_=2.0, W_=1.25, H_=1.35)
    for i, k in enumerate(('pol_vout', 'pol_gnd', 'pol_vin')):
        A[k] = wpt('pol', (1.91 + i*2.54, 1.27, 1.0))

def make_tc():
    # TC4056 mit Schutz (DW01 + FS8205), USB-C; 17 x 26 mm (+ USB-Ueberstand = 27 mm laut Haendler)
    with grp('tc', (56.0, 71.6, 3.5), 0, C_EL, 'Lader TC4056 USB-C'):
        t = 1.0
        def Y(b): return 26 - b
        box('TC4056 Platine', 0, 0, 0, 17, 26, t, M['fr4'], top=tex_mat('TC4056 Oben', 'tc4056.png', 0.35, 0.6), bot=M['pcb_te'])
        # USB-C (Mid-Mount auf der Oberseite), ragt 0,6 mm ueber
        u0 = 8.5 - 4.47; b0, b1 = -0.6, 6.75
        prism('TC USB-C', rrect_pts(u0, t, 8.94, 3.26, 1.3, 6), Y(b1), b1-b0, M['nickel'], axis='y')
        prism('TC USB-C Innen', rrect_pts(u0+0.5, t+0.5, 7.94, 2.26, 0.9, 6), Y(b0)-1.2, 1.22, M['black'], axis='y')
        box('TC USB-C Zunge', u0+1.7, Y(b0)-3.6, t+1.28, 8.94-3.4, 3.4, 0.7, M['black'])
        for x in (u0-0.6, u0+8.94): box('TC USB-C Lasche', x, Y(4.5), t, 0.6, 1.6, 1.4, M['nickel'])
        L1 = smd_ic('TC4056A', 8.5-3.0, Y(12.0)-2.45, 6.0, 4.9, 1.5, 'u', 4, 1.27, down=False)
        smd_ic('FS8205A', 5.4-2.2, Y(19.8)-1.5-0.8, 4.4, 4.6, 1.1, 'v', 4, 0.65, lead=0.8, down=False, lw=0.3)
        smd_ic('DW01', 11.8-1.45, Y(19.8)-1.5-0.8, 2.9, 4.6, 1.1, 'v', 3, 0.95, lead=0.8, down=False, lw=0.35)
        box('LED rot', 15.6, Y(7.4)-0.8, t, 0.8, 1.6, 0.55, M['led_r'], 0.05)
        box('LED blau', 15.6, Y(12.7)-0.8, t, 0.8, 1.6, 0.55, M['led_b'], 0.05)
        for i, (a, b, q) in enumerate([(12.3, 11.8, 1), (12.0, 7.6, 0), (3.2, 9.0, 0), (3.6, 6.8, 0), (7.0, 6.8, 0), (3.2, 11.0, 0),
                                       (9.8, 15.6, 0), (4.6, 15.0, 0), (11.0, 15.2, 0), (14.4, 14.6, 1), (15.6, 4.2, 0)]):
            passive('TC SMD %d' % i, a, Y(b), q, 'c' if i % 2 else 'r', down=False)
        B = Batch(); Bh = Batch()
        for (a, b) in [(1.6, 2.2), (15.4, 2.2), (1.6, 23.6), (5.5, 23.6), (11.5, 23.6), (15.4, 23.6)]:
            B.cyl((a, Y(b), -0.03), 2.2, t+0.06, 20); Bh.cyl((a, Y(b), -0.06), 0.9, t+0.12, 14)
        B.make('TC Pads', M['tin'], False); Bh.make('TC Loecher', M['hole'], False)
    for k, a in (('tc_out-', 1.6), ('tc_b-', 5.5), ('tc_b+', 11.5), ('tc_out+', 15.4)):
        A[k] = wpt('tc', (a, 26-23.6, 1.0))

# ---------------- FET-Platine (Layout loeten_5b, siehe HydroDesk/loeten/fet3d) ----------------
ROWS = "ABCDEFGHIJ"; PI = 2.54
def hp(h):
    c = int(h[1:]); r = ROWS.index(h[0]); return ((c-1)*PI, -(r-1)*PI)
FET_PADS = {1: "G04", 2: "J02", 3: "F01", 4: "J01", 5: "H01", 6: "F09", 7: "F06", 8: "F10", 9: "I01", 10: "F05"}
BAND = {0: (10, 10, 10), 1: (120, 60, 20), 2: (220, 0, 0), 3: (255, 120, 0), 4: (255, 210, 0), 5: (0, 150, 0), 6: (0, 0, 220), 7: (130, 40, 190)}
def make_fet():
    BR = [["E04", "F04", "G04", "H04"], ["E02", "F02", "F03", "G03"], ["G02", "H02", "H03"], ["G01", "H01"],
          ["I01", "I02", "I03", "J03", "J04"], ["J01", "J02", "J03"], ["E07", "F07", "F06"], ["E09", "F09", "F08"], ["F09", "F10"]]
    JU = [('r', "B03", "F01"), ('y', "B08", "F05")]
    RES = [("R1 10k", (1, 0, 3), "F03", "F04"), ("R2 4k7", (4, 7, 2), "G01", "G02"), ("R3 47k", (4, 7, 3), "I02", "H02"), ("R4 47k", (4, 7, 3), "F08", "F07")]
    with grp('fet', (50.69, 42.97, 5.1), 90, C_EL, 'FET-Platine (Lochraster)'):
        T = 1.6; x0b, x1b = -3.57, 26.43; y0b, y1b = -22.41, 2.09
        box('Lochraster', x0b, y0b, -T, x1b-x0b, y1b-y0b, T, M['pcb_gr'], 0.1, 1)
        Bp = Batch(); Bh = Batch()
        for r in "BCDEFGHIJ":
            for c in range(1, 11):
                x, y = hp("%s%02d" % (r, c))
                Bp.cyl((x, y, -0.005), 1.8, 0.04, 16); Bp.cyl((x, y, -T-0.035), 1.8, 0.04, 16)
                Bh.cyl((x, y, 0.036), 0.95, 0.002, 12); Bh.cyl((x, y, -T-0.038), 0.95, 0.002, 12)
        Bp.make('Lochraster Pads', M['tin'], False); Bh.make('Lochraster Loecher', M['hole'], False)
        legs = set(); Bl = Batch()
        # SOT-23-Adapter (gruen) mit AO3401A auf 2 Stiftleisten
        ZA = 2.5
        for name, c0 in (("Q1", 1), ("Q2", 6)):
            xa, _ = hp("B%02d" % c0); xb, _ = hp("B%02d" % (c0+4)); cx = (xa+xb)/2
            yB = hp("B01")[1]; yE = hp("E01")[1]; cy = (yB+yE)/2
            cbox(name+' Adapter', cx, cy, ZA, 12.7, 10.2, 1.6, M['pcb_gr'], 0.08, 1, top=tex_mat('SOT23-Adapter', 'sot23_adapter.png', 0.35, 0.6))
            for yy in (yB, yE):
                cbox(name+' Stiftleiste', cx, yy, 0, 12.7, 2.5, ZA, M['black'], 0.1, 1)
                for c in range(c0, c0+5):
                    x, _ = hp("B%02d" % c)
                    Bl.box(x-0.32, yy-0.32, -T-1.2, 0.64, 0.64, ZA+1.6+1.0+T+1.2)
                    Bl.sph((x, yy, ZA+1.6), 0.6, 0.5)
                    legs.add("%s%02d" % ("B" if yy == yB else "E", c))
            zc = ZA+1.6
            cbox(name+' AO3401A', cx, cy, zc+0.1, 2.9, 1.3, 1.0, M['epoxy'], 0.05, 1)
            for dx, s in ((-0.95, -1), (0.95, -1), (0, 1)):
                cbox(name+' Bein', cx+dx, cy+s*1.0, zc, 0.4, 0.8, 0.15, M['tin'])
        # Widerstaende MSW 0207 stehend (4 Ringe, 1 % braun)
        for ref, bands, hb, hl in RES:
            xb_, yb_ = hp(hb); xl, yl = hp(hl); z0, Lr = 1.0, 6.3
            cyl(ref, xb_, yb_, z0+0.5, 2.3, Lr-1.0, M['res_body'], 24)
            lathe(ref+' Kappe1', [(0, z0), (0.9, z0+0.05), (1.25, z0+0.4), (1.25, z0+0.9), (0, z0+0.9)], M['res_body'], 24, xb_, yb_)
            lathe(ref+' Kappe2', [(0, z0+Lr-0.9), (1.25, z0+Lr-0.9), (1.25, z0+Lr-0.4), (0.9, z0+Lr-0.05), (0, z0+Lr)], M['res_body'], 24, xb_, yb_)
            cols = [BAND[bands[0]], BAND[bands[1]], BAND[bands[2]], BAND[1]]
            for k, (zb, cc) in enumerate(zip([z0+Lr-1.3, z0+Lr-2.1, z0+Lr-2.9, z0+1.2], cols)):
                cyl(ref+' Ring', xb_, yb_, zb, 2.36 if k else 2.6, 0.5, mat('Ring %s' % str(cc), srgb(cc), 0.45, coat=0.3), 24)
            tube(ref+' Bein1', [(xb_, yb_, -T-1.0), (xb_, yb_, z0+0.5)], M['tin'], 0.25)
            tube(ref+' Bein2', [(xb_, yb_, z0+Lr-0.4), (xb_, yb_, z0+Lr+1.0), ((xb_+xl)/2, (yb_+yl)/2, z0+Lr+1.7), (xl, yl, z0+Lr+0.8), (xl, yl, 2.0), (xl, yl, -T-1.0)], M['tin'], 0.25)
            legs.add(hb); legs.add(hl)
        # BC547B (TO-92)
        xs, ys = hp("G03"); _, ye = hp("I03"); ym = (ys+ye)/2; zt0, zt1 = 3.0, 7.6; xf = xs-1.6
        pts = [(xf + 3.7*math.cos(-math.pi/2 + math.pi*i/24), ym + 2.3*math.sin(-math.pi/2 + math.pi*i/24)) for i in range(25)]
        prism('T1 BC547B', [(xf, ym-2.3)] + pts + [(xf, ym+2.3)], zt0, zt1-zt0, M['epoxy'], 0.15)
        box('T1 Aufdruck', xf-0.02, ym-1.4, zt0+1.5, 0.03, 2.8, 1.4, mat('Aufdruck grau', (0.4, 0.4, 0.4), 0.5))
        for h in ["G03", "H03", "I03"]:
            x, y = hp(h); tube('T1 Bein', [(x, y, -T-1.0), (x, y, 0.5), (x+0.3, y, zt0+0.2)], M['tin'], 0.22); legs.add(h)
        # Elko 470 uF / 25 V, liegend (10 x 16), schwarz mit grauem Streifen
        yI = hp("I01")[1]; xe0, xe1 = 3.6*PI, 3.6*PI+16.0; ze = 5.0
        cyl('Elko 470uF', yI, ze, xe0+0.6, 10.0, 16.0-1.6, M['elko'], 48, axis='x')
        cyl('Elko Boden', yI, ze, xe0, 9.4, 0.62, M['rubber'], 48, axis='x')
        cyl('Elko Deckel', yI, ze, xe1-1.0, 9.6, 0.9, M['alu'], 48, axis='x')
        cyl('Elko Sicke', yI, ze, xe0+1.4, 9.7, 0.5, M['elko'], 48, axis='x')
        nn = 16; v = []; f = []
        for i in range(nn+1):
            a = math.radians(-150 + 60*i/nn)
            for x in (xe0+2.0, xe1-1.0): v.append((x, yI + 5.03*math.sin(a), ze + 5.03*math.cos(a)))
        for i in range(nn): f.append((2*i, 2*i+1, 2*i+3, 2*i+2))
        mesh_from('Elko Streifen', v, f, M['elko_str'], True)
        for h, dy in (("H04", 2.54), ("J04", -2.54)):
            x, y = hp(h)
            tube('Elko Bein', [(xe0, yI+dy*0.98, ze), (xe0-1.0, y, ze), (x, y, ze-2.0), (x, y, 0.5), (x, y, -T-1.0)], M['tin'], 0.25); legs.add(h)
        for nr, h in FET_PADS.items(): legs.add(h)
        for h in legs:
            x, y = hp(h); Bl.sph((x, y, -T-0.06), 0.95, 0.55)
        Bl.make('Loetstellen unten', M['tin'])
        for ch in BR:
            for a, b in zip(ch, ch[1:]):
                (xa, ya), (xb, yb) = hp(a), hp(b)
                tube('Bruecke', [(xa, ya, -T-0.3), (xb, yb, -T-0.3)], M['tin'], 0.4, caps=True)
        for c, ha, hb in JU:
            (xa, ya), (xb, yb) = hp(ha), hp(hb); mx, my = (xa+xb)/2 - 2.0, (ya+yb)/2
            tube('Drahtbruecke', [(xa, ya, -T-0.4), (xa, ya, -T-0.7), (mx, my, -T-0.85), (xb, yb, -T-0.7), (xb, yb, -T-0.4)], wmat(c), 0.38)
    for nr, h in FET_PADS.items():
        x, y = hp(h); A['fet%d' % nr] = wpt('fet', (x, y, 0.0))
    # Klebeband-Leisten unter der Platine liegen auf den Gehaeuseleisten (z = 3,5)

def header_angled(name, x0, y0, z0, n, out_dir=-1, pin_len=6.0):
    """abgewinkelte Stiftleiste (2,54 mm), Reihe entlang x, Stifte zeigen nach out_dir (y)."""
    o = [box(name+' Kunststoff', x0-1.27, y0-1.27 if out_dir < 0 else y0-1.23, z0, n*2.54, 2.5, 2.5, M['black'], 0.12, 1)]
    for i in range(n):
        x = x0 + i*2.54
        tube(name+' Stift', [(x, y0, z0-1.5), (x, y0, z0+1.27), (x, y0+out_dir*0.4, z0+1.27+0.0), (x, y0+out_dir*(pin_len+1.27), z0+1.27)], M['gold'], 0.32, 2, 4)
    return o

def make_cmp():
    # LM393-Auswertemodul 16 x 30 (blau), Kabel direkt angeloetet (Hoehe < 12 mm)
    with grp('cmp', (56.0, 7.6, 2.0), 0, C_EL, 'Regensensor-Modul LM393'):
        t = 1.6
        def Y(b): return 30 - b
        box('LM393 Platine', 0, 0, 0, 16, 30, t, M['fr4'], top=tex_mat('LM393 Oben', 'lm393.png', 0.35, 0.6), bot=M['pcb_bl'])
        smd_ic('LM393', 8-3.0, Y(17.5)-2.45, 6.0, 4.9, 1.5, 'u', 4, 1.27, down=False)
        box('Poti Gehaeuse', 8-3.3, Y(10.0)-3.3, t, 6.6, 6.6, 4.0, M['potblue'], 0.3)
        cyl('Poti Rotor', 8, Y(10.0), t+4.0, 3.4, 0.5, M['pot_white'], 24)
        box('Poti Schlitz1', 8-1.5, Y(10.0)-0.25, t+4.45, 3.0, 0.5, 0.08, M['black']); box('Poti Schlitz2', 8-0.25, Y(10.0)-1.5, t+4.45, 0.5, 3.0, 0.08, M['black'])
        box('LED Power', 2.6, Y(21.0)-0.8, t, 0.8, 1.6, 0.5, M['led_r'], 0.05); box('LED DO', 12.6, Y(21.0)-0.8, t, 0.8, 1.6, 0.5, M['led_g'], 0.05)
        for i, (a, b, q) in enumerate([(3.5, 14.0, 1), (12.5, 14.0, 1), (4.0, 24.0, 0), (12.0, 24.0, 0), (8.0, 23.5, 0), (8.0, 6.5, 0)]):
            passive('LM393 SMD %d' % i, a, Y(b), q, 'r' if i % 2 else 'c', down=False)
        B = Batch(); Bh = Batch()
        for i in range(4): B.box(4.19+i*2.54-0.85, Y(28.0)-0.85, -0.02, 1.7, 1.7, t+0.04); Bh.cyl((4.19+i*2.54, Y(28.0), -0.05), 1.0, t+0.1, 12)
        for i in range(2): B.box(6.73+i*2.54-0.85, Y(2.4)-0.85, -0.02, 1.7, 1.7, t+0.04); Bh.cyl((6.73+i*2.54, Y(2.4), -0.05), 1.0, t+0.1, 12)
        B.make('LM393 Pads', M['tin'], False); Bh.make('LM393 Loecher', M['hole'], False)
    for i, k in enumerate(('cmp_vcc', 'cmp_gnd', 'cmp_do', 'cmp_ao')):
        A[k] = wpt('cmp', (4.19+i*2.54, 30-28.0, 1.6))
    A['cmp_s1'] = wpt('cmp', (6.73, 30-2.4, 1.6)); A['cmp_s2'] = wpt('cmp', (9.27, 30-2.4, 1.6))

def make_rs():
    # Regenplatte MH-RD / FC-37: 40 x 54 x 1,6, abgewinkelte 2er-Stiftleiste vorne
    with grp('rs', (115.5, 74.0, 1.2), 180, C_EL, 'Regenplatte FC-37'):
        t = 1.6
        box('Regenplatte', 0, 0, 0, 40, 54, t, M['fr4'], top=tex_mat('Regenplatte Oben', 'rain_plate.png', 0.25, 0.7, metal=0.0), bot=M['pcb_k'])
        header_angled('Regen Stiftleiste', 18.73, 51.5, t, 2, out_dir=+1, pin_len=5.0)
    # Stiftspitzen (Welt): Stifte zeigen nach vorne (-Y)
    A['rs_1'] = wpt('rs', (18.73, 51.5+6.0, 1.6+1.27)); A['rs_2'] = wpt('rs', (21.27, 51.5+6.0, 1.6+1.27))

def make_hx():
    # HX711-Modul (DIYmalls, gruen) ca. 34 x 20; Wagezelle an J1, Kabel zum CYD an GND/DT/SCK/VCC
    with grp('hx', (170.0, 80.0, 2.0), 180, C_EL, 'HX711-Modul'):
        t = 1.6
        def Y(b): return 20 - b
        box('HX711 Platine', 0, 0, 0, 34, 20, t, M['fr4'], top=tex_mat('HX711 Oben', 'hx711.png', 0.35, 0.6), bot=M['pcb_gr'])
        smd_ic('HX711', 15.9-5.0, Y(7.6)-3.0, 10.0, 6.0, 1.5, 'v', 8, 1.27, lead=1.0, down=False)
        box('HX S8550', 11.2-1.45, Y(1.6)-1.2, t, 2.9, 1.3, 1.0, M['epoxy'], 0.05)
        for i, (a, b, q) in enumerate([(23.8, 2.5, 0), (8.6, 12.0, 1), (11.0, 12.0, 1), (8.6, 16.4, 0), (11.0, 16.4, 0), (15.0, 15.0, 0),
                                       (20.6, 15.0, 0), (22.8, 9.6, 1), (25.4, 9.6, 1), (19.0, 2.5, 0)]):
            passive('HX SMD %d' % i, a, Y(b), q, 'r' if i % 2 else 'c', down=False, L_=2.0, W_=1.25, H_=0.6)
        B = Batch(); Bh = Batch()
        for i in range(6): B.cyl((4.0, Y(3.7+i*2.54), -0.02), 1.7, t+0.04, 16); Bh.cyl((4.0, Y(3.7+i*2.54), -0.05), 0.95, t+0.1, 12)
        for i in range(4): B.cyl((30.0, Y(6.4+i*2.54), -0.02), 1.7, t+0.04, 16); Bh.cyl((30.0, Y(6.4+i*2.54), -0.05), 0.95, t+0.1, 12)
        B.make('HX Pads', M['tin'], False); Bh.make('HX Loecher', M['hole'], False)
    for i, k in enumerate(('hx_e+', 'hx_e-', 'hx_a-', 'hx_a+')):
        A[k] = wpt('hx', (4.0, 20-(3.7+i*2.54), 1.6))
    for i, k in enumerate(('hx_gnd', 'hx_dt', 'hx_sck', 'hx_vcc')):
        A[k] = wpt('hx', (30.0, 20-(6.4+i*2.54), 1.6))

def make_loadcell():
    # Waegezelle 5 kg (TAL220-Bauform) 80 x 12,7 x 12,7, Loecher M4/M5, Kabel rot/schwarz/weiss/gruen
    with grp('lc', (lc_x0, lc_y0, lc_z0), 0, C_EL, 'Waegezelle 5 kg'):
        w = 12.7; l = 80
        bar = box('Waegezelle', 0, 0, 0, w, l, w, M['alu'])
        cut = []
        cut.append(cyl('c', 36.0, w/2, -2, 8.6, w+4, M['hole'], 48, axis='x', smooth=False))
        cut.append(cyl('c', 44.0, w/2, -2, 8.6, w+4, M['hole'], 48, axis='x', smooth=False))
        cut.append(box('c', -2, 36.0, w/2-1.6, w+4, 8.0, 3.2, M['hole']))
        for yy, d in ((5, 3.3), (20, 3.3), (60, 4.2), (75, 4.2)):
            cut.append(cyl('c', w/2, yy, -2, d, w+4, M['hole'], 32, smooth=False))
        bool_cut(bar, cut)
        bevel(bar, 0.4, 2, 60)
        for yy, d in ((5, 4.0), (20, 4.0), (60, 5.0), (75, 5.0)):
            for z in (-0.01, w-0.01): cyl('Gewinde', w/2, yy, z, d*0.82, 0.02, M['black'], 24)
        for z in (w, -0.9):
            box('DMS-Verguss', 2.0, 34.5, z, w-4.0, 11.0, 0.9, M['cell_pot'], 0.4, 3)
        lab = box('Etikett Seite', w-0.01, 6.0, 0.8, 0.04, 68.0, 11.1, M['alu'])
        # Etikett als Textur auf der Aussenseite (+x)
        me = lab.data; uv = me.uv_layers.new(); lab.data.materials.clear(); lab.data.materials.append(tex_mat('Waegezelle Etikett', 'lc_label.png', 0.5))
        for p in me.polygons:
            for li in p.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = ((co.y-6.0)/68.0, (co.z-0.8)/11.1)
        cyl('Kabeltuelle', 6.35, 9.0, l-0.2, 3.2, 1.5, M['black'], 20, axis='y')
    for i, k in enumerate(('lc_r', 'lc_k', 'lc_w', 'lc_g')):
        A[k] = wpt('lc', (6.35 + (i-1.5)*0.75, l+1.0, 9.0 + (0.3 if i % 2 else -0.3)))

def make_cob():
    # BTF FCOB WS2812B-kompatibel, 160 LED/m, 5 mm breit; auf der Rueckwand der Lichtkammer (y = 5,7)
    with grp('led', (0, 0, 0), 0, C_EL, 'COB-LED-Streifen'):
        yw = 5.7; tf = 0.25
        box('COB Traeger', cob_x0, yw-tf, cob_zc-2.5, cob_len, tf, 5.0, M['cob_fpc'], 0.05, 1)
        prof = [(cob_zc - 1.7 + 3.4*i/16, yw - tf - 2.2*math.sin(math.pi*i/16)**0.6) for i in range(17)]
        pts = [(z, y) for (z, y) in prof]
        prism('COB Silikon', [(y, z) for (z, y) in [(cob_zc-1.75, yw-tf)] + prof + [(cob_zc+1.75, yw-tf)]], cob_x0+3.2, cob_len-3.6, M['cob_sil'], axis='x')
        B = Batch()
        for i in range(1, 13):
            x = cob_x0 + i*12.5
            for zz in (cob_zc-2.3, cob_zc+1.9): B.box(x-0.45, yw-tf-0.03, zz, 0.9, 0.04, 0.4)
        for k, zz in enumerate((cob_zc-1.7, cob_zc-0.35, cob_zc+1.0)):
            B.box(cob_x0+0.3, yw-tf-0.03, zz, 2.4, 0.04, 0.7)
        B.make('COB Pads', M['gold'], False)
    for k, zz in zip(('cob_5v', 'cob_din', 'cob_gnd'), (cob_zc-1.35, cob_zc, cob_zc+1.35)):
        A[k] = Vector((cob_x0+1.5, 5.7-0.25-0.3, zz))

def make_switch():
    # C&K OS102011MS2QN1, Schieber durch die linke Wand, Pins nach innen (x), Raster 2 mm (oben: AN-Pin, Annahme)
    with grp('sw', (0, 0, 0), 0, C_EL, 'Schiebeschalter OS102011'):
        y0 = 27 - 2.15; z0 = 3.05
        box('Schalter Blech', 2.45, y0, z0, 3.0, 4.3, 8.6, M['steel'], 0.12, 1)
        box('Schalter Sockel', 5.45, y0+0.15, z0+0.2, 0.95, 4.0, 8.2, M['black'], 0.08, 1)
        box('Schalter Schieber', -1.55, 27-1.0, 7.3-1.0, 4.0, 2.0, 2.0, M['black'], 0.2)
        for i in range(3):
            box('Schalter Pin %d' % i, 6.4, 27-0.25, 5.1+i*2.0-0.2, 2.8, 0.5, 0.4, M['tin'])
        for zz in (z0+0.3, z0+8.6-0.8): box('Schalter Lasche', 6.4, 27-0.75, zz, 2.2, 1.5, 0.5, M['steel'])
    for i, k in enumerate(('sw_aus', 'sw_mid', 'sw_an')):
        A[k] = Vector((8.4, 27.0, 5.1+i*2.0))

# ---------------- Gehaeuse, Schrauben, Fuesse, Matte ----------------
def hex_pts(cx, cy, s):
    r = s/math.sqrt(3); return [(cx + r*math.cos(math.radians(30+60*i)), cy + r*math.sin(math.radians(30+60*i))) for i in range(6)]
def screw_csk(name, x, y, ztop, d, L_, dk, k, s, up=False):
    """DIN 7991 Senkkopf mit Innensechskant, A2. up=True: Kopf unten (von unten eingeschraubt)."""
    sg = -1 if up else 1
    if not up:
        lathe(name+' Kopf', [(0, ztop), (dk/2, ztop), (dk/2-0.1, ztop-0.15), (d/2, ztop-k), (d/2*0.92, ztop-k-0.01), (d/2*0.92, ztop-L_+0.4), (d/2*0.75, ztop-L_), (0, ztop-L_)], M['steel'], 32, x, y)
        prism(name+' Innensechskant', hex_pts(x, y, s), ztop-s*0.9, s*0.9+0.02, M['black'])
    else:
        lathe(name+' Kopf', [(0, ztop), (dk/2, ztop), (dk/2-0.1, ztop+0.15), (d/2, ztop+k), (d/2*0.92, ztop+k+0.01), (d/2*0.92, ztop+L_-0.4), (d/2*0.75, ztop+L_), (0, ztop+L_)], M['steel'], 32, x, y)
        prism(name+' Innensechskant', hex_pts(x, y, s), ztop-0.02, s*0.9, M['black'])

def make_housing():
    with grp('base', (0, 0, 0), 0, C_GEH, 'Unterschale'):
        import_stl('Unterschale', 'base.stl', M['pla'])
    with grp('cover', (0, 0, 0), 0, C_GEH, 'Deckel'):
        import_stl('Deckel', 'cover.stl', M['pla'])
    with grp('pad', (0, 0, 0), 0, C_GEH, 'Flaschenplatte'):
        import_stl('Flaschenplatte', 'pad.stl', M['pad'])
    with grp('cap', (0, 0, 0), 0, C_GEH, 'Abdeckkappe USB'):
        import_stl('Abdeckkappe USB', 'cap.stl', M['pla'])
    with grp('diff', (0, 0, 0), 0, C_GEH, 'Diffusor'):
        import_stl('Diffusor-Leiste', 'diff.stl', MATS.get('Diffusor') or milky_mat('Diffusor', DIFF_GLOW))
    with grp('keil', (0, 0, 0), 0, C_GEH, 'Klemmkeile'):
        import_stl('Klemmkeile', 'keil.stl', M['pla'])

def make_mat():
    with grp('mat', (0, 0, 0), 0, C_GEH, 'Silikonmatte'):
        o = prism('Silikonmatte 86x86x1,2', rrect_pts(83.1, 7.1, 85.8, 85.8, 3.0, 6), pad_top_z, 1.2, M['sil'], 0.3)

def make_screws():
    with grp('m3', (0, 0, 0), 0, C_EL, 'Schrauben M3x12 (Deckel)'):
        for i, (x, y) in enumerate([(cyd_x+u, cyd_y+v) for (u, v) in cyd_holes_uv] + cov_bosses):
            screw_csk('M3x12 %d' % i, x, y, H, 3, 12, 6.0, 1.7, 2.0)
    with grp('m4', (0, 0, 0), 0, C_EL, 'Schrauben M4x10 (Pad)'):
        for i, yy in enumerate([15, 30]): screw_csk('M4x10 %d' % i, pad_cx, yy, pad_top_z, 4, 10, 8.0, 2.3, 2.5)
    with grp('m5', (0, 0, 0), 0, C_EL, 'Schrauben M5x12 (Boden)'):
        for i, yy in enumerate([70, 85]): screw_csk('M5x12 %d' % i, pad_cx, yy, 0.0, 5, 12, 10.0, 2.8, 3.0, up=True)

def make_feet(zb):
    with grp('feet', (0, 0, 0), 0, C_GEH, 'Gummifuesse'):
        for i, (x, y) in enumerate(feet_pos):
            z = zb[i]
            lathe('Fuss %d' % i, [(0, z-4.5), (4.2, z-4.5), (4.75, z-4.3), (5.0, z-3.9), (4.75, z-0.05), (0, z-0.05)], M['rubber'], 40, x, y)

# =====================================================================
#  KABEL  (Wegpunkte in Weltkoordinaten der Ruhelage; Tag = Baugruppe, an der der Punkt haengt)
# =====================================================================
WIRES = []
RV = 0.45   # Vierlingslitze 4 x 0,14 mm2 (Ader ca. 0,9 mm)
def V(*a): return Vector(a)
def wire(name, col, r, pts, a='pad', b='pad', shrink=(), note=''):
    """pts: Liste aus (Vector, tag) oder Vector (Tag None = mitlaufend interpoliert)."""
    P = [(p if isinstance(p, tuple) else (p, None)) for p in pts]
    WIRES.append(dict(name=name, col=col, r=r, pts=P, a=a, b=b, shrink=list(shrink), note=note))

def up(p, dz): return Vector((p.x, p.y, p.z + dz))

def define_wires():
    # ---- Akku -> TC4056 (B-/B+), AWG24 UL1007: vorne rechts aus dem Kapton, ueber den Akku, ueber die FET-Platine ----
    for key, tgt, c in (('bat-', 'tc_b-', 'k'), ('bat+', 'tc_b+', 'r')):
        s = A[key]; e = A[tgt]; d = 0.0 if c == 'k' else 1.0
        o = Vector((1.33, -0.88, 0)) * d
        pts = [(s, 'bat'), V(s.x, 40.5, 7.5), V(s.x, 40.1, 10.0), V(s.x+0.2, 40.9, 12.6), V(s.x+0.6-0.4*d, 42.8, 13.55),
               V(44.2, 47.0, 13.6) + o*1.0 + V(0.6*d, 0, 0), V(48.5, 58.0, 13.6) + o, V(53.0, 66.5, 13.6) + o]
        if c == 'k': pts += [V(58.0, 71.0, 11.2), V(60.9, 72.6, 8.4)]
        else: pts += [V(59.3, 70.1, 11.8), V(63.5, 70.9, 10.8), V(66.6, 72.4, 8.4)]
        pts += [(up(e, 2.0), None), (up(e, 0.3), 'tc')]
        wire('Akku ' + ('minus' if c == 'k' else 'plus') + ' -> TC4056 ' + ('B-' if c == 'k' else 'B+'), c, 0.7, pts, a='inside')
    # ---- TC4056 OUT+ -> Pad 6 (Source Q2), OUT- -> Pad 2 (GND) ----
    e = A['fet6']; s = A['tc_out+']
    wire('TC4056 OUT+ -> FET Pad 6 (Source Q2)', 'r', RV, [(up(s, 0.3), 'tc'), up(s, 2.2), V(70.2, 71.0, 7.8), V(64.6, 70.6, 7.8),
         V(62.6, 66.8, 7.6), V(61.4, 64.2, 7.2), (up(e, 2.0), None), (up(e, 0.25), 'fet')])
    e = A['fet2']; s = A['tc_out-']
    wire('TC4056 OUT- -> FET Pad 2 (GND)', 'b', RV, [(up(s, 0.3), 'tc'), up(s, 2.4), V(58.0, 72.8, 11.0), V(62.0, 72.6, 15.2),
         V(72.0, 71.6, 14.6), V(74.7, 66.0, 11.0), V(74.8, 55.0, 9.2), V(74.6, 48.0, 9.0), V(72.6, 45.8, 8.6), (up(e, 2.2), None), (up(e, 0.25), 'fet')])
    # ---- Schalter (Pins oben/Mitte/unten = AN/Mitte/AUS, Annahme) ----
    def sw_start(key):
        z = A[key].z
        return [(V(6.9, 27.0, z), 'sw'), V(11.5, 27.0, z), V(15.4, 27.0 + 0.25*(z-7.1), z)]
    e = A['fet9']
    wire('Schalter AN -> FET Pad 9 (GND)', 'b', RV, sw_start('sw_an') + [V(17.6, 32.0, 8.6), V(20.5, 36.0, 7.6), V(26.0, 37.0, 7.2), V(40.0, 37.4, 7.2),
         V(46.0, 37.9, 8.0), V(52.0, 38.8, 8.6), V(66.8, 38.8, 8.6), V(68.47, 40.6, 8.4), (up(e, 2.0), None), (up(e, 0.25), 'fet')], a='shrink', shrink=[(0.0, 4.6)])
    e = A['fet7']
    wire('Schalter Mitte -> FET Pad 7 (Gate Q2)', 'g', RV, sw_start('sw_mid') + [V(16.2, 31.0, 7.1), V(16.8, 38.0, 9.2), V(17.4, 41.4, 12.9), V(19.4, 44.2, 14.8), V(30.0, 47.2, 15.3),
         V(41.0, 48.8, 15.3), V(46.0, 52.2, 15.3), V(52.0, 56.4, 15.0), V(56.6, 55.67, 11.6), V(59.4, 55.67, 10.4), (up(e, 2.4), None), (up(e, 0.25), 'fet')], a='shrink', shrink=[(0.0, 4.6)])
    e = A['fet8']
    wire('Schalter AUS -> FET Pad 8 (Source Q2)', 'y', RV, sw_start('sw_aus') + [V(16.0, 31.0, 5.6), V(16.0, 38.0, 8.6), V(16.6, 41.4, 12.8), V(18.0, 45.6, 14.8), V(30.0, 49.0, 15.3),
         V(41.0, 50.5, 15.3), V(45.6, 59.0, 15.3), V(56.0, 64.4, 15.0), V(59.0, 65.6, 12.2), V(60.6, 65.83, 10.4), (up(e, 2.4), None), (up(e, 0.25), 'fet')], a='shrink', shrink=[(0.0, 4.6)])
    # ---- Pololu (Loecher hinten: VIN x 26,86 / GND 29,40 / VOUT 31,94) ----
    vo, gn, vi = A['pol_vout'], A['pol_gnd'], A['pol_vin']
    S3, S1 = A['S3'], A['S1']
    wire('Pololu VOUT -> CYD Testpunkt S3 (5 V)', 'r', RV, [(up(vo, 0.25), 'pol'), up(vo, 3.0), up(vo, 4.6), V(vo.x+0.8, 34.6, 10.0), V(35.6, 38.0, 11.6), V(36.1, 41.6, 12.95),
         V(36.1, 50.0, 12.95), V(36.1, 60.0, 12.95), V(36.1, 70.0, 12.95), V(36.0, S3.y-0.6, 13.6), V(35.6, S3.y, 15.8), (S3 + V(0, 0, -1.4), None), (S3 + V(0, 0, -0.1), 'cyd')], b='under')
    wire('Pololu GND -> CYD Testpunkt S1 (GND)', 'b', RV, [(up(gn, 0.25), 'pol'), up(gn, 3.0), up(gn, 4.6), V(gn.x+1.2, 34.4, 9.6), V(34.4, 38.0, 11.4), V(35.0, 41.6, 12.95),
         V(35.0, 50.0, 12.95), V(35.0, 60.0, 12.95), V(35.0, 72.0, 12.95), V(35.0, S1.y-0.6, 13.6), V(35.1, S1.y, 15.8), (S1 + V(0, 0, -1.4), None), (S1 + V(0, 0, -0.1), 'cyd')], b='under')
    e = A['fet1']
    wire('Pololu VOUT -> FET Pad 1 (Source Q1, Elko +)', 'r', RV, [(up(vo, 0.25), 'pol'), up(vo, 1.6), V(vo.x+0.6, 34.6, 6.6), V(34.5, 35.6, 7.0),
         V(40.0, 35.8, 9.6), V(45.2, 36.8, 11.4), V(47.0, 40.0, 12.8), V(47.4, 44.4, 14.6), V(48.6, 47.4, 15.2), V(56.0, 49.0, 15.2), V(62.2, 50.4, 14.8), (up(e, 2.6), None), (up(e, 0.25), 'fet')])
    e = A['fet2']
    wire('Pololu GND -> FET Pad 2 (GND)', 'b', RV, [(up(gn, 0.25), 'pol'), up(gn, 1.2), V(gn.x+0.6, 34.2, 5.8), V(33.6, 34.5, 5.9),
         V(40.0, 34.8, 9.4), V(45.8, 36.0, 12.0), V(48.0, 40.4, 13.8), V(48.2, 44.6, 15.4), V(50.4, 47.4, 15.9), V(60.0, 47.0, 15.9), V(70.6, 46.3, 15.8), V(71.01, 45.7, 12.5), (up(e, 2.6), None), (up(e, 0.25), 'fet')])
    e = A['fet10']
    wire('FET Pad 10 (Drain Q2) -> Pololu VIN', 'r', RV, [(up(vi, 0.25), 'pol'), up(vi, 0.9), V(vi.x+0.4, 34.6, 5.0), V(28.0, 35.4, 4.8),
         V(36.0, 35.6, 4.6), V(44.0, 35.8, 5.0), V(46.2, 37.0, 5.6), V(46.4, 39.0, 7.2), V(46.9, 41.0, 9.2), V(47.6, 43.6, 11.6), V(49.6, 47.6, 12.2),
         V(54.0, 51.4, 12.2), V(59.4, 53.13, 11.4), (up(e, 2.4), None), (up(e, 0.25), 'fet')])
    # ---- Akku-Teiler 2 x 10 kOhm im Schrumpfschlauch (x 51,3; y 22,5-33,5), Mitte -> IO35 (P3) ----
    wire('Teiler oben -> Pololu VIN', 'r', RV, [(up(vi, 0.25), 'pol'), up(vi, 1.6), V(vi.x-0.2, 34.2, 4.4), V(28.0, 34.3, 4.2), V(36.0, 34.3, 4.2),
         V(44.0, 34.4, 4.4), V(47.4, 34.6, 5.6), V(49.4, 34.8, 6.0), V(51.1, 34.8, 4.6), (V(51.3, 33.4, 3.75), 'div')], b='inside')
    p3 = A['p3']
    wire('CYD P3 GND (schwarz) -> Teiler unten', 'k', 0.4, [(p3[0], 'cyd'), V(61.0, p3[0].y-0.2, 15.8), V(61.6, 22.4, 12.0), V(58.0, 21.8, 8.0),
         V(54.6, 21.6, 6.4), V(52.2, 21.8, 4.6), (V(51.3, 22.6, 3.75), 'div')], a='plug', b='inside')
    wire('CYD P3 IO35 (blau) -> Teiler Mitte', 'b', 0.4, [(p3[1], 'cyd'), V(61.4, p3[1].y, 15.4), V(61.0, 25.8, 11.5), V(57.0, 27.0, 8.4),
         V(53.0, 27.8, 6.6), V(51.6, 28.0, 5.8), (V(51.3, 28.0, 5.0), 'div')], a='plug', b='inside')
    for i, c in ((2, 'y'), (3, 'r')):
        wire('CYD P3 %s (frei, isoliert)' % ('IO22' if i == 2 else 'IO21'), c, 0.4, [(p3[i], 'cyd'), V(60.8, p3[i].y+0.2, 16.3), (V(63.4, p3[i].y+0.9, 15.6), 'cyd')],
             a='plug', b='cap')
    # ---- CN1 -> HX711 (VCC/SCK/DT/GND) mit Abzweig 3,3 V / GND zum LM393 ----
    cn = A['cn1']   # GND, IO22(SCK), IO27(DT), 3V3(VCC)
    hxk = {0: 'hx_gnd', 1: 'hx_sck', 2: 'hx_dt', 3: 'hx_vcc'}
    xlane = {0: 134.4, 1: 135.3, 2: 136.2, 3: 137.1}; zlane = {0: 7.4, 1: 7.4, 2: 8.6, 3: 7.4}
    colc = {0: 'k', 1: 'b', 2: 'y', 3: 'r'}
    for i in range(4):
        e = A[hxk[i]]; xl = xlane[i]; zl = zlane[i]; yi = cn[i].y; xx = 75.7 + (3-i)*0.95; yb = 94.0 + i*0.92; xt = 85.0 + (3-i)*0.92
        pts = [(cn[i], 'cyd'), V(66.0, yi, 16.5), V(72.0, yi+0.4, 15.6), V(xx, 46.0+i*0.3, 10.0), V(xx, 50.0, 5.0), V(xx, 54.0, 3.8),
               V(xx, 62.0, 3.8), V(xx, 70.0, 3.8), V(xx, 78.0, 3.8), V(xx, 84.0, 3.8), V(xx+1.0, 86.0+i*0.92, 3.8), V(82.0, 86.0+i*0.92, 3.7), V(xt-1.2, 86.0+i*0.92, 3.6), V(xt, 87.2+i*0.92, 3.6), V(xt, yb-1.2, 3.5), V(xt+1.2, yb, 3.5)]
        pts += [V(x_, yb, 3.4) for x_ in (93.0, 98.0, 106.0, 114.0, 122.0, 128.0)]
        pts += [V(xl-1.6, yb, 3.6), V(xl, yb-1.6, 5.0), V(xl, 88.0, 7.0), V(xl, 82.0, zl), V(xl, e.y+1.4, zl), V(xl+1.2, e.y, zl),
                V(e.x-1.4, e.y, zl-0.6), (up(e, 1.8), None), (up(e, 0.25), 'hx')]
        nm = {0: 'GND', 1: 'IO22 -> SCK', 2: 'IO27 -> DT', 3: '3V3 -> VCC'}[i]
        sh = [(V(61.0, yi, 16.5), 2.2)] if i in (0, 3) else []
        wire('CYD CN1 %s (HX711)' % nm, colc[i], 0.4, pts, a='plug', shrink=sh)
    for i, tgt, c in ((3, 'cmp_vcc', 'r'), (0, 'cmp_gnd', 'b')):
        e = A[tgt]; s = V(61.0, cn[i].y, 16.5)
        wire('Abzweig CN1 %s -> LM393 %s' % ('3V3' if i == 3 else 'GND', 'VCC' if i == 3 else 'GND'), c, RV,
             [(s, 'cyd'), V(61.2, cn[i].y-1.2, 15.4), V(e.x+0.6, 37.0, 12.4), V(e.x+0.3, 30.0, 10.6), V(e.x, 22.0, 8.6), V(e.x, 17.0, 7.8),
              V(e.x, 12.4, 5.8), (up(e, 1.6), None), (up(e, 0.25), 'cmp')], a='splice')
    # ---- microSD-Kontakte (Unterseite CYD), Bahnen auf dem Akku: SD3 x 37,3 / SD7 x 38,4 / SD5 x 39,6 ----
    sd3, sd5, sd7 = A['sd3'], A['sd5'], A['sd7']
    e = A['fet5']
    wire('SD-Kontakt 5 (GPIO18) -> FET Pad 5 (4,7 k -> BC547B)', 'y', RV, [(sd5 + V(0, 0, -0.05), 'cyd'), V(39.2, sd5.y, 17.2), V(39.6, sd5.y-0.8, 14.6),
         V(39.6, 50.0, 12.95), V(39.6, 43.0, 12.95), V(39.6, 40.6, 12.0), V(40.4, 38.6, 10.4), V(44.0, 38.5, 10.0), V(47.8, 39.6, 9.6), V(52.0, 40.0, 9.2),
         V(58.0, 40.0, 9.2), V(64.4, 40.0, 9.2), V(65.93, 41.4, 8.8), (up(e, 2.2), None), (up(e, 0.25), 'fet')], a='under')
    e = A['cmp_do']
    wire('SD-Kontakt 7 (GPIO19) -> LM393 DO', 'g', RV, [(sd7 + V(0, 0, -0.05), 'cyd'), V(38.9, sd7.y, 17.0), V(38.4, sd7.y-0.8, 14.4),
         V(38.4, 50.0, 12.95), V(38.4, 42.0, 12.95), V(38.4, 36.0, 12.6), V(38.5, 30.0, 12.4), V(38.6, 25.0, 11.8), V(39.8, 21.4, 7.6), V(41.6, 19.4, 5.6),
         V(46.0, 19.3, 5.0), V(52.0, 19.3, 5.2), V(55.0, 19.3, 6.6), V(59.0, 19.3, 6.6), V(63.6, 17.0, 6.4), V(e.x, 13.0, 5.6),
         (up(e, 1.6), None), (up(e, 0.25), 'cmp')], a='under')
    # ---- COB-Streifen: weiss GND -> Pad 4, rot 5 V -> Pad 3 (Drain Q1), gruen DIN -> 470 Ohm -> SD-Kontakt 3 (GPIO23) ----
    ST = {'cob_gnd': [V(11.0, 7.9, 10.0), V(13.0, 8.4, 8.0)], 'cob_5v': [V(11.2, 8.3, 7.0), V(12.4, 9.5, 5.6)], 'cob_din': [V(11.2, 8.6, 8.6), V(12.6, 10.4, 7.0)]}
    def cob_start(key):
        s = A[key]
        return [(s, 'led'), V(s.x-1.4, 4.75, s.z), V(9.75, 5.2, s.z), V(9.65, 6.5, s.z), V(9.9, 7.6, s.z)] + ST[key]
    e = A['fet4']
    wire('COB weiss (GND) -> FET Pad 4 (GND)', 'w', 0.5, cob_start('cob_gnd') + [V(15.6, 8.6, 4.4), V(22.0, 8.6, 4.1),
         V(30.0, 8.6, 4.1), V(38.0, 8.6, 4.1), V(46.0, 8.6, 4.1), V(52.4, 9.0, 4.2), V(55.25, 12.6, 4.4), V(55.25, 20.0, 4.5), V(55.25, 27.0, 4.5),
         V(55.25, 32.0, 5.0), V(55.9, 35.6, 6.4), V(58.0, 38.0, 6.4), V(64.0, 38.0, 6.4), V(69.6, 38.0, 6.4), V(71.01, 40.0, 6.6),
         (up(e, 1.8), None), (up(e, 0.25), 'fet')])
    e = A['fet3']
    wire('COB rot (5 V) -> FET Pad 3 (Drain Q1)', 'r', 0.5, cob_start('cob_5v') + [V(15.0, 9.6, 4.3), V(22.0, 9.6, 4.1),
         V(30.0, 9.6, 4.1), V(38.0, 9.6, 4.1), V(46.0, 9.6, 4.1), V(51.4, 9.9, 4.2), V(54.2, 13.0, 4.4), V(54.2, 20.0, 4.5), V(54.2, 27.0, 4.5),
         V(54.2, 32.0, 5.4), V(54.4, 36.0, 6.8), V(55.4, 39.4, 7.0), V(57.4, 40.6, 7.0), V(60.85, 41.4, 7.0), (up(e, 1.8), None), (up(e, 0.25), 'fet')])
    wire('COB gruen (DIN) -> 470 Ohm -> SD-Kontakt 3 (GPIO23)', 'g', 0.5, cob_start('cob_din') + [V(15.0, 10.6, 4.4),
         V(22.0, 10.6, 4.2), V(30.0, 10.6, 4.2), V(35.6, 10.6, 4.4), V(37.3, 12.4, 5.6), V(37.3, 18.0, 9.0), V(37.3, 24.0, 12.2), V(37.3, 30.0, 12.6),
         V(37.3, 36.0, 12.8), V(37.3, 42.0, 12.95), V(37.3, 50.0, 12.95), V(37.3, sd3.y-0.6, 13.6), V(38.3, sd3.y, 15.4), V(38.9, sd3.y, 17.2),
         (sd3 + V(0, 0, -0.05), 'cyd')], b='under', shrink=[(V(25.0, 10.6, 4.2), 5.0, 0.55)])
    # ---- Regenplatte -> LM393 (2 Dupont-Litzen, Stecker abgeschnitten, an die Winkelstifte geloetet) ----
    for key, tgt, c, xl, yf, yt in (('rs_1', 'cmp_s1', 'o', 74.0, 14.0, 33.6), ('rs_2', 'cmp_s2', 'y', 75.2, 15.2, 35.0)):
        s = A[key]; e = A[tgt]
        wire('Regenplatte -> LM393 Sensor-Eingang (%s)' % ('orange' if c == 'o' else 'gelb'), c, 0.55, [(s + V(0, 2.4, 0), 'rs'), V(s.x, s.y-1.4, s.z+0.2), V(s.x-1.6, yf, 4.6), V(88.0, yf, 5.0),
             V(xl+2.5, yf+0.4, 5.6), V(xl, yf+4.0, 5.8), V(xl, yf+10.0, 5.9), V(xl, yt-2.0, 6.0), V(xl-1.6, yt, 6.0), V(e.x+1.5, yt, 5.6),
             V(e.x, yt + (1.0 if c == 'o' else 0.2), 5.4), (up(e, 1.6), None), (up(e, 0.25), 'cmp')], a='shrink', shrink=[(0.0, 5.0)])
    # ---- Waegezelle -> HX711 J1 ----
    for i, (key, tgt, c) in enumerate((('lc_r', 'hx_e+', 'r'), ('lc_k', 'hx_e-', 'k'), ('lc_w', 'hx_a-', 'w'), ('lc_g', 'hx_a+', 'g'))):
        s = A[key]; e = A[tgt]; xl = {0: 170.6, 1: 169.6, 2: 168.6, 3: 167.6}[i]; yb = 92.4 + (3-i)*0.95
        wire('Waegezelle %s -> HX711 J1' % {0: 'rot E+', 1: 'schwarz E-', 2: 'weiss A-', 3: 'gruen A+'}[i], c, 0.38, [(s, 'lc'), V(s.x, s.y+1.2, s.z-0.6),
             V(s.x+2.0, yb, s.z-3.0), V(136.0, yb, 8.6), V(146.0, yb, 8.0), V(156.0, yb, 7.6), V(xl-1.6-(3-i)*0.0, yb, 7.2), V(xl, yb-1.8, 7.0), V(xl, 86.0, 6.8),
             V(xl, 80.0, 6.8), V(xl, e.y+1.4, 6.6), V(xl-1.2, e.y, 6.2), V(e.x+1.0, e.y, 5.8), (up(e, 2.0), None), (up(e, 0.25), 'hx')], a='none')

# ---------------- Kabel erzeugen (mit Versatz der Baugruppen) ----------------
OFF = {}
def goff(tag): return OFF.get(tag, Vector((0, 0, 0)))
def wire_points(wd):
    P0 = wd['pts']; P = [P0[0]]
    for (p, t_) in P0[1:]:
        q = P[-1][0]; n_ = int((p-q).length / 5.0)
        for k in range(1, n_+1):
            if n_ > 0 and k < n_+1 and (p-q).length > 5.0 and k <= n_ - 0: P.append((q.lerp(p, k/(n_+1)), None))
        P.append((p, t_))
    n = len(P)
    pos = [p for p, t in P]
    # Bogenlaenge
    s = [0.0]
    for i in range(1, n): s.append(s[-1] + (pos[i]-pos[i-1]).length)
    tagged = [i for i, (p, t) in enumerate(P) if t is not None]
    out = []
    for i, (p, t) in enumerate(P):
        if t is not None: out.append(p + goff(t)); continue
        a = max([j for j in tagged if j < i]); b = min([j for j in tagged if j > i])
        f = (s[i]-s[a]) / max(s[b]-s[a], 1e-6)
        out.append(p + goff(P[a][1]).lerp(goff(P[b][1]), f))
    return out

WOBJ = []; WPOLY = {}
def poly_len(P):
    s = [0.0]
    for i in range(1, len(P)): s.append(s[-1] + (P[i]-P[i-1]).length)
    return s
def sub_poly(P, S, s0, s1):
    out = []
    for i in range(len(P)):
        if s0 <= S[i] <= s1: out.append(P[i])
    if len(out) < 2:
        i = min(range(len(P)), key=lambda k: abs(S[k]-(s0+s1)/2)); out = [P[max(i-1, 0)], P[min(i+1, len(P)-1)]]
    return out

def build_wires():
    CUR[0] = C_KAB
    Bs = Batch(); n_sold = 0
    for wd in WIRES:
        pts = wire_points(wd)
        P = catmull(pts, 8)
        WPOLY[wd['name']] = (P, wd['r'])
        cd = bpy.data.curves.new(wd['name'], 'CURVE'); cd.dimensions = '3D'
        cd.bevel_depth = wd['r']; cd.bevel_resolution = 3; cd.use_fill_caps = True
        sp = cd.splines.new('POLY'); sp.points.add(len(P)-1)
        for i, p in enumerate(P): sp.points[i].co = (p.x, p.y, p.z, 1)
        o = bpy.data.objects.new(wd['name'], cd); link(o, wmat(wd['col'])); WOBJ.append(o)
        S = poly_len(P)
        for end, p, q in (('a', P[0], P[1]), ('b', P[-1], P[-2])):
            kind = wd[end]
            if kind == 'pad':
                Bs.sph(p + Vector((0, 0, -0.05)), 0.78, 0.62, 14); n_sold += 1
            elif kind == 'under':
                Bs.sph(p + Vector((0, 0, 0.0)), 0.62, 0.6, 14); n_sold += 1
            elif kind == 'cap':
                SP = sub_poly(P, S, S[-1]-4.0, S[-1]); SP = SP + [SP[-1] + (SP[-1]-SP[-2]).normalized()*0.6]
                tube(wd['name']+' Schrumpfkappe', SP, M['shrink'], wd['r']+0.32, 3, 1)
        for sh in wd['shrink']:
            if isinstance(sh[0], Vector):
                c = sh[0] + goff(wd['pts'][0][1]); hl = sh[1]; rr = sh[2] if len(sh) > 2 else 0.32
                i = min(range(len(P)), key=lambda k: (P[k]-c).length); s0, s1 = S[i]-hl, S[i]+hl
            else:
                s0, s1 = sh; rr = 0.32
                if s1 < 0: s0, s1 = S[-1]+s0, S[-1]+s1
            SP = sub_poly(P, S, max(0, s0), min(S[-1], s1))
            tube(wd['name']+' Schrumpfschlauch', SP, M['shrink'], wd['r']+rr, 3, 1)
    Bs.make('Loetstellen Kabel', M['tin'])
    # Teiler-Kapsel (2 x 10 kOhm in Schrumpfschlauch)
    d0 = Vector((51.3, 22.5, 3.75)) + goff('div'); d1 = Vector((51.3, 33.5, 3.75)) + goff('div')
    tube('Akku-Teiler 2x10k (Schrumpfschlauch)', [d0, (d0+d1)/2 + Vector((0, 0, 0.1)), d1], M['shrink'], 1.55, 4, 1)
    CUR[0] = C_EL

# =====================================================================
#  AUFBAU, LICHT, KAMERA, PRUEFUNG
# =====================================================================
DIFF_GLOW = 0.0
def build_all():
    global DIFF_GLOW
    make_housing(); make_mat()
    make_cyd(); make_battery(); make_pololu(); make_tc(); make_fet(); make_cmp(); make_rs(); make_hx(); make_loadcell()
    make_cob(); make_switch(); make_screws()
    # Fuesse: Unterkante der Unterschale an den Mulden per Strahl bestimmen
    base = bpy.data.objects['Unterschale']; dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(base, dg); zb = []
    for (x, y) in feet_pos:
        hit = bvh.ray_cast(Vector((x, y, -20)), Vector((0, 0, 1))); zb.append(hit[0].z if hit[0] else 0.0)
    make_feet(zb)
    define_wires()

def set_offsets(d):
    OFF.clear()
    for k, v in d.items():
        OFF[k] = Vector(v)
        if k in GROUPS: GROUPS[k].location = G_BASEMAT[k].to_translation() + Vector(v)

def hide(names):
    for g in names:
        GROUPS[g].hide_render = True; GROUPS[g].hide_viewport = True
        for o in GROUPS[g].children_recursive: o.hide_render = True; o.hide_viewport = True

def xray(objs, alpha=0.18):
    for o in objs:
        for i, m in enumerate(o.data.materials):
            mx = m.copy(); mx.name = m.name + ' (Roentgen)'; nt = mx.node_tree
            out = nt.nodes['Material Output']; src = out.inputs['Surface'].links[0].from_node
            tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
            mix.inputs['Fac'].default_value = 1.0 - alpha
            nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(src.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs['Surface'])
            o.data.materials[i] = mx

def world_hdri(strength=0.6, rot=0.0, file='studio.exr', bg=None):
    w = bpy.data.worlds.new('Studio'); w.use_nodes = True; scn.world = w; nt = w.node_tree
    bgn = nt.nodes['Background']; env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(SL + file)
    mp = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord'); mp.inputs['Rotation'].default_value[2] = math.radians(rot)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bgn.inputs['Color']); bgn.inputs['Strength'].default_value = strength
    if bg is not None:   # Kamera sieht neutralen Hintergrund, Licht kommt aus der HDRI
        lp = nt.nodes.new('ShaderNodeLightPath'); bg2 = nt.nodes.new('ShaderNodeBackground'); bg2.inputs['Color'].default_value = (*bg, 1)
        mx = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes['World Output']
        nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs['Fac']); nt.links.new(bgn.outputs[0], mx.inputs[1]); nt.links.new(bg2.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs['Surface'])

def sun(name, rot, s, ang=8):
    l = bpy.data.lights.new(name, 'SUN'); l.energy = s; l.angle = math.radians(ang)
    o = bpy.data.objects.new(name, l); o.rotation_euler = Euler([math.radians(a) for a in rot]); C_ENV.objects.link(o); return o

def camera(target, az, el, dist, lens=85, ortho=None, roll=0.0):
    c = bpy.data.cameras.new('Kamera'); c.lens = lens; c.clip_start = 1; c.clip_end = 20000; c.sensor_width = 36
    if ortho: c.type = 'ORTHO'; c.ortho_scale = ortho
    o = bpy.data.objects.new('Kamera', c); C_ENV.objects.link(o)
    t = Vector(target); a = math.radians(az); e = math.radians(el)
    o.location = t + Vector((-math.sin(a)*math.cos(e), -math.cos(a)*math.cos(e), math.sin(e)))*dist
    q = (t - o.location).to_track_quat('-Z', 'Y'); o.rotation_euler = q.to_euler()
    if roll: o.rotation_euler.rotate_axis('Z', math.radians(roll))
    scn.camera = o; return o

def backdrop(z, col=(0.62, 0.63, 0.65)):
    CUR[0] = C_ENV
    m = mat('Studio-Hintergrund', col, 0.75)
    # Boden + Hohlkehle nach hinten (y+)
    v = []; f = []; nx = 2; xs = (-1500, 1700)
    prof = [(-1500, z)] + [(260 + 300*math.sin(math.radians(a)), z + 300*(1-math.cos(math.radians(a)))) for a in range(0, 91, 6)] + [(560, z+2000)]
    for (y, zz) in prof:
        for x in xs: v.append((x, y, zz))
    for i in range(len(prof)-1): f.append((2*i, 2*i+1, 2*i+3, 2*i+2))
    o = mesh_from('Studio-Hintergrund', v, f, m, smooth=True)
    CUR[0] = C_EL; return o

def check():
    """Kollisionen: Kabel gegen Gehaeuse/Bauteile und Kabel gegen Kabel"""
    dg = bpy.context.evaluated_depsgraph_get()
    verts = []; polys = []; owner = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render: continue
        if C_KAB in o.users_collection or C_ENV in o.users_collection: continue
        eo = o.evaluated_get(dg); me = eo.to_mesh(); mw = o.matrix_world
        base = len(verts); verts += [mw @ v.co for v in me.vertices]
        for p in me.polygons: polys.append([base + i for i in p.vertices]); owner.append(o.name)
        eo.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys)
    print('CHECK Hindernis-Polygone:', len(polys))
    ex = dict(pad=2.6, under=2.2, plug=2.5, inside=3.2, shrink=5.0, splice=0.0, cap=0.0, none=2.0)
    samples = []; bad = 0
    for wd in WIRES:
        P, r = WPOLY[wd['name']]; S = poly_len(P); L_ = S[-1]
        worst = (9, None, None)
        k = 0
        for i in range(len(P)-1):
            seg = P[i+1]-P[i]; n = max(1, int(seg.length/0.3))
            for j in range(n):
                p = P[i] + seg*(j/n); s = S[i] + seg.length*(j/n)
                samples.append((p, r, wd['name'], s, L_))
                if s < ex[wd['a']] or s > L_ - ex[wd['b']]: continue
                loc, nrm, idx, dist = bvh.find_nearest(p)
                if loc is None: continue
                inside = (p - loc).dot(nrm) < 0
                clr = (-dist if inside else dist) - r
                if clr < worst[0]: worst = (clr, p.copy(), owner[idx])
        if worst[0] < -0.12:
            bad += 1; print('CHECK KOLLISION %-55s %6.2f mm bei (%.1f, %.1f, %.1f) mit %s' % (wd['name'][:55], worst[0], *worst[1], worst[2]))
        else:
            print('CHECK ok        %-55s min. Abstand %5.2f mm' % (wd['name'][:55], worst[0]))
    kd = KDTree(len(samples))
    for i, s in enumerate(samples): kd.insert(s[0], i)
    kd.balance(); pairs = {}
    for i, (p, r, nm, s, L_) in enumerate(samples):
        for (co, j, d) in kd.find_range(p, r + 0.62):
            p2, r2, nm2, s2, L2 = samples[j]
            if nm2 <= nm: continue
            if min(s, L_-s) < 4.0 and min(s2, L2-s2) < 4.0: continue    # gemeinsame Loetstelle
            ov = r + r2 - d
            if ov > 0.18:
                k_ = (nm, nm2)
                if k_ not in pairs or pairs[k_][0] < ov: pairs[k_] = (ov, p.copy())
    for (a, b), (ov, p) in sorted(pairs.items(), key=lambda x: -x[1][0]):
        print('CHECK KABEL-KABEL %.2f mm  %s  <->  %s  bei (%.1f, %.1f, %.1f)' % (ov, a[:40], b[:40], *p))
    tot = sum(poly_len(WPOLY[w['name']][0])[-1] for w in WIRES)
    print('CHECK Summe: %d Kabel, %d Kollisionen, %d Kabel-Kabel-Ueberlappungen, Gesamtlaenge %.0f mm' % (len(WIRES), bad, len(pairs), tot))
    for w in WIRES: print('LEN %-60s %6.1f mm' % (w['name'][:60], poly_len(WPOLY[w['name']][0])[-1]))

# =====================================================================
#  MODI
# =====================================================================
LAYER = ['bat', 'pol', 'tc', 'fet', 'cmp', 'rs', 'hx', 'lc', 'led', 'sw', 'div', 'keil']
def render(path):
    scn.render.filepath = path; bpy.ops.render.render(write_still=True); print('RENDER', path)

if MODE == 'produkt': DIFF_GLOW = 2.2
build_all()

if MODE == 'check':
    set_offsets({}); build_wires(); check()
    if len(argv) > 2: exec(open(argv[2]).read())

elif MODE == 'save':
    set_offsets({}); build_wires()
    world_hdri(0.8); sun('Key', (50, 0, 30), 2.5, 10)
    camera((90, 50, 10), -30, 35, 700, 60)
    blend, glb = OUT.split(',')
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
    # GLB: Kurven -> Mesh, alles unter eine Wurzel mit Massstab 0,001 (Meter)
    for o in list(bpy.data.objects):
        if o.type == 'CURVE':
            dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            mo = bpy.data.objects.new(o.name, me)
            for c in o.users_collection: c.objects.link(mo)
            mo.parent = o.parent; mo.matrix_world = o.matrix_world.copy()
            for m in o.data.materials: me.materials.append(m) if not me.materials else None
            bpy.data.objects.remove(o, do_unlink=True)
    root = bpy.data.objects.new('HydroDesk_Base', None); ROOTC.objects.link(root)
    for o in bpy.data.objects:
        if o.parent is None and o is not root and o.type in ('MESH', 'EMPTY'): o.parent = root
    root.scale = (0.001, 0.001, 0.001)
    for o in bpy.data.objects: o.hide_viewport = False; o.hide_set(False) if o.name in bpy.context.view_layer.objects else None
    bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_yup=True, export_apply=True, export_lights=False, export_cameras=False)
    print('SAVED', blend, glb)

else:
    cyd_parts = [o for o in GROUPS['cyd'].children_recursive if o.type == 'MESH']
    if MODE == 'offen':
        set_offsets({}); hide(['cover', 'pad', 'mat', 'm3', 'm4']); build_wires()
        # Display-Modul ausblenden, Platine fast durchsichtig: Bauteile + Litzen darunter bleiben sichtbar
        for o in cyd_parts:
            if o.name.startswith('TFT') or 'Screen' in o.name or 'Display' in o.name: o.hide_render = True
        xray([o for o in cyd_parts if o.name.startswith('CYD Platine')], 0.9)
        world_hdri(0.9, 30); sun('Key', (28, 0, 20), 2.6, 6); sun('Fill', (55, 0, 200), 0.6, 30)
        backdrop(-4.6, (0.55, 0.56, 0.58))
        cam = camera((90.0, 50.0, 10), 0, 90, 600, ortho=192)
    elif MODE == 'iso':
        set_offsets({'cyd': (0, 0, 36)}); hide(['cover', 'pad', 'mat', 'm3', 'm4']); build_wires()
        world_hdri(0.85, 140); sun('Key', (48, 0, 32), 2.8, 6); sun('Rim', (62, 0, 205), 1.2, 15)
        backdrop(-4.6)
        cam = camera((92, 52, 18), -32, 38, 820, 85)
    elif MODE == 'explosion':
        Z = dict(feet=-34, m5=-58, base=0, el=42, cyd=92, pad=126, m4=142, mat=152, cover=178, m3=200)
        offs = {g: (0, 0, Z['el']) for g in LAYER}
        offs.update({'cyd': (0, 0, Z['cyd']), 'cap': (0, 26, Z['cyd']), 'led': (0, -30, Z['el']), 'diff': (0, -46, Z['el'] - 6),
                     'pad': (0, 0, Z['pad']), 'mat': (0, 0, Z['mat']), 'cover': (0, 0, Z['cover']), 'm3': (0, 0, Z['m3']),
                     'm4': (0, 0, Z['m4']), 'm5': (0, 0, Z['m5']), 'feet': (0, 0, Z['feet']), 'keil': (0, 0, Z['el'] + 14)})
        set_offsets(offs); build_wires()
        world_hdri(0.85, 140); sun('Key', (50, 0, 35), 2.6, 6); sun('Rim', (62, 0, 205), 1.2, 15)
        backdrop(-60)
        cam = camera((90, 48, 88), -30, 22, 1500, 85)
    elif MODE == 'detail':
        set_offsets({'cyd': (0, 0, 30)}); hide(['cover', 'pad', 'mat', 'm3', 'm4']); build_wires()
        world_hdri(0.9, 160); sun('Key', (62, 0, 10), 2.4, 6); sun('Fill', (80, 0, 250), 1.0, 20)
        backdrop(-4.6)
        cam = camera((48, 52, 22), -62, 14, 330, 85)
        scn.cycles.samples = max(SAMPLES, 128)
    elif MODE == 'produkt':
        set_offsets({}); build_wires()
        world_hdri(0.7, 200, bg=(0.11, 0.115, 0.13)); sun('Key', (50, 0, -35), 2.6, 5); sun('Rim', (62, 0, 195), 2.0, 10)
        backdrop(-4.6, (0.16, 0.165, 0.18))
        cam = camera((92, 48, 8), -24, 24, 760, 85)
    render(OUT)
