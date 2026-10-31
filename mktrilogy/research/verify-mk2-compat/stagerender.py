"""Render MK2 stage records to PNG using my LZ port and the $82:F1AB metatile expansion.
BG layer A = blocks 0-9 (5x2 blocks of 32x32 tiles, $82:F0F3 loop), layer B = blocks 10-11 (2x1)."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
from lz import lz
from stages import rec
from mk2spr import planar
from PIL import Image
r=D.rom('mk2'); L=len(r)
def render(i, palbase=0):
    R=rec(i)
    tiles,_=lz('mk2',R['tiles']); meta,_=lz('mk2',R['meta'])
    po=D.off(R['pal'],L); pal=[]
    for k in range(96):
        w=D.w16(r,po+2*k); a,b,c=w&31,(w>>5)&31,(w>>10)&31; pal.append((a<<3|a>>2,b<<3|b>>2,c<<3|c>>2))
    cache={}
    def tilepx(t):
        if t not in cache:
            o=t*32
            cache[t]=planar(tiles[o:o+32]) if o+32<=len(tiles) else [[0]*8 for _ in range(8)]
        return cache[t]
    def block(a):
        m,_=lz('mk2',a); img=Image.new('RGB',(256,256)); px=img.load()
        for my in range(16):
            for mx in range(16):
                w=m[2*(my*16+mx)]|m[2*(my*16+mx)+1]<<8; mt=(w&0x3FF)*8
                for q,(dx,dy) in enumerate([(0,0),(8,0),(0,8),(8,8)]):
                    tw=meta[mt+2*q]|meta[mt+2*q+1]<<8
                    t=tw&0x3FF; pl=(tw>>10)&7; hf=tw&0x4000; vf=tw&0x8000
                    p=tilepx(t)
                    for yy in range(8):
                        for xx in range(8):
                            v=p[7-yy if vf else yy][7-xx if hf else xx]
                            ci=((pl-palbase)%6)*16+v
                            px[mx*16+dx+xx,my*16+dy+yy]=pal[ci] if v else (0,0,0)
        return img
    A=Image.new('RGB',(5*256,2*256))
    for b in range(10): A.paste(block(R['maps'][b]),((b%5)*256,(b//5)*256))
    Bimg=Image.new('RGB',(2*256,256))
    for b in range(2): Bimg.paste(block(R['maps'][10+b]),(b*256,0))
    return A,Bimg
if __name__=='__main__':
    ids=[int(x) for x in sys.argv[1:]] or list(range(10))
    for i in ids:
        A,B=render(i)
        A.save('/home/claude/work/out/verify-mk2-compat/stage%d_A.png'%i); B.save('/home/claude/work/out/verify-mk2-compat/stage%d_B.png'%i)
        print('stage',i,'ok')
