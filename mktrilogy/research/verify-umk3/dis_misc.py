# Dump the short routines cited in verify-umk3.md into one listing (own disassembler, v.py)
import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
r = v.load('umk3')
items = [
    ('reset/IRQ/NMI stubs', [(0x0083D6, 1, True), (0x0083D7, 15, True), (0x008738, 7, True), (0x008765, 1, True)]),
    ('$80:8470 selection init + $80:84B8 zone->record', [(0x808470, 45, True)]),
    ('$88:93C0 $36D0/$3894 -> $52C8/$52CA', [(0x8893C0, 6, True)]),
    ('$88:9576 / $88:95A0 anim table loaders', [(0x889576, 18, True), (0x8895A0, 18, True)]),
    ('$88:9842..$88:9931 palette choice', [(0x889842, 120, True)]),
    ('$82:9D57 second palette user', [(0x829D57, 12, True)]),
    ('$88:A471 set header', [(0x88A471, 70, True)]),
    ('$88:A5A8 frame locate', [(0x88A5A8, 18, True)]),
    ('$88:A6A6 per-frame +8/+E table', [(0x88A6A6, 20, True)]),
    ('$88:87DD anim interpreter + $FFF8 handler', [(0x8887DD, 30, True)]),
    ('$86:A1F6 grid lookup', [(0x86A1F6, 8, True)]),
    ('$86:A2D7 cursor cell init', [(0x86A2B6, 12, True), (0x86A2D7, 4, True)]),
    ('$86:A726 move handler', [(0x86A726, 30, True)]),
    ('$84:8FC8 record index', [(0x848FC8, 12, True)]),
    ('$84:9081 layer pointer loop', [(0x849081, 18, True)]),
    ('$84:961C palette block loader', [(0x84961C, 20, True)]),
    ('$84:9703 8bpp pixel +16*n transform', [(0x849703, 20, True), (0x849791, 8, True)]),
    ('$84:9444 call of $84:9703', [(0x849444, 14, True)]),
    ('$87:FECB CGRAM DMA from $7E:C0A8', [(0x87FECB, 16, True)]),
    ('$85:DF1A kode dispatch', [(0x85DF1A, 12, True)]),
    ('$85:E237 zone kodes', [(0x85E237, 16, True)]),
    ('$85:E721 battle-X ids', [(0x85E721, 10, True)]),
    ('$85:E8F0 stage-name use', [(0x85E903, 4, True)]),
]
for title, rngs in items:
    print('==== ' + title)
    for a, n, _ in rngs:
        v.show(r, a, n, stop=False)
    print()
