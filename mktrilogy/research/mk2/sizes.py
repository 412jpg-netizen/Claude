"""Per-sprite-set data sizes for MK2 (frames, tile groups, tables). Usage: python3 -I sizes.py"""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g, snes

def interval_union(iv):
    iv=sorted(iv); out=[]
    for a,b in iv:
        if out and a<=out[-1][1]: out[-1][1]=max(out[-1][1],b)
        else: out.append([a,b])
    return out

def analyse(s, verbose=False):
    hd=g.header(s); n=g.nframes(hd)
    franges=[]; words=collections.defaultdict(set); bad=0; maxw=0
    for f in range(1,n+1):
        try:
            fr=g.decode_frame(hd,f)
        except Exception as e:
            bad+=1; continue
        a=snes.to_off(fr['addr'],g.N); e=snes.to_off(fr['end']-1,g.N)+1
        franges.append((a,e))
        for pc in fr['pieces']:
            for w in pc['words']:
                words[(w&0xFC)>>2].add(w>>8)
    fu=interval_union(franges)
    frame_bytes=sum(b-a for a,b in fu)
    groups={}
    for gi,idxs in words.items():
        ent=g.rd(hd['tile_groups']+4*gi,4)
        base=ent[0]|ent[1]<<8|ent[2]<<16
        stride=32 if not ent[3]&0x80 else ent[3]&0x3F
        groups[gi]=(base,stride,max(idxs)+1,len(idxs))
    tile_bytes=sum(st*cnt for base,st,cnt,used in groups.values())
    tbl_bytes = 16 + 3*0 + 2*n + (n+63)//64 + 4*(max(groups)+1) + 32 + (4*n if hd['box_tbl'] else 0)
    return dict(set=s,name=g.SET_NAMES[s],nframes=n,bad=bad,frame_bytes=frame_bytes,frame_runs=len(fu),
                ngroups=max(groups)+1,groups=groups,tile_bytes=tile_bytes,tbl_bytes=tbl_bytes,franges=fu)

if __name__=='__main__':
    allg=collections.defaultdict(list)
    tot=0
    res=[analyse(s) for s in range(17)]
    for R in res:
        print(f"set {R['set']:2d} {R['name'][:28]:28s} frames={R['nframes']:3d} bad={R['bad']} frame_data={R['frame_bytes']:6d}B in {R['frame_runs']} runs  groups={R['ngroups']:2d} tiles={R['tile_bytes']:7d}B  tables~{R['tbl_bytes']}B")
        for gi,(base,st,cnt,used) in R['groups'].items():
            allg[(base,st)].append((R['set'],gi,cnt))
    print('\nshared tile groups (same base used by several sets):')
    for k,v in allg.items():
        if len(set(x[0] for x in v))>1: print('  %06X stride %d:'%k, v)
