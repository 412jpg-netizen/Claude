# Adversarial verification: mk2-map (C1-C21) and compat (T1-T4, corrections)

Verifier scripts: `/home/claude/work/scripts/verify-mk2-compat/` (run with `python3 -I <script>`).
Images and coverage arrays: `/home/claude/work/out/verify-mk2-compat/`.

The other analysts' scripts were not used, with one exception. I read `scripts/compat/vscmp.py`'s docstring
to learn the VS-portrait tile format (6bpp, map value - 1), then rendered the portrait with my own code.

## 0. Method and tooling

* **Disassembler.** `d.py` is my own table-driven 65816 disassembler (all 256 opcodes, M/X widths
  tracked through REP/SEP). It does not use capstone or `snes.py`. `rcmp.py` compares two routines
  instruction by instruction.
* **Mapping.** `d.off` is my own HiROM mapping. WRAM is only banks `$7E`/`$7F`.
* **Shared-lib bug (CONFIRMED).** `snes.to_off(0xFEF13A, 0x400000)` returns `None`, because the lib masks
  the bank with `& 0x7F` before the WRAM test. Banks `$FE`/`$FF` hold UMK3 and MK3 sprite tables and
  palettes. My first version of `d.off` had the same bug; it is now fixed. The umk3-map notes already
  record this bug.
* **Decoders written from my own trace:**
  * MK2 sprite decoder: `mk2spr.py`.
  * MK2/MK3/UMK3 LZ port: `lz.py`, a hand port of `$85:B9FC`, including the type-2 path and the 16-bit
    descending copy chains.
  * UMK3/MK3 tile codec: `umk3spr.py`, from `$83:8362`/`$83:8474`/`$83:850F` and the mask table
    `$83:85AA`.
* **Block matching.** `blockmatch.py` is my own k-byte matcher: 64-bit polynomial window hashes in numpy,
  then a coverage expansion.
* **No emulator.** Everything here is static.

Verdict scale: **holds**, **partly** (core right, a detail wrong), **refuted**, **unverifiable**.

## 1. mk2-map claims

### C1 fighter IDs — holds

* `$83:D126 LDA $83D7B8,X`. X = A*2, where A is stored to `$B6` at `$83:D108`.
* The only caller is `$83:A873 JSL $83AEF1` → `$83:A877 JSL $83D108`.
* `$83:AEF1` loads `$2EF8`, or `$30A6` when `$327E != 1`.
* The table `$83:D7B8` ends where the strings begin, at `$83:D7DA` (file 0x03D7DA). That gives exactly
  17 words: KUNG LAO, LIU KANG, CAGE, BARAKA, KITANA, MILEENA, SHANG TSUNG, RAYDEN, SUB-ZERO, REPTILE,
  SCORPION, JAX, KINTARO, SHAO KAHN, SMOKE, NOOB SAIBOT, JADE ("WINS" strings).
* Evidence: `d.py mk2 83D100`, `d.py mk2 83AEF1`.

### C2 `$2EF8`/`$30A6` → `$4C10,X` — holds

* `$85:C3DA`: `LDA $2EF8`, `STA $06`, `$0E = 0`, `JSL $85C629`.
* `$85:C409`: the same with `$30A6`, `$0E = 1`.
* In `$85:C629`, `$2A = $06`. `$26` = 0, or 2 for P2. `$85:C671 LDA $2A; LDX $26; STA $4C10,X`.
* Evidence: `d.py mk2 85C3D0`, `d.py mk2 85C629`.

### C3 17 sprite sets via `$84:CDCC`/`$84:CDEE` — holds

* `$85:BF66`: `LDA $4C3C,Y; XBA; AND #$00FE` → X. Then `LDA $84CDCC,X` (bank) and `LDA $84CDEE,X` (lo).
* The two tables are $22 bytes apart, so 17 entries.
* The words after `$84:CE10` are not header addresses.
* Every fighter's common animation table equals its set header + $10 (`anims.py` printout). That gives the
  fighter→set map: 0-3→0-3, 4/5/16→4, 6→5, 7→6, 8/9/10/14/15→7, 11→8, 12→9, 13→10.
