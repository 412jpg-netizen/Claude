"""Independent sprite renderer for UMK3, written from my own reading of
$88:A471 (set header), $88:A5A8 (frame locate), $83:8000 (piece parser), $83:8362 (tile codec).
"""
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
from PIL import Image

r = v.load('umk3')


def set_header(s):
    bk = v.u16(r, 0x86EAEC + 2 * s) & 0xFF
    ad = v.u16(r, 0x86EB24 + 2 * s)
    if bk == 0 and ad == 0:
        return None
    a = bk << 16 | ad
    h = v.bytes_at(r, a, 16)
    return dict(addr=a,
                banktab=(h[7] << 16) | h[0] | h[1] << 8,
                dir=(h[4] << 16) | h[2] | h[3] << 8,
                frametab=(h[7] << 16) | h[5] | h[6] << 8,
                delta=(h[11] << 16) | h[12] | h[13] << 8)


def frame_addr(fid):
    s = fid >> 9
    H = set_header(s)
    f0 = (fid & 0x1FF) - 1
    bank = v.u8(r, H['banktab'] + (f0 >> 6))
    ad = v.u16(r, H['frametab'] + 2 * f0)
    return H, bank << 16 | ad


def sx8(b):
    b &= 0xFF
    return b - 256 if b >= 128 else b


def pieces(fid):
    H, fa = frame_addr(fid)
    N = v.u8(r, fa); B = v.u8(r, fa + 1)
    D = H['delta']
    x = v.u8(r, D); y = v.u8(r, D + 1)
    p = fa + 2
    out = []
    for i in range(N):
        c = v.u8(r, p); p += 1
        k = c >> 4
        if k:
            x = (x + v.u8(r, D + 1 + k)) & 0xFF
        else:
            x = v.u8(r, p); p += 1
        k = c & 15
        if k:
            y = (y + v.u8(r, D + 16 + k)) & 0xFF
        else:
            y = v.u8(r, p); p += 1
        big = i < B
        nref = 4 if big else 1
        refs = [v.u16(r, p + 2 * j) for j in range(nref)]
        p += 2 * nref
        out.append((sx8(x), sx8(y), big, refs))
    return H, out


def tile_bytes(H, ref):
    e = H['dir'] + (ref & 0xFC)
    ad = v.u16(r, e); bk = v.u8(r, e + 2); fl = v.u8(r, e + 3)
    t = ref >> 8
    base = bk << 16 | ad
    if not fl & 0x80:
        if fl & 0x40:
            return bytes(v.bytes_at(r, base + t * 16, 16)) + bytes(16)
        return bytes(v.bytes_at(r, base + t * 32, 32))
    rec = fl & 0x3F
    T = v.u8(r, base)
    p = base + 1 + t * rec
    fill = 0
    if t >= T:
        fill = v.u8(r, p); p += 1
    nm = 2 if fl & 0x40 else 4
    masks = [v.u8(r, p + i) for i in range(nm)]
    lp = p + nm
    out = bytearray()
    for m in masks:
        for bit in range(7, -1, -1):
            if m >> bit & 1:
                out.append(v.u8(r, lp)); lp += 1
            else:
                out.append(fill)
    if nm == 2:
        out += bytes(16)
    return bytes(out)


def decode4(tb):
    px = []
    for yy in range(8):
        row = []
        for xx in range(8):
            bit = 7 - xx
            c = 0
            for pl in range(4):
                c |= ((tb[(pl // 2) * 16 + yy * 2 + (pl & 1)] >> bit) & 1) << pl
            row.append(c)
        px.append(row)
    return px


def palette(pid):
    p = v.u24(r, 0x889984 + 3 * pid)
    return v.pal(r, p, 16)


def render(fid, pid, scale=2, bg=(40, 40, 60)):
    H, ps = pieces(fid)
    pal = palette(pid)
    canvas = {}
    for (x, y, big, refs) in ps:
        offs = [(0, 0), (8, 0), (0, 8), (8, 8)] if big else [(0, 0)]
        hf, vf = refs[0] & 1, refs[0] >> 1 & 1   # OAM flip comes from the first ref only ($83:817C)
        for (dx, dy), ref in zip(offs, refs):
            # flip of a 16x16 piece swaps sub-tile positions too
            if big:
                if hf: dx = 8 - dx
                if vf: dy = 8 - dy
            tp = decode4(tile_bytes(H, ref))
            for yy in range(8):
                for xx in range(8):
                    c = tp[yy][xx]
                    if c == 0: continue
                    sxp = 7 - xx if hf else xx
                    syp = 7 - yy if vf else yy
                    canvas[(x + dx + sxp, y + dy + syp)] = pal[c]
    if not canvas:
        return Image.new('RGB', (8, 8), bg)
    xs = [k[0] for k in canvas]; ys = [k[1] for k in canvas]
    x0, y0 = min(xs), min(ys)
    img = Image.new('RGB', (max(xs) - x0 + 1, max(ys) - y0 + 1), bg)
    for (xx, yy), c in canvas.items():
        img.putpixel((xx - x0, yy - y0), c)
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    return img
