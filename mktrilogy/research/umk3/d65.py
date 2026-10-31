"""Self-contained 65816 disassembler (no capstone) with M/X width tracking.
Used for the UMK3 map because the shared lib's capstone wrapper cannot build
the 8-bit/8-bit mode (CS_MODE_MOS65XX_65816 alone raises CS_ERR_MODE).

API:
  dis1(rom, pc, m16, x16) -> dict(pc, size, op, mn, mode, val, text, bytes)
  lst(rom, pc, n, m16, x16, stop=True) -> list of dicts (linear)
  show(rom, pc, n=40, m16=True, x16=True, stop=True)
"""
import sys
sys.path.insert(0, '/home/claude/work/lib')
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u
import snes

ALU = ['ORA', 'AND', 'EOR', 'ADC', 'STA', 'LDA', 'CMP', 'SBC']
# column -> mode for ALU group (low 5 bits)
ALU_MODES = {0x01: 'dpxi', 0x03: 'sr', 0x05: 'dp', 0x07: 'dpil', 0x09: 'immm', 0x0D: 'abs', 0x0F: 'long',
             0x11: 'dpiy', 0x12: 'dpi', 0x13: 'sriy', 0x15: 'dpx', 0x17: 'dpily', 0x19: 'absy',
             0x1D: 'absx', 0x1F: 'longx'}
OPS = {}
for i, mn in enumerate(ALU):
    for col, mode in ALU_MODES.items():
        OPS[(i << 5) | col] = (mn, mode)
