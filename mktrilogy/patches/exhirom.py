"""M2: expand the 4 MB HiROM image to an 8 MB ExHiROM image with no content change.

Steps (PLAN.md section 4):
1. Copy the whole 4 MB into the upper 4 MB. Under ExHiROM, banks $40-$7D and $00-$3F:8000+
   read the upper 4 MB, so with the copy every ROM address returns the same byte as before.
   Later milestones overwrite parts of this mirror with new content.
2. Point the 9 sprite tile-directory entries whose bank byte is $00-$07 at $C0-$C7 instead.
   Same bytes under HiROM; under ExHiROM it keeps Kano, Liu Kang and effect sets 17/18/20/21/
   24/25 independent of the mirror. The entries are found by walking every frame, and must
   match the list verified in ROM-MAP 1.12.
3. Write map mode $35 and ROM size $0D in both header copies (file 0x00FFC0 and 0x40FFC0;
   the console reads 0x40FFC0) and fix the checksum over 8 MB.
"""
from tools import checksum, sprites
from tools.hirom import Rom, hirom_off

NAME = 'exhirom'
SIZE = 0x800000

EXPECTED_LOW_BANK_BYTES = {0x3FB3F5, 0x3FB42D, 0x3FB832, 0x3FC68F, 0x3FC52F,
                           0x3FCAD3, 0x3FD4ED, 0x3FC727, 0x3FC841}


def low_bank_entries(data):
    rom = Rom(data, hirom_off)
    out = []
    for (s, d), a in sorted(sprites.used_dir_entries(rom).items()):
        if rom.u8(a + 2) < 0x40:
            out.append((s, d, rom.off(a + 2)))
    return out


def expand(data):
    """data: the 4 MB HiROM image (bytes or bytearray). Returns the 8 MB bytearray."""
    if len(data) != 0x400000:
        raise ValueError('%s: expected a 4 MB HiROM image, got %d bytes' % (NAME, len(data)))
    low = low_bank_entries(data)
    found = {o for _, _, o in low}
    if found != EXPECTED_LOW_BANK_BYTES:
        raise ValueError('%s: low-bank tile entries differ from the verified list: %s'
                         % (NAME, sorted('%06X' % o for o in found ^ EXPECTED_LOW_BANK_BYTES)))
    out = bytearray(data) + bytearray(data)
    for _, _, o in low:
        out[o] |= 0xC0
        out[o + 0x400000] |= 0xC0
    for h in (checksum.HIROM_HEADER, checksum.EXHIROM_HEADER):
        out[h + 0x15] = 0x35
        out[h + 0x17] = 0x0D
    return out, low
