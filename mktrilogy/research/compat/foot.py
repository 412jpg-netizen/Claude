"""Byte footprint of a sprite set (header, tables, frame data, tile records), and how much of it is
found in another ROM by the block matcher (out/compat/match_<a>_in_<b>_k32.pkl).
Also: decoded-tile identity -- for every tile referenced by a set's frames, is a tile with the same
32 decoded bytes referenced by any set of the other game?  (catches re-encoded data)

usage: python3 -I foot.py gameA gameB
"""
import sys, pickle, hashlib
import numpy as np
sys.path.insert(0, '/home/claude/work/scripts/compat')
import spr
from c import ROM, to_off, b8, w16


def footprint(S):
    """dict category -> set of file offsets"""
    g = S.g
    size = len(ROM[g])
    F = {k: set() for k in ('tables', 'frames', 'tiles')}
    o = lambda a: to_off(a, size)

    def add(cat, a, n):
        base = o(a)
        F[cat].update(range(base, base + n))
    n = S.nframes() or 0
    add('tables', S.hdr, 16)
    add('tables', S.frametab, 2 * n)
    add('tables', S.banktab, (n + 63) // 64)
    add('tables', S.deltas, 32)
    if S.box:
        add('tables', S.box, 4 * n)
    refs = set()
    dirents = set()
    for f in range(1, n + 1):
        try:
            pcs, a, end = S.pieces(f)
        except Exception:
            continue
        if not pcs and b8(g, a) == 0:
            add('frames', a, 2)
            continue
        add('frames', a, end - a)
        for (_, _, _, rr) in pcs:
            for r in rr:
                refs.add(r & 0xFFFC)
    tiles = {}
    for r in refs:
        de = r & 0xFC
        dirents.add(de)
        base, fl = S.dir_entry(r)
        t = r >> 8
        bank = base & 0xFF0000
        if not fl & 0x80:
            sz = 16 if (fl & 0x40 and S.codec == 'umk3') else 32
            add('tiles', bank | ((base + t * sz) & 0xFFFF), sz)
        else:
            s = fl & 0x3F
            if S.codec == 'mk2':
                add('tiles', bank | ((base + t * s) & 0xFFFF), s)
            else:
                add('tiles', base, 1)
                add('tiles', bank | ((base + t * s + 1) & 0xFFFF), s)
        try:
            tiles[r] = S.tile(r)
        except Exception:
            pass
    for de in dirents:
        add('tables', S.tiledir + de, 4)
    return F, tiles


def tile_hashes(game):
    G = spr.GAMES[game]
    H = {}
    seen = set()
    for s in range(G['nsets']):
        S = spr.Set(game, s)
        if S.hdr is None or S.hdr in seen:
            continue
        seen.add(S.hdr)
        F, tiles = footprint(S)
        for r, t in tiles.items():
            H.setdefault(t, (s, r))
    return H


if __name__ == '__main__':
    ga, gb = sys.argv[1], sys.argv[2]
    M = pickle.load(open(f'/home/claude/work/out/compat/match_{ga}_in_{gb}_k32.pkl', 'rb'))
    cov = M['cov']
    HB = tile_hashes(gb)
    G = spr.GAMES[ga]
    seen = {}
    print(f'{ga} sets vs {gb}: bytes found by block match / total, per category; decoded tiles found')
    tot = np.zeros(2, int)
    for s in range(G['nsets']):
        S = spr.Set(ga, s)
        if S.hdr is None:
            continue
        if S.hdr in seen:
            print(f'set {s:2d}: same header as set {seen[S.hdr]}')
            continue
        seen[S.hdr] = s
        F, tiles = footprint(S)
        parts = []
        for k in ('tables', 'frames', 'tiles'):
            idx = np.fromiter(F[k], int)
            f = int((cov[idx] > 0).sum()) if len(idx) else 0
            parts.append(f'{k} {f}/{len(idx)}')
            tot += (f, len(idx))
        dt = sum(1 for t in tiles.values() if t in HB)
        print(f'set {s:2d} hdr ${S.hdr:06X} n={S.nframes()}: ' + ', '.join(parts) +
              f'; decoded tiles found {dt}/{len(tiles)}')
    print('total bytes found', tot[0], 'of', tot[1])
