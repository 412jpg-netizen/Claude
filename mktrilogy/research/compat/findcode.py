"""Find the counterpart of a routine in another ROM by wildcard byte matching.
The source routine is disassembled linearly (n instructions); opcode bytes stay fixed, operand
bytes of abs/long/immediate/branch modes become wildcards (dp/sr operands too if loose=True).
Each hit is then disassembled with the same M/X widths and the operands of the two versions are
paired, which gives the address translation (e.g. UMK3 table $86:EAEC <-> MK3 table $xx:xxxx).

usage: python3 -I findcode.py srcgame addr n tgtgame [loose]
"""
import sys, re
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, lst, to_off

WILD = {'abs', 'absx', 'absy', 'absi', 'absxi', 'absil', 'long', 'longx', 'immm', 'immx', 'rel', 'rell'}
LOOSE = WILD | {'dp', 'dpx', 'dpy', 'dpi', 'dpxi', 'dpiy', 'dpil', 'dpily', 'sr', 'sriy', 'imm8'}


def pattern(game, addr, n, m16=True, x16=True, loose=False, stop=False):
    L = lst(game, addr, n, m16, x16, stop=stop)
    wild = LOOSE if loose else WILD
    pat = b''
    for d in L:
        pat += re.escape(bytes([d['op']]))
        k = d['size'] - 1
        if k:
            if d['mode'] in wild and d['op'] not in (0xC2, 0xE2):
                pat += b'.' * k
            else:
                pat += re.escape(bytes(d['bytes'][1:]))
    return L, pat


def find(srcgame, addr, n, tgtgame, m16=True, x16=True, loose=False, region=None, stop=False):
    L, pat = pattern(srcgame, addr, n, m16, x16, loose, stop)
    r = ROM[tgtgame]
    lo, hi = region if region else (0, len(r))
    hits = []
    for m in re.finditer(pat, r[lo:hi], re.S):
        o = lo + m.start()
        a = 0x800000 | o if (o & 0xFFFF) >= 0x8000 else 0xC00000 | o
        hits.append(a)
        if len(hits) > 20:
            break
    return L, hits


def pair(srcgame, addr, n, tgtgame, taddr, m16=True, x16=True):
    A = lst(srcgame, addr, n, m16, x16, stop=False)
    B = lst(tgtgame, taddr, n, m16, x16, stop=False)
    out = []
    for a, b in zip(A, B):
        if a['bytes'] != b['bytes']:
            out.append((a['pc'], a['text'], b['pc'], b['text']))
    return out


if __name__ == '__main__':
    sg, a, n, tg = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]), sys.argv[4]
    loose = len(sys.argv) > 5
    L, hits = find(sg, a, n, tg, loose=loose)
    print('hits', ['$%06X' % h for h in hits])
    for h in hits[:3]:
        print('--- pairing with $%06X' % h)
        for pa, ta, pb, tb in pair(sg, a, n, tg, h):
            print(f'  {pa:06X} {ta:<20} | {pb:06X} {tb}')
