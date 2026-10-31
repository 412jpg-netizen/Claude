"""Attribute MK3 bytes to known structures and report what is NOT found in UMK3 per category.
Categories (first match wins, in this order):
  sprite set N  - spr/foot.py footprint of MK3 set N (header, tables, frames, tile records)
  stage/screen  - packed LZ tiles/map streams + palette blocks of MK3 records ($82:B888, stagecmp.py)
  vs portrait   - packed tiles/map + 64-colour palette of MK3 VS portraits (vscmp.py)
  palette       - 32-byte palettes pointed to by MK3 palette table $86:F0FC (230 entries)
  code-bank     - upper half ($8000-$FFFF) of file banks $00-$08 (code banks $80-$88; contains some data)
  other         - everything else
'unique' = not covered by a >=32-byte block match in UMK3 (blockmatch.py mk3 umk3 32).
Writes out/compat/attrib_mk3.pkl (category array) and prints a summary + largest unique 'other' runs.
usage: python3 -I attrib.py
"""
import sys, pickle
import numpy as np
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, to_off, w16, p24, A
import spr, foot, stagecmp, vscmp, glz
from blockmatch import runs

g = 'mk3'
N = len(ROM[g])
cat = np.full(N, -1, np.int16)   # -1 other; 0..25 sprite set; 100 stage; 101 vs; 102 palette; 103 code-bank
labels = {100: 'stage/screen', 101: 'vs portrait', 102: 'palette', 103: 'code-bank', -1: 'other'}


def mark(a, n, c, by_off=False):
    o = a if by_off else to_off(a, N)
    if o is None:
        return
    sl = cat[o:o + n]
    sl[sl == -1] = c


seen = {}
for s in range(26):
    S = spr.Set(g, s)
    if S.hdr is None or S.hdr in seen:
        continue
    seen[S.hdr] = s
    F, _ = foot.footprint(S)
    for k in F:
        idx = np.fromiter(F[k], int)
        sub = cat[idx]
        cat[idx[sub == -1]] = s
    labels[s] = f'sprite set {s}'
for rec in range(26):
    for d in stagecmp.descs(g, rec):
        if not d or 'tiles' not in d:
            continue
        for k in ('tiles', 'map'):
            t = glz.try_stream(g, d[k])
            if t:
                mark(d[k], t[1], 100)
        if to_off(d['pal']) is not None and (d['pal'] & 0xFFFF) != 0xFFFF:
            n = w16(g, d['pal'])
            if n <= 256:
                mark(d['pal'], 4 + 2 * n, 100)
for i in range(15):
    t, m, p = vscmp.entry(g, i)
    for a in (t, m):
        st = glz.try_stream(g, a)
        if st:
            mark(a, st[1], 101)
    mark(p, 128, 101)
for i in range(230):
    mark(p24(g, 0x86F0FC + 3 * i), 32, 102)
for b in range(9):
    mark(b << 16 | 0x8000, 0x8000, 103, by_off=True)

cov = pickle.load(open('/home/claude/work/out/compat/match_mk3_in_umk3_k32.pkl', 'rb'))['cov']
pickle.dump(cat, open('/home/claude/work/out/compat/attrib_mk3.pkl', 'wb'))
print(f'{"category":<16} {"bytes":>9} {"unique":>9}')
tot_u = 0
for c in sorted(set(cat.tolist())):
    m = cat == c
    u = int((m & (cov == 0)).sum())
    tot_u += u
    print(f'{labels[c]:<16} {int(m.sum()):9d} {u:9d}')
print('total unique', tot_u)
print('largest unique runs in "other":')
rr = sorted(runs((cat == -1) & (cov == 0)), key=lambda x: -x[1])
for s, L in rr[:40]:
    print(f'  {A(s)}-{A(s + L - 1)} {L}')
