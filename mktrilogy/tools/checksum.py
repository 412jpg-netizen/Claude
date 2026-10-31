"""SNES internal checksum.

The checksum is the 16-bit sum of every byte in the image. For a size that is not a power of
two the remainder is counted as if mirrored up to the next power of two; MK2's 3 MB dump stores
sum(first 2 MB) + 2 * sum(last 1 MB). The header holds the complement at +$1C and the checksum
at +$1E, little-endian.
"""

HIROM_HEADER = 0x00FFC0
EXHIROM_HEADER = 0x40FFC0


def compute(data):
    n = len(data)
    p = 1
    while p * 2 <= n:
        p *= 2
    if p == n:
        return sum(data) & 0xFFFF
    rest = data[p:]
    return (sum(data[:p]) + sum(rest) * (p // len(rest))) & 0xFFFF


def stored(data, header=HIROM_HEADER):
    comp = data[header + 0x1C] | data[header + 0x1D] << 8
    chk = data[header + 0x1E] | data[header + 0x1F] << 8
    return chk, comp


def fix(data, headers=(HIROM_HEADER,)):
    """Recompute the checksum in place and write it to every header given.

    Each complement/checksum pair contributes $1FE to the sum whatever its value, so the pairs
    are set to FFFF/0000 first, summed, then filled in.
    """
    for h in headers:
        data[h + 0x1C:h + 0x20] = b'\xff\xff\x00\x00'
    chk = compute(data)
    comp = chk ^ 0xFFFF
    for h in headers:
        data[h + 0x1C] = comp & 0xFF
        data[h + 0x1D] = comp >> 8
        data[h + 0x1E] = chk & 0xFF
        data[h + 0x1F] = chk >> 8
    return chk
