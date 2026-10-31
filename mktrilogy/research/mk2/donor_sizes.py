"""Byte budget per fighter sprite set (everything except move code), for ROM-expansion planning."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g, snes
from sizes import analyse
# anim block = set header .. next block start (blocks are laid back to back; verified in anims.py output)
ANIM_BLOCK = {0:(0x8596BA,0x859E20),1:(0x84F109,0x84F8BB),2:(0x858000,0x8587B6),3:(0x8587B6,0x858F48),
              4:(0x84B4EE,0x84BE4F),5:(0x84D8E2,0x84E158),6:(0x858F48,0x8596BA),7:(0x84A067,0x84AA85),
              8:(0x84E158,0x84E91A),9:(0x82FE13,0x82FFD1),10:(0x85D9E7,0x85DBC3)}
TABLES=[0x85D547,0x85D558,0x85D569,0x85D57A,0x85D5B7]
def pal_ids(s):
    ids=set()
    for fid in range(17):
        if g.FIGHTER_SET[fid]!=s: continue
        for t in TABLES:
            v=g.b8(t+fid)
            if v==0 and t==0x85D57A: continue   # 00 in the effect2 table = none (Baraka, Mileena)
            if v<0xAE: ids.add(v)
        if fid<12: ids.add(g.b8(0x85D58B+fid))
    return sorted(ids)
if __name__=='__main__':
    print('%-26s %6s %8s %8s %6s %6s %6s %6s %6s %8s' % ('set','frames','tiles','framedat','ftbls','shadow','anim','pals','misc','TOTAL'))
    for s in range(11):
        R=analyse(s); h=g.header(s); n=R['nframes']
        ftbl=2*n+(n+63)//64+4*R['ngroups']+32+16+(4*n if h['box_tbl'] else 0)+(2*n if h['dbg_tbl'] else 0)
        sh=0
        if h['dbg_tbl']:
            ps=[g.w16(h['dbg_tbl']+2*i) for i in range(n)]; ps=[p for p in ps if p!=0xFFFF]
            sh=(h['dbg_tbl']&0xFFFF)-min(ps)
        a=ANIM_BLOCK[s]; an=a[1]-a[0]
        pids=pal_ids(s); pb=32*len(pids)
        tot=R['tile_bytes']+R['frame_bytes']+ftbl+sh+an+pb
        print('%-26s %6d %8d %8d %6d %6d %6d %6d %6s %8d  pal IDs %s' % (g.SET_NAMES[s][:26],n,R['tile_bytes'],R['frame_bytes'],ftbl,sh,an,pb,'',tot,' '.join('%02X'%p for p in pids)))

    # effect-set frames referenced directly by each donor's animation scripts (lower bound)
    import anims, collections
    for fids,nc in [([2],66),([3],66),([7],66),([12],24)]:
        m,fr,ns=anims.set_block(fids,nc)
        eff=sorted(f for f in fr if (f>>9)>=11)
        bysets=collections.Counter(f>>9 for f in eff)
        nb=0; tiles=set()
        for f in eff:
            h=g.header(f>>9); d=g.decode_frame(h,f&0x1FF); nb+=d['end']-d['addr']
            for pc in d['pieces']:
                for w in pc['words']: tiles.add((f>>9,w&0xFFFC))
        tb=0
        for (st,w) in tiles:
            h=g.header(st); tb+=len(g.tile_bytes(h,w)[1].get('src') and g.tile_bytes(h,w)[0])
        print('%-12s effect frames referenced by scripts: %d (%s) frame bytes %d, distinct tiles %d (~%d B decoded)' % (
            g.NAMES[fids[0]], len(eff), ', '.join('set%d x%d'%k for k in sorted(bysets.items())), nb, len(tiles), 32*len(tiles)))
