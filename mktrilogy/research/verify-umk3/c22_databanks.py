# Collect bank bytes used by the data structures decoded in this verification and flag any
# that would be remapped by an ExHiROM conversion ($00-$3F upper half or $40-$7D).
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, spr
from collections import Counter
r = v.load('umk3')
def bad(b): return b < 0x80 and b not in (0x7E, 0x7F)
found = Counter(); flagged = []
def note(kind, b, where):
    found[(kind, b)] += 1
    if bad(b): flagged.append((kind, hex(b), where))
for s in range(28):
    H = spr.set_header(s)
    if not H: continue
    h = v.bytes_at(r, H['addr'], 16)
    for k in (4, 7, 0xB): note('set-hdr+%X' % k, h[k], s)
    note('set-hdr-bank', H['addr'] >> 16, s)
    # frame count from the frame table length: scan bank table up to 8 entries (512 frames max)
    nfr = 0
    for f0 in range(511):
        bk = v.u8(r, H['banktab'] + (f0 >> 6))
        ad = v.u16(r, H['frametab'] + 2 * f0)
        if ad < 0x8000 and bk < 0xC0: break
        nfr += 1
    for i in range((nfr + 63) // 64):
        note('frame-bank', v.u8(r, H['banktab'] + i), s)
    for e in range(64):
        a = H['dir'] + 4 * e
        bk = v.u8(r, a + 2)
        if v.u16(r, a) == 0 and bk == 0: continue
        note('tiledir-bank', bk, (s, e))
for i in range(309): note('paltab', v.u24(r, 0x889984 + 3 * i) >> 16, i)
for i in range(28):
    p = v.u24(r, 0x8895C3 + 4 * i)
    if p: note('animtab', p >> 16, i)
for i in range(26):
    b = v.u16(r, 0x83EEC6 + 2 * i) & 0xFF
    if b: note('vs-bank', b, i)
# layer descriptors of all 29 records (type 1: +15,+18,+1D bank bytes; type 0 not decoded -> skip)
for rec in range(29):
    for L in range(4):
        d = v.u16(r, 0x848A22 + rec * 0x22 + 8 + 2 * L)
        if d in (0xFFFF, 0x8000) or d < 0x8000: continue
        D = 0x840000 | d
        if v.u8(r, D) == 1:
            for k in (0x15, 0x18, 0x1D):
                b = v.u8(r, D + k)
                if b not in (0xFF,) or k != 0x15 or True: note('L1desc+%X' % k, b, (rec, L))
print('flagged (bank < $80, not WRAM):', flagged[:30], 'count', len(flagged))
kinds = {}
for (k, b), n in found.items(): kinds.setdefault(k, set()).add(b)
for k in sorted(kinds): print(k, sorted(hex(b) for b in kinds[k]))
