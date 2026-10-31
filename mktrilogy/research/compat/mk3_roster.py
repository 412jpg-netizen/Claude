"""MK3 roster: per fighter ID (0-17) the animation table ($86:DC53), first frame of anim 0, sprite set,
primary/alt palette ($86:F3AE/$86:F3C0), and a render with the primary palette.
Also lists the 26 MK3 sprite-set headers ($85:ABAA/$85:ABDE) next to UMK3's 28.
Output: out/compat/mk3_roster.png, text to stdout."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import spr
from c import w16, b8
items = []
for g in ('mk3', 'umk3'):
    G = spr.GAMES[g]
    print(g, 'sets:')
    for s in range(G['nsets']):
        S = spr.Set(g, s)
        print(f'  set {s:2d} hdr {S.hdr and "$%06X" % S.hdr} frames {S.hdr and S.nframes()}')
G = spr.GAMES['mk3']
for fid in range(18):
    t = spr.anim_table('mk3', fid)
    fw = spr.first_frame('mk3', fid)
    pp, pa = b8('mk3', G['prim'] + fid), b8('mk3', G['alt'] + fid)
    im = None
    if fw:
        S = spr.Set('mk3', fw >> 9)
        try:
            im = spr.render(S, fw & 0x1FF, spr.palette('mk3', pp))
        except Exception as e:
            print('render fail', fid, e)
    print(f'fid {fid:2d} anim ${t or 0:06X} frame {fw and "$%04X" % fw} set {fw and fw >> 9} pal {pp:#04x}/{pa:#04x}')
    items.append((f'{fid} s{fw and fw >> 9} p{pp:02X}', im))
spr.sheet(items, '/home/claude/work/out/compat/mk3_roster.png')
