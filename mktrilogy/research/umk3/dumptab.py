"""Dump a per-fighter table: python3 -I dumptab.py ADDR WIDTH(1|2|4) [N]"""
import sys
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import u, snes
rom = snes.load('umk3')
N = ['Kano', 'Sonya', 'Jax', 'NWolf', 'SubZ', 'Stryk', 'Sindel', 'Sektor', 'Cyrax', 'KLao', 'Kabal', 'id11', 'Shang',
     'LiuK', 'Smoke', 'Kitana', 'Jade', 'Mileena', 'Scorp', 'Rept', 'Ermac', 'ClSZ', 'HSmoke', 'Noob', 'Rain', 'id25',
     'Motaro', 'Kahn', 'x28', 'x29', 'x30', 'x31']


def tab(addr, wdt, n=28):
    o = u.to_off(addr)
    out = []
    for i in range(n):
        if wdt == 1: out.append(rom[o + i])
        elif wdt == 2: out.append(snes.u16(rom, o + 2 * i))
        elif wdt == 3: out.append(snes.u24(rom, o + 3 * i))
        else: out.append(snes.u24(rom, o + 4 * i) | rom[o + 4 * i + 3] << 24)
    return out


if __name__ == '__main__':
    a = int(sys.argv[1], 16); wdt = int(sys.argv[2]); n = int(sys.argv[3]) if len(sys.argv) > 3 else 28
    v = tab(a, wdt, n)
    fmt = {1: '{:02X}', 2: '{:04X}', 3: '{:06X}', 4: '{:08X}'}[wdt]
    print(f'${a:06X} w{wdt}: ' + ' '.join(f'{N[i]}=' + fmt.format(x) for i, x in enumerate(v)))
