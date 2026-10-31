"""Block matcher: which bytes of ROM A also occur (as runs of >= K bytes) somewhere in ROM B?

Method
  1. 64-bit polynomial hash of every K-byte window (every offset, unaligned) of A and of B (numpy).
  2. For each A offset whose window hash occurs in B, take up to 16 candidate B offsets, verify the
     bytes and extend the match forward byte by byte; keep the longest.  Record segment
     (a_off, b_off, length) and continue at the first window that contains the mismatching byte.
  3. Segments whose bytes take <= 2 distinct values are classed as 'filler' (e.g. $00/$FF runs).
Output: pickle with segments + coverage mask, text report, PNG coverage map (1 row per 64 KB bank,
1 px = 64 bytes; colour = best class of the 64 bytes).

usage: python3 -I blockmatch.py A B [K]      (A, B in mk2 mk3 umk3)
"""
import sys, pickle
import numpy as np
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, A as AD

OUT = '/home/claude/work/out/compat/'


def win_hash(buf, k):
    a = np.frombuffer(buf, np.uint8).astype(np.uint64)
    n = len(a) - k + 1
    h = np.zeros(n, np.uint64)
    B = np.uint64(0x100000001B3)
    with np.errstate(over='ignore'):
        for i in range(k):
            h = h * B + a[i:i + n] + np.uint64(1)
    return h


def first_mismatch(a, b, p, q, limit):
    """length of the common run a[p:], b[q:] (<= limit)"""
    L = 0
    step = 256
    while L < limit:
        m = min(step, limit - L)
        x = np.frombuffer(a, np.uint8, m, p + L)
        y = np.frombuffer(b, np.uint8, m, q + L)
        ne = np.nonzero(x != y)[0]
        if len(ne):
            return L + int(ne[0])
        L += m
        step = min(step * 4, 65536)
    return L


def match(an, bn, k=32):
    a, b = ROM[an], ROM[bn]
    ha, hb = win_hash(a, k), win_hash(b, k)
    order = np.argsort(hb, kind='stable')
    hbs = hb[order]
    idx = np.searchsorted(hbs, ha)
    idx[idx >= len(hbs)] = len(hbs) - 1
    hit = hbs[idx] == ha
    segs = []
    p = 0
    na = len(a)
    hit_pos = np.nonzero(hit)[0]
    hp = 0
    while True:
        # next hit position >= p
        while hp < len(hit_pos) and hit_pos[hp] < p:
            hp += 1
        if hp >= len(hit_pos):
            break
        p = int(hit_pos[hp])
        i0 = int(idx[p])
        best = (0, None)
        j = i0
        while j < len(hbs) and hbs[j] == ha[p] and j < i0 + 16:
            q = int(order[j])
            L = first_mismatch(a, b, p, q, min(na - p, len(b) - q))
            if L > best[0]:
                best = (L, q)
            j += 1
        L, q = best
        if L >= k:
            segs.append((p, q, L))
            p = p + L - k + 1
        else:
            p += 1
    cov = np.zeros(na, np.uint8)   # 0 unique, 1 filler match, 2 moved match, 3 same-offset match
    for (p, q, L) in segs:
        seg = np.frombuffer(a, np.uint8, L, p)
        if len(np.unique(seg[:4096])) <= 2:
            cls = 1
        elif p == q:
            cls = 3
        else:
            cls = 2
        cur = cov[p:p + L]
        np.maximum(cur, cls, out=cur)
    return segs, cov


def runs(mask):
    """(start, length) runs of True"""
    m = np.concatenate([[0], mask.astype(np.int8), [0]])
    d = np.diff(m)
    s = np.nonzero(d == 1)[0]
    e = np.nonzero(d == -1)[0]
    return list(zip(s.tolist(), (e - s).tolist()))


def png(cov, path):
    from PIL import Image
    nb = len(cov) // 0x10000
    col = {0: (220, 40, 40), 1: (90, 90, 90), 2: (60, 120, 230), 3: (40, 200, 80)}
    img = Image.new('RGB', (1024, nb * 4))
    px = img.load()
    for bank in range(nb):
        blk = cov[bank * 0x10000:(bank + 1) * 0x10000].reshape(1024, 64)
        # pixel = unique if >= half the 64 bytes unique, else the commonest matched class
        for x in range(1024):
            v = blk[x]
            u = int((v == 0).sum())
            if u >= 32:
                c = 0
            else:
                c = int(np.bincount(v[v > 0], minlength=4).argmax())
            for yy in range(4):
                px[x, bank * 4 + yy] = col[c]
    img.save(path)


if __name__ == '__main__':
    an, bn = sys.argv[1], sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    segs, cov = match(an, bn, k)
    pickle.dump({'segs': segs, 'cov': cov, 'k': k}, open(f'{OUT}match_{an}_in_{bn}_k{k}.pkl', 'wb'))
    n = len(cov)
    with open(f'{OUT}match_{an}_in_{bn}_k{k}.txt', 'w') as f:
        tot = {c: int((cov == c).sum()) for c in range(4)}
        print(f'{an} ({n} B) vs {bn}, K={k}: unique {tot[0]}, filler {tot[1]}, moved {tot[2]}, same-offset {tot[3]}', file=f)
        print('per bank: bank unique filler moved same', file=f)
        for bank in range(n // 0x10000):
            v = cov[bank * 0x10000:(bank + 1) * 0x10000]
            print(f'  ${0xC0 | bank:02X}  ' + ' '.join(f'{int((v == c).sum()):6d}' for c in range(4)), file=f)
        print('segments >= 256 B (a_off -> b_off len delta):', file=f)
        for (p, q, L) in segs:
            if L >= 256:
                print(f'  {AD(p)} -> {AD(q)} {L:7d} delta {q - p:+#x}', file=f)
        print('unique runs >= 256 B:', file=f)
        for s, L in runs(cov == 0):
            if L >= 256:
                print(f'  {AD(s)}-{AD(s + L - 1)} {L:7d}', file=f)
    png(cov, f'{OUT}match_{an}_in_{bn}_k{k}.png')
    print(open(f'{OUT}match_{an}_in_{bn}_k{k}.txt').read()[:3000])
