"""Generic wrapper around the UMK3 analyst's LZ port (scripts/umk3/lz.py) for any of the three ROMs.
The MK2 analyst's port (scripts/mk2/mk2lz.py) implements the same format; compat notes section 3.6
shows the two decompressor routines are the same code."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, to_off
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import lz


def decompress(game, addr, maxcmds=1 << 20):
    lz.rom = ROM[game]
    try:
        return lz.decompress(addr, maxcmds)
    finally:
        lz.rom = ROM['umk3']


def try_stream(game, addr, maxsize=0x10000):
    r = ROM[game]
    o = to_off(addr, len(r))
    if o is None or o + 3 >= len(r):
        return None
    size = r[o] | r[o + 1] << 8
    if size == 0 or size > maxsize or r[o + 2] > 3:
        return None
    try:
        d, Y, sz, used = decompress(game, addr, 40000)
    except Exception:
        return None
    return (d, used) if Y == 0 else None
