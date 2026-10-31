"""Local helpers for the UMK3 map. Fixes two problems found in /home/claude/work/lib/snes.py:
 1. snes.to_off masks the bank with $7F before testing for WRAM, so banks $FE/$FF (ROM $3E0000-$3FFFFF)
    are wrongly reported as WRAM ($7E/$7F). to_off() below only treats $7E/$7F as WRAM.
 2. snes.disasm cannot build capstone's 8-bit/8-bit 65816 mode; use d65.py instead.
"""
import sys
sys.path.insert(0, '/home/claude/work/lib')
import snes
from snes import u16, u24, bgr555, decode_tile, tiles_png, load


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


snes.to_off = to_off  # d65 and others in this directory use the fixed mapping
