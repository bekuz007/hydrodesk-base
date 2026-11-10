# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE
# Ansichten fuer die Uebersichtsbilder im README (gleiche Kameras wie die alten OpenSCAD/Blender-Bilder):
#   v_produkt | v_explosion | v_innen | v_teile
# Wird von real_scene.py per exec() geladen (gleiche Variablen). Schreibt neben das PNG eine .json mit den
# Ankerpunkten (normiert 0..1) fuer die Beschriftung (real_final.py). HD_NO_RENDER=1: nur Anker, kein Rendern.
import json, numpy as np
VIEW = MODE[2:]
scn.render.resolution_x, scn.render.resolution_y = 2560, 1440
LIFT_IN = float(os.environ.get('HD_LIFT', '60'))

# ---------- Hilfen ----------
def dashed(p0, p1, dash=3.0, gap=2.2, r=0.25, col=None):
    CUR[0] = C_ENV
    p0 = Vector(p0); p1 = Vector(p1); Ln = (p1 - p0).length; t = 0
    gm = mat('Hilfslinie', (0, 0, 0), 1.0, emis=(0.12, 0.13, 0.15), estr=1.0)
    while t < Ln:
        a = p0 + (p1 - p0).normalized()*t; b = p0 + (p1 - p0).normalized()*min(t + dash, Ln)
        cyl('Hilfslinie', a.x, a.y, min(a.z, b.z), 2*r, abs(b.z - a.z), gm, 8)
        t += dash + gap
    CUR[0] = C_EL

def group_of(o):
    p = o
    while p is not None:
        if p.name.startswith('G_'): return p.name[2:]
        p = p.parent
    if C_KAB in o.users_collection: return 'cables'
    return 'other'

def proj_np(P, cam):
    """Weltpunkte (N,3) -> normierte Bildkoordinaten (u: 0..1 links->rechts, v: 0..1 oben->unten), Tiefe"""
    M = np.array(cam.matrix_world.inverted()); C = P @ M[:3, :3].T + M[:3, 3]
    W_, H_ = scn.render.resolution_x, scn.render.resolution_y; cd = cam.data
    if cd.type == 'ORTHO':
        x = C[:, 0]/cd.ortho_scale; y = C[:, 1]/cd.ortho_scale*(W_/H_)
    else:
        k = cd.lens/cd.sensor_width; z = -C[:, 2]; x = k*C[:, 0]/z; y = k*C[:, 1]/z*(W_/H_)
    return np.stack([0.5 + x + cd.shift_x, 0.5 - (y + cd.shift_y*W_/H_)], 1), -C[:, 2]

