"""UMK3 sprite decoding with the MK2 frame parser (header/frame tables/frame bytes identical by trace of
$88:A471, $88:A645, $83:8000) and the UMK3 tile fetch $83:8362/$83:8474/$83:850F."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D, mk2spr as M
class USet(M.Set):
    def __init__(self, s, game='umk3', bank_tbl=0x86EAEC, lo_tbl=0x86EB24):
        super().__init__(game, s, bank_tbl, lo_tbl)
    def tile(self, word):
        g=(word&0xFC)>>2; idx=word>>8; lo,bank,flag=self.group(g); r=self.r
        if not flag&0x80:
            if flag&0x40:   # 16-byte tiles, upper 16 bytes zero ($83:8375)
                o=D.off((bank<<16)|((lo+idx*16)&0xFFFF),self.L); return bytes(r[o:o+16])+bytes(16),('raw16',g,idx,flag)
            o=D.off((bank<<16)|((lo+idx*32)&0xFFFF),self.L); return bytes(r[o:o+32]),('raw',g,idx,flag)
        s=flag&0x3F; base=D.off((bank<<16)|lo,self.L); T=r[base]
        a=base+1+idx*s; fill=0
        if idx>=T: fill=r[a]; a+=1
        nm=2 if flag&0x40 else 4
        m=r[a:a+nm]; p=a+nm; out=bytearray(32)
        for k in range(nm):
            for b in range(8):
                if m[k]&(0x80>>b): out[k*8+b]=r[p]; p+=1
                else: out[k*8+b]=fill
        return bytes(out),('cmp',g,idx,flag,T)
