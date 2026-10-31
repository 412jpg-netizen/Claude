"""Grey-scale 4bpp tile sheet of a stage layer's decompressed tiles (first N tiles), for visual
comparison of MK3 and UMK3 stage art.  usage: python3 -I tilesheet.py game rec layer [n] [out]"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import stagecmp, glz, snes
g, rec, layer = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
n = int(sys.argv[4]) if len(sys.argv) > 4 else 512
out = sys.argv[5] if len(sys.argv) > 5 else f'/home/claude/work/out/compat/tiles_{g}_rec{rec}_L{layer}.png'
d = stagecmp.descs(g, rec)[layer]
t = glz.try_stream(g, d['tiles'])[0]
snes.tiles_png(t, 0, min(n, len(t) // 32), out, bpp=4, cols=32, scale=2)
print(out, len(t) // 32, 'tiles')
