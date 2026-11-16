# -*- coding: utf-8 -*-
# Blender 4.2 headless: 3D-Ansichten Lötschritt 4 (Stromweg) und 6 (LED + Regensensor)
# Aufruf: blender -b -P loeten_3d_scene.py -- 4|6 out.png [samples] [eevee]
import bpy, sys, math, json, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from loeten_3d_common import (
    prepare_fresh_scene, apply_renames, group_by_prefix, pack_and_save, set_view_to_camera,
)
TEX = os.path.join(HERE, "tex")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

argv = sys.argv[sys.argv.index("--") + 1:]
MODE = argv[0]
OUT = argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
USE_EEVEE = len(argv) > 3 and argv[3].lower() in ("eevee", "preview", "1")

SCENE_NAMES = {"4": "Loetschritt_4_Stromweg", "4b": "Loetschritt_4_Stromweg",
               "6": "Loetschritt_6_LED_Regensensor", "6b": "Loetschritt_6_LED_Regensensor"}
BLEND_NAMES = {"4": "loeten_4b_stromweg_3d.blend", "4b": "loeten_4b_stromweg_3d.blend",
               "6": "loeten_6b_led_regen_3d.blend", "6b": "loeten_6b_led_regen_3d.blend"}
scn = prepare_fresh_scene(SCENE_NAMES.get(MODE, "Szene"))
if USE_EEVEE:
    scn.render.engine = "BLENDER_EEVEE_NEXT"
    ee = getattr(scn, "eevee", None)
    if ee is not None:
        if hasattr(ee, "taa_render_samples"):
            ee.taa_render_samples = max(16, min(SAMPLES, 64))
        elif hasattr(ee, "taa_samples"):
            ee.taa_samples = max(16, min(SAMPLES, 64))
else:
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = SAMPLES
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = "OPENIMAGEDENOISE"
scn.render.resolution_x, scn.render.resolution_y = 2000, 1500
scn.render.film_transparent = True
scn.view_settings.view_transform = "AgX"
scn.view_settings.look = "AgX - Medium High Contrast"
coll = scn.collection

# ---------- materials ----------
MATS = {}
def srgb(c):
    return tuple((v / 255) ** 2.2 for v in c)

def mat(name, col, rough=0.5, metal=0.0, coat=0.0, trans=0.0, alpha=1.0, emis=None, estr=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    rgb = col if (isinstance(col[0], float) and col[0] <= 1.0) else srgb(col)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
        b.inputs["IOR"].default_value = 1.45
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "HASHED"
    if emis is not None:
        er = emis if (isinstance(emis[0], float) and emis[0] <= 1.0) else srgb(emis)
        b.inputs["Emission Color"].default_value = (*er, 1)
        b.inputs["Emission Strength"].default_value = estr
    MATS[name] = m
    return m

def tex_mat(name, path, rough=0.4, coat=0.3):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    img = bpy.data.images.load(path)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    MATS[name] = m
    return m

NETC = dict(
    bat=(215, 30, 30),
    gnd=(25, 25, 25),
    gate=(90, 90, 160),
    vin=(240, 130, 0),
    v5=(200, 0, 120),
    led=(215, 30, 30),
    din=(20, 150, 60),
    white=(230, 230, 230),
    teal=(0, 150, 150),
    v33=(215, 30, 30),
    dark=(40, 40, 40),
    plate=(50, 50, 50),
)

M = dict(
    pcb=mat("pcb", srgb((30, 110, 60)), 0.45, coat=0.4),
    pcb_bl=mat("pcb_bl", srgb((25, 70, 160)), 0.45, coat=0.4),
    pcb_te=mat("pcb_te", srgb((20, 85, 155)), 0.45, coat=0.4),
    pcb_ye=mat("pcb_ye", srgb((220, 185, 20)), 0.45, coat=0.3),
    fr4=mat("fr4", srgb((40, 90, 50)), 0.5),
    tin=mat("tin", (0.78, 0.78, 0.80), 0.22, 1.0),
    gold=mat("gold", (0.95, 0.70, 0.30), 0.25, 1.0),
    hole=mat("hole", (0.02, 0.02, 0.02), 0.8),
    purple=mat("adapter", srgb((105, 40, 140)), 0.4, coat=0.4),
    black=mat("black", (0.02, 0.02, 0.022), 0.4),
    plastic=mat("plastic", (0.03, 0.03, 0.03), 0.5),
    res=mat("res", srgb((210, 195, 150)), 0.45),
    elko=mat("elko", srgb((30, 70, 170)), 0.35, coat=0.5),
    stripe=mat("stripe", srgb((210, 215, 225)), 0.4),
    alu=mat("alu", (0.8, 0.81, 0.83), 0.3, 1.0),
    rubber=mat("rubber", (0.04, 0.04, 0.04), 0.9),
    lead=mat("lead", (0.75, 0.75, 0.77), 0.25, 1.0),
    steel=mat("steel", (0.7, 0.72, 0.74), 0.28, 1.0),
    nickel=mat("nickel", (0.75, 0.76, 0.78), 0.25, 1.0),
    ferrite=mat("ferrite", srgb((50, 45, 40)), 0.55),
    epoxy=mat("epoxy", (0.04, 0.04, 0.045), 0.4),
    cob_fpc=mat("cob_fpc", srgb((235, 232, 220)), 0.5),
    cob_sil=mat("cob_sil", srgb((248, 246, 238)), 0.3),
    pot=mat("pot", srgb((30, 70, 150)), 0.4),
    potw=mat("potw", srgb((230, 230, 230)), 0.4),
    led_r=mat("led_r", srgb((180, 20, 20)), 0.3, emis=(255, 40, 40), estr=0.4),
    led_b=mat("led_b", srgb((20, 40, 180)), 0.3, emis=(40, 80, 255), estr=0.4),
    led_g=mat("led_g", srgb((20, 140, 40)), 0.3, emis=(40, 220, 60), estr=0.4),
    shrink_k=mat("shrink_k", srgb((25, 25, 25)), 0.25, trans=0.25, alpha=0.88),
    shrink_r=mat("shrink_r", srgb((140, 20, 20)), 0.25, trans=0.25, alpha=0.88),
    shrink_g=mat("shrink_g", srgb((20, 90, 40)), 0.25, trans=0.25, alpha=0.88),
    shrink_c=mat("shrink_c", srgb((40, 40, 45)), 0.25, trans=0.35, alpha=0.8),
    text=mat("text", (0.95, 0.95, 0.97), 0.4),
    text_y=mat("text_y", srgb((255, 230, 80)), 0.4),
    txtk=mat("txtk", (0.08, 0.08, 0.08), 0.4),
)
BAND = {0: (0, 0, 0), 1: (120, 60, 20), 2: (220, 0, 0), 3: (255, 120, 0),
        4: (255, 210, 0), 5: (0, 150, 0), 6: (0, 0, 220), 7: (130, 40, 190),
        "gold": (200, 160, 60)}

def wire_mat(net):
    name = "litze_" + net
    if name in MATS:
        return MATS[name]
    return mat(name, srgb(NETC[net]), 0.45, coat=0.2)

# ---------- geometry helpers ----------
def link(o, m=None):
    if o.name not in coll.objects:
        coll.objects.link(o)
    if m is not None and m not in list(o.data.materials):
        o.data.materials.append(m)
    return o

def mesh(name, v, f, m, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return link(bpy.data.objects.new(name, me), m)

def box(name, x0, y0, z0, w, l, h, m):
    v = [(x0, y0, z0), (x0 + w, y0, z0), (x0 + w, y0 + l, z0), (x0, y0 + l, z0),
         (x0, y0, z0 + h), (x0 + w, y0, z0 + h), (x0 + w, y0 + l, z0 + h), (x0, y0 + l, z0 + h)]
    return mesh(name, v, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], m)

def cbox(name, cx, cy, z0, w, l, h, m):
    return box(name, cx - w / 2, cy - l / 2, z0, w, l, h, m)

def box_tex(name, x0, y0, z0, w, l, h, side_m, tex_path):
    o = box(name, x0, y0, z0, w, l, h, side_m)
    tm = tex_mat(name + "_top", tex_path)
    o.data.materials.append(tm)
    me = o.data
    uv = me.uv_layers.new()
    # normals not required in 4.2
    for p in me.polygons:
        is_top = all(me.vertices[i].co.z >= z0 + h - 1e-4 for i in p.vertices)
        p.material_index = 1 if is_top else 0
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x - x0) / max(w, 1e-6), (co.y - y0) / max(l, 1e-6))
    return o

