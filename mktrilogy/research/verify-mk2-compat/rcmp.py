"""Compare two routines instruction by instruction (linear, no stop) using my disassembler.
usage: rcmp.py romA addrA romB addrB count"""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
a=sys.argv
ra,aa,rb,ab,n=a[1],int(a[2],16),a[3],int(a[4],16),int(a[5])
A=D.dis(ra,aa,n,stop=False); B=D.dis(rb,ab,n,stop=False)
same=sameop=diff=0
for (pa,ba,ta),(pb,bb,tb) in zip(A,B):
    if ba==bb: k='=='; same+=1
    elif ba[:2]==bb[:2]: k='~~'; sameop+=1
    else: k='!!'; diff+=1
    if len(sys.argv)>6: print('%06X %-10s %-22s %s %06X %-10s %s'%(pa,ba,ta,k,pb,bb,tb))
print('identical %d same-opcode %d different %d'%(same,sameop,diff))
