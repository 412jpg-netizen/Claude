import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M, umk3spr as U
from PIL import Image, ImageDraw
r=D.rom('umk3'); L=len(r)
o=D.off(0x86EAEC,L); o2=D.off(0x86EB24,L)
rows=[]
for s in range(28):
    try:
        st=U.USet(s); n=st.nframes_guess() or 40
    except Exception as e:
        print(s,'hdr err',e); continue
    fr=[1+int(i*(n-1)/11) for i in range(12)]; ims=[]
    for f in fr:
        try: ims.append(M.render(st,f))
        except Exception as e: ims.append(Image.new('RGBA',(8,8),(255,0,0,255)))
    rows.append((s,n,st.hdr_addr,ims))
W=max(sum(i.width+4 for i in ims) for *_,ims in rows)+90; H=sum(max(i.height for i in ims)+4 for *_,ims in rows)
img=Image.new('RGB',(W,H),(40,40,120)); dr=ImageDraw.Draw(img); y=0
for s,n,h,ims in rows:
    dr.text((2,y+2),'%d n%d'%(s,n),fill=(255,255,0)); x=90
    for im in ims: img.paste(im,(x,y),im); x+=im.width+4
    y+=max(i.height for i in ims)+4
img.save('/home/claude/work/out/verify-mk2-compat/umk3_sets.png'); print(img.size, len(rows))