def cyl(name, cx, cy, z0, d, h, m, n=32, axis="z"):
    v = []
    for z in (0, h):
        for i in range(n):
            a = 2 * math.pi * i / n
            v.append((d / 2 * math.cos(a), d / 2 * math.sin(a), z))
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [
        (i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)
    ]
    o = mesh(name, v, f, m, smooth=True)
    if axis == "x":
        o.rotation_euler = (0, math.pi / 2, 0)
    elif axis == "y":
        o.rotation_euler = (math.pi / 2, 0, 0)
    o.location = (cx, cy, z0)
    return o

def tube(name, pts, m, r=0.3):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = r
    cd.bevel_resolution = 4
    cd.use_fill_caps = True
    sp = cd.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, cd)
    coll.objects.link(o)
    cd.materials.append(m)
    return o

def sphere(name, c, r, m, sz=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=c, segments=20, ring_count=12)
    o = bpy.context.active_object
    o.scale = (1, 1, sz)
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o

def text3d(name, txt, loc, size=2.2, m=None, rot=(0, 0, 0), align="CENTER", extrude=0.04):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = txt
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    try:
        cu.font = bpy.data.fonts.load(FONT)
    except Exception:
        pass
    o = bpy.data.objects.new(name, cu)
    o.location = loc
    o.rotation_euler = rot
    coll.objects.link(o)
    if m is None:
        m = M["text"]
    cu.materials.append(m)
    return o

def pad(name, x, y, z, d=2.4, t=0.12):
    cyl(name, x, y, z, d, t, M["tin"], 20)
    cyl(name + "_loch", x, y, z + t - 0.02, 0.9, 0.04, M["hole"], 14)
    sphere(name + "_zinn", (x, y, z + t), 0.85, M["tin"], 0.5)
    return (x, y, z + t + 0.4)

def shrink(name, p0, p1, m, r=1.15):
    # short tube between two points
    return tube(name, [p0, p1], m, r)

# resistor color bands: (digit, digit, multiplier) + gold
def resistor(name, p_a, p_b, bands, body_r=1.15, lift=0):
    ax, ay, az = p_a
    bx, by, bz = p_b
    # standing if mostly vertical and close in xy
    dx, dy, dz = bx - ax, by - ay, bz - az
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    # body along the lead-to-lead path, shortened
    # Use a horizontal or vertical cylinder between ends with leads
    mid = ((ax + bx) / 2, (ay + by) / 2, (az + bz) / 2)
    # default: axial along the vector
    # We'll build in local Z and rotate
    L = 6.2
    z0 = 0
    # place body at midpoint, orient from A to B
    o = cyl(name, 0, 0, -L / 2, body_r * 2, L, M["res"], 24)
    # orientation: default cyl along +Z; we need along (dx,dy,dz)
    v = Vector((dx, dy, dz))
    if v.length > 1e-6:
        o.rotation_euler = v.normalized().to_track_quat("Z", "Y").to_euler()
    o.location = mid
    # end caps
    for sign in (-1, 1):
        cap = sphere(name + "k", (0, 0, 0), body_r * 1.15, M["res"], 0.7)
        cap.location = Vector(mid) + v.normalized() * (L / 2 * 0.92 * sign)
    # bands along body
    cols = [BAND[bands[0]], BAND[bands[1]], BAND[bands[2]], BAND["gold"]]
    offs = [-1.6, -0.6, 0.4, 1.6]
    for k, (off, cc) in enumerate(zip(offs, cols)):
        ring = cyl(name + "band%d" % k, 0, 0, -0.28, body_r * 2.08, 0.5,
                   mat("band%s_%s" % (name, k), srgb(cc), 0.5), 20)
        ring.rotation_euler = o.rotation_euler
        ring.location = Vector(mid) + v.normalized() * off
    # leads
    tube(name + "b1", [p_a, (ax + 0.15 * dx, ay + 0.15 * dy, az + 0.15 * dz)], M["lead"], 0.22)
    tube(name + "b2", [p_b, (bx - 0.15 * dx, by - 0.15 * dy, bz - 0.15 * dz)], M["lead"], 0.22)
    return mid

def standing_res(name, x, y, bands, z0=0.2, L=6.4):
    """Upright resistor, first lead at (x,y), second lead offset in +x by 2.54 later via jumper."""
    cyl(name, x, y, z0 + 0.4, 2.3, L - 0.8, M["res"])
    sphere(name + "k1", (x, y, z0 + 0.5), 1.2, M["res"], 0.55)
    sphere(name + "k2", (x, y, z0 + L - 0.5), 1.2, M["res"], 0.55)
    zz = [z0 + L - 1.0, z0 + L - 1.8, z0 + L - 2.6, z0 + 1.3]
    cols = [BAND[bands[0]], BAND[bands[1]], BAND[bands[2]], BAND["gold"]]
    for zb, cc in zip(zz, cols):
        cyl(name + "band", x, y, zb, 2.36, 0.5, mat("band_%s_%s" % (name, str(cc)), srgb(cc), 0.5))
    tube(name + "bein", [(x, y, -0.8), (x, y, z0 + 0.5)], M["lead"], 0.25)
    return (x, y, z0 + L + 1.2)

# ---------- anchors ----------
ANCH = {}

