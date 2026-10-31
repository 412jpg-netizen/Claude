"""Compare animation numbering of the common animation tables: MK2 $85:C49E (via $85:C47D, wrapper $83:F347)
vs UMK3 $88:95C3 (via $88:95A0, wrapper $88:8A24 -- the same code shape, findcode.py).  For a fighter present in
both games, render the first frame of common animation k for k = 0..N-1 side by side.
usage: python3 -I animcmp.py mk2_fid umk3_fid [N]   (default Liu Kang: 1 13)"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import spr
from c import w16, b8
fm, fu = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 13)
N = int(sys.argv[3]) if len(sys.argv) > 3 else 76


def first(game, fid, k, nmax):
    t = spr.anim_table(game, fid)
    s = (t & 0xFF0000) | w16(game, t + 2 * k)
    for _ in range(40):
        v = w16(game, s)
        if v == 0xFFFF:
            s = (s & 0xFF0000) | w16(game, s + 2); continue
        if v == 0xFFF8:
            s = (s & 0xFF0000) | w16(game, s + 3) if b8(game, s + 2) == fid else s + 5; continue
        if v in (0xFFFD, 0xFFF9):
            s += 4; continue
        if v == 0xFFFC or v == 0xFFFA:
            s += 6; continue
        if v >= 0xFFEA or v == 0:
            s += 2; continue
        if (v >> 9) < nmax:
            return v
        s += 2
    return None


items = []
for k in range(N):
    for g, fid in (('mk2', fm), ('umk3', fu)):
        try:
            v = first(g, fid, k, spr.GAMES[g]['nsets']) if not (g == 'mk2' and k >= 66) else None
        except TypeError:
            v = None
        im = None
        if v:
            try:
                im = spr.render(spr.Set(g, v >> 9), v & 0x1FF, spr.palette(g, b8(g, spr.GAMES[g]['prim'] + fid)), scale=1)
            except Exception:
                im = None
        items.append((f'{g} a{k}', im))
spr.sheet(items, f'/home/claude/work/out/compat/animcmp_mk2_{fm}_umk3_{fu}.png', cell=(80, 110), cols=16)
