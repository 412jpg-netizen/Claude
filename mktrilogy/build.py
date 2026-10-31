#!/usr/bin/env python3
"""Build the mktrilogy ROM from your own UMK3 dump.

    python build.py --umk3 "path/to/Ultimate Mortal Kombat 3 (USA).sfc"
    python build.py --umk3 umk3.sfc --exhirom          # 8 MB ExHiROM build
    python build.py --umk3 umk3.sfc --identity         # no patches; must equal the input

Writes build/mktrilogy.sfc (or -o PATH) plus a report next to it. Nothing from the game is
stored in this repository: every patch checks the instructions it expects before writing.
Needs only Python 3.8+.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from tools import checksum, roms  # noqa: E402
from tools.hirom import hirom_off  # noqa: E402
from patches import boss_unlock, exhirom  # noqa: E402

CONTENT_PATCHES = [boss_unlock]


def build(umk3, identity=False, expand=False, skip=()):
    """Return (image, report lines). umk3 is the verified 4 MB input."""
    data = bytearray(umk3)
    report = ['input UMK3 sha1 %s' % roms.sha1(umk3)]
    if identity:
        return data, report + ['identity build: no patches']
    for mod in CONTENT_PATCHES:
        if mod.NAME in skip:
            report.append('%s: skipped' % mod.NAME)
            continue
        for name, off in mod.apply(data, hirom_off):
            report.append('%s: %s (file 0x%06X)' % (mod.NAME, name, off))
    headers = (checksum.HIROM_HEADER,)
    if expand:
        data, low = exhirom.expand(data)
        headers = (checksum.HIROM_HEADER, checksum.EXHIROM_HEADER)
        report.append('exhirom: 8 MB, map mode $35, upper 4 MB mirrors the lower 4 MB')
        for s, d, o in low:
            report.append('exhirom: set %d dir +$%02X bank byte at file 0x%06X -> $C0+' % (s, d, o))
    chk = checksum.fix(data, headers)
    report.append('checksum $%04X, size %d bytes, sha1 %s' % (chk, len(data), roms.sha1(data)))
    return data, report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--umk3', required=True, help='your Ultimate Mortal Kombat 3 (USA) .sfc')
    ap.add_argument('-o', '--out', default=os.path.join(HERE, 'build', 'mktrilogy.sfc'))
    ap.add_argument('--exhirom', action='store_true', help='expand to 8 MB ExHiROM')
    ap.add_argument('--identity', action='store_true', help='apply nothing (pipeline self-check)')
    ap.add_argument('--skip', action='append', default=[], metavar='PATCH',
                    help='leave out a patch by name (%s)' % ', '.join(m.NAME for m in CONTENT_PATCHES))
    args = ap.parse_args(argv)

    try:
        umk3 = roms.load('umk3', args.umk3)
    except roms.RomError as e:
        sys.exit(str(e))
    data, report = build(umk3, identity=args.identity, expand=args.exhirom, skip=args.skip)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'wb') as f:
        f.write(data)
    with open(os.path.splitext(args.out)[0] + '.report.txt', 'w') as f:
        f.write('\n'.join(report) + '\n')
    print('\n'.join(report))
    print('wrote', args.out)


if __name__ == '__main__':
    main()
