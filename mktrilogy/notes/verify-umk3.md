# Verification of the UMK3 base-ROM claims (umk3:C1 - umk3:C23)

Verifier: independent re-derivation, static analysis only (no emulator).
ROM: `/home/claude/work/roms/umk3.sfc` (read-only). MK3 (`mk3.sfc`) was used once, for a cross-check of fighter ID 11.

Addresses are SNES addresses `$BB:AAAA`. HiROM: file offset = `addr & $3FFFFF`.

## How this was done

None of the other analyst's scripts or outputs were imported. Their notes were read only to find out what each claim means; every result below comes from my own code.

My scripts are in `/home/claude/work/scripts/verify-umk3/`. Run each one as `python3 -I <script>`.

| script | what it is |
|---|---|
| `v.py` | My own table-driven 65816 disassembler (all 256 opcodes, REP/SEP width tracking, no capstone). It also has a HiROM mapper in which only banks `$7E`/`$7F` count as WRAM, plus xref helpers |
| `spr.py` | Sprite renderer written from my reading of `$88:A471`, `$88:A5A8`, `$83:8000` and `$83:8362` |
| `lzv.py` | LZ decompressor written from my reading of `$88:AD30` (normal mode) and `$88:AE7D` (mode 2) |
| `trace.py` | Recursive-descent code tracer. Seeds: vectors, `LDA #/LDX #/JSL` process creators, `PEA/PEA` call frames. Output: `out/verify-umk3/trace_v.pkl` (36,341 instructions) |
| `c*.py` | One script per claim group (names below) |
| `dis_misc.py` | Listing of every short routine cited here → `out/verify-umk3/dis_misc.txt` |

Evidence goes to `/home/claude/work/out/verify-umk3/`: PNG renders, `dis_*.txt` listings, and a `c*.txt` text output for each script.

Tags:
- **CONFIRMED**: I traced the code that uses the data and decoded the data myself.
- **LIKELY**: inference or heuristic.

## Verdict summary

| id | verdict | one-line reason |
|---|---|---|
| C1 | holds | header, map mode, size and checksum reproduced |
| C2 | holds | all vector targets disassembled; matches exactly |
| C3 | holds | own renders + name table + kode messages agree for every ID |
| C4 | holds | grid, select BG, VS portraits, palettes and animation pointers all present for Rain and Noob (move sets not checked) |
| C5 | holds (LIKELY) | only cell 10 is gated; both cursors **start** on cells 0 (Rain) and 6 (Noob) |
| C6 | holds | ID 11 is empty everywhere; **SNES MK3's ID 11 renders as Sheeva**, which strongly supports the attribution |
| C7 | holds | its VS entries are byte-identical to Scorpion's |
| C8 | holds | set tables + frame IDs in the scripts |
| C9 | holds | traced; there is also a Shang Tsung morph rule |
| C10 | holds | bytes read and rendered |
| C11 | holds | 309 valid entries ending at `$88:9D23`; only two long xrefs. The register wording is imprecise (see below) |
| C12 | holds | my own decoder renders all 27 fighters correctly |
| C13 | holds | my own port decodes the 4 named streams exactly, plus 79 more |
| C14 | holds | grid, rows, direction tables, record 13 |
| C15 | holds | traced; extra open conditions found |
| C16 | **partly** | tables and formats are right, but the VS tile index has **no -1** (their render and notes are off by one). Tiles are loaded by `$83:E808`, not `$83:E730` |
| C17 | holds | 29 records, indexing, `$80:84B8`, names |
| C18 | holds (LIKELY) | supported by the ground parameters; records 7 and 8 have abnormal layer data |
| C19 | holds | 45 entries, matcher, both dispatch tables, handlers |
| C20 | holds (LIKELY) | the 4 kodes check out; 5 more arcade kodes also match their handlers |
| C21 | holds | free-space numbers reproduced exactly |
| C22 | **partly** | the code-side evidence reproduces, but **9 sprite tile-directory entries use bank bytes `$00`-`$07`**, which the recipe breaks |
| C23 | holds | both bugs reproduced; only the M8+X8 capstone mode fails |

---

## C1: header and checksum. **holds** (CONFIRMED)

- File size: 4,194,304 bytes, i.e. 4 MB with no 512-byte copier header.
- Title at file `0xFFC0`: "ULTIMATE KOMBAT 3".
- Map mode `$FFD5 = $31`, cart type `$00`, ROM size `$FFD7 = $0C`, SRAM size `$00`, country `$01`.
- Complement `$9B16` XOR checksum `$64E9` = `$FFFF`.
- The 16-bit byte sum of the whole file is `$64E9`, which matches the stored checksum.
- The LoROM header position (`0x7FC0`) holds no valid title.

