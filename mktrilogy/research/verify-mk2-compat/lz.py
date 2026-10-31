"""Hand port of the MK2 general LZ decompressor $85:B9FC (main entry, $72=0).
Written from my own trace (see notes). Output is built backwards.
Returns (bytes, info) where info has 'type', 'len', 'final_ptr' (write pointer relative
to the destination start when the end command is reached; must be 0 for a clean stream),
'src_len' (compressed bytes consumed including the 3-byte header)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/verify-mk2-compat')
import d as D

def lz(game_or_bytes, addr):
    r = D.rom(game_or_bytes) if isinstance(game_or_bytes, str) else game_or_bytes
    p = D.off(addr, len(r))
    length = r[p] | r[p+1] << 8; typ = r[p+2]; p0 = p; p += 3
    PAD = 0x900
    B = PAD
    buf = bytearray(length + 2*PAD)
    if typ != 2:
        Y = B + length
        while True:
            c = r[p]; nx = r[p+1]
            if c & 0x80:
                off = ((c & 7) << 8) | nx; n = (c >> 3) & 15
                Y -= n + 3; X = Y + off + 1; t = n + 3
                ks = list(range(t - 2, 0, -2)) + [0]
                for k in ks:             # 16-bit LDA/STA pairs, descending ($85:BCA8 / $85:BD17 chains)
                    lo, hi = buf[X+k], buf[X+k+1]
                    buf[Y+k], buf[Y+k+1] = lo, hi
                p += 2
            elif c & 0x40:
                n = (c & 0x3F) + 1
                buf[Y-n:Y] = r[p+1:p+1+n]; Y -= n; p += 1 + n
            elif c & 0x20:
                k = c & 0x1F; Y -= 1; buf[Y] = buf[Y + 1 + k]; p += 1
            else:
                n = c & 0x1F
                if n == 0: p += 1; break
                Y -= n + 2
                for i in range(n + 2): buf[Y+i] = nx
                p += 2
    else:
        end = B + length
        Y = end + (1 if length % 2 == 0 else 0)
        stopY = B + 1; wrapped = False
        while True:
            if not wrapped and Y == stopY:
                Y = B + length + (length & 1); wrapped = True
            c = r[p]; nx = r[p+1]
            if c & 0x80:
                off = ((c & 7) << 8) | nx; n = (c >> 3) & 15
                Y -= 2*(n + 3)
                A = Y + 2*off + 2
                X = A + (1 if length % 2 == 0 else 0) - length if A >= end else A
                for k in range(2*(n+2), -1, -2):
                    buf[Y+k] = buf[X+k]
                p += 2
            elif c & 0x40:
                n = (c & 0x3F) + 1
                for k in range(1, n+1):
                    buf[Y - 2*(n-k+1)] = r[p+k]
                Y -= 2*n; p += 1 + n
            elif c & 0x20:
                cnt = (c & 0x1F) + 3; b = nx
                for i in range(cnt):
                    Y -= 2; buf[Y] = b; b = (b - 1) & 0xFF
                p += 2
            else:
                n = c & 0x1F
                if n == 0: p += 1; break
                Y -= 2*(n + 2)
                for i in range(n + 2): buf[Y + 2*i] = nx
                p += 2
    return bytes(buf[B:B+length]), {'type': typ, 'len': length, 'final_ptr': Y - B, 'src_len': p - p0}