* Render with my decoder: `out/verify-mk2-compat/mk2_sets.png` (viewed).
  * Sets 0-10: Kung Lao, Liu Kang, Cage, Baraka, female ninja, Shang Tsung, Raiden, male ninja, Jax,
    Kintaro, Kahn.
  * Sets 11-16: effects and UI (FINISH, FATALITY, portraits).

### C4 16-byte header layout — holds

* Header copy at `$85:BF85`-`$BFC3`, offsets +0, +2, +4, +5, +7, +8, +9, +B, +C, +E. DP setup at
  `$85:BFC6`-`$BFF7`.
* Each field and its use:
  * Frame-bank table: [`$5A`], bank `$5C` = h+7. Read at `$85:C0EC` with Y = (f-1)>>6.
  * Tile-group table: [`$4E`] = h+2..4.
  * Frame-pointer table: [`$3E`] = h+5..7. Read at `$85:C0F5` with Y = (f-1)*2.
  * Shadow table: lo h+9, bank h+8 (`$85:C106`-`$C115`).
  * Box table: [`$5E`], lo h+E, bank `$60` = h+8.
  * Position table: [`$52`], lo h+C, bank `$54` = h+B.
* Evidence: `d.py mk2 85BF50 110`.

### C5 frame format — holds (wording clarified)

Frame decoder `$81:8000`:

* Byte 0 is the piece count. Byte 1 is N; the first N pieces are 16x16 (`$0E` = N-1, `BIT $0E`/`BPL` →
  big path `$81:8154`).
* Each piece has one position byte:
  * The high nibble drives X; the low nibble drives Y. They are independent.
  * A nibble of 0 means one explicit absolute byte follows for that axis.
  * Otherwise the coordinate is updated as `x += pos[1+n]` / `y += pos[16+n]`, 8-bit wrapping.
  * The start values are x = pos[0], y = pos[1] (`$85:BFFC`-`$C012`).
  * Coordinates are signed bytes.
* Then 4 tile words for a big piece (VRAM +$20, +$1E0, +$20 → TL, TR, BL, BR; `$81:81A1`-`$81D4`) or
  1 word for a small piece.
* Tile word:
  * Bits 0-1 → OAM bits 14/15 (H/V flip). Only the first word of a big piece is used for this.
  * `AND #$FC` = group*4.
  * High byte = tile index (`$81:834B`).
* Baraka frame $64 reproduces: `$DE:0E5C`, 115 B, 19 pieces (`t_baraka.py`).

### C6 tile codec — holds (exact numbers reproduced)

* `$81:834B`:
  * Group entry: lo word, bank, flag.
  * Flag bit 7 clear → raw, `idx*32` added (no carry into the bank).
  * Flag bit 7 set → `WRMPYA = flag & $3F`, `WRMPYB = idx`, record at base + product.
  * Then 4 mask bytes, each dispatched through `JSR ($A451,X)`.
* Handlers checked:
  * Mask 00 → zero 8 bytes.
  * 01 → byte 7. 02 → byte 6. 03 → bytes 6-7 as a word.
  * 80 → byte 0. 81 → bytes 0 and 7.
  * FF → 8 bytes.
  * So the masks are MSB first.
* `tilecheck.py` walks all frames of all 17 sets (n = (fbank lo − fptr lo)/2). Results:
  * 62,767 compressed refs with 4+popcount == stride, 0 bad.
  * 31,359 raw refs.
  * Flags are exactly `$20` and `$85`-`$9F`; strides 5-31.

### C7 decoder renders donors correctly — holds

* My independent decoder: `donors.py` → `mk2_donors.png` (viewed). It shows Cage, Baraka, Raiden and
  Kintaro, 16 frames each, with `$85:D547` palettes. All are correct.
