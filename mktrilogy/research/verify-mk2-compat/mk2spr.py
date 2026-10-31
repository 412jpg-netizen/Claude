"""Independent MK2 sprite decoder written from the traced code
($85:BF66 header copy, $85:C0E0 frame ptr, $81:8000 frame walk, $81:834B tile fetch,
$81:A451 mask handlers). Works for 'mk2'; parameterised table addresses for reuse.
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/verify-mk2-compat')
import d as D

class Set:
    def __init__(self, game, s, bank_tbl=0x84CDCC, lo_tbl=0x84CDEE):
        self.r = r = D.rom(game); L = len(r); self.L = L; self.game = game; self.s = s
        bk = D.w16(r, D.off(bank_tbl, L) + 2*s); lo = D.w16(r, D.off(lo_tbl, L) + 2*s)
        self.hdr_addr = (bk << 16) | lo
        h = r[D.off(self.hdr_addr, L):][:16]; self.h = h
        self.fbank = (h[7] << 16) | h[0] | h[1] << 8          # [$5A], bank $5C = h[7]
        self.tg = D.w24(h, 2)                                 # [$4E]
        self.fp = D.w24(h, 5)                                 # [$3E], bank $40 = h[7]
        self.b8 = h[8]                                        # bank of shadow/box
        self.sh = D.w16(h, 9)                                 # $2D04
        self.pos = (h[11] << 16) | D.w16(h, 12)               # [$52] bank $54=h[11]
        self.box = D.w16(h, 14)                               # $5E
    def nframes_guess(self):
        # frame-ptr table appears to be followed by the frame-bank table
        if (self.fp >> 16) == (self.fbank >> 16) and self.fbank > self.fp:
            return ((self.fbank & 0xFFFF) - (self.fp & 0xFFFF)) // 2
        return None
    def frame_ptr(self, f):
        r = self.r; idx = (f & 0x1FF) - 1
        bank = r[D.off(self.fbank + (idx >> 6), self.L)]
        lo = D.w16(r, D.off(self.fp + idx*2, self.L))
        return (bank << 16) | lo
    def posbytes(self):
        o = D.off(self.pos, self.L); return self.r[o:o+32]
    def group(self, g):
        o = D.off(self.tg + 4*g, self.L); r = self.r
        return D.w16(r, o), r[o+2], r[o+3]
    def tile(self, word):
        """returns (32 bytes, info) following $81:834B"""
        g = (word & 0xFC) >> 2; idx = word >> 8
        lo, bank, flag = self.group(g)
        r = self.r
        if not flag & 0x80:
            a = (bank << 16) | ((lo + idx*32) & 0xFFFF)
            o = D.off(a, self.L)
            return bytes(r[o:o+32]), ('raw', g, idx, flag, a)
        s = flag & 0x3F
        a = (bank << 16) | ((lo + idx*s) & 0xFFFF)
        o = D.off(a, self.L)
        m = r[o:o+4]; p = o + 4; out = bytearray(32)
        for k in range(4):
            for b in range(8):
                if m[k] & (0x80 >> b):
                    out[k*8+b] = r[p]; p += 1
        return bytes(out), ('cmp', g, idx, flag, a, p - o)
    def frame(self, f):
        """decode frame -> list of pieces (x, y, big, flipbits, [tilewords]), byte length"""
        a = self.frame_ptr(f); o = D.off(a, self.L); r = self.r
        cnt = r[o]; nbig = r[o+1]; p = o + 2
        pb = self.posbytes(); x = pb[0]; y = pb[1]
        pieces = []
        for i in range(cnt):
            b = r[p]; p += 1
            hn, ln = b >> 4, b & 15
            if hn: x = (x + pb[1+hn]) & 0xFF
            else: x = r[p]; p += 1
            if ln: y = (y + pb[16+ln]) & 0xFF
            else: y = r[p]; p += 1
            big = i < nbig
            n = 4 if big else 1
            ws = [D.w16(r, p+2*k) for k in range(n)]; p += 2*n
            sx = x - 256 if x >= 128 else x; sy = y - 256 if y >= 128 else y
            pieces.append((sx, sy, big, ws[0] & 3, ws))
        return pieces, p - o, a

def planar(t):
    px = [[0]*8 for _ in range(8)]
    for yy in range(8):
        for xx in range(8):
            bit = 7 - xx; v = 0
            for pl in range(4):
                v |= ((t[(pl//2)*16 + yy*2 + (pl & 1)] >> bit) & 1) << pl
            px[yy][xx] = v
    return px

def render(st, f, pal=None):
    from PIL import Image
    pieces, n, a = st.frame(f)
    if not pieces: return Image.new('RGBA', (8, 8))
    minx = min(p[0] for p in pieces); miny = min(p[1] for p in pieces)
    maxx = max(p[0] + (16 if p[2] else 8) for p in pieces); maxy = max(p[1] + (16 if p[2] else 8) for p in pieces)
    img = Image.new('RGBA', (maxx-minx, maxy-miny), (0, 0, 0, 0)); px = img.load()
    if pal is None: pal = [(i*17, i*17, i*17) for i in range(16)]
    for (sx, sy, big, fl, ws) in reversed(pieces):   # draw first piece on top
        sub = []
        offs = [(0, 0), (8, 0), (0, 8), (8, 8)] if big else [(0, 0)]
        size = 16 if big else 8
        for (dx, dy), w in zip(offs, ws):
            t, _ = st.tile(w); pp = planar(t)
            for yy in range(8):
                for xx in range(8):
                    v = pp[yy][xx]
                    if not v: continue
                    X, Y = dx+xx, dy+yy
                    if fl & 1: X = size-1-X
                    if fl & 2: Y = size-1-Y
                    px[sx-minx+X, sy-miny+Y] = pal[v] + (255,)
    return img
