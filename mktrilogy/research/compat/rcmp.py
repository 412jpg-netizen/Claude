"""Side-by-side comparison of two routines (linear disassembly, aligned on opcode sequence with difflib).
usage: python3 -I rcmp.py gameA addrA gameB addrB [n_insns] [m16 x16]
Markers:  '=' identical bytes, '~' same opcode, different operand, '<' / '>' only in A / only in B,
          '!' different opcode at an aligned position.
Prints a summary line: identical / same-opcode / differing instruction counts.
"""
import sys, difflib
sys.path.insert(0, '/home/claude/work/scripts/compat')
from c import lst


def compare(ga, aa, gb, ab, n=60, m16=True, x16=True, out=sys.stdout, quiet=False):
    A = lst(ga, aa, n, m16, x16, stop=False)
    B = lst(gb, ab, n, m16, x16, stop=False)
    sa = [d['op'] for d in A]
    sb = [d['op'] for d in B]
    sm = difflib.SequenceMatcher(None, sa, sb, autojunk=False)
    same = op = diff = 0
    rows = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                if A[i]['bytes'] == B[j]['bytes']:
                    m = '='; same += 1
                else:
                    m = '~'; op += 1
                rows.append((A[i], m, B[j]))
        else:
            for k in range(max(i2 - i1, j2 - j1)):
                a = A[i1 + k] if i1 + k < i2 else None
                b = B[j1 + k] if j1 + k < j2 else None
                m = '!' if (a and b) else ('<' if a else '>')
                diff += 1
                rows.append((a, m, b))
    if not quiet:
        for a, m, b in rows:
            ta = f"{a['pc']:06X} {a['bytes'].hex():<9} {a['text']:<16}" if a else ' ' * 40
            tb = f"{b['pc']:06X} {b['bytes'].hex():<9} {b['text']}" if b else ''
            print(f'{ta} {m} {tb}', file=out)
    print(f'summary {ga} ${aa:06X} vs {gb} ${ab:06X}: {len(A)}/{len(B)} insns, identical {same}, '
          f'same-opcode {op}, differing {diff}', file=out)
    return same, op, diff, rows


if __name__ == '__main__':
    ga, aa, gb, ab = sys.argv[1], int(sys.argv[2], 16), sys.argv[3], int(sys.argv[4], 16)
    n = int(sys.argv[5]) if len(sys.argv) > 5 else 60
    m16 = x16 = True
    if len(sys.argv) > 7:
        m16, x16 = sys.argv[6] == '1', sys.argv[7] == '1'
    compare(ga, aa, gb, ab, n, m16, x16)
