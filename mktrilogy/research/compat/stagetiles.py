"""Tile-level comparison of stage/screen layers: every decompressed tiles stream is cut into 32-byte
(4bpp 8x8) tiles; for each MK3 layer report the best-matching UMK3 layer by shared distinct
non-blank tiles, and the fraction of the MK3 layer's tiles found anywhere in UMK3 stage layers.
Catches stages that were recompressed or re-ordered (whole-stream hashes in stagecmp.py would miss them).

usage: python3 -I stagetiles.py
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import stagecmp, glz

NAMES_MK3 = ['THE SUBWAY', 'THE STREET', 'THE BANK', 'ROOFTOP', 'THE BALCONY', 'THE BRIDGE',
             'SOUL CHAMBER', 'SHAO KAHNS TOWER', 'THE TEMPLE', 'THE PIT 3', 'THE VORTEX']


def tileset(g, d):
    t = glz.try_stream(g, d['tiles'])
    if not t:
        return set()
    b = t[0]
    return {b[i:i + 32] for i in range(0, len(b) - 31, 32) if any(b[i:i + 32])}


def layers(g):
    out = {}
    for rec in range(stagecmp.REC[g][2]):
        for k, d in enumerate(stagecmp.descs(g, rec)):
            if d and 'tiles' in d:
                out[(rec, k)] = (d, tileset(g, d))
    return out


if __name__ == '__main__':
    M = layers('mk3')
    U = layers('umk3')
    allU = set().union(*[v[1] for v in U.values()])
    for key, (d, ts) in sorted(M.items()):
        if not ts:
            continue
        best = max(U.items(), key=lambda kv: len(ts & kv[1][1]))
        bk, (bd, bts) = best
        nm = NAMES_MK3[key[0]] if key[0] < len(NAMES_MK3) else ''
        print(f'MK3 rec {key[0]:2d} L{key[1]} {nm:<17} tiles ${d["tiles"]:06X}: {len(ts):4d} distinct tiles, '
              f'in UMK3 stage layers {len(ts & allU):4d} ({100 * len(ts & allU) // len(ts):3d}%), '
              f'best UMK3 rec {bk[0]} L{bk[1]} (${bd["tiles"]:06X}) shares {len(ts & bts)}')
