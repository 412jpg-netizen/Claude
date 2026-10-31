import sys, pickle; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
from collections import Counter
r = v.load('umk3')
seen, longs = pickle.load(open('/home/claude/work/out/verify-umk3/trace_v.pkl', 'rb'))
bc = Counter(); risky = []
for pc, t, val in longs:
    tb = val >> 16; bc[tb] += 1
    if (tb <= 0x3F and (val & 0xFFFF) >= 0x8000) or (0x40 <= tb <= 0x7D):
        risky.append((pc, t))
print('long operand banks:', sorted((hex(k), n) for k, n in bc.items()))
print('risky (bank $00-$3F with addr>=$8000, or $40-$7D):', len(risky))
for pc, t in risky[:40]: print('  %06X %s' % (pc, t))
# bank-$00 I/O style operands (addr < $8000) are fine; list distinct ones for the record
low = sorted(set(val for pc, t, val in longs if (val >> 16) <= 0x3F and (val & 0xFFFF) < 0x8000))
print('bank $00-$3F operands below $8000 (I/O / low WRAM):', ['$%06X' % x for x in low][:40])
# header reads: any traced operand (abs or long) in $FFB0-$FFFF?
hdr = [(pc, s[3]) for pc, s in seen.items() if s[6] in ('abs', 'absx', 'absy', 'long', 'longx') and s[5] is not None and 0xFFB0 <= (s[5] & 0xFFFF) <= 0xFFFF]
print('traced abs/long operands in $FFB0-$FFFF:', hdr[:20])
# code executing in bank $00
b0 = sorted(pc for pc in seen if pc >> 16 == 0)
print('traced bank-$00 instructions:', ['$%06X' % p for p in b0])
# immediates that look like bank bytes $40-$7D pushed as data bank / pointer bank
pb = [(pc, s[3]) for pc, s in seen.items() if s[4] in (0xA9, 0xA2, 0xA0) and s[5] is not None and 0x40 <= s[5] <= 0x7D and s[0]]
print('LDA/LDX/LDY #$0040-#$007D (possible bank bytes, mostly constants):', len(pb))
# PHK/PLB style DB loads from immediates: PEA $xxyy then PLB
pea = [(pc, s[3]) for pc, s in seen.items() if s[4] == 0xF4]
dbs = Counter((s[5] >> 8) for pc, s in seen.items() if s[4] == 0xF4 and (pc + 3) in seen and seen[pc + 3][4] == 0xAB)
print('PEA+PLB data banks:', sorted((hex(k), n) for k, n in dbs.items()))
