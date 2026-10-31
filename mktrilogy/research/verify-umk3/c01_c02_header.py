import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
r = v.load('umk3')
print('size', len(r), hex(len(r)), 'size%1024', len(r) % 1024)
h = r[0xFFC0:0xFFE0]
print('title', h[:21])
print('map $FFD5=%02X type $FFD6=%02X romsize $FFD7=%02X sram $FFD8=%02X country $FFD9=%02X lic $FFDA=%02X ver $FFDB=%02X' % tuple(r[0xFFD5:0xFFDC]))
cc = r[0xFFDC] | r[0xFFDD] << 8; ck = r[0xFFDE] | r[0xFFDF] << 8
print('complement %04X checksum %04X xor %04X' % (cc, ck, cc ^ ck))
print('byte sum & FFFF = %04X' % (sum(r) & 0xFFFF))
# LoROM header location sanity: what is at 0x7FC0
print('7FC0 title', r[0x7FC0:0x7FD5])
# vectors
names = ['n_COP', 'n_BRK', 'n_ABORT', 'n_NMI', 'n_unused', 'n_IRQ']
for i, nm in enumerate(names):
    print(nm, '%04X' % (r[0xFFE4 + 2*i] | r[0xFFE5 + 2*i] << 8))
en = ['e_COP', 'e_unused', 'e_ABORT', 'e_NMI', 'e_RESET', 'e_IRQ/BRK']
for i, nm in enumerate(en):
    print(nm, '%04X' % (r[0xFFF4 + 2*i] | r[0xFFF5 + 2*i] << 8))
print('native unused FFE0-FFE3', r[0xFFE0:0xFFE4].hex(), 'emu FFF0-FFF3', r[0xFFF0:0xFFF4].hex())
for a in (0x0083D6, 0x0083D7, 0x008738, 0x008765, 0x808743):
    print('---- %06X' % a)
    v.show(r, a, 30)
