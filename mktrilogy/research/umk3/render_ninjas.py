"""Render the shared male-ninja stance frame (set 27, frame $7F; anim script $85:80D8 first frame $367F)
with every male-ninja palette from the per-fighter tables $88:9D23 (primary) and $88:9D3F (alternate)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes, sprite
from PIL import Image, ImageDraw


def bbox(H, f):
    fp, pcs = sprite.frame_pieces(H, f)
    xs = [x for x, y, s, r in pcs] + [x + s for x, y, s, r in pcs]
    ys = [y for x, y, s, r in pcs] + [y + s for x, y, s, r in pcs]
    return min(xs), min(ys), max(xs), max(ys)


def render_fit(s, f, pid, pad=4):
    H = sprite.set_header(s)
    x0, y0, x1, y1 = bbox(H, f)
    img, fp, pcs = sprite.render(s, f, pid, None, size=(x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), origin=(pad - x0, pad - y0))
    return img


if __name__ == '__main__':
    rom = sprite.rom
    p1 = rom[0x89D23:0x89D23 + 28]; p2 = rom[0x89D3F:0x89D3F + 28]
    names = {18: 'Scorpion', 19: 'Reptile', 20: 'Ermac', 21: 'Classic SZ', 22: 'Human Smoke', 23: 'Noob Saibot', 24: 'Rain', 25: 'id25'}
    tiles = []
    for fid in range(18, 26):
        for pid, tag in ((p1[fid], ''), (p2[fid], ' alt')):
            im = render_fit(27, 0x7F, pid)
            tiles.append((f'{fid} {names[fid]}{tag} P{pid:02X}', im))
    W = max(t[1].width for t in tiles); Hh = max(t[1].height for t in tiles)
    cols = 4
    sheet = Image.new('RGBA', (cols * W, (len(tiles) + cols - 1) // cols * (Hh + 12)), (30, 30, 30, 255))
    d = ImageDraw.Draw(sheet)
    for i, (lab, im) in enumerate(tiles):
        cx, cy = (i % cols) * W, (i // cols) * (Hh + 12)
        sheet.paste(im, (cx, cy + 12))
        d.text((cx + 1, cy), lab[:20], fill=(255, 255, 255, 255))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save('/home/claude/work/out/umk3/ninja_palettes_on_sprite.png')
    # female ninjas: set 26
    H = sprite.set_header(26)
    print('set26 hdr', hex(H['hdr']))
