"""Render VS-screen portraits ($83:E730 loader). Per fighter ID 0-25:
  bank  = $83:EEC6[id] (word, low byte)   tiles   = LZ($83:EEFA[id])  6bpp, 48 bytes/tile ($83:E97E pads to 8bpp)
  tilemap = LZ($83:EF2E[id]) 32x32 words, portrait in the left 16x22   palette = 64 colours at $83:EF62[id]
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes, lz
from dumptab import tab, N
from PIL import Image, ImageDraw


def portrait(fid):
    b = tab(0x83EEC6, 2, 26)[fid] & 0xFF
    tiles, *_ = lz.decompress((b << 16) | tab(0x83EEFA, 2, 26)[fid])
    tmap, *_ = lz.decompress((b << 16) | tab(0x83EF2E, 2, 26)[fid])
    po = u.to_off((b << 16) | tab(0x83EF62, 2, 26)[fid])
    pal = [snes.bgr555(snes.u16(lz.rom, po + 2 * i)) for i in range(64)]
    img = Image.new('RGB', (16 * 8, 22 * 8), (0, 0, 0))
    px = img.load()
    for row in range(22):
        for col in range(16):
            w = snes.u16(tmap, 2 * (row * 32 + col))
            t = w & 0x3FF
            if t == 0:
                continue
            t -= 1   # tile 0 = blank; uploaded tiles start at 1 (tilemap min index is 1)
            if (t + 1) * 48 > len(tiles):
                continue
            rows = snes.decode_tile(tiles, t * 48, 6)
            hf, vf = (w >> 14) & 1, (w >> 15) & 1
            for y in range(8):
                for x in range(8):
                    X = col * 8 + (7 - x if hf else x); Y = row * 8 + (7 - y if vf else y)
                    px[X, Y] = pal[rows[y][x]]
    return img


if __name__ == '__main__':
    ims = []
    for fid in range(26):
        if fid == 11:
            continue
        ims.append((f'{fid} {N[fid]}', portrait(fid)))
    cols = 9
    W, H = 128, 176 + 12
    sheet = Image.new('RGB', (cols * W, (len(ims) + cols - 1) // cols * H), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for i, (lab, im) in enumerate(ims):
        x, y = (i % cols) * W, (i // cols) * H
        sheet.paste(im, (x, y + 12)); d.text((x + 2, y), lab, fill=(255, 255, 255))
    sheet.save('/home/claude/work/out/umk3/vs_portraits.png')