Evidence: `c01_c02_header.py` → `out/verify-umk3/c01_c02_header.txt`.

## C2: vectors. **holds** (CONFIRMED)

Native vectors:

| vector | target |
|---|---|
| COP / BRK / ABORT | `$83D6` |
| NMI | `$8765` |
| unused | `$83D7` |
| IRQ | `$8738` |

Emulation vectors:

| vector | target |
|---|---|
| COP / unused / ABORT | `$83D6` |
| NMI | `$8765` |
| RESET | `$83D7` |
| IRQ/BRK | `$8738` |

Disassembly:
- `$00:83D6`: `RTI`.
- `$00:83D7`: `SEI`, `CLD`, `CLC`, `XCE`, `REP #$30`, `LDA #$1FFF`, `TCS`, `LDA #$1800`, `TCD`, `PEA $7E7E`, `PLB`, `PLB`, `JSL $88C7E4`, `JML $8083F2`.
- `$00:8738`: `REP #$30`, `PHA`, `PHX`, `PHY`, `PHD`, `PHB`, `JML $808743`.
- `$00:8765`: `RTI`.

Evidence: `c01_c02_header.txt`; `dis_misc.txt` section "reset/IRQ/NMI stubs".

## C3: roster IDs 0-27, `$52C8,X`, `$36D0`/`$3894`. **holds** (CONFIRMED)

Three independent routes give the same roster.

1. **Sprite renders.**
   - Route: the first animation-0 frame from `$88:95C3[id]`, following `$FFFF` jumps and `$FFF8` per-fighter branches, drawn with my own sprite decoder and the primary palette `$88:9D23[id]`.
   - Output: `out/verify-umk3/roster_mine.png` (script `c03_roster.py`).
   - Every ID shows the stated fighter. IDs 26 and 27 are clearly Motaro (centaur) and Shao Kahn. ID 11 has no data.
2. **Name table `$83:E544`.**
   - It is a word-pointer table into bank `$83` and is read at `$83:E363` (`LDA $83E544,X`).
   - Entries 0-26 decode to: -KANO, -SONYA, -JAX, -NIGHTWOLF, -SUB-ZERO, -STRYKER, -SINDEL, -SEKTOR, -CYRAX, -KUNG LAO, -KABAL, (null), -SHANG TSUNG, -LIU KANG, -SMOKE, -KITANA, -JADE, -MILEENA, -SCORPION, -REPTILE, -ERMAC, -SUB-ZERO (entry 21 shares 4's string), -SMOKE (entry 22 shares 14's), -NOOB SAIBOT, -RAIN, (null), "? ? ? ? ?".
   - Entry 27 is past the end of the table (code bytes).
   - Output: `c03_names.txt`.
3. **Kode handlers.** They pair fighter IDs with ASCII messages (see C19):
   - `$0E` "…BATTLES SMOKE"
   - `$17` "…NOOB SAIBOT"
   - `$1A` "…MOTARO"
   - `$1B` "…SHAO KAHN"

Fighter-ID variables:
- `$88:93C0`: `LDA $36D0` / `STA $52C8` / `LDA $3894` / `STA $52CA`, so P1's ID is `$52C8+0` and P2's is `$52C8+2`.
- `$86:A40E` / `$86:A441`: the grid lookup `$86:A1F6` writes `$36D0` / `$3894`.
- The animation, palette and `$FFF8` code all index by `$52C8,X`.

Evidence: `dis_misc.txt` sections "$88:93C0" and "$86:A1F6"; `dis_86A3FA.txt`.

## C4: Rain (24) and Noob (23) are already in the base game. **holds** (CONFIRMED for the listed assets)

| asset | Rain | Noob | evidence |
|---|---|---|---|
| grid cell (`$86:A207`) | cell 0 = `$18` | cell 6 = `$17` | C14 |
| select-screen portrait | top-left: purple-masked ninja | top-right: black ninja | `select_L0_blockpal.png` |
| VS portrait (shared ninja art, own palette pointer) | `$D4:86B5` | `$D4:85F5` | `vs_portraits_shift0.png` |
| primary / alt palettes | `$75` / `$86` | `$74` / `$88` | `ninjas_pri_alt.png` |
| animation table | `$85:8010` | `$85:8010` | shared |

In `ninjas_pri_alt.png`, Noob's primary palette is all black and his alt is dark grey. Rain is purple in both.

Caveat: "complete fighter" is only demonstrated for these assets. I did not audit per-fighter move code or finishers.

## C5: Rain and Noob are selectable without a kode. **holds** (stays LIKELY: static reading only)

