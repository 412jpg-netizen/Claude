"""Per-frame fraction of non-blank decoded tiles absent from all UMK3 decoded tiles, MK3 sets 18,19,21,22;
render MK3 set 18 frames 200-215 and set 22 frames with >=90% absent."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M, umk3spr as U
from PIL import Image, ImageDraw
utiles=set()
for s in range(28):
    if s==11: continue
    us=U.USet(s)
    for f in range(1,us.nframes_guess()+1):
        for p in us.frame(f)[0]:
            for w in p[4]: utiles.add(us.tile(w)[0])
def frac(st,f):
    ts=[st.tile(w)[0] for p in st.frame(f)[0] for w in p[4]]; nz=[t for t in ts if any(t)]
    return (sum(t not in utiles for t in nz)/len(nz)) if nz else None
res={}
for s in [18,19,21,22]:
    st=U.USet(s,'mk3',0x85ABAA,0x85ABDE); n=st.nframes_guess()
    fr=[(f,frac(st,f)) for f in range(1,n+1)]
    hi=[f for f,x in fr if x is not None and x>=0.9]
    res[s]=hi
    print('set %d: %d frames with >=90%% of non-blank tiles absent from UMK3: %s'%(s,len(hi),hi if len(hi)<60 else str(hi[:30])+'...'))
def sheet(st,frames,path):
    ims=[(f,M.render(st,f)) for f in frames]; W=1400; x=y=H=0; pos=[]
    for f,i in ims:
        if x+i.width>W: x=0; y+=H+12; H=0
        pos.append((x,y,f,i)); x+=i.width+6; H=max(H,i.height)
    img=Image.new('RGB',(W,y+H+12),(0,0,90)); dr=ImageDraw.Draw(img)
    for x,y,f,i in pos: img.paste(i,(x,y+10),i); dr.text((x,y),str(f),fill=(255,255,0))
    img.save(path)
st18=U.USet(18,'mk3',0x85ABAA,0x85ABDE)
print('set18 200-215 fractions',[(f,round(frac(st18,f),2) if frac(st18,f) is not None else None) for f in range(200,216)])
sheet(st18,range(200,216),'/home/claude/work/out/verify-mk2-compat/mk3_set18_200_215.png')
sheet(U.USet(22,'mk3',0x85ABAA,0x85ABDE),res[22],'/home/claude/work/out/verify-mk2-compat/mk3_set22_absent.png')
sheet(U.USet(19,'mk3',0x85ABAA,0x85ABDE),res[19],'/home/claude/work/out/verify-mk2-compat/mk3_set19_absent.png')
