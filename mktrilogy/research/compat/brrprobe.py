"""BRR (SPC700 sample) signature test for a byte range: for each of the 9 phase alignments, the fraction
of 9-byte blocks whose header byte has range nibble <= 12 and end-flag clear except possibly the last.
Random data gives ~0.81 for the nibble test; BRR gives 1.0.  usage: imported by other scripts."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM


def brr_score(g, o, L):
    r = ROM[g]
    best = (0, 0)
    for ph in range(9):
        hs = [r[o + ph + 9 * k] for k in range((L - ph) // 9)]
        if len(hs) < 8:
            continue
        ok = sum(1 for h in hs[:-1] if (h >> 4) <= 12 and not (h & 1))
        f = ok / (len(hs) - 1)
        if f > best[0]:
            best = (f, ph)
    return best
