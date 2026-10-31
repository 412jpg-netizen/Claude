"""Critic check: dump the UMK3 kode-message table $85:EA3E (umk3-map 10.2: 6-byte entries =
flag variable word, value word, message pointer word in bank $85) until the entries stop looking
valid, and print each message string. Used to find the RAM flags behind existing gameplay toggles
(SHADOW FIGHTING, HYPER KOMBAT, brutalities) that an Aggressor-meter implementation could reuse.
Entry layout is from umk3-map 10.2 (LIKELY until the reader is traced). Output: out/plan/kodemsgs.txt
"""
import sys, re
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import w16, rd
out = []
a = 0x85EA3E
for i in range(40):
    var, val, ptr = w16('umk3', a), w16('umk3', a + 2), w16('umk3', a + 4)
    if ptr < 0x8000:
        out.append(f'stop at ${a>>16:02X}:{a&0xFFFF:04X} (ptr {ptr:04X})'); break
    s = rd('umk3', 0x850000 | ptr, 48).split(b'\x00')[0]
    s = re.sub(rb'[^\x20-\x7e]', b'.', s).decode()
    out.append(f'{i:2} ${a>>16:02X}:{a&0xFFFF:04X}  var ${var:04X}  val ${val:04X}  msg $85:{ptr:04X}  "{s}"')
    a += 6
open('/home/claude/work/out/plan/kodemsgs.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
