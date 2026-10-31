"""M1: Motaro and Shao Kahn selectable from power-on.

The reset path calls $80:8653 (JSL from $80:8469), which clears the kombat-kode flags and then
the two boss unlocks: STZ $3BAE (Kahn) and STZ $3BB0 (Motaro). The only other users of those
flags are the hidden-cell routine at $84:A328-$84:A383, which tests them for non-zero.

A still holds #$0001 from LDA #$0001 at $80:8656 (the loop between only stores, and STA $3BB6 /
STA $3BB4 right before rely on the same value), so turning each STZ into STA stores 1 instead of
0. Two opcode bytes change; nothing moves.

In game: the boss cell in the middle of the select grid opens once both players have joined
($36C6 and $388A non-zero), the same as after the "Lost Treasures" unlock.
"""
from tools.patch import Patch, expect_at
from tools.hirom import Rom
from tools import d65

NAME = 'boss_unlock'

PATCHES = [
    Patch('kahn unlocked at power-on', 0x8086B1, ['STZ $3BAE'], [0x8D, 0xAE, 0x3B]),
    Patch('motaro unlocked at power-on', 0x8086B4, ['STZ $3BB0'], [0x8D, 0xB0, 0x3B]),
]

# Instructions that may sit between the LDA #$0001 and the patched stores without changing A.
_A_SAFE = {'STZ', 'STA', 'DEX', 'BPL', 'LDX'}


def check_context(rom):
    expect_at(rom, 0x808653, ['LDX #$0002', 'LDA #$0001'], NAME)
    expect_at(rom, 0x8086AB, ['STA $3BB6', 'STA $3BB4', 'STZ $3BAE', 'STZ $3BB0',
                              'STZ $3BB2', 'RTL'], NAME)
    for d in d65.lst(rom, 0x808659, 40):
        if d['pc'] >= 0x8086B1:
            break
        if d['mn'] not in _A_SAFE:
            raise ValueError('%s: unexpected %s at $%06X changes A' % (NAME, d['text'], d['pc']))


def apply(data, mapper):
    check_context(Rom(data, mapper))
    return [(p.name, p.apply(data, mapper)) for p in PATCHES]
