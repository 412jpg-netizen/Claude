"""Probe the largest MK3-unique 'other' runs (attrib.py): for each run, find LZ streams that start in or
just before the run (glz.try_stream on every offset in [start-64, start+64)), BRR-like signature, and 24-bit
pointers to the stream start anywhere in MK3.  usage: python3 -I other_probe.py [nruns]"""
import sys, pickle
import numpy as np
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, A
import glz, snes
from blockmatch import runs
cat = pickle.load(open('/home/claude/work/out/compat/attrib_mk3.pkl', 'rb'))
cov = pickle.load(open('/home/claude/work/out/compat/match_mk3_in_umk3_k32.pkl', 'rb'))['cov']
r = ROM['mk3']
n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
rr = sorted(runs((cat == -1) & (cov == 0)), key=lambda x: -x[1])[:n]
for s, L in rr:
    found = None
    for o in range(max(0, s - 96), s + 96):
        t = glz.try_stream('mk3', 0xC00000 | o)
        if t and t[1] > 256:
            found = (o, len(t[0]), t[1], r[o + 2])
            break
    ptrs = []
    if found:
        a = 0xC00000 | found[0]
        ptrs = snes.find_ptrs(r, a)
        # also bank-word + addr-word split tables are common: search the low word only
        lw = sum(1 for _ in [0])
    print(f'{A(s)} len {L}: LZ {"@" + A(found[0]) + f" out {found[1]} packed {found[2]} mode {found[3]}" if found else "-"}'
          f' ptrs {[A(p) for p, _ in ptrs][:4]}')