# =====================================================================
#  STEP 4 — Stromweg
# =====================================================================
def build_step4():
    T = 1.2

    # --- TC4056 at origin, pads toward +X / near y=0 ---
    # Board 17 x 26, USB at y=26
    tx0, ty0 = 0.0, 0.0
    box_tex("TC4056", tx0, ty0, 0, 17, 26, T, M["pcb_te"], os.path.join(TEX, "tc4056.png"))
    # USB-C at far end (y=26)
    u0 = tx0 + 8.5 - 4.5
    box("TC4056_USB_C", u0, ty0 + 25.2, T, 9.0, 2.2, 3.2, M["nickel"])
    box("TC4056_USB_C_innen", u0 + 0.6, ty0 + 26.4, T + 0.5, 7.8, 1.4, 2.2, M["black"])
    # ICs
    cbox("TC4056_IC", tx0 + 8.5, ty0 + 14.0, T, 6.0, 4.9, 1.5, M["epoxy"])
    cbox("TC4056_LED_rot", tx0 + 15.2, ty0 + 18.5, T, 0.8, 1.6, 0.5, M["led_r"])
    cbox("TC4056_LED_blau", tx0 + 15.2, ty0 + 13.5, T, 0.8, 1.6, 0.5, M["led_b"])
    # pads OUT- B- B+ OUT+ at y=2.4
    pads_tc = [("tc_out-", 1.6, "OUT−"), ("tc_b-", 5.5, "B−"),
               ("tc_b+", 11.5, "B+"), ("tc_out+", 15.4, "OUT+")]
    for key, xmm, lab in pads_tc:
        ANCH[key] = pad(key, tx0 + xmm, ty0 + 2.4, T, 2.2)
    ANCH["TC4056"] = (tx0 + 8.5, ty0 + 16.0, T + 4.0)
    text3d("Beschriftung_TC4056", "TC4056", (tx0 + 8.5, ty0 + 16.5, T + 0.12), 2.0, M["text"], (0, 0, 0))

    # --- Q2 on a simplified FET board ---
    # Place to the right of TC4056
    qx0, qy0 = 28.0, 6.0
    qw, ql = 30.0, 24.0
    box_tex("FET_Platine_Q2", qx0, qy0, 0, qw, ql, 1.6, M["pcb"], os.path.join(TEX, "q2board.png"))
    # proto holes (decorative)
    for r in range(3, 8):
        for c in range(1, 10):
            x = qx0 + 3.0 + c * 2.54
            y = qy0 + 3.0 + r * 2.54
            cyl("loch", x, y, 1.58, 1.4, 0.05, M["tin"], 12)
            cyl("loch2", x, y, 1.62, 0.7, 0.02, M["hole"], 10)
    # SOT-23 adapter centered
    acx, acy = qx0 + 12.0, qy0 + 14.0
    ZA = 2.6
    cbox("Q2_Adapter", acx, acy, ZA, 12.7, 10.2, 1.6, M["purple"])
    for yy in (acy - 3.81, acy + 3.81):
        cbox("Stiftleiste", acx, yy, 0, 12.7, 2.5, ZA, M["plastic"])
        for i in range(5):
            x = acx - 5.08 + i * 2.54
            cbox("Stift", x, yy, -1.2, 0.64, 0.64, ZA + 1.6 + 1.2 + 1.0, M["gold"])
            sphere("ZinnA", (x, yy, ZA + 1.6), 0.5, M["tin"], 0.5)
    zc = ZA + 1.6
    cbox("Q2_Ein_Aus", acx, acy, zc + 0.1, 2.9, 1.6, 1.0, M["black"])
    for dx, s in ((-0.95, -1), (0.95, -1), (0, 1)):
        cbox("sotbein", acx + dx, acy + s * 1.15, zc + 0.04, 0.4, 0.9, 0.12, M["lead"])
    ANCH["Q2"] = (acx, acy, zc + 1.4)
    text3d("Beschriftung_Q2", "Q2", (acx, acy, zc + 1.25), 1.8, M["text"])

    # Connection pads on the right edge of the FET board: S, G, D
    # S and G near the adapter (source/gate row), D a bit lower (drain)
    # Place three large pads on the +X side for clear wiring
    s_xy = (qx0 + qw - 4.0, qy0 + 19.0)
    g_xy = (qx0 + qw - 4.0, qy0 + 13.5)
    d_xy = (qx0 + qw - 4.0, qy0 + 8.0)
    ANCH["Q2S"] = pad("Pad_Q2_S", s_xy[0], s_xy[1], 1.6, 2.6)
    ANCH["Q2G"] = pad("Pad_Q2_G", g_xy[0], g_xy[1], 1.6, 2.6)
    ANCH["Q2D"] = pad("Pad_Q2_D", d_xy[0], d_xy[1], 1.6, 2.6)
    text3d("Beschriftung_S", "S", (s_xy[0] - 4.2, s_xy[1], 1.75), 2.0, M["text"])
    text3d("Beschriftung_G", "G", (g_xy[0] - 4.2, g_xy[1], 1.75), 2.0, M["text"])
    text3d("Beschriftung_D", "D", (d_xy[0] - 4.2, d_xy[1], 1.75), 2.0, M["text"])
    # short traces on top from adapter area to pads (visual only, not extra nets)
    tube("trS", [(acx + 4.0, acy + 3.0, 1.72), (s_xy[0] - 1.2, s_xy[1], 1.72)],
         mat("tr_bat", srgb(NETC["bat"]), 0.3, 0.6), 0.35)
    tube("trG", [(acx + 4.0, acy, 1.72), (g_xy[0] - 1.2, g_xy[1], 1.72)],
         mat("tr_gate", srgb(NETC["gate"]), 0.3, 0.6), 0.35)
    tube("trD", [(acx + 4.0, acy - 3.0, 1.72), (d_xy[0] - 1.2, d_xy[1], 1.72)],
         mat("tr_vin", srgb(NETC["vin"]), 0.3, 0.6), 0.35)

    # 47 kΩ standing between S and G (on the board, toward the adapter)
    rx, ry = qx0 + qw - 9.5, qy0 + 16.2
    ANCH["R47"] = standing_res("Widerstand_47k", rx, ry, (4, 7, 3))
    # second lead jumper to G pad area
    tube("R47b2", [(rx, ry, 6.6), (rx, ry, 7.8), (g_xy[0] - 1.5, g_xy[1], 7.0),
                   (g_xy[0], g_xy[1], 3.0), (g_xy[0], g_xy[1], 1.8)], M["lead"], 0.22)
    # first lead already goes through board; solder to a pad that we connect to S
    # Add a small solder pad under R47 and a bridge to S
    pad("R47pad", rx, ry, 1.6, 2.0)
    tube("R47toS", [(rx, ry, 1.55), (s_xy[0], s_xy[1], 1.55)],
         mat("tr_bat2", srgb(NETC["bat"]), 0.3, 0.6), 0.35)

    # --- Ein/Aus-Schalter in front of the FET board (toward camera, -Y) ---
    # Enlarged slightly for readability (~1.8×), pins AUS Mitte AN left to right
    sx0, sy0, sz0 = 42.0, -20.0, 0.0
    box("Ein_Aus_Schalter", sx0 - 8.0, sy0 - 4.0, 0.0, 16.0, 8.0, 9.0, M["plastic"])
    # mounting lugs
    box("Schalter_Lasche_1", sx0 - 10.4, sy0 - 2.0, 6.5, 2.2, 4.0, 0.5, M["steel"])
    box("Schalter_Lasche_2", sx0 + 8.2, sy0 - 2.0, 6.5, 2.2, 4.0, 0.5, M["steel"])
    # slider (position AUS = left / -X), protruding toward -Y (camera)
    box("Schalter_Schieber", sx0 - 7.2, sy0 - 7.5, 4.5, 4.0, 4.0, 3.2, M["black"])
    # 3 pins on +Y side (toward the FET board), left to right: AUS, Mitte, AN
    pin_xs = [sx0 - 5.0, sx0, sx0 + 5.0]
    pin_keys = ["SW_AUS", "SW_MITTE", "SW_AN"]
    pin_labs = ["AUS", "Mitte", "AN"]
    for x, key, lab in zip(pin_xs, pin_keys, pin_labs):
        # pin sticking out +Y
        box("pin", x - 0.3, sy0 + 4.5, 3.8, 0.6, 5.0, 0.45, M["tin"])
        ANCH[key] = (x, sy0 + 9.2, 4.1)
        sphere("pinz", ANCH[key], 0.7, M["tin"], 0.6)
        text3d("t" + key, lab, (x, sy0 - 6.5, 11.2), 1.7, M["text_y"] if lab != "Mitte" else M["text"])
    ANCH["Schalter"] = (sx0, sy0, 12.0)
    text3d("Beschriftung_Ein_Aus", "Ein/Aus", (sx0, sy0, 10.5), 2.0, M["text"])

    # --- Voltage divider (2 × 10 kΩ), freely wired, between Drain and GND ---
    dx0, dy0 = 70.0, 8.0
    # two standing 10k in a line along Y: upper (from drain) at y=14, lower (to GND) at y=4
    ANCH["R10o"] = standing_res("Widerstand_10k_oben", dx0, dy0 + 10.0, (1, 0, 3))
    ANCH["R10u"] = standing_res("Widerstand_10k_unten", dx0, dy0, (1, 0, 3))
    pad("R10o_pad", dx0, dy0 + 10.0, 0.0, 2.0)
    pad("R10u_pad", dx0, dy0, 0.0, 2.0)
    # mid point: jumper from top of lower / we connect the two bottoms? 
    # Standing resistors have one lead through the board at their foot.
    # For a series divider: Drain -> top of R10o (second lead), foot of R10o = midpoint,
    # foot of R10o connected to top of R10u, foot of R10u = GND.
    # Simpler visual: the two feet are 10mm apart; connect R10o foot to R10u top-lead with a short wire,
    # and take the mid tap from a solder blob between them.
    # Even clearer: lay them as two axial resistors in a vertical stack (along Y, at z=6).
    # I'll add a mid pad between the two feet and a jumper.
    mid_x, mid_y = dx0 + 6.0, dy0 + 5.0
    ANCH["TEILER_M"] = pad("TEILER_M", mid_x, mid_y, 0.0, 2.2)
    # jumper foot R10o -> mid, mid -> top of R10u (the second lead of R10u)
    tube("div1", [(dx0, dy0 + 10.0, 6.8), (dx0, dy0 + 10.0, 8.0),
                  (mid_x, mid_y, 7.5), (mid_x, mid_y, 1.0)], M["lead"], 0.22)
    tube("div2", [(dx0, dy0, 6.8), (dx0, dy0, 8.0),
                  (mid_x, mid_y + 0.2, 7.2), (mid_x, mid_y, 1.0)], M["lead"], 0.22)
    text3d("Beschriftung_10k_oben", "10 kΩ", (dx0 - 6.5, dy0 + 10.0, 5.0), 1.6, M["txtk"], (math.radians(90), 0, 0))
    text3d("Beschriftung_10k_unten", "10 kΩ", (dx0 - 6.5, dy0, 5.0), 1.6, M["txtk"], (math.radians(90), 0, 0))

    # --- P3 GPIO35 block ---
    px0, py0 = 64.0, -22.0
    box_tex("CYD_Stecker_P3", px0, py0, 0, 22.0, 12.0, 1.4, M["plastic"], os.path.join(TEX, "p3.png"))
    # one gold pin
    ANCH["GPIO35"] = pad("Pad_GPIO35", px0 + 11.0, py0 + 4.0, 1.4, 2.2)
    ANCH["P3"] = (px0 + 11.0, py0 + 8.0, 3.5)

    # --- Pololu, pads toward camera (-Y), VIN on the left, VOUT on the right ---
    # Board 8.9 x 12.1 is small; scale 1.7× for readability, labels still correct.
    sc = 1.7
    pw, pl, pt = 8.9 * sc, 12.1 * sc, 1.0
    ox, oy = 96.0, 10.0
    # We'll build local: pads along y=oy (front edge), x increasing: VIN, GND, VOUT
    box_tex("Pololu", ox, oy, 0, pw, pl, pt, M["pcb"], os.path.join(TEX, "pololu.png"))
    # Note: texture has VOUT, GND, VIN left-to-right with origin at board corner
    # and pads at y = 12.1-1.27 from bottom in *unscaled* texture space.
    # If I place the board with texture VOUT at left, I should wire left pad as VOUT.
    # For left-to-right signal flow I want VIN on the left. So I'll rotate the board 180°
    # around Z by placing it flipped: use a rotated object, or just remap pads.
    # Easier: don't use the auto UV as "left = VOUT". I'll NOT rely on texture pad order
    # and instead add 3D-text VIN/GND/VOUT on the pads I define.
    # Rebuild pololu without depending on pad order in texture — I'll rotate the mesh 180.
    # Actually the texture will look upside down if I flip. Let me just label pads in 3D
    # and define: left = VIN, mid = GND, right = VOUT, ignoring the printed VOUT-left
    # on the small texture (3D text will be larger and correct).
    # Wait, that's inventing a false silkscreen. Better regenerate texture with VIN on the left.
    # I'll assume I will fix the texture after, and set pads as VIN, GND, VOUT left to right.
    pad_names = [("pol_vin", "VIN"), ("pol_gnd", "GND"), ("pol_vout", "VOUT")]
    # place pads along the front edge (small y), spaced 2.54*sc
    p0x = ox + 1.91 * sc
    p0y = oy + 1.27 * sc
    for i, (key, lab) in enumerate(pad_names):
        x = p0x + i * 2.54 * sc
        ANCH[key] = pad(key, x, p0y, pt, 2.4)
        text3d("t" + key, lab, (x, p0y - 4.2, 2.2), 1.6, M["text"])
    # inductor + caps for recognition
    ocx, ocy = ox + pw / 2, oy + pl * 0.55
    cyl("Pololu_Spule", ocx, ocy, pt, 6.0, 3.0, M["ferrite"], 24)
    cbox("pc1", ox + 2.8, oy + pl - 3.0, pt, 3.2, 2.0, 1.6, M["epoxy"])
    cbox("pc2", ox + pw - 2.8, oy + pl - 3.0, pt, 3.2, 2.0, 1.6, M["epoxy"])
    ANCH["Pololu"] = (ox + pw / 2, oy + pl * 0.7, pt + 4.0)
    text3d("Beschriftung_Pololu", "Pololu", (ox + pw / 2, oy + pl * 0.78, pt + 3.2), 1.7, M["text"])

    # --- CYD 5 V stub ---
    cx0, cy0 = 128.0, 18.0
    box_tex("CYD_5V", cx0, cy0, 0, 28.0, 20.0, 1.4, M["pcb_ye"], os.path.join(TEX, "cyd5v.png"))
    ANCH["CYD5V"] = pad("Pad_CYD_5V", cx0 + 14.0, cy0 + 4.5, 1.4, 2.8)
    ANCH["CYD"] = (cx0 + 14.0, cy0 + 12.0, 4.0)
    # GND pad on the same stub
    ANCH["CYDGND"] = pad("Pad_CYD_GND", cx0 + 22.0, cy0 + 4.5, 1.4, 2.2)

    # --- FET Source Q1 + Elko destination ---
    fx0, fy0 = 128.0, -14.0
    box_tex("FET_Platine_Q1_Elko", fx0, fy0, 0, 28.0, 20.0, 1.6, M["pcb"], os.path.join(TEX, "fet_q1.png"))
    ANCH["Q1S"] = pad("Pad_Q1_Source", fx0 + 8.0, fy0 + 4.5, 1.6, 2.6)
    ANCH["Q1GND"] = pad("Pad_Q1_GND", fx0 + 22.0, fy0 + 4.5, 1.6, 2.2)
    # small elko lying on the board
    cyl("Elko_C1", fx0 + 16.0, fy0 + 13.0, 6.5, 8.0, 12.0, M["elko"], 32, "x")
    cyl("Elko_C1_Boden", fx0 + 16.0 - 6.0, fy0 + 13.0, 6.5, 7.6, 0.6, M["rubber"], 32, "x")
    cyl("Elko_C1_Deckel", fx0 + 16.0 + 5.4, fy0 + 13.0, 6.5, 7.4, 0.6, M["alu"], 32, "x")
    ANCH["Elko"] = (fx0 + 16.0, fy0 + 13.0, 11.5)
    ANCH["FETQ1"] = (fx0 + 14.0, fy0 + 14.0, 12.0)

    # --- GND bus along the front ---
    gy = -34.0
    gz = 2.0
    tube("Litze_GND_Sammelleitung", [(ANCH["tc_out-"][0], gy, gz), (fx0 + 28.0, gy, gz)], wire_mat("gnd"), 0.7)
    ANCH["GNDbus"] = ((ANCH["tc_out-"][0] + fx0 + 28.0) / 2, gy, gz)

    # ---------- Wires (only connections from the plan) ----------
    wr = 0.6

    def W(name, net, pts, r=wr):
        tube(name, pts, wire_mat(net), r)

    # 1. OUT+ -> Source Q2 (red), branch to AUS
    op = ANCH["tc_out+"]
    qs = ANCH["Q2S"]
    aus = ANCH["SW_AUS"]
    # junction above OUT+ path
    jbat = (op[0] + 12.0, 0.0, 10.0)
    W("Litze_Akku_plus", "bat", [op, (op[0], op[1] - 6.0, 6.0), (op[0], op[1] - 8.0, 10.0),
                        jbat, (qs[0], qs[1] - 8.0, 10.0), (qs[0], qs[1], qs[2])])
    W("Litze_Schalter_AUS", "bat", [jbat, (aus[0], jbat[1], 10.0), (aus[0], aus[1] + 2.0, 8.0), aus])

    # 2. OUT- -> GND bus
    om = ANCH["tc_out-"]
    W("Litze_OUT_minus", "gnd", [om, (om[0], om[1] - 8.0, 5.0), (om[0], gy + 2.0, gz + 2.0), (om[0], gy, gz)])

    # 3. Mitte -> Gate Q2 (violet)
    mid = ANCH["SW_MITTE"]
    qg = ANCH["Q2G"]
    W("Litze_Schalter_Mitte", "gate", [mid, (mid[0], mid[1] + 4.0, 9.0), (qg[0] + 2.0, qg[1] - 10.0, 11.0),
                          (qg[0], qg[1] - 3.0, 9.0), qg])

    # 4. AN -> GND bus
    an = ANCH["SW_AN"]
    W("Litze_Schalter_AN", "gnd", [an, (an[0], an[1] + 3.0, 6.0), (an[0], gy + 3.0, gz + 3.0), (an[0], gy, gz)])

    # 5. Drain Q2 -> Pololu VIN (orange), branch to top of divider
    qd = ANCH["Q2D"]
    vin = ANCH["pol_vin"]
    r10top = (dx0, dy0 + 10.0, 7.2)
    jdr = (qd[0] + 10.0, qd[1], 10.5)
    W("Litze_Drain_VIN", "vin", [qd, (qd[0] + 4.0, qd[1], 8.0), jdr,
                         (vin[0], vin[1] + 6.0, 10.0), (vin[0], vin[1], vin[2])])
    W("Litze_Teiler_oben", "vin", [jdr, (r10top[0], jdr[1], 10.5), r10top])

    # 6. Bottom of lower 10k -> GND bus
    r10bot = (dx0, dy0, 0.3)
    W("Litze_Teiler_GND", "gnd", [(dx0, dy0, 0.2), (dx0, dy0 - 6.0, 3.0), (dx0, gy, gz)])

    # 7. Midpoint -> GPIO35 (dark)
    tm = ANCH["TEILER_M"]
    g35 = ANCH["GPIO35"]
    W("Litze_GPIO35", "dark", [tm, (tm[0], tm[1] - 6.0, 6.0), (g35[0], g35[1] + 6.0, 7.0), g35], 0.45)

    # 8. Pololu GND -> GND bus
    pg = ANCH["pol_gnd"]
    W("Litze_Pololu_GND", "gnd", [pg, (pg[0], pg[1] - 6.0, 5.0), (pg[0], gy, gz)])

    # 9. Pololu VOUT -> CYD 5V and FET Source Q1 (magenta)
    vo = ANCH["pol_vout"]
    c5 = ANCH["CYD5V"]
    q1s = ANCH["Q1S"]
    j5 = (vo[0] + 14.0, vo[1] - 2.0, 11.0)
    W("Litze_5V_CYD", "v5", [vo, (vo[0], vo[1] - 5.0, 8.0), j5,
                       (c5[0], c5[1] - 6.0, 10.0), (c5[0], c5[1], c5[2])])
    W("Litze_5V_Source_Q1", "v5", [j5, (j5[0], q1s[1] - 4.0, 11.0), (q1s[0], q1s[1] - 4.0, 8.0), q1s])

    # 10. CYD GND and FET Q1 GND -> bus
    W("Litze_CYD_GND", "gnd", [ANCH["CYDGND"], (ANCH["CYDGND"][0], ANCH["CYDGND"][1] - 6.0, 5.0),
                        (ANCH["CYDGND"][0], gy, gz)])
    W("Litze_Q1_GND", "gnd", [ANCH["Q1GND"], (ANCH["Q1GND"][0], ANCH["Q1GND"][1] - 5.0, 4.0),
                       (ANCH["Q1GND"][0], gy, gz)])

    ANCH["AkkuPlus"] = jbat
    ANCH["FuenfV"] = j5
    ANCH["Geschaltet"] = jdr


