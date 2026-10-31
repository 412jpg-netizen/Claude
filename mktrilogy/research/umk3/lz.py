"""Python port of the UMK3 general decompressor at $88:AD30 (normal mode; mode 2 in decompress2()).
Static re-implementation; see notes 'Compression format'.

Stream at src:  word  out_size
                byte  mode  (2 = stride-2 variant handled by $88:AE7D; see decompress2() below)
                then commands, output is produced BACKWARDS from dst+out_size down to dst:
  c >= $80        2 bytes: len = ((c>>3)&$0F)+3, off = ((c&7)<<8)|next ; Y -= len;
                   copy len bytes from Y+off+1 (word-wise, highest word first)
  $40 <= c < $80  literal: n = (c&$3F)+1 bytes follow, placed at [Y-n, Y) in stream order; consumes n+1
  $20 <= c < $40  1 byte: Y -= 1; out[Y] = out[Y + (c&$1F) + 1]
  $01 <= c < $20  2 bytes: fill len = c+2 with byte 'next'
  c == $00        end
Mode 2 ($88:AE7D, used for 16-bit tilemaps/word arrays): same command bytes but every write steps by 2.
  The odd bytes (high bytes of words) are produced first, top-down, then the even (low) bytes.
  Back-refs that point past the end of the buffer wrap into the odd plane (src - size + 1).
  $20 <= c < $40 differs: 2 bytes, count = (c&$1F)+3, writes next, next-1, next-2 ... downwards
  (an incrementing sequence in memory order).  Fill (c<$20) writes c+2 bytes.
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes

rom = snes.load('umk3')


def rd(addr, n):
    o = u.to_off(addr)
    return rom[o:o + n]


def decompress(src, maxcmds=1 << 20, trace=False):
    o = u.to_off(src)
    size = snes.u16(rom, o)
    mode = rom[o + 2]
    if mode == 2:
        return decompress2(o, size, maxcmds)
    p = o + 3
    out = bytearray(size + 64)   # slack: word writes can touch 1 byte past
    Y = size
    for _ in range(maxcmds):
        c = rom[p]
        if c & 0x80:
            b1 = rom[p + 1]
            ln = ((c >> 3) & 0xF) + 3
            off = ((c & 7) << 8) | b1
            Y -= ln
            X = Y + off + 1
            ofs = list(range(ln - 2, -1, -2)) + ([0] if ln & 1 else [])
            for k in ofs:
                out[Y + k] = out[X + k]; out[Y + k + 1] = out[X + k + 1]
            p += 2
        elif c & 0x40:
            n = (c & 0x3F) + 1
            Y -= n
            out[Y:Y + n] = rom[p + 1:p + 1 + n]
            p += n + 1
        elif c & 0x20:
            d = c & 0x1F
            Y -= 1
            out[Y] = out[Y + d + 1]
            p += 1
        elif c:
            ln = c + 2
            Y -= ln
            out[Y:Y + ln] = bytes([rom[p + 1]]) * ln
            p += 2
        else:
            p += 1
            break
        if Y < 0:
            raise ValueError(f'underflow at stream {p:06X}')
    return bytes(out[:size]), Y, size, p - o


def decompress2(o, size, maxcmds=1 << 20):
    """Mode-2 (stride-2) stream, physical-address emulation of $88:AE7D..$88:AFDB with dst = 0."""
    out = bytearray(size + 64)
    p = o + 3
    Y = size + (0 if size & 1 else 1)   # $88:AE83: dst + size + (size even)
    end = size                          # $8C
    switch = 1                          # $8A = dst + 1
    for _ in range(maxcmds):
        if switch is not None and Y == switch:
            Y = size + (size & 1)
            switch = None
        c = rom[p]
        if c & 0x80:
            b1 = rom[p + 1]
            n = (c >> 3) & 0xF
            off = ((c & 7) << 8) | b1
            Y -= 2 * (n + 3)
            X = Y + 2 * off + 2
            if X >= end:
                X = X + (0 if size & 1 else 1) - size
            for k in range(n + 2, -1, -1):
                out[Y + 2 * k] = out[X + 2 * k]
            p += 2
        elif c & 0x40:
            n = (c & 0x3F) + 1
            for i in range(n, 0, -1):
                Y -= 2
                out[Y] = rom[p + i]
            p += n + 1
        elif c & 0x20:
            cnt = (c & 0x1F) + 3
            v = rom[p + 1]
            for k in range(cnt):
                Y -= 2
                out[Y] = v & 0xFF
                v -= 1
            p += 2
        elif c:
            n = c & 0x1F
            v = rom[p + 1]
            for k in range(n + 2):
                Y -= 2
                out[Y] = v
            p += 2
        else:
            p += 1
            break
        if Y < 0:
            raise ValueError(f'underflow at stream {p:06X}')
    return bytes(out[:size]), (Y if Y >= 0 else Y), size, p - o


if __name__ == '__main__':
    a = int(sys.argv[1], 16)
    data, Y, size, used = decompress(a)
    print(f'src ${a:06X} size={size:#x} final Y={Y} (0 = exact) stream bytes={used:#x}')

