# Per set: frame count from layout (frame table directly followed by bank table), parse every frame,
# collect the tile-directory entries actually referenced and their bank bytes + frame bank bytes.
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, spr
from collections import Counter
r = v.load('umk3')
allb = Counter(); bad = []
for s in range(28):
    H = spr.set_header(s)
    if not H: continue
    ft, bt = H['frametab'], H['banktab']
    if (ft >> 16) == (bt >> 16) and bt > ft:
        nfr = (bt - ft) // 2
    else:
        nfr = None
    fbanks = sorted(set(v.u8(r, bt + i) for i in range(((nfr or 64) + 63) // 64)))
    used = set(); perr = 0
    for f0 in range(nfr or 0):
        fid = (s << 9) | (f0 + 1)
        try:
            _, ps = spr.pieces(fid)
            if len(ps) > 128: perr += 1; continue
            for (_, _, _, refs) in ps:
                for rf in refs: used.add(rf & 0xFC)
        except Exception:
            perr += 1
    dbanks = sorted(set(v.u8(r, H['dir'] + d + 2) for d in used))
    flags = sorted(set(v.u8(r, H['dir'] + d + 3) & 0xC0 for d in used))
    for b in fbanks + dbanks:
        allb[b] += 1
        if b < 0x80: bad.append((s, hex(b)))
    print('set %2d frames %s  frame-banks %s  dir entries used %d  dir banks %s  flags %s  parse-errors %d' % (
        s, nfr, [hex(b) for b in fbanks], len(used), [hex(b) for b in dbanks], [hex(f) for f in flags], perr))
print('any bank byte < $80:', bad)