# =====================================================================
#  STEP 6 — LED-Streifen + Regensensor
# =====================================================================
def build_step6():
    # --- LED strip along +X, prominent input pad block on the left ---
    lx0, ly0, lz = 8.0, 16.0, 0.0
    length, width = 70.0, 6.0
    # input stiffener with large pads (recognizable solder pads at the strip entrance)
    box("LED_Streifen_Padboard", lx0 - 2.0, ly0 - 3.5, 0.0, 16.0, 13.0, 0.8, M["cob_fpc"])
    box_tex("LED_Streifen", lx0, ly0, lz, length, width, 0.3, M["cob_fpc"], os.path.join(TEX, "cob_top.png"))
    cbox("LED_Streifen_Silikon", lx0 + length / 2 + 6, ly0 + width / 2, 0.28, length - 14, 5.2, 1.7, M["cob_sil"])
    # cut marks and warm segments on top of the silicone (stay on the strip)
    for i in range(0, 5):
        x = lx0 + 18 + i * 11.0
        cbox("ledglow", x + 4.0, ly0 + width / 2, 2.05, 7.5, 3.6, 0.12,
             mat("glow%d" % i, srgb((255, 220, 140)), 0.35, emis=(255, 220, 140), estr=1.2))
        if i:
            cbox("cut", x, ly0 + width / 2, 2.08, 0.35, 4.6, 0.18,
                 mat("cutmark", srgb((120, 110, 90)), 0.6))
    pad_labs = [("LED5V", "5V", ly0 + 8.5), ("LEDDIN", "DIN", ly0 + 4.5), ("LEDGND", "GND", ly0 + 0.5)]
    for key, lab, yy in pad_labs:
        ANCH[key] = pad(key, lx0 + 3.0, yy, 0.8, 2.6)
        text3d("t" + key, lab, (lx0 + 8.8, yy, 2.0), 1.7, M["txtk"])
    ANCH["LED"] = (lx0 + 32.0, ly0 + 3.0, 4.0)
    # arrow cut into the FPC as a dark chevron (data direction away from input)
    chev = mesh("pfeil",
                [(lx0 + 22, ly0 + 7.4, 0.45), (lx0 + 30, ly0 + 9.0, 0.45),
                 (lx0 + 22, ly0 + 10.6, 0.45), (lx0 + 24, ly0 + 9.0, 0.45),
                 (lx0 + 22, ly0 + 7.4, 0.65), (lx0 + 30, ly0 + 9.0, 0.65),
                 (lx0 + 22, ly0 + 10.6, 0.65), (lx0 + 24, ly0 + 9.0, 0.65)],
                [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)],
                M["txtk"])
    ANCH["Pfeil"] = (lx0 + 28.0, ly0 + 9.0, 2.0)

    # 470 Ω directly at the strip, in the DIN line (just left of DIN pad)
    # axial resistor in the green wire, close to the pad
    din = ANCH["LEDDIN"]
    r_a = (din[0] - 14.0, din[1], 3.2)
    r_b = (din[0] - 6.0, din[1], 3.2)
    mid470 = resistor("Widerstand_470Ohm", r_a, r_b, (4, 7, 1), body_r=1.2)
    ANCH["R470"] = mid470
    # heat shrink over the resistor body and over the three pad joints
    shrink("hs470", (mid470[0] - 3.0, mid470[1], mid470[2]),
           (mid470[0] + 3.0, mid470[1], mid470[2]), M["shrink_c"], 1.9)
    for key, m, yoff in (("LED5V", M["shrink_r"], 8.5), ("LEDDIN", M["shrink_g"], 4.5), ("LEDGND", M["shrink_k"], 0.5)):
        p = ANCH[key]
        shrink("hs" + key, (p[0] - 7.0, p[1], p[2] + 0.4), (p[0] - 0.3, p[1], p[2] + 0.3), m, 1.5)

    # Incoming wires from the left, ending at labels
    # red: 5V from Drain Q1
    Wends = {}
    def lead_in(name, net, end, y, z, x0=-38.0, r=0.6):
        start = (x0, y, z)
        pts = [start, (x0 + 10, y, z), (end[0] - 8, end[1], z), end]
        tube(name, pts, wire_mat(net), r)
        # tinned tip
        sphere(name + "tip", start, 0.55, M["tin"])
        ANCH[name] = start
        return start

    lead_in("Litze_5V_Drain_Q1", "led", ANCH["LED5V"], ly0 + 8.5, 7.0, -28.0)
    # green goes to the left end of the 470Ω, not directly to DIN
    lead_in("Litze_GPIO23_DIN", "din", r_a, ly0 + 4.5, 6.0, -28.0)
    tube("Litze_470Ohm_nach_DIN", [r_b, (din[0] - 2.0, din[1], 3.0), din], wire_mat("din"), 0.55)
    lead_in("Litze_LED_GND", "white", ANCH["LEDGND"], ly0 + 0.5, 4.5, -28.0)
    ANCH["DrainQ1"] = ANCH["Litze_5V_Drain_Q1"]
    ANCH["GPIO23"] = ANCH["Litze_GPIO23_DIN"]
    ANCH["LEDGNDin"] = ANCH["Litze_LED_GND"]

    # --- LM393 module ---
    mx0, my0 = 100.0, 6.0
    mw, ml, mt = 16.0, 30.0, 1.6
    box_tex("LM393", mx0, my0, 0, mw, ml, mt, M["pcb_bl"], os.path.join(TEX, "lm393.png"))
    # pot
    cbox("LM393_Poti", mx0 + 8.0, my0 + 20.0, mt, 6.6, 6.6, 4.0, M["pot"])
    cyl("LM393_Poti_Rotor", mx0 + 8.0, my0 + 20.0, mt + 4.0, 3.4, 0.5, M["potw"], 24)
    # IC
    cbox("LM393_IC", mx0 + 8.0, my0 + 12.5, mt, 6.0, 4.9, 1.5, M["epoxy"])
    cbox("LED PWR", mx0 + 3.0, my0 + 9.0, mt, 0.8, 1.6, 0.5, M["led_r"])
    cbox("LED DO", mx0 + 13.0, my0 + 9.0, mt, 0.8, 1.6, 0.5, M["led_g"])
    # pads VCC GND DO AO along the near edge (small y) — matches texture bottom
    # In texture, pads are at the bottom (y small if we mapped v = (y-y0)/l with y0 = my0, pads at y=28mm from top...
    # Texture: pads at cy = 28*s from top of 30mm board, so y local = 28, which is the FAR edge if y0 is origin and +y is up.
    # That's the opposite of "near the camera".
    # I'll put signal pads on the camera side (low y) and ignore exact UV pad positions;
    # I'll add 3D labels. And put sensor pads on the far (+y) edge.
    # To make texture labels match, I should put VCC/GND/DO/AO at y local = 28 (far).
    # Camera is from -Y, so those pads would be on the far side — harder to see.
    # I'll rotate the board 180° so pads face the camera: place board and use pads at y local = 2 (if texture flipped).
    # Simpler: put pads at low y (camera side) and accept that silkscreen may be opposite;
    # large 3D labels VCC/GND/DO/AO will be correct. The board color and pot/IC make it recognizable.

    pad_m = [("LM_VCC", "VCC", 3.2), ("LM_GND", "GND", 6.5), ("LM_DO", "DO", 9.8), ("LM_AO", "AO", 13.1)]
    for key, lab, xx in pad_m:
        ANCH[key] = pad(key, mx0 + xx, my0 + 2.4, mt, 2.1)
        text3d("t" + key, lab, (mx0 + xx, my0 + 2.4 - 4.0, 2.6), 1.5, M["text"])
    # AO stays free — no wire. A small "frei" label later in PIL.
    ANCH["LM393"] = (mx0 + 8.0, my0 + 16.0, mt + 6.0)
    # sensor pads on far side
    ANCH["LM_S1"] = pad("LM_S1", mx0 + 6.5, my0 + ml - 2.4, mt, 2.0)
    ANCH["LM_S2"] = pad("LM_S2", mx0 + 9.5, my0 + ml - 2.4, mt, 2.0)

    # heat shrink on VCC, GND, DO joints (not AO — nothing soldered)
    for key, m in (("LM_VCC", M["shrink_r"]), ("LM_GND", M["shrink_k"]), ("LM_DO", M["shrink_g"])):
        p = ANCH[key]
        shrink("hs" + key, (p[0], p[1] - 3.0, p[2] + 0.7), (p[0], p[1] + 0.4, p[2] + 0.7), m, 1.25)

    # Incoming leads from the left/front for VCC, GND, DO
    def lead_mod(name, net, end, x0, y, z):
        start = (x0, y, z)
        pts = [start, (x0 + 8, y, z), (end[0], y, z), (end[0], end[1] - 6, z), end]
        tube(name, pts, wire_mat(net), 0.55)
        sphere(name + "tip", start, 0.5, M["tin"])
        ANCH[name] = start
        return start

    lead_mod("Litze_3V3_VCC", "v33", ANCH["LM_VCC"], 72.0, -14.0, 8.0)
    lead_mod("Litze_LM393_GND", "gnd", ANCH["LM_GND"], 72.0, -18.0, 6.0)
    lead_mod("Litze_DO_GPIO19", "teal", ANCH["LM_DO"], 72.0, -22.0, 4.5)
    ANCH["V33"] = ANCH["Litze_3V3_VCC"]
    ANCH["GPIO19"] = ANCH["Litze_DO_GPIO19"]
    ANCH["LMGNDin"] = ANCH["Litze_LM393_GND"]

    # --- Rain plate ---
    rx0, ry0 = 132.0, 2.0
    rw, rl, rt = 40.0, 54.0, 1.6
    # Scale slightly? Real size is large (40x54) vs LM393 16x30 — that's correct and recognizable.
    # But it may dominate. I'll use 0.75 scale for composition (still clearly a plate).
    scp = 0.75
    rw, rl = 40.0 * scp, 54.0 * scp
    box_tex("Sensorplatte", rx0, ry0, 0, rw, rl, rt, M["black"], os.path.join(TEX, "rain_plate.png"))
    # two pads / angled header at the edge facing the module (left, -X)
    ANCH["PL1"] = pad("Pad_Platte_1", rx0 + 3.0, ry0 + rl * 0.45, rt, 2.2)
    ANCH["PL2"] = pad("Pad_Platte_2", rx0 + 3.0, ry0 + rl * 0.55, rt, 2.2)
    ANCH["Platte"] = (rx0 + rw / 2, ry0 + rl / 2, rt + 2.0)
    # two dark wires, orientation does not matter
    s1, s2 = ANCH["LM_S1"], ANCH["LM_S2"]
    p1, p2 = ANCH["PL1"], ANCH["PL2"]
    tube("Litze_Sensorplatte_1", [s1, (s1[0], s1[1] + 4, 8.0), (p1[0] - 6, p1[1], 8.0), p1], wire_mat("plate"), 0.5)
    tube("Litze_Sensorplatte_2", [s2, (s2[0], s2[1] + 6, 7.0), (p2[0] - 6, p2[1], 7.0), p2], wire_mat("plate"), 0.5)
    # heat shrink on plate joints and module sensor joints
    for key, m in (("PL1", M["shrink_c"]), ("PL2", M["shrink_c"]), ("LM_S1", M["shrink_c"]), ("LM_S2", M["shrink_c"])):
        p = ANCH[key]
        shrink("hs" + key, (p[0] - 2.2, p[1], p[2] + 0.7), (p[0] + 2.2, p[1], p[2] + 0.7), m, 1.2)

    ANCH["Schrumpf"] = (lx0 + 4.5, ly0 + 3.0, 3.5)


