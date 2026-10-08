import sys
from PIL import Image
def bg(w,h,c0=(196,199,203),c1=(150,154,160)):
    import numpy as np
    y,x=np.mgrid[0:h,0:w]; r=np.sqrt(((x-w*0.5)/(w*0.75))**2+((y-h*0.45)/(h*0.85))**2); r=np.clip(r,0,1)**1.4
    a=np.array(c0)[None,None,:]*(1-r[...,None])+np.array(c1)[None,None,:]*r[...,None]
    return Image.fromarray(a.astype('uint8'),'RGB')
if __name__=='__main__':
    im=Image.open(sys.argv[1]).convert('RGBA'); b=bg(*im.size).convert('RGBA'); b.alpha_composite(im); b.convert('RGB').save(sys.argv[2])
