"""Overview sheets: every ~n/20-th frame of each sprite set, coloured with the main palette of the
first fighter that uses the set (effect/UI sets 11-16 in grey). Output out/mk2/overview_setNN.png
and overview_part0..2.png."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g
from PIL import Image
for s in range(17):
    h=g.header(s); n=g.nframes(h)
    fids=[f for f in range(17) if g.FIGHTER_SET[f]==s]
    pal=[(0,96,0)]+g.palette(g.b8(g.PAL_ID_MAIN+fids[0]))[1:] if fids else None
    g.sheet(s, list(range(1,n+1,max(1,n//20)))[:20], '/home/claude/work/out/mk2/overview_set%02d.png'%s, pal=pal, cols=10, cell=(100,120))
ims=[Image.open('/home/claude/work/out/mk2/overview_set%02d.png'%s) for s in range(17)]
for k,(a,b) in enumerate([(0,6),(6,12),(12,17)]):
    W=max(i.width for i in ims[a:b]); H=sum(i.height for i in ims[a:b]); M=Image.new('RGB',(W,H)); y=0
    for i in ims[a:b]: M.paste(i,(0,y)); y+=i.height
    M.save('/home/claude/work/out/mk2/overview_part%d.png'%k)
