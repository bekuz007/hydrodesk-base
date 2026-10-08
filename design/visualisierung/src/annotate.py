import json, sys, math
import numpy as np
from PIL import Image, ImageDraw
from fonts import F
from comp import bg

INK=(28,33,40); SUB=(70,78,88); LINE=(40,46,54)

def compose(raw, dark=False):
    im = Image.open(raw).convert('RGBA')
    if dark: b = bg(*im.size, c0=(58,64,73), c1=(22,25,30)).convert('RGBA')
    else: b = bg(*im.size).convert('RGBA')
    b.alpha_composite(im); return b, im

def content_bbox(im):
    a = np.array(im)[..., 3]; ys, xs = np.where(a > 40)
    return xs.min(), ys.min(), xs.max(), ys.max()

def title(d, k, t1, t2):
    d.text((int(70*k), int(56*k)), t1, font=F(int(50*k), 700), fill=INK)
    d.text((int(72*k), int(122*k)), t2, font=F(int(28*k), 450), fill=SUB)

def footer(d, k, W, H, txt):
    d.text((W-int(70*k), H-int(48*k)), txt, font=F(int(22*k), 450), fill=SUB, anchor='rs')

def labels(img, anchors, specs, k, colL, colR, top, bottom, gap=None):
    d = ImageDraw.Draw(img)
    fN = F(int(30*k), 650); fS = F(int(22*k), 450)
    lh = int(gap or 74*k)
    for side in 'LR':
        items = [s for s in specs if s[1] == side]
        items = [(anchors[s[0]][1], s) for s in items if s[0] in anchors]
        items.sort(key=lambda t: t[0])
        ys = [max(top, min(bottom, y)) for y, _ in items]
        for _ in range(200):  # Ueberlappungen aufloesen
            moved = False
            for i in range(1, len(ys)):
                if ys[i] - ys[i-1] < lh:
                    m = (lh - (ys[i]-ys[i-1]))/2; ys[i-1] -= m; ys[i] += m; moved = True
            ys = [max(top, min(bottom, y)) for y in ys]
            if not moved: break
        for i in range(1, len(ys)):
            ys[i] = max(ys[i], ys[i-1]+lh)
        for (ay, s), ly in zip(items, ys):
            key, _, name, sub = s
            ax, ay = anchors[key][0], anchors[key][1]
            if side == 'L':
                tx = colL; ex = colL + int(16*k); bx = ex + int(40*k)
            else:
                tx = colR; ex = colR - int(16*k); bx = ex - int(40*k)
            ly2 = ly + int(14*k)
            d.line([(ax, ay), (bx, ly2), (ex, ly2)], fill=LINE, width=max(2, int(2.2*k)), joint='curve')
            r = int(6*k)
            d.ellipse([ax-r, ay-r, ax+r, ay+r], fill=(255,255,255), outline=LINE, width=max(2, int(2.5*k)))
            d.ellipse([ax-r*0.4, ay-r*0.4, ax+r*0.4, ay+r*0.4], fill=LINE)
            d.text((tx, ly2), name, font=fN, fill=INK, anchor='rm' if side == 'L' else 'lm')
            if sub: d.text((tx, ly2 + int(21*k)), sub, font=fS, fill=SUB, anchor='rt' if side == 'L' else 'lt')
    return img
