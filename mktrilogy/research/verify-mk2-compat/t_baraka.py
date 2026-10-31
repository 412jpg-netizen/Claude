import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
st=M.Set('mk2',3)
print('hdr %06X nframes_guess'%st.hdr_addr, st.nframes_guess())
pcs,n,a=st.frame(0x64)
print('frame 64 at %06X len %d pieces %d'%(a,n,len(pcs)))
for p in pcs[:5]: print(p)
