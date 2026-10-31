"""Small table-driven 65816 disassembler (pure python) for the MK2 analysis.
Written because the shared snes.disasm crashes when both M and X are 8-bit
(capstone 5 rejects CS_MODE_MOS65XX_65816 alone).
"""
import sys; sys.path.insert(0,'/home/claude/work/lib'); import snes

# addressing modes: name -> (operand size or special, format)
M = {
 'imp':0,'acc':0,'imm8':1,'immM':'M','immX':'X','dp':1,'dpx':1,'dpy':1,'idp':1,'idx':1,'idy':1,
 'ildp':1,'ildy':1,'abs':2,'absx':2,'absy':2,'long':3,'longx':3,'sr':1,'sry':1,'rel':1,'rell':2,
 'iabs':2,'iabsx':2,'ilabs':2,'mv':2,
}
F = {
 'imp':'','acc':'a','imm8':'#${:02X}','immM':'#${:0{w}X}','immX':'#${:0{w}X}','dp':'${:02X}','dpx':'${:02X},x',
 'dpy':'${:02X},y','idp':'(${:02X})','idx':'(${:02X},x)','idy':'(${:02X}),y','ildp':'[${:02X}]','ildy':'[${:02X}],y',
 'abs':'${:04X}','absx':'${:04X},x','absy':'${:04X},y','long':'${:06X}','longx':'${:06X},x','sr':'${:02X},s',
 'sry':'(${:02X},s),y','iabs':'(${:04X})','iabsx':'(${:04X},x)','ilabs':'[${:04X}]',
}
OPS = {}
def _d(op, mn, mode): OPS[op]=(mn,mode)
_tbl = """
00 brk imm8;01 ora idx;02 cop imm8;03 ora sr;04 tsb dp;05 ora dp;06 asl dp;07 ora ildp;08 php imp;09 ora immM;0A asl acc;0B phd imp;0C tsb abs;0D ora abs;0E asl abs;0F ora long
10 bpl rel;11 ora idy;12 ora idp;13 ora sry;14 trb dp;15 ora dpx;16 asl dpx;17 ora ildy;18 clc imp;19 ora absy;1A inc acc;1B tcs imp;1C trb abs;1D ora absx;1E asl absx;1F ora longx
20 jsr abs;21 and idx;22 jsl long;23 and sr;24 bit dp;25 and dp;26 rol dp;27 and ildp;28 plp imp;29 and immM;2A rol acc;2B pld imp;2C bit abs;2D and abs;2E rol abs;2F and long
30 bmi rel;31 and idy;32 and idp;33 and sry;34 bit dpx;35 and dpx;36 rol dpx;37 and ildy;38 sec imp;39 and absy;3A dec acc;3B tsc imp;3C bit absx;3D and absx;3E rol absx;3F and longx
40 rti imp;41 eor idx;42 wdm imm8;43 eor sr;44 mvp mv;45 eor dp;46 lsr dp;47 eor ildp;48 pha imp;49 eor immM;4A lsr acc;4B phk imp;4C jmp abs;4D eor abs;4E lsr abs;4F eor long
50 bvc rel;51 eor idy;52 eor idp;53 eor sry;54 mvn mv;55 eor dpx;56 lsr dpx;57 eor ildy;58 cli imp;59 eor absy;5A phy imp;5B tcd imp;5C jml long;5D eor absx;5E lsr absx;5F eor longx
60 rts imp;61 adc idx;62 per rell;63 adc sr;64 stz dp;65 adc dp;66 ror dp;67 adc ildp;68 pla imp;69 adc immM;6A ror acc;6B rtl imp;6C jmp iabs;6D adc abs;6E ror abs;6F adc long
70 bvs rel;71 adc idy;72 adc idp;73 adc sry;74 stz dpx;75 adc dpx;76 ror dpx;77 adc ildy;78 sei imp;79 adc absy;7A ply imp;7B tdc imp;7C jmp iabsx;7D adc absx;7E ror absx;7F adc longx
80 bra rel;81 sta idx;82 brl rell;83 sta sr;84 sty dp;85 sta dp;86 stx dp;87 sta ildp;88 dey imp;89 bit immM;8A txa imp;8B phb imp;8C sty abs;8D sta abs;8E stx abs;8F sta long
90 bcc rel;91 sta idy;92 sta idp;93 sta sry;94 sty dpx;95 sta dpx;96 stx dpy;97 sta ildy;98 tya imp;99 sta absy;9A txs imp;9B txy imp;9C stz abs;9D sta absx;9E stz absx;9F sta longx
A0 ldy immX;A1 lda idx;A2 ldx immX;A3 lda sr;A4 ldy dp;A5 lda dp;A6 ldx dp;A7 lda ildp;A8 tay imp;A9 lda immM;AA tax imp;AB plb imp;AC ldy abs;AD lda abs;AE ldx abs;AF lda long
B0 bcs rel;B1 lda idy;B2 lda idp;B3 lda sry;B4 ldy dpx;B5 lda dpx;B6 ldx dpy;B7 lda ildy;B8 clv imp;B9 lda absy;BA tsx imp;BB tyx imp;BC ldy absx;BD lda absx;BE ldx absy;BF lda longx
C0 cpy immX;C1 cmp idx;C2 rep imm8;C3 cmp sr;C4 cpy dp;C5 cmp dp;C6 dec dp;C7 cmp ildp;C8 iny imp;C9 cmp immM;CA dex imp;CB wai imp;CC cpy abs;CD cmp abs;CE dec abs;CF cmp long
D0 bne rel;D1 cmp idy;D2 cmp idp;D3 cmp sry;D4 pei dp;D5 cmp dpx;D6 dec dpx;D7 cmp ildy;D8 cld imp;D9 cmp absy;DA phx imp;DB stp imp;DC jml ilabs;DD cmp absx;DE dec absx;DF cmp longx
E0 cpx immX;E1 sbc idx;E2 sep imm8;E3 sbc sr;E4 cpx dp;E5 sbc dp;E6 inc dp;E7 sbc ildp;E8 inx imp;E9 sbc immM;EA nop imp;EB xba imp;EC cpx abs;ED sbc abs;EE inc abs;EF sbc long
F0 beq rel;F1 sbc idy;F2 sbc idp;F3 sbc sry;F4 pea abs;F5 sbc dpx;F6 inc dpx;F7 sbc ildy;F8 sed imp;F9 sbc absy;FA plx imp;FB xce imp;FC jsr iabsx;FD sbc absx;FE inc absx;FF sbc longx
"""
for line in _tbl.strip().splitlines():
    for ent in line.split(';'):
        op, mn, mode = ent.split()
        _d(int(op,16), mn, mode)

