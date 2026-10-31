import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, spr
from PIL import Image, ImageDraw
r = v.load('umk3')
ids = list(range(15, 28))
sheet = Image.new('RGB', (len(ids) * 110, 2 * 250 + 20), (20, 20, 20))
d = ImageDraw.Draw(sheet)
import c03_roster
for i, fid in enumerate(ids):
    fr = c03_roster.first_frames(fid)[0]
    for row, tab in enumerate((0x889D23, 0x889D3F)):
        pid = v.u8(r, tab + fid)
        im = spr.render(fr, pid, scale=2)
        if im.height > 220: im = im.resize((im.width * 220 // im.height, 220))
        sheet.paste(im, (i * 110 + 4, row * 250 + 22))
        d.text((i * 110 + 4, row * 250 + 6), '%d p%d' % (fid, pid), fill=(255, 255, 0))
sheet.save('/home/claude/work/out/verify-umk3/ninjas_pri_alt.png')
