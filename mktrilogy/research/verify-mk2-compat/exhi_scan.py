"""Byte-pattern scan of UMK3 for ExHiROM hazards that a code trace could miss:
 (1) PEA $hhll ; PLB  with ll (the byte PLB pulls) a ROM bank < $7E
 (2) 8-bit LDA #$bb ; PHA ; PLB with bb < $7E
 (3) JSL/JML long to banks $00-$7D (opcode 22/5C)
 (4) LDA #imm8/16 then STA $43x4 (DMA source bank) with bank < $7E
Reports raw hits; each must be judged (data vs code)."""
import sys, re, collections; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
r=D.rom('umk3')
def hits(p): return [m.start() for m in re.finditer(p, r, re.S)]
out=collections.defaultdict(list)
for o in hits(rb'\xF4..\xAB'):
    ll=r[o+1]
    if ll<0x7E and not (0x00<=ll<0x00): out['pea_plb'].append((o,ll,r[o+2]))
for o in hits(rb'\xA9.\x48\xAB'):
    if r[o+1]<0x7E: out['lda8_pha_plb'].append((o,r[o+1]))
for o in hits(rb'[\x22\x5C]...'):
    pass
for o in hits(rb'\xA9..?[\x8D\x8F][\x04\x14\x24\x34\x44\x54\x64\x74]\x43'):
    out['dma_bank'].append((o,r[o+1]))
for k,v in out.items():
    print(k, len(v))
    for x in v[:40]: print('   %06X'%(0xC00000|x[0]), ' '.join('%02X'%b for b in x[1:]), r[x[0]:x[0]+8].hex())
