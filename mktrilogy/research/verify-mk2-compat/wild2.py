import sys, re; sys.path.insert(0,'/home/claude/work/scripts/verify-mk2-compat')
import d as D
def rx(p): return re.compile(b''.join(b'.' if t=='..' else re.escape(bytes([int(t,16)])) for t in p.split()), re.S)
PATS={'setsel':'eb 29 fe 00','hdrcopy':'a7 .. 9d .. .. a0 02 00 b7 .. 9d .. ..',
'framewalk':'29 f0 00 f0 .. 4a 4a 4a 4a a8 b7 .. 29 ff 00',
'tilefetch':'29 fc 00 a8 b7 .. 85 .. c8 c8 b7 .. 85 ..',
'posdecode':'e2 20 eb a5 .. eb c2 20 a8'}
for name,p in PATS.items():
    for g in ['mk2','mk3','umk3']:
        r=D.rom(g); hits=['%06X'%(0xC00000|m.start()) for m in rx(p).finditer(r)]
        print('%-10s %-5s %d %s'%(name,g,len(hits),hits[:10]))
