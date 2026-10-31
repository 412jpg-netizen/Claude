"""Scan a ROM in 1 KB windows for BRR-sample signature (brrprobe.brr_score > 0.99) and report the BRR-like
byte total and, for MK3, how much of it is absent from UMK3 (block match).  usage: python3 -I brrscan.py"""
import sys, pickle
import numpy as np
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, A
from brrprobe import brr_score
from blockmatch import runs
res = {}
for g in ('mk3', 'umk3', 'mk2'):
    n = len(ROM[g])
    m = np.zeros(n, bool)
    for o in range(0, n, 1024):
        f, ph = brr_score(g, o, 1024)
        if f > 0.99:
            m[o:o + 1024] = True
    res[g] = m
    rr = runs(m)
    print(g, 'BRR-like bytes', int(m.sum()), 'regions', len(rr), [f'{A(s)}+{L:#x}' for s, L in rr[:12]])
cov = pickle.load(open('/home/claude/work/out/compat/match_mk3_in_umk3_k32.pkl', 'rb'))['cov']
m = res['mk3']
print('MK3 BRR-like bytes absent from UMK3:', int((m & (cov == 0)).sum()))
pickle.dump(res, open('/home/claude/work/out/compat/brr_masks.pkl', 'wb'))
