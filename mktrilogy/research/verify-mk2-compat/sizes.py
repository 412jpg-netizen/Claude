"""Per-set footprint of MK2 sprite data: frames (union of decoded ranges) + tile groups ((max idx+1)*stride)."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
r=D.rom('mk2'); L=len(r)
cover=bytearray(L); owner={}
per={}
grp_users=collections.defaultdict(set)
for s in range(17):
    st=M.Set('mk2',s); n=st.nframes_guess()
    fr=set(); gmax={}
    for f in range(1,n+1):
        pcs,ln,a=st.frame(f); o=D.off(a,L); fr.update(range(o,o+ln))
        for p in pcs:
            for w in p[4]:
                g=(w&0xFC)>>2; gmax[g]=max(gmax.get(g,-1),w>>8)
    gb=set()
    for g,mx in gmax.items():
        lo,bank,flag=st.group(g); sd=(flag&0x3F) if flag&0x80 else 32
        o=D.off((bank<<16)|lo,L); gb.update(range(o,o+(mx+1)*sd)); grp_users[(bank<<16)|lo].add(s)
    # tables: header16, fp 2n, fbank ceil(n/64), group table 4*(max g+1), pos 32, shadow 2n (if), box 4n (if)
    tb=16+2*n+(n+63)//64+4*(max(gmax)+1)+32+(2*n if st.sh!=0xFFFF else 0)+(4*n if st.box!=0xFFFF else 0)
    per[s]=(len(fr),len(gb),tb,len(gmax))
    for o in fr|gb:
        cover[o]+=1
print('set frames_bytes gfx_bytes tables groups')
for s,v in per.items(): print(s, *v, sum(v[:3]))
print('overlap bytes (cover>1):', sum(1 for c in cover if c>1))
print('covered bytes:', sum(1 for c in cover if c))
print('groups shared by >1 set:', [hex(k) for k,v in grp_users.items() if len(v)>1])

# --- reproduce the coverage figure with tables included (fptr+fbank, group table, pos, box)
cov2=bytearray(cover)
cov2=bytearray(1 if c else 0 for c in cover)
for s in range(17):
    st=M.Set('mk2',s); n=st.nframes_guess()
    gmax=set()
    for f in range(1,n+1):
        for p in st.frame(f)[0]:
            for w in p[4]: gmax.add((w&0xFC)>>2)
    def mark(a,ln):
        o=D.off(a,L)
        for i in range(o,o+ln): cov2[i]=1
    mark(st.fp,2*n+(n+63)//64); mark(st.tg,4*(max(gmax)+1)); mark(st.pos,32)
    if st.box!=0xFFFF: mark((st.b8<<16)|st.box,4*n)
    tbl_noshadow=None
print('covered incl. fptr/fbank/grouptbl/pos/box tables:', sum(cov2))
for s in range(17):
    st=M.Set('mk2',s); n=st.nframes_guess()
    if st.sh!=0xFFFF:
        o=D.off((st.b8<<16)|st.sh,L)
        for i in range(o,o+2*n): cov2[i]=1
print('... plus shadow tables:', sum(cov2))
