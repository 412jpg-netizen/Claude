"""T1-3: MK3 sets 18/19/21/22 footprints and k=32 coverage in UMK3; per-frame 'unique' (no byte of frame
data or its tiles covered) lists; renders."""
import sys, numpy as np, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M, umk3spr as U
from PIL import Image, ImageDraw
L=4<<20
cov=np.load('/home/claude/work/out/verify-mk2-compat/cov_mk3_in_umk3_k32.npy')
# all UMK3 decoded tiles (content) for tile-level comparison
utiles=set()
for s in range(28):
    if s==11: continue
    us=U.USet(s)
    for f in range(1,us.nframes_guess()+1):
        for p in us.frame(f)[0]:
            for w in p[4]: utiles.add(us.tile(w)[0])
def mk3set(s): return U.USet(s,'mk3',0x85ABAA,0x85ABDE)
for s in [18,19,21,22]:
    st=mk3set(s); n=st.nframes_guess(); foot=np.zeros(L,bool); refs=collections.defaultdict(set)
    uniqf=[]
    for f in range(1,n+1):
        pcs,ln,a=st.frame(f); o=D.off(a,L); foot[o:o+ln]=True
        ts=[st.tile(w)[0] for p in pcs for w in p[4]]
        nz=[t for t in ts if any(t)]
        if nz and not any(t in utiles for t in nz): uniqf.append(f)
        for p in pcs:
            for w in p[4]: refs[(w&0xFC)>>2].add(w>>8)
    for g,idxs in refs.items():
        lo,bank,flag=st.group(g); o=D.off((bank<<16)|lo,L); mx=max(idxs)
        if flag&0x80: sd=flag&0x3F; T=st.r[o]; ln=1+(mx+1)*sd+(1 if mx>=T else 0)
        else: ln=(mx+1)*(16 if flag&0x40 else 32)
        foot[o:o+ln]=True
    print('MK3 set %d: frames %d footprint %d B, not covered by UMK3 %d B; frames whose non-blank tiles are all absent from UMK3: %d %s'%(
        s,n,foot.sum(),(foot&~cov).sum(),len(uniqf),uniqf if len(uniqf)<40 else (uniqf[:20],'...')))
    sel=uniqf if s!=21 else uniqf[::max(1,len(uniqf)//24)]
    ims=[(f,M.render(st,f)) for f in sel[:40]]
    if ims:
        W=min(1600,sum(i.width+6 for _,i in ims)); rows=[];
        x=0; y=0; H=0; pos=[]
        for f,i in ims:
            if x+i.width>W: x=0; y+=H+12; H=0
            pos.append((x,y,f,i)); x+=i.width+6; H=max(H,i.height)
        img=Image.new('RGB',(W,y+H+12),(0,0,90)); dr=ImageDraw.Draw(img)
        for x,y,f,i in pos: img.paste(i,(x,y+10),i); dr.text((x,y),str(f),fill=(255,255,0))
        img.save('/home/claude/work/out/verify-mk2-compat/mk3_set%d_uniq.png'%s)
