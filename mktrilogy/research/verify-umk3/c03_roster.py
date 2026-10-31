# Render the first anim-0 frame of every fighter ID with its primary palette ($88:9D23)
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, spr
from PIL import Image, ImageDraw
r = v.load('umk3')

def first_frames(fid, anim=0, n=1):
    t = v.u24(r, 0x8895C3 + 4 * fid)
    if t == 0: return []
    bank = t & 0xFF0000
    p = bank | v.u16(r, t + 2 * anim)
    out = []
    for _ in range(200):
        w = v.u16(r, p); p += 2
        if w == 0: break
        if w < 0xFFEA:
            out.append(w)
            if len(out) >= n: break
        elif w == 0xFFFF:
            p = bank | v.u16(r, p)
        elif w == 0xFFF8:
            b = v.u8(r, p); tgt = v.u16(r, p + 1); p += 3
            if b == fid: p = bank | tgt
        else:
            break
    return out

if __name__ == '__main__':
    imgs = []
    for fid in range(28):
        fr = first_frames(fid)
        pid = v.u8(r, 0x889D23 + fid)
        if not fr:
            imgs.append((fid, None, pid, None)); continue
        im = spr.render(fr[0], pid, scale=2)
        imgs.append((fid, fr[0], pid, im))
        print(fid, 'frame %04X set %d pal %d' % (fr[0], fr[0] >> 9, pid))
    W = 8 * 200; rows = 4
    sheet = Image.new('RGB', (W, rows * 300), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, (fid, fr, pid, im) in enumerate(imgs):
        cx, cy = (i % 7) * 228, (i // 7) * 300
        d.text((cx + 4, cy + 4), 'id%d %s p%d' % (fid, ('%04X' % fr) if fr else '-', pid), fill=(255, 255, 0))
        if im:
            if im.height > 270: im = im.resize((im.width * 270 // im.height, 270))
            sheet.paste(im, (cx + 4, cy + 20))
    sheet.save('/home/claude/work/out/verify-umk3/roster_mine.png')
