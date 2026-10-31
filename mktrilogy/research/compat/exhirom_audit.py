"""ExHiROM audit of UMK3 (static).  In ExHiROM, banks $80-$BF/$C0-$FF keep mapping to file 0x000000-0x3FFFFF,
but $00-$3F ($8000-$FFFF) and $40-$7D ($0000-$FFFF) map to file 0x400000-0x7FFFFF.  So every ROM access
through a bank in $00-$7D is a hazard.  Checks:

 A. traced code (out/umk3/trace.pkl): long operands / JSL / JML whose bank is $00-$3F or $40-$7D;
    PLB sequences that set DB to a bank < $7E other than $00; AND/ORA/EOR/CMP immediates of $3F/$7F/$80/$C0/$40
    (possible bank-byte masking) with context.
 B. reads of the internal header ($xx:FFB0-$xx:FFFF long operands, any bank) in all code-bank bytes.
 C. bank bytes stored in data tables reachable from known structures:
    sprite set headers ($86:EAEC/$86:EB24), their frame-bank tables and tile-directory entries used by frames,
    palette table $88:9984 (309), animation-table pointers $88:95C3/$88:9633, VS-portrait banks $83:EEC6,
    stage/screen layer descriptors ($84:8A22 records: tiles/map/palette pointers).
 D. JSL $88:AD30 / $84:98B0 call sites: immediates loaded in the 10 instructions before the call that look
    like a bank byte < $80.
usage: python3 -I exhirom_audit.py   (writes out/compat/exhirom_audit.txt)
"""
import sys, pickle, re
from collections import Counter, defaultdict
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import ROM, w16, b8, p24, to_off, A
import spr, stagecmp, d65

out = open('/home/claude/work/out/compat/exhirom_audit.txt', 'w')
P = lambda *a: print(*a, file=out)
r = ROM['umk3']
T = pickle.load(open('/home/claude/work/out/umk3/trace.pkl', 'rb'))
ins = T['insns']
pcs = sorted(ins)
idx = {p: i for i, p in enumerate(pcs)}


def low(b):
    return b < 0x7E


# ---------- A
P('A1. traced long operands / JSL / JML with bank in $00-$7D (excluding $7E/$7F WRAM):')
cnt = Counter()
for p in pcs:
    sz, m, x, txt, op, val = ins[p]
    mode = d65.OPS[op][1]
    if mode in ('long', 'longx') and val is not None:
        bk = val >> 16
        if low(bk):
            # $00-$3F with addr < $8000 is WRAM mirror / I/O: harmless in every mapping
            hz = (bk < 0x40 and (val & 0xFFFF) >= 0x8000) or 0x40 <= bk < 0x7E
            cnt['io/wram-mirror' if not hz else 'ROM-hazard'] += 1
            if hz:
                P(f'   {p:06X} {txt}')
P('   counts:', dict(cnt))
P('A2. PLB preceded (within 4 insns) by PEA/LDA # with a bank byte < $7E, other than $00:')
for p in pcs:
    if ins[p][4] != 0xAB:
        continue
    i = idx[p]
    for q in pcs[max(0, i - 4):i]:
        sz, m, x, txt, op, val = ins[q]
        if op == 0xF4 and val is not None:
            for bb in (val & 0xFF, val >> 8):
                if 0 < bb < 0x7E:
                    P(f'   {p:06X} PLB after {q:06X} {txt}')
        if op == 0xA9 and val is not None and 0 < (val & 0xFF) < 0x7E and ins[q + sz if q + sz in ins else q][4] == 0x48:
            P(f'   {p:06X} PLB after {q:06X} {txt}; PHA')
P('A3. immediate masks that could clamp bank bytes (AND/ORA #$3F/$7F/$C0/$80/$40, 8- or 16-bit):')
masks = Counter()
for p in pcs:
    sz, m, x, txt, op, val = ins[p]
    if op in (0x29, 0x09) and val in (0x3F, 0x7F, 0xC0, 0x80, 0x40, 0x003F, 0x007F, 0x00C0):
        i = idx[p]
        ctx = ' ; '.join(ins[q][3] for q in pcs[max(0, i - 3):i + 3])
        masks[txt] += 1
        P(f'   {p:06X} {txt:<14} ctx: {ctx}')
P('   counts:', dict(masks))

# ---------- B
P('B. long-operand reads of $xx:FFB0-$xx:FFFF (internal header / vectors) anywhere in code banks $80-$88:')
hits = []
for mm in re.finditer(rb'[\xaf\xbf\x2f\x3f\x4f\x5f\xcf\xdf\x6f\x7f\xef\xff\x0f\x1f][\xb0-\xff]\xff[\x00\x40\x80\xc0\xbf\xff\x3f\x7f]', r[:0x90000]):
    o = mm.start()
    if (o & 0xFFFF) >= 0x8000 and r[o:o + 4] != b'\xff\xff\xff\xff' and r[o + 3] != 0xFF:
        hits.append(o)
