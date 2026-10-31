"""T2-8: per-frame 8x8-tile and piece counts: MK2 donors vs UMK3 maxima."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M, umk3spr as U
def stats(st):
    mt=mp=0; at=None
    for f in range(1,st.nframes_guess()+1):
        pcs=st.frame(f)[0]; t=sum(4 if p[2] else 1 for p in pcs)
        if t>mt: mt=t; at=f
        mp=max(mp,len(pcs))
    return mt,mp,at
for nm,s in [('Cage',2),('Baraka',3),('Raiden',6),('Kintaro',9)]:
    print(nm, 'max tiles/pieces', stats(M.Set('mk2',s)))
best=[]
for s in range(28):
    if s==11: continue
    mt,mp,at=stats(U.USet(s)); best.append((mt,mp,s,at))
print('UMK3 max tiles', max(best), ' max pieces', max(best,key=lambda x:x[1]))
