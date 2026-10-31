"""MK2 stage data: per-stage record table $82:EDFC (34 bytes/stage, index via $82:EF50), loaded by $82:F04F.
Record: +0 bank(tiles) +1 bank(metatiles) +2 bank(map blocks) +3 bank(palette)
        +4 lo(tiles)  +6 lo(metatiles)  +8 lo(palette, 192 bytes)  +$A..+$20: 12 x lo(map block)
Tiles/metatiles/map blocks are $85:B9FC-compressed. Map block = 16x16 metatile words (512 B);
metatile = 4 BG tilemap words (TL,TR,BL,BR) -> expanded by $82:F1AB into a 32x32 tilemap.
Blocks 0-4 and 5-9 form two bands 5 screens wide (dest offsets table $82:EF64); 10-11 a 2-screen band."""
import sys; sys.path.insert(0,'/home/claude/work/lib'); sys.path.insert(0,'/home/claude/work/scripts/mk2')
import snes, mk2lz, mk2gfx as g
STAGE_NAMES = ['The Dead Pool','Kombat Tomb','Wasteland','The Tower','Living Forest','The Armory',
               'The Pit II','The Portal',"Kahn's Arena","stage 9 (unnamed; Goro's Lair?)"]
REC_TBL = 0x82EDFC; REC_IDX = 0x82EF50

def record(s):
    x = g.w16(REC_IDX + 2*s); rec = g.rd(REC_TBL + x, 0x22)
    w = lambda i: rec[i] | rec[i+1] << 8
    return {'tiles': rec[0] << 16 | w(4), 'meta': rec[1] << 16 | w(6), 'pal': rec[3] << 16 | w(8),
            'maps': [rec[2] << 16 | w(10 + 2*k) for k in range(12)]}

def render_stage(s, path):
    from PIL import Image
    R = record(s)
    tiles, ti = mk2lz.decompress(R['tiles']); meta, mi = mk2lz.decompress(R['meta'])
    pd = g.rd(R['pal'], 192)
    pal = [snes.bgr555(pd[2*i] | pd[2*i+1] << 8) for i in range(96)]
    ntiles = len(tiles)//32
    cache = {}
    def tile(t):
        if t not in cache: cache[t] = snes.decode_tile(tiles, 32*t, 4) if t < ntiles else [[0]*8]*8
        return cache[t]
    bands = [(0, 5), (5, 5), (10, 2)]
    W = 5*256; H = 3*256
    img = Image.new('RGB', (W, H), (0, 0, 0)); px = img.load()
    for bi, (first, n) in enumerate(bands):
        for k in range(n):
            m, _ = mk2lz.decompress(R['maps'][first+k])
            for my in range(16):
                for mx in range(16):
                    mw = m[2*(my*16+mx)] | m[2*(my*16+mx)+1] << 8
                    mt = mw & 0x3FF
                    for q in range(4):
                        tw = meta[8*mt+2*q] | meta[8*mt+2*q+1] << 8
                        t = tw & 0x3FF; p = (tw >> 10) & 7; hf = tw >> 14 & 1; vf = tw >> 15 & 1
                        tx = k*256 + mx*16 + (q & 1)*8; ty = bi*256 + my*16 + (q >> 1)*8
                        tl = tile(t)
                        for yy in range(8):
                            for xx in range(8):
                                v = tl[7-yy if vf else yy][7-xx if hf else xx]
                                if v: px[tx+xx, ty+yy] = pal[(p*16+v) % 96]
    img.save(path)
    return ti, mi

def sizes(s):
    R = record(s); out = {}
    for k in ('tiles', 'meta'):
        d, i = mk2lz.decompress(R[k]); out[k] = (i['packed'], i['size'], i['type'])
    seen = {}
    for a in R['maps']:
        if a not in seen: seen[a] = mk2lz.decompress(a)[1]['packed']
    out['maps'] = (sum(seen.values()), len(seen))
    out['pal'] = 192
    return out
