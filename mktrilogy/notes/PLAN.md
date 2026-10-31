# mktrilogy (SNES): build plan

This plan is for a private SNES hack, built from the user's own cartridge dumps, that turns
**Ultimate Mortal Kombat 3 (SNES)** into a *Mortal Kombat Trilogy*-style game. Content comes from
**Mortal Kombat 3 (SNES)** and **Mortal Kombat II (SNES)**.

Inputs:
- `notes/umk3-map.md`, `notes/mk2-map.md`, `notes/compat.md` (analyst maps);
- `notes/verify-umk3.md`, `notes/verify-mk2-compat.md` (independent verification);
- a few extra static checks I ran while writing this plan (section 10; scripts in
  `/home/claude/work/scripts/plan/`, outputs in `/home/claude/work/out/plan/`).

The companion reference is `notes/ROM-MAP.md`, which lists every address and format with a status of verified or open.

Ground rules that shaped this plan:
- Everything so far is **static analysis**. Nothing has been emulated. Every in-game test below is
  meant for the user's PC.
- A claim is only treated as solid if the verifiers said it **holds**. Claims marked partly,
  refuted or unverifiable are treated as open. LIKELY claims stay LIKELY.
- No game data goes into the repository. The build reads the user's ROM files and writes the
  patched ROM (section 5).

---

## 1. Summary: what is feasible and how hard

| Group | Content | Verdict |
|---|---|---|
| Already in SNES UMK3 | Rain, Noob Saibot, Classic Sub-Zero, Human Smoke, Ermac, Kitana, Jade, Mileena, Reptile, Scorpion | **Already done.** Rain and Noob have grid cells, portraits, palettes and animation tables (verified C4). Their move sets were not audited. Motaro and Shao Kahn are playable behind a menu unlock (verified C15). |
| Easy | Bosses selectable from power-on; a debug select override for testing | A few bytes of patch plus a small hook (M1). |
| Easy-medium | ExHiROM expansion to 8 MB | The recipe is known. One extra data fix was found by verification: 9 tile-directory bank bytes (M2). |
| Medium | Restoring MK3 stages that SNES UMK3 dropped | MK3 is the same engine generation, and two dead UMK3 stage records can be reused in place (M3). |
| Medium | Chameleon in spare slot 25 | Built on the existing male-ninja machinery (M5). |
| Hard | Sheeva (back in her old slot 11) | Her graphics copy across as they are (same sprite codec). Her move code has to be ported from MK3 code, which is close to UMK3's but has not been mapped (M7). |
| Hard | Bigger select screen | The 24-cell grid is full. A new grid needs new 8bpp art under a shared 96-colour palette (M6). |
| Very hard | MK2 fighters: Baraka, Johnny Cage, Raiden, Kintaro, optionally MK2 Jax and Kung Lao | See below (M9-M12). |
| Hard | Aggressor meter | Damage and shadow-trail hooks were found (section 10). The HUD and the speed boost are unmapped (M14). |
| Very hard / stretch | Goro, MK1 Kano and Raiden, MK1 stages, Animalities | None of the three ROMs holds their art, except MK3 animality art for MK3's own cast. |

### Why the MK2 fighters are very hard

The **data** converts mechanically:
- the LZ decompressor is identical (verified T2-1);
- the sprite headers, frame bytes and raw tiles use the same format (verified T2-2);
- compressed tiles need a one-byte-per-group converter that was tested lossless on all 17 MK2 sets
  (verified T2-3).

The **behaviour** does not convert:
- MK2 object RAM has a different layout: 11 slots with `$16`-byte strides, against 12 slots with
  `$18`-byte strides (verified T2-5).
- MK2 code can therefore not run unchanged. Code-skeleton similarity is only 14-20%, against 67.6% for
  MK3 (unverifiable T1-7; treat it as indicative).
- UMK3 has 76 animation slots per fighter, against 66 in MK2, and the numbering differs after about
  the first 6 (T2-7, LIKELY). My inference, still open: the extra slots are UMK3-only actions such as
  running, which MK2 had no button or frames for, so they will need substitute frames.
- **UMK3's own move, special, AI and sound systems are not mapped at all yet.**

