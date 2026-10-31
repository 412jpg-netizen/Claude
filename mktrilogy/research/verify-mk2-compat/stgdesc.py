"""MK3 ($82:B888, 26 recs) / UMK3 ($84:8A22, 29 recs) stage records: 34 B, layer descriptor ptrs at +8..+F
(bank $82/$84). Descriptor type byte +0. Type 0 offsets traced at UMK3 $84:913E (y=1 start):
 tiles bank +1A / lo +1B (-> $EB12/$EB0A, LZ call $84:9425..943E); map candidates lo +20 or +22 with bank +1F.
Type 1 offsets ($84:920C) taken from compat notes and validated by clean decompression only."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
from lz import lz
REC={'mk3':(0x82B888,0x82,26),'umk3':(0x848A22,0x84,29)}
def safe_lz(g,a):
    try:
        if D.off(a,4<<20) is None: return None
        out,inf=lz(g,a)
        return (out,inf) if inf['final_ptr']==0 and 0<inf['len']<0x10000 else None
    except Exception: return None
def descs(g,i):
    tab,bank,n=REC[g]; r=D.rom(g); o=D.off(tab+0x22*i,len(r)); rec=r[o:o+0x22]; out=[]
    for k in range(4):
        p=D.w16(rec,8+2*k)
        if p in (0xFFFF,0x8000): out.append(None); continue
        do=D.off((bank<<16)|p,len(r)); dd=r[do:do+0x30]; out.append(dd)
    return out
if __name__=='__main__':
    for g in ['umk3','mk3']:
        st=collections.Counter()
        for i in range(REC[g][2]):
            for k,dd in enumerate(descs(g,i)):
                if dd is None: continue
                t=dd[0]
                if t==0:
                    til=(dd[0x1A]<<16)|D.w16(dd,0x1B); m20=(dd[0x1F]<<16)|D.w16(dd,0x20); m22=(dd[0x1F]<<16)|D.w16(dd,0x22)
                    st[('t0 tiles ok',safe_lz(g,til) is not None)]+=1
                    st[('t0 map@20 ok',safe_lz(g,m20) is not None)]+=1; st[('t0 map@22 ok',safe_lz(g,m22) is not None)]+=1
                elif t==1:
                    til=(dd[0x18]<<16)|D.w16(dd,0x19); mp=(dd[0x1D]<<16)|D.w16(dd,0x1E)
                    st[('t1 tiles ok',safe_lz(g,til) is not None)]+=1; st[('t1 map ok',safe_lz(g,mp) is not None)]+=1
                else: st[('type',t)]+=1
        print(g, sorted(st.items(),key=str))
