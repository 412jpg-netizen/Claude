"""Find code references to SNES addresses in MK2 code banks ($80-$85).
usage: xref.py ADDR [ADDR...]   prints JSL/JML (any bank form) and same-bank JSR/JMP/abs-operand refs."""
import sys; sys.path.insert(0,'/home/claude/work/lib'); import snes
r=snes.load('mk2')
CODE_END=0x60000
LONG_OPS={0x22:'jsl',0x5C:'jml',0xAF:'lda.l',0xBF:'lda.l,x',0x8F:'sta.l',0x9F:'sta.l,x',0x0F:'ora.l',0x2F:'and.l',0x6F:'adc.l',0x7F:'adc.l,x',0xCF:'cmp.l',0xDF:'cmp.l,x',0xEF:'sbc.l',0xFF:'sbc.l,x'}
ABS_OPS={0x20:'jsr',0x4C:'jmp',0xFC:'jsr(,x)',0x7C:'jmp(,x)',0x6C:'jmp()',0xAD:'lda',0xBD:'lda,x',0xB9:'lda,y',0xA9:'lda#',0xA2:'ldx#',0xA0:'ldy#',0xF4:'pea'}
for a in sys.argv[1:]:
    t=int(a,16); lo=t&0xffff; bk=(t>>16)&0x3f
    print(a)
    for o in range(1,CODE_END-3):
        if snes.u16(r,o)!=lo: continue
        op=r[o-1]
        if op in LONG_OPS and (r[o+2]&0x3f)==bk and r[o+2] in (bk|0x80,bk|0xc0,bk|0x40,bk):
            print(f'  {0x800000|(o-1):06X}  {LONG_OPS[op]}')
        elif op in ABS_OPS and ((o-1)>>16)==bk:
            print(f'  {0x800000|(o-1):06X}  {ABS_OPS[op]} (same bank)')
