"""Independent port of the UMK3 LZ decompressor $88:AD30 (normal mode) and $88:AE7D (mode 2),
written from my own reading of the disassembly (out/verify-umk3/dis_88AD30.txt, dis_88AEA0.txt).
decompress(rom, snes_addr) -> (bytes, info) ; info has final_y, consumed, mode, size, cmds.
The source pointer [$7A] is incremented 16-bit, so reads wrap inside the bank (faithful)."""
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v


class Src:
    def __init__(self, r, a):
        self.r, self.bank, self.lo = r, a & 0xFF0000, a & 0xFFFF
        self.start = self.lo

    def b(self, k=0):
        return v.u8(self.r, self.bank | ((self.lo + k) & 0xFFFF))

    def adv(self, n):
        self.lo = (self.lo + n) & 0xFFFF


def decompress(r, a, strict=True):
    s = Src(r, a)
    size = s.b(0) | s.b(1) << 8
    mode = s.b(2)
    s.adv(3)
    out = [None] * (size + 2)
    info = dict(size=size, mode=mode, cmds=0, bad_reads=0)

    def rd(i):
        if i < 0 or i >= size or out[i] is None:
            info['bad_reads'] += 1
            if i < 0 or i >= len(out) or out[i] is None:
                return 0
        return out[i]

    if mode != 2:
        y = size
        while True:
            c = s.b(0)
            info['cmds'] += 1
            if c & 0x80:
                nb = s.b(1)
                n = (c >> 3) & 0xF
                off = ((c & 7) << 8) | nb
                L = n + 3
                y -= L
                src = y + off + 1
                # word-wise copy, highest word first; odd L ends with overlapping word at 0
                offs = list(range(L - 2, -1, -2))
                if L % 2 == 1:
                    offs.append(0)
                for o in offs:
                    w0, w1 = rd(src + o), rd(src + o + 1)
                    out[y + o] = w0; out[y + o + 1] = w1
                s.adv(2)
            elif c & 0x40:
                n = (c & 0x3F) + 1
                for i in range(n):
                    out[y - n + i] = s.b(1 + i)
                y -= n
                s.adv(1 + n)
            elif c & 0x20:
                n = c & 0x1F
                srcp = y + n
                y -= 1
                out[y] = rd(srcp)
                s.adv(1)
            else:
                n = c & 0x1F
                if n == 0:
                    s.adv(1)
                    break
                fb = s.b(1)
                L = n + 2
                y -= L
                for i in range(L):
                    out[y + i] = fb
                s.adv(2)
    else:
        y = size + (1 if size % 2 == 0 else 0)
        first = True
        while True:
            if first and y == 1:
                y = size + (size & 1)
                first = False
            c = s.b(0)
            info['cmds'] += 1
            if c & 0x80:
                nb = s.b(1)
                n = (c >> 3) & 0xF
                off2 = ((((c & 7) << 8) | nb) << 1) | 1
                y -= 2 * (n + 3)
                src = y + off2 + 1
                if src >= size:  # $88:AF3D: CMP $8C (dst+size) -> wrap
                    src = src - size + (1 if size % 2 == 0 else 0)
                for k in range(n + 2, -1, -1):  # highest first, stride 2
                    out[y + 2 * k] = rd(src + 2 * k)
                s.adv(2)
            elif c & 0x40:
                n = (c & 0x3F) + 1
                for i in range(n):
                    out[y - 2 * n + 2 * i] = s.b(1 + i)
                y -= 2 * n
                s.adv(1 + n)
            elif c & 0x20:
                cnt = (c & 0x1F) + 3
                val = s.b(1)
                s.adv(2)
                for i in range(cnt):
                    y -= 2
                    out[y] = val
                    val = (val - 1) & 0xFF
            else:
                n = c & 0x1F
                if n == 0:
                    s.adv(1)
                    break
                fb = s.b(1)
                cnt = n + 2
                y -= 2 * cnt
                for i in range(cnt):
                    out[y + 2 * i] = fb
                s.adv(2)
    info['final_y'] = y
    info['consumed'] = (s.lo - s.start) & 0xFFFF
    info['unfilled'] = sum(1 for i in range(size) if out[i] is None)
    data = bytes((b or 0) for b in out[:size])
    return data, info


if __name__ == '__main__':
    r = v.load('umk3')
    for arg in sys.argv[1:]:
        a = int(arg, 16)
        d, info = decompress(r, a)
        print('%06X' % a, info)
