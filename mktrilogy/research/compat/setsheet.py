"""Contact sheet of every k-th frame of a sprite set.  usage: python3 -I setsheet.py game set [step] [palid] [out]"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import spr
g, s = sys.argv[1], int(sys.argv[2])
step = int(sys.argv[3]) if len(sys.argv) > 3 else 4
pid = int(sys.argv[4], 16) if len(sys.argv) > 4 and sys.argv[4] != '-' else None
out = sys.argv[5] if len(sys.argv) > 5 else f'/home/claude/work/out/compat/sheet_{g}_set{s}.png'
S = spr.Set(g, s)
pal = spr.palette(g, pid) if pid is not None else None
items = []
for f in range(1, S.nframes() + 1, step):
    try:
        im = spr.render(S, f, pal, scale=1)
    except Exception as e:
        im = None
    items.append((f'{f}', im))
spr.sheet(items, out, cell=(96, 96), cols=12)
print(out, len(items))
