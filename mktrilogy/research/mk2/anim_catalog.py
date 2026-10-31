"""Contact sheet: middle frame of every common + specific animation of a fighter (labelled c<idx>/s<idx>)."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g, anims
from PIL import Image, ImageDraw
def catalog(fid, ncommon, path, cell=(96,120), cols=12):
    c, s, cp, sp = anims.fighter_anims(fid)
    bank = c >> 16
    entries = [('c%d' % i, g.w16(c+2*i)) for i in range(ncommon)]
    if s != c: entries += [('s%d' % i, v) for i, v in enumerate(sp)]
    pal = [(0,90,0)] + g.palette(g.b8(g.PAL_ID_MAIN+fid))[1:]
    rows = (len(entries)+cols-1)//cols
    S = Image.new('RGB', (cols*cell[0], rows*cell[1]), (30,30,30)); d = ImageDraw.Draw(S)
    info = []
    for i, (lab, lo) in enumerate(entries):
        cx, cy = (i % cols)*cell[0], (i//cols)*cell[1]
        if lo < 0x8000:
            d.text((cx+2, cy), lab+' -', fill=(255,0,0)); info.append((lab, lo, [])); continue
        items, fr, _ = anims.parse_script(bank, lo)
        info.append((lab, lo, fr))
        d.text((cx+2, cy), '%s n%d' % (lab, len(fr)), fill=(255,255,0))
        if not fr: continue
        w = fr[len(fr)//2]
        hd = g.header(w >> 9)
        p = pal if (w >> 9) == g.FIGHTER_SET[fid] else None
        im = g.render(hd, g.decode_frame(hd, w & 0x1FF), None, p, scale=1, pad=0)
        if im: im.thumbnail((cell[0]-4, cell[1]-14)); S.paste(im, (cx+2, cy+12))
    S.save(path)
    return info
if __name__ == '__main__':
    for fid, nc in [(3,66),(2,66),(7,66),(12,24)]:
        info = catalog(fid, nc, '/home/claude/work/out/mk2/anims_%s.png' % g.NAMES[fid].replace(' ','_').lower())
        print(g.NAMES[fid]); print('  ' + '; '.join('%s@%04X:%s' % (l, lo, ','.join('%03X' % (f & 0x1FF) for f in fr[:6]) + ('..' if len(fr) > 6 else '')) for l, lo, fr in info))
