"""MK2 animation tables & scripts (interpreter $83:F28E).
Per fighter: common table ($85:C49E -> <set header>+$10) and specific table ($85:C4E2), 16-bit
pointers into the same bank. Script words:
  0000            end of animation (interpreter returns Z=1)
  0001..FFF5      frame word = set<<9 | frame (1-based) -> stored to $4C3C,x by $83:EF0C; one frame per call
  FFFF a          jump to a (same bank)
  FFFE            jsl $83:F1E4, continue
  FFFD a          X=a, Y=0, jsl $83:F4D8, continue
  FFFC a b        X=a, Y=b, jsl $83:F4D8, continue
  FFFB f          show frame f and continue immediately (C=1, caller does not wait)
  FFFA lo bank    $1900/$1902 = 24-bit address, jsl $85:DF88 (call), continue
  FFF9 a          jsl $85:E0C5 with A=a, continue
  FFF8 b a        (byte b) jsl $84:A05C; if C set jump to a, else skip a
  FFF7            jsl $83:F1F5, continue
Frame timing is NOT in the script: callers pass A = delay<<8 | anim ($83:F347 common, $83:F356 specific),
and $83:F39C sleeps `delay` ticks ($85:DDF9) after each frame word."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g, snes

def parse_script(bank, lo, limit=400):
    a = bank << 16 | lo; p = a; items = []; frames = []
    for _ in range(limit):
        if snes.to_off(p, g.N) is None or (p & 0xFFFF) < 0x8000: items.append(('bad',)); break
        w = g.w16(p); p += 2
        if w == 0: items.append(('end',)); break
        if w < 0xFFF6: items.append(('frame', w)); frames.append(w); continue
        if w == 0xFFFF:
            t = g.w16(p); p += 2; items.append(('jump', t)); break
        if w == 0xFFFE: items.append(('call_F1E4',)); continue
        if w == 0xFFFD: items.append(('move', g.w16(p))); p += 2; continue
        if w == 0xFFFC: items.append(('move2', g.w16(p), g.w16(p+2))); p += 4; continue
        if w == 0xFFFB: f = g.w16(p); p += 2; items.append(('frame_nowait', f)); frames.append(f); continue
        if w == 0xFFFA: items.append(('calllong', g.w16(p+2) << 16 | g.w16(p))); p += 4; continue
        if w == 0xFFF9: items.append(('E0C5', g.w16(p))); p += 2; continue
        if w == 0xFFF8:
            b = g.b8(p); t = g.w16(p+1); p += 3; items.append(('cond', b, t)); continue
        if w == 0xFFF7: items.append(('call_F1F5',)); continue
        items.append(('??', w)); break
    return items, frames, (a, p)

def fighter_anims(fid):
    c, s = g.anim_tables(fid)
    bank = c >> 16
    # table extents: common table runs up to the lowest pointer target or the specific table
    def tbl(addr):
        ptrs = []; p = addr
        first_script = 0xFFFF
        while (p & 0xFFFF) < first_script:
            v = g.w16(p)
            if v < 0x8000: break
            ptrs.append(v); first_script = min(first_script, v); p += 2
            if len(ptrs) > 120: break
        return ptrs
    return c, s, tbl(c), tbl(s)

if __name__ == '__main__':
    for fid in range(17):
        c, s, cp, sp = fighter_anims(fid)
        print('%-12s common %06X n=%d  specific %06X n=%d' % (g.NAMES[fid], c, len(cp), s, len(sp)))

def set_block(fids, ncommon):
    """Union of header + tables + all scripts reachable for the fighters sharing one sprite set."""
    regs = []; frames = set(); nscripts = 0
    hdr = g.header(g.FIGHTER_SET[fids[0]])['addr']
    regs.append((hdr, hdr+16))
    for fid in fids:
        c, s, cp, sp = fighter_anims(fid)
        bank = c >> 16
        regs.append((c, c + 2*ncommon))
        ns = len(sp) if s != c else 0
        if ns: regs.append((s, s + 2*ns))
        todo = list(cp[:ncommon]) + (list(sp) if ns else [])
        seen = set()
        while todo:
            lo = todo.pop()
            if lo in seen or lo < 0x8000 or lo > 0xFFF0: continue
            seen.add(lo); nscripts += 1
            items, fr, (a, e) = parse_script(bank, lo)
            regs.append((a, e)); frames.update(fr)
            for it in items:
                if it[0] == 'jump': todo.append(it[1])
                if it[0] == 'cond': todo.append(it[2])
    regs.sort(); merged = []
    for a, b in regs:
        if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    return merged, frames, nscripts

GROUPS = [([0],66),([1],66),([2],66),([3],66),([4,5,16],66),([6],66),([7],66),([8,9,10,14,15],66),([11],66),([12],24),([13],26)]
if __name__ == '__main__':
    print()
    for fids, nc in GROUPS:
        m, fr, ns = set_block(fids, nc)
        sets = sorted(set(f >> 9 for f in fr))
        tot = sum(b-a for a, b in m)
        print('%-28s scripts=%3d  frames referenced=%3d (sets %s)  bytes=%5d  span %06X-%06X  pieces=%d' % (
            '/'.join(g.NAMES[f] for f in fids)[:28], ns, len(fr), sets, tot, m[0][0], m[-1][1], len(m)))