Movement handler `$86:A726`:
- It reads the next cell from the direction table.
- Only if the next cell is `$0A` does it check `$1C57 == 1`, then `$F5A6 == 0`, then that neither `$3A50` nor `$3A52` is already 10.
- Otherwise it double-steps past cell 10 (up → 3, down → 16, left → 9, right → 11).

No other gating exists in the move or confirm paths:
- Confirm (`$86:A3FA`) does `LDA $3A50` → `JSL $86A1F6` → `STA $36D0`, with no ID filter.
- **New evidence:** the cursor init stores `$1A` into `($94)` at `$86:A2DB`/`$86:A2DD`.
  - P1 (`$94 = $3A50`) starts at cell `$00` (`$86:A2B6`), which is **Rain**.
  - P2 (`$94 = $3A52`) starts at cell `$06` (`$86:A259`), which is **Noob**.
  - So each player's cursor starts on one of the two.

Evidence: `dis_86A21F.txt`, `dis_86A661.txt`, `dis_86A3FA.txt`.

## C6: ID 11 is empty and was probably Sheeva. **holds** (empty: CONFIRMED; Sheeva: strongly supported)

Every per-fighter structure is empty for ID 11:

| structure | ID 11 value |
|---|---|
| `$88:95C3[11]` | `$000000` |
| `$88:9633[11]` | `$000000` |
| name pointer | `$0000` |
| `$88:9D23[11]` / `$88:9D3F[11]` | `0` / `0` |
| set 11 in `$86:EAEC`/`$86:EB24` | bank 0, address 0 |
| grid | no `$0B` |
| VS tables (`$83:EEC6[11]` etc.) | all 0 |

Note: "palette 0" is literally palette ID 0, which is Kano's alternate palette. It is not a "no palette" marker.

Sheeva cross-check:
- I found SNES MK3's equivalent tables by code-pattern search:
  - set tables `$85:ABAA`/`$85:ABDE` (code `$86:E9AC`);
  - animation tables `$86:DC53`/`$86:DC9B` (`$86:DC13`/`$86:DC34`);
  - primary palette IDs `$86:F3AE` (`$86:DE70`);
  - palette table `$86:F0FC` (`$83:F7E9`).
- I rendered MK3 IDs 0-17 with the same decoder.
- IDs 0-14 are the same fighters as in UMK3, and **MK3 ID 11 is Sheeva** (four arms): `out/verify-umk3/mk3_roster_check.png` (script `c06_mk3_id11.py`).
- UMK3's ID 11 therefore keeps the slot of a fighter that was removed (Sheeva). That this is why the slot is empty is LIKELY.

## C7: ID 25 is a spare male ninja. **holds** (CONFIRMED)

- Animation table `$88:95C3[25] = $85:8010`.
- Palettes `$88:9D23[25] = $70` and `$88:9D3F[25] = $82`, the same as Scorpion.
- Name pointer `$83:E544[25] = 0`.
- No `$19` in the grid.

VS tables (`$83:EEC6`/`EEFA`/`EF2E`/`EF62`/`EE92`/`EFE6`, 26 entries each, `$34` bytes apart):
- Entry 25 has a VS portrait, but it is **byte-identical to entry 18 (Scorpion)**: bank `$D4`, tiles `$63A2`, map `$838F`, palette `$8475`.
- Entries 26 and 27 do not exist (they would read the next table).

## C8: shared sprite sets. **holds** (CONFIRMED)

The set tables `$86:EAEC` (bank) and `$86:EB24` (address) are read at `$88:A483`/`$88:A489`. They are `$38` bytes apart, so 28 entries.

| sets | header |
|---|---|
| 7, 8, 14 | all `$86:C9AB` |
| 26 | `$85:CE30` |
| 27 | `$85:8000` |
| 11 | null |

The frame IDs in the animation scripts show which set each fighter uses:
- IDs 18-25 (table `$85:8010`): only set 27 (stance frames `$367F`-`$3684`; `$367F >> 9 = 27`).
- IDs 15-17 (table `$85:CE40`): set 26.
- IDs 7, 8, 14 (table `$86:CA27`): set 7, whose header is the shared `$86:C9AB`.

Evidence: `c08_sets.txt`, `c08_anim.txt`, `roster_mine.png`.

## C9: palette choice. **holds** (CONFIRMED)

At `$88:9874` (entry `$88:987B` skips the `$7C` bit-`$20` test):
1. `JSL $8898BE`.
2. Carry set → `AND #$FFBF` on `$5538,X`, then `LDA $889D23,X` (X = `$52C8,X`).
3. Carry clear → `ORA #$0040`, then `LDA $889D3F,X`.
4. Both paths end with `JSL $889842` → `$85:CD14`.

