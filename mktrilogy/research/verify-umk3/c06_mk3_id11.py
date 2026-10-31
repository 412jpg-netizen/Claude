# Cross-check: what is fighter ID 11 in SNES MK3? Uses MK3's own tables found by code-pattern search:
# set tables $85:ABAA/$85:ABDE (MK3 $86:E9AC: LDA $85ABAA,X / LDA $85ABDE,X), anim table $86:DC9B (MK3 $86:DC13),
# primary palette IDs $86:F3AE (MK3 $86:DE70), palette table $86:F0FC (MK3 $83:F7E9).
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v, spr
from PIL import Image, ImageDraw
r = v.load('mk3')
spr.r = r  # reuse decoder with MK3 rom
def set_header(s):
    bk = v.u16(r, 0x85ABAA + 2 * s) & 0xFF; ad = v.u16(r, 0x85ABDE + 2 * s)
    a = bk << 16 | ad; h = v.bytes_at(r, a, 16)
    return dict(addr=a, banktab=(h[7] << 16) | h[0] | h[1] << 8, dir=(h[4] << 16) | h[2] | h[3] << 8,
                frametab=(h[7] << 16) | h[5] | h[6] << 8, delta=(h[11] << 16) | h[12] | h[13] << 8)
spr.set_header = set_header
def palette(pid):
    return v.pal(r, v.u24(r, 0x86F0FC + 3 * pid), 16)
spr.palette = palette
def first_frame(fid, table):
    t = v.u24(r, table + 4 * fid); bank = t & 0xFF0000
    p = bank | v.u16(r, t)
    for _ in range(100):
        w = v.u16(r, p); p += 2
        if w < 0xFFEA and w: return w
        if w == 0xFFFF: p = bank | v.u16(r, p)
        elif w == 0xFFF8:
            b = v.u8(r, p); tgt = v.u16(r, p + 1); p += 3
            if b == fid: p = bank | tgt
        else: return None
sheet = Image.new('RGB', (9 * 110, 2 * 240), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for fid in range(18):
    fr = first_frame(fid, 0x86DC53)
    pid = v.u8(r, 0x86F3AE + fid)
    print(fid, 'frame', fr and '%04X' % fr, 'pal', pid)
    try:
        im = spr.render(fr, pid, scale=2)
    except Exception as e:
        print('  render fail', e); continue
    if im.height > 210: im = im.resize((im.width * 210 // im.height, 210))
    cx, cy = (fid % 9) * 110, (fid // 9) * 240
    sheet.paste(im, (cx + 4, cy + 20)); d.text((cx + 4, cy + 4), 'mk3 id%d' % fid, fill=(255, 255, 0))
sheet.save('/home/claude/work/out/verify-umk3/mk3_roster_check.png')
