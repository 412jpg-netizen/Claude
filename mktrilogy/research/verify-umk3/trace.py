"""Independent recursive-descent tracer over UMK3 code (banks $80-$88 + bank $00 stubs).
Seeds: vectors; process-create patterns (LDA #addr / LDX #bank / JSL ...); PEA/PEA call-frame pairs.
Tracks M/X via REP/SEP; PLP resets to M16/X16 (the game's default). Output: traced instruction set
and every long operand seen, pickled to out/verify-umk3/trace_v.pkl."""
import sys, re, pickle; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v

r = v.load('umk3')
CODE_BANKS = set(range(0x80, 0x89)) | {0x00}


def is_code_addr(a):
    b = a >> 16
    return b in CODE_BANKS and (a & 0xFFFF) >= 0x8000


def seeds():
    s = set()
    for vec in range(0xFFE4, 0x10000, 2):
        w = r[vec] | r[vec + 1] << 8
        if w >= 0x8000: s.add((w, True, True))
    # LDA #lo ; LDX #bank ; JSL x   (process create)
    for m in re.finditer(rb'\xa9(..)\xa2(.)\x00\x22', r, re.S):
        a = int.from_bytes(m.group(1), 'little') | m.group(2)[0] << 16
        if is_code_addr(a) and (m.start() >> 16) < 9: s.add((a, True, True))
    # PEA $bbhh ; PEA $ll00 -> return address bb:hhll, resumes at +1
    for m in re.finditer(rb'\xf4(.)(.)\xf4\x00(.)', r, re.S):
        bb = m.group(2)[0]; a = bb << 16 | m.group(1)[0] << 8 | m.group(3)[0]
        a = (a & 0xFF0000) | ((a + 1) & 0xFFFF)
        if is_code_addr(a) and (m.start() >> 16) < 9: s.add((a, True, True))
    return s


def trace(extra=()):
    seen = {}  # addr -> (m,x,len,text,op,val,mode)
    work = list(seeds()) + list(extra)
    longs = []
    while work:
        pc, m, x = work.pop()
        while True:
            if not is_code_addr(pc): break
            if pc in seen: break
            n, t, op, val, md = v.dis1(r, pc, m, x)
            seen[pc] = (m, x, n, t, op, val, md)
            if md in ('long', 'longx'):
                longs.append((pc, t, val))
            nxt = (pc & 0xFF0000) | ((pc + n) & 0xFFFF)
            if op == 0xC2:
                if val & 0x20: m = True
                if val & 0x10: x = True
            elif op == 0xE2:
                if val & 0x20: m = False
                if val & 0x10: x = False
            elif op == 0x28:  # PLP
                m, x = True, True
            if op in (0x20, 0x22):  # JSR / JSL
                tgt = (pc & 0xFF0000 | val) if op == 0x20 else val
                if is_code_addr(tgt): work.append((tgt, m, x))
            if md in ('rel', 'rell'):
                if is_code_addr(val): work.append((val, m, x))
            if op in (0x4C, 0x5C):  # JMP abs / JML
                tgt = (pc & 0xFF0000 | val) if op == 0x4C else val
                if is_code_addr(tgt): work.append((tgt, m, x))
                break
            if op in (0x60, 0x6B, 0x40, 0x80, 0x82, 0x6C, 0x7C, 0xDC, 0xFC, 0xDB, 0x00):
                if op == 0xFC:  # JSR (abs,X) returns
                    pc = nxt; continue
                break
            pc = nxt
    return seen, longs


if __name__ == '__main__':
    seen, longs = trace()
    pickle.dump((seen, longs), open('/home/claude/work/out/verify-umk3/trace_v.pkl', 'wb'))
    print('traced instructions:', len(seen), ' long operands:', len(longs))
