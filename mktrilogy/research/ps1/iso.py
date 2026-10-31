"""Minimal ISO9660 reader for a PS1 MODE2/2352 track (Form 1 user data at +24)."""
import sys, struct
SEC = 2352
class Disc:
    def __init__(s, path): s.f = open(path, 'rb')
    def sector(s, lba):
        s.f.seek(lba * SEC + 24); return s.f.read(2048)
    def read(s, lba, size):
        out = bytearray()
        n = (size + 2047) // 2048
        for i in range(n): out += s.sector(lba + i)
        return bytes(out[:size])
    def entries(s, lba, size):
        data = s.read(lba, size); p = 0; out = []
        while p < len(data):
            L = data[p]
            if L == 0: p = (p // 2048 + 1) * 2048; continue
            elba = struct.unpack_from('<I', data, p + 2)[0]; esz = struct.unpack_from('<I', data, p + 10)[0]
            fl = data[p + 25]; nl = data[p + 32]; name = data[p + 33:p + 33 + nl]
            if name not in (b'\x00', b'\x01'): out.append((name.decode('ascii', 'replace'), elba, esz, bool(fl & 2)))
            p += L
        return out
    def walk(s, lba=None, size=None, prefix=''):
        if lba is None:
            pvd = s.sector(16); root = pvd[156:190]
            lba = struct.unpack_from('<I', root, 2)[0]; size = struct.unpack_from('<I', root, 10)[0]
        for name, elba, esz, isdir in s.entries(lba, size):
            path = prefix + '/' + name
            yield path, elba, esz, isdir
            if isdir: yield from s.walk(elba, esz, path)
if __name__ == '__main__':
    d = Disc(sys.argv[1])
    for p, l, sz, isd in d.walk(): print('%-40s lba %6d size %9d%s' % (p, l, sz, ' DIR' if isd else ''))
