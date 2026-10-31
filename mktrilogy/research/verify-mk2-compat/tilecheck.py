"""Walk every frame of every MK2 set (frame count = (fbank_lo - fp_lo)/2) and check tile records."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
r=D.rom('mk2'); L=len(r)
tot=collections.Counter(); flags=collections.Counter(); bad=[]; badpos=0
stride_hist=collections.Counter(); grp_set=collections.defaultdict(set)
for s in range(17):
    st=M.Set('mk2',s); n=st.nframes_guess()
    for f in range(1,n+1):
        pcs,ln,a=st.frame(f)
        for (x,y,big,fl,ws) in pcs:
            for w in ws:
                g=(w&0xFC)>>2; lo,bank,flag=st.group(g); flags[flag]+=1
                grp_set[(st.tg+4*g)].add(s)
                if flag&0x80:
                    sd=flag&0x3F; o=D.off((bank<<16)|((lo+(w>>8)*sd)&0xFFFF),L)
                    pc=sum(bin(b).count('1') for b in r[o:o+4])
                    tot['cmp']+=1; stride_hist[sd]+=1
                    if pc+4!=sd: bad.append((s,f,hex(w),sd,pc))
                else: tot['raw']+=1
    print(s, n, dict(tot))
print('total', dict(tot), 'bad', len(bad), bad[:5])
print('flags', sorted((hex(k),v) for k,v in flags.items()))
print('strides', sorted(stride_hist))
