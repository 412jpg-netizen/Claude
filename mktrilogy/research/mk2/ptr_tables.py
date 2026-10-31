"""Scan MK2 for runs of 24-bit pointers (bank C0-EF or 80-AF; lo-word any) of length >= N."""
import sys; sys.path.insert(0,'/home/claude/work/lib'); import snes
r=snes.load('mk2')
N=int(sys.argv[1]) if len(sys.argv)>1 else 12
def ok(o):
    b=r[o+2]
    if 0xc0<=b<=0xef: return True
    if 0x80<=b<=0xaf and r[o+1]>=0x80: return True
    return False
o=0; seen=set()
res=[]
for start in range(0,0x60000):
    if start in seen: continue
    n=0; o=start
    while o+3<=len(r) and ok(o): n+=1; o+=3
    if n>=N:
        for k in range(start,o,3): seen.add(k)
        banks=sorted(set(r[k+2] for k in range(start,o,3)))
        res.append((start,n,banks))
for s,n,b in res:
    print(f'{s:06X} ({snes.to_addr(s):06X}) n={n} banks={[hex(x) for x in b][:10]}')