`$88:98BE`:
- If `$3BEE != 0` or `$F5A6 == 1`: object `$2A == 0` gets SEC (primary) and any other object gets CLC (alternate).
- Otherwise it compares own and opponent selections from `$36D0`/`$3894`. `$36CA`/`$388E` hold the P1/P2 object offsets (set to 0 and 2 at `$88:93CC`/`$88:93D2`).
- In a mirror match, the object at `$388E` (P2) gets the alternate.

Extra (not in the claim): Shang Tsung (`$0C`) rule at `$88:991C`. When Shang's current `$52C8,X` equals the opponent's fighter (he has morphed into them), he gets the alternate.

`$82:9D59`:
- IDs >= 15 pick `$9D3F`/`$9D23` by `$5538` bit `$40`.
- IDs < 15 use `$88:9E19`.

Evidence: `dis_misc.txt` sections "$88:9842..", "$82:9D57".

## C10: male-ninja palette IDs. **holds** (CONFIRMED)

Bytes read from `$88:9D23` and `$88:9D3F`:

| fighter | primary / alt |
|---|---|
| Scorpion | `70` / `82` |
| Reptile | `76` / `87` |
| Ermac | `71` / `83` |
| Classic Sub-Zero | `72` / `84` |
| Human Smoke | `73` / `85` |
| Noob | `74` / `88` |
| Rain | `75` / `86` |
| id25 | `70` / `82` |
| Motaro | `94` / `94` |
| Kahn | `97` / `97` |

The alt palettes `$82`-`$88` are stored in bank `$88` (`$88:C42D`-`$88:C4ED`).

Evidence: `c10_palids.txt`; render `ninjas_pri_alt.png`.

## C11: palette table and loader. **holds** (CONFIRMED)

Table `$88:9984`:
- Exactly 309 consecutive entries are valid 24-bit pointers to 16 words with bit 15 clear.
- Entry 309 would be the bytes of `$88:9D23` (`$100801`), which is not a valid pointer.
- 309 × 3 = `$39F`, and `$9984 + $39F = $9D23`.
- Banks used: `$88`, `$CA`-`$CD`, `$D5`, `$FD`-`$FF`.

References to the table:
- Long xrefs to `$889984`/`$889985`/`$889986` and to the `$C8` forms are only `$85:CDA2` and `$85:CDA8`.
- No other raw 24-bit copy of the pointer exists in the ROM.
- No immediate `#$9984` in code banks.

Wording detail: on entry to `$85:CD8B`, **`$0A` = palette ID** (stored by `$85:CD14`) and **X = slot byte offset** (0, 2, …, 14). Internally X is then recomputed as ID × 3.
- Destination: `$C1A8 + 16 × X`, i.e. 32 bytes per slot. Y runs from `$1E` down to `$02`, so colors 1-15 are copied and color 0 is not.
- The claim's "(A = ID, X = ID*3)" mixes the input and the internal use; the substance is right.

Extra, about the CGRAM shadow (LIKELY roles):
- `$87:FECB` DMAs 512 bytes from `$7E:C0A8` to CGADD 0, and `$87:FE15` DMAs `$7E:C2A8` to CGADD 0. So `$7E:C0A8` is a full CGRAM image.
- `$C1A8` is therefore **CGRAM color 128**, the first OBJ palette, and loader slot X/2 is OBJ palette X/2.
- This contradicts a side remark in the umk3 notes ("`$C1A8` is CGRAM color 0"); that remark was not one of the claims.

Evidence: `c11_paltab.txt`, `dis_85CD14.txt`, `dis_misc.txt` "$87:FECB".

## C12: sprite format. **holds** (CONFIRMED by an independent decoder)

Re-read from the code:
- `$88:A471`: `XBA`; `AND #$00FE`, so X = set × 2. The header words are read at offsets 0, 2, 4, 5, 7, 8, 9, B, C, E.
- `$88:A5A8`: `f0 = (id & $1FF) - 1`; bank = `[$6A + (f0 >> 6)]`; address = `[$4E + 2 × f0]`.
- `$83:8000`: byte N, byte B. The first B pieces take the 16x16 path (4 refs placed at +0, +`$20`, +`$200`, +`$220`, i.e. TL/TR/BL/BR in a 16-tile-wide VRAM row); the rest take the 8x8 path.
- Piece position, from the control byte:
  - High nibble k → x += `delta[1+k]`; k = 0 → an explicit x byte follows.
  - Low nibble → y += `delta[16+k]` (or an explicit byte).
  - The start is (`delta[0]`, `delta[1]`).
