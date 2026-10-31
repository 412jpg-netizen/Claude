"""Critic check: disassemble the raw-search readers of the kode flag pairs found by flagraw2.py
(SHADOW FIGHTING $3C22 at $85:C656, 2X HEALTH/2X DAMAGE $3BD6/$3BDA at $84:E82C/$84:E833) to see
whether they are global or per-player. Linear disassembly from a few bytes before each site; the
start points were chosen by hand and may begin mid-instruction (check the listing).
Output: out/plan/dis_flagreaders.txt
"""
import sys, io, contextlib
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import show
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    for a, n in ((0x85C64A, 18), (0x84E81E, 22)):
        show('umk3', a, n, True, True, False)
        print('----')
open('/home/claude/work/out/plan/dis_flagreaders.txt', 'w').write(buf.getvalue())
print(buf.getvalue())
