"""T1-6 heuristic: 1 KB windows of MK3 that look like BRR (some 9-byte phase where <=10% of header bytes have
the END bit and >=95% have range <= 12); count BRR-like bytes with no k=32 match in UMK3."""
import sys, numpy as np; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
r=np.frombuffer(D.rom('mk3'),dtype=np.uint8)
cov=np.load('/home/claude/work/out/verify-mk2-compat/cov_mk3_in_umk3_k32.npy')
W=1024; like=np.zeros(len(r),bool); n=0
for s in range(0,len(r),W):
    w=r[s:s+W]; ok=False
    if len(set(w.tolist()))<16: continue
    for ph in range(9):
        h=w[ph::9]
        if len(h)<50: continue
        endf=(h&1).mean(); rng=((h>>4)<=12).mean()
        if endf<=0.10 and rng>=0.95: ok=True; break
    if ok: like[s:s+W]=True; n+=1
u=like&~cov
print('BRR-like windows',n,'bytes',like.sum(),' of which no UMK3 match',u.sum())
idx=np.nonzero(u)[0]
banks={}
for i in idx: banks[i>>16]=banks.get(i>>16,0)+1
print('uncovered BRR-like bytes by bank', {('$%02X'%(0xC0+k)):v for k,v in sorted(banks.items())})
print('in $CF:B800-$D4:4FFF:', u[0x0FB800:0x145000].sum())
