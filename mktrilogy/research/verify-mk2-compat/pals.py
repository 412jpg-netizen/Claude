"""Render MK2 palettes 0-173 (from $85:D33D) and set-7 ninja stance with palettes $17-$26 and D5B7 targets on a set frame."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
from PIL import Image, ImageDraw
r=D.rom('mk2'); L=len(r)
def pal(pid):
    o=D.off(D.w24(r,D.off(0x85D33D+3*pid,L)),L); out=[]
    for i in range(16):
        w=D.w16(r,o+2*i); R,G,B=w&31,(w>>5)&31,(w>>10)&31; out.append((R<<3|R>>2,G<<3|G>>2,B<<3|B>>2))
    return out
# ninja sheet: set 7 frame 1 with pal 0x17..0x26
st=M.Set('mk2',7); ims=[(p,M.render(st,1,pal(p))) for p in range(0x17,0x27)]
W=sum(i.width+6 for _,i in ims); H=max(i.height for _,i in ims)+14
img=Image.new('RGB',(W,H),(0,90,0)); dr=ImageDraw.Draw(img); x=0
for p,i in ims: img.paste(i,(x,14),i); dr.text((x,0),'%02X'%p,fill=(255,255,0)); x+=i.width+6
img.resize((W*2,H*2),Image.NEAREST).save('/home/claude/work/out/verify-mk2-compat/mk2_ninja_pals.png')
# D5B7 targets: each fighter's set frame 1 with D5B7 palette
fs={0:0,1:1,2:2,3:3,4:4,5:4,6:5,7:6,8:7,9:7,10:7,11:8,12:9,13:10,14:7,15:7,16:4}
ims=[]
for fid in range(17):
    p=r[D.off(0x85D5B7+fid,L)]; ims.append((fid,p,M.render(M.Set('mk2',fs[fid]),1,pal(p))))
W=sum(i.width+6 for _,_,i in ims); H=max(i.height for _,_,i in ims)+14
img=Image.new('RGB',(W,H),(0,90,0)); dr=ImageDraw.Draw(img); x=0
for f,p,i in ims: img.paste(i,(x,14),i); dr.text((x,0),'%d:%d'%(f,p),fill=(255,255,0)); x+=i.width+6
img.resize((W*2,H*2),Image.NEAREST).save('/home/claude/work/out/verify-mk2-compat/mk2_d5b7.png')
