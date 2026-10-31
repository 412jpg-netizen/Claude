"""Proof-of-concept MK2 -> UMK3 sprite-set converter, verified in memory (no ROM is written).

Differences between the two tile codecs (compat notes section 3.3):
  MK2  ($81:834B): compressed group, record n at base + n*s (4 masks + literals, fill 0)
  UMK3 ($83:8362): compressed group starts with a threshold byte T; record n at base + 1 + n*s;
                   records n >= T begin with a fill byte.  flags bit6 = 2bpp.
Everything else (16-byte set header, frame-pointer/bank tables, frame byte format, position/delta
table, tile-word layout, raw 4bpp groups, box table) is the same layout in both games.

Conversion used here: for every compressed tile group referenced by the set, emit a new blob
  [T = max_index_used + 1] + original group bytes, point the directory entry at the blob.
Raw groups ($20 flag) are kept as is.  If a group uses index 255, T would have to be 256 (impossible):
then T = 255 and a $00 fill byte is inserted in front of record 255 (the last record, so no other
record moves).  Groups using index 255 are listed in the output.

The converted set is then decoded with the UMK3 codec (spr.Set with codec='umk3', reading from a
virtual ROM = MK2 ROM + appended blobs) and every tile of every frame is compared with the MK2 decode.
Also writes a side-by-side PNG of a few donor frames decoded through the UMK3 path.
usage: python3 -I convert_test.py [mk2_set ...]      (default: 2 3 6 9 = Cage, Baraka, Raiden, Kintaro)
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import c, spr
from c import ROM, to_off

NAMES = {2: 'Johnny Cage', 3: 'Baraka', 6: 'Raiden', 9: 'Kintaro'}
PAL = {2: 0x00, 3: 0x39, 6: 0x32, 9: 0x40}


def convert(s):
    S = spr.Set('mk2', s)
    n = S.nframes()
    # collect max index used per directory entry
    used = {}
    for f in range(1, n + 1):
        pcs, a, e = S.pieces(f)
        for p in pcs:
            for r in p[3]:
                de = r & 0xFC
                used[de] = max(used.get(de, -1), r >> 8)
    base_rom = bytearray(ROM['mk2'])
    # virtual space: append blobs after the 3 MB MK2 image, at file 0x300000+ ($F0:0000+ in HiROM terms)
    blobs = bytearray()
    newdir = {}
    over = []
    for de, mx in sorted(used.items()):
        base, fl = S.dir_entry(de)
        if not fl & 0x80:
            newdir[de] = (base, fl)
            continue
        st = fl & 0x3F
        if mx >= 255:
            over.append(de)
        size = (mx + 1) * st
        if (to_off(base, len(ROM['mk2'])) & 0xFFFF) + size > 0x10000:
            over.append(('crosses bank', de))
        o = to_off(base, len(ROM['mk2']))
        grp = ROM['mk2'][o:o + size]
        # keep blobs inside one 64 KB bank
        cur = 0x300000 + len(blobs)
        if (cur & 0xFFFF) + 1 + size > 0x10000:
            blobs += bytes(0x10000 - (cur & 0xFFFF))
            cur = 0x300000 + len(blobs)
        if mx < 255:
            blobs += bytes([mx + 1]) + grp
        else:
            # T = 255: record 255 is read as [fill][masks][literals]; it is the last record, so a $00 fill
            # byte can be inserted in front of it without moving any other record.
            blobs += bytes([255]) + grp[:255 * st] + b'\x00' + grp[255 * st:]
        newdir[de] = (0xC00000 | cur, fl)
    vrom = bytes(base_rom) + bytes(blobs)
    return S, newdir, vrom, over, used


class VSet(spr.Set):
    """MK2 set whose tile directory is replaced by the converted one; decoded with the UMK3 codec."""
    def __init__(self, S, newdir, vrom):
        self.__dict__.update(S.__dict__)
        self.codec = 'umk3'
        self.newdir = newdir
        self.vrom = vrom

    def dir_entry(self, ref):
        return self.newdir[ref & 0xFC]

    def tile(self, ref):
        # same algorithm as spr.Set.tile (umk3 codec) but on the virtual ROM
        base, fl = self.dir_entry(ref)
        R = self.vrom
        o = lambda a: to_off(a, len(R))
        nn = ref >> 8
        bank = base & 0xFF0000
        if not fl & 0x80:
            a = bank | ((base + nn * 32) & 0xFFFF)
            return R[o(a):o(a) + 32]
        st = fl & 0x3F
        T = R[o(base)]
        p = o(bank | ((base + nn * st + 1) & 0xFFFF))
        fill = 0
        if nn >= T:
            fill = R[p]; p += 1
        masks = R[p:p + 4]
        lit = p + 4
        out = bytearray()
        for m in masks:
            for k in range(8):
                if m & (0x80 >> k):
                    out.append(R[lit]); lit += 1
                else:
                    out.append(fill)
        return bytes(out)


if __name__ == '__main__':
    sets = [int(a) for a in sys.argv[1:]] or [2, 3, 6, 9]
    items = []
    for s in sets:
        S, newdir, vrom, over, used = convert(s)
        V = VSet(S, newdir, vrom)
        n = S.nframes()
        tiles = bad = 0
        for f in range(1, n + 1):
            pcs, a, e = S.pieces(f)
            for p in pcs:
                for r in p[3]:
                    tiles += 1
                    if S.tile(r) != V.tile(r):
                        bad += 1
        ncomp = sum(1 for de in used if S.dir_entry(de)[1] & 0x80)
        print(f'MK2 set {s} ({NAMES.get(s, "?")}): {n} frames, {len(used)} dir entries used ({ncomp} compressed), '
              f'max tile index {max(used.values())}, groups using index 255: {over}; '
              f'tile refs checked {tiles}, mismatches {bad}; added bytes {len(vrom) - len(ROM["mk2"])}')
        pal = spr.palette('mk2', PAL.get(s, 0))
        for f in (1, n // 3, 2 * n // 3):
            items.append((f'{NAMES.get(s, s)} f{f} MK2', spr.render(S, f, pal, scale=1)))
            items.append((f'{NAMES.get(s, s)} f{f} conv', spr.render(V, f, pal, scale=1)))
    spr.sheet(items, '/home/claude/work/out/compat/convert_test.png', cell=(110, 150), cols=6)
