"""Find tables indexed by fighter ID: code that loads $4C10,x (per-object fighter ID, written by
$85:C629) or the P1/P2 fighter vars $2EF8/$30A6, then (within a few instructions, after asl/tax)
does an indexed load from a fixed table. Prints table address + context."""
import sys, re, collections; sys.path.insert(0,'/home/claude/work/lib'); sys.path.insert(0,'/home/claude/work/scripts/mk2')
import snes, d65
r=snes.load('mk2')
found=collections.defaultdict(list)
for o in range(0,0x60000-3):
    w=snes.u16(r,o+1)
    if (r[o] in (0xbd,0xb9) and w==0x4C10) or (r[o] in (0xad,) and w in (0x2EF8,0x30A6)):
        a=0x800000|o
        ins=d65.disasm(r,a,8,stop=False)
        for pc,b,t in ins[1:]:
            m=re.match(r'(lda|ldx|ldy|adc|cmp|and|ora|jsr|jmp) (\(?\$[0-9A-F]{4,6}(,x\))?)(,x|,y)?',t)
            if m and (m.group(4) or 'x)' in t):
                tb=m.group(2)
                if tb.startswith('$4C10') or tb.startswith('$2EF8') : continue
                found[tb].append(a)
                break
for tb,refs in sorted(found.items()):
    print(tb, ' '.join('%06X'%x for x in refs[:8]), '(+%d)'%(len(refs)-8) if len(refs)>8 else '')
