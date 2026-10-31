"""Render frames referenced by per-fighter tables $85:AEBA (frame id) + $88:9DE5 (palette id)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes, sprite
from render_ninjas import render_fit
from dumptab import tab, N
from PIL import Image, ImageDraw


def sheet(items, path, cols=7, scale=2):
    W = max(t[1].width for t in items); Hh = max(t[1].height for t in items)
    img = Image.new('RGBA', (cols * W, (len(items) + cols - 1) // cols * (Hh + 12)), (30, 30, 30, 255))
    d = ImageDraw.Draw(img)
    for i, (lab, im) in enumerate(items):
        cx, cy = (i % cols) * W, (i // cols) * (Hh + 12)
        img.paste(im, (cx, cy + 12))
        d.text((cx + 1, cy), lab, fill=(255, 255, 255, 255))
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(path)


if __name__ == '__main__':
    fr = tab(0x85AEBA, 2); pl = tab(0x889DE5, 2)
    items = []
    for fid in range(26):
        if fid == 11: continue
        f = fr[fid]; p = pl[fid]
        s, n = (f >> 9) & 0x7F, f & 0x1FF
        try:
            items.append((f'{fid} {N[fid]} P{p:X}', render_fit(s, n, p & 0x1FF)))
        except Exception as e:
            print(fid, 'err', e)
    sheet(items, '/home/claude/work/out/umk3/tab_85AEBA_frames.png')
