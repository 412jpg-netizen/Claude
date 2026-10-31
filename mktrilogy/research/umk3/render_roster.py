"""Render the first frame of animation 0 (stance) of every fighter ID 0-27, using:
 anim table  $88:95C3 (4 bytes per fighter: 24-bit ptr to word table of animation scripts)
 palette     $88:9D23 (byte per fighter -> palette ID in $88:9984)
The first non-command word of anim script 0 is the frame ID (set<<9 | frame)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes, sprite
from render_ninjas import render_fit
from PIL import Image, ImageDraw
rom = sprite.rom
N = ['Kano', 'Sonya', 'Jax', 'Nightwolf', 'Sub-Zero', 'Stryker', 'Sindel', 'Sektor', 'Cyrax', 'Kung Lao', 'Kabal',
     'id11', 'Shang Tsung', 'Liu Kang', 'Smoke', 'Kitana', 'Jade', 'Mileena', 'Scorpion', 'Reptile', 'Ermac',
     'Classic SZ', 'H.Smoke', 'Noob', 'Rain', 'id25', 'id26', 'id27']


def first_frame(fid, anim=0):
    o = u.to_off(0x8895C3 + 4 * fid)
    t = snes.u24(rom, o)
    if t == 0:
        return None
    s = sprite.w(t + 2 * anim)
    a = (t & 0xFF0000) | s
    for k in range(40):
        v = sprite.w(a)
        if v == 0xFFF8:   # conditional jump: byte fighter id, word target
            a += 5; continue
        if v >= 0xFFEA:
            return ('cmd', v, a)
        return v
    return None


if __name__ == '__main__':
    pals = rom[0x89D23:0x89D23 + 28]
    tiles = []
    for fid in range(28):
        fr = first_frame(fid)
        if not isinstance(fr, int):
            print(fid, N[fid], 'no frame', fr); continue
        s, f = (fr >> 9) & 0x7F, fr & 0x1FF
        print(fid, N[fid], f'frame id {fr:04X} set {s} f {f:#x} pal {pals[fid]:02X}')
        tiles.append((f'{fid} {N[fid]}', render_fit(s, f, pals[fid])))
    W = max(t[1].width for t in tiles); Hh = max(t[1].height for t in tiles)
    cols = 7
    sheet = Image.new('RGBA', (cols * W, (len(tiles) + cols - 1) // cols * (Hh + 12)), (30, 30, 30, 255))
    d = ImageDraw.Draw(sheet)
    for i, (lab, im) in enumerate(tiles):
        cx, cy = (i % cols) * W, (i // cols) * (Hh + 12)
        sheet.paste(im, (cx, cy + 12))
        d.text((cx + 1, cy), lab, fill=(255, 255, 255, 255))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save('/home/claude/work/out/umk3/roster_stance.png')
