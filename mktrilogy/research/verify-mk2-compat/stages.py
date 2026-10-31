"""Decompress every stream of the 10 MK2 stage records ($82:EDFC, 34 B each) with my LZ port."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
from lz import lz
r=D.rom('mk2'); L=len(r)
def rec(i):
    o=D.off(0x82EDFC+34*i,L); x=r[o:o+34]
    return dict(banks=x[:4], tiles=(x[0]<<16)|D.w16(x,4), meta=(x[1]<<16)|D.w16(x,6), pal=(x[3]<<16)|D.w16(x,8),
                maps=[(x[2]<<16)|D.w16(x,10+2*k) for k in range(12)])
if __name__=='__main__':
    streams={}
    for i in range(10):
        R=rec(i)
        for k,a in [('tiles',R['tiles']),('meta',R['meta'])]+[('map%d'%j,a) for j,a in enumerate(R['maps'])]:
            streams.setdefault(a,[]).append((i,k))
    bad=0; tot=0; types={}
    for a,u in sorted(streams.items()):
        out,inf=lz('mk2',a); tot+=inf['src_len']; types[inf['type']]=types.get(inf['type'],0)+1
        if inf['final_ptr']!=0: bad+=1; print('NONZERO', hex(a), u, inf)
    print('distinct streams', len(streams), 'nonzero end', bad, 'types', types, 'packed bytes', tot)
    for i in range(10):
        R=rec(i); s=0; seen=set()
        for a in [R['tiles'],R['meta']]+R['maps']:
            if a in seen: continue
            seen.add(a); s+=lz('mk2',a)[1]['src_len']
        t=lz('mk2',R['tiles'])[1]; m=lz('mk2',R['meta'])[1]; mp=lz('mk2',R['maps'][0])[1]
        print(i, 'tiles len %d type %d | meta len %d type %d | map0 len %d type %d | packed(record, distinct) %d'%(t['len'],t['type'],m['len'],m['type'],mp['len'],mp['type'],s))
