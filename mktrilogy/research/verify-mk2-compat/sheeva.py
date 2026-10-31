"""T1-2: MK3 set 11 footprint, its k=32 coverage in UMK3, decoded-tile overlap with all UMK3 frames, render."""
import sys, numpy as np, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M, umk3spr as U
from PIL import Image
m3=D.rom('mk3'); L=len(m3)
cov=np.load('/home/claude/work/out/verify-mk2-compat/cov_mk3_in_umk3_k32.npy')
def footprint(st):
    n=st.nframes_guess(); fr=np.zeros(L,bool); tl=np.zeros(L,bool); refs=collections.defaultdict(set)
    for f in range(1,n+1):
        pcs,ln,a=st.frame(f); o=D.off(a,st.L); fr[o:o+ln]=True
        for p in pcs:
            for w in p[4]: refs[(w&0xFC)>>2].add(w>>8)
    for g,idxs in refs.items():
        lo,bank,flag=st.group(g); o=D.off((bank<<16)|lo,st.L); mx=max(idxs)
        if flag&0x80:
            s=flag&0x3F; T=st.r[o]; ln=1+(mx+1)*s+(1 if mx>=T else 0)
        else: ln=(mx+1)*(16 if flag&0x40 else 32)
        tl[o:o+ln]=True
    return n,fr,tl,refs
st=U.USet(11,'mk3',0x85ABAA,0x85ABDE)
n,fr,tl,refs=footprint(st)
tb=16+2*n+(n+63)//64+4*(max(refs)+1)+32+(2*n if st.sh!=0xFFFF else 0)+(4*n if st.box!=0xFFFF else 0)
print('MK3 set 11 frames',n,'frame bytes',fr.sum(),'tile bytes',tl.sum(),'tables~',tb,'total~',fr.sum()+tl.sum()+tb)
print('footprint bytes covered by >=32-byte matches in UMK3:', (cov&(fr|tl)).sum())
# decoded tiles
mk3tiles=set(); mk3ref=0
for g,idxs in refs.items():
    for i in idxs: mk3tiles.add(st.tile((i<<8)|(g<<2))[0]); mk3ref+=1
u=set()
for s in range(28):
    if s==11: continue
    us=U.USet(s); 
    for f in range(1,us.nframes_guess()+1):
        for p in us.frame(f)[0]:
            for w in p[4]: u.add(us.tile(w)[0])
print('MK3 set11 distinct (group,idx) tiles',mk3ref,' distinct contents',len(mk3tiles),' contents also decoded in UMK3:',len(mk3tiles&u))
ims=[M.render(st,f) for f in [1+int(i*(n-1)/9) for i in range(10)]]
W=sum(i.width+4 for i in ims); H=max(i.height for i in ims)
img=Image.new('RGB',(W,H),(0,0,90)); x=0
for i in ims: img.paste(i,(x,0),i); x+=i.width+4
img.resize((W*2,H*2)).save('/home/claude/work/out/verify-mk2-compat/mk3_set11.png')
