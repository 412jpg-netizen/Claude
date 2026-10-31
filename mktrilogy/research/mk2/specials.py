"""Special-move input checks. $81:A943 dispatches per fighter (ID*2 into a 12-entry table chosen by the
button event: $81:A989, $81:A9A1, $81:A9B9, $81:AA88, $81:AAA0; $AACD = nothing). Each check routine calls
$81:C8CB (X = time window, A = input-sequence pointer in bank 81) and on success starts a move with
`lda #routine; jmp $81:C83F` (bank-81 routine) / `jmp $81:C852` (bank 85) / `jmp $81:C7C6|C7D5|C78F` (range-checked)."""
import sys, re; sys.path.insert(0,'/home/claude/work/lib'); sys.path.insert(0,'/home/claude/work/scripts/mk2')
import snes, d65, mk2gfx as g
r=g.ROM
EVT=[0x81A989,0x81A9A1,0x81A9B9,0x81AA88,0x81AAA0]
entries={}
for t in EVT:
    for fid in range(12):
        v=g.w16(t+2*fid)
        if v!=0xAACD: entries.setdefault(fid,[]).append(0x810000|v)
allstarts=sorted(set(a for v in entries.values() for a in v))
def walk(a):
    seqs=[]; moves=[]; prev=None; pc=a
    for _ in range(200):
        ins=d65.disasm(r,pc,1,stop=False)[0]; t=ins[2]
        if t.startswith('jsl $81C8CB') and prev and prev.startswith('lda #$'): seqs.append(prev[5:])
        m=re.match(r'jmp \$(C83F|C852|C7C6|C7D5|C78F)',t)
        if m and prev and prev.startswith('lda #$'): moves.append(prev[5:]+'@'+m.group(1))
        if t in ('rtl','rts') or t.startswith('jml'): break
        prev=t; pc=(pc&0xFF0000)|((pc+len(ins[1])//2)&0xFFFF)
        if pc!=a and pc in allstarts: break
    return seqs, moves, pc
if __name__=='__main__':
    for fid in range(12):
        out=[]
        for e in entries.get(fid,[]):
            s,m,end=walk(e)
            out.append('%04X-%04X seq[%s] -> [%s]'%(e&0xFFFF,end&0xFFFF,','.join(s),','.join(m)))
        print('%-12s'%g.NAMES[fid]); [print('    '+x) for x in out]
