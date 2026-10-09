# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE
# Exportiert die komplette HydroDesk Base (Gehaeuse + Elektronik) als GLB/STL.
# Aufruf: HD_NO_RENDER=1 HD_OUT=/pfad/name blender -b -P export.py -- produkt|explosion /tmp/x.png 1 10
import bpy, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
__file__ = os.path.join(_here, 'scene.py')
exec(compile(open(__file__).read(), __file__, 'exec'))

OUTB = os.environ['HD_OUT']
NAMES = {'base': 'Unterschale', 'cover': 'Deckel', 'pad': 'Flaschenplatte', 'mat': 'Silikonmatte',
         'cyd': 'Display-Board', 'lc': 'Waegezelle', 'hx': 'HX711', 'bat': 'Akku', 'boost': 'Pololu-5V-Wandler',
         'tc': 'TC4056', 'fet': 'FET-Platine', 'sw': 'Ein-Aus-Schalter', 'keil': 'Klemmkeile', 'cmp': 'LM393', 'rs': 'Regensensor', 'led': 'COB-LED-Streifen', 'diff': 'Diffusor',
         'cap': 'Abdeckkappe_USB', 'm3': 'Schrauben_M3', 'm4': 'Schrauben_M4', 'm5': 'Schrauben_M5', 'feet': 'Gummifuesse'}

def part_of(o):
    p = o
    while p.parent is not None: p = p.parent
    if p.type == 'EMPTY' and p.name.startswith('G_'): return NAMES.get(p.name[2:])
    n = o.name
    if n.startswith('M4_'): return 'Schrauben_M4'
    if n.startswith('M3_'): return 'Schrauben_M3'
    if n.startswith('M5_'): return 'Schrauben_M5'
    if n.startswith('Fuss'): return 'Gummifuesse'
    return None

bpy.context.view_layer.update()
drop = [o for o in scn.objects if o.type in ('LIGHT', 'CAMERA') or o.hide_render
        or (o.name in ('Boden', 'Flasche', 'Flaschendeckel', 'Wasser') or o.name.startswith('g')) and o.type != 'EMPTY']
for o in drop: bpy.data.objects.remove(o, do_unlink=True)
parts = {}
for o in list(scn.objects):
    if o.type not in ('MESH', 'CURVE'): continue
    p = part_of(o)
    if p is None: print('UNZUGEORDNET', o.name); bpy.data.objects.remove(o, do_unlink=True); continue
    parts.setdefault(p, []).append(o)
# Eltern loesen (Weltlage behalten), Modifier anwenden, Kurven -> Mesh
for o in scn.objects:
    if o.type in ('MESH', 'CURVE'):
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
for o in [o for o in scn.objects if o.type == 'EMPTY']: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in scn.objects: o.select_set(True)
bpy.context.view_layer.objects.active = scn.objects[0]
bpy.ops.object.convert(target='MESH')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
# pro Teil zusammenfuegen
result = []
for name, objs in parts.items():
    objs = [bpy.data.objects.get(o.name) for o in objs]; objs = [o for o in objs if o]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active; j.name = name; j.data.name = name
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    result.append(j)
tris = sum(len(o.data.loop_triangles) if not o.data.calc_loop_triangles() else len(o.data.loop_triangles) for o in result)
print('TEILE', len(result), sorted(o.name for o in result), 'Dreiecke', tris)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.stl_export(filepath=OUTB + '.stl', export_selected_objects=False, apply_modifiers=True, global_scale=1.0)
# glTF arbeitet in Metern
for o in result:
    o.location *= 0.001; o.scale = (0.001, 0.001, 0.001)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.export_scene.gltf(filepath=OUTB + '.glb', export_format='GLB', export_apply=True,
                          export_yup=True, export_materials='EXPORT', export_image_format='AUTO')
print('EXPORT OK', OUTB)
