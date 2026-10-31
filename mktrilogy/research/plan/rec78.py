"""Critic check: UMK3 stage records 7 and 8 (dead stubs, compat T1-5) as reusable slots.
Prints, for records 0-10 and 23, the 4 layer-descriptor words at record +8..+F (bank $84,
$FFFF = none) and, for each descriptor, its type byte and whether other records share it.
Record table $84:8A22, $22 bytes per record (verified C17). Output: out/plan/rec78.txt
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import w16, b8
from collections import defaultdict
users = defaultdict(list)
rows = []
for rec in range(29):
    base = 0x848A22 + rec * 0x22
    ds = [w16('umk3', base + 8 + 2 * i) for i in range(4)]
    for d in ds:
        if d not in (0xFFFF, 0x8000):
            users[d].append(rec)
    rows.append((rec, ds))
out = []
for rec, ds in rows:
    if rec not in list(range(0, 11)) + [23]:
        continue
    parts = []
    for d in ds:
        if d in (0xFFFF, 0x8000):
            parts.append(f'{d:04X}')
        else:
            parts.append(f'{d:04X}(type {b8("umk3", 0x840000 | d)}, recs {users[d]})')
    out.append(f'rec {rec:2}: ' + '  '.join(parts))
open('/home/claude/work/out/plan/rec78.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