* Their `donors_decoded.png` and `anims_raiden.png` were also viewed. They are correct.

### C8 animation tables and interpreter — holds (details)

* `$85:C45C` reads `$85:C4E2` (specific). `$85:C47D` reads `$85:C49E` (common). Both are indexed by
  `$4C10,X`*4.
* `$83:F28E`:
  * Word 0 ends the script.
  * A word < $FFF6 is a frame (`$83:EF0C` stores `$4C3C,X`).
  * Otherwise it dispatches through `JMP ($F32C,X)` with X = (~w)*2.
* Dispatch entries FFFF..FFF7 are valid: F2EB, F2F1, F2F7, F308, F31D, F2D3, F2C7, F2B4, F2AE.
  * **FFF6 passes the CMP, but its slot holds `$0002` (garbage).** So FFF6 is not a usable command.
* FFF8: a 1-byte fighter ID plus a target word (`$84:A05C CMP $4C10,X`).
* The 66/24/26 counts come from table adjacency (specific − common), not from a code bound.
  * Entry 64 is `$0000` in every playable fighter's common table.
  * Jade's "specific" pointer equals her common table.
* Baraka anim 0 at `$85:8852` = frames $664, $665, $666, $667, $666, $665, then a jump back (`anims.py`).

### C9 timing — holds (detail)

* `$83:F347`/`$F356`: low byte = anim, high byte = delay.
* `$83:F39C` pushes the delay to (`$36`), then loops: `JSL $83F28E`; `BEQ` end; `BCS` loop without
  waiting; else `JSL $85DDF9` with A = delay.
