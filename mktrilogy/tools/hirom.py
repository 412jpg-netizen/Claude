"""SNES address <-> file offset mapping for HiROM and ExHiROM images.

HiROM (the original 4 MB UMK3 cart, map mode $31):
  $C0-$FF:0000-FFFF and $40-$7D:0000-FFFF -> the whole bank
  $80-$BF and $00-$3F, $8000-$FFFF only   -> upper half of the same bank
ExHiROM (the 8 MB build, map mode $35):
  $C0-$FF full banks, $80-$BF upper halves -> file 0x000000-0x3FFFFF (as HiROM)
  $40-$7D full banks, $00-$3F upper halves -> file 0x400000-0x7FFFFF
Banks $7E/$7F are WRAM in both.
"""


def _bank_lo(addr):
    return (addr >> 16) & 0xFF, addr & 0xFFFF


def hirom_off(addr):
    bank, lo = _bank_lo(addr)
    if bank in (0x7E, 0x7F):
        return None
    b = bank & 0x7F
    if b >= 0x40:
        return ((b - 0x40) << 16) | lo
    if lo >= 0x8000:
        return (b << 16) | lo
    return None


def exhirom_off(addr):
    bank, lo = _bank_lo(addr)
    if bank in (0x7E, 0x7F):
        return None
    upper = 0 if bank & 0x80 else 0x400000
    b = bank & 0x7F
    if b >= 0x40:
        return upper | ((b - 0x40) << 16) | lo
    if lo >= 0x8000:
        return upper | (b << 16) | lo
    return None


class Rom:
    """Read helper over a ROM image, addressed by SNES address."""

    def __init__(self, data, mapper=hirom_off):
        self.data = data
        self.mapper = mapper

    def off(self, addr):
        o = self.mapper(addr)
        if o is None or o >= len(self.data):
            raise ValueError('address $%06X is not mapped ROM' % addr)
        return o

    def u8(self, addr):
        return self.data[self.off(addr)]

    def u16(self, addr):
        o = self.off(addr)
        return self.data[o] | self.data[o + 1] << 8

    def u24(self, addr):
        o = self.off(addr)
        return self.data[o] | self.data[o + 1] << 8 | self.data[o + 2] << 16

    def read(self, addr, n):
        o = self.off(addr)
        return bytes(self.data[o:o + n])
