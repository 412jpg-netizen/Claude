"""Critic check: ASCII strings relevant to Trilogy features in all three ROMs (BRUTAL, ANIMAL,
AGGRESS, BABALIT, MERCY, GORO, SHEEVA, CHAMELEON, ...), with 60 characters of printable context.
Used for PLAN.md P8 (MK2 'GORO'S LAIR' text) and P10 (UMK3 'ONE BUTTON BRUTALITIES').
Output: out/plan/strings.txt
"""
import re
WORDS = [b'BRUTAL', b'ANIMAL', b'AGGRESS', b'FRIENDSHIP', b'BABALIT', b'MERCY', b'GORO', b'SHEEVA',
         b'CHAMELEON', b'KHAMELEON', b'KINTARO', b'BARAKA', b'RAYDEN', b'CAGE', b'TREASURE']
out = []
for g in ('umk3', 'mk3', 'mk2'):
    d = open(f'/home/claude/work/roms/{g}.sfc', 'rb').read()
    for w in WORDS:
        for m in re.finditer(re.escape(w), d):
            a = m.start()
            ctx = re.sub(rb'[^\x20-\x7e]', b'.', d[max(0, a - 60):a + 40]).decode()
            out.append(f'{g:5} {w.decode():10} ${0xC0 | (a >> 16):02X}:{a & 0xFFFF:04X}  {ctx}')
open('/home/claude/work/out/plan/strings.txt', 'w').write('\n'.join(out) + '\n')
print(len(out), 'hits')
