"""T1-4: per-record decoded-tile overlap, MK3 stage/screen records vs all UMK3 records (32-byte chunks)."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
from stgdesc import descs, safe_lz, REC
def rec_tiles(g,i):
    per=[]
    for k,dd in enumerate(descs(g,i)):
        if dd is None: per.append(None); continue
        if dd[0]==0: a=(dd[0x1A]<<16)|D.w16(dd,0x1B)
        elif dd[0]==1: a=(dd[0x18]<<16)|D.w16(dd,0x19)
        else: per.append(None); continue
        x=safe_lz(g,a)
        if x is None: per.append(('bad',a)); continue
        out=x[0]; ts=set(out[j:j+32] for j in range(0,len(out)-31,32)); ts.discard(bytes(32))
        per.append((a,ts))
    return per
U=collections.defaultdict(set); urec={}
for i in range(REC['umk3'][2]):
    urec[i]=rec_tiles('umk3',i)
    for x in urec[i]:
        if x and x[0]!='bad': U['all'].update(x[1])
for i in range(REC['mk3'][2]):
    per=rec_tiles('mk3',i); s=[]
    for k,x in enumerate(per):
        if x is None: continue
        if x[0]=='bad': s.append('L%d bad'%k); continue
        a,ts=x; f=len(ts&U['all'])/len(ts) if ts else 0
        # best single UMK3 record match
        best=max(((len(ts&set().union(*[y[1] for y in urec[j] if y and y[0]!='bad']))/len(ts) if ts else 0),j) for j in urec)
        s.append('L%d $%06X %4d tiles %5.1f%% in UMK3 (best rec %d %.0f%%)'%(k,a,len(ts),100*f,best[1],100*best[0]))
    print('MK3 rec %2d: '%i+' | '.join(s))
