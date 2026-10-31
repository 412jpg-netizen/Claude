"""MK2 (SNES) fighter sprite decoder, derived from static analysis of:
  $85:BF66  per-character header load (table $84:CDCC bank words / $84:CDEE low words, 17 entries)
  $85:C0AA  frame build entry: frame = ($4C3C & $1FF) - 1; bank = [$5A][f>>6]; lo = [$3E][2f]
  $81:8000  frame -> OAM pieces (16x16 pieces first, then 8x8), delta-coded positions
  $81:834B  tile fetch: tile word lo&$FC = group*4 into [$4E] (4-byte entries), hi = tile index
            group entry byte3 bit7 clear -> raw 4bpp, 32 bytes/tile
            group entry byte3 bit7 set   -> fixed-stride records of (byte3&$3F) bytes:
                                            4 mask bytes (bit7 = first byte) + nonzero bytes
  $81:A451  256-entry jump table implementing the mask expansion (8 output bytes per mask byte)
"""
import sys; sys.path.insert(0,'/home/claude/work/lib')
import snes

ROM = snes.load('mk2')
N = len(ROM)
# Fighter IDs (order of the "X WINS" string table $83:D7B8 and of every per-fighter table below)
NAMES = ['Kung Lao','Liu Kang','Johnny Cage','Baraka','Kitana','Mileena','Shang Tsung','Raiden',
         'Sub-Zero','Reptile','Scorpion','Jax','Kintaro','Shao Kahn','Smoke','Noob Saibot','Jade']
# Sprite-set IDs (index into header table $84:CDCC/$84:CDEE; = bits 9-15 of animation frame words)
SET_NAMES = ['Kung Lao','Liu Kang','Johnny Cage','Baraka','Kitana/Mileena/Jade','Shang Tsung','Raiden',
             'male ninjas (Sub-Zero/Reptile/Scorpion/Smoke/Noob)','Jax','Kintaro','Shao Kahn',
             'shared effects A','shared effects B','shared effects C','shared effects D','silhouettes','select/UI']
# fighter ID -> sprite set (derived from table $85:C49E, which points at <set header>+$10)
FIGHTER_SET = [0,1,2,3,4,4,5,6,7,7,7,8,9,10,7,7,4]

def rd(addr, n):
    o = snes.to_off(addr, N); return ROM[o:o+n]
def b8(addr): return rd(addr,1)[0]
def w16(addr): return int.from_bytes(rd(addr,2),'little')

HDR_BANK_TBL = 0x84CDCC
HDR_LO_TBL   = 0x84CDEE

def header_addr(cid):
    return (w16(HDR_BANK_TBL + 2*cid) & 0xFF) << 16 | w16(HDR_LO_TBL + 2*cid)

def header(cid):
    a = header_addr(cid); h = rd(a, 16)
    u = lambda i: h[i] | h[i+1] << 8
    return {
        'addr': a,
        'frame_bank_tbl': h[7] << 16 | u(0),        # $5A/$5C: byte per 64 frames
        'tile_groups':    h[4] << 16 | u(2),        # $4E/$50: 4-byte group entries
        'frame_ptr_tbl':  h[7] << 16 | u(5),        # $3E/$40: 16-bit lo word per frame
        'aux_bank': h[8],                           # $2CEE -> $60 (and bank for +9 table)
        'dbg_tbl':  (h[8] << 16 | u(9)) if u(9) != 0xFFFF else None,   # $2D04, used by $81:A71A
        'pos_tbl':  h[11] << 16 | u(12),            # $52/$54: X0,Y0, 15 dX, 15 dY
        'box_tbl':  (h[8] << 16 | u(14)) if u(14) != 0xFFFF else None, # $5E: 4 bytes/frame
        'raw': h,
    }

def frame_addr(hd, frame):
    f = frame - 1
    bank = b8(hd['frame_bank_tbl'] + (f >> 6))
    lo = w16(hd['frame_ptr_tbl'] + 2*f)
    return bank << 16 | lo

def tile_bytes(hd, word):
    """Return (32 bytes of 4bpp tile, info dict) for a tile word, as $81:834B does."""
    g = (word & 0xFC)
    ent = rd(hd['tile_groups'] + g, 4)
    base = ent[0] | ent[1] << 8 | ent[2] << 16
    idx = word >> 8
    if not (ent[3] & 0x80):
        src = (base & 0xFF0000) | ((base + idx*32) & 0xFFFF)
        return bytes(rd(src, 32)), {'group': g >> 2, 'raw': True, 'src': src}
    stride = ent[3] & 0x3F
    src = (base & 0xFF0000) | ((base + idx*stride) & 0xFFFF)
    rec = rd(src, stride)
    out = bytearray(32); p = 4
    for q in range(4):
        m = rec[q]
        for bit in range(8):
            if m & (0x80 >> bit):
                out[q*8+bit] = rec[p]; p += 1
    return bytes(out), {'group': g >> 2, 'raw': False, 'src': src, 'stride': stride, 'used': p}

