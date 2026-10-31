"""Independent table-driven 65816 disassembler (verify-mk2-compat).
Does not use capstone. HiROM mapping re-implemented here.
Usage: python3 -I d.py <rom> <hexaddr> [count] [m8] [x8]
"""
import sys, struct

ROMS = {'mk2': '/home/claude/work/roms/mk2.sfc',
        'mk3': '/home/claude/work/roms/mk3.sfc',
        'umk3': '/home/claude/work/roms/umk3.sfc'}
_cache = {}
def rom(name):
    if name not in _cache:
        _cache[name] = open(ROMS[name], 'rb').read()
    return _cache[name]

def off(addr, size):
    bank = (addr >> 16) & 0xFF; b = bank & 0x7F; lo = addr & 0xFFFF
    if bank in (0x7E, 0x7F): return None   # WRAM only at $7E/$7F; $FE/$FF are ROM
    if b >= 0x40: o = ((b - 0x40) << 16) | lo
    elif lo >= 0x8000: o = (b << 16) | lo
    else: return None
    return o % size

def w16(d, o): return d[o] | d[o+1] << 8
def w24(d, o): return d[o] | d[o+1] << 8 | d[o+2] << 16

T = """
00 brk i8|01 ora dxi|02 cop i8|03 ora sr|04 tsb d|05 ora d|06 asl d|07 ora dl|08 php -|09 ora im|0a asl A|0b phd -|0c tsb a|0d ora a|0e asl a|0f ora l
10 bpl r|11 ora diy|12 ora di|13 ora sriy|14 trb d|15 ora dx|16 asl dx|17 ora dly|18 clc -|19 ora ay|1a inc A|1b tcs -|1c trb a|1d ora ax|1e asl ax|1f ora lx
20 jsr a|21 and dxi|22 jsl l|23 and sr|24 bit d|25 and d|26 rol d|27 and dl|28 plp -|29 and im|2a rol A|2b pld -|2c bit a|2d and a|2e rol a|2f and l
30 bmi r|31 and diy|32 and di|33 and sriy|34 bit dx|35 and dx|36 rol dx|37 and dly|38 sec -|39 and ay|3a dec A|3b tsc -|3c bit ax|3d and ax|3e rol ax|3f and lx
40 rti -|41 eor dxi|42 wdm i8|43 eor sr|44 mvp bm|45 eor d|46 lsr d|47 eor dl|48 pha -|49 eor im|4a lsr A|4b phk -|4c jmp a|4d eor a|4e lsr a|4f eor l
50 bvc r|51 eor diy|52 eor di|53 eor sriy|54 mvn bm|55 eor dx|56 lsr dx|57 eor dly|58 cli -|59 eor ay|5a phy -|5b tcd -|5c jml l|5d eor ax|5e lsr ax|5f eor lx
60 rts -|61 adc dxi|62 per rl|63 adc sr|64 stz d|65 adc d|66 ror d|67 adc dl|68 pla -|69 adc im|6a ror A|6b rtl -|6c jmp ai|6d adc a|6e ror a|6f adc l
70 bvs r|71 adc diy|72 adc di|73 adc sriy|74 stz dx|75 adc dx|76 ror dx|77 adc dly|78 sei -|79 adc ay|7a ply -|7b tdc -|7c jmp axi|7d adc ax|7e ror ax|7f adc lx
80 bra r|81 sta dxi|82 brl rl|83 sta sr|84 sty d|85 sta d|86 stx d|87 sta dl|88 dey -|89 bit im|8a txa -|8b phb -|8c sty a|8d sta a|8e stx a|8f sta l
90 bcc r|91 sta diy|92 sta di|93 sta sriy|94 sty dx|95 sta dx|96 stx dy|97 sta dly|98 tya -|99 sta ay|9a txs -|9b txy -|9c stz a|9d sta ax|9e stz ax|9f sta lx
a0 ldy ix|a1 lda dxi|a2 ldx ix|a3 lda sr|a4 ldy d|a5 lda d|a6 ldx d|a7 lda dl|a8 tay -|a9 lda im|aa tax -|ab plb -|ac ldy a|ad lda a|ae ldx a|af lda l
b0 bcs r|b1 lda diy|b2 lda di|b3 lda sriy|b4 ldy dx|b5 lda dx|b6 ldx dy|b7 lda dly|b8 clv -|b9 lda ay|ba tsx -|bb tyx -|bc ldy ax|bd lda ax|be ldx ay|bf lda lx
c0 cpy ix|c1 cmp dxi|c2 rep i8|c3 cmp sr|c4 cpy d|c5 cmp d|c6 dec d|c7 cmp dl|c8 iny -|c9 cmp im|ca dex -|cb wai -|cc cpy a|cd cmp a|ce dec a|cf cmp l
d0 bne r|d1 cmp diy|d2 cmp di|d3 cmp sriy|d4 pei di|d5 cmp dx|d6 dec dx|d7 cmp dly|d8 cld -|d9 cmp ay|da phx -|db stp -|dc jml ali|dd cmp ax|de dec ax|df cmp lx
e0 cpx ix|e1 sbc dxi|e2 sep i8|e3 sbc sr|e4 cpx d|e5 sbc d|e6 inc d|e7 sbc dl|e8 inx -|e9 sbc im|ea nop -|eb xba -|ec cpx a|ed sbc a|ee inc a|ef sbc l
f0 beq r|f1 sbc diy|f2 sbc di|f3 sbc sriy|f4 pea a|f5 sbc dx|f6 inc dx|f7 sbc dly|f8 sed -|f9 sbc ay|fa plx -|fb xce -|fc jsr axi|fd sbc ax|fe inc ax|ff sbc lx
"""
OPS = {}
for line in T.strip().splitlines():
    for ent in line.split('|'):
        h, mn, md = ent.split()
        OPS[int(h, 16)] = (mn, md)
