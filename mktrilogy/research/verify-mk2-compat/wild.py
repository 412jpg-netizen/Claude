"""Wildcard byte-pattern search across the three ROMs. '..' = any byte."""
import sys, re; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
PATS={
 'lz_backref': 'aa eb 29 ff 07 85 .. 8a 29 78 00 4a 4a aa',
 'lz_head': '64 .. 8b d4 .. ab ab a7 .. 85 .. a8 e6 .. e6 .. a7 .. 29 ff 00 85 .. e6 .. c9 02 00',
 'mask01': 'a6 .. 9e .. .. 9e .. .. 9e .. .. b7 .. c8 29 ff 00 eb 9d .. .. 60',
 'mask00': 'a6 .. 9e .. .. 9e .. .. 9e .. .. 9e .. .. 60',
 'maskFF': 'a6 .. b7 .. c8 c8 9d .. .. b7 .. c8 c8 9d .. .. b7 .. c8 c8 9d .. .. b7 .. c8 c8 9d .. .. 60',
 'tilefetch_mul': 'e2 20 eb 29 3f 8f 02 42 .. a5 .. 8f 03 42',
}
def rx(p): return re.compile(b''.join(b'.' if t=='..' else re.escape(bytes([int(t,16)])) for t in p.split()), re.S)
for name,p in PATS.items():
    for g in ['mk2','mk3','umk3']:
        r=D.rom(g); hits=['%06X'%(0xC00000|m.start()) for m in rx(p).finditer(r)]
        print('%-14s %-5s %d %s'%(name,g,len(hits),hits[:8]))