* `$85:DDF9` is the task-sleep (it stores A-1 to the task's `$04` and switches D through the `$00` link).
* Detail: frames emitted by FFFB return with carry set, so they get **no** sleep.

### C10 box table — holds (LIKELY meaning)

* `$85:C165`: if `$5E == $FFFF`, use `$84:CFC6` with Y = 0. Else Y = ((frame & $1FF) − 1)*4.
* The 4 bytes go to `$44E4`/`$487A`/`$414E`/`$3DB8` via sign/scale helpers `$85:C1AB`/`$C1CD`.
* Baraka f$64 box bytes are (-16, 19, -51, 49), reproduced.

### C11 shadow table — partly

* Confirmed:
  * box − shadow table start == 2*frames for all 11 fighter sets (0-10) (`sizes.py`/inline printout).
  * `$85:C0FF`-`$C119` reads the table only when `$2ED8 != 0` and the pointer is not `$FFFF`, then calls
    `$81:A71A` (an OAM list builder).
* **Wrong detail:** `$83:EE57` does not clear `$2ED8`. It **sets `$2ED8 = 1` unless the stage (`$3270`) is
  6**, and leaves it alone on stage 6.
  * The clears are `STZ $2ED8` at `$80:BB54`, `$81:F01D`, `$82:A11F`, `$83:ABF3` and `$85:A64B`.
  * Stage 6 is Pit II (rendered, see C16).
  * The net effect (no shadows on stage 6) is the same.

### C12 palette tables — partly

* Confirmed:
  * `$85:D33D` has exactly 174 × 24-bit pointers, ending at `$85:D547`. Entry 174 would be table data.
  * 158 of the gaps between sorted palette addresses are 32 B.
  * `$85:C629` picks `$85:D547`, or `$85:D558` when P2 (`$0E != 0`) and P1 has the same fighter and
    `$2EE4 != 4`.
* **Wrong detail:** the loader `$83:F8CC` copies **30 bytes (colours 1-15)**: `LDY #$001E` …
  `DEY; DEY; BNE`, so Y = 0 is never copied. It does not copy 32.
* Also: palette entries 100 and 101 point through bank `$05` (`$05:FFBF`, `$05:FFDF`).

### C13 ninja palettes — holds (LIKELY)

* `pals.py` → `mk2_ninja_pals.png` (viewed):
  * $17 blue, $18 green, $19 yellow, $1A-$1C alternates.
  * $1D cyan monochrome, $1E black, $1F grey.
  * $20-$26 damaged/variant palettes.
* `$85:C784 LDA $85D5B7,X` (X = fighter ID). Every `$D5B7` target renders cyan monochrome on its own
  fighter (`mk2_d5b7.png`, viewed).

### C14 donor byte budgets — holds (reproduced exactly; caveats)

My components:

| Fighter | Tiles | Frames | Tables (incl. header 16, fptr, fbank, group tbl, pos 32, shadow tbl, box tbl) | Shadow data [min ptr, tbl) | Anim block | Palettes |
|---|---:|---:|---:|---:|---:|---|
| Cage | 138,766 | 21,062 | 2,008 | 2,774 | 1,974 | 5 × 32 |
| Baraka | 131,895 | 20,472 | 1,900 | 3,001 | 1,938 | 5 × 32 |
| Raiden | 164,985 | 20,261 | 1,731 | 2,818 | 1,906 | 5 × 32 |
| Kintaro | 123,795 | 13,255 | 738 | 2,019 | 446 | 3 × 32 |

* The totals are 166,744, 159,366, 191,861 and 140,349, which equal the claim. Total 658,320.
* Caveats:
  * The 16-byte header is counted twice (tables and anim block).
  * The shadow-data extent is an assumption, not traced.
  * Effect-set frames that the scripts use are excluded.
  * My script walker ends Raiden's scripts at `$85:96A8`, 18 B before the next header.
* Scripts: `sizes.py`, `donor_budget.py`.

### C15 no shared groups; 2,003,360 B — holds

* Frames plus tile groups alone cover 1,983,879 B.
* Adding the fptr+fbank, group-table, pos and box tables gives **2,003,360** exactly. Shadow tables are
  excluded.
* Overlaps 0; shared groups none.
* Script: `sizes.py` (tail).

### C16 stage IDs/names — holds

* `$82:D7B3 LDA $7E3270; ASL; LDA $82DD76,X`. The 9 names end at `$82:DD88`.
* `$83:AEBD` increments `$3270` and wraps to 0 at 9.
* All 10 records render (`stages_all_A.png`, viewed):
  * 0 Dead Pool (hooks), 1 Kombat Tomb (spiked ceiling), 2 Wasteland, 3 Tower, 4 Living Forest,
    5 Armory, 6 Pit II (bridge, moon), 7 Portal, 8 Kahn's Arena (throne).
  * 9: stone arches with a chained figure. "Goro's Lair" stays LIKELY.

### C17 stage records — holds

* `$82:F04F`: record = `$82:EDFC` + `EF50[stage]`, 34 B, 10 records (EF50 = 0, $22, …, $132).
* Fields:
  * +0..+3: banks for tiles / metatiles / maps / palette.
  * +4: tiles LZ (to `$7F:0000`, then `$85:D776`).
  * +6: metatiles LZ.
  * +8: 192-B palette, copied to `$B91C`.
  * +A..+21: 12 map blocks. Each is 512 B = 16×16 metatile words, expanded by `$82:F1AB` (metatile =
    w & $3FF, 8 B each).
  * Blocks 0-9 form a 5×2 layer (pitch $140); blocks 10-11 form a 2×1 layer (pitch $80).
* Packed sizes reproduce: 13,479-32,416 including the 192-B palette, 239,052 total (237,132 streams +
  1,920 palettes). Script: `stages.py`.

### C18 LZ `$85:B9FC` — holds (details added)

* `lz.py` reproduces the decoder:
  * 84 distinct stage streams; every end command reached with write pointer exactly 0.
  * 75 of them are type 2 and 9 are type 1; type 0 is unused.
* Format (header: length word, type byte), output written backwards:
  * `1xxxxnnn oooooooo`: copy n+3 bytes from distance off+1. Types 0/1 use 16-bit descending pair copies
    (`$85:BCA8`/`$BD17` chains), which matters for overlapping copies.
  * `01nnnnnn`: n+1 literals.
  * `001kkkkk`: one byte from distance k+1.
  * `000nnnnn b`: fill n+2 (n = 0 ends).
* Type 2 writes the odd positions, then the even positions, and backrefs wrap between the two planes.
  **Its `001` command is a decrementing-byte run of (k+3) bytes, not a 1-byte backref.**

### C19 special-move dispatch — partly

* Confirmed:
  * `$81:A943`: `[$0A]` = table in bank `$81`, Y = `$4C10,X`*2, `JML [$1900]`.
  * Tables have 12 entries. `$81:AACD` = RTL.
  * The listed entries match: Baraka AA88[3] = B054; Cage A989[2] = B0C3, AA88[2] = B0E0, AAA0[2] = B38D;
    Raiden A989[7] = AA0F, A9B9[7] = AA2D, AA88[7] = AB0A.
* **Incomplete:** there are 8 tables, not 5.
  * `$81:AA40` (from `$81:A913`), `$81:AA58` (`$81:A922`) and `$81:AA70` (`$81:A931`) are missing.
  * Baraka's real input checks are `$81:B094` (AA40) and `$81:B065` (AA58); those use `$81:C8CB` →
    `$81:C83F`.
  * B054 instead goes to `$81:C78F`. That routine tests `$327E == 3` and stage 6 or 1, so it is LIKELY a
    stage-fatality check.
  * Cage also has AA40 = B0F1, AA58 = B2AA, AA70 = B115. Raiden has AA40 = B311, AA58 = B2FF.
* "Kintaro has none" is consistent: ID 12 is outside the 12-entry tables.

### C20 LZ in MK3/UMK3, MK2 mask handlers only in MK2 — holds (LIKELY)

* Wildcard probes (`wild.py`): the LZ head is at MK3 `$86:E41A` and UMK3 `$88:AD30`.
* MK2 mask handlers 00/01/FF (`$81:8451`/`$8460`/`$A432`) are found only in MK2.
* MK3/UMK3 have a different mask expander (`$83:85AA` table in UMK3: the fill byte is read through the
  M7 multiply result `$2135`, and output goes to `WMDATA`).

### C21 capstone mode bug — holds

`Cs(CS_ARCH_MOS65XX, CS_MODE_MOS65XX_65816)` raises `CS_ERR_MODE` (capstone 5.0.7). `snes.disasm` uses that
mode when M and X are both 8-bit.

## 2. compat claims

### T1-1 — holds

`blockmatch.py mk3 umk3 32`: **1,047,940** unmatched MK3 bytes (exact).

### T1-2 Sheeva — holds (numbers within definition noise)

* MK3 set table: `$85:ABAA` (bank) / `$85:ABDE` (lo), from `$86:E9B9`/`$86:E9BF`; 26 sets.
* Set 11:
  * Header `$86:9B3F`, 204 frames, 25,345 frame bytes.
  * 7,413 distinct tiles, of which **28** also occur among all decoded UMK3 tiles.
  * Tile bytes 183,239 vs the claim's 183,227, and 12 footprint bytes covered vs the claim's 6. Both gaps
    come from whether the T and fill bytes are counted.
  * The render shows a four-armed woman (`mk3_set11.png`).
* VS entry 11 (`$80:F414` bank C9, `$80:F432` tiles `$0000`):
  * `$C9:0000` is a clean LZ stream of exactly 10,817 B, with 0 bytes covered in UMK3.
  * It renders as Sheeva's portrait (`vs11.py` → `mk3_vs11.png`).

### T1-3 MK3-only sets — partly

* **Set 21:**
  * 99,203 of 99,220 footprint bytes are unmatched (claim: 99,712/99,714; definitions differ).
  * **Set 21 is not only animality sprites.** Frames 139-157 are the kode-message banners and 158-166 are
    actor credits (`mk3_set21_uniq.png`).
  * UMK3 keeps the kode banners in its own set 21 ($17-$29), with different tile data.
* **Set 19:**
  * 36,182 B unmatched.
  * At least 90% of the non-blank tiles are absent from UMK3 in these frames:
    * 1-11 ANIMALITY.
    * 45-56: **all** stage names, including ROOFTOP and THE PIT 3, which UMK3 keeps. UMK3 set 19 has no
      stage-name banners at all (`umk3_set19_all.png`).
    * The MK3 FIGHT!/spiral/FATALITY variants: 58-62, 67, 78, 84-89, 105-108. UMK3 has its own
      redrawn versions.
  * So "dropped stages' name banners" is too narrow.
* **MERCY:** set 18 frames 206-212 are 93-98% absent (`mk3_set18_200_215.png`, viewed). Frame 213, the
  static MERCY, is 0% absent, so its tiles exist in UMK3.
* **Set 22 claim is overstated.**
  * 21 frames use at least one tile absent from UMK3; that is their `uniqframes.py` criterion "u ≥ 1".
  * But each of those frames is only 2-30% absent. No frame is at least 90% absent.
  * They are variants of UMK3 frames, not absent frames.
* Scripts: `mk3sets.py`, `mk3frames.py`.

### T1-4 stage tile overlap — partly

* `stgdesc.py` (records `$82:B888` ×26 and `$84:8A22` ×29, layer descriptors at +8..+F) and
  `stagetiles.py`.
* The type-0 tiles offset (+1A bank / +1B lo) was traced at `$84:913E`→`$84:9425`. The other offsets were
  validated only by clean decompression.
* **Reproduced:**
  * MK3 records 0, 1, 4, 5, 6, 7, 8, 12, 13 and 15 have 0-1.4% overlap per layer.
  * Rec 2: L0 = `$C5:0000` is 100% (the shared skyline); the other layers are 0.4%.
  * Rec 3: UMK3 rec 0 ⊂ MK3 rec 3. 100% of UMK3's tiles are in MK3, but MK3 has 96% in UMK3.
  * Rec 9: likewise, with UMK3 rec 6.
* **Detail:**
  * MK3 records 3 and 9 carry an extra layer `$F6:0000` (40 tiles). It is shared by almost all MK3 fight
    records and is absent from UMK3, so "100%" holds only from the UMK3 side.
  * The record→stage-name mapping was not independently checked.

### T1-5 UMK3 rec 7/8 — holds

* Rec 7: L0 and L1 tiles are `$C0:0000`, the same 14,144-B stream as rec 6 L1. Maps `$F0:A95D` (also
  +22 `$F0:9D74`) and `$F0:AB2B` do not decompress.
* Rec 8: all tile and map pointers are `$00:0001`. Its palettes are `$00:0001`/`$00:FFFF` null markers.
* Script: `stagerecs.py`.

### T1-6 BRR-like data — holds (LIKELY)

* My own heuristic (`brr.py`: some 9-byte phase with ≤ 10% END bits and ≥ 95% range ≤ 12, in 1 KB
  windows) gives:
  * 299,008 BRR-like bytes.
  * 65,892 of them unmatched in UMK3, 61,991 of those in `$CF:B800`-`$D4:4FFF`.
* That is the same region and order of magnitude as the claim (55,264). Only a heuristic.

### T1-7 code-skeleton percentages — unverifiable

The figures depend on their trace and skeleton definition, which I did not reproduce.

### T2-1 LZ identical — holds (details)

* `rcmp.py mk2 85B9FC umk3 88AD30 200`: 129 identical / 71 same opcode / 0 different.
* Over the whole 1,008-B code range (`lzcmp.py`), every differing byte is one of:
  * a DP operand +$10;
  * the scratch pointer `$1900` → `$1A00`;
  * a relocated address.
* All 4 jump tables (`$85:BDEC`/`$BE0C`/`$BE2A`/`$BE68` → `$88:B120`/`$B140`/`$B15E`/`$B19C`) are equal
  after relocation.

### T2-2 same sprite format — holds

* UMK3 `$88:A471` copies the header at the same offsets from `$86:EAEC`/`$86:EB24` (28 sets, set 11
  null).
* `$88:A645` looks up the frame pointer the same way as MK2.
* `$83:8000` uses the same nibble/explicit-byte position scheme, 4 tile words per big piece, and the same
  tile-word layout.
* Every UMK3 set renders coherently with my MK2 parser plus the UMK3 tile codec (`umk3_sets.png`, viewed).
* Raw groups are the same. UMK3 adds flag bit 6 = 16-byte tiles (`$83:8375`) and a 2-mask compressed
  variant (`$83:850F`).

### T2-3 lossless converter — holds

* `convert_test.py`: 45,347 distinct compressed tiles across all 17 MK2 sets, **0 mismatches**.
* Method:
  * Convert each group to [T = max+1] + records. If index 255 is used, T = 255 and a $00 fill byte goes
    before record 255.
  * Decode with a decoder written from UMK3 `$83:8474`: T at base; record at base + 1 + idx*s; if
    idx ≥ T, a fill byte comes first.
* 29 groups use index 255.
* The claim's per-fighter numbers (7,909 / 7,620 / 7,689 / 5,249) are total tile-word references (raw +
  compressed). They match my C6 counts.

