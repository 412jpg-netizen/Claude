"""Find instructions referencing a 16-bit or 24-bit address (cheap byte-pattern xref).
usage: python3 -I xref.py ADDR [rom]   ADDR hex like C3E544 or E544"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import d65, snes

ABS_OPS = [op for op, (mn, mode) in d65.OPS.items() if mode in ('abs', 'absx', 'absy', 'absi', 'absxi', 'absil')]
LONG_OPS = [op for op, (mn, mode) in d65.OPS.items() if mode in ('long', 'longx')]
IMM_OPS = [0xA9, 0xA2, 0xA0, 0xC9, 0xE0, 0xC0, 0x69, 0xE9, 0x29, 0x09, 0x49, 0xF4]


def xref(rom, addr, bank_filter=None, imm=False):
    res = []
    lo = addr & 0xFFFF
    pat2 = bytes([lo & 0xFF, lo >> 8])
    i = rom.find(pat2)
    while i != -1:
        if i >= 1:
            op = rom[i - 1]
            if op in ABS_OPS or (imm and op in IMM_OPS):
                if bank_filter is None or (i >> 16) in bank_filter:
                    res.append((i - 1, d65.OPS[op][0] + ' ' + d65.OPS[op][1]))
            if op in LONG_OPS and False:
                pass
        if i + 2 < len(rom) and i >= 1 and rom[i - 1] in LONG_OPS and (rom[i + 2] & 0x3F) == ((addr >> 16) & 0x3F) and addr > 0xFFFF:
            res.append((i - 1, d65.OPS[rom[i - 1]][0] + ' LONG'))
        i = rom.find(pat2, i + 1)
    return res


if __name__ == '__main__':
    a = int(sys.argv[1], 16)
    rom = snes.load(sys.argv[2] if len(sys.argv) > 2 else 'umk3')
    imm = '-i' in sys.argv
    for off, kind in xref(rom, a, imm=imm):
        print(f'{off:06X} ${snes.to_addr(off):06X} {kind}')
