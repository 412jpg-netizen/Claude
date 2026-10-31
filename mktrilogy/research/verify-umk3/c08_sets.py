import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
r = v.load('umk3')
# set tables used by $88:A483/$88:A489 (X = set*2)
print('EB24-EAEC =', hex(0xEB24 - 0xEAEC), 'entries', (0xEB24 - 0xEAEC)//2)
for s in range(30):
    bk = v.u16(r, 0x86EAEC + 2*s); ad = v.u16(r, 0x86EB24 + 2*s)
    hdr = (bk & 0xFF) << 16 | ad
    line = '%2d bank %04X addr %04X -> %06X' % (s, bk, ad, hdr)
    if bk and ad >= 0x8000 or (bk & 0xFF) >= 0xC0:
        h = v.bytes_at(r, hdr, 16)
        bt = (h[7] << 16) | h[0] | h[1] << 8
        dr = (h[4] << 16) | h[2] | h[3] << 8
        ft = (h[7] << 16) | h[5] | h[6] << 8
        dl = (h[11] << 16) | h[12] | h[13] << 8
        x8 = h[8] | h[9] << 8; xe = h[14] | h[15] << 8
        line += '  banktab %06X dir %06X frametab %06X delta %06X  +8=%04X +E=%04X' % (bt, dr, ft, dl, x8, xe)
    print(line)
