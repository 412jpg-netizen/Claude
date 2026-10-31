"""Critic check for milestone M1: context of the only traced stores to the boss-unlock flags
$3BAE (Kahn) / $3BB0 (Motaro): STZ at $80:86B1 / $80:86B4 (flagrefs.py). Also lists traced callers
of the enclosing routine, to judge whether it runs once at power-on or on every return to the title.
Output: out/plan/dis_bossflags.txt
"""
import sys, io, contextlib, pickle
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import show
T = pickle.load(open('/home/claude/work/out/umk3/trace.pkl', 'rb'))
ins = T['insns']
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    # find the start of the straight-line block containing $80:86B1 (walk back over traced insns)
    pcs = sorted(p for p in ins if 0x808600 <= p <= 0x8086C0)
    show('umk3', pcs[0] if pcs else 0x808680, 48, True, True, False)
    print('---- traced JSR/JSL/JMP operands that land in $80:8600-$80:86C0')
    for p in sorted(ins):
        t = ins[p][3].upper()
        if t.startswith(('JSR', 'JSL', 'JMP', 'JML')):
            v = ins[p][5]
            if v is None:
                continue
            tgt = v if v > 0xFFFF else (p & 0xFF0000) | v
            if 0x808600 <= tgt <= 0x8086C0:
                print(f'   ${p>>16:02X}:{p&0xFFFF:04X}  {ins[p][3]}')
open('/home/claude/work/out/plan/dis_bossflags.txt', 'w').write(buf.getvalue())
print(buf.getvalue())