- Tile ref: `LSR`/`ROR`/`ROR`/`AND #$C000` puts bit 0 into OAM H-flip and bit 1 into V-flip. `$83:8362` uses `ref & $FC` (directory byte offset) and `ref >> 8` (tile number).
- `$83:8362` codec:
  - flags bit 7 = mask-compressed; bit 6 = 2bpp; bits 0-5 = record size;
  - threshold byte T; a fill byte if n >= T;
  - 4 (or 2) mask bytes, MSB first; 1 = literal, 0 = fill. This was checked in the `$83:85AA` jump-table routines for masks `$00`, `$80`, `$01`, `$FF` and `$A5`.

`spr.py` implements exactly this. It renders every fighter correctly (`roster_mine.png`) and also SNES MK3's fighters (same format).

Details the claim does not state:
- A 16x16 piece takes its flip **only from its first ref**. `$8362` ignores bits 0-1 of the other three refs.
- Header `+8` (bank) and `+E` (address) point to a 4-byte-per-frame table (`$88:A6A6`). `+E = $FFFF` selects a default at `$86:EC3C`.
- In every set, the frame table is directly followed by the bank table, so frame count = (banktab - frametab) / 2. For example, set 0 has 255 frames and set 27 has 380 (`c22_spritebanks.txt`).

## C13: LZ decompressor. **holds** (CONFIRMED by an independent port)

My port `lzv.py`:
- emulates the word-wise, highest-word-first back-reference copy of normal mode (the `$88:B120` routines);
- emulates mode 2's stride-2 copy/fill (`$88:B140`, `$88:B19C`);
- emulates the odd-then-even pass switch at `$88:AEDA` and the back-reference wrap at `$88:AF3D`.

The four named streams decode exactly (final Y = 0, nothing unfilled, no read of an unwritten byte):

| stream | mode | output size |
|---|---|---|
| `$C3:0000` | 2 | `$9C80` |
| `$F9:FACF` | 2 | `$870` |
| `$F2:BAAA` | 1 | `$16C0` |
| `$F9:FCB9` | 2 | `$1000` |

Bulk test (`c13_lz_bulk.py`): of 85 distinct streams named by the VS tables and the layer descriptors, **83 decode exactly** (64 mode 2, 19 normal mode).

The 2 failures are record 7's map pointers `$F0:A95D` and `$F0:AB2B`. Their "mode" bytes are 72 and 66, which suggests that record's data is not LZ, or the record is unused (see C18).

## C14: select-screen grid. **holds** (CONFIRMED)

- `$86:9F57`: `LDA #$000D` / `STA $3A7E`, inside the routine that resets `$36D0`/`$3894`/`$3A50`/`$3A52` to `$FFFF`.
- Grid `$86:A207` (24 bytes): `18 13 05 02 03 10 17 | 01 00 11 FF 15 04 09 | 07 0F 14 12 08 | 0A 06 0E 0D 0C`. Code follows at `$86:A21F`.

Direction tables (24 bytes each): `$86:A6C6` (up), `$86:A6DE` (down), `$86:A6F6` (left), `$86:A70E` (right). They give the 7/7/5/5 layout: row 2 sits under cells 8-12 and row 3 under 14-18. They are selected by joypad bits `$0800`/`$0400`/`$0200`/`$0100` at `$86:A387`-`$86:A3EE`.

Blocked lists `$86:A677` (7 bytes per direction, padded with `$1B`), checked by `$86:A661`:

| direction | blocked cells |
|---|---|
| up | 0-6 |
| down | 7, 19-23, 13 |
| left | 0, 7, 14, 19 |
| right | 6, 13, 18, 23 |

Cursor steps: x ±50 (`#$FFCE`/`#$0032`) and y ±64.

The select BG map (`$F9:FACF`, 32 wide) has 4x6-tile portraits at:
- rows 3-8: 7 portraits;
- rows 9-14: 6 portraits, with a blank 4-column gap at columns 14-17 (the hidden cell);
- rows 15-20 and 21-26: 5 portraits each.

Evidence: `dis_86A661.txt`, `dis_86A21F.txt`, `select_L0_blockpal.png`.

## C15: hidden slot. **holds** (CONFIRMED)

`$84:A328`-`$84:A383`:
- If `$3BAE` or `$3BB0` is set, the routine waits until **`$36C6` and `$388A` are both nonzero**.
- If `$3BAE` is set: `$1C59 = $1B` (Kahn).
- If `$3BB0` is set: `$1C59 = $1A` (Motaro).
- If both are set, it loops and alternates between them.

