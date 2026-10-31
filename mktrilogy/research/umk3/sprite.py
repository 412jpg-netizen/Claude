"""UMK3 fighter/object sprite decoder (pure static re-implementation of $88:A471, $88:A5A8,
$83:8000 and $83:8362). See notes section 'Sprite graphics format'.

Frame ID (16-bit, as found in animation scripts and stored to $52F8,X):
   set = (id >> 9) & 0x7F   ($88:A471: XBA; AND #$00FE -> word index into $86:EAEC / $86:EB24)
   f   = id & 0x1FF          (1-based frame number within the set)
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes
from PIL import Image

rom = snes.load('umk3')
SET_BANKS = 0x86EAEC   # 28 words: low byte = bank of set header
SET_ADDRS = 0x86EB24   # 28 words: address of set header
PALTAB = 0x889984      # 309 x 24-bit palette pointers


def rd(addr, n):
    o = u.to_off(addr)
    return rom[o:o + n]


def b(addr):
    return rd(addr, 1)[0]


def w(addr):
    return snes.u16(rd(addr, 2), 0)


def set_header(s):
    bank = w(SET_BANKS + 2 * s) & 0xFF
    lo = w(SET_ADDRS + 2 * s)
    if bank == 0 and lo == 0:
        return None
    h = (bank << 16) | lo
    raw = rd(h, 16)
    return dict(
        hdr=h,
        banktab=(raw[7] << 16) | snes.u16(raw, 0),    # [$6A]: bank byte per 64 frames
        tiledir=(raw[4] << 16) | snes.u16(raw, 2),    # [$5E]: 4-byte tile-bank directory
        frametab=(raw[7] << 16) | snes.u16(raw, 5),   # [$4E]: word frame pointers
        deltas=(raw[0xB] << 16) | snes.u16(raw, 0xC),  # [$62]: x0,y0, 15 x-deltas, 15 y-deltas
        w8=snes.u16(raw, 8), wE=snes.u16(raw, 0xE), raw=raw)


def frame_ptr(H, f):
    idx = f - 1
    bank = b(H['banktab'] + (idx >> 6))
    lo = w(H['frametab'] + 2 * idx)
    return (bank << 16) | lo


def tile_data(H, ref):
    """$83:8362: returns 32 bytes (4bpp planar tile) for a tile reference word."""
    ent = rd(H['tiledir'] + (ref & 0xFC), 4)
    addr = snes.u16(ent, 0)
    flags = snes.u16(ent, 2)
    bank = flags & 0xFF
    tno = ref >> 8
    if not flags & 0x8000:
        if flags & 0x4000:  # raw 2bpp, planes 2-3 zero
            return rd((bank << 16) | ((addr + tno * 16) & 0xFFFF), 16) + bytes(16)
        return rd((bank << 16) | ((addr + tno * 32) & 0xFFFF), 32)
    # mask-compressed
    recsz = (flags >> 8) & 0x3F
    base = (bank << 16) | addr
    thr = b(base)
    p = (base + recsz * tno + 1)
    fill = 0
    if tno >= thr:
        fill = b(p); p += 1
    nmask = 2 if flags & 0x4000 else 4
    masks = rd(p, nmask)
    lit = p + 4 if nmask == 4 else p + 2
    out = bytearray()
    for m in masks:
        for k in range(8):
            if (m >> (7 - k)) & 1:
                out.append(b(lit)); lit += 1
            else:
                out.append(fill)
    if nmask == 2:
        out += bytes(16)
    return bytes(out)


def sx(v):
    v &= 0xFF
    return v - 256 if v & 0x80 else v


def frame_pieces(H, f):
    """$83:8000 piece parser. Returns list of (x, y, size, [tile refs])."""
    fp = frame_ptr(H, f)
    n = b(fp); big = b(fp + 1)
    p = fp + 2
    dl = H['deltas']
    x = b(dl); y = b(dl + 1)
    pieces = []
    for i in range(n):
        c = b(p); p += 1
        if c >> 4:
            x = (x + b(dl + 1 + (c >> 4))) & 0xFF
        else:
            x = b(p); p += 1
        if c & 0xF:
            y = (y + b(dl + 1 + 15 + (c & 0xF))) & 0xFF
        else:
            y = b(p); p += 1
        if i < big:
            refs = [w(p + 2 * k) for k in range(4)]; p += 8
            pieces.append((sx(x), sx(y), 16, refs))
        else:
            refs = [w(p)]; p += 2
            pieces.append((sx(x), sx(y), 8, refs))
    return fp, pieces


def palette_rgb(pid):
    pp = snes.u24(rd(PALTAB + 3 * pid, 3), 0)
    raw = rd(pp, 32)
    return [snes.bgr555(snes.u16(raw, 2 * i)) for i in range(16)]


def put_tile(img, data, ox, oy, pal, hf, vf):
    t = snes.decode_tile(data, 0, 4)
    px = img.load()
    for yy in range(8):
        for xx in range(8):
            c = t[yy][xx]
            if c == 0: continue
            X = ox + (7 - xx if hf else xx); Y = oy + (7 - yy if vf else yy)
            if 0 <= X < img.width and 0 <= Y < img.height:
                px[X, Y] = pal[c] + (255,)


def render(s, f, pid, path=None, scale=3, size=(160, 160), origin=(80, 140)):
    H = set_header(s)
    fp, pieces = frame_pieces(H, f)
    pal = palette_rgb(pid)
    img = Image.new('RGBA', size, (60, 60, 90, 255))
    ox, oy = origin
    for (x, y, sz, refs) in pieces:
        hf = refs[0] & 1; vf = (refs[0] >> 1) & 1   # bit0 -> OAM $4000 (H), bit1 -> $8000 (V)
        if sz == 8:
            put_tile(img, tile_data(H, refs[0]), ox + x, oy + y, pal, hf, vf)
        else:
            pos = [(0, 0), (8, 0), (0, 8), (8, 8)]
            for k, r in enumerate(refs):
                dx, dy = pos[k]
                if hf: dx = 8 - dx
                if vf: dy = 8 - dy
                put_tile(img, tile_data(H, r), ox + x + dx, oy + y + dy, pal, hf, vf)
    if path:
        img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(path)
    return img, fp, pieces


if __name__ == '__main__':
    s, f, pid = (int(a, 16) for a in sys.argv[1:4])
    img, fp, pieces = render(s, f, pid, sys.argv[4])
    print(f'set {s} frame {f:#x} data ${fp:06X} pieces={len(pieces)}')
