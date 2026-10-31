# Render frames whose tiles come from the low-bank ($00-$07) directory entries, to confirm they are real data.
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, spr
from PIL import Image, ImageDraw
r = v.load('umk3')
items = [(0x0036, 1, 'Kano stance (set0)'), (0x0003, 1, 'Kano f3 (set0 dir+34 bank05)'), (0x000F, 1, 'Kano f15 (dir+6C bank04)'),
         (0x1A01, 68, 'LiuKang f1 (set13 dir+00 bank07)'), (0x1A71, 68, 'LiuKang stance')]
sheet = Image.new('RGB', (5 * 200, 300), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for i, (fid, pid, label) in enumerate(items):
    H, ps = spr.pieces(fid)
    lows = sum(1 for p in ps for rf in p[3] if v.u8(r, H['dir'] + (rf & 0xFC) + 2) < 0x80)
    im = spr.render(fid, pid, scale=2)
    if im.height > 260: im = im.resize((im.width * 260 // im.height, 260))
    sheet.paste(im, (i * 200 + 4, 30)); d.text((i * 200 + 4, 4), label, fill=(255, 255, 0)); d.text((i * 200 + 4, 16), 'low-bank tile refs: %d' % lows, fill=(0, 255, 0))
    print(label, 'low-bank refs', lows)
sheet.save('/home/claude/work/out/verify-umk3/lowbank_tiles.png')