assert len(OPS) == 256
FIX = {'-': 0, 'A': 0, 'i8': 1, 'd': 1, 'dx': 1, 'dy': 1, 'di': 1, 'dxi': 1, 'diy': 1, 'dl': 1, 'dly': 1,
       'sr': 1, 'sriy': 1, 'r': 1, 'a': 2, 'ax': 2, 'ay': 2, 'ai': 2, 'axi': 2, 'ali': 2, 'rl': 2, 'bm': 2,
       'l': 3, 'lx': 3}

def one(d, pc, m8, x8):
    o = off(pc, len(d))
    op = d[o]; mn, md = OPS[op]
    if md == 'im': n = 1 if m8 else 2
    elif md == 'ix': n = 1 if x8 else 2
    else: n = FIX[md]
    raw = d[o:o+1+n]
    v = int.from_bytes(raw[1:], 'little') if n else 0
    nxt = (pc & 0xFF0000) | ((pc + 1 + n) & 0xFFFF)
    if md in ('im', 'ix', 'i8'): s = '#$%0*X' % (2*n, v)
    elif md == '-': s = ''
    elif md == 'A': s = 'A'
    elif md == 'd': s = '$%02X' % v
    elif md == 'dx': s = '$%02X,x' % v
    elif md == 'dy': s = '$%02X,y' % v
    elif md == 'di': s = '($%02X)' % v
    elif md == 'dxi': s = '($%02X,x)' % v
    elif md == 'diy': s = '($%02X),y' % v
    elif md == 'dl': s = '[$%02X]' % v
    elif md == 'dly': s = '[$%02X],y' % v
    elif md == 'sr': s = '$%02X,s' % v
    elif md == 'sriy': s = '($%02X,s),y' % v
    elif md == 'a': s = '$%04X' % v
    elif md == 'ax': s = '$%04X,x' % v
    elif md == 'ay': s = '$%04X,y' % v
    elif md == 'ai': s = '($%04X)' % v
    elif md == 'axi': s = '($%04X,x)' % v
    elif md == 'ali': s = '[$%04X]' % v
    elif md == 'l': s = '$%06X' % v
    elif md == 'lx': s = '$%06X,x' % v
    elif md == 'r':
        rel = v - 256 if v >= 128 else v
        s = '$%04X' % ((nxt + rel) & 0xFFFF)
    elif md == 'rl':
        rel = v - 65536 if v >= 32768 else v
        s = '$%04X' % ((nxt + rel) & 0xFFFF)
    elif md == 'bm': s = '$%02X,$%02X' % (raw[2], raw[1])
    return pc, raw, mn, s, nxt, op, v

def dis(name, addr, count=40, m8=False, x8=False, stop=True):
    d = rom(name); out = []; pc = addr
    for _ in range(count):
        pc0, raw, mn, s, nxt, op, v = one(d, pc, m8, x8)
        out.append((pc0, raw.hex(), (mn + ' ' + s).strip()))
        if op == 0xC2:
            if v & 0x20: m8 = False
            if v & 0x10: x8 = False
        elif op == 0xE2:
            if v & 0x20: m8 = True
            if v & 0x10: x8 = True
        pc = nxt
        if stop and op in (0x60, 0x6B, 0x40, 0x4C, 0x5C, 0x6C, 0x7C, 0xDC, 0x80, 0x82):
            break
    return out

def show(name, addr, count=40, m8=False, x8=False, stop=True):
    for a, b, t in dis(name, addr, count, m8, x8, stop):
        print('%02X:%04X  %-10s %s' % (a >> 16, a & 0xFFFF, b, t))

if __name__ == '__main__':
    a = sys.argv
    show(a[1], int(a[2], 16), int(a[3]) if len(a) > 3 else 40,
         len(a) > 4 and a[4] == '1', len(a) > 5 and a[5] == '1',
         stop=not (len(a) > 6 and a[6] == 'nostop'))
