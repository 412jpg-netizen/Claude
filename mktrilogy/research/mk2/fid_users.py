"""List code that loads the fighter-ID variables ($7E:2EF8 = P1, $7E:30A6 = P2) and the
first long/abs-indexed table it touches in the next few instructions."""
import sys; sys.path.insert(0,'/home/claude/work/lib'); sys.path.insert(0,'/home/claude/work/scripts/mk2')
import snes, d65, re
r=snes.load('mk2')
for o in range(0,0x60000-3):
    if snes.u16(r,o+1) in (0x2EF8,0x30A6) and r[o] in (0xad,0xae,0xac):
        a=0x800000|o
        ins=d65.disasm(r,a,12,stop=False)
        tabs=[t for _,_,t in ins if re.search(r'\$[0-9A-F]{6},x|\$[0-9A-F]{4},[xy]',t)]
        print('%06X'%a, ' | '.join(t for _,_,t in ins[:7]))
