"""Worked example for the notes: Baraka (fighter 3, sprite set 3), stance animation (common anim 0)."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g, anims, snes
from PIL import Image
h=g.header(3)
print('header @%06X:'%h['addr'], {k:('%06X'%v if isinstance(v,int) else v) for k,v in h.items() if k not in ('raw','addr')})
c,s,cp,sp=anims.fighter_anims(3)
items,fr,(a,e)=anims.parse_script(c>>16,g.w16(c))
print('common anim 0 script @%06X-%06X:'%(a,e), items)
f=0x64
fa=g.frame_addr(h,f); d=g.decode_frame(h,f)
print('frame %d: bank byte table[%d]=%02X, ptr table entry @%06X -> frame @%06X, %d bytes, count=%d n16=%d' % (
    f,(f-1)>>6,g.b8(h['frame_bank_tbl']+((f-1)>>6)),h['frame_ptr_tbl']+2*(f-1),fa,d['end']-fa,d['count'],d['n16']))
for i,p in enumerate(d['pieces'][:4]):
    print('  piece',i,p)
box=g.rd(h['box_tbl']+4*(f-1),4)
print('  body box bytes (x1,x2,y1,y2 as signed):',[b-256 if b>127 else b for b in box])
print('  shadow ptr:', '%04X'%g.w16(h['dbg_tbl']+2*(f-1)))
w=d['pieces'][0]['words'][0]
tb,info=g.tile_bytes(h,w); print('  first tile word %04X ->'%w, info)
# donor montage
ims=[]
for fid,fno in [(3,0x64),(2,0x61),(7,0x61),(12,0x27)]:
    hh=g.header(g.FIGHTER_SET[fid]); pal=[(0,90,0)]+g.palette(g.b8(g.PAL_ID_MAIN+fid))[1:]
    ims.append(g.render(hh,g.decode_frame(hh,fno),None,pal,scale=3,pad=4))
W=sum(i.width for i in ims); H=max(i.height for i in ims)
M=Image.new('RGB',(W,H),(30,30,30)); x=0
for i in ims: M.paste(i,(x,H-i.height)); x+=i.width
M.save('/home/claude/work/out/mk2/donors_decoded.png'); print('saved donors_decoded.png')
