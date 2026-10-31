import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, spr
r = v.load('umk3')
for s in (0, 13, 17, 18, 20, 21, 24, 25):
    H = spr.set_header(s)
    nfr = (H['banktab'] - H['frametab']) // 2
    users = {}
    for f0 in range(nfr):
        fid = (s << 9) | (f0 + 1)
        _, ps = spr.pieces(fid)
        for (_, _, _, refs) in ps:
            for rf in refs:
                d = rf & 0xFC
                if v.u8(r, H['dir'] + d + 2) < 0x80:
                    users.setdefault(d, set()).add(f0 + 1)
    for d, fr in users.items():
        e = H['dir'] + d
        print('set %2d dir+%02X entry @%06X: addr %04X bank %02X flags %02X  used by %d frames e.g. %s' % (
            s, d, e, v.u16(r, e), v.u8(r, e + 2), v.u8(r, e + 3), len(fr), sorted(fr)[:6]))
