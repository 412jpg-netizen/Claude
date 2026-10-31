"""Find runs of consecutive 24-bit ROM pointers (bank byte $C0-$FF or $80-$BF) of length >= N."""
import sys
sys.path.insert(0, '/home/claude/work/lib'); import snes
rom = snes.load('umk3')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
lim = int(sys.argv[2], 16) if len(sys.argv) > 2 else len(rom)
res = []
for phase in range(3):
    o = phase; run = []
    while o + 3 <= lim:
        b = rom[o + 2]; lo = snes.u16(rom, o)
        ok = (0xC0 <= b <= 0xFF) or (0x80 <= b <= 0xBF and lo >= 0x8000)
        if ok:
            run.append(o)
        else:
            if len(run) >= N: res.append((run[0], len(run)))
            run = []
        o += 3
    if len(run) >= N: res.append((run[0], len(run)))
res.sort()
for s, n in res:
    ents = [snes.u24(rom, s + 3 * i) for i in range(min(n, 6))]
    print(f'{s:06X} ${snes.to_addr(s):06X} n={n:3d} ', ' '.join(f'{e:06X}' for e in ents))