### T2-4 box tables — holds

* UMK3 `$88:A6A6` uses the same indexing and the default `$86:EC3C`.
* It adds `$0A` = `$2DE4,X`, negated when `$5480,X` bit 14 is set, to both X bytes (`$88:A707`).
* My instruction counts (10 / 12 / 23) differ from the claim's (17 / 18 / 20). The counts depend on the
  tool; the conclusion does not.

### T2-5 WRAM layout — holds

* The header-copy targets are MK2 `$2C96`…`$2D46` (stride $16) and UMK3 `$3474`…`$3534` (stride $18).
* The object-list loops start at `LDX #$16` (MK2 `$85:C017`) and `LDX #$18` (UMK3 `$88:A523`).
* The `$3662` block was not checked.

### T2-6 command encoding — holds

* UMK3 `$88:87DD`: `CMP #$FFEA`, `JMP ($89E2,X)`. The 22 entries cover FFFF..FFEA; FFE9 is garbage.
* FFFF..FFF7 have the same argument layouts as MK2: jump; none; X; X,Y; frame + SEC; ptr24 → `JML`; sound
  word; fid byte + target; none.
* FFFD/FFFC are flip-aware position offsets in both games, so no remap is needed for them.

### T2-7 numbering — holds (LIKELY)

* UMK3 common = `$88:95C3` = header + $10; specific = `$88:9633` = common + $98 (76 words).
* The side-by-side first frames (`animcmp.py` → `animcmp_lk.png`, MK2 Liu Kang vs UMK3 fighter 13 Liu
  Kang) agree only for roughly the first 5-6 indices.

