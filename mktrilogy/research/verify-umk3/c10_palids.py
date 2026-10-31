import sys; sys.path.insert(0, '/home/claude/work/scripts/verify-umk3'); import v
r = v.load('umk3')
names = ['Kano','Sonya','Jax','Nightwolf','SubZero','Stryker','Sindel','Sektor','Cyrax','KungLao','Kabal','id11','Shang','LiuKang','SmokeR','Kitana','Jade','Mileena','Scorpion','Reptile','Ermac','ClassicSZ','HumanSmoke','Noob','Rain','id25','Motaro','Kahn']
print('9D3F-9D23 =', 0x9D3F-0x9D23)
for i in range(28):
    a = v.u8(r, 0x889D23+i); b = v.u8(r, 0x889D3F+i)
    pa = v.u24(r, 0x889984+3*a); pb = v.u24(r, 0x889984+3*b)
    print('%2d %-10s pri $%02X (%3d) -> %06X   alt $%02X (%3d) -> %06X' % (i, names[i], a, a, pa, b, b, pb))
print('byte after 9D3F+27:', hex(v.u8(r, 0x889D3F+28)))
