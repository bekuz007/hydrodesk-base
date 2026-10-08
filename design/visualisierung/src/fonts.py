from PIL import ImageFont
INTER='/usr/share/fonts/truetype/sand-box/google/Inter/Inter-VariableFont_opsz,wght.ttf'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
_cache={}
def F(size, w=400):
    k=(size,w)
    if k not in _cache:
        f=ImageFont.truetype(INTER, size)
        try: f.set_variation_by_axes([min(32,max(14,size)), w])
        except Exception: pass
        _cache[k]=f
    return _cache[k]
