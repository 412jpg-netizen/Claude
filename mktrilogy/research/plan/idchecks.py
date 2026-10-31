"""Critic check: hard-coded fighter-ID comparisons in the traced UMK3 code.
Reads the umk3 tracer output (out/umk3/trace.pkl, built by scripts/umk3/run_trace.py) and lists
every CMP #imm that follows a load of a fighter-ID variable within the next 6 traced instructions
on the straight-line path (no intervening store to A's source, no branch target analysis).
This is a heuristic (LIKELY): it finds candidates for 'ID range / special-case' checks that a new
fighter ID must be taught about. Output: out/plan/idchecks.txt
"""
import pickle, re, sys
from collections import Counter
T = pickle.load(open('/home/claude/work/out/umk3/trace.pkl', 'rb'))
ins = T['insns']
SRC = re.compile(r'LDA \$(52C8|52CA|36D0|3894)(,X|,Y)?$|LDA \$7E(52C8|36D0|3894)')
out = []
pcs = sorted(ins)
idx = {pc: i for i, pc in enumerate(pcs)}
for pc in pcs:
    size, m, x, text, op, val = ins[pc]
    if not SRC.search(text.upper()):
        continue
    # walk forward along fallthrough
    cur = pc
    for step in range(6):
        cur = (cur & 0xFF0000) | ((cur + ins[cur][0]) & 0xFFFF)
        if cur not in ins:
            break
        t = ins[cur][3].upper()
        if t.startswith('CMP #'):
            nx = (cur & 0xFF0000) | ((cur + ins[cur][0]) & 0xFFFF)
            out.append((pc, text, cur, t + '  ; next: ' + (ins[nx][3] if nx in ins else '?')))
        if t.startswith(('STA', 'LDA', 'JSL', 'JSR', 'RTS', 'RTL', 'JMP', 'JML', 'BRA', 'TAX', 'TAY', 'ASL')) and not t.startswith('CMP'):
            if not t.startswith('STA'):
                break
vals = Counter(t.split('#')[1].split()[0] for _, _, _, t in out)
with open('/home/claude/work/out/plan/idchecks.txt', 'w') as f:
    f.write('# load_pc  load_insn  ->  cmp_pc  cmp_insn   (heuristic, see docstring)\n')
    for pc, t1, cpc, t2 in out:
        f.write(f'${pc>>16:02X}:{pc&0xFFFF:04X}  {t1:<16} -> ${cpc>>16:02X}:{cpc&0xFFFF:04X}  {t2}\n')
    f.write('\n# immediate value histogram\n')
    for v, n in sorted(vals.items(), key=lambda kv: -kv[1]):
        f.write(f'{v:>8} {n}\n')
print(len(out), 'compare sites;', dict(vals.most_common(20)))
