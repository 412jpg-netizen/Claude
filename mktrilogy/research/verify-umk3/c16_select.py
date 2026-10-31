# Render select screen record 13 layer 0 (8bpp) with CGRAM built from both layers' palette blocks
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, lzv
from PIL import Image
from collections import Counter
r = v.load('umk3')
tiles, ti = lzv.decompress(r, 0xC30000)
mp, mi = lzv.decompress(r, 0xF9FACF)
print('tiles', ti, 'map', mi, 'ntiles', len(tiles) / 64)

def dec(t, off, bpp):
    rows = []
    for y in range(8):
        row = []
        for x in range(8):
            c = 0
            for p in range(bpp):
                c |= ((t[off + (p // 2) * 16 + y * 2 + (p & 1)] >> (7 - x)) & 1) << p
            row.append(c)
        rows.append(row)
    return rows
cnt = Counter()
T = [dec(tiles, i * 64, 8) for i in range(len(tiles) // 64)]
for t in T:
    for row in t: cnt.update(row)
vals = sorted(cnt)
print('pixel values used: min %d max %d distinct %d' % (vals[0], vals[-1], len(vals)))
print('values <48 used:', [x for x in vals if x < 48][:20], ' values >=144:', [x for x in vals if x >= 144][:10])
# CGRAM
cg = [(0, 0, 0)] * 256
for blk in (0xFF7B5E, 0xFF7BC2):
    n = v.u16(r, blk); first = v.u16(r, blk + 2)
    for i in range(n):
        cg[first + i] = v.bgr(v.u16(r, blk + 4 + 2 * i))
w = [mp[2 * i] | mp[2 * i + 1] << 8 for i in range(len(mp) // 2)]
rows = (len(w) + 31) // 32
img = Image.new('RGB', (256, rows * 8))
px = img.load()
for i, e in enumerate(w):
    t = T[e & 0x3FF]
    hf, vf = e >> 14 & 1, e >> 15 & 1
    cx, cy = (i % 32) * 8, (i // 32) * 8
    for y in range(8):
        for x in range(8):
            c = t[7 - y if vf else y][7 - x if hf else x]
            px[cx + x, cy + y] = cg[c]
img = img.resize((512, rows * 16), Image.NEAREST)
img.save('/home/claude/work/out/verify-umk3/select_L0_cgram.png')
# variant B: pixel value v -> layer-0 block colour v (i.e. CGRAM[48+v])
img2 = Image.new('RGB', (256, rows * 8)); px2 = img2.load()
blk = 0xFF7BC2
own = [v.bgr(v.u16(r, blk + 4 + 2 * i)) for i in range(96)]
for i, e in enumerate(w):
    t = T[e & 0x3FF]
    cx, cy = (i % 32) * 8, (i // 32) * 8
    for y in range(8):
        for x in range(8):
            px2[cx + x, cy + y] = own[t[y][x]]
img2.resize((512, rows * 16), Image.NEAREST).save('/home/claude/work/out/verify-umk3/select_L0_blockpal.png')
