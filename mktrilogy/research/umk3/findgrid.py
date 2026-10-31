"""Search for candidate select-grid tables: runs of >=18 byte or word entries, values 0..27 (or $FF/$FFFF),
with >= 16 distinct fighter IDs."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes
rom = snes.load('umk3')
lim = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x90000
for wdt in (1, 2):
    for start in range(0, lim - 40 * wdt):
        vals = []
        for i in range(32):
            o = start + i * wdt
            v = rom[o] if wdt == 1 else snes.u16(rom, o)
            if v <= 27 or v in (0xFF, 0xFFFF):
                vals.append(v)
            else:
                break
        ids = [v for v in vals if v <= 27]
        if len(vals) >= 18 and len(set(ids)) >= 16 and len(set(ids)) >= 0.8 * len(ids):
            # only report run starts
            prev = start - wdt
            pv = (rom[prev] if wdt == 1 else snes.u16(rom, prev)) if prev >= 0 else 999
            if pv <= 27 or pv in (0xFF, 0xFFFF):
                continue
            print(f'w{wdt} {start:06X} ${u.to_off and 0xC00000 | start:06X} n={len(vals)} ', ' '.join(f'{v:X}' for v in vals))
