import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
r = v.load('umk3')
T = 0x889984
def ok_ptr(p):
    if (p >> 16) < 0xC0 and not (0x80 <= (p >> 16) < 0xC0 and (p & 0xFFFF) >= 0x8000):
        return False
    o = v.off(p, len(r))
    if o is None or o + 32 > len(r): return False
    ws = [r[o+2*i] | r[o+2*i+1] << 8 for i in range(16)]
    return all(w < 0x8000 for w in ws)
n = 0
first_bad = None
for i in range(400):
    p = v.u24(r, T + 3*i)
    if not ok_ptr(p):
        first_bad = i; break
print('consecutive valid palette pointers from $88:9984:', first_bad, 'end addr $%06X' % (T + 3*first_bad))
# report the boundary entries
for i in (0, 1, 307, 308, 309, 310):
    print(i, '%06X' % v.u24(r, T + 3*i))
print('bytes at 9D23..', v.bytes_at(r, 0x889D23, 8).hex())
banks = sorted(set(v.u24(r, T + 3*i) >> 16 for i in range(309)))
print('banks used', [hex(b) for b in banks])
ps = [v.u24(r, T + 3*i) for i in range(309)]
print('min %06X max %06X distinct %d' % (min(ps), max(ps), len(set(ps))))
# xrefs
for tgt in (0x889984, 0x889985, 0x889986, 0xC89984, 0xC89986):
    print('long', hex(tgt), [(hex(o), hex(op)) for o, op, t in v.long_xrefs(r, tgt)])
print('abs $9984/$9986 in code banks 0-8:', [(hex(0x800000|o), hex(op)) for o, op in v.abs_xrefs(r, 0x9984, set(range(9)))], [(hex(0x800000|o), hex(op)) for o, op in v.abs_xrefs(r, 0x9986, set(range(9)))])
# Any immediate #$9984 (pointer-building)?
for o in v.find_all(r, bytes([0xA9, 0x84, 0x99])) + v.find_all(r, bytes([0xA2, 0x84, 0x99])) + v.find_all(r, bytes([0xA0, 0x84, 0x99])):
    if (o >> 16) < 9: print('imm #$9984 at %06X' % (0x800000|o))
# raw 24-bit pointer to table stored anywhere
print('raw ptr hits', [hex(o) for o in v.find_all(r, bytes([0x84, 0x99, 0x88])) + v.find_all(r, bytes([0x84, 0x99, 0xC8]))])
