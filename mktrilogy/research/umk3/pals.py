"""Render the UMK3 palette table ($C8:9984, 309 x 24-bit pointers to 16-colour BGR555 palettes)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3'); import u; import snes
from PIL import Image, ImageDraw
rom = snes.load('umk3')
PTAB = 0x089984
NPAL = 309
NAMES = ['Kano', 'Sonya', 'Jax', 'Nightwolf', 'Sub-Zero', 'Stryker', 'Sindel', 'Sektor', 'Cyrax', 'Kung Lao', 'Kabal',
         'id11', 'Shang Tsung', 'Liu Kang', 'Smoke(robot)', 'Kitana', 'Jade', 'Mileena', 'Scorpion', 'Reptile', 'Ermac',
         'Classic SZ', 'Human Smoke', 'Noob Saibot', 'Rain', 'id25', 'id26', 'id27']


def pal_ptr(i):
    return snes.u24(rom, PTAB + 3 * i)


def pal(i):
    o = snes.to_off(pal_ptr(i), len(rom))
    return [snes.u16(rom, o + 2 * k) for k in range(16)]


def swatch(rows, path, sz=14):
    img = Image.new('RGB', (200 + 16 * sz, len(rows) * sz), (40, 40, 40))
    dr = ImageDraw.Draw(img)
    for y, (label, words) in enumerate(rows):
        dr.text((2, y * sz + 1), label, fill=(255, 255, 255))
        for k, w in enumerate(words):
            dr.rectangle([200 + k * sz, y * sz, 200 + k * sz + sz - 2, y * sz + sz - 2], fill=snes.bgr555(w))
    img.save(path)


if __name__ == '__main__':
    out = '/home/claude/work/out/umk3/'
    rows = [(f'{i:3d} ${i:02X} {pal_ptr(i):06X}', pal(i)) for i in range(NPAL)]
    for part in range(0, NPAL, 80):
        swatch(rows[part:part + 80], out + f'paltable_{part:03d}.png')
    p1 = rom[0x89D23:0x89D23 + 28]; p2 = rom[0x89D3F:0x89D3F + 28]
    rows = []
    for f in range(28):
        rows.append((f'{f:2d} {NAMES[f][:11]:11s} P{p1[f]:02X}', pal(p1[f])))
        rows.append((f'{"":2s} {"  alt":11s} P{p2[f]:02X}', pal(p2[f])))
    swatch(rows, out + 'fighter_palettes.png')
    print('ok')
