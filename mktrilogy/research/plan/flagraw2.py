"""Critic check (follow-up to flagraw.py): the kode flags are word pairs cleared by the loop at
$80:8653-$80:86A9 (STZ base,X with X = 2, 0), so the flags named in the $85:EA3E message table
(e.g. 2X DAMAGE $3BDC) are base+2 of a pair. Search UMK3 code banks for indexed reads of the pair
bases (LDA/CMP/ORA/AND abs,X or abs,Y) and for direct reads of base+0. Raw byte search, so LIKELY.
Output: out/plan/flagraw2.txt
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM
r = ROM['umk3']
BASES = {0x3BDA: '2X DAMAGE pair', 0x3BD6: '2X HEALTH pair', 0x3BF2: 'HYPER KOMBAT pair',
         0x3C22: 'SHADOW FIGHTING pair', 0x3BE2: 'ONE BUTTON FATALITIES pair', 0x3C1E: 'ALL BACKGROUND BLAST pair',
         0x3BFE: 'UNLIMITED RUN? pair', 0x3C02: '? pair', 0x3BEA: 'kode 5 pair', 0x3BEE: 'RANDPER pair'}
OPS = {0xBD: 'LDA abs,X', 0xB9: 'LDA abs,Y', 0xDD: 'CMP abs,X', 0xD9: 'CMP abs,Y', 0x3D: 'AND abs,X',
       0x1D: 'ORA abs,X', 0xAD: 'LDA abs', 0xCD: 'CMP abs', 0xFE: 'INC abs,X', 0xEE: 'INC abs', 0x9D: 'STA abs,X'}
out = []
for base, name in BASES.items():
    hits = []
    for v in (base, base + 2):
        lo, hi = v & 0xFF, v >> 8
        for off in range(0x008000, 0x090000):
            if (off & 0xFFFF) < 0x8000 or (off & 0xFFFF) > 0xFFFC:
                continue
            if r[off + 1] == lo and r[off + 2] == hi and r[off] in OPS:
                hits.append(f'${0x80 | (off >> 16):02X}:{off & 0xFFFF:04X} {OPS[r[off]]} ${v:04X}')
    out.append(f'## ${base:04X} {name}: {len(hits)} raw hits')
    out += ['   ' + h for h in hits[:20]]
open('/home/claude/work/out/plan/flagraw2.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