`$1C57` is the slot state:
- 0 at `$84:A306`/`$84:A38E`;
- 1 (open) at `$84:A39B`;
- 2 (closing) at `$84:A3F7`.

`$86:A203` returns `$1C59` for grid value `$FF`.

The portrait art is at select-map rows 28-33 (`select_rows28_33.png`):
- columns 0-3: Motaro (horned, bearded);
- columns 4-7: Shao Kahn (skull helmet).

This matches table `$84:A2EC`: Motaro (X = 0) → offset 0; Kahn (X = 2) → offset 8 bytes (4 tiles). The tiles are copied as 4×6 (`A = $0406`, `JSL $84A750`).

Extra conditions for the mod:
- the slot opens only when `$36C6` and `$388A` are both nonzero;
- the cursor may enter it only if `$F5A6 == 0` and the other cursor is not already on cell 10 (C5).

`$3BAE`/`$3BB0` have no direct stores in code other than `STZ` at `$80:86B1`/`$80:86B4`. Both appear as words in the menu variable list at `$83:D742`-`$83:D76E` (`$3BB0` at `$83:D754`, `$3BAE` at `$83:D76E`), which is consistent with menu-driven toggles. LIKELY.

## C16: select BG layer 0 and VS portraits. **partly**

Select layer, record 13. Everything in the claim is right (CONFIRMED):

- Record 13 (`$84:8BDC`) holds layer pointers `$8299` and `$82C6`.
- Descriptor `$84:8299` is type 1 (byte 0 = 1). The type-1 loader is `$84:920C`. Pointers are stored bank-first:

  | field | offset | value |
  |---|---|---|
  | palette | +`$15` | `$FF:7BC2` |
  | tiles | +`$18` | `$C3:0000` |
  | map | +`$1D` | `$F9:FACF` |
  | tile count | +`$1B` | `$0272` = 626 tiles = `$9C80` / 64 |

- 8bpp: descriptor +1 = `$FF`, which `$84:920C` turns into `$40` bytes per tile.
- Palette block `$FF:7BC2`: count `$60` (96), first CGRAM index `$30` (48). Loader `$84:961C`.

How pixel values reach the palette block (new, CONFIRMED):
- The block is loaded at CGRAM 48, not 0. The tile pixels still index it from 0 because `$84:9444`-`$84:945F` calls **`$84:9703` with A = descriptor +2 (here 3)**.
- That routine adds 16 to every non-zero 8bpp pixel, A times (planar add over planes 4-7), so pixel v becomes v + 48.
- Tile 0 is skipped because the loop starts at offset `$60`, but tile 0 is blank and never used.
- Result: pixel value v (1-95) shows block color v. Pixel values 0-95 are used.
- `select_L0_blockpal.png` (correct) vs `select_L0_cgram.png`, which shows what you get without the transform.

VS portraits. Tables and format are right; the tile-index detail is wrong:

| table | contents |
|---|---|
| `$83:EEC6` | bank |
| `$83:EEFA` | tile stream |
| `$83:EF2E` | map stream |
| `$83:EF62` | 64-color palette |
| `$83:EE92` | tile count |
| `$83:EFE6` | mirror-match palette offset |

- 26 entries each.
- `$83:E97E` copies 24 words (48 bytes) per tile and then 8 zero words, so the tiles are **6bpp at 48 bytes**. CONFIRMED.
- Map and palette are loaded by `$83:E730`. **The tiles are loaded by `$83:E808`** (its tile count comes from `$83:EE92`), not by `$83:E730`.
- **Error in the evidence:** `render_vs.py` and the umk3 notes use "tile index = map value - 1". The correct rule is **tile index = map value & `$3FF`**.
  - For every ID checked, the distinct map values are exactly 0..N-1 for N tiles.
  - Tile 0 is the blank tile, and map value 0 is the background.
  - Rendered both ways: `vs_portraits_shift0.png` is clean, while `vs_portraits_shift1.png` and their `out/umk3/vs_portraits.png` show fringe and missing-tile artifacts.
- `$83:E87C` copies a 16 × 22 map window, which confirms the "left 16x22" portrait area.

## C17: record table and stage names. **holds** (CONFIRMED)

- `$84:8FC8`: low byte of `$3A7E` × `$22` (via `$4202`/`$4203`), then `LDA $848A22,X`.
- Records 0-28 are well-formed. The bytes at "record 29" (`$84:8DFC`) are different data.
- The highest immediate stored to `$3A7E` is `$1C` (at `$83:D838`).
- `$84:9081` loop: +8..+F are 4 descriptor words in bank `$84` (`$FFFF` = none).
- `$80:84B8`: `$3A84` → `$3A7E` with 0 → 5 and `$70` → 0 (which also clears `$3A84`); any other value is copied unchanged.
- Name table `$85:EE32` is read at `$85:E908` and `$85:EA00` (index `$3A84 × 2`). Seven entries: ROOFTOP, THE DESERT, HADES, THE KAVE, THE WATERFRONT, LOST, THE PIT 3.

