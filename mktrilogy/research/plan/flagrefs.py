"""Critic check: traced UMK3 instructions that reference the kode flag variables found by
kodemsgs.py (HYPER KOMBAT $3BF4, SHADOW FIGHTING $3C24, 2X DAMAGE $3BDC, UNLIMITED RUN $3C00,
ONE BUTTON FATALITIES $3BE4) plus the boss unlock flags $3BAE/$3BB0. Uses out/umk3/trace.pkl.
Output: out/plan/flagrefs.txt (each line = traced pc + instruction text).
"""
import pickle, re
T = pickle.load(open('/home/claude/work/out/umk3/trace.pkl', 'rb'))
ins = T['insns']
FL = {'3BF4': 'HYPER KOMBAT', '3C24': 'SHADOW FIGHTING', '3BDC': '2X DAMAGE', '3C00': 'UNLIMITED RUN',
      '3BE4': 'ONE BUTTON FATALITIES', '3BAE': 'Kahn unlock', '3BB0': 'Motaro unlock'}
out = []
for v, name in FL.items():
    hits = [(pc, ins[pc][3]) for pc in sorted(ins) if re.search(r'\$(7E)?' + v + r'\b', ins[pc][3].upper())]
    out.append(f'## ${v} {name}: {len(hits)} traced refs')
    for pc, t in hits:
        out.append(f'   ${pc>>16:02X}:{pc&0xFFFF:04X}  {t}')
open('/home/claude/work/out/plan/flagrefs.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