# ---------- lights + camera + render ----------
def setup_view(mode):
    world = bpy.data.worlds.new("w")
    scn.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.77, 0.8, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7

    def light(name, loc, energy, size=40):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.size = size
        o = bpy.data.objects.new(name, ld)
        coll.objects.link(o)
        o.location = loc
        # aim at scene center
        tgt = Vector(cen)
        d = tgt - Vector(loc)
        o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    if mode == "4":
        cen = Vector((95.0, 0.0, 4.0))
        cam_loc = cen + Vector((-70, -130, 95))
        lens, sensor = 50, 36
    else:
        cen = Vector((95.0, 18.0, 3.0))
        cam_loc = cen + Vector((-55, -140, 90))
        lens, sensor = 50, 36

    light("key", (cen.x - 80, cen.y - 120, 140), 140000, 50)
    light("fill", (cen.x + 120, cen.y + 40, 90), 50000, 45)
    light("rim", (cen.x + 20, cen.y + 100, 70), 30000, 35)

    cd = bpy.data.cameras.new("Kamera")
    cd.type = "PERSP"
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 1
    cd.clip_end = 1000
    cam = bpy.data.objects.new("Kamera", cd)
    coll.objects.link(cam)
    scn.camera = cam
    cam.location = cam_loc
    cam.rotation_euler = (cen - cam.location).to_track_quat("-Z", "Y").to_euler()
    # slight shift so the header/sidebar composition has room — framing is the 2000x1500 raw
    bpy.context.view_layer.update()

    # If something is clipped, that's ok; we'll adjust after preview.
    proj = {}
    for k, p in ANCH.items():
        v = world_to_camera_view(scn, cam, Vector(p))
        proj[k] = (v.x * scn.render.resolution_x, (1 - v.y) * scn.render.resolution_y, v.z)
    # store only x,y for annotator, plus a visible flag
    outj = {}
    for k, (x, y, z) in proj.items():
        outj[k] = [x, y, 1 if (0 <= v_vis(x, y) and z > 0) else 0]


