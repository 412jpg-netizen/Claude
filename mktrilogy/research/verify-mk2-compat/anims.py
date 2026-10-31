"""Parse MK2 animation scripts per the $83:F28E interpreter (dispatch $83:F32C)."""
import sys, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
r=D.rom('mk2'); L=len(r)
ARGS={0xFFFF:'jump',0xFFFE:0,0xFFFD:1,0xFFFC:2,0xFFFB:1,0xFFFA:2,0xFFF9:1,0xFFF8:'fid',0xFFF7:0}
def parse(bank, lo, maxn=200):
    items=[]; p=lo; seen=set()
    for _ in range(maxn):
        a=(bank<<16)|p; w=D.w16(r,D.off(a,L)); p+=2
        if w==0: items.append(('end',)); break
        if w<0xFFF6: items.append(('f',w)); continue
        if w==0xFFF6: items.append(('BAD',w)); break
        k=ARGS[w]
        if k=='jump':
            t=D.w16(r,D.off((bank<<16)|p,L)); items.append(('jmp',t)); break
        if k=='fid':
            fid=r[D.off((bank<<16)|p,L)]; t=D.w16(r,D.off((bank<<16)|p+1,L)); items.append(('ifid',fid,t)); p+=3; continue
        args=[D.w16(r,D.off((bank<<16)|p+2*i,L)) for i in range(k)]; p+=2*k
        items.append(('cmd',hex(w),[hex(x) for x in args]))
    return items
if __name__=='__main__':
    oc=D.off(0x85C49E,L); fsets={0:0,1:1,2:2,3:3,4:4,5:4,6:5,7:6,8:7,9:7,10:7,11:8,12:9,13:10,14:7,15:7,16:4}
    ncom={f:(0x84 if f<12 or f>13 else (0x30 if f==12 else 0x34))//2 for f in range(17)}
    for f in [2,3,7,12,13]:
        c=D.w24(r,oc+4*f); bank=c>>16
        sets=collections.Counter(); bad=0; firstnonf=0
        for i in range(ncom[f]):
            lo=D.w16(r,D.off(c+2*i,L))
            if lo==0: sets['null']+=1; continue
            it=parse(bank,lo)
            for x in it:
                if x[0]=='f': sets[x[1]>>9]+=1
                if x[0]=='BAD': bad+=1
        print(f, 'common n=%d'%ncom[f], 'frame-word sets', dict(sets), 'bad', bad)
    c=D.w24(r,oc+4*3); lo=D.w16(r,D.off(c,L)); print('Baraka anim0 @%02X:%04X'%(c>>16,lo), parse(c>>16,lo))
    # entry after table: what is at common+$84 for Baraka (the specific table)
