# -*- coding: utf-8 -*-
"""Gemeinsame Helfer: Einheiten, Collections, selbstständige .blend-Datei."""
import bpy, os
from mathutils import Vector


def prepare_fresh_scene(name="Szene"):
    """Factory-UI behalten (angenehm zum Öffnen), Standard-Cube entfernen, mm als Einheit."""
    bpy.ops.wm.read_factory_settings(use_empty=False)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    # leere Standard-Collections aufräumen, außer die Szenen-Collection
    scn = bpy.context.scene
    scn.name = name
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 0.001  # 1 Blendereinheit = 1 mm
    scn.unit_settings.length_unit = "MILLIMETERS"
    return scn


def ensure_collection(name, parent=None):
    scn = bpy.context.scene
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or scn.collection).children.link(c)
    return c


def move_to_collection(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    if obj.name not in coll.objects:
        coll.objects.link(obj)


def rename(old, new):
    o = bpy.data.objects.get(old)
    if o is not None:
        o.name = new
        if o.data is not None and hasattr(o.data, "name"):
            try:
                o.data.name = new
            except Exception:
                pass
        return o
    return None


def apply_renames(mapping):
    """mapping: alter Name (oder Prefix mit *) -> neuer Name."""
    done = []
    for old, new in mapping:
        if old.endswith("*"):
            pre = old[:-1]
            hits = [o for o in bpy.data.objects if o.name.startswith(pre)]
            for i, o in enumerate(hits):
                nm = new if i == 0 else ("%s_%02d" % (new, i + 1))
                o.name = nm
                done.append(nm)
        else:
            if rename(old, new):
                done.append(new)
    return done


def group_by_prefix(groups, rest_name="Sonstiges"):
    """groups: list of (collection_name, list_of_prefixes). First match wins."""
    scn = bpy.context.scene
    assigned = set()
    for cname, prefixes in groups:
        coll = ensure_collection(cname)
        for o in list(bpy.data.objects):
            if o.name in assigned:
                continue
            if any(o.name.startswith(p) or o.name == p for p in prefixes):
                move_to_collection(o, coll)
                assigned.add(o.name)
    rest = [o for o in bpy.data.objects if o.name not in assigned]
    if rest:
        coll = ensure_collection(rest_name)
        for o in rest:
            move_to_collection(o, coll)


def pack_and_save(path):
    """Texturen (und was Blender packen kann) einpacken und als .blend speichern."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # Bilder einzeln packen, dann pack_all
    for img in bpy.data.images:
        if img.source == "FILE" and img.filepath:
            try:
                img.pack()
            except Exception as e:
                print("warn: Bild nicht gepackt:", img.name, e)
    try:
        bpy.ops.file.pack_all()
    except Exception as e:
        print("warn: pack_all:", e)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True, check_existing=False)
    size = os.path.getsize(path)
    print("saved blend", path, size)
    # prüfen, ob Bilder wirklich gepackt sind
    packed = sum(1 for i in bpy.data.images if i.packed_file)
    print("packed images", packed, "/", len(bpy.data.images))
    return path, size


def set_view_to_camera():
    """Beim Öffnen soll die Kamera der Szene aktiv sein; Viewport wenn möglich auf Kamera."""
    scn = bpy.context.scene
    if scn.camera is None:
        return
    # Workspaces / Screens der Factory-Datei
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.camera = scn.camera
                        space.lens = 50
                        try:
                            space.region_3d.view_perspective = "CAMERA"
                        except Exception:
                            pass