def scene_geo():
    dg = bpy.context.evaluated_depsgraph_get(); G = {}; V_ = []; T_ = []; n = 0
    for o in bpy.data.objects:
        if o.type not in ('MESH', 'CURVE') or o.hide_render or C_ENV in o.users_collection: continue
        eo = o.evaluated_get(dg); me = eo.to_mesh()
        if len(me.vertices) == 0: eo.to_mesh_clear(); continue
        me.calc_loop_triangles()
        co = np.empty(len(me.vertices)*3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        Mw = np.array(o.matrix_world); w = co @ Mw[:3, :3].T + Mw[:3, 3]
        tri = np.empty(len(me.loop_triangles)*3, np.int32); me.loop_triangles.foreach_get('vertices', tri)
        V_.append(w); T_.append(tri.reshape(-1, 3) + n); n += len(w); eo.to_mesh_clear()
        G.setdefault(group_of(o), []).append(w)
    allv = np.concatenate(V_); allt = np.concatenate(T_)
    bvh = BVHTree.FromPolygons([tuple(v) for v in allv.tolist()], [tuple(t) for t in allt.tolist()])
    return {k: np.concatenate(v) for k, v in G.items()}, bvh, allv

def make_anchors(cam, specs, tag_extra=None):
    """specs: key -> (gruppe, Ziel-Weltpunkt oder None). Ergebnis: key -> [u, v]; Ziel = naechster SICHTBARER Punkt"""
    bpy.context.view_layer.update()
    G, bvh, allv = scene_geo()
    cl = np.array(cam.matrix_world.translation); fwd = np.array(cam.matrix_world.to_quaternion() @ Vector((0, 0, -1)))
    def visible(p):
        if cam.data.type == 'ORTHO': o_ = Vector(p - fwd*1500); d_ = Vector(fwd); dist = 1500.0
        else:
            d = p - cl; dist = float(np.linalg.norm(d)); o_ = Vector(cl); d_ = Vector(d/dist)
        h = bvh.ray_cast(o_, d_, dist + 5)
        return h[0] is not None and abs(h[3] - dist) < 0.45
    out = {}; rng = np.random.default_rng(1)
    for key, (g, tgt) in specs.items():
        if g not in G: print('ANKER fehlt Gruppe', g, key); continue
        P = G[g]; found = None
        if tgt is not None:
            order = np.argsort(np.linalg.norm(P - np.array(tgt), axis=1))
            for i in order[:4000]:
                if visible(P[i]): found = P[i]; break
        else:
            S = P[rng.choice(len(P), min(len(P), 3000), replace=False)]
            vis = np.array([visible(p) for p in S])
            if vis.any():
                S = S[vis]; uv, _ = proj_np(S, cam); c = uv.mean(0)
                found = S[np.argmin(np.linalg.norm(uv - c, axis=1))]
        if found is None: print('ANKER unsichtbar', key, g); continue
        uv, _ = proj_np(found[None], cam); out[key] = [float(uv[0, 0]), float(uv[0, 1])]
    uv, _ = proj_np(allv, cam)
    bbox = [float(uv[:, 0].min()), float(uv[:, 1].min()), float(uv[:, 0].max()), float(uv[:, 1].max())]
    return out, bbox

def finish(cam, specs, extra=None):
    anc, bbox = make_anchors(cam, specs)
    if extra: anc.update(extra)
    json.dump({'anchors': anc, 'bbox': bbox}, open(OUT.replace('.png', '.json'), 'w'), indent=1)
    print('ANKER', len(anc), 'bbox', [round(b, 3) for b in bbox])
    if not os.environ.get('HD_NO_RENDER'): render(OUT)

def T(g, p): return np.array(p, float) + np.array(goff(g))

# ---------- Detailbilder (gleiche Kameras wie die OpenSCAD-Vorschauen in gehaeuse/render.sh) ----------
DETAIL = {   # Name: (OpenSCAD --camera: Ziel x,y,z, Drehung rx, rz, Abstand)
    'fet': ((61, 55, 6), 50, 200, 95), 'schalter': ((0, 27, 9), 85, 270, 60),
    'kappe_ein': ((29, 100, 15), 72, 205, 140), 'kappe_offen': ((29, 104, 15), 72, 205, 160),
    'diffusor': ((40, -8, 10), 70, 330, 150)}
def ocam(name):
    t, rx, rz, dist = DETAIL[name]
    c = camera(t, -rz, 90 - rx, dist, 60.3)          # OpenSCAD: 22,5 Grad vertikal -> Sensor 24 mm hoch, Brennweite 60,3 mm
    c.data.sensor_fit = 'VERTICAL'; c.data.sensor_height = 24
    scn.render.resolution_x, scn.render.resolution_y = 1600, 1100
    return c
def detail_light(rotz=140, key=2.6):
    world_hdri(0.9, rotz); sun('Key', (48, 0, 32), key, 6); sun('Fill', (62, 0, 205), 1.0, 15)
    backdrop(-4.6, (0.66, 0.67, 0.69))

# ---------- Ansichten ----------
if VIEW == 'explosion':
    Z = dict(feet=-34, m5=-58, base=0, el=42, cyd=92, pad=126, m4=142, mat=152, cover=178, m3=200)
    offs = {g: (0, 0, Z['el']) for g in LAYER}
    offs.update({'cyd': (0, 0, Z['cyd']), 'cap': (0, 26, Z['cyd']), 'led': (0, -30, Z['el']), 'diff': (0, -46, Z['el'] - 6),
                 'pad': (0, 0, Z['pad']), 'mat': (0, 0, Z['mat']), 'cover': (0, 0, Z['cover']), 'm3': (0, 0, Z['m3']),
                 'm4': (0, 0, Z['m4']), 'm5': (0, 0, Z['m5']), 'feet': (0, 0, Z['feet']), 'keil': (0, 0, Z['el'] + 14)})
    set_offsets(offs); build_wires()
    world_hdri(0.85, 140); sun('Key', (50, 0, 35), 2.6, 6); sun('Rim', (62, 0, 205), 1.2, 15)
    backdrop(-60, (0.66, 0.67, 0.69))
    # Hilfslinien (wie im alten Bild)
    for (x, y) in cov_bosses: dashed((x, y, 21), (x, y, H + Z['m3'] - 12))
    for (u, v) in cyd_holes_uv:
        x, y = cyd_x + u, cyd_y + v
        dashed((x, y, 18.4), (x, y, cyd_pcb_z + Z['cyd'])); dashed((x, y, cyd_pcb_z + cyd_t + Z['cyd'] + 1.5), (x, y, H + Z['m3'] - 12))
    for yy in [12, 27]: dashed((pad_cx, yy, 17.7 + Z['el']), (pad_cx, yy, pad_top_z + Z['m4'] - 10))
    for yy in [70, 85]: dashed((pad_cx, yy, Z['m5'] + 12), (pad_cx, yy, lc_z0 + Z['el']))
    for (x, y) in feet_pos: dashed((x, y, Z['feet']), (x, y, 0))
    cam = camera((90, 50, 93), -28, 24, 1800, 100)
    specs = {'cover': ('cover', T('cover', (178, 60, 25))), 'cap': ('cap', T('cap', (14.5, 101.2, 17))), 'cyd': ('cyd', None),
             'tc': ('tc', None), 'fet': ('fet', None), 'sw': ('sw', None), 'keil': ('keil', None), 'cmp': ('cmp', None),
             'bat': ('bat', None), 'boost': ('pol', None), 'base_l': ('base', T('base', (2, 40, 14))), 'led': ('led', None),
             'diff': ('diff', None), 'feet': ('feet', T('feet', (169, 11, 0))), 'm3': ('m3', T('m3', (175.5, 80, H))),
             'mat': ('mat', None), 'm4': ('m4', T('m4', (pad_cx + 4, 27, pad_top_z))), 'pad': ('pad', T('pad', (170, 70, 24.6))),
             'lc': ('lc', None), 'hx': ('hx', None), 'rs': ('rs', None), 'm5': ('m5', T('m5', (pad_cx + 5, 70, 0)))}
    finish(cam, specs)

elif VIEW == 'innen':
    set_offsets({'cyd': (0, 0, LIFT_IN)}); hide(['cover', 'pad', 'mat', 'm3', 'm4']); build_wires()
    world_hdri(0.85, 140); sun('Key', (45, 0, -40), 2.8, 8); sun('Rim', (62, 0, 205), 1.2, 15)
    backdrop(-4.6, (0.66, 0.67, 0.69))
    for (u, v) in cyd_holes_uv:
        x, y = cyd_x + u, cyd_y + v; dashed((x, y, 18.4), (x, y, cyd_pcb_z + LIFT_IN))
    cam = camera((96, 52, 46), -25, 50, 1280, 100)
    specs = {'cyd': ('cyd', None), 'bat': ('bat', None), 'boost': ('pol', None), 'cmp': ('cmp', None), 'diff': ('diff', None),
             'base_l': ('base', T('base', (2, 40, 14))), 'tc': ('tc', None), 'fet': ('fet', None), 'sw': ('sw', None),
             'boss': ('base', T('base', (175.5, 80, 21))), 'hx': ('hx', None), 'lc': ('lc', None), 'rs': ('rs', None),
             'cables': ('cables', T('cables', (100, 93, 3.5)))}
    finish(cam, specs)

elif VIEW == 'produkt':
    set_offsets({}); build_wires()
    world_hdri(0.7, 200, bg=(0.11, 0.115, 0.13)); sun('Key', (50, 0, -35), 2.6, 5); sun('Rim', (62, 0, 195), 2.0, 10)
    backdrop(-4.6, (0.035, 0.037, 0.043))
    # angedeutete Flasche (nicht im Lieferumfang), wie im alten Produktbild
    CUR[0] = C_ENV
    glass = mat('Glas', (0.95, 0.97, 1.0), 0.03, trans=1.0, ior=1.06)
    water = mat('Wasser', (0.55, 0.80, 1.0), 0.08, trans=1.0, ior=1.08)
    capm = mat('Flaschendeckel', srgb((205, 208, 212)), 0.35, 0.5, coat=0.3)
    zb = pad_top_z + 1.2 + 0.5; R = 33; cxp, cyp = pad_cx, 50.0
    prof = [(0, 0), (R-3, 0), (R-0.5, 1.5), (R, 5), (R, 122), (R-5, 136), (13, 148), (12, 153), (0, 153)]
    lathe('Flasche', prof, glass, 96, cxp, cyp, zb)
    lathe('Flaschendeckel', [(0, 152), (13.5, 152), (14, 153), (14, 166), (13.5, 167), (0, 167)], capm, 64, cxp, cyp, zb)
    fill = 4 + 118*0.56
    lathe('Wasser', [(0, 1.5), (R-2.0, 1.5), (R-1.2, 4), (R-1.2, fill), (0, fill)], water, 96, cxp, cyp, zb)
    CUR[0] = C_EL
    dm = MATS['Diffusor'].node_tree.nodes['Principled BSDF']   # Lichtlinie: milchiger Diffusor, von hinten blau beleuchtet (kein ausgebranntes Weiss)
    dm.inputs['Base Color'].default_value = (0.22, 0.30, 0.55, 1); dm.inputs['Emission Color'].default_value = (0.12, 0.42, 1.0, 1)
    dm.inputs['Emission Strength'].default_value = float(os.environ.get('HD_GLOWV', '2.2'))
    cam = camera((100, 48, 78), -22, 20, 1320, 100); cam.data.shift_x = -0.16
    finish(cam, {})

elif VIEW == 'teile':
    # nur die Teile, wie gekauft/gedruckt (ohne Litzen), auf einer Schneidematte mit 1-cm-Raster
    set_offsets({})
    MW, MH = 540, 330
    world_hdri(0.85, 140); sun('Key', (35, 0, -30), 2.6, 8); sun('Rim', (62, 0, 205), 1.0, 15)
    CUR[0] = C_ENV
    bm_ = mat('Teile-Boden', (0.5, 0.5, 0.5), 0.9, emis=(0.57, 0.58, 0.60), estr=1.0)   # ohne Licht/Schatten, sonst Geisterfleck vom Gehaeuse
    bm_.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0, 0, 0, 1)
    boden = box('Boden', -1500, -1500, -6.05, 3600, 3600, 4, bm_, 0.0, 1)
    matobj = box('Schneidematte', 0, 0, -2, MW, MH, 2, None, 0.8, 3)
    matobj.data.materials.append(tex_mat('Matte', 'cutting_mat.png', rough=0.75))
    me = matobj.data; uvl = me.uv_layers.new()
    for p in me.polygons:
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; uvl.data[li].uv = (v.x/MW, v.y/MH)
    CUR[0] = C_EL
    # Schrauben und Fuesse einzeln: je Schraube/Fuss eine eigene Baugruppe
    PIECES = {}
    def split_group(g, prefix):
        e = GROUPS[g]; kids = [o for o in e.children_recursive if o.type == 'MESH']; by = {}
        for o in kids:
            key = o.name.replace(' Kopf', '').replace(' Innensechskant', ''); by.setdefault(key, []).append(o)
        for i, (k, objs) in enumerate(sorted(by.items())):
            pe = bpy.data.objects.new('P_%s%d' % (prefix, i), None); GCOLL[g].objects.link(pe)
            for o in objs:
                mw = o.matrix_world.copy(); o.parent = pe; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_world = mw
            PIECES['%s%d' % (prefix, i)] = (pe, objs)
    split_group('m3', 'm3_'); split_group('m4', 'm4_'); split_group('m5', 'm5_'); split_group('feet', 'ft_')
    def meshes_of(e): return [o for o in e.children_recursive if o.type == 'MESH' and not o.hide_render]
    def wbbox(e):
        bpy.context.view_layer.update(); mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
        for o in meshes_of(e):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                mn = Vector((min(mn[i], w[i]) for i in range(3))); mx = Vector((max(mx[i], w[i]) for i in range(3)))
        return mn, mx
    def lay(name, x0, y0, rot=(0, 0, 0)):
        e = GROUPS[name] if name in GROUPS else PIECES[name][0]
        Rb = G_BASEMAT[name].to_3x3() if name in GROUPS else Matrix.Identity(3)
        Rx = Euler([math.radians(a) for a in rot]).to_matrix()
        e.matrix_basis = (Rx @ Rb).to_4x4()
        mn, mx = wbbox(e)
        e.matrix_basis = Matrix.Translation((x0 - mn.x, y0 - mn.y, 0.02 - mn.z)) @ (Rx @ Rb).to_4x4()
    for g in ('m3', 'm4', 'm5', 'feet'): hide([g]) if False else None
    for g in ('m3', 'm4', 'm5', 'feet'): GROUPS[g].hide_render = False
    LAYOUT = {'cover': (15, 214, (0, 0, 0)), 'base': (210, 214, (0, 0, 0)), 'pad': (410, 219, (0, 0, 0)),
              'cyd': (15, 102, (0, 0, 0)), 'bat': (82, 118, (0, 0, 0)), 'mat': (135, 100, (0, 0, 0)),
              'rs': (238, 118, (0, 0, 0)), 'lc': (300, 162, (0, 0, -90)), 'hx': (300, 112, (0, 0, 0)),
              'tc': (398, 140, (0, 0, 0)), 'fet': (425, 138, (0, 0, 0)), 'cmp': (462, 138, (0, 0, 0)), 'pol': (398, 100, (0, 0, 0)),
              'sw': (440, 104, (0, -90, 0)), 'keil': (472, 104, (0, 0, 0)), 'led': (15, 36, (-90, 0, 0)),
              'diff': (15, 52, (-90, 0, 0)), 'cap': (452, 27, (-90, 0, 0))}
    LAYOUT.update(json.loads(os.environ.get('HD_LAYOUT', '{}')))
    for g, (x0, y0, r) in LAYOUT.items(): lay(g, x0, y0, tuple(r))
    sx = 212
    for i in range(8): lay('m3_%d' % i, sx + i*9, 28, (90, 0, 0))
    for i in range(2): lay('m4_%d' % i, sx + 80 + i*12, 28, (90, 0, 0))
    for i in range(2): lay('m5_%d' % i, sx + 110 + i*14, 28, (90, 0, 0))
    for i in range(4): lay('ft_%d' % i, 370 + i*17, 30)
    for g in ('m3', 'm4', 'm5', 'feet'): GROUPS[g].hide_render = False
    for n_ in ('div',): pass
    if os.environ.get('HD_NOBODEN'): boden.hide_render = True
    if os.environ.get('HD_HIDE'): hide(os.environ['HD_HIDE'].split(','))
    cam = camera((MW/2 + 95, MH/2 - 4, 0), 0, 68, 3000, 100, ortho=760)
    TE = {}
    for g in ['cover', 'base', 'pad', 'cyd', 'bat', 'mat', 'rs', 'lc', 'hx', 'tc', 'fet', 'cmp', 'pol', 'led', 'cap', 'diff', 'sw', 'keil']:
        TE[g] = wbbox(GROUPS[g])
    allp = {k: wbbox(v[0]) for k, v in PIECES.items()}
    sm = [v for k, v in allp.items() if k[:2] in ('m3', 'm4', 'm5')]; ft = [v for k, v in allp.items() if k.startswith('ft')]
    def merge(L_):
        return (Vector((min(a[0][i] for a in L_) for i in range(3))), Vector((max(a[1][i] for a in L_) for i in range(3))))
    TE['screws'] = merge(sm); TE['feet'] = merge(ft)
    pts = {}
    for g, (mn, mx) in TE.items():
        pts[g + '_tl'] = Vector((mn.x, mx.y, mx.z)); pts[g + '_bc'] = Vector(((mn.x + mx.x)/2, mn.y, 0)); pts[g + '_c'] = Vector(((mn.x + mx.x)/2, (mn.y + mx.y)/2, mx.z))
        print('MASS %-7s %6.1f x %6.1f x %5.1f mm' % (g, mx.x - mn.x, mx.y - mn.y, mx.z - mn.z))
    pts['mat_tl_corner'] = Vector((0, MH, 0)); pts['mat_br_corner'] = Vector((MW, 0, 0))
    for k in ('ft_0', 'm3_0'): pass
    bpy.context.view_layer.update()
    keys = list(pts); uv, _ = proj_np(np.array([list(pts[k]) for k in keys]), cam)
    extra = {k: [float(uv[i, 0]), float(uv[i, 1])] for i, k in enumerate(keys)}
    finish(cam, {}, extra)

