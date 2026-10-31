"""Independent helper for verify-umk3. Own 65816 disassembler (no capstone),
fixed HiROM mapping (banks $FE/$FF are ROM), xref scanning, palette helpers.
Usage: import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
"""
import struct

ROMS = {
    'mk2': '/home/claude/work/roms/mk2.sfc',
    'mk3': '/home/claude/work/roms/mk3.sfc',
    'umk3': '/home/claude/work/roms/umk3.sfc',
}
_cache = {}


def load(name='umk3'):
    if name not in _cache:
        _cache[name] = open(ROMS[name], 'rb').read()
    return _cache[name]


def off(addr, size=0x400000):
    """HiROM SNES address -> file offset. Only $7E/$7F are WRAM."""
    bank, lo = (addr >> 16) & 0xFF, addr & 0xFFFF
    if bank in (0x7E, 0x7F):
        return None
    b = bank & 0x7F
    if b >= 0x40:
        o = ((b - 0x40) << 16) | lo
    elif lo >= 0x8000:
        o = (b << 16) | lo
    else:
        return None
    return o % size


def u8(r, a):
    return r[off(a, len(r))]


def u16(r, a):
    o = off(a, len(r))
    return r[o] | r[o + 1] << 8


def u24(r, a):
    o = off(a, len(r))
    return r[o] | r[o + 1] << 8 | r[o + 2] << 16


def bytes_at(r, a, n):
    o = off(a, len(r))
    return r[o:o + n]


# ---- 65816 opcode table: mnemonic, mode ----
# modes: imp, acc, immM, immX, imm8, dp, dpx, dpy, idp, idpx, idpy, ildp, ildpy,
#        abs, absx, absy, long, longx, iabs, iabsx, ilabs, sr, isry, rel, rell, bm
_T = """
00 BRK imm8|01 ORA idpx|02 COP imm8|03 ORA sr|04 TSB dp|05 ORA dp|06 ASL dp|07 ORA ildp|
08 PHP imp|09 ORA immM|0A ASL acc|0B PHD imp|0C TSB abs|0D ORA abs|0E ASL abs|0F ORA long|
10 BPL rel|11 ORA idpy|12 ORA idp|13 ORA isry|14 TRB dp|15 ORA dpx|16 ASL dpx|17 ORA ildpy|
18 CLC imp|19 ORA absy|1A INC acc|1B TCS imp|1C TRB abs|1D ORA absx|1E ASL absx|1F ORA longx|
20 JSR abs|21 AND idpx|22 JSL long|23 AND sr|24 BIT dp|25 AND dp|26 ROL dp|27 AND ildp|
28 PLP imp|29 AND immM|2A ROL acc|2B PLD imp|2C BIT abs|2D AND abs|2E ROL abs|2F AND long|
30 BMI rel|31 AND idpy|32 AND idp|33 AND isry|34 BIT dpx|35 AND dpx|36 ROL dpx|37 AND ildpy|
38 SEC imp|39 AND absy|3A DEC acc|3B TSC imp|3C BIT absx|3D AND absx|3E ROL absx|3F AND longx|
40 RTI imp|41 EOR idpx|42 WDM imm8|43 EOR sr|44 MVP bm|45 EOR dp|46 LSR dp|47 EOR ildp|
48 PHA imp|49 EOR immM|4A LSR acc|4B PHK imp|4C JMP abs|4D EOR abs|4E LSR abs|4F EOR long|
50 BVC rel|51 EOR idpy|52 EOR idp|53 EOR isry|54 MVN bm|55 EOR dpx|56 LSR dpx|57 EOR ildpy|
58 CLI imp|59 EOR absy|5A PHY imp|5B TCD imp|5C JML long|5D EOR absx|5E LSR absx|5F EOR longx|
60 RTS imp|61 ADC idpx|62 PER rell|63 ADC sr|64 STZ dp|65 ADC dp|66 ROR dp|67 ADC ildp|
68 PLA imp|69 ADC immM|6A ROR acc|6B RTL imp|6C JMP iabs|6D ADC abs|6E ROR abs|6F ADC long|
70 BVS rel|71 ADC idpy|72 ADC idp|73 ADC isry|74 STZ dpx|75 ADC dpx|76 ROR dpx|77 ADC ildpy|
78 SEI imp|79 ADC absy|7A PLY imp|7B TDC imp|7C JMP iabsx|7D ADC absx|7E ROR absx|7F ADC longx|
80 BRA rel|81 STA idpx|82 BRL rell|83 STA sr|84 STY dp|85 STA dp|86 STX dp|87 STA ildp|
88 DEY imp|89 BIT immM|8A TXA imp|8B PHB imp|8C STY abs|8D STA abs|8E STX abs|8F STA long|
90 BCC rel|91 STA idpy|92 STA idp|93 STA isry|94 STY dpx|95 STA dpx|96 STX dpy|97 STA ildpy|
98 TYA imp|99 STA absy|9A TXS imp|9B TXY imp|9C STZ abs|9D STA absx|9E STZ absx|9F STA longx|
A0 LDY immX|A1 LDA idpx|A2 LDX immX|A3 LDA sr|A4 LDY dp|A5 LDA dp|A6 LDX dp|A7 LDA ildp|
A8 TAY imp|A9 LDA immM|AA TAX imp|AB PLB imp|AC LDY abs|AD LDA abs|AE LDX abs|AF LDA long|
B0 BCS rel|B1 LDA idpy|B2 LDA idp|B3 LDA isry|B4 LDY dpx|B5 LDA dpx|B6 LDX dpy|B7 LDA ildpy|
B8 CLV imp|B9 LDA absy|BA TSX imp|BB TYX imp|BC LDY absx|BD LDA absx|BE LDX absy|BF LDA longx|
C0 CPY immX|C1 CMP idpx|C2 REP imm8|C3 CMP sr|C4 CPY dp|C5 CMP dp|C6 DEC dp|C7 CMP ildp|
C8 INY imp|C9 CMP immM|CA DEX imp|CB WAI imp|CC CPY abs|CD CMP abs|CE DEC abs|CF CMP long|
D0 BNE rel|D1 CMP idpy|D2 CMP idp|D3 CMP isry|D4 PEI idp|D5 CMP dpx|D6 DEC dpx|D7 CMP ildpy|
D8 CLD imp|D9 CMP absy|DA PHX imp|DB STP imp|DC JML ilabs|DD CMP absx|DE DEC absx|DF CMP longx|
E0 CPX immX|E1 SBC idpx|E2 SEP imm8|E3 SBC sr|E4 CPX dp|E5 SBC dp|E6 INC dp|E7 SBC ildp|
E8 INX imp|E9 SBC immM|EA NOP imp|EB XBA imp|EC CPX abs|ED SBC abs|EE INC abs|EF SBC long|
F0 BEQ rel|F1 SBC idpy|F2 SBC idp|F3 SBC isry|F4 PEA abs|F5 SBC dpx|F6 INC dpx|F7 SBC ildpy|
F8 SED imp|F9 SBC absy|FA PLX imp|FB XCE imp|FC JSR iabsx|FD SBC absx|FE INC absx|FF SBC longx
"""
OPS = {}
for ent in _T.replace('\n', '').split('|'):
    ent = ent.strip()
    if not ent:
        continue
    h, mn, md = ent.split()
    OPS[int(h, 16)] = (mn, md)