def v_vis(x, y):
    return 0 <= x <= 2000 and 0 <= y <= 1500


def project_and_render():
    bpy.context.view_layer.update()
    cam = scn.camera
    proj = {}
    for k, p in ANCH.items():
        v = world_to_camera_view(scn, cam, Vector(p))
        vis = 1 if (v.z > 0 and -0.15 <= v.x <= 1.15 and -0.15 <= v.y <= 1.15) else 0
        proj[k] = [v.x * scn.render.resolution_x, (1 - v.y) * scn.render.resolution_y, vis]
    jpath = OUT.rsplit(".", 1)[0] + ".json"
    json.dump(proj, open(jpath, "w"), indent=2)
    scn.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("rendered", OUT, "anchors", len(proj))



def add_world_lights(cen):
    world = bpy.data.worlds.new("w")
    scn.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.77, 0.8, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7

    def add_light(name, loc, energy, size=45):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.size = size
        o = bpy.data.objects.new(name, ld)
        coll.objects.link(o)
        o.location = loc
        o.rotation_euler = (cen - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

    add_light("Licht_Haupt", (cen.x - 90, cen.y - 140, 160), 160000, 55)
    add_light("Licht_Fuell", (cen.x + 140, cen.y + 50, 100), 55000, 50)
    add_light("Licht_Kante", (cen.x + 20, cen.y + 120, 80), 32000, 40)


def fit_ortho_camera(view_dir, margin=1.22):
    """Place an orthographic camera so all anchors fit in the 2000x1500 frame."""
    pts = [Vector(p) for p in ANCH.values()]
    if not pts:
        raise SystemExit("no anchors")
    cen = sum(pts, Vector()) / len(pts)
    # bias slightly up so labels on top of boards stay in frame
    zs = [p.z for p in pts]
    cen = Vector((cen.x, cen.y, max(3.0, sum(zs) / len(zs))))
    vd = Vector(view_dir).normalized()
    # camera basis
    up_hint = Vector((0, 0, 1))
    right = vd.cross(up_hint)
    if right.length < 1e-6:
        right = Vector((1, 0, 0))
    right.normalize()
    up = right.cross(vd)
    up.normalize()
    # include a few extra points around each anchor so parts aren't clipped
    extras = []
    for p in pts:
        for d in (right, up, -right, -up):
            extras.append(p + d * 3.0)
    allp = pts + extras
    rs = [(p - cen).dot(right) for p in allp]
    us = [(p - cen).dot(up) for p in allp]
    # recenter on the visual bbox
    cr = (min(rs) + max(rs)) / 2
    cu = (min(us) + max(us)) / 2
    cen = cen + right * cr + up * cu
    rs = [(p - cen).dot(right) for p in allp]
    us = [(p - cen).dot(up) for p in allp]
    width = (max(rs) - min(rs)) * margin
    height = (max(us) - min(us)) * margin
    aspect = scn.render.resolution_x / scn.render.resolution_y
    scale = max(width, height * aspect)
    add_world_lights(cen)
    cd = bpy.data.cameras.new("Kamera")
    cd.type = "ORTHO"
    cd.ortho_scale = scale
    cd.clip_start = 1
    cd.clip_end = 2000
    cam = bpy.data.objects.new("Kamera", cd)
    coll.objects.link(cam)
    scn.camera = cam
    cam.location = cen + vd * 400
    cam.rotation_euler = (-vd).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    print("camera scale", round(scale, 2), "center", tuple(round(c, 2) for c in cen))



def labels_facing_camera(items, size=3.2):
    """3D-Text, zur Kamera ausgerichtet, damit die Beschriftung in Blender lesbar ist."""
    cam = scn.camera
    rot = cam.rotation_euler.copy() if cam else (0, 0, 0)
    # Kamera-Achsen
    if cam:
        right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
        up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    else:
        right, up = Vector((1, 0, 0)), Vector((0, 0, 1))
    for key, text, dx, dy, dz in items:
        if key not in ANCH:
            print("warn: kein Anker", key)
            continue
        base = Vector(ANCH[key])
        pos = base + right * dx + up * dy + Vector((0, 0, dz))
        text3d("Beschriftung_" + key, text, tuple(pos), size, M["txtk"], rot, extrude=0.08)


def finish_and_save(mode):
    # Zusätzliche lesbare 3D-Beschriftungen (utf-8, echte Umlaute)
    if mode in ("4", "4b"):
        labels_facing_camera([
            ("TC4056", "TC4056", -8, 14, 2),
            ("Q2", "Q2 Ein/Aus\nAO3401A", 0, 12, 2),
            ("R47", "47 kΩ  (G–S)", -12, 8, 2),
            ("Schalter", "Ein/Aus-Schalter\nAUS · Mitte · AN", 0, -12, 2),
            ("R10o", "Akku-Teiler\n2 × 10 kΩ", 0, 12, 2),
            ("P3", "GPIO35\nCYD-Stecker P3", 8, -10, 2),
            ("Pololu", "Pololu S13V10F5\n(kein EN-Pin)", 0, 10, 2),
            ("CYD", "CYD 5 V\n(Anschluss offen)", 0, 10, 2),
            ("Elko", "Source Q1 + Elko\n(Schritt 5)", 8, -8, 2),
            ("GNDbus", "GND (alle zusammen)", 0, -8, 2),
        ], 3.0)
        group_by_prefix([
            ("TC4056", ["TC4056", "Pad_OUT", "Pad_B_"]),
            ("FET_Platine_Q2", ["FET_Platine_Q2", "Q2_", "Pad_Q2", "Widerstand_47k", "Beschriftung_Q", "Beschriftung_S", "Beschriftung_G", "Beschriftung_D", "Beschriftung_R47", "trS", "trG", "trD", "R47"]),
            ("Ein_Aus_Schalter", ["Ein_Aus_Schalter", "Schalter_", "Beschriftung_Ein", "tSW", "SW_"]),
            ("Akku_Teiler", ["Widerstand_10k", "Beschriftung_10k", "TEILER", "div1", "div2", "R10"]),
            ("CYD_Stecker_P3", ["CYD_Stecker_P3", "Pad_GPIO35", "Beschriftung_P3", "Beschriftung_GPIO35"]),
            ("Pololu", ["Pololu", "Pad_Pololu", "Beschriftung_Pololu", "pc1", "pc2"]),
            ("CYD_5V", ["CYD_5V", "Pad_CYD", "Beschriftung_CYD"]),
            ("FET_Platine_Q1_Elko", ["FET_Platine_Q1", "Pad_Q1", "Elko_", "Beschriftung_Elko", "Beschriftung_FET"]),
            ("Litzen", ["Litze_"]),
            ("Licht", ["Licht_"]),
            ("Kamera", ["Kamera"]),
            ("Beschriftung", ["Beschriftung_"]),
        ])
    else:
        labels_facing_camera([
            ("LED", "LED-Streifen (Eingang)\nPfeil zeigt vom Eingang weg", 0, 12, 2),
            ("R470", "470 Ω direkt am Streifen", -8, 10, 2),
            ("DrainQ1", "5 V  ←  Drain Q1", -6, 8, 2),
            ("GPIO23", "GPIO23 (SD-Pin 3)", -6, -8, 2),
            ("LEDGNDin", "GND (weiß)", 8, -8, 2),
            ("LM393", "Regensensor-Modul\nLM393", 0, 10, 2),
            ("V33", "3,3 V *  →  VCC", -10, 6, 2),
            ("GPIO19", "DO  →  GPIO19", 6, -8, 2),
            ("LM_AO", "AO frei", 8, 4, 2),
            ("Platte", "Sensorplatte\n2 Kabel, egal wie rum", 0, 10, 2),
            ("Schrumpf", "Schrumpfschlauch", 8, 8, 2),
        ], 3.0)
        group_by_prefix([
            ("LED_Streifen", ["LED_Streifen", "Pad_LED", "Widerstand_470", "ledglow", "cut", "pfeil", "Beschriftung_LED", "Beschriftung_R470", "Schrumpf", "hs470", "hsLED"]),
            ("LM393", ["LM393", "Pad_LM393", "Beschriftung_LM", "Beschriftung_V33", "Beschriftung_GPIO19"]),
            ("Sensorplatte", ["Sensorplatte", "Pad_Platte", "Beschriftung_Platte"]),
            ("Litzen", ["Litze_"]),
            ("Licht", ["Licht_"]),
            ("Kamera", ["Kamera"]),
            ("Beschriftung", ["Beschriftung_"]),
        ])
    set_view_to_camera()
    # In der gespeicherten Datei soll F12 anständig rendern
    if hasattr(scn, 'cycles'):
        scn.cycles.samples = 64
        scn.cycles.use_denoising = True
    blend = os.path.join(HERE, BLEND_NAMES[mode])
    if OUT.lower().endswith(".blend"):
        blend = os.path.abspath(OUT)
    pack_and_save(blend)


if MODE in ("4", "4b"):
    build_step4()
    fit_ortho_camera((-0.40, -0.95, 0.88), 1.08)
    if SAMPLES > 0 and not OUT.lower().endswith(".blend"):
        project_and_render()
    finish_and_save(MODE)
elif MODE in ("6", "6b"):
    build_step6()
    fit_ortho_camera((-0.35, -0.95, 0.90), 1.08)
    if SAMPLES > 0 and not OUT.lower().endswith(".blend"):
        project_and_render()
    finish_and_save(MODE)
else:
    raise SystemExit("MODE must be 4 or 6, got %r" % MODE)
