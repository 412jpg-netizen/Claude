"""Raw scan of UMK3 code banks ($C0-$C8 = file 0-0x8FFFF) for long-address opcodes whose operand is a ROM
address through banks $00-$7D (bank $00-$3F with addr >= $8000, or bank $40-$7D)."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
r=D.rom('umk3')
LONG={0x0F,0x1F,0x2F,0x3F,0x4F,0x5F,0x6F,0x7F,0x8F,0x9F,0xAF,0xBF,0xCF,0xDF,0xEF,0xFF,0x22,0x5C}
hits=[]
for o in range(0,0x90000-3):
    if r[o] in LONG:
        a=r[o+1]|r[o+2]<<8|r[o+3]<<16; b=a>>16
        if (b<0x40 and (a&0xFFFF)>=0x8000) or (0x40<=b<0x7E):
            hits.append((o,a))
print('raw candidate hits', len(hits))
by=collections.Counter(h[0]>>16 for h in hits); print('by file bank', dict(sorted(by.items())))
# show those whose next 2 instructions decode as plausible code (heuristic: no BRK/COP/WDM/STP in next 6 insns)
good=[]
for o,a in hits:
    pc=0x800000|o
    try:
        ins=D.dis('umk3',pc,6,stop=False)
    except Exception: continue
    if any(t.split()[0] in ('brk','cop','wdm','stp','xce','rti') for _,_,t in ins): continue
    good.append((o,a,ins[0][2]))
print('after crude code filter', len(good))
for o,a,t in good[:60]: print('  %06X  %s'%(0x800000|o,t))
