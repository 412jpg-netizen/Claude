"""Trailing padding per 64KB bank (file offsets), UMK3. Read-only.
Prints bank, pad byte, first padded address, free bytes. Also lists total."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes
rom = snes.load('umk3')
tot = 0
rows = []
for b in range(len(rom) // 0x10000):
    base = b * 0x10000
    end = base + 0x10000
    pad = rom[end - 1]
    if pad not in (0xFF, 0x00):
        rows.append((b, None, None, 0))
        continue
    i = end
    while i > base and rom[i - 1] == pad:
        i -= 1
    free = end - i
    rows.append((b, pad, i, free))
    tot += free
for b, pad, i, free in rows:
    if free >= 64:
        print(f'bank file {b:02X} (SNES ${0xC0 + b:02X}) pad={pad:02X} from ${0xC0 + b:02X}:{i & 0xFFFF:04X} free={free}')
print('total trailing free bytes (runs >=1):', tot)