So every special move, projectile, fatality, friendship, babality, brutality, combo and AI routine for
each MK2 fighter has to be **written new** in 65816 assembly against an engine that is not yet
documented. That is the bulk of the whole project, and it is why milestone R1 (map UMK3's move system)
sits in front of every new-fighter milestone.

---

## 2. Target feature list vs Mortal Kombat Trilogy (PS1/N64)

What MKT contained is outside knowledge and marked **LIKELY**. It differs between the PS1 and N64
versions; the user's PS1/N64 copies can settle the exact lists (section 8). "Map says" cites the
verified map unless marked open.

| # | Feature (MKT) | SNES UMK3 today | What the map says it takes | Source data | Difficulty | Milestone |
|---|---|---|---|---|---|---|
| 1 | Rain | Full fighter: ID 24, grid cell 0, VS portrait, palettes `$75`/`$86` (verified C4, C10) | Nothing. Optionally audit his moves. | in base | none | (R1 audit) |
| 2 | Noob Saibot | Full fighter: ID 23, grid cell 6, palettes `$74`/`$88` (verified C4) | Nothing | in base | none | – |
| 3 | Classic Sub-Zero, Human Smoke, Ermac and the other UMK3 additions | IDs 15-22. Human Smoke (22) has no grid cell; how he is selected is open | Nothing, apart from putting Human Smoke on a new grid if wanted | in base | none / medium | M6 |
| 4 | **Sheeva** | Removed. ID 11 and set 11 are empty (verified C6); `$83:F29D`[11] = `$83:FC9E` is a leftover routine (verified C-U3) | Copy MK3 set 11 (header `$86:9B3F`, 204 frames, about 210 KB; verified T1-2) to the new banks. Palettes MK3 `$4A`/`$4B`. Animation tables (numbering 0-52 matches UMK3, section 10 P2). VS portrait MK3 `$C9:0000` (verified). Select portrait from the MK3 select screen. Name. **Port her MK3 move code** (location open) | `mk3.sfc` | hard | M7 |
| 5 | **Chameleon** (PS1: male ninja that cycles ninja colours and moves) | ID 25 is a spare male ninja: set 27, scripts `$85:8010`, Scorpion palettes, Scorpion's VS art, no name, no cell (verified C7) | Palette-cycling hook through the existing palette path (`$88:9874` → `$85:CD14`; verified C9). Move borrowing (proposal in M5). Name string. Grid cell (M6) | in base | medium | M5 |
| 6 | **Khameleon** (N64: female equivalent, LIKELY) | none | Same idea on the female-ninja set 26 / scripts `$85:CE40` (verified C8). Needs a new ID ≥ 28 | in base | medium (after M8) | M15 |
| 7 | **Baraka** | none | Convert MK2 set 3 (about 159 KB; verified C14), palettes, scripts with remap; all move/AI code new; portraits; sounds | `mk2.sfc` | very hard | M9-M10 |
| 8 | **Johnny Cage** | none | Same, MK2 set 2 (about 167 KB) | `mk2.sfc` | very hard | M11 |
| 9 | **Raiden** | none | Same, MK2 set 6 (about 192 KB). His lightning uses 16 frames of effect set 13 directly (mk2-map 6) | `mk2.sfc` | very hard | M11 |
| 10 | Classic MK2 **Jax** and **Kung Lao** (PS1 MKT, LIKELY) | none | Same as the donors: MK2 set 8 (201 KB) and set 0 (186 KB) (mk2-map 6, single-source sizes) | `mk2.sfc` | very hard | M11 (optional) |
| 11 | Classic MK1 Kano and Raiden (PS1 MKT, LIKELY) | none | No source in the three ROMs | MK1 SNES or PS1 art | very hard | M16 (stretch) |
| 12 | **Kintaro** (boss, playable) | none | MK2 set 9 (about 140 KB). Frame sizes fit (verified T2-8: 106 tiles/39 pieces, against Motaro's 106/62). Boss AI and ladder placement new | `mk2.sfc` | very hard | M12 |
| 13 | **Goro** | none | No source in the three ROMs | MK1 SNES or PS1/N64 art | very hard | M16 (stretch) |
| 14 | **Motaro and Shao Kahn playable** | Yes, after "LOST TREASURES" menu items set `$3BB0`/`$3BAE`. Hidden cell 10 opens only when `$36C6` and `$388A` are both non-zero (verified C15; LIKELY means two players) | Unlock at power-on: hook the init clears at `$80:86B1`/`$80:86B4` (section 10 P4). One-player use: lift the `$36C6`/`$388A` gate (risk: ladder logic) | in base | easy / medium | M1 |
| 15 | **Aggressor meter** | none | New per-player meter, HUD graphics, fill logic, boost. Existing hooks: the damage scaler at `$84:E829` and the per-object shadow-trail bit `$5538,X` bit `$20` (section 10 P5, LIKELY). HUD and speed systems are open | new code and art | hard | M14 |
| 16 | **Brutalities** | LIKELY already present: kode 45 announces one-button brutalities and sets `$3A78` bit 3 (verified C19 handler list) | New fighters need their own brutality inputs. The explosion is LIKELY shared | in base | part of each fighter | M10+ |
| 17 | Fatality / Friendship / Babality for new fighters | Babality frame table `$85:AEBA` and palette `$88:9DE5` (single-source, LIKELY) | Per-fighter code and art. MK2 has babality art for its cast (the "BABALITY" string is at MK2 `$C3:D958`) | `mk2.sfc` | part of each fighter | M10+ |
| 18 | Animalities and Mercy | Absent: the MK3 animality sprites are not in UMK3 (verified T1-3, partly; the set-21 animal frames are absent). MERCY banner frames 206-212 are absent | MK3 art covers only MK3's cast. MK3-only code would need porting | `mk3.sfc` | very hard | M16 (stretch) |
| 19 | **MK3 stages back**: Subway, Street, Bank, Balcony, Bridge, Soul Chamber, Kahn's Tower, Temple, Vortex sky | Dropped (verified T1-4, partly: 0-1.4% tile overlap). Only Rooftop and Pit 3 remain | Copy MK3 record streams (same LZ, same descriptor types). Records 7 and 8 are dead and have private descriptors that can be rewritten in place (section 10 P6). More stages need the record table moved out of bank `$84` | `mk3.sfc` | medium | M3 |
| 20 | **MK2 stages**: Dead Pool, Kombat Tomb, Wasteland, Tower, Living Forest, Armory, Pit II, Portal, Kahn's Arena, Goro's Lair (LIKELY stage 9) | none | LZ streams usable as they are (verified T2-1). Container converter MK2 record → UMK3 records and type-0 descriptors. UMK3 fight-stage metatile format **open**. Props and animations unmapped | `mk2.sfc` | hard | M13 |
| 21 | MK1 stages | none | No source in the three ROMs | PS1/N64 art | very hard | M16 (stretch) |
| 22 | Bigger select screen | 24 cells, all used; hidden cell 10 for bosses (verified C14) | New grid, direction and blocked tables, cursor positions, 8bpp BG art under the 96-colour block at CGRAM 48 (verified C16 select part) | portraits from all ROMs | hard | M6 |
| 23 | Endings, bios, "X WINS" names, ladder portraits for new fighters | Unmapped (umk3 open questions) | Locate first | – | open | R2 |
| 24 | Voices and SFX for new fighters | Sound system unmapped. About 55-66 KB of MK3-only BRR-like data (T1-6, LIKELY) | Locate the driver and sample directory; measure the ARAM budget | `mk3.sfc`, `mk2.sfc`, PS1 audio | open / hard | R3 |

---

## 3. Fighter-ID and slot allocation

| ID | Use | Why |
|---|---|---|
| 0-10, 12-24 | unchanged | |
| 11 | **Sheeva** | Her MK3 slot. UMK3 tables already have an (empty) entry 11 everywhere. Re-point `$83:F29D`[11] (verified C-U3) |
| 25 | **Chameleon** | Already a male ninja with animation table and VS entry (verified C7) |
| 26, 27 | Motaro, Shao Kahn | unchanged |
| 28+ | Kintaro first (boss), then Khameleon, Baraka, Johnny Cage, Raiden, optional MK2 Jax/Kung Lao | Needs M8 |

Why Kintaro is a good first ID 28: heuristic scanning found five `CMP #$001A ; BCS` "ID ≥ 26 means
boss" tests (section 10 P1). A boss at 28 gets those boss branches for free. Every non-boss fighter at
28+ needs those sites patched. Sprite sets follow the same plan: set 11 for Sheeva, sets 28+ for new
fighters. The tables `$86:EAEC`/`$86:EB24` hold 28 entries (verified C8), so they must be relocated
(M4).

---

## 4. ROM expansion approach

**Decision: 8 MB ExHiROM**, not 6 MB.
- The 8 MB layout avoids the 6 MB checksum-convention question.
- MK2's 3 MB dump shows the dumps follow the mirrored-sum convention (section 10 P7), so a 6 MB image would by analogy use sum(4 MB) + 2 × sum(last 2 MB). That is LIKELY, and not needed with 8 MB.

Recipe (compat 4.4, with the verifier's fix, verified C22 partly and T4-2/T4-3):

1. Start from the 4 MB file and pad to 8 MB.
2. Copy file `0x008000`-`0x00FFFF` to `0x408000`-`0x40FFFF`. This covers the header, the vectors and
   every bank-`$00` instruction that ever executes: `$83D6`-`$83EE`, `$8738`-`$873F` and `$8765`
   (verified C2/C22).
3. Patch the **9 tile-directory bank bytes** (`$00`-`$07` to `$C0`-`$C7`) at file `0x3FB3F5`, `0x3FB42D`,
   `0x3FB832`, `0x3FC68F`, `0x3FC52F`, `0x3FCAD3`, `0x3FD4ED`, `0x3FC727` and `0x3FC841` (verified T4-2).
   Without this, Kano, Liu Kang (stance included) and effect sets 17/18/20/21/24/25 draw garbage.
4. Header at `0x40FFC0`: map mode `$35`, ROM size `$0D`, checksum over the 8 MB image. No code reads
   the header in the traced code (verified C22 code side).
5. New data goes in banks `$40`-`$7D`. Rules:
   - Never address tile data through `$00`-`$3F`: the tile fetch does `PLB` + `LDA $0000,Y`
     (verified T4-3).
   - Keep every tile group inside one 64 KB bank.
   - File `0x7E0000`-`0x7FFFFF` is reachable only as `$3E`/`$3F:8000+`; keep it for non-tile data.
6. New code. Constraints:
   - Every new byte lives in the **SlowROM** half. Banks `$40`-`$7D` and `$00`-`$3F` map the upper 4 MB
     at 2.68 MHz access speed; only `$80`-`$FF` is FastROM. This is standard SNES behaviour, LIKELY to
     matter for per-frame tile fetch of new fighters (see risks).
   - Hot new code should go in the 9,106 free bytes at `$FF:DC6E` (fast, verified C21).
   - Hooks go only in the `$FF` runs at the ends of banks `$C0`-`$C7`. The bytes after each run are
     tile data (verified C-U5).
   - If fast space runs out, move cold existing data (e.g. ending art) to the upper 4 MB and re-point
     it, to free fast space.
7. **Bank-relative 16-bit pointers limit placement** (single-source facts, consistent with the verified
   readers). The following need code patches before their data can move or grow:
   - stage records and layer descriptors (words in bank `$84`, verified C17);
   - names (words in bank `$83`, verified C3);
   - kode messages (bank `$85`);
   - animation scripts (same bank as their table).

---

## 5. Build-pipeline design

**Principle: the repository contains only our code, hand-written tables and notes.** At build time a
script reads the user's own ROM files, extracts and converts what it needs in memory, and writes the
patched ROM into an ignored folder.

```
mktrilogy/
  README.md
  notes/                PLAN.md, ROM-MAP.md, the maps and verification notes
  tools/                python, stdlib + numpy/pillow only
    hirom.py            address mapping (HiROM and ExHiROM; banks $FE/$FF are ROM, unlike lib/snes.py)
    d65.py              capstone-free 65816 disassembler (from scripts/umk3 or verify-umk3/v.py)
    asm65.py            minimal 65816 assembler built from the d65 opcode table; round-trip tested
    lz.py               decompressor (verified port) + a compressor (new; round-trip tested)
    sprite.py           UMK3/MK3/MK2 set reader, renderer, MK2->UMK3 tile-group converter (compat 2.2)
    anim.py             script reader/writer with command-aware parsing (FFF8 = byte+word, not aligned)
    stage.py            record/descriptor reader; MK3 copier; later the MK2 converter
    alloc.py            bank allocator for $40-$7D (one-bank tile groups, no $7E/$7F file area for tiles)
    checksum.py         SNES checksum, incl. mirrored sizes (tested on all three inputs)
  patches/              one python module per feature: hook asm text + table edits + "expect" guards
  content/              hand-authored data only: ID allocation, names, Chameleon cycle order,
                        select-grid layout (cell -> ID, coordinates), anim remap tables
  build.py              verify -> extract -> convert -> allocate -> patch -> header/checksum -> self-test
  tests/                static self-tests (no emulator)
  config.example.toml   paths to the user's ROMs (the real config.toml is git-ignored)
  .gitignore            *.sfc *.smc *.bin build/ out/ config.toml renders/
```

Pipeline steps:

1. **Verify inputs** by SHA-1. Refuse unknown dumps with a clear message:

   | ROM | SHA-1 | CRC32 |
   |---|---|---|
   | UMK3 | `09c094ca1114bcb6d5917e989686ca79b96cf9ea` | `F5BFE41E` |
   | MK3 | `58e4e1259a86faaadbc982176e569cb2038dbac5` | `4E6AF725` |
   | MK2 | `f6aa5291759e982ea249c4b76f729ca2f4ab1cf4` | `70BB5513` |

   Source: `scripts/plan/checksum.py` → `out/plan/checksum.txt`.
2. **Patch guards instead of stored bytes.** Each patch asserts what it expects at its site as
   disassembly text, e.g. "`$80:86B1` is `STZ $3BAE`", or as a hash of the original range. No ROM bytes
   are copied into the repo.
3. **Extract and convert in memory**:
   - MK3 sets and stage streams are copied verbatim, with pointers re-based.
   - MK2 sets go through the tile-group converter, which is verified lossless (compat 2.2).
   - Scripts go through the remap tables in `content/`.
4. **Allocate** with a deterministic first-fit allocator that respects the bank rules (section 4).
   Same inputs give byte-identical output.
5. **Patch**: assemble hooks with `asm65.py`, write tables, re-point readers. Every relocated table
   keeps its old copy in place, so a reader we missed still sees correct data for IDs 0-27.
6. **Header and checksum.**
7. **Self-tests**, all static:
   - every pointer we wrote resolves to mapped ROM;
   - no tile group crosses a bank;
   - every frame of every new or moved set decodes through the *UMK3* decoding path to the same pixels
     as the source game's decoder;
   - every new LZ stream decompresses exactly (final pointer 0);
   - the free-space report;
   - an ExHiROM re-decode of all 917 frame-referenced directory entries is identical to HiROM.
8. **Outputs** (all git-ignored):
   - `build/mktrilogy.sfc`;
   - a symbol file for emulator debuggers (labels for our hooks and tables);
   - `build/report.txt` (sizes, free space, what changed).

Distribution: none. The user builds locally from their own dumps. No IPS/BPS patch is produced, because
a patch file would embed MK2/MK3 data.

---

## 6. Milestones (in order; easiest real win first)

Format for each: goal · work · depends on · difficulty · static test (here) · emulator test (user's PC)
· exit criterion. Emulator suggestion for the user: Mesen 2 or bsnes-plus. Both have the read/write
breakpoints, memory viewer, VRAM/tilemap viewers and (Mesen) SPC debugger and profiler used below. I
cannot run them; the user installs them on their PC.

### M0. Build pipeline and identity build (easy)

- **Work**: repo skeleton, input verification, `hirom.py`, checksum, patch-guard mechanism, symbol
  output.
- **Depends on**: nothing.
- **Static test**:
  - a build with no patches reproduces the input SHA-1;
  - `checksum.py` reproduces `$64E9`, `$7149` and MK2's mirrored `$7221`;
  - `asm65.py` round-trips every instruction in the UMK3 trace.
- **Emulator**: none.
- **Exit**: all of the above pass.

### M1. Bosses selectable from power-on, plus a debug select override (easy; first real win)

- **Work**:
  1. The init routine at `$80:8653` (called by `JSL` from `$80:8469`) clears the kode flags and then
     `STZ $3BAE` / `STZ $3BB0` at `$80:86B1`/`$80:86B4` (section 10 P4). Replace the two 3-byte `STZ`
     with a `JSL` to a hook in the `$C0:FF1F` `$FF` run that stores 1 to both flags, plus `NOP`s. The
     two `STZ` are 6 bytes, the `JSL` is 4.
  2. Debug build option: hidden cell 10 always open and mapped to a configurable fighter ID. This means
     patching the `$86:A726` gate (`$1C57 == 1`, `$F5A6 == 0`) and the `$1C59` value returned by
     `$86:A203` (verified C5/C15).
- **Depends on**: M0.
- **Static test**:
  - the guards match;
  - a disassembly of the patched sites shows the intended code;
  - the hook sits wholly inside the `$FF` run.
- **Emulator**:
  1. Two-player versus: move a cursor into the centre cell and confirm Motaro and Kahn without the
     menu. Watch `$1C57`, `$1C59`, `$36D0`/`$3894`.
  2. Check whether the cell opens in one-player mode (it should not, if `$36C6`/`$388A` mean "both
     players joined"; watch them).
  3. Return to the title and repeat, to learn whether `$80:8653` runs only at power-on.
  4. Debug build: select ID 25, ID 22 (Human Smoke), and ID 11 (expected to fail; it shows what breaks).
     These answer open questions cheaply (section 7).
- **Exit**: bosses selectable from power-on in versus mode.
- **Optional M1b** (medium): allow bosses in one-player mode. Risk: ladder and ending logic for a boss
  as player 1 is unmapped.

### M2. ExHiROM 8 MB with no content change (easy-medium)

- **Work**: the section 4 recipe.
- **Depends on**: M0.
- **Static test**:
  - an ExHiROM-mapper re-decode of all 917 frame-referenced tile-directory entries is byte-identical to
    the HiROM decode;
  - every pointer table in ROM-MAP resolves to the same file offsets as before.
- **Emulator**: the emulator detects ExHiROM; the game boots; attract mode, select screen and VS screen
  look the same. Then:
  - fight with **Kano** and **Liu Kang** (they use patched groups);
  - enter several kombat kodes (their banners are in set 21, which has a patched group);
  - do projectiles and finishers, to exercise the effect sets 17/18/20/24/25, whose exact contents are
    unknown;
  - compare screenshots with the original ROM.
- **Exit**: no visible difference.

### M3. First new content: two MK3 stages in UMK3 records 7 and 8 (medium)

- **Work**:
  1. **Decode the type-0 descriptor and the fight-stage metatile format** (`$84:913E`, `$84:9AB8`,
     `$84:9C87`; open). Plain-tilemap renders of fight stages come out as noise (section 10 P9), so
     without this decode there is no static check and fields could be missed.
  2. Copy the chosen MK3 record's streams into `$40`+ banks.
  3. Rewrite UMK3's private descriptors for rec 7 (`$84:8946` type 0, `$84:89B6` type 1) and rec 8
     (`$84:8752`, `$84:8786` type 0, `$84:87B0` type 1), and the record parameters (`+$10`..`+$20`)
     (section 10 P6).
  4. Decide whether MK3's extra layer `$F6:0000` (40 tiles, used by most MK3 fight records, absent in
     UMK3; verified T1-4) is needed.
  5. Make the stages reachable: `$3A84` = 7/8 maps to records 7/8 (verified C17). For testing, re-point
     one kombat-zone kode (kodes 38-43 set `$3A84`; verified C19). Stage names need `$85:EE32`
     extended (7 entries).
  6. Pick stages **without** stage fatalities or uppercut transitions first. Which MK3 stages have
     special logic is open (section 7).
- **Depends on**: M2.
- **Static test**:
  - render UMK3 Rooftop (rec 0) and MK3 Rooftop (rec 3) with the new decoder: they must match except
    for the MK3-only `$F6` layer;
  - then render the transplanted records.
- **Emulator**:
  - enter the test kode, fight a full match, check both layers scroll correctly and the floor height
    is right;
  - compare against `mk3.sfc` running the same stage;
  - watch `$3A7E` and `$3A84`.
- **Exit**: two restored MK3 stages playable.
- **Follow-up (M3b)**: relocate the record table out of bank `$84` (patch `$84:8FC8` and the
  descriptor loop at `$84:9081`) to add the other six stages and the Vortex sky.

### R1. Map UMK3's fighter move system (hard; research, mostly static, some emulator)

Prerequisite for M5 (partly), M7 and M9-M14. Items to map:
- special-move input dispatch (MK2's is `$81:A943` with 8 per-event tables, verified C19 partly; find
  UMK3's counterpart via the compat code-skeleton pairs);
- move-routine conventions and projectile spawning;
- hit and attack boxes (the 4-byte box table is known, verified T2-4; attack boxes are not);
- reactions, dial-a-combo tables, finisher framework (fatality, friendship, babality, brutality);
- AI;
- meanings of UMK3 animation slots 53-75 (where MK3 and UMK3 diverge, section 10 P2);
- UMK3-only script commands `$FFF6`-`$FFEA`.

Write `notes/umk3-moves.md` with the same tagging rules plus independent verification.

- **Emulator help**: breakpoint on the frame-ID writes (`$52F8,X`) when a special starts, and read the
  call stack.

### M4. Per-fighter table inventory and relocation infrastructure (medium)

- **Work**:
  1. **Complete inventory**. Data-flow from `$52C8`/`$36D0`/`$3894` loads through `ASL`/`TAX` into
     `abs,X`/`long,X` reads (extend `scripts/umk3/ftabs.py`), plus the 42 ID-compare sites already
     found (section 10 P1).
  2. Relocate the tables that must grow, into fast space where it is hot:
     - palette table (readers `$85:CDA2`/`$85:CDA8` only, verified C11);
     - primary/alt palette IDs `$88:9D23`/`$88:9D3F` (readers `$88:9874` path, `$82:9D59`, `$86:C90E`);
     - set tables `$86:EAEC`/`$86:EB24` (readers `$88:A483`/`$88:A489` + any others found);
     - animation tables `$88:95C3`/`$88:9633` (readers `$88:95A0`/`$88:9576`, verified C-U1);
     - names `$83:E544` (reader `$83:E363`);
     - VS tables `$83:EE92`-`$83:EFE6` (readers `$83:E730`/`$83:E808`).
  3. Keep the old copies in place.
- **Depends on**: M2.
- **Static test**:
  - no traced reader still references an old copy;
  - the new copies are byte-equal to the old ones for IDs 0-27.
- **Emulator**: full regression (every fighter's stance, mirror match palettes, VS screen, a kode
  battle).
- **Exit**: identical behaviour with relocated tables.

### M5. Chameleon in slot 25 (medium)

- **Work** (proposal, LIKELY workable):
  - Keep the "real" identity (ID 25) in a new per-player RAM byte.
  - While the fighter is idle, switch `$52C8,X` between the male-ninja IDs 18-24 on a timer and reload
    the palette through `$88:9874`. Moves, `$FFF8` script branches and specials then follow the active
    ninja automatically.
  - Name, win text and announcer read the real identity.
  - Add "CHAMELEON" to the name table. There are about 100 free bytes in bank `$83` at `$C3:FF8E`
    (verified C21).
  - The VS entry already shows ninja art; point its palette at a suitable ninja VS palette.
  - Select via the M1 debug cell until M6.
- **Depends on**: M1 (debug select), M4 (only if a new palette or name table growth is needed), and R1
  findings on where `$52C8,X` is cached (switching mid-move must be avoided).
- **Static test**: hook disassembly; the timer only fires in the idle animation.
- **Emulator**:
  - colours cycle only while idle;
  - each colour's specials work;
  - mirror match against Scorpion;
  - the win screen shows Chameleon;
  - no crash when hit during a switch.
- **Exit**: playable Chameleon via the debug cell.

### M6. Select screen v2 (hard)

- **Work**:
  - New grid layout in `content/`: cells → IDs and screen coordinates.
  - Bigger grid table plus up/down/left/right and blocked tables (verified C14).
  - Cursor positioning: the current code steps x ±50 and y ±64 (verified C14), so a non-uniform
    layout needs a per-cell coordinate table.
  - Random-select scripts (`$86:A91F`/`$86:A953`, single-source).
  - New 8bpp BG built at build time from portraits cut out of the ROMs:
    - UMK3 select BG for existing fighters (verified C16 select part);
    - the MK3 select screen for Sheeva;
    - MK2 portraits (location open);
    - PS1/N64 portraits as an option (section 8).
  - Everything quantized into the 96-colour block at CGRAM 48. Pixels are offset by +48 through
    `$84:9703` (verified C16).
  - Budget: the current BG is 626 8bpp tiles (about 40 KB of VRAM).
- **Depends on**: M2, M4.
- **Static test**: render the new BG with the select-screen renderer; check the tile count against
  VRAM; check that the direction tables are consistent (every cell reachable, moves are inverse pairs
  where intended).
- **Emulator**: walk every cell with both cursors; confirm the chosen ID in `$36D0`/`$3894`; check the
  hidden-cell boss logic still works; random select.
- **Exit**: all intended fighters selectable from the grid.

### M7. Sheeva (hard)

- **Work**:
  - Graphics: copy MK3 set 11 group by group into `$40`+ (same codec; MK3 tile-directory banks are all
    ≥ `$C9`, section 10 P2).
  - Palettes `$4A`/`$4B` into the relocated palette table.
  - Animation tables:
    - MK3 has 65 common entries, UMK3 76;
    - entries 0-52 agree for 13 shared fighters (section 10 P2), so copy those;
    - map or substitute 53-75 using R1.
  - Script commands: re-point `$FFFA` code pointers to ported code; remap `$FFF9` sound IDs (R3).
  - **Move code**:
    - locate MK3's per-fighter dispatch entries for ID 11 and walk the call graph inside the MK3-only
      code ranges (`out/compat/attrib_mk3.txt`);
    - first check whether MK3 object RAM equals UMK3's (same method as compat T2-5);
    - also disassemble `$83:FC9E`, UMK3's leftover routine for ID 11 (verified C-U3), which may be a
      Sheeva remnant (LIKELY).
  - Portraits: VS from MK3 `$C9:0000` (verified); select from MK3 select BG.
  - Name, AI, sounds.
- **Depends on**: M2, M4, R1, M6 (normal selection; the debug cell works earlier), R3 (sounds).
- **Static test**:
  - all 204 frames render identically through the UMK3 path after relocation;
  - every script frame word points into set 11;
  - every `$FFFA` target is inside ported code.
- **Emulator**: debug-select ID 11; every normal and special move; throws; fatalities; mirror match;
  vs CPU (AI); the ladder.
- **Exit**: Sheeva complete and stable.

### M8. Fighter IDs 28 and above (medium-hard)

- **Work**:
  - Extend every inventoried table (M4).
  - Patch the boss-range tests `CMP #$001A ; BCS` at `$85:9ADE`, `$85:9C5E`, `$85:9F99`, `$85:E6D7` and
    `$88:AB0B` for non-boss IDs.
  - Review `CMP #$000F ; BMI` at `$80:9945` and the "ID ≥ 15" rule in `$82:9D59` (verified C9 extra).
  - Review `CMP #$001E ; BMI` on `$36D0` at `$85:99D2` (meaning open). All sites: section 10 P1.
  - VS tables (26 entries) and the name table need growth.
- **Depends on**: M4.
- **Static test**: no traced indexed read can run past a table end for IDs up to the new maximum.
- **Emulator, "clone test"**: make ID 28 an exact clone of Scorpion (18) in every table. It must
  behave identically to Scorpion: moves, palette, VS, win, ladder. Any difference points to a missed
  table or check.
- **Exit**: the clone is indistinguishable.

### M9. MK2 data converter and a "puppet" fighter (medium)

- **Work**:
  - Offline: convert Baraka's set (tile groups per compat 2.2, frame tables re-based, palettes).
  - Build an animation-number remap for MK2's 66 → UMK3's 76 entries (open; method `animcmp.py`
    plus manual labelling).
  - Convert scripts:
    - frame words: set number;
    - `$FFFF`: targets;
    - `$FFF8`: fighter ID and target;
    - `$FFF9`: sound IDs, stubbed until R3;
    - `$FFFA`: code pointers, stubbed.
  - Puppet: the ID-28 clone from M8 with Baraka's set and converted stance/walk/jump/reaction scripts
    on top of ninja moves.
- **Depends on**: M8 (or the debug cell on a scratch ID), M4.
- **Static test**:
  - converted frames decode through the UMK3 path to the same pixels as MK2's decoder (already 0
    mismatches in `convert_test.txt`);
  - frame sizes are within UMK3's observed maxima (verified T2-8).
- **Emulator**:
  - Baraka appears and animates;
  - VRAM viewer: no tile-buffer overflow in his largest frames;
  - check for slowdown with tile data in SlowROM banks (Mesen profiler).
- **Exit**: puppet works without glitches or slowdown.

### M10. First complete MK2 fighter: Baraka (very hard)

- **Work**: everything R1 mapped, written new for Baraka:
  - specials and projectiles (effect-frame attribution is open, mk2-map open question 1);
  - fatalities, friendship, babality, brutality, combos;
  - AI, sounds (R3), portraits (M6), name and ending.
  - MK2 move code is used only as a behaviour reference: timings, velocities and inputs, e.g. his real
    input checks `$81:B094`/`$81:B065` (verified C19 partly).
- **Depends on**: M9, R1, R3, M6.
- **Static test**: script and pointer checks as in M7.
- **Emulator**: full move list, CPU matches, mirror match, all finishers.
- **Exit**: Baraka playable end to end.

### M11. Johnny Cage, Raiden; optional MK2 Jax and Kung Lao (very hard each)

The same framework as M10. Each is cheaper after Baraka, but every move is still new code.

### M12. Kintaro: boss and playable (very hard)

Boss AI, the ladder slot (unmapped) and a boss stage (Goro's Lair from M13 if wanted). He benefits from
the `ID ≥ $1A` boss tests if placed at ID 28 (section 3).

### M13. MK2 stages (hard)

- **Work**: a converter from the MK2 record (`$82:EDFC` + `$82:EF50`; 192-byte palette, 12 metatile
  map blocks; verified mk2:C17) to the UMK3 type-0/1 container decoded in M3. Map props and
  animations (Dead Pool acid, Kombat Tomb spikes) and stage fatalities, all unmapped.
- **Depends on**: M3 and M3b.
- **Exit**: MK2 stages selectable and rendering correctly.

### M14. Aggressor meter (hard)

- **Work**:
  - per-player meter state;
  - fill on damage dealt, by hooking the damage scaler `$84:E829`, which already halves or doubles the
    damage value in DP `$32` for the 2X HEALTH and 2X DAMAGE kodes (section 10 P5);
  - when full: double damage for that attacker; set the shadow-trail bit `$5538,X` bit `$20` (set
    today at `$85:C656` when SHADOW FIGHTING is on);
  - speed boost (the HYPER KOMBAT consumer is not found);
  - HUD bar graphics and rendering (unmapped; the run meter is a candidate to study).
- **Depends on**: R1 and HUD mapping.
- **Exit**: meter fills, triggers and expires correctly for both players.

### M15. Khameleon (medium, after M5 and M8)

M5's switching scheme on the female-ninja IDs 15-17 (set 26), at a new ID.

### M16. Stretch goals (very hard)

- Animalities and Mercy for MK3's cast (MK3 set 21 art plus MK3-only code; new fighters have no art).
- Goro, MK1 Kano and Raiden, and MK1 stages: art from MK1 SNES (not available) or from PS1/N64
  (section 8).
- Endings and bios for all new fighters.

### R2 and R3. Research milestones that unblock "finish" work

- **R2**: win names, endings and bios text, ladder ("choose your destiny") data. Needed by M5, M7 and
  M10+.
- **R3**: sound driver, sample directory, SFX/voice IDs, ARAM budget. Needed by M7 and M10+.

---

## 7. What is still unknown, and the cheapest way to find out

"Static" means I can do it here. "Emulator" means a short session on the user's PC (Mesen 2: memory
breakpoints, VRAM/tilemap viewers, SPC debugger, profiler).

| # | Unknown | Blocks | Cheapest way to find out |
|---|---|---|---|
| U1 | UMK3 special-move dispatch, move routines, projectiles, attack boxes, combos, finishers, AI | M5, M7, M9-M14 | Static: find UMK3's counterpart of MK2's `$81:A943` through the compat code-skeleton pairs (`codematch_mk2.txt`), then walk it. Emulator: break on `$52F8,X` writes during a special and read the call stack |
| U2 | Is slot 25 a working fighter (moves, specials, finishers)? | M5 | Emulator with the M1 debug cell (minutes). Static: count `$FFF8` branches naming 25 in `$85:8010` and ID-25 entries in the per-fighter jump tables |
| U3 | How Human Smoke (22) is selected | M6 | Emulator: write breakpoint on `$36D0` while entering his selection code. Static: follow `$86:8E15` → `$8E4D` (`$86:8E71` compares `$0E`/`$16`) |
| U4 | Complete list of per-fighter tables and ID checks | M4, M8 | Static: the data-flow scan in M4. Emulator: the M8 clone test |
| U5 | Fight-stage type-0 / metatile format | M3, M13 | Static: decode `$84:9AB8`/`$84:9C87` and render Rooftop. Emulator: tilemap viewer screenshot of Rooftop as ground truth |
| U6 | Which MK3 stages have special logic (transitions, stage fatalities, props) | M3 | Emulator: play `mk3.sfc` on each stage (uppercut test, stage fatality). Static: per-stage jump tables indexed by `$3A7E` (like MK2's `$82:FD66`) |
| U7 | Sound driver, sample directory, SFX/voice IDs, ARAM budget | M7, M10+ | Static: find the APU upload loop (writes to `$2140`-`$2143`); start from the sound region shared with MK2 (`$CE:8E00`-`$CF:5000`, verified T3-1). Emulator: APU RAM viewer during a fight |
| U8 | "X WINS" text, ending/bio encoding, ladder portraits | M5, M7, M10+ | Emulator: VRAM viewer on the win screen, then search the tiles statically. Static: LZ-decode candidate starts in `$E5`/`$F6` with the verified port |
| U9 | VRAM budget per player object | M9 | Emulator: VRAM viewer during Motaro vs Kahn (largest frames). Static: slot tables `$86:E322`/`$86:E33A` (single-source) |
| U10 | CPU cost of tile data in SlowROM banks | M9+ | Emulator: profiler on the M9 puppet |
| U11 | ExHiROM boot on the user's emulator (and flash cart, if any) | M2 | Emulator: the M2 build |
| U12 | MK3 object-RAM layout vs UMK3, and where Sheeva's MK3 code lives | M7 | Static: `codematch.py`-style translation pairs MK3↔UMK3 (as in compat T2-5); MK3 per-fighter jump tables at entry 11. Also disassemble UMK3 `$83:FC9E` |
| U13 | MK2 → UMK3 animation remap (66 → 76) and UMK3 slots 53-75 | M7, M9 | Static: first-frame comparison per index (`animcmp.py`, `scripts/plan/sheeva_check.py`) plus labelling from R1 |
| U14 | HYPER KOMBAT consumer (speed) and HUD/run-meter rendering | M14 | Emulator: read breakpoint on `$7E:3BF2` with the kode on. Static: raw search found only the kode `INC` (section 10 P5) |
| U15 | What `$36C6`/`$388A` mean (hidden-cell gate) | M1b | Emulator: watch them in 1P vs 2P |
| U16 | How the stage is chosen in normal play (ladder order, random) | M3, M13 | Emulator: write breakpoint on `$3A84`/`$3A7E`. Static: callers of `$80:84B8` |
| U17 | MK2 portraits usable for the select and VS screens | M6 | Static: MK2 set 16 UI frames and `$82:D059`/`$82:E104` (single-source) |
| U18 | Effect-set frames per MK2 donor projectile | M10-M12 | Static: follow the process spawns (`$85:DF5D`) in MK2 move code (mk2-map open question 1) |
| U19 | Remaining ExHiROM risk in untraced code (APU upload, variable DMA banks) | M2 | Emulator: the M2 regression run covers it in practice |

---

## 8. What the PS1/N64 Trilogy copies are good for

Neither version holds SNES-format data. PS1 is MIPS R3000 code plus CD files; N64 is MIPS R4300 code
plus compressed cartridge data. Their code, sprite formats and audio formats are unrelated to the SNES
engine, so **nothing from them drops in**. The SNES MK2 and MK3 ROMs stay the primary donors, because
their data is already in (or one converter away from) UMK3's format. The PS1/N64 copies are useful as:

1. **Authoritative reference for behaviour and content.** Per-version roster, every move and input,
   combos, Brutality inputs, Aggressor rules (fill rate, duration, boost), Chameleon/Khameleon colour
   order and move borrowing, kodes, stage list, endings and bio text. Text is often plain ASCII and
   cheap to pull out. Static RE of MIPS code is possible here (capstone supports MIPS), but it is a
   separate project.
2. **Art source for content that no SNES ROM here has**: Goro, MK1 Kano/Raiden, MK1 stages, Khameleon
   (if not done as a palette swap), any MKT-only frames for MK2 characters (e.g. run or combo frames),
   the Aggressor HUD. Converting means:
   - reverse-engineering their sprite format;
   - downscaling to SNES size;
   - quantizing to 15 colours per sprite palette;
   - encoding with our own UMK3-format encoder (the inverse of the verified decoder).

   That is a large art pipeline. It pays off for portraits first: 8bpp select portraits and 6bpp VS
   portraits for Sheeva, Baraka, Johnny Cage, Raiden, Kintaro and Chameleon, where MK2 SNES may have
   nothing comparable (U17).
3. **Audio source**: name call-outs and fighter voices, resampled to BRR. This depends on the ARAM
   budget (U7).
4. **Ground truth for testing**: play the same move on PS1/N64 and on the hack and compare.

When the user brings them:
- record their SHA-1 hashes next to the SNES ones;
- treat them like the SNES ROMs: read at build time, nothing extracted into the repo.

None of M0-M9 needs them.

---

## 9. Risks (most severe first)

1. **The fighter move/AI system of UMK3 is unmapped**, and MK2 code cannot be reused (verified T2-5).
   Every MK2 donor is a from-scratch 65816 programming job against an undocumented engine. This decides
   whether the MK2 roster is achievable at all. R1 comes first for that reason.
2. **Incomplete knowledge of per-fighter tables and ID checks.** A missed table or `CMP #$1A` test
   makes a new ID behave like a boss, read garbage or crash. Only a heuristic list exists
   (section 10 P1). Mitigation: M4 inventory plus the M8 clone test.
3. **Sound may not fit.** The driver and ARAM budget are unknown. New voices and SFX might need
   trimming or sample swapping per match.
4. **ExHiROM speed and coverage.** All new data sits in SlowROM banks, which may cause slowdown in tile
   assembly for big new fighters. Untraced code could still hold a bank assumption. Mitigations: fast
   free space at `$FF:DC6E` for hot code and data; move cold data out of the fast half; regression test
   in M2.
5. **The select screen is full.** More fighters need new art squeezed into a shared 96-colour palette
   and the VRAM budget.
6. **Stage format and stage logic undecoded.** Copying records blind risks missed pointer fields;
   transitions and stage fatalities need code.
7. **Bank-relative 16-bit pointers** (stage descriptors in `$84`, names in `$83`, kode messages in
   `$85`, scripts next to their tables) force code patches before tables can grow.
8. **Slow feedback loop.** Everything here is static, and every runtime check waits for a session on
   the user's PC. Mitigation: small milestones, a debug select cell, symbol files, and precise
   watch-lists per test.

---

## 10. Completeness-critic findings made while planning

These are new checks, not part of the verified set. Each is reproducible with
`python3 -I /home/claude/work/scripts/plan/<script>`; outputs are in `/home/claude/work/out/plan/`.

| id | finding | tag | evidence |
|---|---|---|---|
| P1 | 42 traced places compare a just-loaded fighter ID with a constant. There are 14 compares with `$1A` (Motaro), 6 with `$1B` (Kahn), and robot checks `$07`/`$08`/`$0E`. **Five are `CMP #$001A ; BCS`, i.e. "ID ≥ 26 is a boss"**: `$85:9ADE`, `$85:9C5E`, `$85:9F99`, `$85:E6D7`, `$88:AB0B`. Also `CMP #$000F ; BMI` at `$80:9945` and `CMP #$001E ; BMI` at `$85:99D2`. Heuristic: a straight-line window of 6 instructions after the load; indexed-table and copied-ID checks are missed | LIKELY | `idchecks.py` → `idchecks.txt` (uses `out/umk3/trace.pkl`) |
| P2 | MK3's two animation tables are `$82` bytes apart (65 words), against `$98` (76) in UMK3. For the 13 fighters present in both, 682 of 881 animation indices start on the same frame number. The mismatches cluster at index ≥ 53, plus a few per fighter (e.g. 15, 36, 37, 40). So Sheeva's scripts need a remap only for the upper slots. MK3 set 11's tile-directory bank bytes are all ≥ `$C9` | numbers CONFIRMED (bytes read); implication LIKELY | `sheeva_check.py` → `sheeva_check.txt` |
| P3 | The kode-message table `$85:EA3E` is read at `$85:E819` and `$85:E8AB`. Entry = (pointer to RAM variable, value, message pointer); a message shows when the variable equals the value. 22 entries, e.g. HYPER KOMBAT `$3BF4`, SHADOW FIGHTING `$3C24`, 2X DAMAGE `$3BDC` | CONFIRMED (disassembly; single analyst) | `dis_kodemsg_reader.py` → `dis_85E805.txt`; `kodemsgs.py` → `kodemsgs.txt` |
| P4 | The kode flags are word pairs cleared by the loop at `$80:8653`-`$80:86A9` (`STZ base,X`, X = 2, 0). The same routine then clears the boss unlocks: `STZ $3BAE` at `$80:86B1`, `STZ $3BB0` at `$80:86B4`. Those are the only traced stores to them. The routine is called by `JSL` from `$80:8469` (reset path); "power-on only" is LIKELY | CONFIRMED (disassembly); "power-on only" LIKELY | `dis_bossflags.py` → `dis_bossflags.txt`; `flagrefs.py` |
| P5 | Gameplay readers of the kode flags (raw byte search, not traced):<br>- `$85:C656 LDA $3C22` → if set, `ORA #$0020` into `$5538,X`. The routine is LIKELY fighter-object setup (it sits just after the `$85:C62E` fighter-ID check); the bit is LIKELY the shadow trail.<br>- `$84:E829`-`$84:E84A` scales the damage value in DP `$32`: `LSR` if `$3BD6` (2X HEALTH), `ASL` if `$3BDA` (2X DAMAGE), two `LSR` if `$3C16`, minimum 1.<br>- The HYPER KOMBAT pair `$3BF2` showed only the kode's `INC`; no reader found | code CONFIRMED (disassembly); meanings LIKELY | `flagraw2.py` → `flagraw2.txt`; `dis_flagreaders.py` → `dis_flagreaders.txt` |
| P6 | UMK3 records 7 and 8, the dead stubs (verified T1-5), have **private** layer descriptors, shared with no other record: rec 7 `$84:8946` (type 0) and `$84:89B6` (type 1); rec 8 `$84:8752`, `$84:8786` (type 0) and `$84:87B0` (type 1). They can be rewritten in place for two new stages without moving the bank-`$84` record table. Also: rec 9 reuses all of rec 6's layers; rec 23 shares `$84:87FD` with recs 6 and 9; rec 10 shares `$84:83BB` with screens 17 and 20 | descriptor facts CONFIRMED (bytes read); reuse LIKELY | `rec78.py` → `rec78.txt` |
| P7 | MK2's stored checksum `$7221` equals sum(first 2 MB) + 2 × sum(last 1 MB): the mirrored convention. UMK3 and MK3 match their plain sums | CONFIRMED | `checksum.py` → `checksum.txt` |
| P8 | Two MK2 secret-fighter messages, near `$C3:DA34` and `$C3:DC44`, both name "GORO'S LAIR" as the place of the next fight. This supports stage 9 = Goro's Lair but does not prove it | LIKELY | `strings_check.py` → `strings.txt` |
| P9 | Fight stages do not render under a plain-tilemap reading (`out/compat/mk3_rec0_L0.png` is noise, viewed), so the metatile format must be decoded before any static stage check | CONFIRMED (viewed) | `out/compat/mk3_rec0_L0.png` |
| P10 | Kode 45's message announces one-button brutalities; its handler sets `$3A78` bit 3. Brutalities therefore LIKELY exist in SNES UMK3 | LIKELY | `out/umk3/kodes.txt`; `strings_check.py` → `strings.txt` (string at `$85:ECC7`) |

Gaps in the existing maps that this plan depends on, all listed in section 7:
- the move, special, AI and combo systems (U1);
- sound (U7);
- fight-stage format (U5);
- win, ending and ladder text and graphics (U8);
- HUD (U14);
- per-fighter table completeness (U4);
- VRAM and CPU budgets (U9, U10).

None of these blocks M0-M3.

---

## Appendix A: emulator watch-list (UMK3, bank `$7E`)

| address | meaning | status |
|---|---|---|
| `$52C8,X` | fighter ID of player object (X = 0 P1, 2 P2) | verified C3 |
| `$52F8,X` | current frame ID (`set<<9 \| frame`) | verified (C-U2 path) |
| `$36D0` / `$3894` | P1 / P2 selected fighter | verified C3 |
| `$3A50` / `$3A52` | P1 / P2 select-cursor cell | verified C5 |
| `$1C57` / `$1C59` | hidden-cell state / fighter in the hidden cell | verified C15 |
| `$3BAE` / `$3BB0` | Kahn / Motaro unlocked | verified C15 |
| `$36C6` / `$388A` | hidden-cell precondition (meaning open) | verified condition, open meaning |
| `$3A84` / `$3A7E` | kombat zone / screen-stage record | verified C17 |
| `$5538,X` | object flags: bit `$40` alt palette (verified C9); bit `$20` shadow (P5, LIKELY) | mixed |
| `$3BF2` / `$3C22` / `$3BDA` | HYPER / SHADOW / 2X DAMAGE kode flags (base of word pair) | P4/P5 |
| `$7E:C0A8` | CGRAM shadow image (`$C1A8` = colour 128, first OBJ palette) | LIKELY (verifier) |