elif VIEW == 'fet':      # Bodenwanne mit Schalter, Klemmkeilen und FET-Platine (ohne CYD/Akku), wie OpenSCAD "sw_detail"
    set_offsets({}); hide(['cover', 'pad', 'mat', 'm3', 'm4', 'cyd', 'bat', 'cap'])
    detail_light(140, 1.5); ocam('fet'); render(OUT)
elif VIEW == 'schalter':
    set_offsets({}); hide(['pad', 'mat', 'm3', 'm4']); detail_light(); ocam('schalter'); render(OUT)
elif VIEW in ('kappe_ein', 'kappe_offen'):
    set_offsets({'cap': (0, 14, 0)} if VIEW == 'kappe_offen' else {}); detail_light(); ocam(VIEW); render(OUT)
elif VIEW == 'diffusor':
    set_offsets({'diff': (0, -16, 0)}); detail_light(); ocam('diffusor'); render(OUT)

elif VIEW == 'fetsolo':   # Vergleich: FET-Platine allein (Prueffoto)
    set_offsets({}); hide([g for g in GROUPS if g != 'fet']); world_hdri(0.9, 140); sun('Key', (48, 0, 32), 2.6, 6)
    cam = camera((50.7, 43, 8), -20, 40, 110, 85); scn.render.resolution_x, scn.render.resolution_y = 1200, 800; render(OUT)
