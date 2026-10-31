"""ROM coverage map of decoded sprite data (frames + tile groups + per-set tables) for MK2."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import mk2gfx as g, snes
from sizes import analyse
regs=[]
for s in range(17):
    R=analyse(s); hd=g.header(s)
    for a,b in R['franges']: regs.append((a,b,'frames',s))
    for gi,(base,st,cnt,used) in R['groups'].items():
        o=snes.to_off(base,g.N); regs.append((o,o+st*cnt,'g%d/st%d'%(gi,st),s))
    n=R['nframes']
    o=snes.to_off(hd['frame_ptr_tbl'],g.N); regs.append((o,o+2*n+(n+63)//64,'fptr+bank',s))
    o=snes.to_off(hd['tile_groups'],g.N); regs.append((o,o+4*R['ngroups'],'grouptbl',s))
    o=snes.to_off(hd['pos_tbl'],g.N); regs.append((o,o+32,'pos',s))
    if hd['box_tbl']:
        o=snes.to_off(hd['box_tbl'],g.N); regs.append((o,o+4*n,'box',s))
regs.sort()
# overlaps
ov=[(x,y) for x,y in zip(regs,regs[1:]) if y[0]<x[1]]
print('overlaps:',len(ov)); [print('  ',['%06X-%06X %s set%d'%t for t in p]) for p in ov[:20]]
# per bank coverage
cov=bytearray(g.N)
for a,b,k,s in regs:
    for i in range(a,min(b,g.N)): cov[i]=1
for bank in range(0x30):
    c=sum(cov[bank*0x10000:(bank+1)*0x10000])
    print('bank %02X (C%X): sprite-data coverage %5.1f%%'%(bank,bank,100*c/0x10000) if bank>=0x10 else 'bank %02X: %5.1f%%'%(bank,100*c/0x10000))
print('total covered bytes', sum(cov))
print('\nuncovered gaps >= 512 bytes in banks $07-$2F:')
i=0x70000
while i<g.N:
    if not cov[i]:
        j=i
        while j<g.N and not cov[j]: j+=1
        if j-i>=512: print('  %06X-%06X (%6d B)  $%06X'%(i,j,j-i,0xC00000|i))
        i=j
    else: i+=1
