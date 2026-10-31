"""List code that reads the stage-ID variable $7E:3270 and the tables it indexes."""
import sys, re; sys.path.insert(0,'/home/claude/work/lib'); sys.path.insert(0,'/home/claude/work/scripts/mk2')
import snes, d65
r=snes.load('mk2')
for o in range(0,0x60000-3):
    hit = (r[o] in (0xad,0xae,0xac,0xcd) and snes.u16(r,o+1)==0x3270) or (r[o]==0xaf and snes.u16(r,o+1)==0x3270 and r[o+3]==0x7e)
    if hit:
        a=0x800000|o
        ins=d65.disasm(r,a,9,stop=False)
        print('%06X'%a, ' | '.join(t for _,_,t in ins))
