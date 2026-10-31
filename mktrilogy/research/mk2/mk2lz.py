"""Python port of the MK2 general decompressor at $85:B9FC (static translation of the 65816 code).
Stream: u16 size, u8 type, then commands. Output is produced BACKWARDS from the end.
type != 2 ("plain"), command byte c:
  1LLLLooo oooooooo : copy L+3 bytes from distance ((c&7)<<8|o)+1 (16-bit word copies, high->low)
  01nnnnnn          : n+1 literal bytes follow (stored in ascending address order)
  001kkkkk          : copy 1 byte from distance k+1
  000kkkkk bb       : k==0 -> end; else fill k+2 bytes with bb
type == 2 ("split"): same decoding into a virtual buffer V (low bytes then high bytes), byte copies,
  and 001kkkkk bb becomes a descending run bb, bb-1, ... of k+3 bytes (ascending in memory).
  Result interleaves: out[2i] = V[i], out[2i+1] = V[ceil(size/2)+i].
"""
import sys; sys.path.insert(0,'/home/claude/work/lib')
import snes
ROM = snes.load('mk2')

def decompress(addr, rom=ROM):
    o = snes.to_off(addr, len(rom))
    size = rom[o] | rom[o+1] << 8; typ = rom[o+2]
    p = o + 3
    V = bytearray(size); y = size
    split = (typ == 2)
    while True:
        c = rom[p]
        if c & 0x80:
            off = ((c & 7) << 8 | rom[p+1]); L = (c >> 3) & 15; n = L + 3; p += 2
            y -= n; x = y + off + 1
            if split:
                for i in range(n-1, -1, -1): V[y+i] = V[x+i] if x+i < size else 0
            else:
                offs = list(range(n-2, -1, -2))
                if offs[-1] != 0: offs.append(0)
                for k in offs:
                    w0 = V[x+k] if x+k < size else 0; w1 = V[x+k+1] if x+k+1 < size else 0
                    V[y+k] = w0
                    if y+k+1 < size: V[y+k+1] = w1
        elif c & 0x40:
            n = (c & 0x3F) + 1
            y -= n; V[y:y+n] = rom[p+1:p+1+n]; p += 1 + n
        elif c & 0x20:
            if split:
                n = (c & 0x1F) + 3; b = rom[p+1]; p += 2
                for i in range(n): y -= 1; V[y] = (b - i) & 0xFF
            else:
                k = c & 0x1F; p += 1
                y -= 1; V[y] = V[y + k + 1]
        else:
            k = c & 0x1F
            if k == 0: p += 1; break
            n = k + 2; b = rom[p+1]; p += 2
            y -= n; V[y:y+n] = bytes([b]) * n
        if y < 0: raise ValueError('underflow at %06X' % p)
    if split:
        h = (size + 1) // 2
        out = bytearray(size)
        out[0::2] = V[:h]; out[1::2] = V[h:h + size//2]
        V = out
    return bytes(V), {'size': size, 'type': typ, 'packed': p - o, 'end_y': y}
