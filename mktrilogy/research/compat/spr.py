"""Generic sprite decoder for the shared Sculptured-Software MK engine (MK2, MK3, UMK3).

Formats (see notes/compat.md section 3):
  set header (16 B): +0 w bank-table lo, +2 w/+4 b tile directory, +5 w frame-ptr table lo, +7 b bank,
                     +8 b aux bank, +9 w aux table (shadow), +B b/+C w position/delta table, +E w box table
  frame: N, B(16x16 count), per piece nibble-coded position + 4 or 1 tile words
  tile word: bits0-1 flip, bits2-7 dir offset, bits8-15 tile number
  tile directory entry: w addr, b bank, b flags
     flags bit7 clear: raw 4bpp (bit6 set: raw 2bpp in UMK3/MK3)
     flags bit7 set, MK2 ('mk2' codec):   record n at addr + n*s, 4 masks + literals, fill 0
     flags bit7 set, UMK3 ('umk3' codec): byte T at addr; record n at addr+1+n*s; if n >= T the record
                                          starts with a fill byte; masks (4, or 2 if bit6) + literals
Game parameters (CONFIRMED by findcode.py pairing of $88:A471 / $85:CD8B / $88:9874 / $88:95A0):
  umk3: sets $86:EAEC/$86:EB24 (28), palettes $88:9984, prim $88:9D23, alt $88:9D3F, anim $88:95C3
  mk3:  sets $85:ABAA/$85:ABDE (26), palettes $86:F0FC, prim $86:F3AE, alt $86:F3C0, anim $86:DC53
  mk2:  sets $84:CDCC/$84:CDEE (17), palettes $85:D33D, prim $85:D547, alt $85:D558, anim $85:C49E
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, rd, b8, w16, p24
import snes

GAMES = {
    'umk3': dict(setb=0x86EAEC, seta=0x86EB24, nsets=28, pal=0x889984, prim=0x889D23, alt=0x889D3F,
                 anim=0x8895C3, nf=28, codec='umk3'),
    'mk3': dict(setb=0x85ABAA, seta=0x85ABDE, nsets=26, pal=0x86F0FC, prim=0x86F3AE, alt=0x86F3C0,
                anim=0x86DC53, nf=18, codec='umk3'),
    'mk2': dict(setb=0x84CDCC, seta=0x84CDEE, nsets=17, pal=0x85D33D, prim=0x85D547, alt=0x85D558,
                anim=0x85C49E, nf=17, codec='mk2'),
}


class Set:
    def __init__(self, game, s=None, hdr=None, codec=None):
        self.g = game
        G = GAMES[game]
        self.codec = codec or G['codec']
        if hdr is None:
            bank = w16(game, G['setb'] + 2 * s) & 0xFF
            lo = w16(game, G['seta'] + 2 * s)
            hdr = (bank << 16) | lo if (bank or lo) else None
        self.hdr = hdr
        if hdr is None:
            return
        r = rd(game, hdr, 16)
        self.raw = r
        u = lambda i: r[i] | r[i + 1] << 8
        self.banktab = r[7] << 16 | u(0)
        self.tiledir = r[4] << 16 | u(2)
        self.frametab = r[7] << 16 | u(5)
        self.auxbank = r[8]
        self.shadow = (r[8] << 16 | u(9)) if u(9) != 0xFFFF else None
        self.deltas = r[0xB] << 16 | u(0xC)
        self.box = (r[8] << 16 | u(0xE)) if u(0xE) != 0xFFFF else None

    def nframes(self):
        # frame-pointer table is followed by the bank table in all games checked
        n = (self.banktab - self.frametab) // 2
        return n if 0 < n < 512 else None

    def frame_addr(self, f):
        i = f - 1
        bank = b8(self.g, self.banktab + (i >> 6))
        return bank << 16 | w16(self.g, self.frametab + 2 * i)

    def dir_entry(self, ref):
        e = rd(self.g, self.tiledir + (ref & 0xFC), 4)
        return e[0] | e[1] << 8 | e[2] << 16, e[3]

    def tile(self, ref):
        g = self.g
        base, fl = self.dir_entry(ref)
        n = ref >> 8
        bank = base & 0xFF0000
        if not fl & 0x80:
            if fl & 0x40 and self.codec == 'umk3':
                return rd(g, bank | ((base + n * 16) & 0xFFFF), 16) + bytes(16)
            return rd(g, bank | ((base + n * 32) & 0xFFFF), 32)
        s = fl & 0x3F
        fill = 0
        if self.codec == 'mk2':
            p = bank | ((base + n * s) & 0xFFFF)
            nm = 4
        else:
            T = b8(g, base)
            p = bank | ((base + n * s + 1) & 0xFFFF)
            if n >= T:
                fill = b8(g, p); p += 1
            nm = 2 if fl & 0x40 else 4
        masks = rd(g, p, nm)
        lit = p + nm
        out = bytearray()
        for m in masks:
            for k in range(8):
                if m & (0x80 >> k):
                    out.append(b8(g, lit)); lit += 1
                else:
                    out.append(fill)
        if nm == 2:
            out += bytes(16)
        return bytes(out)

    def pieces(self, f=None, addr=None):
        g = self.g
        if addr is None:
            addr = self.frame_addr(f)
        dl = rd(g, self.deltas, 32)
        x, y = dl[0], dl[1]
        n, big = b8(g, addr), b8(g, addr + 1)
        p = addr + 2
        out = []
        for i in range(n):
            c = b8(g, p); p += 1
            if c >> 4:
                x = (x + dl[1 + (c >> 4)]) & 0xFF
            else:
                x = b8(g, p); p += 1
            if c & 15:
                y = (y + dl[16 + (c & 15)]) & 0xFF
            else:
                y = b8(g, p); p += 1
            k = 4 if i < big else 1
            refs = [w16(g, p + 2 * j) for j in range(k)]; p += 2 * k
            out.append((x - 256 if x > 127 else x, y - 256 if y > 127 else y, 16 if k == 4 else 8, refs))
        return out, addr, p


def palette(game, pid):
    G = GAMES[game]
    a = p24(game, G['pal'] + 3 * pid)
    d = rd(game, a, 32)
    return [snes.bgr555(d[2 * i] | d[2 * i + 1] << 8) for i in range(16)]


def render(S, f=None, pal=None, addr=None, tilefn=None, scale=2, pad=4):
    from PIL import Image
    pcs, a, _ = S.pieces(f, addr)
    if pal is None:
        pal = [(0, 0, 0)] + [(i * 16 + 15,) * 3 for i in range(1, 16)]
    tilefn = tilefn or S.tile
    if not pcs:
        return None
    xs = [p[0] for p in pcs] + [p[0] + p[2] for p in pcs]
    ys = [p[1] for p in pcs] + [p[1] + p[2] for p in pcs]
    x0, y0 = min(xs) - pad, min(ys) - pad
    W, H = max(xs) - x0 + pad, max(ys) - y0 + pad
    img = Image.new('RGB', (W, H), (70, 70, 100))
    px = img.load()
    for (x, y, sz, refs) in reversed(pcs):
        hf, vf = refs[0] & 1, refs[0] & 2
        tiles = [snes.decode_tile(tilefn(r), 0, 4) for r in refs]
        for ty in range(sz):
            for tx in range(sz):
                t = (ty >= 8) * 2 + (tx >= 8) if sz == 16 else 0
                v = tiles[t][ty & 7][tx & 7]
                if not v:
                    continue
                dx = sz - 1 - tx if hf else tx
                dy = sz - 1 - ty if vf else ty
                px[x - x0 + dx, y - y0 + dy] = pal[v]
    if scale != 1:
        img = img.resize((W * scale, H * scale), Image.NEAREST)
    return img


def anim_table(game, fid):
    G = GAMES[game]
    lo = w16(game, G['anim'] + 4 * fid)
    bank = w16(game, G['anim'] + 4 * fid + 2) & 0xFF
    return bank << 16 | lo if (lo or bank) else None


def first_frame(game, fid, anim=0):
    """first frame word of animation `anim` of fighter fid (follows $FFFF jumps)"""
    t = anim_table(game, fid)
    if t is None:
        return None
    s = (t & 0xFF0000) | w16(game, t + 2 * anim)
    for _ in range(64):
        v = w16(game, s)
        if v == 0xFFFF:
            s = (s & 0xFF0000) | w16(game, s + 2)
            continue
        if v == 0xFFF8:          # byte fighter-ID, word target: per-fighter branch (UMK3 $88:8804)
            if b8(game, s + 2) == fid:
                s = (s & 0xFF0000) | w16(game, s + 3)
            else:
                s += 5
            continue
        if v >= 0xFFE0 or v == 0:
            s += 2
            continue
        if (v >> 9) < GAMES[game]['nsets']:
            return v
        s += 2
    return None


def sheet(items, path, cell=(120, 150), cols=9):
    """items: list of (label, PIL image or None)"""
    from PIL import Image, ImageDraw
    rows = (len(items) + cols - 1) // cols
    S = Image.new('RGB', (cols * cell[0], rows * cell[1]), (30, 30, 30))
    dr = ImageDraw.Draw(S)
    for i, (lab, im) in enumerate(items):
        cx, cy = (i % cols) * cell[0], (i // cols) * cell[1]
        if im is not None:
            im = im.copy()
            im.thumbnail((cell[0] - 4, cell[1] - 16))
            S.paste(im, (cx + 2, cy + 14))
        dr.text((cx + 2, cy + 1), lab, fill=(255, 255, 0))
    S.save(path)
