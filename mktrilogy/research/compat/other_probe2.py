"""For MK3-unique 'other' runs that are not BRR-like: find an LZ stream that starts up to 12 KB before the
run and whose packed extent covers the run start; then look for pointers to it (24-bit, or split
bank/addr word tables: low word hits within the same bank-table neighbourhood are listed raw)."""
import sys, pickle
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, A
import glz, snes
from brrprobe import brr_score
from blockmatch import runs
cat = pickle.load(open('/home/claude/work/out/compat/attrib_mk3.pkl', 'rb'))
cov = pickle.load(open('/home/claude/work/out/compat/match_mk3_in_umk3_k32.pkl', 'rb'))['cov']
r = ROM['mk3']
rr = sorted(runs((cat == -1) & (cov == 0)), key=lambda x: -x[1])[:60]
for s, L in rr:
    f, ph = brr_score('mk3', s, L)
    if f > 0.95:
        continue
    hit = None
    for o in range(s, max(0, s - 12288), -1):
        if r[o + 2] > 2:
            continue
        sz = r[o] | r[o + 1] << 8
        if sz < 64:
            continue
        t = glz.try_stream('mk3', 0xC00000 | o)
        if t and o + t[1] > s:
            hit = (o, len(t[0]), t[1], r[o + 2])
            break
    if hit:
        a = 0xC00000 | hit[0]
        lw = (a & 0xFFFF).to_bytes(2, 'little')
        p3 = [A(p) for p, _ in snes.find_ptrs(r, a)][:3]
        print(f'{A(s)} len {L}: inside LZ @{A(hit[0])} out {hit[1]} packed {hit[2]} mode {hit[3]} '
              f'(stream unique {int((cov[hit[0]:hit[0]+hit[2]]==0).sum())}/{hit[2]}) ptr24 {p3}')
    else:
        print(f'{A(s)} len {L}: no covering LZ stream found; brr {f:.2f}')