### T2-8 frame maxima — holds (LIKELY)

* `framestats.py` reproduces Cage 69/29, Baraka 86/29, Raiden 92/32, Kintaro 106/39, and UMK3 maxima of
  133 tiles (set 22) and 62 pieces (set 15).
* Stronger comparison: among UMK3 **fighter** sets the maximum is 108 tiles (set 10), and Motaro (set 15)
  has 106/62. Kintaro still fits.

### T3-1 MK2 in UMK3 — holds

* `blockmatch.py mk2 umk3 32` covers **37,205** B (= 28,264 + 129 + 8,812).
* Big runs:
  * MK2 `$C4:C7A9`-`$C98B` → UMK3 `$C6:E369`.
  * MK2 `$C4:C9CC`-`$CDCB` → `$C6:E6EC`. These are the frame-decoder tables just before each sprite-set
    table.
  * Sound runs in `$CE`/`$CF`; 24,233 B are inside `$CE:8E00`-`$CF:5000`.
* `mk2assets_in_umk3.py`: the only covered bytes inside MK2 sprite, stage or palette data are constant
  fills of 1-3 distinct byte values. So no real asset is present.
* The list of zero-match banks is incomplete: `$DD`-`$E0`, `$E3`, `$E4` and `$EB` are also 0.

### T4-1 trace-scoped ExHiROM code audit — unverifiable

