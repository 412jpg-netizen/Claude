"""Cross-validate the two independent LZ ports on each other's data:
  every MK2 stage stream (tiles, metatiles, map blocks of stages 0-9, scripts/mk2/stages.py) is decoded with
  the MK2 port (mk2lz.py) and with the UMK3 port (umk3/lz.py via glz.py, rom swapped to MK2);
  every UMK3/MK3 stage-layer stream (stagecmp.descs) is decoded with both ports as well.
Identical outputs mean the two analysts' ports implement the same format, consistent with the code
identity shown by rcmp.py (MK2 $85:B9FC == UMK3 $88:AD30 apart from DP/WRAM operands)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM
import glz, stagecmp
sys.path.insert(0, '/home/claude/work/scripts/mk2')
import mk2lz, stages
ok = bad = 0
types = {}
for s in range(10):
    R = stages.record(s)
    for a in [R['tiles'], R['meta']] + R['maps']:
        d1, info = mk2lz.decompress(a)
        d2 = glz.decompress('mk2', a)
        types[info['type']] = types.get(info['type'], 0) + 1
        if d1 == d2[0] and d2[1] == 0:
            ok += 1
        else:
            bad += 1
print('MK2 stage streams: both ports identical', ok, 'differ', bad, 'stream types', types)
for g in ('umk3', 'mk3'):
    ok = bad = 0
    types = {}
    seen = set()
    for rec in range(stagecmp.REC[g][2]):
        for d in stagecmp.descs(g, rec):
            if not d or 'tiles' not in d:
                continue
            for a in (d['tiles'], d['map']):
                if a in seen or glz.try_stream(g, a) is None:
                    continue
                seen.add(a)
                d2 = glz.decompress(g, a)
                d1, info = mk2lz.decompress(a, ROM[g])
                types[info['type']] = types.get(info['type'], 0) + 1
                if d1 == d2[0]:
                    ok += 1
                else:
                    bad += 1
    print(f'{g} stage-layer streams: both ports identical', ok, 'differ', bad, 'stream types', types)