OPS[0x89] = ('BIT', 'immm')  # STA # slot
other = {
    0x00: ('BRK', 'imm8'), 0x02: ('COP', 'imm8'), 0x04: ('TSB', 'dp'), 0x06: ('ASL', 'dp'), 0x08: ('PHP', 'imp'),
    0x0A: ('ASL', 'acc'), 0x0B: ('PHD', 'imp'), 0x0C: ('TSB', 'abs'), 0x0E: ('ASL', 'abs'), 0x10: ('BPL', 'rel'),
    0x14: ('TRB', 'dp'), 0x16: ('ASL', 'dpx'), 0x18: ('CLC', 'imp'), 0x1A: ('INC', 'acc'), 0x1B: ('TCS', 'imp'),
    0x1C: ('TRB', 'abs'), 0x1E: ('ASL', 'absx'), 0x20: ('JSR', 'abs'), 0x22: ('JSL', 'long'), 0x24: ('BIT', 'dp'),
    0x26: ('ROL', 'dp'), 0x28: ('PLP', 'imp'), 0x2A: ('ROL', 'acc'), 0x2B: ('PLD', 'imp'), 0x2C: ('BIT', 'abs'),
    0x2E: ('ROL', 'abs'), 0x30: ('BMI', 'rel'), 0x34: ('BIT', 'dpx'), 0x36: ('ROL', 'dpx'), 0x38: ('SEC', 'imp'),
    0x3A: ('DEC', 'acc'), 0x3B: ('TSC', 'imp'), 0x3C: ('BIT', 'absx'), 0x3E: ('ROL', 'absx'), 0x40: ('RTI', 'imp'),
    0x42: ('WDM', 'imm8'), 0x44: ('MVP', 'blk'), 0x46: ('LSR', 'dp'), 0x48: ('PHA', 'imp'), 0x4A: ('LSR', 'acc'),
    0x4B: ('PHK', 'imp'), 0x4C: ('JMP', 'abs'), 0x4E: ('LSR', 'abs'), 0x50: ('BVC', 'rel'), 0x54: ('MVN', 'blk'),
    0x56: ('LSR', 'dpx'), 0x58: ('CLI', 'imp'), 0x5A: ('PHY', 'imp'), 0x5B: ('TCD', 'imp'), 0x5C: ('JML', 'long'),
    0x5E: ('LSR', 'absx'), 0x60: ('RTS', 'imp'), 0x62: ('PER', 'rell'), 0x64: ('STZ', 'dp'), 0x66: ('ROR', 'dp'),
    0x68: ('PLA', 'imp'), 0x6A: ('ROR', 'acc'), 0x6B: ('RTL', 'imp'), 0x6C: ('JMP', 'absi'), 0x6E: ('ROR', 'abs'),
    0x70: ('BVS', 'rel'), 0x74: ('STZ', 'dpx'), 0x76: ('ROR', 'dpx'), 0x78: ('SEI', 'imp'), 0x7A: ('PLY', 'imp'),
    0x7B: ('TDC', 'imp'), 0x7C: ('JMP', 'absxi'), 0x7E: ('ROR', 'absx'), 0x80: ('BRA', 'rel'), 0x82: ('BRL', 'rell'),
    0x84: ('STY', 'dp'), 0x86: ('STX', 'dp'), 0x88: ('DEY', 'imp'), 0x8A: ('TXA', 'imp'), 0x8B: ('PHB', 'imp'),
    0x8C: ('STY', 'abs'), 0x8E: ('STX', 'abs'), 0x90: ('BCC', 'rel'), 0x94: ('STY', 'dpx'), 0x96: ('STX', 'dpy'),
    0x98: ('TYA', 'imp'), 0x9A: ('TXS', 'imp'), 0x9B: ('TXY', 'imp'), 0x9C: ('STZ', 'abs'), 0x9E: ('STZ', 'absx'),
    0xA0: ('LDY', 'immx'), 0xA2: ('LDX', 'immx'), 0xA4: ('LDY', 'dp'), 0xA6: ('LDX', 'dp'), 0xA8: ('TAY', 'imp'),
    0xAA: ('TAX', 'imp'), 0xAB: ('PLB', 'imp'), 0xAC: ('LDY', 'abs'), 0xAE: ('LDX', 'abs'), 0xB0: ('BCS', 'rel'),
    0xB4: ('LDY', 'dpx'), 0xB6: ('LDX', 'dpy'), 0xB8: ('CLV', 'imp'), 0xBA: ('TSX', 'imp'), 0xBB: ('TYX', 'imp'),
    0xBC: ('LDY', 'absx'), 0xBE: ('LDX', 'absy'), 0xC0: ('CPY', 'immx'), 0xC2: ('REP', 'imm8'), 0xC4: ('CPY', 'dp'),
    0xC6: ('DEC', 'dp'), 0xC8: ('INY', 'imp'), 0xCA: ('DEX', 'imp'), 0xCB: ('WAI', 'imp'), 0xCC: ('CPY', 'abs'),
    0xCE: ('DEC', 'abs'), 0xD0: ('BNE', 'rel'), 0xD4: ('PEI', 'dpi'), 0xD6: ('DEC', 'dpx'), 0xD8: ('CLD', 'imp'),
    0xDA: ('PHX', 'imp'), 0xDB: ('STP', 'imp'), 0xDC: ('JML', 'absil'), 0xDE: ('DEC', 'absx'), 0xE0: ('CPX', 'immx'),
    0xE2: ('SEP', 'imm8'), 0xE4: ('CPX', 'dp'), 0xE6: ('INC', 'dp'), 0xE8: ('INX', 'imp'), 0xEA: ('NOP', 'imp'),
    0xEB: ('XBA', 'imp'), 0xEC: ('CPX', 'abs'), 0xEE: ('INC', 'abs'), 0xF0: ('BEQ', 'rel'), 0xF4: ('PEA', 'abs'),
    0xF6: ('INC', 'dpx'), 0xF8: ('SED', 'imp'), 0xFA: ('PLX', 'imp'), 0xFB: ('XCE', 'imp'), 0xFC: ('JSR', 'absxi'),
    0xFE: ('INC', 'absx'),
}
OPS.update(other)
assert len(OPS) == 256, len(OPS)

