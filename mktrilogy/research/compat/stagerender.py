"""Render a BG layer of a screen/stage record for MK3 or UMK3 (simple tilemap interpretation:
map = LZ stream of 16-bit SNES tilemap words, 32 per row; tiles = LZ stream, 4bpp unless given).
CGRAM is built from the palette blocks of all layers of the record (word count, word first index,
colours), as the UMK3 analyst's render_screen.py does.  Good enough to identify a stage visually.

usage: python3 -I stagerender.py game rec layer [bpp] [out.png]
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, to_off, w16
import glz, snes, stagecmp
from PIL import Image


def cgram(g, rec):
    cg = [(0, 0, 0)] * 256
    for d in stagecmp.descs(g, rec):
        if not d or 'pal' not in d:
            continue
        o = to_off(d['pal'])
        if o is None or to_off(d['pal'] + 2) is None or (d['pal'] & 0xFFFF) == 0xFFFF:
            continue
        n = w16(g, d['pal'])
        st = w16(g, d['pal'] + 2)
        if n > 256 or st > 255:
            continue
        for i in range(n):
            if st + i < 256:
                cg[st + i] = snes.bgr555(int.from_bytes(ROM[g][o + 4 + 2 * i:o + 6 + 2 * i], 'little'))
    return cg


def render(g, rec, layer, bpp=4, path=None, maxrows=64):
    d = stagecmp.descs(g, rec)[layer]
    t = glz.try_stream(g, d['tiles'])
    m = glz.try_stream(g, d['map'])
    if not t or not m:
        return None
    tiles, mp = t[0], m[0]
    cg = cgram(g, rec)
    words = [mp[2 * i] | mp[2 * i + 1] << 8 for i in range(len(mp) // 2)]
    rows = min((len(words) + 31) // 32, maxrows)
    tsz = 8 * bpp
    img = Image.new('RGB', (256, rows * 8))
    px = img.load()
    for i, w in enumerate(words[:rows * 32]):
        tn = w & 0x3FF
        if (tn + 1) * tsz > len(tiles):
            continue
        pal = (w >> 10) & 7
        hf, vf = (w >> 14) & 1, (w >> 15) & 1
        tr = snes.decode_tile(tiles, tn * tsz, bpp)
        for y in range(8):
            for x in range(8):
                c = tr[y][x]
                ci = c if bpp == 8 else pal * (1 << bpp) + c
                X = (i % 32) * 8 + (7 - x if hf else x)
                Y = (i // 32) * 8 + (7 - y if vf else y)
                px[X, Y] = cg[ci % 256]
    if path:
        img.save(path)
    return img


if __name__ == '__main__':
    g, rec, layer = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    bpp = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    path = sys.argv[5] if len(sys.argv) > 5 else f'/home/claude/work/out/compat/{g}_rec{rec}_L{layer}.png'
    render(g, rec, layer, bpp, path)
    print(path)
