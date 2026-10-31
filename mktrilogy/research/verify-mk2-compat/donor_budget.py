"""Independent donor byte budget for MK2 Cage/Baraka/Raiden/Kintaro."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
from anims import parse
r=D.rom('mk2'); L=len(r)
def script_end(bank, lo, maxn=400):
    # walk linearly until end/jump; returns end address (exclusive) and set of jump targets
    p=lo; tg=[]
    for _ in range(maxn):
        w=D.w16(r,D.off((bank<<16)|p,L)); p+=2
        if w==0: return p,tg
        if w<0xFFF6: continue
        if w==0xFFFF: tg.append(D.w16(r,D.off((bank<<16)|p,L))); return p+2,tg
        if w==0xFFF8: tg.append(D.w16(r,D.off((bank<<16)|p+1,L))); p+=3; continue
        p+=2*{0xFFFE:0,0xFFFD:1,0xFFFC:2,0xFFFB:1,0xFFFA:2,0xFFF9:1,0xFFF7:0}[w]
    return p,tg
oc=D.off(0x85C49E,L); osp=D.off(0x85C4E2,L)
for name,s,fids in [('Cage',2,[2]),('Baraka',3,[3]),('Raiden',6,[7]),('Kintaro',9,[12])]:
    st=M.Set('mk2',s); n=st.nframes_guess()
    # shadow data extent
    sh=None
    if st.sh!=0xFFFF:
        ps=sorted(set(D.w16(r,D.off((st.b8<<16)|st.sh+2*i,L)) for i in range(n))-{0xFFFF})
        sh=(ps[0],ps[-1],st.sh, st.sh-ps[0])
    # anim block: header .. max script end reachable from common (+specific) tables
    c=D.w24(r,oc+4*fids[0]); sp=D.w24(r,osp+4*fids[0]); bank=c>>16
    todo=[]; ncom=(sp-c)//2 if sp>c else 24
    for i in range(ncom):
        w=D.w16(r,D.off(c+2*i,L)); 
        if w: todo.append(w)
    # specific: walk entries until a word points below the table end or is not plausible
    i=0; spe=[]
    while True:
        w=D.w16(r,D.off(sp+2*i,L))
        if w==0 and i>0: i+=1; continue
        if not (sp&0xFFFF) < w < 0xFFF0 or i>60: break
        spe.append(w); i+=1
        if sp+2*i>=min(todo+spe): break
    todo+=spe
    seen=set(); mx=0
    while todo:
        a=todo.pop()
        if a in seen: continue
        seen.add(a); e,tg=script_end(bank,a); mx=max(mx,e); todo+=tg
    print('%-8s n=%d hdr=%06X shadow ptrs %s anim block %06X..%02X%04X = %d bytes (%d scripts, specific entries %d)'%(
        name,n,st.hdr_addr, ('%04X..%04X tbl %04X gap %d'%sh) if sh else '-', st.hdr_addr, bank, mx, mx-(st.hdr_addr&0xFFFF), len(seen), len(spe)))