assert len(OPS) == 256, len(OPS)

_LEN = {'imp': 0, 'acc': 0, 'imm8': 1, 'dp': 1, 'dpx': 1, 'dpy': 1, 'idp': 1, 'idpx': 1,
        'idpy': 1, 'ildp': 1, 'ildpy': 1, 'abs': 2, 'absx': 2, 'absy': 2, 'long': 3,
        'longx': 3, 'iabs': 2, 'iabsx': 2, 'ilabs': 2, 'sr': 1, 'isry': 1, 'rel': 1,
        'rell': 2, 'bm': 2}


def ins_len(op, m16, x16):
    mn, md = OPS[op]
    if md == 'immM':
        return 1 + (2 if m16 else 1)
    if md == 'immX':
        return 1 + (2 if x16 else 1)
    return 1 + _LEN[md]


def dis1(r, pc, m16=True, x16=True):
    """Disassemble one instruction. Returns (len, text, op, operand_value, mode)."""
    o = off(pc, len(r))
    op = r[o]
    mn, md = OPS[op]
    n = ins_len(op, m16, x16)
    b = r[o + 1:o + n]
    v = int.from_bytes(b, 'little') if b else None
    if md in ('imp',):
        t = mn
    elif md == 'acc':
        t = mn + ' A'
    elif md in ('immM', 'immX', 'imm8'):
        t = f'{mn} #${v:0{2*(n-1)}X}'
    elif md == 'dp':
        t = f'{mn} ${v:02X}'
    elif md == 'dpx':
        t = f'{mn} ${v:02X},X'
    elif md == 'dpy':
        t = f'{mn} ${v:02X},Y'
    elif md == 'idp':
        t = f'{mn} (${v:02X})'
    elif md == 'idpx':
        t = f'{mn} (${v:02X},X)'
    elif md == 'idpy':
        t = f'{mn} (${v:02X}),Y'
    elif md == 'ildp':
        t = f'{mn} [${v:02X}]'
    elif md == 'ildpy':
        t = f'{mn} [${v:02X}],Y'
    elif md == 'abs':
        t = f'{mn} ${v:04X}'
    elif md == 'absx':
        t = f'{mn} ${v:04X},X'
    elif md == 'absy':
        t = f'{mn} ${v:04X},Y'
    elif md == 'long':
        t = f'{mn} ${v:06X}'
    elif md == 'longx':
        t = f'{mn} ${v:06X},X'
    elif md == 'iabs':
        t = f'{mn} (${v:04X})'
    elif md == 'iabsx':
        t = f'{mn} (${v:04X},X)'
    elif md == 'ilabs':
        t = f'{mn} [${v:04X}]'
    elif md == 'sr':
        t = f'{mn} ${v:02X},S'
    elif md == 'isry':
        t = f'{mn} (${v:02X},S),Y'
    elif md == 'rel':
        tgt = (pc & 0xFF0000) | ((pc + 2 + (v - 256 if v > 127 else v)) & 0xFFFF)
        v = tgt
        t = f'{mn} ${tgt:06X}'
    elif md == 'rell':
        tgt = (pc & 0xFF0000) | ((pc + 3 + (v - 65536 if v > 32767 else v)) & 0xFFFF)
        v = tgt
        t = f'{mn} ${tgt:06X}'
    elif md == 'bm':
        t = f'{mn} ${b[1]:02X},${b[0]:02X}'
    return n, t, op, v, md


