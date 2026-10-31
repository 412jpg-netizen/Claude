"""Static self-tests for the build (no emulator).

Point them at your dumps with environment variables, or put the files in mktrilogy/roms/
(git-ignored) as umk3.sfc, mk3.sfc and mk2.sfc:

    MKT_UMK3=path/to/umk3.sfc python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import build  # noqa: E402
from tools import checksum, d65, roms, sprites  # noqa: E402
from tools.hirom import Rom, exhirom_off, hirom_off  # noqa: E402
from patches import boss_unlock, exhirom  # noqa: E402


def rom_path(name):
    return os.environ.get('MKT_' + name.upper(), os.path.join(HERE, 'roms', name + '.sfc'))


def need(name):
    p = rom_path(name)
    if not os.path.exists(p):
        raise unittest.SkipTest('%s not found (set MKT_%s)' % (p, name.upper()))
    return roms.load(name, p)


class Checksums(unittest.TestCase):
    def test_stored_checksums_match(self):
        for name in ('umk3', 'mk3', 'mk2'):
            p = rom_path(name)
            if not os.path.exists(p):
                continue
            data = roms.load(name, p)
            chk, comp = checksum.stored(data)
            self.assertEqual(checksum.compute(data), chk, name)
            self.assertEqual(chk ^ 0xFFFF, comp, name)


class Builds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.umk3 = need('umk3')
        cls.m1, _ = build.build(cls.umk3)
        cls.big, _ = build.build(cls.umk3, expand=True)

    def test_identity_reproduces_input(self):
        data, _ = build.build(self.umk3, identity=True)
        self.assertEqual(roms.sha1(data), roms.KNOWN['umk3'][0])

    def test_boss_unlock_changes_only_its_bytes(self):
        diff = [i for i in range(len(self.umk3)) if self.umk3[i] != self.m1[i]]
        allowed = {0x0086B1, 0x0086B4} | set(range(0xFFDC, 0xFFE0))
        self.assertTrue(set(diff) <= allowed, ['%06X' % i for i in diff])
        rom = Rom(self.m1)
        self.assertEqual(d65.text_at(rom, 0x8086B1, 2), ['STA $3BAE', 'STA $3BB0'])
        # the hidden-cell routine still reads both flags
        self.assertEqual(d65.text_at(rom, 0x84A328, 2), ['LDA $3BAE', 'ORA $3BB0'])
        chk, comp = checksum.stored(self.m1)
        self.assertEqual(checksum.compute(self.m1), chk)
        self.assertEqual(chk ^ 0xFFFF, comp)

    def test_exhirom_header_and_checksum(self):
        big = self.big
        self.assertEqual(len(big), exhirom.SIZE)
        h = checksum.EXHIROM_HEADER
        self.assertEqual(big[h + 0x15], 0x35)
        self.assertEqual(big[h + 0x17], 0x0D)
        chk, comp = checksum.stored(big, h)
        self.assertEqual(checksum.compute(big), chk)
        self.assertEqual(chk ^ 0xFFFF, comp)
        self.assertEqual(checksum.stored(big, checksum.HIROM_HEADER), (chk, comp))
        # reset/NMI/IRQ vectors are where the console reads them ($00:FFE0-$00:FFFF)
        self.assertEqual(big[0x40FFE0:0x410000], self.m1[0xFFE0:0x10000])

    def test_exhirom_reads_like_hirom(self):
        """Every ROM address returns the same byte under ExHiROM as the 4 MB build under HiROM,
        apart from the 9 patched bank bytes."""
        patched = exhirom.EXPECTED_LOW_BANK_BYTES
        headers = set(range(0xFFC0, 0xFFE0)) | set(range(0x40FFC0, 0x40FFE0))
        for bank in range(0x100):
            for lo in list(range(0, 0x10000, 97)) + [0x7FFF, 0x8000, 0xFFC0, 0xFFFF]:
                a = bank << 16 | lo
                o_old, o_new = hirom_off(a), exhirom_off(a)
                self.assertEqual(o_old is None, o_new is None, '%06X' % a)
                if o_old is None or o_old in patched or o_new in headers:
                    continue
                self.assertEqual(self.m1[o_old], self.big[o_new], '$%06X' % a)

    def test_sprite_tiles_do_not_need_the_mirror(self):
        """With the upper 4 MB blanked (except bank $00), every tile any frame draws decodes the
        same under ExHiROM as the original does under HiROM. Proves the 9 bank-byte fixes cover
        all sprite tile data, so later content may overwrite the mirror."""
        blank = bytearray(self.big)
        blank[0x400000:0x408000] = b'\xff' * 0x8000
        blank[0x410000:] = b'\xff' * (len(blank) - 0x410000)
        old, new = Rom(self.umk3, hirom_off), Rom(blank, exhirom_off)
        entries_old = sprites.used_dir_entries(old)
        self.assertEqual(len(entries_old), 917)
        for s, d, t in sorted(sprites.used_tiles(old)):
            a = entries_old[(s, d)]
            self.assertEqual(sprites.tile_bytes(old, a, t), sprites.tile_bytes(new, a, t),
                             'set %d dir +%02X tile %d' % (s, d, t))


if __name__ == '__main__':
    unittest.main()
