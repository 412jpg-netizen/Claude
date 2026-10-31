# usage: xr.py HEX16 [banklist]  -> raw abs/long xrefs in code banks $80-$88 (file banks 0-8), with disasm context
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
r = v.load('umk3')
t = int(sys.argv[1], 16)
banks = range(0, 9) if len(sys.argv) < 3 else [int(x, 16) for x in sys.argv[2].split(',')]
for o, op in v.abs_xrefs(r, t & 0xFFFF, set(banks)):
    a = (0x800000 | o) if (o & 0xFFFF) >= 0x8000 else (0xC00000 | o)
    n, txt, *_ = v.dis1(r, a)
    print('%06X  %s' % (a, txt))
if t > 0xFFFF:
    for o, op, tg in v.long_xrefs(r, t):
        a = (0x800000 | o) if (o & 0xFFFF) >= 0x8000 else (0xC00000 | o)
        n, txt, *_ = v.dis1(r, a)
        print('L %06X  %s' % (a, txt))
