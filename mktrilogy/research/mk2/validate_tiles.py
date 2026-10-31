"""Validate the bucketed zero-mask tile format: for every tile referenced by every frame of every
sprite set, check that 4 + popcount(mask bytes) == group stride (compressed groups)."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g
stat=collections.Counter(); ex=[]
for s in range(17):
    hd=g.header(s)
    for f in range(1,g.nframes(hd)+1):
        for pc in g.decode_frame(hd,f)['pieces']:
            for w in pc['words']:
                tb,info=g.tile_bytes(hd,w)
                if info['raw']: stat['raw']+=1; continue
                if info['used']==info['stride']: stat['exact']+=1
                elif info['used']<info['stride']: stat['short']+=1; ex.append((s,f,hex(w),info))
                else: stat['over']+=1; ex.append((s,f,hex(w),info))
print(stat); print(ex[:10])
