"""Render sample frames of every MK2 sprite set with my decoder -> out/verify-mk2-compat/mk2_sets.png"""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
from PIL import Image, ImageDraw
r=D.rom('mk2'); L=len(r)
def pal(pid):
    p=D.w24(r,D.off(0x85D33D+3*pid,L)); o=D.off(p,L)
    out=[]
    for i in range(16):
        w=D.w16(r,o+2*i); R,G,B=w&31,(w>>5)&31,(w>>10)&31
        out.append((R<<3|R>>2,G<<3|G>>2,B<<3|B>>2))
    return out
setpal={0:17,1:68,2:0,3:57,4:39,5:75,6:50,7:23,8:12,9:64,10:94}
rows=[]
for s in range(17):
    st=M.Set('mk2',s); n=st.nframes_guess() or 60
    fr=[1+int(i*(n-1)/13) for i in range(14)]
    ims=[]
    for f in fr:
        try: ims.append(M.render(st,f,pal(setpal[s]) if s in setpal else None))
        except Exception as e: ims.append(Image.new('RGBA',(16,16),(255,0,0,255)))
    rows.append((s,n,ims))
W=max(sum(i.width+4 for i in ims) for _,_,ims in rows)+60
H=sum(max(i.height for i in ims)+4 for _,_,ims in rows)
img=Image.new('RGB',(W,H),(40,40,90)); dr=ImageDraw.Draw(img); y=0
for s,n,ims in rows:
    dr.text((2,y+2),'%d n%d'%(s,n),fill=(255,255,0)); x=60
    for im in ims: img.paste(im,(x,y),im); x+=im.width+4
    y+=max(i.height for i in ims)+4
img.save('/home/claude/work/out/verify-mk2-compat/mk2_sets.png'); print(img.size)
