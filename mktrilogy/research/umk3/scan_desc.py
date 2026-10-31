"""Brute-force: for a screen/stage record, try every (bank byte, address word) position in each layer descriptor
($84:xxxx) as an LZ stream for $88:AD30 and report those that decompress exactly (final pointer == 0)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes, lz
rom = lz.rom


def try_src(src):
    o = u.to_off(src)
    if o is None or o + 3 >= len(rom):
        return None
    size = snes.u16(rom, o); mode = rom[o + 2]
    if size == 0 or size > 0x10000 or mode > 3:
        return None
    try:
        d, Y, sz, used = lz.decompress(src, maxcmds=20000)
    except Exception:
        return None
    if Y == 0:
        return (sz, mode, used)
    return None


def scan_record(rec):
    o = u.to_off(0x848A22) + 0x22 * rec
    r = rom[o:o + 0x22]
    res = []
    for k in range(4):
        L = snes.u16(r, 8 + 2 * k)
        if L in (0xFFFF, 0x8000):
            continue
        d = rom[u.to_off(0x840000 | L):u.to_off(0x840000 | L) + 0x30]
        for j in range(0, 0x2C):
            bank = d[j]
            if not (0xC0 <= bank <= 0xFF):
                continue
            src = (bank << 16) | snes.u16(d, j + 1)
            t = try_src(src)
            if t:
                res.append((k, L, j, src, t))
    return res


if __name__ == '__main__':
    for rec in [int(a) for a in sys.argv[1:]]:
        for k, L, j, src, (sz, mode, used) in scan_record(rec):
            print(f'rec {rec} layer{k} desc $84{L:04X} +{j:02X}: src ${src:06X} size={sz:#x} mode={mode} stream={used:#x}')
