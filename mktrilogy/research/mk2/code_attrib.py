"""Attribute code locations to sprite sets: find `lda #$xxxx` immediates that are frame words
(set<<9|frame, frame<=nframes(set)) consumed within 4 instructions by jsl $83:EF0C (set frame) or
sta $4C3C,x/y. Prints, per set, the sorted addresses (clustered)."""
import sys, collections; sys.path.insert(0,'/home/claude/work/lib'); sys.path.insert(0,'/home/claude/work/scripts/mk2')
import snes, d65, mk2gfx as g
r=g.ROM
NF=[g.nframes(g.header(s)) for s in range(17)]
hits=collections.defaultdict(list)
for o in range(0,0x60000-3):
    if (o & 0xFFFF) < 0x8000 or r[o]!=0xA9: continue
    v=snes.u16(r,o+1); s=v>>9; f=v&0x1FF
    if s>16 or f==0 or f>NF[s]: continue
    ins=d65.disasm(r,0x800000|o,5,stop=False)
    if any(t in ('jsl $83EF0C','sta $4C3C,x','sta $4C3C,y') for _,_,t in ins[1:]):
        hits[s].append(0x800000|o)
for s in sorted(hits):
    a=hits[s]
    cl=[]; 
    for x in a:
        if cl and x-cl[-1][1] < 0x400 and (x>>16)==(cl[-1][1]>>16): cl[-1][1]=x; cl[-1][2]+=1
        else: cl.append([x,x,1])
    print('set %2d %-12s %3d refs: %s' % (s, g.SET_NAMES[s][:12], len(a), ' '.join('%06X-%04X(%d)'%(c[0],c[1]&0xFFFF,c[2]) for c in cl)))
