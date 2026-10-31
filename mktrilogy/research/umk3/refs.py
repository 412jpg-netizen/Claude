"""List traced instructions whose operand equals a given 16-bit address, with following context.
usage: python3 -I refs.py 52C8 [ctx]"""
import sys, pickle
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, d65, snes
T = pickle.load(open('/home/claude/work/out/umk3/trace.pkl', 'rb'))
ins = T['insns']
pcs = sorted(ins)
idx = {p: i for i, p in enumerate(pcs)}
a = int(sys.argv[1], 16)
ctx = int(sys.argv[2]) if len(sys.argv) > 2 else 6
for p in pcs:
    sz, m, x, txt, op, val = ins[p]
    if val is not None and d65.OPS[op][1] in ('abs', 'absx', 'absy', 'long', 'longx') and (val & 0xFFFF) == a:
        i = idx[p]
        print('----')
        for q in pcs[max(0, i - 2): i + ctx]:
            print(f'{q:06X} {ins[q][3]}')
