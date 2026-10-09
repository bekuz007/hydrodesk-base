# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE
from PIL import Image, ImageDraw, ImageFilter
import math
from fonts import F
S=4  # scale of 240x320 TFT
def screen():
    W,H=240*S,320*S
    im=Image.new('RGB',(W,H),(0,0,0)); d=ImageDraw.Draw(im)
    def t(x,y,s,txt,col,w=500,anchor='la'): d.text((x*S,y*S),txt,font=F(int(s*S),w),fill=col,anchor=anchor)
    t(8,6,22,'14:23',(255,255,255),600)
    t(8,42,10,'Di 06.10.2026',(200,200,200),500)
    # bluetooth symbol (connected, blue with dots)
    bx,by=179,6; blue=(40,140,255)
    pts=[(bx-5,by+5),(bx+5,by+14),(bx,by+18),(bx,by),(bx+5,by+4),(bx-5,by+13)]
    d.line([(p[0]*S,p[1]*S) for p in pts],fill=blue,width=2*S,joint='curve')
    d.rectangle([169*S,14*S,172*S,17*S],fill=blue); d.rectangle([188*S,14*S,191*S,17*S],fill=blue)
    # battery
    d.rectangle([196*S,8*S,228*S,23*S],outline=(255,255,255),width=S)
    d.rectangle([228*S,12*S,231*S,19*S],fill=(255,255,255))
    d.rectangle([198*S,10*S,(198+int(28*0.88))*S,21*S],fill=(40,200,80))
    t(234,28,15,'88 %',(255,255,255),600,'ra')
    d.line([8*S,56*S,232*S,56*S],fill=(60,60,60),width=S)
    t(120,62,10,'heute getrunken',(150,150,150),500,'ma')
    t(112,74,40,'1.250',(255,255,255),700,'ma'); t(178,98,15,'ml',(255,255,255),500)
    t(120,124,14,'von 2.750 ml',(200,200,200),500,'ma')
    bx0,by0,bw,bh=12,148,216,24
    d.rectangle([bx0*S,by0*S,(bx0+bw)*S,(by0+bh)*S],fill=(50,50,50))
    d.rectangle([bx0*S,by0*S,int((bx0+bw*0.45)*S),(by0+bh)*S],fill=(0,170,255))
    d.rectangle([bx0*S,by0*S,(bx0+bw)*S,(by0+bh)*S],outline=(255,255,255),width=S)
    t(120,152,14,'45 %',(255,255,255),600,'ma')
    t(120,184,10,'noch 1.500 ml',(150,150,150),500,'ma')
    d.line([8*S,197*S,232*S,197*S],fill=(60,60,60),width=S)
    t(10,201,14,'Flasche: 420/750 ml',(0,220,230),600)
    t(10,219,8.5,'Leer 250 g (kalibriert) | Kap. 750 ml',(150,150,150),500)
    for x,lab,col in [(6,'Leer',(0,90,40)),(124,'Voll',(0,90,40))]:
        d.rounded_rectangle([x*S,230*S,(x+110)*S,282*S],radius=8*S,fill=col,outline=(255,255,255),width=S)
        t(x+55,247,16,lab,(255,255,255),600,'ma')
    d.rounded_rectangle([6*S,286*S,234*S,316*S],radius=6*S,fill=(0,0,0))
    t(120,296,9.5,'Zuletzt: vor 12 min | Err. 15:40',(150,150,150),500,'ma')
    im.save('tex/screen_ui.png')

def rain_plate():
    W,H=400,540; im=Image.new('RGB',(W,H),(18,110,110)); d=ImageDraw.Draw(im)
    sil=(205,205,200); m=20
    d.rectangle([m,m,W-m,H-m-40],outline=sil,width=6)
    # interdigitated comb
    for i,y in enumerate(range(m+20,H-m-60,22)):
        if i%2==0: d.rectangle([m,y,W-m-28,y+8],fill=sil)
        else: d.rectangle([m+28,y,W-m,y+8],fill=sil)
    d.rectangle([150,H-60,170,H-10],fill=sil); d.rectangle([230,H-60,250,H-10],fill=sil)
    d.ellipse([10,H-40,34,H-16],outline=sil,width=4); d.ellipse([W-34,H-40,W-10,H-16],outline=sil,width=4)
    im.save('tex/rain_plate.png')

def cutting_mat():
    # 1 px = 0.5 mm ; mat 480 x 300 mm
    pmm=4; Wmm,Hmm=480,300
    W,H=Wmm*pmm,Hmm*pmm
    im=Image.new('RGB',(W,H),(36,88,78)); d=ImageDraw.Draw(im)
    for xm in range(0,Wmm+1,10):
        w=3 if xm%50==0 else 1; c=(190,215,205) if xm%50==0 else (120,165,150)
        d.line([xm*pmm,0,xm*pmm,H],fill=c,width=w)
    for ym in range(0,Hmm+1,10):
        w=3 if ym%50==0 else 1; c=(190,215,205) if ym%50==0 else (120,165,150)
        d.line([0,ym*pmm,W,ym*pmm],fill=c,width=w)
    # ruler numbers along bottom (cm)
    for i,xm in enumerate(range(10,Wmm,10)):
        d.text((xm*pmm,(Hmm-4)*pmm),str(xm//10),font=F(22,500),fill=(200,225,215),anchor='mb')
    im=im.filter(ImageFilter.GaussianBlur(0.6))
    im.save('tex/cutting_mat.png')

def battery_label():
    W,H=560,345; im=Image.new('RGB',(W,H),(52,54,58)); d=ImageDraw.Draw(im)
    d.rectangle([20,20,W-20,H-20],outline=(150,150,150),width=3)
    d.text((40,40),'LiPo  3,7 V',font=F(60,700),fill=(235,235,235))
    d.text((40,120),'2000 mAh  ·  7,4 Wh',font=F(42,500),fill=(210,210,210))
    d.text((40,190),'LP103454',font=F(40,500),fill=(170,170,170))
    d.text((40,250),'+  rot   −  schwarz',font=F(32,500),fill=(170,170,170))
    im.save('tex/battery_label.png')

def loadcell_label():
    W,H=800,127; im=Image.new('RGB',(W,H),(200,202,206)); d=ImageDraw.Draw(im)
    d.text((W*0.30,H/2),'5 kg',font=F(64,700),fill=(60,60,60),anchor='mm')
    d.text((W*0.72,H/2),'→',font=F(64,700),fill=(60,60,60),anchor='mm')
    im.save('tex/loadcell_label.png')

screen(); rain_plate(); cutting_mat(); battery_label(); loadcell_label()
print('ok')
