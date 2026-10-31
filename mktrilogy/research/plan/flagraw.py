"""Critic check: raw byte-pattern search (not traced, so LIKELY) in UMK3 code banks $80-$88 for
absolute / long reads of the kode flags whose traced-ref count was 0 (flagrefs.py).
Opcodes: AD (LDA abs), AF (LDA long, bank $7E/$00), CD (CMP abs), 2C (BIT abs), AE/AC (LDX/LDY abs).
Output: out/plan/flagraw.txt
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM
r = ROM['umk3']
FL = {0x3BF4: 'HYPER KOMBAT', 0x3C24: 'SHADOW FIGHTING', 0x3BDC: '2X DAMAGE', 0x3BD8: '2X HEALTH',
      0x3BE4: 'ONE BUTTON FATALITIES', 0x3C1C: 'HEALTH RECOVERY'}
OPS = {0xAD: 'LDA', 0xCD: 'CMP', 0x2C: 'BIT', 0xAE: 'LDX', 0xAC: 'LDY', 0x0D: 'ORA'}
out = []
for v, name in FL.items():
    lo, hi = v & 0xFF, v >> 8
    hits = []
    for off in range(0x008000, 0x090000):
        if (off & 0xFFFF) < 0x8000:
            continue
        if r[off + 1] == lo and r[off + 2] == hi:
            if r[off] in OPS:
                hits.append(f'${0x80 | (off >> 16):02X}:{off & 0xFFFF:04X} {OPS[r[off]]} ${v:04X}')
            elif r[off] == 0xAF and r[off + 3] in (0x7E, 0x00):
                hits.append(f'${0x80 | (off >> 16):02X}:{off & 0xFFFF:04X} LDA ${r[off+3]:02X}{v:04X}')
    out.append(f'## ${v:04X} {name}: {len(hits)} raw hits: ' + '; '.join(hits[:12]))
open('/home/claude/work/out/plan/flagraw.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
