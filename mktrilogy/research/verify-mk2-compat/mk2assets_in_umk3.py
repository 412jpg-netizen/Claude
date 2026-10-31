"""How many MK2 sprite/stage/palette bytes are covered by k=32 matches in UMK3?"""
import sys, numpy as np, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
from lz import lz
from stages import rec
r=D.rom('mk2'); L=len(r)
cov=np.load('/home/claude/work/out/verify-mk2-compat/cov_mk2_in_umk3_k32.npy')
spr=np.zeros(L,bool)
for s in range(17):
    st=M.Set('mk2',s); n=st.nframes_guess(); gm={}
    for f in range(1,n+1):
        pcs,ln,a=st.frame(f); o=D.off(a,L); spr[o:o+ln]=True
        for p in pcs:
            for w in p[4]: g=(w&0xFC)>>2; gm[g]=max(gm.get(g,-1),w>>8)
    for g,mx in gm.items():
        lo,bank,flag=st.group(g); sd=(flag&0x3F) if flag&0x80 else 32; o=D.off((bank<<16)|lo,L); spr[o:o+(mx+1)*sd]=True
stg=np.zeros(L,bool)
for i in range(10):
    R=rec(i)
    for a in [R['tiles'],R['meta']]+R['maps']:
        o=D.off(a,L); stg[o:o+lz('mk2',a)[1]['src_len']]=True
    o=D.off(R['pal'],L); stg[o:o+192]=True
pal=np.zeros(L,bool)
o=D.off(0x85D33D,L)
for i in range(174):
    po=D.off(D.w24(r,o+3*i),L); pal[po:po+32]=True
for nm,mask in [('sprite frames+tiles',spr),('stage streams+palettes',stg),('fighter palettes',pal)]:
    c=cov&mask; print('%-24s bytes %8d  covered-by-UMK3-match %6d'%(nm,mask.sum(),c.sum()))
    if c.sum():
        idx=np.nonzero(c)[0]; runs=[]; s=idx[0]; pr=s
        for x in idx[1:]:
            if x!=pr+1: runs.append((s,pr)); s=x
            pr=x
        runs.append((s,pr))
        for a,b in runs[:12]:
            seg=r[a:b+1]; print('     $%06X-$%06X %d B  distinct byte values %d'%(0xC00000|a,0xC00000|b,b-a+1,len(set(seg))))
