"""T1-4/T1-5: MK3 rec 3/9 vs UMK3 rec 0/6 tile overlap, and UMK3 rec 6/7/8 stream health."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
from lz import lz
from stgdesc import descs, safe_lz
from stagetiles import rec_tiles
def recset(g,i):
    s=set()
    for x in rec_tiles(g,i):
        if x and x[0]!='bad': s|=x[1]
    return s
for m,u in [(3,0),(9,6)]:
    A=recset('mk3',m); B=recset('umk3',u)
    print('MK3 rec %d (%d tiles) vs UMK3 rec %d (%d): MK3-in-UMK3 %.1f%%, UMK3-in-MK3 %.1f%%'%(m,len(A),u,len(B),100*len(A&B)/len(A),100*len(A&B)/len(B)))
for i in (6,7,8):
    for k,dd in enumerate(descs('umk3',i)):
        if dd is None: continue
        if dd[0]==0: til=(dd[0x1A]<<16)|D.w16(dd,0x1B); mp=[(dd[0x1F]<<16)|D.w16(dd,0x20),(dd[0x1F]<<16)|D.w16(dd,0x22)]
        else: til=(dd[0x18]<<16)|D.w16(dd,0x19); mp=[(dd[0x1D]<<16)|D.w16(dd,0x1E)]
        print('UMK3 rec %d L%d type %d tiles $%06X %s maps %s'%(i,k,dd[0],til,'ok' if safe_lz('umk3',til) else 'BAD',
              ' '.join('$%06X:%s'%(a,'ok' if safe_lz('umk3',a) else 'BAD') for a in mp)))
