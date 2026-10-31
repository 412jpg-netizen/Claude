"""Shared SNES helpers for the MK Trilogy mod analysis.
All three ROMs are unheadered HiROM FastROM. Import with:
    import sys; sys.path.insert(0, '/home/claude/work/lib'); import snes
"""
import struct
import capstone as _cs

ROMS = {
    'mk2': '/home/claude/work/roms/mk2.sfc',
    'mk3': '/home/claude/work/roms/mk3.sfc',
    'umk3': '/home/claude/work/roms/umk3.sfc',
}

def load(name):
    return open(ROMS[name], 'rb').read()

def to_off(addr, size):
    """SNES 24-bit address -> file offset (HiROM). None if not ROM."""
    bank, lo = addr >> 16, addr & 0xFFFF
    b = bank & 0x7F
    if b in (0x7E, 0x7F):
        return None  # WRAM
    if b >= 0x40:
        off = ((b - 0x40) << 16) | lo
    elif lo >= 0x8000:
        off = (b << 16) | lo
    else:
        return None  # I/O / WRAM mirror
    return off % size if off >= size else off

def to_addr(off):
    """File offset -> canonical FastROM HiROM address ($C0-$FF bank)."""
    return 0xC00000 | off

def u16(d, o): return struct.unpack_from('<H', d, o)[0]
def u24(d, o): return d[o] | d[o+1] << 8 | d[o+2] << 16

_modes = {}
def _md(m16, x16):
    k = (m16, x16)
    if k not in _modes:
        mode = {(False, False): _cs.CS_MODE_MOS65XX_65816,
                (True, False): _cs.CS_MODE_MOS65XX_65816_LONG_M,
                (False, True): _cs.CS_MODE_MOS65XX_65816_LONG_X,
                (True, True): _cs.CS_MODE_MOS65XX_65816_LONG_MX}[k]
        _modes[k] = _cs.Cs(_cs.CS_ARCH_MOS65XX, mode)
    return _modes[k]

def disasm(rom, addr, count=40, m16=True, x16=True, stop_at_rts=True):
    """Linear 65816 disassembly from SNES addr, tracking REP/SEP for M/X width.
    Returns list of (addr, bytes_hex, text). Widths are a guess after branches/joins."""
    out = []
    pc = addr
    for _ in range(count):
        off = to_off(pc, len(rom))
        if off is None:
            break
        ins = next(_md(m16, x16).disasm(rom[off:off+4], pc & 0xFFFF), None)
        if ins is None:
            out.append((pc, rom[off:off+1].hex(), '.db $%02X' % rom[off])); pc += 1; continue
        text = f'{ins.mnemonic} {ins.op_str}'.strip()
        out.append((pc, ins.bytes.hex(), text))
        op = ins.bytes[0]
        if op == 0xC2:  # REP
            if ins.bytes[1] & 0x20: m16 = True
            if ins.bytes[1] & 0x10: x16 = True
        elif op == 0xE2:  # SEP
            if ins.bytes[1] & 0x20: m16 = False
            if ins.bytes[1] & 0x10: x16 = False
        pc = (pc & 0xFF0000) | ((pc + ins.size) & 0xFFFF)
        if stop_at_rts and op in (0x60, 0x6B, 0x40):  # RTS RTL RTI
            break
    return out

def show(rom, addr, count=40, m16=True, x16=True, stop_at_rts=True):
    for a, b, t in disasm(rom, addr, count, m16, x16, stop_at_rts):
        print(f'{a:06X}  {b:<10} {t}')

def bgr555(w):
    r, g, b = w & 31, (w >> 5) & 31, (w >> 10) & 31
    return (r << 3 | r >> 2, g << 3 | g >> 2, b << 3 | b >> 2)

def palette(rom_or_bytes, off, n=16):
    d = rom_or_bytes
    return [bgr555(u16(d, off + 2*i)) for i in range(n)]

def decode_tile(data, off, bpp=4):
    """One 8x8 SNES planar tile -> 8 rows of 8 colour indices."""
    rows = []
    for y in range(8):
        row = []
        for x in range(8):
            bit = 7 - x; v = 0
            for p in range(bpp):
                base = off + (p // 2) * 16 + y * 2 + (p & 1)
                v |= ((data[base] >> bit) & 1) << p
            row.append(v)
        rows.append(row)
    return rows

def tiles_png(data, off, ntiles, path, pal=None, bpp=4, cols=16, scale=2):
    """Render ntiles planar tiles starting at off into a PNG sheet."""
    from PIL import Image
    tsz = 8 * bpp
    rows_n = (ntiles + cols - 1) // cols
    img = Image.new('RGB', (cols*8, rows_n*8))
    if pal is None:
        pal = [(i*255//((1<<bpp)-1),)*3 for i in range(1 << bpp)]
    px = img.load()
    for t in range(ntiles):
        if off + (t+1)*tsz > len(data): break
        tile = decode_tile(data, off + t*tsz, bpp)
        tx, ty = (t % cols) * 8, (t // cols) * 8
        for y in range(8):
            for x in range(8):
                px[tx+x, ty+y] = pal[tile[y][x] % len(pal)]
    if scale != 1:
        img = img.resize((img.width*scale, img.height*scale), Image.NEAREST)
    img.save(path)
    return path

def find_ptrs(rom, target, width=3):
    """Offsets in rom where a pointer to SNES address `target` is stored.
    width=3: 24-bit (tries both $C0+ and $40+ bank forms); width=2: 16-bit low word."""
    hits = []
    if width == 3:
        forms = {target & 0xFFFFFF, (target & 0x3FFFFF) | 0xC00000, (target & 0x3FFFFF) | 0x400000}
        for f in forms:
            pat = bytes((f & 0xFF, (f >> 8) & 0xFF, f >> 16))
            i = rom.find(pat)
            while i != -1:
                hits.append((i, f)); i = rom.find(pat, i + 1)
    else:
        pat = struct.pack('<H', target & 0xFFFF)
        i = rom.find(pat)
        while i != -1:
            hits.append((i, target & 0xFFFF)); i = rom.find(pat, i + 1)
    return sorted(hits)
