# Prueft die Netzliste des Lochraster-Plans (make_5b.py) gegen die Schaltung aus gehaeuse/ANLEITUNG.md 7c.
import re, itertools, collections
import os
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_5b.py')).read()
ns = {}
for name in ("BRIDGES","JUMPERS","PADS","ADAPT","RES","T1","ELKO"):
    m = re.search(r"^%s\s*=\s*(\[.*?\]|\{.*?\})\s*$" % name, src, re.S|re.M)
    ns[name] = eval(m.group(1))
# union find
par={}
def f(x):
    par.setdefault(x,x)
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
def u(a,b): par[f(a)]=f(b)
for net,ch in ns['BRIDGES']:
    for a,b in zip(ch,ch[1:]):
        # adjacency check
        ca,ra=int(a[1:]),a[0]; cb,rb=int(b[1:]),b[0]
        assert abs(ca-cb)+abs(ord(ra)-ord(rb))==1,(a,b)
        u(a,b)
for net,a,b in ns['JUMPERS']: u(a,b)
# nets by named
netof = {}
for net,ch in ns['BRIDGES']:
    for h in ch: netof.setdefault(h,set()).add(net)
for net,a,b in ns['JUMPERS']:
    pass
# connectivity classes
cls = collections.defaultdict(list)
for h in list(par): cls[f(h)].append(h)
# component pins
pins = {}   # hole -> label
for nm,c0,p in ns['ADAPT']:
    for h,l in p.items(): pins[h]=f"{nm}.{l}"
for r,v,a,b in ns['RES']: pins[a]=r+".1"; pins[b]=r+".2"
for h,l in ns['T1'].items(): pins[h]="T1."+l
for h,l in ns['ELKO'].items(): pins[h]="C1"+l
for nr,h,net,k,l in ns['PADS']: pins[h]=(pins.get(h,"")+" P%d"%nr).strip()
# hole used twice?
used = collections.Counter()
for nm,c0,p in ns['ADAPT']:
    for h in p: used[h]+=1
for r,v,a,b in ns['RES']: used[a]+=1; used[b]+=1
for h in ns['T1']: used[h]+=1
for h in ns['ELKO']: used[h]+=1
for nr,h,*_ in ns['PADS']: used[h]+=1
print("holes used by >1 component pin/Litze:", [h for h,c in used.items() if c>1])
# all holes involved
allh = set(pins)|set(par)
for nm,c0,p in ns['ADAPT']:
    pass
# net membership
nets = []
seen=set()
for root,hs in cls.items(): pass
# build nets including isolated pin holes
groups = collections.defaultdict(set)
for h in allh: groups[f(h)].add(h)
for root,hs in sorted(groups.items(), key=lambda kv: sorted(kv[1])[0]):
    labels = sorted(pins[h] for h in hs if h in pins)
    print(sorted(hs), "->", labels)
# check nets in each class declared colour unique
for root,hs in groups.items():
    ns_ = set()
    for h in hs: ns_ |= netof.get(h,set())
    if len(ns_)>1: print("COLOUR MIX", hs, ns_)
# expected netlist from ANLEITUNG 7c
exp = {
 'V5':   {"Q1.S","C1+","R1.2","P1"},
 'GND':  {"C1−","T1.E","R3.2","P2","P4","P9"},
 'GQ1':  {"Q1.G","R1.1","T1.C"},
 'LED+': {"Q1.D","P3"},
 'BASE': {"T1.B","R2.2","R3.1"},
 'IO18': {"R2.1","P5"},
 'GQ2':  {"Q2.G","R4.1","P7"},
 'BAT':  {"Q2.S","R4.2","P6","P8"},
 'VIN':  {"Q2.D","P10"},
}
got=[]
for root,hs in groups.items():
    s=set()
    for h in hs:
        if h in pins:
            for t in pins[h].split(): s.add(t)
    got.append(s)
# map R/Pin names: R1.1=F03, R1.2=F04 (R1.1 is Gate side); R2.1=G01 (GPIO18), R2.2=G02; R3.1=H02 (base),R3.2=I02; R4.1=F07,R4.2=F08
print()
for k,e in exp.items():
    ok = any(g_==e for g_ in got)
    print(k, "OK" if ok else "MISMATCH", e if ok else [x for x in got if x&e])
unmatched=[g_ for g_ in got if not any(g_==e for e in exp.values())]
print("unmatched groups:", unmatched)
# adjacency risk: neighbours with different classes, both populated holes
print("\nAdjacent populated holes in different nets (Brueckenrisiko):")
def hn(h): return (h[0],int(h[1:]))
pop = sorted(allh)
cl = {h:f(h) for h in pop}
rk=[]
for a,b in itertools.combinations(pop,2):
    (ra,ca),(rb,cb)=hn(a),hn(b)
    if abs(ord(ra)-ord(rb))+abs(ca-cb)==1 and cl[a]!=cl[b]:
        rk.append((a,b))
print(len(rk)); print(rk)
