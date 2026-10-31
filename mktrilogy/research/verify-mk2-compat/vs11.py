"""Render MK3 VS portrait entry 11 (VS tables $80:F414 bank / $80:F432 tiles / $80:F450 map / $80:F46E pal):
tiles $C9:0000 (LZ), map $C9:2A41 (LZ), palette $C9:2B1C; 6bpp 48-B tiles, map value-1 = tile."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
from lz import lz
from PIL import Image
r=D.rom('mk3'); L=len(r)
tiles,ti=lz('mk3',0xC90000); mp,mi=lz('mk3',0xC92A41); print(ti, mi)
po=D.off(0xC92B1C,L); pal=[]
for k in range(64):
    w=D.w16(r,po+2*k); a,b,c=w&31,(w>>5)&31,(w>>10)&31; pal.append((a<<3|a>>2,b<<3|b>>2,c<<3|c>>2))
img=Image.new('RGB',(256,256)); P=img.load()
for i in range(1024):
    w=mp[2*i]|mp[2*i+1]<<8; t=(w&0x3FF)-1
    if t<0 or (t+1)*48>len(tiles): continue
    o=t*48
    for y in range(8):
        for x in range(8):
            v=0
            for pl in range(6): v|=((tiles[o+(pl//2)*16+y*2+(pl&1)]>>(7-x))&1)<<pl
            P[(i%32)*8+x,(i//32)*8+y]=pal[v]
img.crop((0,0,176,128)).resize((352,256)).save('/home/claude/work/out/verify-mk2-compat/mk3_vs11.png')
