"""Full comparison of MK2 LZ $85:B9FC..$85:BEA7 (code + 4 jump tables) with UMK3 $88:AD30 (+delta)."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
m=D.rom('mk2'); u=D.rom('umk3')
A0=0x85B9FC; B0=0x88AD30; delta=(B0&0xFFFF)-(A0&0xFFFF)
oa=D.off(A0,len(m)); ob=D.off(B0,len(u))
n=0xBDEC-0xB9FC
eq=sum(1 for i in range(n) if m[oa+i]==u[ob+i])
print('code bytes', n, 'equal bytes', eq)
# opcode-level compare along MK2 instruction boundaries using sync linear sweep with M/X widths from each entry
# simple approach: compare raw bytes, and classify differing bytes
diffs=[i for i in range(n) if m[oa+i]!=u[ob+i]]
print('differing byte positions', len(diffs))
# tables
for ta,cnt in [(0xBDEC,16),(0xBE0C,16),(0xBE2A,32),(0xBE68,32)]:
    o1=D.off(0x850000|ta,len(m)); o2=D.off(0x880000|(ta+delta),len(u))
    t1=[D.w16(m,o1+2*i)-(A0&0xFFFF) for i in range(cnt)]; t2=[D.w16(u,o2+2*i)-(B0&0xFFFF) for i in range(cnt)]
    print('table %04X -> %04X same after relocation: %s'%(ta,ta+delta,t1==t2))
# show distinct (mk2,umk3) byte pairs at differing positions
import collections
c=collections.Counter((m[oa+i],u[ob+i]) for i in diffs)
print(sorted(c.items(),key=lambda x:-x[1])[:30])
