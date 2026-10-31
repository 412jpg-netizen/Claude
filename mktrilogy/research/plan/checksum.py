"""Critic check: which checksum convention do the user's dumps follow?
For a ROM whose size is not a power of two, the usual SNES convention mirrors the last part up to
the next power of two. MK2 is 3 MB = 2 MB + 1 MB, so the convention predicts
sum(first 2 MB) + 2 * sum(last 1 MB). This is the evidence base for the 6 MB question
(compat open question 9): a 6 MB image would by analogy be sum(4 MB) + 2 * sum(last 2 MB).
Also prints SHA-1 / CRC32 of each input (used by the build pipeline to recognise clean dumps).
Output: out/plan/checksum.txt
"""
import hashlib, zlib
out = []
for g in ('umk3', 'mk3', 'mk2'):
    d = open(f'/home/claude/work/roms/{g}.sfc', 'rb').read()
    stored = d[0xFFDE] | d[0xFFDF] << 8
    comp = d[0xFFDC] | d[0xFFDD] << 8
    plain = sum(d) & 0xFFFF
    line = f'{g}: size {len(d):,} sha1 {hashlib.sha1(d).hexdigest()} crc32 {zlib.crc32(d) & 0xFFFFFFFF:08X} stored ${stored:04X} complement ${comp:04X} plain-sum ${plain:04X}'
    if len(d) == 0x300000:
        mir = (sum(d[:0x200000]) + 2 * sum(d[0x200000:])) & 0xFFFF
        line += f' mirrored-sum ${mir:04X}'
    out.append(line)
open('/home/claude/work/out/plan/checksum.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
