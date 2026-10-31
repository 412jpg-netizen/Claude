"""Render a BG layer of a screen/stage record from the $84:8A22 table (decompress tiles + map, load palette blocks).
Usage: render_screen.py REC LAYER BPP [out.png]
Descriptor (type 1, parsed by $84:920C): +$15 bank/+$16 addr = palette block; +$18 bank/+$19 addr = tiles (LZ);
+$1D bank/+$1E addr = tilemap (LZ, 32 words per row).  Type 0 ($84:913E): palette +$17/+$18, tiles +$1A/+$1B, map +$1F/+$20.
Palette block: word count, word first CGRAM index, then count BGR555 words ($84:961C)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes, lz
from PIL import Image
rom = lz.rom


def desc_ptrs(rec):
    o = u.to_off(0x848A22) + 0x22 * rec
    r = rom[o:o + 0x22]
    out = []
    for k in range(4):
        L = snes.u16(r, 8 + 2 * k)
        if L in (0xFFFF, 0x8000):
            out.append(None); continue
        d = rom[u.to_off(0x840000 | L):u.to_off(0x840000 | L) + 0x30]
        if d[0] == 1:
            pal = (d[0x15] << 16) | snes.u16(d, 0x16); til = (d[0x18] << 16) | snes.u16(d, 0x19); mp = (d[0x1D] << 16) | snes.u16(d, 0x1E)
        elif d[0] == 0:
            pal = (d[0x17] << 16) | snes.u16(d, 0x18); til = (d[0x1A] << 16) | snes.u16(d, 0x1B); mp = (d[0x1F] << 16) | snes.u16(d, 0x20)
        else:
            out.append(None); continue
        out.append(dict(L=L, type=d[0], pal=pal, tiles=til, map=mp))
    return out


def cgram_for(rec):
    cg = [(0, 0, 0)] * 256
    for dsc in desc_ptrs(rec):
        if not dsc: continue
        o = u.to_off(dsc['pal'])
        n = snes.u16(rom, o); st = snes.u16(rom, o + 2)
        for i in range(n):
            if st + i < 256:
                cg[st + i] = snes.bgr555(snes.u16(rom, o + 4 + 2 * i))
    return cg


def own_palette(dsc):
    o = u.to_off(dsc['pal'])
    n = snes.u16(rom, o)
    return [snes.bgr555(snes.u16(rom, o + 4 + 2 * i)) for i in range(n)] + [(0, 0, 0)] * 256


def render_layer(rec, layer, bpp, path, tilebase=0, ownpal=False):
    dsc = desc_ptrs(rec)[layer]
    tiles, *_ = lz.decompress(dsc['tiles'])
    mp, *_ = lz.decompress(dsc['map'])
    cg = own_palette(dsc) if ownpal else cgram_for(rec)
    words = [snes.u16(mp, 2 * i) for i in range(len(mp) // 2)]
    rows = (len(words) + 31) // 32
    tsz = 8 * bpp
    img = Image.new('RGB', (256, rows * 8))
    px = img.load()
    for i, w in enumerate(words):
        t = (w & 0x3FF) - tilebase
        if t < 0 or (t + 1) * tsz > len(tiles): continue
        pal = (w >> 10) & 7
        hf, vf = (w >> 14) & 1, (w >> 15) & 1
        tr = snes.decode_tile(tiles, t * tsz, bpp)
        for y in range(8):
            for x in range(8):
                c = tr[y][x]
                ci = c if bpp == 8 else (pal * (1 << bpp) + c)
                X = (i % 32) * 8 + (7 - x if hf else x); Y = (i // 32) * 8 + (7 - y if vf else y)
                px[X, Y] = cg[ci % 256]
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(path)
    return dsc, len(tiles), len(words)


if __name__ == '__main__':
    rec, layer, bpp = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    path = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != 'own' else f'/home/claude/work/out/umk3/screen{rec}_L{layer}.png'
    print(render_layer(rec, layer, bpp, path, ownpal='own' in sys.argv))