Evidence: `dis_misc.txt`.

## C18: which records are fight stages. **holds** (stays LIKELY)

Supporting:
- Records 0-10 and 23 use mode 1 with 2-4 layers and have non-zero parameters at +`$10`.
- All other records have zero parameters there and 1-2 layers (menus, modes 1 and 3).
- `$3A84` values 1-6 map 1:1 to records 1-6, so names 1-6 plausibly label records 1-6.

Anomalies:
- **Record 7**: its map streams `$F0:A95D`/`$F0:AB2B` do not LZ-decode; its tile count `$03B7` does not match its tile stream.
- **Record 8**: all its data pointers are `$00:0001`.
- Either both are special cases or they are unused.
- Name index 0 (ROOFTOP) is ambiguous: `$3A84 = 0` means record 5, while `$70` means record 0 and then `$3A84 = 0`.

No fight stage was rendered.

## C19: kombat kodes. **holds** (CONFIRMED)

Table `$85:DFF5`: 45 × 8 bytes (6 icons + 2 zero bytes), terminated by `$FF` at `$85:E15D`.

Matcher `$85:E1B3` (called from `$83:E6BA`):
- 0 = wildcard; `$FF` ends the table;
- compares against `$7E:52F8 + $18 + 2k`;
- stores (index / 8) + 1 in `$3C2E` and `$3C30`.

Dispatch at `$85:DF1F`:
- `$3A90 == 1` → `JMP ($DF3D,X)`;
- otherwise → `JMP ($DF99,X)`.
- The two tables (46 words each) differ only at kodes 10, 29 and 36 (→ `$E209`, a no-op).

Handlers:
- Kode 11 → `$E730`: `LDA #$1A`, message `$85:EB7F` "WINNER OF THIS ROUND BATTLES MOTARO".
- Kode 12 → `$1B`, "…SHAO KAHN".
- Kode 13 → `$17`, "…NOOB SAIBOT".
- Kode 20 → `$0E`, "…SMOKE".
- Kodes 38-43 → `$3A84` = 6, 4, 2, 3, 1, `$70` (`$85:E237`-`$85:E255`).

## C20: icon = arcade digit + 1. **holds** (stays LIKELY: relies on outside knowledge of arcade kodes)

The four named kodes match: entry 13 = 769-342, 20 = 205-205, 11 = 969-141, 12 = 033-564.

Further consistency (my recollection of the arcade list, LIKELY):

| entry | arcade kode | handler |
|---|---|---|
| 1 | 100-100 throwing disabled | `STZ $3BC2` |
| 2 | 020-020 blocking disabled | `STZ $3BC6` |
| 36 | 300-300 | SILENT KOMBAT message |
| 44 | 010-010 | THROWING ENCOURAGED |
| 6 and 37 | 460-460 / 444-444 randper | `INC $3BEE`, which is the C9 "random" palette rule |

Entry 27 (all 11s) remains unexplained.

## C21: free space. **holds** (CONFIRMED)

`c21_free.py`:
- The largest `$FF` run is **9,106 bytes at `$FF:DC6E`-`$FF:FFFF`**.
- Each code bank's tail has one `$FF` run:

  | bank | start | length |
  |---|---|---|
  | `$C0` | `$C0:FF1F` | 103 |
  | `$C1` | `$C1:FF72` | 98 |
  | `$C2` | `$C2:FF0B` | 102 |
  | `$C3` | `$C3:FF8E` | 100 |
  | `$C4` | `$C4:FF83` | 87 |
  | `$C5` | `$C5:FEE1` | 92 |
  | `$C6` | `$C6:FF79` | 100 |
  | `$C7` | `$C7:FF58` | 90 |

- Total of `$FF` runs of 64+ bytes: 9,978 bytes.

Additions:
- `$C8:CAE6` has 100 `$FF` bytes in mid-bank. Possibly free; not verified.
- `$C8:C22B` has a 518-byte zero run. Its last 6 bytes overlap palette `$82` at `$88:C42D`, so it is not all free.
- The code-bank `$FF` runs end **directly before small compressed sprite-tile blocks** (see C22). Do not grow into them.

## C22: ExHiROM conversion. **partly**

