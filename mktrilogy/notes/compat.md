# Compatibility notes: MK3 / MK2 vs UMK3 (SNES), and the ExHiROM audit

Scope: static analysis only, of the user's three ROM files (read-only):
`/home/claude/work/roms/{umk3,mk3,mk2}.sfc`. Nothing was emulated or downloaded.
All scripts are in `/home/claude/work/scripts/compat/`, and all evidence (PNG/TXT/PKL) is in
`/home/claude/work/out/compat/`. Run every script with `python3 -I <script>`.

Tags: **CONFIRMED** means re-checked byte-for-byte or by decoding. **LIKELY** means a strong inference
that was not proven. Every claim carries an evidence string (script, output file, address).
Addresses use HiROM notation (`$Cx:xxxx` = file offset `0x0x xxxx`); code addresses use `$8x`.

## 0. Short answers

1. **UMK3 is NOT a superset of MK3.** 1,047,940 of MK3's 4,194,304 bytes (25%) have no >=32-byte
   match in UMK3. What was dropped:
   - Sheeva (her whole sprite set, palettes, VS portrait and select portrait);
   - all Animality sprites, plus the ANIMALITY and MERCY banners;
   - 8 stages (Subway, Street, Bank, Balcony, Bridge, Soul Chamber, Kahn's Tower, Temple) and the Vortex sky;
   - the MK3 select and logo screens;
   - about 55 KB of BRR-like sample data;
   - MK3-only code.

   **CONFIRMED** (sections 1.1-1.6).
2. **MK2 → UMK3: most of the data layer converts mechanically, but the fighter code does not.**
   - **Use as is:** the LZ decompressor, sprite set header, frame byte format, raw tiles, box tables
     and palette format.
   - **Trivial converter:** compressed tile groups (one threshold byte per group; verified lossless
     on all 17 MK2 sets).
   - **Remapping converter:** animation scripts (set numbers, jump targets, fighter IDs, sound IDs,
     code pointers, animation numbers).
   - **Port or rewrite:** the per-fighter move/special code. MK2 object RAM has a different layout
     (11 slots with $16-byte arrays vs UMK3's 12 slots with $18-byte arrays, at different bases).

   Section 2 has the verdict for each layer.
3. **MK2 inside UMK3: about 37 KB matches.** It is engine tables, code fragments, sound-driver/sample
   areas and padding. None of MK2's sprite, stage or palette assets survive in UMK3.
   **CONFIRMED** (section 3).
4. **ExHiROM is feasible with one data patch.**
   - Traced code shows no bank masking, no reads through banks $00-$7D, and no header or checksum
     reads.
   - **However, 9 tile-directory entries use bank bytes $00-$07.** In ExHiROM these would read from
     file 0x400000+, so they must be patched to $C0-$C7. This corrects umk3-map 11.2 step 1.
   - Section 4 gives a safe 6/8 MB recipe.

## 1. MK3 vs UMK3 block match (task 1)

Method:
- `blockmatch.py mk3 umk3 32` hashes every 32-byte window of UMK3 (64-bit polynomial hash) and
  extends the matches.
- Coverage classes: 0 = unique, 1 = filler, 2 = moved, 3 = same offset.
- Output: `match_mk3_in_umk3_k32.{txt,png,pkl}`.
- Totals: unique 1,047,940, filler 5,219, moved 3,118,196, same offset 22,949. **CONFIRMED**.

`attrib.py` assigns every MK3 byte to a known structure (in priority order: sprite-set footprint,
stage/screen streams, VS portraits, palettes, code banks). Output is in `attrib_mk3.txt`.
Unique bytes by category:

| category | bytes | not in UMK3 |
|---|---:|---:|
| sprite set 11 (Sheeva) | 210,036 | 210,030 |
| sprite set 21 (animalities/banners) | 99,714 | 99,712 |
| sprite set 19 (banners) | 54,705 | 36,579 |
| sprite set 18 | 71,374 | 16,749 |
| sprite set 22 (fatality FX) | 42,728 | 10,309 |
| sprite set 5 (Stryker) | 153,797 | 8,159 |
| other sprite sets (each) | – | < 1,200 |
| stage/screen LZ streams + palettes | 364,326 | 281,589 |
| VS portraits | 113,800 | 11,121 |
| palettes (table $86:F0FC) | 7,264 | 678 |
| code banks $80-$88 (upper halves) | 242,463 | 172,417 |
| other (unattributed) | 550,643 | 189,946 |

### 1.1 MK3 tables used (decoder `spr.py`, GAMES['mk3'])

| What | Location | Status |
|---|---|---|
| Sprite-set pointer tables | `$85:ABAA` / `$85:ABDE` (26 sets) | **CONFIRMED** |
| Palette table | `$86:F0FC` (230 entries) | **CONFIRMED** |
| Primary / alternate palette IDs | `$86:F3AE` / `$86:F3C0` | **CONFIRMED** |
| Animation table | `$86:DC53` | **CONFIRMED** |
| Stage/screen records | `$82:B888` (26 records) | **CONFIRMED** |
| VS portrait tables (15 entries) | bank `$80:F414`, tiles `$80:F432`, map `$80:F450`, palette `$80:F46E` | **CONFIRMED** |

- Evidence that the decoder is right: `selftest_spr.py` matches the umk3 analyst's decoder on 761 frames and the mk2 analyst's decoder on 595 frames, with 0 mismatches.
- The roster render is `mk3_roster.png`.

MK3 fighter IDs:

| ID | Fighter | ID | Fighter |
|---:|---|---:|---|
| 0 | Kano | 9 | Kung Lao |
| 1 | Sonya | 10 | Kabal |
| 2 | Jax | **11** | **Sheeva** |
| 3 | Nightwolf | 12 | Shang Tsung |
| 4 | Sub-Zero | 13 | Liu Kang |
| 5 | Stryker | 14 | Smoke (robot; set 14 = set 7 header) |
| 6 | Sindel | 15 | Motaro |
| 7 | Sektor | 16 | Shao Kahn |
| 8 | Cyrax | 17 | Noob Saibot (set 0 with palette 3, i.e. black Kano) |

Status: **CONFIRMED** by render (`mk3_roster.png`).

### 1.2 Fighters dropped: Sheeva

The sprite set:
- Set 11, header `$86:9B3F`, 204 frames.
- Footprint 210,036 B (tables 1,464, frames 25,345, tiles 183,227).
- Only 6 bytes and 28 of 7,413 decoded tiles occur anywhere in UMK3.
- Evidence: `foot.py mk3 umk3`, output `foot_mk3_umk3.txt` (the set 11 line). **CONFIRMED**.
- Four arms visible in `mk3_set11_sheeva.png`. **CONFIRMED**.

Other assets:
- Palettes $4A/$4B (via `$86:F3AE`/`$86:F3C0`[11]). **CONFIRMED** by render.
- VS portrait: entry 11 has tiles `$C9:0000` (10,817 B packed), map `$C9:2A41` and palette `$C9:2B1C`. Raw bytes found in UMK3: 0. Evidence: `vscmp.txt` line "MK3 VS 11". **CONFIRMED**.
- Select-screen portrait: on the MK3 select screen (`mk3_select_L0.png`), which has no UMK3 counterpart. **CONFIRMED**.

Code:
- Sheeva's move code was not separated from the MK3-only code (172 KB unique in the code banks). Open question.

Every other MK3 fighter's set is fully present in UMK3:
- Every decoded tile is found. Some tables and frames have moved.
- Set 5 (Stryker) has 7.4 KB of frame bytes that differ.
- Evidence: `foot_mk3_umk3.txt`. **CONFIRMED**.

### 1.3 Animalities, banners, effects (set 21/19/18/22)

| Set | What was dropped | Evidence / status |
|---|---|---|
| 21 (header `$85:ACA2`, 169 frames) | Frames ~1-115 are animal sprites. 99,712 of 99,714 bytes are absent from UMK3; 64 of 5,631 decoded tiles are found. | `sheet_mk3_set21.png` vs `sheet_umk3_set21.png`. **CONFIRMED** |
| 19 | The ANIMALITY banner and the name banners of the dropped stages (36,579 B unique) | `uniq_mk3_set19.png`. **CONFIRMED** |
| 18 | Frames 206-212 are the MERCY banner | `uniq_mk3_set18.png`. **CONFIRMED** |
| 22 | 21 fatality/friendship effect frames | `uniq_mk3_set22.png`. **CONFIRMED** that they are unique; which move uses each frame is **LIKELY** |

The MK3 animality scripts are around `$84:AC9E`-`$84:B0xx`. **LIKELY**: located from frame-ID references; the routine boundaries were not traced.

### 1.4 Stages and screens

Method:
- `stagecmp.py` parses the MK3 records at `$82:B888` (26) and the UMK3 records at `$84:8A22` (29).
  - Type 1 layer descriptors hold palette +$15, tiles +$18, map +$1D.
  - Type 0 hold palette +$17, tiles +$1A, map +$1F.
- `stagetiles.py` compares decoded 8x8 tiles. Output: `stagetiles.txt`.

| MK3 rec | Stage | In UMK3? | Status |
|---:|---|---|---|
| 0 | The Subway | No: 0 of 627/80 tiles | **CONFIRMED** |
| 1 | The Street | No: 1 of 556/219 tiles | **CONFIRMED** |
| 2 | The Bank | No. Its L0 skyline (`$C5:0000`) is Rooftop's L0. L1 (`$C8:920B`) and L3 (`$C8:780F`) are absent. | **CONFIRMED** |
| 3 | Rooftop | **Kept** as UMK3 rec 0 (100% of tiles) | **CONFIRMED** |
| 4 | The Balcony | No: 0 of 443/496 tiles | **CONFIRMED** |
| 5 | The Bridge | No: 1 of 542 and 4 of 421 tiles | **CONFIRMED** |
| 6 | Soul Chamber | No: 0 of 485 and 1 of 521 tiles | **CONFIRMED** |
| 7 | Shao Kahn's Tower | No: 1 of 950 tiles | **CONFIRMED** |
| 8 | The Temple | No: 1 of 559 and 1 of 307 tiles | **CONFIRMED** |
| 9 | The Pit 3 | **Kept** as UMK3 rec 6 (100%) | **CONFIRMED** |
| 10 | The Vortex | L0 = Pit 3 tiles (kept). The L1 sky (`$C6:0000`, 563 tiles) is absent (`mk3_rec10_L1.png`). | **CONFIRMED** |
| 13 | MK3 select screen | No: 4 of 1,227 tiles (`mk3_select_L0.png`) | **CONFIRMED** |
| 15 | MK3 logo screen | No: 0 of 652 tiles (`mk3_rec15_L0.png`) | **CONFIRMED** |
| 12, 14/16/19 | Unidentified screens (`$D5:1678`, 972 tiles; `$C8:3FFF`, 256 tiles) | Absent. Purpose unknown (renders unreadable with the stored palettes, `mk3_screens_12_15_14_10.png`). | **CONFIRMED** absent; purpose open |

Leftovers in UMK3:
- **UMK3 rec 7**: L0 and L1 point their tiles at `$C0:0000`. That is the Pit 3 L1 stream, the same one rec 6 L1 uses, and it decodes to 14,144 B. Their maps are at `$F0:A95D`/`$F0:AB2B`, and neither decompresses.
- **UMK3 rec 8**: every pointer is `$00:0001`.
- Both are leftover stubs. **CONFIRMED** (`stagecmp.descs('umk3',7/8)` + `glz.try_stream`; `exhirom_audit.txt` section C "null marker").
- Which MK3 stage these slots once held is unknown, because the record numbering was not preserved (MK3 3→UMK3 0, 9→6). `tiles_umk3_rec7_L0.png` shows the rec 7 tiles.

### 1.5 Sound

- MK3 has 251,904 bytes in 1 KB windows that score as BRR-like. 55,264 of them have no match in UMK3, mostly in `$CF:B800`-`$D4:4FFF`.
- Evidence: `brrprobe.py`/`brrscan.py` → `brr_masks.pkl`, cross-checked against `match_mk3_in_umk3_k32.pkl`.
- **LIKELY** these are MK3-only samples (for example Sheeva and animality sounds). Neither the BRR classification nor the sample attribution was proven.

### 1.6 Code

- `codematch.py mk3 10` turns each window of 10 traced UMK3 instructions into a pattern (opcodes fixed, operands wildcarded) and searches the MK3 code banks for it.
- 21,390 of 31,656 traced UMK3 instructions (67.6%) have a unique counterpart in MK3. Output: `codematch_mk3.txt`. **CONFIRMED**.
- So MK3 and UMK3 share most engine code with shifted addresses. MK3-only code (172 KB of code-bank bytes absent from UMK3) holds Sheeva, animalities and the dropped stages' logic. **LIKELY**.
- Unattributed MK3-only "other" data includes 3-15 KB runs in `$CF`-`$D5` (mostly BRR-like, see 1.5), plus about 3 KB chunks in `$F0`-`$F5` (for example `$F0:0000`-`$F0:0C0E`, `$F2:11FF`-`$F2:1F41`). The `$F0`-`$F5` chunks are unidentified (open question). Evidence: `attrib_mk3.txt`, "largest unique runs".

## 2. MK2 → UMK3 engine compatibility (task 2, most important)

Both games use the same Sculptured Software engine lineage. Shared design:
- a 16-byte set header;
- frame ID = set<<9 | frame;
- frame = N, B, nibble positions against a 32-byte delta table, and tile words (bits 0-1 flip, 2-7 directory offset, 8-15 index);
- a 4-byte tile-directory entry (word address, bank, flags);
- backward LZ;
- animation word scripts;
- struct-of-arrays object RAM.

### 2.1 Verdict table

| Layer | MK2 | UMK3 | Verdict | Evidence | Tag |
|---|---|---|---|---|---|
| General LZ decompressor | `$85:B9FC` | `$88:AD30` | **Use as is.** The routines differ only in DP/WRAM operands. All 266 MK2 streams decode byte-identically with both ports. | `rcmp.py mk2 0x85B9FC umk3 0x88AD30 200` → "200/200 insns, identical 129, same-opcode 71, differing 0" (`rcmp_lz_mk2_umk3.txt`); `lzcross.py` | **CONFIRMED** |
| Sprite-set header (16 B) | `$84:CDCC`/`$84:CDEE` (17 sets) | `$86:EAEC`/`$86:EB24` (28) | **Use as is.** Same field layout. Field +9 ("shadow" pointer) is stored by UMK3 only at `$88:A4BA` and never read. | `spr.py` decodes both with one parser; `selftest_spr.py` | **CONFIRMED** (layout); +9 unused is **LIKELY** (traced code only) |
| Frame-pointer/bank tables, frame bytes, delta table | – | – | **Use as is** (same byte format) | `selftest_spr.py`, `convert_test.py`: the same frame bytes decode in the UMK3 path | **CONFIRMED** |
| Raw 4bpp tile groups (flag $20) | – | – | **Use as is** | `convert_test.py` keeps them unchanged; 0 mismatches | **CONFIRMED** |
| Compressed tile groups (flag $80\|stride) | `$81:834B`: record n at base+n*s, fill 0 | `$83:8362`/`$83:8474`: byte T first, record n at base+1+n*s, records n>=T carry a fill byte; flag bit 6 = 2bpp | **Trivial converter** (2.2) | `convert_test.py` (all 17 sets) → `convert_test.txt`: 0 mismatches over every referenced tile | **CONFIRMED** |
| Box/collision table (header +$E) | `$85:C165` | `$88:A6A6` | **Use as is** (same table reader, same default tables `$84:CFC6` vs `$86:EC3C`, same `[dp],Y` with Y=(frame-1)*4). UMK3 adds a flip-aware X offset from `$2DE4,X` (negated when `$5480` bit $4000 is set). | `rcmp.py mk2 0x85C165 umk3 0x88A6A6 45` → 17 identical / 18 same-opcode / 20 differing | **CONFIRMED** for the data format; the extra flip offset is **LIKELY** harmless for MK2 data |
| Palettes | `$85:D33D` (174) | `$88:9984` (309) | **Same format** (16 colours BGR555; loader copies colours 1-15). But the UMK3 table is full, so new entries need a relocated or extended table plus new `$88:9D23`/`$88:9D3F` slots. | MK2 `$83:F8CC` loop `LDY #$001E … DEY DEY BNE`; UMK3 `$85:CDA2` (umk3-map 5) | **CONFIRMED** |
| Animation scripts | interpreter `$83:F28E`, dispatch `$83:F32C` | interpreter `$88:87DD`, dispatch `$88:89E2` | **Converter with remapping** (2.3) | `$88:89E2` has 22 entries, FFFF→`$88:883C` … FFEA→`$88:89AD`; MK2 handles FFFF..FFF7 | **CONFIRMED** encoding for FFFF..FFF7; per-command semantics **LIKELY** for FFF9/FFFA |
| Common/specific animation tables | specific + common, common = specific + $84 (66 words) | `$88:95C3` + `$88:9633` (second = first + $98, 76 words) | **Remap needed.** The numbers agree for only about the first 6 entries. | `animcmp.py` → `animcmp_mk2_1_umk3_13.png` | **LIKELY** |
| Fighter object WRAM | 11 slots, word arrays $16 apart | 12 slots, word arrays $18 apart; other bases | **MK2 code cannot run as is**: every WRAM operand differs | `codematch.py mk2 6` → `codematch_mk2.txt`: UMK3 `$345C`/`$34A4`/`$34BC`/`$34D4` (= base + k*$18, k=0,3,4,5) → MK2 `$2C80`/`$2CC2`/`$2CD8`/`$2CEE` (= base + k*$16); block `$3662`-`$36E0` → `$2E82`-`$2F04` (delta about -$7E0); DP `$26`-`$7C` → -4 | **CONFIRMED** (stride/slot count from translation pairs) |
| Move/special/AI code | – | – | **Port or rewrite in UMK3 style** | Only 14.3% (W=10) / 20.5% (W=6) of traced UMK3 instructions have an MK2 skeleton match, against 67.6% for MK3 | **CONFIRMED** (the numbers); "rewrite" is a recommendation |
| Stage containers | MK2 stage format (mk2-map 9) | UMK3 records `$84:8A22` (type 0/1 descriptors) | **Converter.** The LZ streams can be used as is, but the descriptors and records must be rebuilt in UMK3 form. | `stagecmp.py`, mk2-map 9 | **LIKELY** (no MK2 stage was rebuilt and rendered through UMK3 tables) |
| Per-frame budget | donors: Cage max 69 tiles/29 pieces, Baraka 86/29, Raiden 92/32, Kintaro 106/39 | UMK3 max observed 133 tiles (set 22), 62 pieces (set 15) | **Fits** within UMK3's observed maxima | `framestats.py` → `framestats.txt` | **LIKELY** (the hard engine limit was not found) |

### 2.2 Tile-group converter (`convert_test.py`, CONFIRMED lossless)

For every compressed group referenced by the donor set:

1. `mx` = the highest tile index used by any frame.
2. Emit a new blob: byte `T = mx+1`, followed by the original `(mx+1)*stride` record bytes, unchanged.
3. If `mx = 255`, T would be 256, which is impossible. Instead emit `T = 255` and insert a `$00` fill byte
   before record 255. It is the last record, so no other record moves.
4. Point the directory entry (word address + bank) at the blob. Keep the flags.
5. Raw groups (`$20`) stay as they are.
6. Each blob must sit inside one 64 KB bank:
   - The records are addressed as `bank | ((base+1+n*s) & $FFFF)`. In the 2bpp path the fetch is
     `ADC $56; TAY; PLB; LDA $0000,Y` (`$83:838C`-`$83:8390`), which wraps within the bank.
     **CONFIRMED** for that path; **LIKELY** for the compressed path `$83:8474`.
   - Every existing UMK3 group ends at or before `$xx:FFFF` (see 4.3).

Results (`convert_test.txt`):

| Set | Fighter | Tile refs | Mismatches | Added bytes | Groups using index 255 |
|---:|---|---:|---:|---:|---|
| 2 | Cage | 7,909 | 0 | 74,125 | 1 |
| 3 | Baraka | 7,620 | 0 | 81,722 | none |
| 6 | Raiden | 7,689 | 0 | 90,247 | 5 |
| 9 | Kintaro | 5,249 | 0 | 46,256 | 1 |

- All 17 MK2 sets were tested: 0 mismatches. **CONFIRMED**.
- Visual check: `convert_test.png` (MK2 decode next to the converted decode through the UMK3 codec).
- Note: in the existing UMK3 groups checked in 4.3, T is always `max_index+1`, which is the same rule.

### 2.3 Animation-script converter (spec)

- Frame-ID words: `set<<9|frame`. Rewrite the set number to the new UMK3 set slot. The frame number is unchanged.
- `$FFFF addr` (jump): rewrite the target. Scripts stay in the same bank as the table.
- `$FFF8 byte fid, word target` (per-fighter branch; UMK3 handler `$88:8804`): rewrite the fighter ID to the UMK3 ID and rewrite the target.
- `$FFF9 word` (sound call): remap MK2 sound IDs to UMK3 sound IDs. The mapping is unknown (open question).
- `$FFFA` (6 bytes; contains a code pointer): the code must exist in UMK3, so this needs porting.
- `$FFFD` (4 bytes) and `$FFFC` (6 bytes): same lengths in both games.
- Animation numbers (indices into the common/specific tables):
  - 76 in UMK3 vs 66 in MK2.
  - Build a remap table by matching the first frame of each animation (`animcmp.py`).
  - **LIKELY** about 6 agree directly.
- UMK3-only commands `$FFF6`-`$FFEA` are not produced by MK2 data. Their semantics were not needed (open question).

### 2.4 Plan per donor (Baraka, Johnny Cage, Raiden, Kintaro)

1. Graphics: copy the frame tables and raw groups. Convert the compressed groups (2.2).
2. Add new set slots: grow `$86:EAEC`/`$86:EB24` (28 entries now) or reuse the free fighter IDs 11 and 25 (umk3-map).
3. Palettes: append to a relocated palette table and add `$88:9D23`/`$88:9D3F` entries.
4. Scripts: convert (2.3).
5. Move, special and AI code: write new UMK3-style code. MK2 code would need every WRAM and DP operand translated (2.1, object row), plus different slot loops. It is not worth porting directly.
6. Kintaro is a boss like UMK3's Motaro/Kahn (set 15: 106 tiles/62 pieces max), so frame size is not a problem. **LIKELY**.

## 3. MK2 vs UMK3 block match (task 3)

- `blockmatch.py mk2 umk3 32` → `match_mk2_in_umk3_k32.txt`: unique 3,108,523, filler 8,812, moved 28,264, same offset 129. In total about 37 KB of MK2 is found in UMK3. **CONFIRMED**.
- What matches:
  - Engine lookup tables: MK2 `$C4:C7A9`-`$C4:CDCB` → UMK3 `$C6:E369`-`$C6:EAEC`. These end exactly where the UMK3 sprite-set tables begin.
  - Unrolled code fragments.
  - The sound-driver/sample region MK2 `$CE:8E00`-`$CF:5000` (banks `$CE`/`$CF` account for 24,425 matched bytes).
  - `$FF` padding.
  - **CONFIRMED**.
- No MK2 fighter-sprite tile, stage stream or palette occurs in UMK3. Banks `$C6`, `$C9`, `$CD`, `$D0`-`$D3`, `$DA`, `$DB` have 0 matched bytes. **CONFIRMED**.
- So the four donors (and every MK2 stage) are all-new data for the hack.

## 4. ExHiROM audit of UMK3 (task 4)

Script: `exhirom_audit.py` → `exhirom_audit.txt`.

ExHiROM mapping:
- `$C0`-`$FF` and `$80`-`$BF:8000+` → file 0-4 MB.
- `$40`-`$7D` and `$00`-`$3F:8000+` → file 4-8 MB.
- The header moves to file 0x40FFC0.

### 4.1 Code (traced, 31,656 instructions)

- **A1, long operands into banks `$00`-`$7D`:**
  - 24 traced instructions look like ROM-bank hazards. All are ASCII text decoded as EOR/AND/SBC (for example `$83:BC97 EOR $415452` = "RTA"; menu text in bank `$83`), or inline data in `$86:FC72`. None is reachable code.
  - The other 40 are I/O or WRAM mirrors (`$00`-`$3F:0000`-`$7FFF`), which are fine.
  - **CONFIRMED** (listing in `exhirom_audit.txt` A1).
- **A2:** no `PLB` sets DB to a ROM bank < `$7E` from an immediate. **CONFIRMED** within the trace.
- **A3, bank masking:**
  - The AND/ORA masks found operate on WRAM flag bytes (`$1C1F,X`, `$1C22,X`, `$1BA7,X`) or on the 8-bit multiplier input (`$83:8482`/`$83:8513`, `AND #$3F` → `STA $804202`). None clamps a bank byte. **CONFIRMED**.
  - `$80:4202` is an I/O write through bank `$80`. Fine.
- **B, header/checksum reads:**
  - No traced instruction reads `$xx:FFB0`-`$FFFF`. All 86 byte-pattern hits are untraced bytes in banks `$80`-`$88`, 50 of them in `$87`/`$88`. Most are pairs of `$FFxx` words (script/table data), not instructions.
  - So there is no checksum or anti-tamper check in the traced code. **CONFIRMED** (trace); **LIKELY** for untraced code.
- **D, LZ call sites:**
  - The traced callers load source banks `$E1` (`$83:C067`, `$83:C081`), `$C3` (`$86:DD7F`) and `$E3` (`$87:EEE4`). The destination bank is `$7F` (WRAM).
  - The others (`$84:943E`, `$84:98B0` wrapper, `$84:A4B8`) take the source from tables, which are checked under C.
  - **CONFIRMED** for the immediates; **LIKELY** for `$84:A4B8`.
- **DB-relative fetch:**
  - The sprite tile fetch pushes the group's bank and does `PLB`, then reads `LDA $0000,Y` (2bpp path `$83:838F`/`$83:8390`; also `$83:84C5`).
  - New tile data therefore must not be addressed through banks `$00`-`$3F`: offsets below `$8000` there are WRAM/I/O.
  - Banks `$40`-`$7D` (full 64 KB) and `$C0`-`$FF` are fine.
  - **CONFIRMED** (disassembly `show('umk3',0x838362,40)`).
  - This qualifies umk3-map 11.5 ("probably absent"): the pattern exists, and it is safe only because of where data is placed.

### 4.2 Data structures (C)

Bank bytes < `$80` in:

| Structure | Entries checked | Bank bytes < $80 |
|---|---:|---:|
| Sprite-set header pointers | 27 headers | 0 |
| Frame-bank bytes | 83 | 0 |
| Palette pointers | 309 | 0 |
| Animation-table pointers | 56 | 0 |
| VS bank bytes | 26 | 0 |
| Stage-layer pointers | 183 | 0 real (45 null markers `$00:FFFF`/`$00:0001`, never dereferenced as ROM) |
| **Tile-directory entries referenced by frames** | 917 | **9** |

Status: **CONFIRMED**.

### 4.3 The 9 low-bank tile groups (must be patched)

| set | dir entry | group address | flags (stride) | max idx (T) | bank-byte file offset |
|---:|---:|---|---|---:|---|
| 0 | 13 | `$05:FF3D` | $86 (6) | 31 (32) | 0x3FB3F5 |
| 0 | 27 | `$04:FFDA` | $85 (5) | 6 (7) | 0x3FB42D |
| 13 | 0 | `$07:FFFB` | $84 (4) | 0 (1) | 0x3FB832 |
| 17 | 17 | `$00:FF86` | $85 (5) | 7 (8) | 0x3FC68F |
| 18 | 17 | `$02:FF71` | $86 (6) | 22 (23) | 0x3FC52F |
| 20 | 9 | `$01:FFD4` | $95 (21) | 1 (2) | 0x3FCAD3 |
| 21 | 14 | `$03:FFF2` | $8D (13) | 0 (1) | 0x3FD4ED |
| 24 | 26 | `$06:FFDD` | $8B (11) | 2 (3) | 0x3FC727 |
| 25 | 11 | `$07:FFB2` | $89 (9) | 7 (8) | 0x3FC841 |

Evidence: `exhirom_audit.txt` C; the directory scan in this note was re-run with `spr.Set(...).tiledir + 4*e + 2`. **CONFIRMED**.

What these groups are:
- They are the tails of code banks `$C0`-`$C7`, packed right after the `$FF` runs that umk3-map 11.1 lists as free. For example, the `$C0:FF1F` run (103 B) ends at `$C0:FF85`, and the group starts at `$FF86`.
- So those tails are **not** free beyond the `$FF` run.
- The `$00:FF86` group ends at `$FFAE`, before the header at `$FFC0`.
- **CONFIRMED** (extents computed from the max index used × stride).

What breaks in ExHiROM:
- `$0b:FFxx` would read file 0x4b FFxx instead of 0x0b FFxx.
- 179 + 186 + 104 + … frames would draw garbage. For example, set 13 entry 0 is used by 179 frames, and set 0 entry 13 by 186.

Notes on the scan:
- Only the 917 entries referenced by decoded frames were checked.
- A blind scan of 64 slots per directory finds more "low" values. These lie past each directory's real end (the directories are packed, so later slots are other tables), and several are the same 9 bytes seen through a neighbouring directory (for example 0x3FB3F5 = set 6 slot 55).
- **LIKELY** that no unreferenced real entry matters.

### 4.4 Safe recipe (8 MB; 6 MB variant below)

1. Start from the 4 MB file. Pad to 8 MB (0x800000) with `$FF`.
2. Copy file 0x008000-0x00FFFF to 0x408000-0x40FFFF. This covers bank `$00`'s vectors, the reset/IRQ/NMI/BRK stubs (`$00:83D6`-`$83F1`, `$8738`, `$8765`), the header, and the `$00:FF86` tile group.
3. Patch the 9 bank bytes in 4.3 from `$0b` to `$Cb` (`$05`→`$C5`, `$04`→`$C4`, `$07`→`$C7`, `$00`→`$C0`, `$02`→`$C2`, `$01`→`$C1`, `$03`→`$C3`, `$06`→`$C6`, `$07`→`$C7`). After this, no existing pointer goes through `$00`-`$7D`.
4. Header at 0x40FFC0 (and, harmlessly, also at 0x00FFC0):
   - map mode `$35`;
   - ROM size `$0D`;
   - recompute the checksum/complement, at least in the 0x40FFDC copy.
   - No code reads the header (4.1 B).
5. New data:
   - Put it in banks `$40`-`$7D` (file 0x400000-0x7DFFFF minus the 0x408000-0x40FFFF copy). That is about 3.9 MB.
   - Address it as `$4x`/`$5x`/…, never through `$00`-`$3F` (DB-relative tile fetch, 4.1).
   - Keep each tile group inside one bank.
   - File 0x7E0000-0x7FFFFF can only be reached as `$3E`/`$3F:8000+` (`$7E`/`$7F` are WRAM). Use it only for `[dp]`-pointer data, not tile groups.
6. New code:
   - It can run from `$40`-`$7D` (SlowROM speed).
   - Hooks go in the existing `$C0`-`$C7` `$FF` runs. Only the runs: not the bank tails after them (4.3).
7. 6 MB variant:
   - Same steps, but the file is 0x600000. New data goes in `$40`-`$5F` (2 MB).
   - **LIKELY** fine on hardware and flash carts. The header size byte stays `$0D`.
   - The checksum convention for a 6 MB image (4 MB + 2 MB mirrored ×2) is not verified (open question).

Status: **LIKELY** as a whole (no emulator run, by rule). Every individual hazard check above is **CONFIRMED** within the traced code and the listed tables.

## 5. Corrections to the other analysts' notes

### umk3-map.md

| # | Section / line | Note says | This audit found | Evidence | Tag |
|---|---|---|---|---|---|
| U1 | 4.x, lines 154-155 | `$88:95C3` is "Loaded by `$88:9576`"; `$88:9633` by `$88:95A0` | Reversed. **`$88:9576` reads `$88:9633`** (`LDA $889633,X`), and **`$88:95A0` reads `$88:95C3`** (`LDA $8895C3,X`). | `show('umk3',0x889576,14)` / `show('umk3',0x8895A0,14)` | **CONFIRMED** |
| U2 | Line 530 | `$80:C794` per-kode words (`$2A17`-`$2A29`) are "**LIKELY** a sound or speech call ID" | They are **frame IDs in sprite set 21** ($2A17>>9 = 21): the kode-message banners. They are read at `$80:C733` (`LDA $80C794,X`, BMI = none), passed to the animation path and stored to `$52F8,X` via `$88:8798`/`$88:87A2`. | `umk3_80C794_banners.png` (renders of these frame IDs) | **CONFIRMED** |
| U3 | Line 48 | "ID 11 … is completely empty: null animation pointer, null name, palette 0" | Mostly right, but the per-fighter jump table `$83:F29D`[11] = `$83:FC9E` is non-null: it points at a leftover routine. A new fighter in slot 11 must re-point it. | `w16('umk3',0x83F29D+22)` = `$FC9E` | **CONFIRMED** (non-null); its purpose is open |
| U4 | 11.2 step 1 ("every existing 24-bit pointer stays valid") and 11.3 ("LIKELY compatible") | – | **False for 9 tile-directory entries** with bank bytes `$00`-`$07`. They must be patched (4.3). | `exhirom_audit.txt` C | **CONFIRMED** |
| U5 | 11.1 | "Each code bank `$C0`-`$C7` ends with a run of about 87-103 `$FF` bytes near `$xx:FF00` … Good for small hooks" | Right for the `$FF` run only. **The bytes after each run up to `$xx:FFFF` are compressed sprite tile groups** (4.3). Do not extend hooks past the run. | 4.3 extents | **CONFIRMED** |
| U6 | 11.5 | "Code that sets DB from a data bank and then uses absolute addressing … probably absent" | **Present.** The sprite tile fetch does `PLB` to the tile bank and then `LDA $0000,Y` (`$83:838F`). It is safe in ExHiROM only if new tile data is addressed through `$40`-`$7D` or `$C0`-`$FF`. | `show('umk3',0x838362,40)` | **CONFIRMED** |
| U7 | 11.4 (no checksum check) | – | Agrees; extended: 0 traced reads of `$xx:FFB0`-`$FFFF` in any bank | `exhirom_audit.txt` B | **CONFIRMED** (traced) |
| U8 | Sprite-set header field +9 | – | Written only at `$88:A4BA` and never read by traced code (unused in UMK3) | trace search | **LIKELY** |

### mk2-map.md

| # | Section / line | Note says | This audit found | Evidence | Tag |
|---|---|---|---|---|---|
| M1 | 7, line 269 | Loader `$83:F8CC` "copies 32 bytes" | It copies **30 bytes = colours 1-15**: `LDY #$001E`, then `LDA [$0A],Y`/`STA ($06),Y`/`DEY`/`DEY`/`BNE`, so Y=0 (colour 0) is never copied. This is the same as UMK3. | `show('mk2',0x83F8CC,30)` | **CONFIRMED** |
| M2 | 1 (lines 48-50) and 12 | The MK2 sprite tile codec "was not found" in MK3/UMK3; "LIKELY a different sprite codec/animation engine; donor sprites will need re-encoding" | **Same codec family.** UMK3 adds only a per-group threshold byte and a fill byte for records >= T. The conversion is a byte insertion, not a re-encode, and is lossless on all 17 sets. The animation command encoding FFFF..FFF7 is also the same. The earlier byte patterns failed because the WRAM/DP operands differ. | 2.1, 2.2, `convert_test.txt` | **CONFIRMED** |
| M3 | 12 | General LZ "LIKELY" the same | Upgraded: 200/200 instructions, 0 differing; streams cross-decode identically | `rcmp_lz_mk2_umk3.txt`, `lzcross.py` | **CONFIRMED** |
| M4 | 1 (line 51, "stages may not [need converting]") | – | The LZ streams can be used as is, but the stage records and layer descriptors are a different container (`$84:8A22`, type 0/1). A converter is needed. | `stagecmp.py` | **LIKELY** |

## 6. Evidence index (scripts in `/home/claude/work/scripts/compat/`)

| Script | What it does / produces |
|---|---|
| `c.py` | ROM loader and the address helpers `to_off`, `w16`, `p24`, `show`, `A` |
| `spr.py` | Generic three-game sprite decoder |
| `selftest_spr.py` | Cross-check of `spr.py` against the analysts' decoders |
| `blockmatch.py` | → `match_{mk3,mk2}_in_umk3_k32.*` |
| `foot.py` | → `foot_mk3_umk3.txt` |
| `attrib.py` | → `attrib_mk3.txt/pkl` |
| `stagecmp.py`, `stagetiles.py`, `stagerender.py` | → `stagecmp.txt`, `stagetiles.txt`, `mk3_rec*_L*.png`, `tiles_*` |
| `vscmp.py` | → `vscmp.txt`, `mk3_vs_portraits.png` |
| `uniqframes.py`, `setsheet.py`, `tilesheet.py` | → `uniq_mk3_set{18,19,22}.png`, `sheet_*_set{19,21}.png` |
| `mk3_roster.py` | → `mk3_roster.png`, `mk3_set11_sheeva.png` |
| `brrprobe.py`, `brrscan.py` | → `brr_masks.pkl` |
| `codematch.py` | → `codematch_{mk2,mk3}.txt`, `codematch_mk2_ranges.txt` |
| `rcmp.py`, `findcode.py` | Routine diffs (`rcmp_lz_mk2_umk3.txt`) |
| `glz.py`, `lzcross.py` | LZ cross-validation |
| `convert_test.py` | → `convert_test.txt/png` |
| `animcmp.py` | → `animcmp_mk2_1_umk3_13.png` |
| `framestats.py` | → `framestats.txt` |
| `exhirom_audit.py` | → `exhirom_audit.txt` |
| (other) | `umk3_80C794_banners.png` (U2) |

## 7. Open questions

1. What are the MK3-only data chunks of about 3 KB in `$F0`-`$F5`, and MK3 records 12 and 14/16/19 (`$D5:1678`, `$C8:3FFF`)?
2. Which samples are in the 55 KB of MK3-only BRR-like data, and where is the MK3 sample directory?
3. UMK3 type-0 stage map format details (needed for an MK2 stage-container converter).
4. Full MK2 → UMK3 animation-number remap (66 → 76 entries), and the semantics of UMK3-only commands `$FFF6`-`$FFEA`.
5. MK2 → UMK3 sound-ID mapping for `$FFF9` (and for move code).
6. The engine's hard per-object limit on pieces/tiles/VRAM (only observed maxima are known).
7. Where Sheeva's MK3 move/AI code is (if she is to be restored), and what `$83:FC9E` (`$83:F29D`[11]) does in UMK3.
8. Residual ExHiROM risk in code not covered by the trace (the hazard checks above are trace-only).
9. Checksum convention for a 6 MB ExHiROM image.
