"""List indexed jump tables (jmp/jsr (abs,x)) in MK2 code banks with the instruction context,
and the number of plausible same-bank code pointers in each table."""
import sys; sys.path.insert(0,'/home/claude/work/lib'); sys.path.insert(0,'/home/claude/work/scripts/mk2')
import snes, d65
r=snes.load('mk2')
for o in range(0x8000,0x60000-3):
    if (o & 0xFFFF) < 0x8000: continue
    if r[o] in (0x7C,0xFC):
        t=snes.u16(r,o+1)
        if t < 0x8000: continue
        bank=o>>16; base=(bank<<16)|t
        n=0
        while n<64:
            v=snes.u16(r,base+2*n)
            if v<0x8000: break
            n+=1
        if 12<=n<=20:
            prev=d65.disasm(r,0x800000|(o-12),5,stop=False)
            print('%06X %s ($%04X,x) n=%d  ctx: %s' % (0x800000|o, 'jmp' if r[o]==0x7C else 'jsr', t, n, ' | '.join(x[2] for x in prev)))