def decode_frame(hd, frame=None, addr=None):
    if addr is None: addr = frame_addr(hd, frame)
    pos = rd(hd['pos_tbl'], 32)
    x, y = pos[0], pos[1]
    d = rd(addr, 2); count, n16 = d[0], d[1]
    p = addr + 2
    pieces = []
    for i in range(count):
        big = i < n16
        c = b8(p); p += 1
        if c >> 4: x = (x + pos[1 + (c >> 4)]) & 0xFF
        else: x = b8(p); p += 1
        if c & 15: y = (y + pos[16 + (c & 15)]) & 0xFF
        else: y = b8(p); p += 1
        sx = x - 256 if x > 127 else x
        sy = y - 256 if y > 127 else y
        nt = 4 if big else 1
        words = [w16(p + 2*k) for k in range(nt)]; p += 2*nt
        pieces.append({'x': sx, 'y': sy, 'size': 16 if big else 8, 'words': words,
                       'hflip': bool(words[0] & 1), 'vflip': bool(words[0] & 2)})
    return {'addr': addr, 'count': count, 'n16': n16, 'pieces': pieces, 'end': p}

def tile_pixels(tb):
    return snes.decode_tile(tb, 0, 4)

def render(hd, fr, path=None, pal=None, scale=3, pad=4):
    from PIL import Image
    if pal is None:
        pal = [(255,0,255)] + [(i*16+15,)*3 for i in range(1,16)]
    xs = [pc['x'] for pc in fr['pieces']] + [pc['x']+pc['size'] for pc in fr['pieces']]
    ys = [pc['y'] for pc in fr['pieces']] + [pc['y']+pc['size'] for pc in fr['pieces']]
    if not xs: return None
    x0, y0 = min(xs)-pad, min(ys)-pad
    W, H = max(xs)-x0+pad, max(ys)-y0+pad
    img = Image.new('RGB', (W, H), pal[0]); px = img.load()
    # draw in reverse so that earlier pieces are on top (OAM priority: lower index wins)
    for pc in reversed(fr['pieces']):
        s = pc['size']
        tiles = [tile_pixels(tile_bytes(hd, w)[0]) for w in pc['words']]
        for ty in range(s):
            for tx in range(s):
                t = (ty >= 8) * 2 + (tx >= 8) if s == 16 else 0
                v = tiles[t][ty & 7][tx & 7]
                if v == 0: continue
                dx = s-1-tx if pc['hflip'] else tx
                dy = s-1-ty if pc['vflip'] else ty
                px[pc['x']-x0+dx, pc['y']-y0+dy] = pal[v]
    if scale != 1: img = img.resize((W*scale, H*scale), Image.NEAREST)
    if path: img.save(path)
    return img

def sheet(cid, frames, path, pal=None, cols=10, scale=2, cell=(150,150)):
    """Render several frames of a character into a labelled contact sheet."""
    from PIL import Image, ImageDraw
    hd = header(cid)
    rows = (len(frames)+cols-1)//cols
    S = Image.new('RGB', (cols*cell[0], rows*cell[1]), (40,40,40))
    dr = ImageDraw.Draw(S)
    for i, f in enumerate(frames):
        try:
            fr = decode_frame(hd, f)
            im = render(hd, fr, None, pal, scale=1, pad=0)
        except Exception as e:
            im = None
        cx, cy = (i % cols)*cell[0], (i//cols)*cell[1]
        if im is not None:
            im.thumbnail((cell[0]-4, cell[1]-14))
            S.paste(im, (cx+2, cy+12))
        dr.text((cx+2, cy), str(f), fill=(255,255,0))
    S.save(path)

PAL_TBL = 0x85D33D       # 24-bit pointers, 3 bytes per palette ID, 32-byte (16 colour) BGR555 palettes
PAL_ID_MAIN = 0x85D547   # byte per fighter ID (17)
PAL_ID_ALT  = 0x85D558   # byte per fighter ID, used by $85:C629 for P2 when P1 picked the same fighter

def pal_addr(pid):
    return int.from_bytes(rd(PAL_TBL + 3*pid, 3), 'little')

def palette(pid):
    d = rd(pal_addr(pid), 32)
    return [snes.bgr555(d[2*i] | d[2*i+1] << 8) for i in range(16)]

def fighter_pal_ids(cid):
    return b8(PAL_ID_MAIN + cid), b8(PAL_ID_ALT + cid)

def nframes(hd):
    """Frame count: the frame-pointer table is immediately followed by the frame-bank table
    (self-consistent for all 17 sets: bank-table length == ceil(n/64))."""
    return (hd['frame_bank_tbl'] - hd['frame_ptr_tbl']) // 2

COMMON_ANIM_TBL = 0x85C49E   # 4 bytes per fighter: lo word, bank word -> common animation pointer table
SPECIFIC_ANIM_TBL = 0x85C4E2 # 4 bytes per fighter -> fighter-specific animation pointer table
def anim_tables(fid):
    c = w16(COMMON_ANIM_TBL+4*fid) | (w16(COMMON_ANIM_TBL+4*fid+2) & 0xFF) << 16
    s = w16(SPECIFIC_ANIM_TBL+4*fid) | (w16(SPECIFIC_ANIM_TBL+4*fid+2) & 0xFF) << 16
    return c, s
