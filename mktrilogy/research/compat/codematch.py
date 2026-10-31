"""Code-skeleton matching of UMK3 traced code against another ROM's code banks.

The UMK3 analyst's recursive-descent trace (out/umk3/trace.pkl, 31,656 instructions in $80-$88) gives
instruction boundaries.  Contiguous traced runs are cut into windows of W instructions (step W//2).
Each window becomes a regex: opcode bytes fixed, REP/SEP operands fixed, every other operand byte a
wildcard.  A window that occurs exactly once in the target's code area (upper halves of the code
banks) is accepted; the paired operands of the two versions are recorded.

Output (out/compat/codematch_<tgt>.pkl / .txt):
  - fraction of traced UMK3 instructions with a unique counterpart in the target
  - per-bank coverage
  - WRAM operand pairs (UMK3 addr -> target addr, with vote counts) for abs/abs,X/abs,Y/long operands
    below $8000 or in bank $7E/$7F  -> the address translation between the two engines
usage: python3 -I codematch.py mk2|mk3 [W]
"""
import sys, re, pickle
from collections import Counter, defaultdict
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, lst
import d65

TGT_BANKS = {'mk2': range(0, 6), 'mk3': range(0, 9)}
ABSM = {'abs', 'absx', 'absy', 'long', 'longx'}


def windows(ins, W):
    pcs = sorted(ins)
    run = [pcs[0]]
    runs = []
    for p in pcs[1:]:
        q = run[-1]
        if (q & 0xFF0000) == (p & 0xFF0000) and (q + ins[q][0]) & 0xFFFF == p & 0xFFFF:
            run.append(p)
        else:
            runs.append(run)
            run = [p]
    runs.append(run)
    for r in runs:
        if len(r) < W:
            continue
        for i in range(0, len(r) - W + 1, max(1, W // 2)):
            yield r[i:i + W]


def main(tgt, W=10):
    T = pickle.load(open('/home/claude/work/out/umk3/trace.pkl', 'rb'))
    ins = T['insns']
    rom_u = ROM['umk3']
    rt = ROM[tgt]
    regions = [(b << 16 | 0x8000, (b + 1) << 16) for b in TGT_BANKS[tgt]]
    matched = {}
    pairs = defaultdict(Counter)
    nwin = nuniq = nmulti = 0
    for win in windows(ins, W):
        pat = b''
        for p in win:
            sz, m, x, txt, op, val = ins[p]
            pat += re.escape(bytes([op]))
            if sz > 1:
                if op in (0xC2, 0xE2):
                    pat += re.escape(bytes([val]))
                else:
                    pat += b'.' * (sz - 1)
        rx = re.compile(pat, re.S)
        hits = []
        for lo, hi in regions:
            for mm in rx.finditer(rt, lo, hi):
                hits.append(mm.start())
                if len(hits) > 1:
                    break
            if len(hits) > 1:
                break
        nwin += 1
        if len(hits) != 1:
            nmulti += len(hits) > 1
            continue
        nuniq += 1
        o = hits[0]
        tpc = 0x800000 | o
        for p in win:
            sz, m, x, txt, op, val = ins[p]
            matched[p] = tpc
            if d65.OPS[op][1] in ABSM and val is not None:
                tv = int.from_bytes(rt[o + 1:o + sz], 'little')
                if val != tv and ((val & 0xFFFF) < 0x8000 or (val >> 16) in (0x7E, 0x7F)) and d65.OPS[op][1] != 'long' or \
                        (d65.OPS[op][1] in ('long', 'longx') and (val >> 16) in (0x7E, 0x7F)):
                    pairs[val][tv] += 1
            o += sz
            tpc += sz
    tot = len(ins)
    per = Counter(p >> 16 for p in matched)
    allb = Counter(p >> 16 for p in ins)
    out = open(f'/home/claude/work/out/compat/codematch_{tgt}.txt', 'w')
    print(f'UMK3 traced insns {tot}; windows {nwin} (W={W}), unique hits {nuniq}, ambiguous {nmulti}', file=out)
    print(f'UMK3 traced insns with a unique counterpart in {tgt}: {len(matched)} ({100 * len(matched) / tot:.1f}%)', file=out)
    for b in sorted(allb):
        print(f'  bank ${b:02X}: {per[b]}/{allb[b]}', file=out)
    print('WRAM operand translation UMK3 -> ' + tgt + ' (votes):', file=out)
    for v in sorted(pairs):
        best, n = pairs[v].most_common(1)[0]
        tot_v = sum(pairs[v].values())
        print(f'  ${v:06X} -> ${best:06X} ({n}/{tot_v})  delta {best - v:+#x}', file=out)
    out.close()
    pickle.dump(dict(matched=matched, pairs=dict(pairs)), open(f'/home/claude/work/out/compat/codematch_{tgt}.pkl', 'wb'))
    print(open(f'/home/claude/work/out/compat/codematch_{tgt}.txt').read()[:2500])


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10)
