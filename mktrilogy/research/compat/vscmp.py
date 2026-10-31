"""VS-screen portraits: MK3 tables $80:F414 bank / $80:F432 tiles / $80:F450 map / $80:F46E palette
(15 entries, IDs 0-14; addresses from findcode.py pairing with UMK3 loader $83:E730) vs UMK3 tables
$83:EEC6 / $83:EEFA / $83:EF2E / $83:EF62 (26 entries).  For each MK3 entry: packed stream sizes,
block-match coverage of the packed bytes in UMK3, and whether the decoded tiles/map/palette equal
any UMK3 portrait.  Renders MK3 portraits to out/compat/mk3_vs_portraits.png (6bpp, 48 B/tile,
map value-1 = tile, like scripts/umk3/render_vs.py)."""
import sys, pickle, hashlib
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, w16, rd, to_off
import glz, snes
from PIL import Image, ImageDraw
T = {'mk3': (0x80F414, 0x80F432, 0x80F450, 0x80F46E, 15), 'umk3': (0x83EEC6, 0x83EEFA, 0x83EF2E, 0x83EF62, 26)}
NM = ['Kano', 'Sonya', 'Jax', 'Nightwolf', 'Sub-Zero', 'Stryker', 'Sindel', 'Sektor', 'Cyrax', 'Kung Lao', 'Kabal',
      'Sheeva', 'Shang Tsung', 'Liu Kang', 'Smoke']


def entry(g, i):
    tb, tt, tm, tp, n = T[g]
    bank = w16(g, tb + 2 * i) & 0xFF
    return bank << 16 | w16(g, tt + 2 * i), bank << 16 | w16(g, tm + 2 * i), bank << 16 | w16(g, tp + 2 * i)


def decoded(g, i):
    t, m, p = entry(g, i)
    td = glz.try_stream(g, t); md = glz.try_stream(g, m)
    return td, md, rd(g, p, 128)


def img(g, i):
    (tiles, _), (tmap, _), pal = decoded(g, i)
    pal = [snes.bgr555(pal[2 * k] | pal[2 * k + 1] << 8) for k in range(64)]
    im = Image.new('RGB', (128, 176)); px = im.load()
    for row in range(22):
        for col in range(16):
            w = tmap[2 * (row * 32 + col)] | tmap[2 * (row * 32 + col) + 1] << 8
            t = (w & 0x3FF) - 1
            if t < 0 or (t + 1) * 48 > len(tiles): continue
            rr = snes.decode_tile(tiles, t * 48, 6)
            hf, vf = (w >> 14) & 1, (w >> 15) & 1
            for y in range(8):
                for x in range(8):
                    px[col * 8 + (7 - x if hf else x), row * 8 + (7 - y if vf else y)] = pal[rr[y][x]]
    return im


if __name__ == '__main__':
    cov = pickle.load(open('/home/claude/work/out/compat/match_mk3_in_umk3_k32.pkl', 'rb'))['cov']
    H = lambda b: hashlib.sha1(b).hexdigest()
    U = {}
    for i in range(26):
        if entry('umk3', i)[0] >> 16 == 0:
            continue
        td, md, p = decoded('umk3', i)
        U.setdefault(('t', H(td[0])), i); U.setdefault(('m', H(md[0])), i); U.setdefault(('p', H(p)), i)
    ims = []
    for i in range(15):
        t, m, p = entry('mk3', i)
        td, md, pd = decoded('mk3', i)
        o = to_off(t)
        print(f'MK3 VS {i:2d} {NM[i]:<11} tiles ${t:06X} ({td[1]} B packed, raw found {int((cov[o:o + td[1]] > 0).sum())}) '
              f'map ${m:06X} pal ${p:06X} | decoded tiles = UMK3 {U.get(("t", H(td[0])))}, map = UMK3 {U.get(("m", H(md[0])))}, '
              f'pal = UMK3 {U.get(("p", H(pd)))}')
        ims.append((f'{i} {NM[i]}', img('mk3', i)))
    S = Image.new('RGB', (8 * 130, 2 * 190), (30, 30, 30)); d = ImageDraw.Draw(S)
    for k, (lab, im) in enumerate(ims):
        x, y = (k % 8) * 130, (k // 8) * 190
        S.paste(im, (x, y + 12)); d.text((x + 2, y), lab, fill=(255, 255, 0))
    S.save('/home/claude/work/out/compat/mk3_vs_portraits.png')
