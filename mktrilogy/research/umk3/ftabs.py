"""Dump per-fighter tables (28 fighter IDs)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes
rom = snes.load('umk3')
N = ['Kano', 'Sonya', 'Jax', 'Nightwolf', 'SubZero', 'Stryker', 'Sindel', 'Sektor', 'Cyrax', 'KungLao', 'Kabal',
     'id11', 'Shang', 'LiuKang', 'Smoke', 'Kitana', 'Jade', 'Mileena', 'Scorpion', 'Reptile', 'Ermac', 'ClassicSZ',
     'HSmoke', 'Noob', 'Rain', 'id25', 'id26', 'id27']


def dump4(addr, n=28):
    o = u.to_off(addr)
    return [snes.u24(rom, o + 4 * i) | (rom[o + 4 * i + 3] << 24) for i in range(n)]


if __name__ == '__main__':
    for a in [int(x, 16) for x in sys.argv[1:]]:
        print(f'== table ${a:06X}')
        for i, v in enumerate(dump4(a)):
            print(f'  {i:2d} {N[i]:10s} {v & 0xFFFFFF:06X} hi={v >> 24:02X}')
