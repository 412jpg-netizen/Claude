# Research scripts

The static-analysis scripts behind `notes/`. They are kept so every claim in the notes can be
re-checked, not as polished tools. Each folder matches one notes file:

| folder | notes |
|---|---|
| `umk3/` | `notes/umk3-map.md` |
| `mk2/` | `notes/mk2-map.md` |
| `compat/` | `notes/compat.md` |
| `verify-umk3/`, `verify-mk2-compat/` | the two verification notes |
| `plan/` | `notes/PLAN.md` section 10 |
| `lib/snes.py` | shared helpers (two known bugs, see below) |

They expect the layout of the machine they were written on:

```
/home/claude/work/roms/{umk3,mk3,mk2}.sfc   your dumps (see tools/roms.py for the SHA-1s)
/home/claude/work/lib/snes.py               this folder's lib/snes.py
/home/claude/work/scripts/<folder>/         this folder's subfolders
/home/claude/work/out/<folder>/             PNG and text outputs (not kept here)
```

Run them with `python3 -I path/to/script.py`. They need `capstone`, `numpy` and `pillow`; the
build itself (`../build.py`) needs none of these.

Known problems in `lib/snes.py`: `to_off` treats banks `$FE`/`$FF` as WRAM, and `disasm` cannot
build capstone's 8-bit/8-bit mode. The `d65.py` copies in `umk3/` and `mk2/`, and
`../tools/d65.py`, avoid both.
