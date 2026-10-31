import sys, pickle, re
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import trace as T, snes, d65
from collections import Counter
rom = T.rom
CREATORS = {0x88C6E7, 0x8890F8, 0x80F482, 0x85C973, 0x85C911, 0x85C6CC, 0x85C6F7, 0x85C93B, 0x85C915, 0x84E736}
seeds = [(0x8083D7, False, False), (0x808765, False, False), (0x808738, False, False)]
# raw regex seeds: LDA #lo ; LDX #bank ; (LDY #imm)? ; JSL creator   (either order)
pats = [rb'\xa9(?P<lo>..)\xa2(?P<bk>[\x80-\x88\xc0-\xc8])\x00(?:\xa0..)?\x22(?P<t>...)',
        rb'\xa2(?P<bk>[\x80-\x88\xc0-\xc8])\x00\xa9(?P<lo>..)(?:\xa0..)?\x22(?P<t>...)',
        rb'\xa9(?P<lo>..)\xa2(?P<bk>[\x80-\x88\xc0-\xc8])\x00(?:\xa0..)?\x5c(?P<t>...)']
raw = set()
for p in pats:
    for mm in re.finditer(p, rom[:0x90000], re.S):
        t = T.canon(snes.u24(rom, mm.start('t')))
        if t in CREATORS:
            e = (rom[mm.start('bk')] << 16) | snes.u16(rom, mm.start('lo'))
            raw.add(T.canon(e))
print('raw process seeds', len(raw))
T.trace(seeds + [(e, True, True) for e in raw])
for it in range(6):
    # traced-code seeds: walk back from each JSL creator in traced code
    new = set()
    pcs = sorted(T.insns)
    idx = {p: i for i, p in enumerate(pcs)}
    for p in pcs:
        sz, m, x, txt, op, val = T.insns[p]
        if op in (0x22, 0x5C) and T.canon(val) in CREATORS:
            a = k = None
            i = idx[p]
            for j in range(1, 6):
                if i - j < 0: break
                q = pcs[i - j]
                s2, _, _, _, op2, v2 = T.insns[q]
                if op2 == 0xA9 and a is None: a = v2
                if op2 == 0xA2 and k is None: k = v2
            if a is not None and k is not None and (k & 0xFF) in range(0x80, 0x89):
                e = T.canon(((k & 0xFF) << 16) | a)
                if e not in T.insns: new.add(e)
    print('iter', it, 'insns', len(T.insns), 'new seeds', len(new))
    if not new: break
    T.trace([(e, True, True) for e in new])
pickle.dump(dict(insns=T.insns, calls=dict(T.calls), jtables=T.jtables, conflicts=T.conflicts, stops=T.stops),
            open('/home/claude/work/out/umk3/trace.pkl', 'wb'))
print('conflicts', len(T.conflicts), 'stops', len(T.stops), 'jtables', len(T.jtables))
per = Counter(p >> 16 for p in T.insns)
print({hex(k): v for k, v in sorted(per.items())})
c = Counter({t: len(v) for t, v in T.calls.items()})
print([(hex(t), n) for t, n in c.most_common(30)])
