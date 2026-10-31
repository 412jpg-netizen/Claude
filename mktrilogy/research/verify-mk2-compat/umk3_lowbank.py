"""T4-2 / C-U5: UMK3 tile-directory entries referenced by frames whose bank byte is < $40; their extents and
the $FF runs before them."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, umk3spr as U
r=D.rom('umk3'); L=len(r)
refs=collections.defaultdict(lambda: collections.defaultdict(set))
allbanks=collections.Counter(); nent=0; dirent=set()
for s in range(28):
    if s==11: continue
    st=U.USet(s); n=st.nframes_guess()
    for f in range(1,n+1):
        try: pcs=st.frame(f)[0]
        except Exception as e: print('frame err',s,f,e); continue
        for p in pcs:
            for w in p[4]:
                g=(w&0xFC)>>2; refs[s][g].add(w>>8)
for s in sorted(refs):
    st=U.USet(s)
    for g,idxs in sorted(refs[s].items()):
        o=D.off(st.tg+4*g,L); lo,bank,flag=D.w16(r,o),r[o+2],r[o+3]; dirent.add(o)
        allbanks[bank>>4]+=1
        if bank<0x40:
            mx=max(idxs)
            if flag&0x80:
                s_=flag&0x3F; base=D.off((bank<<16)|lo,L); T=r[base]
                end=base+1+(mx+1)*s_+(1 if mx>=T else 0)  # approx extent
            else:
                s_=16 if flag&0x40 else 32; base=D.off((bank<<16)|lo,L); end=base+(mx+1)*s_
            # $FF run before
            k=base
            while k>0 and r[k-1]==0xFF: k-=1
            print('set %2d g%2d entry@file %06X bankbyte-file %06X -> %02X:%04X flag %02X maxidx %d  data file %06X-%06X  FF run %06X-%06X (%d B)'%(
                s,g,o,o+2,bank,lo,flag,mx,base,end,k,base,base-k))
print('directory entries referenced:',len(dirent),' bank high-nibble histogram',dict(allbanks))
