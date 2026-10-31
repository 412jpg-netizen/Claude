"""List covered runs of MK2 bytes found in UMK3 (k=32), classify filler (single repeated byte) vs other,
and locate where in UMK3 the biggest runs are."""
import sys, numpy as np; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
m=D.rom('mk2'); u=D.rom('umk3')
cov=np.load('/home/claude/work/out/verify-mk2-compat/cov_mk2_in_umk3_k32.npy')
runs=[]; i=0; n=len(cov)
while i<n:
    if cov[i]:
        j=i
        while j<n and cov[j]: j+=1
        runs.append((i,j)); i=j
    else: i+=1
fill=0; other=[]
for a,b in runs:
    seg=m[a:b]
    if len(set(seg))==1: fill+=b-a
    else: other.append((a,b))
print('runs',len(runs),'covered',int(cov.sum()),'filler(single-byte runs)',fill,'non-filler',sum(b-a for a,b in other))
other.sort(key=lambda x:x[0]-x[1])
for a,b in other[:15]:
    seg=m[a:b]; k=u.find(seg[:64])
    same = 'same offset' if k==a else ''
    print('  MK2 $%06X-$%06X (%5d B) -> UMK3 %s %s'%(0xC00000|a,0xC00000|(b-1),b-a,('$%06X'%(0xC00000|k)) if k>=0 else '?',same))
nb=len(m)//0x10000
print('MK2 banks with 0 covered bytes:',' '.join('%02X'%(0xC0+i) for i in range(nb) if cov[i*0x10000:(i+1)*0x10000].sum()==0))
print('covered in $CE:8E00-$CF:5000:', int(cov[0x0E8E00:0x0F5000].sum()))
