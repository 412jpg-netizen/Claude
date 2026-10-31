"""T2-7: first frame of common anims k=0..39: MK2 Liu Kang (fighter 1, $85:C49E) vs UMK3 fighter 13 ($88:95C3)."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M, umk3spr as U
from PIL import Image, ImageDraw
def first_frame(g,tbl,fid,k):
    r=D.rom(g); L=len(r); c=D.w24(r,D.off(tbl+4*fid,L)); bank=c>>16
    lo=D.w16(r,D.off(c+2*k,L))
    if lo==0: return None
    p=lo
    for _ in range(20):
        w=D.w16(r,D.off((bank<<16)|p,L)); p+=2
        if w==0 or w>=0xFFEA: 
            if w in (0xFFFE,0xFFF7): continue
            if w in (0xFFF9,0xFFFD): p+=2; continue
            if w in (0xFFFC,0xFFFA): p+=4; continue
            return None
        return w
    return None
rows=[]
for k in range(40):
    a=first_frame('mk2',0x85C49E,1,k); b=first_frame('umk3',0x8895C3,13,k)
    ia=M.render(M.Set('mk2',a>>9),a&0x1FF) if a else Image.new('RGBA',(8,8))
    ib=M.render(U.USet(b>>9),b&0x1FF) if b else Image.new('RGBA',(8,8))
    rows.append((k,a,b,ia,ib))
W=10*110; img=Image.new('RGB',(W,4*2*110),(0,0,80)); dr=ImageDraw.Draw(img)
for k,a,b,ia,ib in rows:
    x=(k%10)*110; y=(k//10)*220
    img.paste(ia,(x,y+10),ia); img.paste(ib,(x,y+120),ib); dr.text((x,y),'k%d'%k,fill=(255,255,0))
img.save('/home/claude/work/out/verify-mk2-compat/animcmp_lk.png'); print('ok')
