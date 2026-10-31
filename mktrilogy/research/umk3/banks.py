"""Per-bank code-likeness: count JSL $8x-$BF/$C0+ patterns, REP/SEP #$20/#$30, RTL/RTS density."""
import sys, re, math
sys.path.insert(0, '/home/claude/work/lib'); import snes
from collections import Counter
r = snes.load(sys.argv[1] if len(sys.argv) > 1 else 'umk3')
for b in range(len(r) // 0x10000):
    d = r[b << 16:(b + 1) << 16]
    jsl = len(re.findall(rb'\x22..[\x80-\x8f\xc0-\xcf]', d, re.S))
    rep = d.count(b'\xc2\x20') + d.count(b'\xc2\x30') + d.count(b'\xe2\x20') + d.count(b'\xe2\x30')
    c = Counter(d); n = len(d)
    ent = -sum(v / n * math.log2(v / n) for v in c.values())
    ff = c[0xFF]; zz = c[0]
    print(f'bank {b:02X} jsl={jsl:5d} repsep={rep:5d} ent={ent:.2f} ff={ff:5d} 00={zz:5d}')
