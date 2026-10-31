# Render VS portraits for IDs 0-25 from $83:EEC6 (bank) / $83:EEFA (tiles) / $83:EF2E (map) / $83:EF62 (pal)
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, lzv
from PIL import Image, ImageDraw
r = v.load('umk3')

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

def portrait(i, shift):
    bk = v.u16(r, 0x83EEC6 + 2 * i) & 0xFF
    if bk == 0: return None
    td, ti = lzv.decompress(r, bk << 16 | v.u16(r, 0x83EEFA + 2 * i))
    md, mi = lzv.decompress(r, bk << 16 | v.u16(r, 0x83EF2E + 2 * i))
    pal = v.pal(r, bk << 16 | v.u16(r, 0x83EF62 + 2 * i), 64)
    T = [dec(td, k * 48, 6) for k in range(len(td) // 48)]
    w = [md[2 * k] | md[2 * k + 1] << 8 for k in range(len(md) // 2)]
    img = Image.new('RGB', (256, 256), (30, 30, 30)); px = img.load()
    for k, e in enumerate(w):
        idx = (e & 0x3FF) - shift
        if idx < 0 or idx >= len(T): continue
        hf = e >> 14 & 1; vf = e >> 15 & 1
        t = T[idx]
        for y in range(8):
            for x in range(8):
                c = t[7 - y if vf else y][7 - x if hf else x]
                if c: px[(k % 32) * 8 + x, (k // 32) * 8 + y] = pal[c]
    return img, ti, mi, w

if __name__ == '__main__':
    shift = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    sheet = Image.new('RGB', (9 * 140, 3 * 200), (0, 0, 0)); d = ImageDraw.Draw(sheet)
    for i in range(26):
        res = portrait(i, shift)
        cx, cy = (i % 9) * 140, (i // 9) * 200
        d.text((cx + 2, cy + 2), 'id%d' % i, fill=(255, 255, 0))
        if res is None: continue
        img, ti, mi, w = res
        nz = [k for k, e in enumerate(w) if e & 0x3FF]
        cols = sorted(set(k % 32 for k in nz)); rows = sorted(set(k // 32 for k in nz))
        if i in (0, 24, 25): print(i, 'map cols', cols[0], cols[-1], 'rows', rows[0], rows[-1], 'attrs', sorted(set(e >> 10 for e in w)))
        crop = img.crop((0, 0, 136, 184))
        sheet.paste(crop, (cx + 2, cy + 14))
    sheet.save('/home/claude/work/out/verify-umk3/vs_portraits_shift%d.png' % shift)
