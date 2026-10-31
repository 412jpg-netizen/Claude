"""Independent k-byte block match: for every byte of ROM A, is it covered by some k-byte window that also
occurs somewhere in ROM B?  64-bit polynomial window hashes (numpy), then coverage expansion.
usage: blockmatch.py A B k  -> prints unmatched count and per-bank table; saves coverage .npy"""
import sys, numpy as np; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
def whash(buf,k):
    b=np.frombuffer(buf,dtype=np.uint8).astype(np.uint64); n=len(b)-k+1
    P=np.uint64(1099511628211); h=np.zeros(n,dtype=np.uint64)
    with np.errstate(over='ignore'):
        for j in range(k): h=h*P+b[j:j+n]
    return h
A,B,k=sys.argv[1],sys.argv[2],int(sys.argv[3])
ra,rb=D.rom(A),D.rom(B)
ha=whash(ra,k); hb=np.unique(whash(rb,k))
m=np.isin(ha,hb,assume_unique=False)
cov=np.zeros(len(ra)+1,dtype=np.int32)
idx=np.nonzero(m)[0]
np.add.at(cov,idx,1); np.add.at(cov,idx+k,-1)
cov=np.cumsum(cov)[:len(ra)]>0
print('%s bytes %d, matched windows %d, covered bytes %d, UNMATCHED bytes %d'%(A,len(ra),len(idx),cov.sum(),len(ra)-cov.sum()))
np.save('/home/claude/work/out/verify-mk2-compat/cov_%s_in_%s_k%d.npy'%(A,B,k),cov)
nb=len(ra)//0x10000
print('per bank unmatched:',' '.join('%02X:%d'%(0xC0+i,(~cov[i*0x10000:(i+1)*0x10000]).sum()) for i in range(nb)))