for o in hits:
    a = 0x800000 | o
    tag = 'traced' if a in ins else 'untraced bytes'
    P(f'   {a:06X} {r[o:o + 4].hex()} ({tag})')
P(f'   {len(hits)} byte-pattern hits; traced instructions among them: {sum(1 for o in hits if (0x800000 | o) in ins)}')

# ---------- C
P('C. bank bytes in data structures (value < $80 means the pointer goes through $00-$7D):')
bad = defaultdict(list)
G = spr.GAMES['umk3']
seen = set()
nchk = Counter()
for s in range(28):
    S = spr.Set('umk3', s)
    if S.hdr is None:
        continue
    nchk['set headers'] += 1
    for nm, a in (('header', S.hdr), ('banktab', S.banktab), ('tiledir', S.tiledir), ('frametab', S.frametab),
                  ('deltas', S.deltas)):
        if (a >> 16) < 0x80:
            bad['sprite set table'].append(f'set {s} {nm} ${a:06X}')
    if S.hdr in seen:
        continue
    seen.add(S.hdr)
    n = S.nframes()
    for k in range((n + 63) // 64):
        nchk['frame bank bytes'] += 1
        if b8('umk3', S.banktab + k) < 0x80:
            bad['frame bank byte'].append(f'set {s} block {k}: ${b8("umk3", S.banktab + k):02X}')
    used = set()
    for f in range(1, n + 1):
        try:
            pcs_, a, e = S.pieces(f)
        except Exception:
            continue
        for pc in pcs_:
            for rr in pc[3]:
                used.add(rr & 0xFC)
    for de in used:
        base, fl = S.dir_entry(de)
        nchk['tile dir entries'] += 1
        if (base >> 16) < 0x80:
            bad['tile directory'].append(f'set {s} entry {de >> 2}: ${base:06X} flags ${fl:02X}')
for i in range(309):
    nchk['palette ptrs'] += 1
    a = p24('umk3', 0x889984 + 3 * i)
    if (a >> 16) < 0x80:
        bad['palette table'].append(f'id {i}: ${a:06X}')
for t in (0x8895C3, 0x889633):
    for i in range(28):
        nchk['anim table ptrs'] += 1
        lo, bk = w16('umk3', t + 4 * i), w16('umk3', t + 4 * i + 2) & 0xFF
        if (lo or bk) and bk < 0x80:
            bad['anim table'].append(f'${t:06X}[{i}]: ${bk:02X}:{lo:04X}')
for i in range(26):
    nchk['VS banks'] += 1
    bk = w16('umk3', 0x83EEC6 + 2 * i) & 0xFF
    if bk and bk < 0x80:
        bad['VS bank'].append(f'id {i}: ${bk:02X}')
for rec in range(29):
    for k, d in enumerate(stagecmp.descs('umk3', rec)):
        if not d or 'tiles' not in d:
            continue
        for nm in ('tiles', 'map', 'pal'):
            a = d[nm]
            nchk['stage layer ptrs'] += 1
            if (a >> 16) < 0x80 and (a & 0xFFFF) not in (0xFFFF, 0x0001):
                bad['stage layer'].append(f'rec {rec} L{k} ${d["L"]:04X} {nm} ${a:06X}')
            elif (a >> 16) < 0x80:
                bad['stage layer (null marker)'].append(f'rec {rec} L{k} {nm} ${a:06X}')
P('   checked:', dict(nchk))
for k, v in bad.items():
    P(f'   {k}: {len(v)}')
    for x in v[:40]:
        P('      ', x)

# ---------- D
P('D. LZ call sites ($88:AD30 / wrapper $84:98B0): immediates < $80 loaded within 10 insns before the call:')
for p in pcs:
    sz, m, x, txt, op, val = ins[p]
    if op == 0x22 and val in (0x88AD30, 0x8898B0, 0x8498B0):
        i = idx[p]
        imms = [(q, ins[q][3]) for q in pcs[max(0, i - 10):i] if ins[q][4] in (0xA9, 0xA2, 0xA0) and ins[q][5] is not None]
        lowb = [(q, t) for q, t in imms if ins[q][5] < 0x80 and ins[q][5] not in (0, 1, 2)]
        P(f'   call {p:06X}: imm {[t for q, t in imms]}' + ('  <-- small immediates' if lowb else ''))
out.close()
print(open('/home/claude/work/out/compat/exhirom_audit.txt').read()[:6000])
