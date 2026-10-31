"""Independent test of T2-3: convert every MK2 compressed tile group to the UMK3 layout
([T] + records, fill-byte records for idx>=T) and decode every referenced tile with a decoder written
from UMK3 $83:8362/$83:8474 (+ mask handlers $83:85AA). Compare to the MK2 decode ($81:834B)."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
r=D.rom('mk2'); L=len(r)
def umk3_decode(group_bytes, flag, idx):
    """group_bytes: bytes starting at the group pointer (bank-local), flag = byte +3 of the directory entry"""
    s=flag&0x3F; T=group_bytes[0]
    a=1+idx*s; fill=0
    if idx>=T: fill=group_bytes[a]; a+=1
    m=group_bytes[a:a+4]; p=a+4; out=bytearray(32)
    for k in range(4):
        for b in range(8):
            if m[k]&(0x80>>b): out[k*8+b]=group_bytes[p]; p+=1
            else: out[k*8+b]=fill
    return bytes(out)
def convert(st, g, maxidx):
    lo,bank,flag=st.group(g); s=flag&0x3F; o=D.off((bank<<16)|lo,L)
    recs=bytes(r[o:o+(maxidx+1)*s])
    if maxidx<255: return bytes([maxidx+1])+recs
    return bytes([255])+recs[:255*s]+b'\x00'+recs[255*s:]
tot=collections.Counter(); used255=0
for s in range(17):
    st=M.Set('mk2',s); n=st.nframes_guess(); refs=collections.defaultdict(set)
    for f in range(1,n+1):
        for p in st.frame(f)[0]:
            for w in p[4]: refs[(w&0xFC)>>2].add(w>>8)
    mism=0; cnt=0
    for g,idxs in refs.items():
        lo,bank,flag=st.group(g)
        if not flag&0x80: continue
        mx=max(idxs); used255+= mx==255
        cg=convert(st,g,mx)
        for i in idxs:
            ref,_=st.tile(((i<<8)|(g<<2)))
            if umk3_decode(cg,flag,i)!=ref: mism+=1
            cnt+=1
    tot['tiles']+=cnt; tot['mism']+=mism
    print('set %2d compressed distinct tiles %5d mismatches %d'%(s,cnt,mism))
print(dict(tot),'groups using idx 255:',used255)