def dis1(rom, pc, m16, x16):
    off = snes.to_off(pc, len(rom))
    if off is None: return None
    op = rom[off]; mn, mode = OPS[op]
    sz = M[mode]
    if sz == 'M': sz = 2 if m16 else 1
    if sz == 'X': sz = 2 if x16 else 1
    b = rom[off:off+1+sz]
    v = int.from_bytes(b[1:], 'little') if sz else 0
    if mode == 'rel':
        tgt = (pc & 0xFF0000) | ((pc + 2 + (v - 256 if v > 127 else v)) & 0xFFFF)
        txt = f'{mn} ${tgt & 0xFFFF:04X}'
    elif mode == 'rell':
        tgt = (pc & 0xFF0000) | ((pc + 3 + (v - 65536 if v > 32767 else v)) & 0xFFFF)
        txt = f'{mn} ${tgt & 0xFFFF:04X}'
    elif mode == 'mv':
        txt = f'{mn} ${b[2]:02X},${b[1]:02X}'
    elif mode in ('immM', 'immX'):
        txt = f'{mn} #${v:0{2*sz}X}'
    else:
        txt = (mn + ' ' + F[mode].format(v)).strip()
    return op, b, txt, 1 + sz

def disasm(rom, addr, count=60, m16=True, x16=True, stop=True):
    out = []; pc = addr
    for _ in range(count):
        d = dis1(rom, pc, m16, x16)
        if d is None: break
        op, b, txt, n = d
        out.append((pc, b.hex(), txt))
        if op == 0xC2:
            if b[1] & 0x20: m16 = True
            if b[1] & 0x10: x16 = True
        elif op == 0xE2:
            if b[1] & 0x20: m16 = False
            if b[1] & 0x10: x16 = False
        pc = (pc & 0xFF0000) | ((pc + n) & 0xFFFF)
        if stop and op in (0x60, 0x6B, 0x40, 0x4C, 0x5C, 0x80, 0x82, 0xDC, 0x6C, 0x7C): break
    return out

def show(rom, addr, count=60, m16=True, x16=True, stop=True, file=None):
    for a, b, t in disasm(rom, addr, count, m16, x16, stop):
        print(f'{a:06X}  {b:<10} {t}', file=file)

if __name__ == '__main__':
    rom = snes.load(sys.argv[3] if len(sys.argv) > 3 else 'mk2')
    a = int(sys.argv[1], 16); n = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    m = x = True
    for f in sys.argv[4:]:
        if f == 'm8': m = False
        if f == 'x8': x = False
    show(rom, a, n, m, x, stop=False)