* I did not reproduce a 31,656-instruction trace.
* Spot checks agree with the claim:
  * `$83:BC97`/`$87:FE09` sit in ASCII text ("…MORTAL KOMBAT", "DEVELOPMENT TEAM").
* My byte scans of all of UMK3 (`exhi_scan.py`) found:
  * PEA+PLB with a low-bank byte only in data banks `$D0`/`$D3`/`$F8`/`$FB`/`$FD`.
  * DMA source-bank immediates only `$7E`/`$83`/`$88`.
* A raw long-operand scan (`exhi_long.py`) is too noisy without a trace.

### T4-2 9 low-bank tile groups — holds (exact)

* `umk3_lowbank.py` checks 917 frame-referenced directory entries. Exactly 9 have bank < $40.
* Their bank-byte file offsets are exactly 0x3FB3F5, 0x3FB42D, 0x3FB832, 0x3FC68F, 0x3FC52F, 0x3FCAD3,
  0x3FD4ED, 0x3FC727 and 0x3FC841.

### T4-3 DB-relative fetch — holds (nuance)

* Raw path: `$83:83F5 PHA` … `$83:8401 PLB`, `$83:8402 LDA $0000,Y`.
* 16-byte path: `$83:8382`/`$838F`/`$8390`.
* Compressed path: `$83:8491 PHA`, `$83:84C5 PLB`, `$83:84C6 LDA $0003,Y`.
* Nuance: "never `$00`-`$3F`" is a safe rule, not a hard limit. Data at `$8000`+ in those banks works (that
  is how the 9 groups work today); in ExHiROM it would map to file 4 MB+.

