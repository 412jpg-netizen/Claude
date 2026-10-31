import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
r = v.load('umk3')
def cstr(a, mx=40):
    s = b''
    while len(s) < mx:
        c = v.u8(r, a); 
        if c == 0: break
        s += bytes([c]); a += 1
    return s
base = 0x83E544
for i in range(30):
    p = v.u16(r, base + 2*i)
    s = cstr(0x830000 | p) if p >= 0x8000 else b''
    print(i, '%04X' % p, s)
print('xrefs to E544 (abs) in bank 83:')
for o, op in v.abs_xrefs(r, 0xE544):
    if (o >> 16) == 3: print('  %06X op %02X' % (o, op))
print('long xrefs', [(hex(o), hex(op)) for o, op, t in v.long_xrefs(r, 0x83E544)])
