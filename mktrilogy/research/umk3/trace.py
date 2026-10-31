"""Recursive-descent 65816 tracer for UMK3 code banks ($80-$88).
Produces a pickle with: insns {pc: (size, m16, x16, text, op, val)}, xrefs, jsl/jsr targets.
Heuristics (documented in notes):
 - flags assumed preserved across JSR/JSL;
 - PHP/PLP tracked along a linear path;
 - process-entry seeds from 'LDA #lo ; LDX #bank ; JSL creator' patterns;
 - JMP/JSR (abs,X) tables read until an entry is not a plausible same-bank code address.
"""
import sys, pickle, re
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, d65, snes
from collections import defaultdict

rom = snes.load('umk3')
CODE_BANKS = set(range(0x80, 0x89))
insns = {}
conflicts = set()
calls = defaultdict(set)     # target -> set(callers)
jtables = {}
stops = set()
INLINE = {}   # routine addr -> number of inline arg bytes after JSL (filled later)
NORETURN = set()


def canon(a):
    b = a >> 16
    if b < 0x40: b |= 0x80
    if 0xC0 <= b <= 0xC8: b = b - 0x40  # $C0-$C8 code executes the same as $80-$88
    return (b << 16) | (a & 0xFFFF)


def plausible(a):
    return (a >> 16) in CODE_BANKS and (a & 0xFFFF) >= 0x8000


def trace(seeds):
    work = list(seeds)
    while work:
        pc, m, x = work.pop()
        pc = canon(pc)
        pstack = []
        while True:
            if not plausible(pc):
                break
            if pc in insns:
                if (insns[pc][1], insns[pc][2]) != (m, x):
                    conflicts.add(pc)
                break
            d = d65.dis1(rom, pc, m, x)
            op = d['op']
            if op in (0x00, 0x02, 0xDB, 0x42):  # BRK/COP/STP/WDM -> almost surely data
                stops.add(pc)
                break
            insns[pc] = (d['size'], m, x, d['text'], op, d['val'])
            nxt = d['next']
            if op == 0xC2:
                if d['val'] & 0x20: m = True
                if d['val'] & 0x10: x = True
            elif op == 0xE2:
                if d['val'] & 0x20: m = False
                if d['val'] & 0x10: x = False
            elif op == 0x08:
                pstack.append((m, x))
            elif op == 0x28:
                if pstack: m, x = pstack.pop()
            mode = d['mode']
            if mode in ('rel', 'rell') and d['mn'] not in ('PER',):
                work.append((d['val'], m, x))
                if d['mn'] in ('BRA', 'BRL'):
                    break
            elif op == 0x4C:  # JMP abs
                work.append(((pc & 0xFF0000) | d['val'], m, x)); break
            elif op == 0x5C:
                work.append((d['val'], m, x)); break
            elif op == 0x20:
                t = canon((pc & 0xFF0000) | d['val']); calls[t].add(pc)
                work.append((t, m, x))
                if t in NORETURN: break
                nxt = (pc & 0xFF0000) | ((pc + 3 + INLINE.get(t, 0)) & 0xFFFF)
            elif op == 0x22:
                t = canon(d['val']); calls[t].add(pc)
                work.append((t, m, x))
                if t in NORETURN: break
                nxt = (pc & 0xFF0000) | ((pc + 4 + INLINE.get(t, 0)) & 0xFFFF)
            elif op in (0x7C, 0xFC):  # JMP/JSR (abs,X): jump table in same bank
                base = (pc & 0xFF0000) | d['val']
                ents = []
                o = snes.to_off(base, len(rom))
                for k in range(64):
                    t = (pc & 0xFF0000) | snes.u16(rom, o + 2 * k)
                    if not plausible(t) or t == base: break
                    ents.append(t)
                jtables[pc] = (base, ents)
                for t in ents: work.append((t, m, x))
                if op == 0x7C: break
            elif op in (0x60, 0x6B, 0x40, 0x6C, 0xDC):
                break
            pc = nxt
