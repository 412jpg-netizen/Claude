"""Render 24 frames each for MK2 donors (Cage set2, Baraka set3, Raiden set6, Kintaro set9) with D547 palettes."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
from PIL import Image, ImageDraw
r=D.rom('mk2'); L=len(r)
def pal(pid):
    o=D.off(D.w24(r,D.off(0x85D33D+3*pid,L)),L); out=[]
    for i in range(16):
        w=D.w16(r,o+2*i); R,G,B=w&31,(w>>5)&31,(w>>10)&31; out.append((R<<3|R>>2,G<<3|G>>2,B<<3|B>>2))
    return out
def fpal(fid): return pal(r[D.off(0x85D547+fid,L)])
rows=[]
for name,s,fid in [('cage',2,2),('baraka',3,3),('raiden',6,7),('kintaro',9,12)]:
    st=M.Set('mk2',s); n=st.nframes_guess(); fr=[1+int(i*(n-1)/15) for i in range(16)]
    rows.append((name,[M.render(st,f,fpal(fid)) for f in fr]))
W=max(sum(i.width+4 for i in ims) for _,ims in rows)+60; H=sum(max(i.height for i in ims)+4 for _,ims in rows)
img=Image.new('RGB',(W,H),(0,90,0)); dr=ImageDraw.Draw(img); y=0
for nm,ims in rows:
    dr.text((2,y+2),nm,fill=(255,255,0)); x=60
    for im in ims: img.paste(im,(x,y),im); x+=im.width+4
    y+=max(i.height for i in ims)+4
img=img.resize((img.width*3//2,img.height*3//2),Image.NEAREST)
img.save('/home/claude/work/out/verify-mk2-compat/mk2_donors.png'); print(img.size)
