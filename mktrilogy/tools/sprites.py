"""UMK3 sprite-set reader: set headers, frames, pieces and tile references.

Layout (ROM-MAP 1.5, verified):
  set tables   $86:EAEC (bank word) / $86:EB24 (address word), 28 sets
  set header   16 bytes: +0 word/+7 bank bank table; +2 word/+4 bank tile directory;
               +5 word/+7 bank frame-pointer table; +B bank/+C word delta block
  frame id     (set << 9) | frame, frame 1-based; frame count = (banktab - frametab) / 2
  frame bytes  N pieces, B of them 16x16 (4 refs), the rest 8x8 (1 ref)
  tile ref     bits 2-7 = directory byte offset, bits 8-15 = tile number
  dir entry    word address, byte bank, byte flags (bit 7 compressed, bit 6 2bpp, 0-5 record size)
"""

SET_BANKS = 0x86EAEC
SET_ADDRS = 0x86EB24
NUM_SETS = 28


def set_header(rom, s):
    bank = rom.u16(SET_BANKS + 2 * s) & 0xFF
    addr = rom.u16(SET_ADDRS + 2 * s)
    if bank == 0 and addr == 0:
        return None
    a = bank << 16 | addr
    h = rom.read(a, 16)
    banktab = h[7] << 16 | h[0] | h[1] << 8
    frametab = h[7] << 16 | h[5] | h[6] << 8
    return dict(set=s, addr=a, banktab=banktab, frametab=frametab,
                dir=h[4] << 16 | h[2] | h[3] << 8,
                delta=h[11] << 16 | h[12] | h[13] << 8,
                frames=(banktab - frametab) // 2)


def frame_refs(rom, hdr, frame):
    """Tile refs of one frame (1-based), in piece order."""
    f0 = frame - 1
    bank = rom.u8(hdr['banktab'] + (f0 >> 6))
    fa = bank << 16 | rom.u16(hdr['frametab'] + 2 * f0)
    n, big = rom.u8(fa), rom.u8(fa + 1)
    p = fa + 2
    refs = []
    for i in range(n):
        c = rom.u8(p)
        p += 1
        if not c >> 4:
            p += 1  # explicit x
        if not c & 15:
            p += 1  # explicit y
        k = 4 if i < big else 1
        refs.extend(rom.u16(p + 2 * j) for j in range(k))
        p += 2 * k
    return refs


def used_dir_entries(rom):
    """{(set, dir byte offset): SNES address of the entry} for every entry a frame references.
    Sets that share a header are reported once."""
    seen, out = set(), {}
    for s in range(NUM_SETS):
        hdr = set_header(rom, s)
        if hdr is None or hdr['addr'] in seen:
            continue
        seen.add(hdr['addr'])
        for f in range(1, hdr['frames'] + 1):
            for ref in frame_refs(rom, hdr, f):
                d = ref & 0xFC
                out[(s, d)] = hdr['dir'] + d
    return out


def tile_bytes(rom, entry_addr, tile):
    """The 32 bytes of one 4bpp tile as the game unpacks it ($83:8362 codec)."""
    ad, bk, fl = rom.u16(entry_addr), rom.u8(entry_addr + 2), rom.u8(entry_addr + 3)
    base = bk << 16 | ad
    if not fl & 0x80:
        if fl & 0x40:
            return rom.read(base + tile * 16, 16) + bytes(16)
        return rom.read(base + tile * 32, 32)
    size = fl & 0x3F
    p = base + 1 + tile * size
    fill = 0
    if tile >= rom.u8(base):
        fill = rom.u8(p)
        p += 1
    nm = 2 if fl & 0x40 else 4
    masks = rom.read(p, nm)
    lp = p + nm
    out = bytearray()
    for m in masks:
        for bit in range(7, -1, -1):
            if m >> bit & 1:
                out.append(rom.u8(lp))
                lp += 1
            else:
                out.append(fill)
    if nm == 2:
        out += bytes(16)
    return bytes(out)


def used_tiles(rom):
    """{(set, dir offset, tile number)} for every tile any frame draws."""
    seen, out = set(), set()
    for s in range(NUM_SETS):
        hdr = set_header(rom, s)
        if hdr is None or hdr['addr'] in seen:
            continue
        seen.add(hdr['addr'])
        for f in range(1, hdr['frames'] + 1):
            for ref in frame_refs(rom, hdr, f):
                out.add((s, ref & 0xFC, ref >> 8))
    return out
