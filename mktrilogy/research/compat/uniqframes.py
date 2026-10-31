"""For a set of game A, list frames that use decoded tiles absent from every sprite set of game B, and
render them to out/compat/uniq_<A>_set<N>.png.  usage: python3 -I uniqframes.py A B set [palid]"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import spr, foot
ga, gb, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
pid = int(sys.argv[4], 16) if len(sys.argv) > 4 else None
HB = foot.tile_hashes(gb)
S = spr.Set(ga, s)
items, fl = [], []
for f in range(1, S.nframes() + 1):
    try:
        pcs, a, e = S.pieces(f)
    except Exception:
        continue
    refs = [r for p in pcs for r in p[3]]
    if not refs:
        continue
    u = sum(1 for r in refs if S.tile(r) not in HB and any(S.tile(r)))
    if u:
        fl.append((f, u, len(refs)))
        if len(items) < 72:
            items.append((f'{f} {u}/{len(refs)}', spr.render(S, f, spr.palette(ga, pid) if pid is not None else None, scale=1)))
print(f'{ga} set {s}: {len(fl)} of {S.nframes()} frames use tiles absent from {gb}:', [f for f, _, _ in fl])
spr.sheet(items, f'/home/claude/work/out/compat/uniq_{ga}_set{s}.png', cell=(96, 96), cols=12)
