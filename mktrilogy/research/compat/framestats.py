"""Per-set frame statistics: max number of 16x16 pieces (B), max 8x8 pieces (N-B), max 8x8 tiles (4B + N-B),
for MK2 and UMK3 sprite sets -- to check whether MK2 frames fit the UMK3 per-object VRAM/OAM budget
(the piece-placement tables $84:C7EA/$86:E3DA are identical, 24 entries; see compat notes 3.4)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import spr
from c import b8
for g in ('mk2', 'umk3'):
    seen = set()
    allmx = [0, 0, 0, 0]
    for s in range(spr.GAMES[g]['nsets']):
        S = spr.Set(g, s)
        if S.hdr is None or S.hdr in seen:
            continue
        seen.add(S.hdr)
        mb = ms = mt = mn = 0
        for f in range(1, S.nframes() + 1):
            a = S.frame_addr(f)
            n, bb = b8(g, a), b8(g, a + 1)
            if bb > n:
                continue
            mb, ms, mt, mn = max(mb, bb), max(ms, n - bb), max(mt, 4 * bb + n - bb), max(mn, n)
        allmx = [max(x, y) for x, y in zip(allmx, (mb, ms, mt, mn))]
        print(f'{g} set {s:2d}: max 16x16 {mb:3d}, max 8x8 {ms:3d}, max tiles {mt:3d}, max pieces {mn:3d}')
    print(f'{g} overall: max 16x16 {allmx[0]}, max 8x8 {allmx[1]}, max tiles {allmx[2]}, max pieces {allmx[3]}')