SIZES = {'imp': 1, 'acc': 1, 'imm8': 2, 'dp': 2, 'dpx': 2, 'dpy': 2, 'dpi': 2, 'dpxi': 2, 'dpiy': 2, 'dpil': 2,
         'dpily': 2, 'sr': 2, 'sriy': 2, 'rel': 2, 'abs': 3, 'absx': 3, 'absy': 3, 'absi': 3, 'absxi': 3,
         'absil': 3, 'rell': 3, 'blk': 3, 'long': 4, 'longx': 4}
FMT = {'imp': '', 'acc': 'A', 'imm8': '#${:02X}', 'dp': '${:02X}', 'dpx': '${:02X},X', 'dpy': '${:02X},Y',
       'dpi': '(${:02X})', 'dpxi': '(${:02X},X)', 'dpiy': '(${:02X}),Y', 'dpil': '[${:02X}]', 'dpily': '[${:02X}],Y',
       'sr': '${:02X},S', 'sriy': '(${:02X},S),Y', 'abs': '${:04X}', 'absx': '${:04X},X', 'absy': '${:04X},Y',
       'absi': '(${:04X})', 'absxi': '(${:04X},X)', 'absil': '[${:04X}]', 'long': '${:06X}', 'longx': '${:06X},X'}


def dis1(rom, pc, m16=True, x16=True):
    off = snes.to_off(pc, len(rom))
    if off is None:
        return None
    op = rom[off]
    mn, mode = OPS[op]
    if mode == 'immm':
        size = 3 if m16 else 2
    elif mode == 'immx':
        size = 3 if x16 else 2
    else:
        size = SIZES[mode]
    b = rom[off:off + size]
    val = None
    if size > 1:
        val = int.from_bytes(b[1:], 'little')
    nxt = (pc & 0xFF0000) | ((pc + size) & 0xFFFF)
    if mode == 'rel':
        d = val - 256 if val >= 128 else val
        val = (pc & 0xFF0000) | ((pc + 2 + d) & 0xFFFF)
        text = f'{mn} ${val & 0xFFFF:04X}'
    elif mode == 'rell':
        d = val - 65536 if val >= 32768 else val
        val = (pc & 0xFF0000) | ((pc + 3 + d) & 0xFFFF)
        text = f'{mn} ${val & 0xFFFF:04X}'
    elif mode in ('immm', 'immx'):
        text = f'{mn} #${val:0{(size - 1) * 2}X}'
    elif mode == 'blk':
        text = f'{mn} ${b[2]:02X},${b[1]:02X}'
    else:
        text = (mn + ' ' + FMT[mode].format(val) if FMT[mode] else mn).strip()
    return dict(pc=pc, size=size, op=op, mn=mn, mode=mode, val=val, text=text, bytes=b, next=nxt)


def lst(rom, pc, n=40, m16=True, x16=True, stop=True):
    out = []
    for _ in range(n):
        d = dis1(rom, pc, m16, x16)
        if d is None:
            break
        d['m16'], d['x16'] = m16, x16
        out.append(d)
        if d['op'] == 0xC2:
            if d['val'] & 0x20: m16 = True
            if d['val'] & 0x10: x16 = True
        elif d['op'] == 0xE2:
            if d['val'] & 0x20: m16 = False
            if d['val'] & 0x10: x16 = False
        pc = d['next']
        if stop and d['op'] in (0x60, 0x6B, 0x40, 0x4C, 0x5C, 0x6C, 0x7C, 0xDC, 0x80, 0x82):
            break
    return out


def show(rom, pc, n=40, m16=True, x16=True, stop=True, file=None):
    for d in lst(rom, pc, n, m16, x16, stop):
        flag = ('M' if d['m16'] else 'm') + ('X' if d['x16'] else 'x')
        print(f"{d['pc']:06X} {flag} {d['bytes'].hex():<9} {d['text']}", file=file)
