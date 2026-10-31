import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
r = v.load('umk3')
def runs(val, minlen):
    out = []; i = 0; n = len(r)
    while i < n:
        if r[i] == val:
            j = i
            while j < n and r[j] == val: j += 1
            if j - i >= minlen: out.append((i, j - i))
            i = j
        else: i += 1
    return out
ff = runs(0xFF, 64)
print('FF runs >=64:', len(ff), 'total', sum(l for _, l in ff))
for o, l in sorted(ff, key=lambda x: -x[1])[:12]:
    print('  file %06X len %5d  ($%06X-$%06X)' % (o, l, 0xC00000 | o, 0xC00000 | (o + l - 1)))
print('per code bank C0-C8: longest FF run in bank and its start')
for b in range(0, 9):
    br = [(o, l) for o, l in runs(0xFF, 16) if (o >> 16) == b]
    if br:
        o, l = max(br, key=lambda x: x[1]); print('  $%02X: $%06X len %d' % (0xC0 + b, 0xC00000 | o, l))
z = runs(0x00, 256)
print('00 runs >=256:', len(z), 'total', sum(l for _, l in z))
for o, l in sorted(z, key=lambda x: -x[1])[:8]:
    print('  file %06X len %5d' % (o, l))