### T4-4 recipe — unverifiable (no contradiction found)

* Reset `$00:83D7` does `JSL $88C7E4` then `JML $8083F2`.
* IRQ `$00:8738` does `JML $808743`.
* NMI `$00:8765` and COP/BRK/ABORT `$00:83D6` are RTI.
* So copying file 0x8000-0xFFFF to 0x408000 covers bank-0 execution.
* Header bytes today are map mode $31 and size $0C. Pointer tables not audited by anyone (sound/APU
  upload, DMA banks from variables) remain a risk.

### C-U1 — holds

`$88:9576 LDA $889633,X`; `$88:95A0 LDA $8895C3,X`. umk3-map lines 154-155 have them reversed.

### C-U2 — holds

* `$80:C733 LDA $80C794,X; BMI`.
* Values `$2A17`-`$2A29` decode to set 21 frames $17-$29. These render as the kode messages ("PSYCHO
  KOMBAT", "UNLIMITED RUN", …) in `umk3_C794_set21.png` (viewed).

### C-U3 — holds

* `$83:F29D`[11] = `$FC9E`. It is used by `$83:F2E7 LDA $83F29D,X; BEQ; JMP ($F29D,X)` with X =
  `$52C8`*2.
* `$83:FC9E` is real code.

### C-U5 — holds

Every bank `$C0`-`$C7` has a tile group directly after its `$FF` run. For example, the `$C0:FF1F`-`$FF85`
run is followed by the set 17 group at `$FF86`-`$FFAE` (`umk3_lowbank.py`).

### C-M1 — holds

`$83:F8CC`-`$F8F8` copies Y = $1E down to 2, so 15 words.

### C-M2 — holds

Supported by T2-3 (0 mismatches) and T2-6 (same command encoding).
