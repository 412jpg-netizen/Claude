"""Heuristic: rank JSL targets in MK2 code banks by decompressor-like features."""
import sys; sys.path.insert(0,'/home/claude/work/lib'); sys.path.insert(0,'/home/claude/work/scripts/mk2')
import snes, d65, collections
r=snes.load('mk2')
targets=collections.Counter()
for o in range(0,0x60000-4):
    if r[o]==0x22 and r[o+3] in (0x80,0x81,0x82,0x83,0x84,0x85):
        targets[(r[o+3]<<16)|snes.u16(r,o+1)]+=1
res=[]
for t,c in targets.items():
    if (t&0xffff)<0x8000: continue
    ins=d65.disasm(r,t,150,stop=False)
    # cut at first rtl
    txt=[]
    for a,b,x in ins:
        txt.append(x)
        if x.startswith('rtl'): break
    sh=sum(1 for x in txt if x.split()[0] in ('asl','lsr','rol','ror'))
    ind=sum(1 for x in txt if '[' in x and x.split()[0] in ('lda','ora','and','eor'))
    st=sum(1 for x in txt if x.split()[0]=='sta' and ('$7F' in x or '[' in x or ',x' in x or ',y' in x))
    score=sh+2*ind+st
    res.append((score,t,c,sh,ind,st,len(txt)))
res.sort(reverse=True)
for s in res[:40]:
    print('score=%d %06X calls=%d shifts=%d indlong=%d stores=%d len=%d'%s)
