# Raw scan of code banks $80-$88 (file 0x000000-0x08FFFF, upper halves) for long-addressing opcodes whose
# operand bank would change meaning under ExHiROM: banks $00-$3F with addr >= $8000, or banks $40-$7D.
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
from collections import Counter
r = v.load('umk3')
LONG_OPS = [op for op, (mn, md) in v.OPS.items() if md in ('long', 'longx')]
hits = []; banks = Counter()
for b in range(0, 9):
    for lo in range(0x8000, 0x10000 - 3):
        o = (b << 16) | lo
        op = r[o]
        if op not in LONG_OPS: continue
        tgt = r[o + 1] | r[o + 2] << 8 | r[o + 3] << 16
        tb = tgt >> 16
        banks[tb] += 1
        risky = (tb <= 0x3F and (tgt & 0xFFFF) >= 0x8000) or (0x40 <= tb <= 0x7D)
        if risky: hits.append((0x800000 | o, v.OPS[op][0], tgt))
print('raw long-operand bank histogram (top):', [(hex(k), n) for k, n in banks.most_common(14)])
print('risky raw hits:', len(hits))
# context filter: accept a hit only if a linear disassembly started 24..2 bytes earlier lands on it
# (instruction-boundary agreement from many start points) -- crude but reduces data false positives
def aligned(a):
    votes = 0
    for back in range(2, 26):
        pc = a - back; ok = False
        for _ in range(30):
            if pc == a: ok = True; break
            if pc > a: break
            n, *_ = v.dis1(r, pc)
            pc += n
        votes += ok
    return votes
strong = [(a, m, t, aligned(a)) for a, m, t in hits]
strong = [h for h in strong if h[3] >= 18]
print('hits on which >=18/24 linear decodes agree:', len(strong))
for a, m, t, vt in strong[:60]:
    print('  %06X %s $%06X (votes %d)' % (a, m, t, vt))