def dis(r, pc, count=40, m16=True, x16=True, stop=True):
    out = []
    for _ in range(count):
        n, t, op, v, md = dis1(r, pc, m16, x16)
        o = off(pc, len(r))
        out.append((pc, r[o:o + n].hex(), t, m16, x16))
        if op == 0xC2:
            if v & 0x20: m16 = True
            if v & 0x10: x16 = True
        elif op == 0xE2:
            if v & 0x20: m16 = False
            if v & 0x10: x16 = False
        pc = (pc & 0xFF0000) | ((pc + n) & 0xFFFF)
        if stop and op in (0x60, 0x6B, 0x40, 0x5C, 0x4C, 0x80, 0x82, 0xDC, 0x7C, 0x6C):
            break
    return out


def show(r, pc, count=40, m16=True, x16=True, stop=True, file=None):
    lines = []
    for a, h, t, m, x in dis(r, pc, count, m16, x16, stop):
        lines.append(f'{a:06X}  {h:<10} {t:<24} ; {"M16" if m else "M8 "} {"X16" if x else "X8"}')
    s = '\n'.join(lines)
    if file:
        file.write(s + '\n')
    else:
        print(s)
    return s


def bgr(w):
    r, g, b = w & 31, (w >> 5) & 31, (w >> 10) & 31
    return (r << 3 | r >> 2, g << 3 | g >> 2, b << 3 | b >> 2)


def pal(r, a, n=16):
    return [bgr(u16(r, a + 2 * i)) for i in range(n)]


def find_all(r, pat):
    hits = []
    i = r.find(pat)
    while i != -1:
        hits.append(i)
        i = r.find(pat, i + 1)
    return hits


def long_xrefs(r, addr):
    """Raw byte-pattern search for long-addressing opcodes with operand == addr (any of
    $xx/$xx|$80 bank forms). Returns list of (file_off, opcode, operand)."""
    res = []
    bank = (addr >> 16) & 0xFF
    banks = {bank, bank ^ 0x80}
    for b in banks:
        tgt = (addr & 0xFFFF) | (b << 16)
        pat = tgt.to_bytes(3, 'little')
        for i in find_all(r, pat):
            if i > 0 and OPS[r[i - 1]][1] in ('long', 'longx'):
                res.append((i - 1, r[i - 1], tgt))
    return sorted(res)


def abs_xrefs(r, lo16, banks=None):
    res = []
    pat = (lo16 & 0xFFFF).to_bytes(2, 'little')
    for i in find_all(r, pat):
        if i > 0 and OPS[r[i - 1]][1] in ('abs', 'absx', 'absy', 'iabs', 'iabsx', 'ilabs'):
            if banks is None or (i >> 16) in banks:
                res.append((i - 1, r[i - 1]))
    return res
