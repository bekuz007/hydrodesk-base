# Importiert eine GLB-Datei neu und rendert eine Kontroll-Vorschau (Farben/Materialien pruefen)
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--')+1:]; src, out = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
s = bpy.context.scene
objs = [o for o in s.objects if o.type == 'MESH']
print('IMPORT', len(objs), sorted(o.name for o in objs))
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in objs:
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, p)); mx = Vector(map(max, mx, p))
print('BBOX_MM', [round(v*1000, 1) for v in (mx-mn)])
s.render.engine = 'CYCLES'; s.cycles.samples = 48; s.cycles.use_denoising = True
s.render.resolution_x, s.render.resolution_y = 1600, 900
s.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('W'); w.use_nodes = True; s.world = w
w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.57, 0.6, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
l = bpy.data.lights.new('sun', 'SUN'); l.energy = 2.5; l.angle = 0.2
lo = bpy.data.objects.new('sun', l); lo.rotation_euler = (math.radians(50), 0, math.radians(30)); s.collection.objects.link(lo)
c = bpy.data.cameras.new('cam'); c.lens = 85; c.clip_start = 0.001
co = bpy.data.objects.new('cam', c); s.collection.objects.link(co); s.camera = co
t = (mn+mx)/2; d = max((mx-mn).length*2.6, 0.3)
co.location = t + Vector((0.35, -0.8, 0.55)).normalized()*d
co.rotation_euler = (t-co.location).to_track_quat('-Z', 'Y').to_euler()
s.render.filepath = out; bpy.ops.render.render(write_still=True); print('PREVIEW', out)
