"""Render all 174 MK2 palettes (table $85:D33D) as swatches, and list per-fighter palette IDs."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g
from PIL import Image, ImageDraw
NPAL = 0xAE   # table ends where the per-fighter ID tables begin ($85:D33D + 3*$AE = $85:D547)
TABLES = [('main',0x85D547),('alt (same-fighter P2)',0x85D558),('effect1',0x85D569),('effect2',0x85D57A),
          ('morph (12)',0x85D58B),('special',0x85D5B7)]
img = Image.new('RGB', (2*(16*10+60), (NPAL//2+1)*12), (30,30,30)); d = ImageDraw.Draw(img)
for i in range(NPAL):
    cx = (i % 2)*(16*10+60); cy = (i//2)*12
    d.text((cx+2, cy), '%02X' % i, fill=(255,255,0))
    for k, c in enumerate(g.palette(i)):
        d.rectangle([cx+24+k*10, cy+1, cx+24+k*10+9, cy+10], fill=c)
img.save('/home/claude/work/out/mk2/palettes_all.png')
if __name__ == '__main__':
    for fid in range(17):
        row = []
        for nm, t in TABLES:
            if nm.startswith('morph') and fid >= 12: row.append('--'); continue
            row.append('%02X' % g.b8(t+fid))
        print('%2d %-12s set%-2d ' % (fid, g.NAMES[fid], g.FIGHTER_SET[fid]) + ' '.join(row))
    # identical-palette check
    import collections
    byd = collections.defaultdict(list)
    for i in range(NPAL): byd[g.rd(g.pal_addr(i), 32)].append(i)
    print('duplicate palettes:', [['%02X' % x for x in v] for v in byd.values() if len(v) > 1])
