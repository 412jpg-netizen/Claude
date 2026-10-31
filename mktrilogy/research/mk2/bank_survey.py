import sys; sys.path.insert(0,'/home/claude/work/lib'); import snes
import math, collections
r=snes.load('mk2')
for b in range(len(r)//0x10000):
    d=r[b*0x10000:(b+1)*0x10000]
    c=collections.Counter(d)
    ent=-sum(v/len(d)*math.log2(v/len(d)) for v in c.values())
    # count JSL to bank C0-C2 / 80-82 patterns and RTS/RTL
    jsl=sum(1 for i in range(len(d)-3) if d[i]==0x22 and d[i+3] in (0x80,0x81,0x82,0x83,0xC0,0xC1,0xC2,0xC3))
    ff=c[0xFF]; z=c[0]
    print(f'bank {b:02X} ent={ent:.3f} 00={z:5d} FF={ff:5d} JSL~={jsl:4d} top={c.most_common(3)}')
