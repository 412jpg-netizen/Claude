"""Critic check (cheap, static): how close is MK3's animation numbering to UMK3's?
If MK3 and UMK3 use the same animation index for the same move, Sheeva's MK3 scripts can be moved
to UMK3 without an animation-number remap (unlike MK2, compat 2.3).
Method: for fighters present in both games with the same ID (0-10, 12, 13), compare for every
animation index n the first frame word reached from the common table (MK3 $86:DC53, UMK3 $88:95C3),
following $FFFF jumps and $FFF8 per-fighter branches (spr.first_frame). Frames are compared as
(frame number within set) because set numbers can differ. Also print the common->second table
distance for each game (UMK3: +$98 = 76 words).
Output: out/plan/sheeva_check.txt
"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import w16, b8, p24, rd
import spr

out = []
P = out.append
# distance between the two per-fighter animation tables, per fighter
for g, t1, t2 in (('mk3', 0x86DC53, 0x86DC9B), ('umk3', 0x8895C3, 0x889633)):
    ds = []
    n = 18 if g == 'mk3' else 28
    for fid in range(n):
        a = p24(g, t1 + 4 * fid); b = p24(g, t2 + 4 * fid)
        ds.append(None if not a else (b - a))
    P(f'{g}: second-table minus first-table per fighter: ' + ' '.join('-' if d is None else f'{d:+X}' for d in ds))

def frames(g, fid, nanim):
    r = []
    for n in range(nanim):
        try:
            v = spr.first_frame(g, fid, n)
        except Exception:
            v = None
        r.append(None if v is None else (v >> 9, v & 0x1FF))
    return r

NA = 76
tot = same = 0
for fid in list(range(0, 11)) + [12, 13]:
    a = frames('mk3', fid, NA); b = frames('umk3', fid, NA)
    eq = [i for i in range(NA) if a[i] and b[i] and a[i][1] == b[i][1]]
    both = [i for i in range(NA) if a[i] and b[i]]
    tot += len(both); same += len(eq)
    P(f'fid {fid:2}: indices with a first frame in both = {len(both)}, same frame number = {len(eq)}; differing: {[i for i in both if i not in eq][:20]}')
P(f'TOTAL same {same}/{tot}')
# Sheeva (MK3 id 11) basics
t = spr.anim_table('mk3', 11)
P(f'MK3 Sheeva common anim table {t:06X}; second table {p24("mk3", 0x86DC9B + 44):06X}')
S = spr.Set('mk3', 11)
P(f'MK3 set 11 header {S.hdr:06X}, frames {S.nframes()}, tiledir {S.tiledir:06X}, frametab {S.frametab:06X}, banktab {S.banktab:06X}')
banks = sorted({b8('mk3', S.tiledir + 4 * e + 2) for e in range(40)})
P(f'MK3 set 11 tile-directory bank bytes (first 40 slots, includes slots past the real end): {[hex(x) for x in banks]}')
sh = frames('mk3', 11, NA)
P('MK3 Sheeva first frames by anim index: ' + ' '.join('-' if x is None else f'{x[0]}:{x[1]}' for x in sh))
open('/home/claude/work/out/plan/sheeva_check.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
