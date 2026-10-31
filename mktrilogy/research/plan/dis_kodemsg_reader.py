"""Critic check: disassemble the reader of the kode-message table $85:EA3E (found by a raw
search for the operand bytes of $85:EA3E/$85:EA40/$85:EA42). Shows that each 6-byte entry is
(pointer to a RAM variable, compare value, message pointer): LDA $85EA3E,X / STA $0A / LDA ($0A) /
CMP $85EA40,X, then LDA $85EA42,X as the message. Output: out/plan/dis_85E805.txt
"""
import sys, io, contextlib
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import show
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    show('umk3', 0x85E805, 24, True, True, False)
    print('----')
    show('umk3', 0x85E8AB, 20, True, True, False)
open('/home/claude/work/out/plan/dis_85E805.txt', 'w').write(buf.getvalue())
print(buf.getvalue())