What reproduces:
- My own tracer (36,341 instructions) finds traced bank-`$00` code only at `$83D6`-`$83EE`, `$8738`-`$873F` and `$8765`.
- No traced abs or long operand addresses `$FFB0`-`$FFFF`, so there is no header or checksum read in the traced code.
- Long operands in traced code use banks `$7E`/`$7F`, `$80`-`$88`, `$A9`, `$C0`-`$FF`, plus bank-`$00` I/O. The 24 operands in `$40`-`$7D` are all ASCII text the tracer ran into (e.g. `EOR $524556`).
- Data pointers checked: palette table, animation tables, VS banks, all type-0/1 layer descriptors, sprite set headers and frame bank tables. All are `>= $C0` or `$80`-`$88` (or `$00:FFFF` / `$00:0001` sentinels).

What breaks the recipe:
- **9 sprite tile-directory entries hold bank bytes `$00`-`$07`.**
- `$83:837D` uses that byte directly as the data bank (`ORA #$7E00` / `PHA` / `PLB`), and the compressed path uses it as the `[$56]` bank.
- They point at small mask-compressed tile blocks packed into the last bytes of the code banks.

| set | dir entry (address) | data | records × size | tiles used | frames using it |
|---|---|---|---|---|---|
| 0 Kano | +`$34` (`$FF:B3F3`) | `$05:FF3D` | 32 × 6 | 0-31 | 186 |
| 0 Kano | +`$6C` (`$FF:B42B`) | `$04:FFDA` | — | 0-6 | 104 |
| 13 Liu Kang | +`$00` (`$FF:B830`) | `$07:FFFB` | — | 0 | 179, including his stance |
| 17 | +`$44` (`$FF:C68D`) | `$00:FF86` | — | — | — |
| 18 | +`$44` (`$FF:C52D`) | `$02:FF71` | — | — | — |
| 20 | +`$24` (`$FF:CAD1`) | `$01:FFD4` | — | — | — |
| 21 | +`$38` (`$FF:D4EB`) | `$03:FFF2` | — | — | — |
| 24 | +`$68` (`$FF:C725`) | `$06:FFDD` | — | — | — |
| 25 | +`$2C` (`$FF:C83F`) | `$07:FFB2` | — | — | — |

- Under HiROM, `$0n:FFxx` reads file `0x0nFFxx`. Under ExHiROM it reads file `0x4nFFxx`.
- Copying only bank `$00` covers set 17's entry only. Kano, Liu Kang and sets 18/20/21/24/25 would get garbage tiles.
- Proof that these are live data: `lowbank_tiles.png`. Liu Kang's stance uses 4 tile refs from the bank-`$07` entry and renders correctly under HiROM mapping. Listing: `c22_lowbank_entries.txt`.

Fix (pick one):
- (a) OR `$80` into those 9 bank bytes (4-byte entries in bank `$FF`, trivial to patch); or
- (b) mirror file `0x008000`-`0x07FFFF` (upper halves) into `0x408000`-`0x47FFFF`.

Option (b) costs the upper halves of banks `$40`-`$47` for new data.

Still unaudited: sound/SPC data, fight-stage metatile data, other loaders not reached by the tracer. The rest of the recipe (map mode `$35`, new data in `$41`-`$7D`) is standard and stays LIKELY.

## C23: shared-lib bugs. **holds** (CONFIRMED)

- `snes.to_off(0xFF7BC2)` and `snes.to_off(0xFE0000)` return `None` (bank masked with `$7F` before the WRAM test).
- `snes.disasm` raises `CS_ERR_MODE` **only for m16 = False and x16 = False**; the other three width combinations work.
- `scripts/umk3/u.py` monkey-patches `to_off`, and `d65.py` is a capstone-free disassembler.
- `lib/snes.py` still has both bugs, so it was not "fixed" in place.

---

## Other findings worth carrying into the mod map

Both points below were checked with my own disassembler and are not among the claims (CONFIRMED):

1. **Animation-table loaders are swapped in the umk3 notes.**
   - `$88:95A0` (entry `$88:95A4`) reads **`$88:95C3`**. It returns the script address unchanged if the table word is 0.
   - `$88:9576` reads **`$88:9633`**.
   - `$88:9633` = `$88:95C3` + `$98` for every ID except 11 (null) and 27 (Kahn: both `$88:BB97`).
2. **Animation script command dispatch.**
   - The interpreter `$88:87DD` indexes `$88:89E2` with `(word EOR $FFFF) × 2`.
   - `$FFFF` → `$883C` (jump), `$FFF8` → `$8804` (per-fighter branch), `$FFEA` → `$89AD`.
   - The `$FFF8` operand is byte fighter ID + word target. It is not word-aligned, so a naive word scan of the scripts misreads them.
