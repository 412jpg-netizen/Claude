"""Common helpers for the compat analysis (MK3 vs UMK3, MK2 vs UMK3).

Uses the shared lib for loading and the UMK3 analyst's table-driven 65816 disassembler
(/home/claude/work/scripts/umk3/d65.py), which works in every M/X mode.  d65 imports umk3/u.py,
which monkey-patches snes.to_off so that banks $FE/$FF are ROM (shared-lib bug, see notes).
to_off() below is our own copy of the fixed mapping; it takes the ROM size into account (MK2 = 3 MB).
"""
import sys
sys.path.insert(0, '/home/claude/work/lib')
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import snes
import d65  # noqa: E402  (also patches snes.to_off)

ROM = {n: snes.load(n) for n in ('mk2', 'mk3', 'umk3')}


def to_off(addr, size=0x400000):
    bank, lo = (addr >> 16) & 0xFF, addr & 0xFFFF
    if bank in (0x7E, 0x7F):
        return None
    b = bank & 0x7F
    if b >= 0x40:
        off = ((b - 0x40) << 16) | lo
    elif lo >= 0x8000:
        off = (b << 16) | lo
    else:
        return None
    return off % size


def rd(game, addr, n):
    r = ROM[game]
    o = to_off(addr, len(r))
    return r[o:o + n]


def b8(game, addr):
    return rd(game, addr, 1)[0]


def w16(game, addr):
    return int.from_bytes(rd(game, addr, 2), 'little')


def p24(game, addr):
    return int.from_bytes(rd(game, addr, 3), 'little')


def show(game, addr, n=40, m16=True, x16=True, stop=True, file=None):
    d65.show(ROM[game], addr, n, m16, x16, stop, file=file)


def lst(game, addr, n=40, m16=True, x16=True, stop=True):
    return d65.lst(ROM[game], addr, n, m16, x16, stop)


def A(off):
    """file offset -> $C0-$FF style address string"""
    return '$%02X:%04X' % (0xC0 | (off >> 16), off & 0xFFFF)
