"""Compare screen/stage records of MK3 ($82:B888, 26 records, descriptors in bank $82) and UMK3
($84:8A22, 29 records, descriptors in bank $84).  Descriptor parse offsets are the same in both games
(the parsers UMK3 $84:913E/$84:920C and MK3 $82:BF17 are the same code, rcmp.py: 0 differing insns):
  type 1: palette +15 bank/+16 word, tiles +18/+19, map +1D/+1E
  type 0: palette +17/+18, tiles +1A/+1B, map +1F/+20
For every layer the tiles and map streams are decompressed (glz.py) and hashed; the palette block
(word count, word first index, colours) is hashed raw.  A layer counts as 'in UMK3' if the decoded
tiles hash equals that of some UMK3 layer.  Also renders each MK3 fight-stage layer whose tiles
are absent from UMK3 to out/compat/mk3_rec<r>_L<k>.png (4bpp, palette from the record).

usage: python3 -I stagecmp.py
"""
import sys, hashlib
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, rd, w16, b8, to_off
import glz, snes
import numpy as np, pickle

REC = {'mk3': (0x82B888, 0x82, 26), 'umk3': (0x848A22, 0x84, 29)}


def h(b):
    return hashlib.sha1(b).hexdigest()[:12]


def descs(g, rec):
    tab, bank, n = REC[g]
    r = rd(g, tab + 0x22 * rec, 0x22)
    out = []
    for k in range(4):
        L = r[8 + 2 * k] | r[9 + 2 * k] << 8
        if L in (0xFFFF, 0x8000):
            out.append(None)
            continue
        d = rd(g, (bank << 16) | L, 0x30)
        if d[0] == 1:
            pal = d[0x15] << 16 | d[0x16] | d[0x17] << 8
            til = d[0x18] << 16 | d[0x19] | d[0x1A] << 8
            mp = d[0x1D] << 16 | d[0x1E] | d[0x1F] << 8
        elif d[0] == 0:
            pal = d[0x17] << 16 | d[0x18] | d[0x19] << 8
            til = d[0x1A] << 16 | d[0x1B] | d[0x1C] << 8
            mp = d[0x1F] << 16 | d[0x20] | d[0x21] << 8
        else:
            out.append(dict(L=L, type=d[0]))
            continue
        out.append(dict(L=L, type=d[0], pal=pal, tiles=til, map=mp))
    return out


def layer_info(g, dsc):
    info = dict(dsc)
    for k in ('tiles', 'map'):
        t = glz.try_stream(g, dsc[k])
        if t is None:
            info[k + '_h'] = None
            info[k + '_n'] = None
            info[k + '_packed'] = None
        else:
            info[k + '_h'] = h(t[0])
            info[k + '_n'] = len(t[0])
            info[k + '_packed'] = t[1]
            info[k + '_data'] = t[0]
    o = to_off(dsc['pal'])
    if o is None:
        info['pal_n'] = None; info['pal_h'] = None
        return info
    n = w16(g, dsc['pal'])
    info['pal_n'] = n
    info['pal_h'] = h(ROM[g][o:o + 4 + 2 * min(n, 256)]) if n < 512 else None
    return info


def all_layers(g):
    out = {}
    for rec in range(REC[g][2]):
        for k, d in enumerate(descs(g, rec)):
            if d and 'tiles' in d:
                out[(rec, k)] = layer_info(g, d)
    return out


if __name__ == '__main__':
    M = all_layers('mk3')
    U = all_layers('umk3')
    cov = pickle.load(open('/home/claude/work/out/compat/match_mk3_in_umk3_k32.pkl', 'rb'))['cov']
    ut = {}
    for key, v in U.items():
        for kk in ('tiles_h', 'map_h', 'pal_h'):
            if v.get(kk):
                ut.setdefault((kk, v[kk]), []).append(key)
    seen = {}
    for key, v in sorted(M.items()):
        rec, k = key
        tag = []
        for kk in ('tiles_h', 'map_h', 'pal_h'):
            m = ut.get((kk, v.get(kk)))
            tag.append(f"{kk[:-2]}:{'U' + str(m[0]) if m else ('?' if v.get(kk) is None else 'NEW')}")
        # raw-byte coverage of the packed streams
        cb = []
        for kk in ('tiles', 'map'):
            if v.get(kk + '_packed'):
                o = to_off(v[kk])
                cb.append(f'{kk} raw {int((cov[o:o + v[kk + "_packed"]] > 0).sum())}/{v[kk + "_packed"]}')
        dup = seen.get(v['L'])
        seen.setdefault(v['L'], key)
        print(f"MK3 rec {rec:2d} L{k} desc $82:{v['L']:04X} t{v['type']} tiles ${v['tiles']:06X} "
              f"({v.get('tiles_n')}/{v.get('tiles_packed')}) map ${v['map']:06X} ({v.get('map_n')}) pal ${v['pal']:06X}"
              f" n={v['pal_n']} | {' '.join(tag)} | {'; '.join(cb)}" + (f' | same desc as {dup}' if dup else ''))
    pickle.dump(dict(M={k: {a: b for a, b in v.items() if not a.endswith('_data')} for k, v in M.items()},
                     U={k: {a: b for a, b in v.items() if not a.endswith('_data')} for k, v in U.items()}),
                open('/home/claude/work/out/compat/stagecmp.pkl', 'wb'))
