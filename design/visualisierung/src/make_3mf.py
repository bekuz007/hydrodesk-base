# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE
# GLB -> 3MF: ein Objekt pro Bauteil, Einheit mm, Z oben, Farben pro Dreieck (basematerials)
import sys, re, zipfile, collections, numpy as np, trimesh
src, dst = sys.argv[1], sys.argv[2]
sc = trimesh.load(src)
R = trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])   # glTF Y-oben -> Z-oben
S = np.diag([1000, 1000, 1000, 1.0])                                # m -> mm
parts = collections.OrderedDict(); colors = []
def colidx(c):
    h = '#%02X%02X%02X' % tuple(int(v) for v in np.clip(c, 0, 255))
    if h not in colors: colors.append(h)
    return colors.index(h)
for node in sc.graph.nodes_geometry:
    T, gname = sc.graph[node]
    g = sc.geometry[gname]
    mat = getattr(g.visual, 'material', None); col = np.array([180, 180, 180])
    if mat is not None:
        if getattr(mat, 'baseColorTexture', None) is not None:
            col = np.array(mat.baseColorTexture.convert('RGB')).reshape(-1, 3).mean(0)
        elif getattr(mat, 'baseColorFactor', None) is not None:
            lin = np.array(mat.baseColorFactor[:3], float) / 255.0          # glTF: linear
            col = np.where(lin <= 0.0031308, 12.92*lin, 1.055*lin**(1/2.4) - 0.055) * 255  # -> sRGB
    m = trimesh.Trimesh(g.vertices, g.faces, process=False); m.apply_transform(S @ R @ T); m.merge_vertices()
    base = re.sub(r'(\.\d{3})?(_[0-9a-f]{6}|_\d+)?$', '', node)
    parts.setdefault(base, []).append((m, colidx(col)))
x = ['<?xml version="1.0" encoding="UTF-8"?>',
     '<model unit="millimeter" xml:lang="de-DE" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
     '<metadata name="Title">HydroDesk Base - komplett</metadata><resources>',
     '<basematerials id="1">' + ''.join('<base name="Farbe%d" displaycolor="%s"/>' % (i, c) for i, c in enumerate(colors)) + '</basematerials>']
oid = 2; ids = []
for name, lst in parts.items():
    V = []; Tr = []; off = 0
    for m, ci in lst:
        V.append(m.vertices); Tr += ['<triangle v1="%d" v2="%d" v3="%d" pid="1" p1="%d"/>' % (a+off, b+off, c+off, ci) for a, b, c in m.faces]
        off += len(m.vertices)
    V = np.vstack(V)
    x.append('<object id="%d" name="%s" type="model" pid="1" pindex="%d"><mesh><vertices>' % (oid, name, lst[0][1]))
    x.append(''.join('<vertex x="%.4f" y="%.4f" z="%.4f"/>' % tuple(v) for v in V))
    x.append('</vertices><triangles>' + ''.join(Tr) + '</triangles></mesh></object>')
    ids.append(oid); oid += 1
x.append('</resources><build>' + ''.join('<item objectid="%d"/>' % i for i in ids) + '</build></model>')
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model', ''.join(x))
print('3MF', dst, len(parts), list(parts), 'Farben', len(colors))
