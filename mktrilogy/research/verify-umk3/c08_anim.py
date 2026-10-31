import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
from collections import Counter
r = v.load('umk3')
for fid in range(28):
    t = v.u24(r, 0x8895C3 + 4*fid)
    if t == 0:
        print(fid, 'null'); continue
    bank = t & 0xFF0000
    sets = Counter(); first = None
    for an in range(76):  # $98 bytes = 76 words in first table
        sa = bank | v.u16(r, t + 2*an)
        if (sa & 0xFFFF) < 0x8000: continue
        for k in range(24):
            w = v.u16(r, sa + 2*k)
            if w >= 0xFFE0: break
            s = w >> 9
            if first is None and an == 0: first = w
            sets[s] += 1
    print(fid, 'table %06X' % t, 'anim0 first word %s' % (('%04X' % first) if first is not None else None), 'sets', dict(sets.most_common(4)))
