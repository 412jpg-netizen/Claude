# mktrilogy (SNES)

A private hack that turns your own **Ultimate Mortal Kombat 3 (SNES, USA)** dump into a
*Mortal Kombat Trilogy*-style game, with content taken from your **Mortal Kombat 3** and
**Mortal Kombat II** SNES dumps.

The repository holds only code and notes. `build.py` reads your ROM files, checks every patch
site before writing, and writes the patched ROM to `build/` (git-ignored). No IPS/BPS patch is
produced, because later milestones copy MK2/MK3 data and a patch file would contain it.

## Build

Python 3.8 or newer, nothing else.

```
python build.py --umk3 "path/to/Ultimate Mortal Kombat 3 (USA).sfc"             # 4 MB
python build.py --umk3 "path/to/Ultimate Mortal Kombat 3 (USA).sfc" --exhirom   # 8 MB
python build.py --umk3 ... --identity      # no patches: output must equal your dump
```

The build accepts only the known dumps (SHA-1s in `tools/roms.py`); a 512-byte copier header
is stripped automatically. Static self-tests:

```
MKT_UMK3=path/to/umk3.sfc python -m unittest discover -s tests -v
```

## Status

| milestone | state |
|---|---|
| M0 build pipeline, identity build | done, tests pass |
| M1 Motaro and Shao Kahn selectable from power-on | done, needs an in-game test |
| M2 8 MB ExHiROM, no content change | done (`--exhirom`), tests pass, needs an in-game test |
| M3 first MK3 stages restored | next |

Already in SNES UMK3 and needing no work: Rain, Noob Saibot, Classic Sub-Zero, Human Smoke,
Ermac, Mileena, Jade. The full plan, with difficulty ratings, is `notes/PLAN.md`; the verified
addresses and formats are in `notes/ROM-MAP.md`.

## In-game test checklist

Use Mesen 2 or bsnes-plus.

- **M1** (either build): start a two-player versus game and move a cursor into the empty
  middle cell of the select grid. Motaro or Shao Kahn should appear there without using the
  "Lost Treasures" menu. Watch `$7E:1C57`, `$7E:1C59`, `$7E:36C6` and `$7E:388A` if it does not.
- **M2** (`--exhirom` build): the emulator should report ExHiROM / 64 Mbit. Check that attract
  mode, the select screen and the VS screen look the same as the original. Then fight with Kano
  and Liu Kang, enter a few kombat kodes, and do some projectiles and finishers. Nothing
  should look different.

## Layout

```
build.py        pipeline: verify input -> content patches -> optional ExHiROM -> checksum
tools/          hirom.py (HiROM/ExHiROM mapping), checksum.py, roms.py, d65.py (65816
                disassembler used by patch guards), patch.py, sprites.py (UMK3 sprite sets)
patches/        one module per feature
tests/          static self-tests
notes/          PLAN.md, ROM-MAP.md, analyst maps and verification notes
research/       the analysis scripts behind notes/
```
