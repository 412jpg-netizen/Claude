# Decode every LZ stream reachable from the VS tables and from all layer descriptors (tiles + map fields)
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, lzv
r = v.load('umk3')
streams = set()
for i in range(26):
    b = v.u16(r, 0x83EEC6 + 2 * i) & 0xFF
    if b:
        streams.add(b << 16 | v.u16(r, 0x83EEFA + 2 * i)); streams.add(b << 16 | v.u16(r, 0x83EF2E + 2 * i))
for rec in range(29):
    for L in range(4):
        d = v.u16(r, 0x848A22 + rec * 0x22 + 8 + 2 * L)
        if d < 0x8000 or d in (0xFFFF, 0x8000): continue
        D = 0x840000 | d; t = v.u8(r, D)
        ks = (0x1A, 0x1F) if t == 0 else (0x18, 0x1D) if t == 1 else ()
        for k in ks:
            a = (v.u8(r, D + k) << 16) | v.u16(r, D + k + 1)
            if (a >> 16) >= 0xC0: streams.add(a)
ok = 0; modes = {}
for a in sorted(streams):
    d, info = lzv.decompress(r, a)
    good = info['final_y'] == 0 and info['bad_reads'] == 0 and info['unfilled'] == 0
    ok += good; modes[info['mode']] = modes.get(info['mode'], 0) + 1
    if not good: print('NOT EXACT %06X %s' % (a, info))
print('streams', len(streams), 'exact', ok, 'modes', modes)
