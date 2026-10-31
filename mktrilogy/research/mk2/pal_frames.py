"""Render one stance frame of a sprite set with a list of palette IDs (labelled), to identify palettes."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g
from PIL import Image, ImageDraw
def strip(setid, frame, pids, path, bg=(0,90,0)):
    hd=g.header(setid); fr=g.decode_frame(hd,frame)
    ims=[]
    for p in pids:
        pal=[bg]+g.palette(p)[1:]
        ims.append(g.render(hd,fr,None,pal,scale=2,pad=2))
    W=sum(i.width for i in ims); H=max(i.height for i in ims)+12
    M=Image.new('RGB',(W,H),(30,30,30)); d=ImageDraw.Draw(M); x=0
    for p,i in zip(pids,ims):
        M.paste(i,(x,12)); d.text((x+2,0),'%02X'%p,fill=(255,255,0)); x+=i.width
    M.save(path)
if __name__=='__main__':
    strip(7, 40, list(range(0x17,0x27)), '/home/claude/work/out/mk2/pal_ninja_set7.png')
    strip(4, 40, list(range(0x27,0x32))+[0x9C,0x9D,0x9E], '/home/claude/work/out/mk2/pal_female_set4.png')
    strip(3, 23, [0x39,0x3A,0x3B,0x3C,0x3D,0x3E,0x3F,0x5A,0xA1], '/home/claude/work/out/mk2/pal_baraka_set3.png')
    strip(2, 1, [0x00,0x01,0x02,0x03,0x04,0x05,0x51,0x9B], '/home/claude/work/out/mk2/pal_cage_set2.png')
    strip(6, 1, [0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x56,0xAA], '/home/claude/work/out/mk2/pal_raiden_set6.png')
    strip(9, 34, [0x40,0x41,0x42], '/home/claude/work/out/mk2/pal_kintaro_set9.png')
