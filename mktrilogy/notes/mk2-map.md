# Mortal Kombat II (SNES, USA) – donor-game map

ROM: `/home/claude/work/roms/mk2.sfc`, 3 MB, HiROM/FastROM, header "MORTAL KOMBAT II", reset $80:8000,
NMI $80:86D9, IRQ $80:86B1. Pure static analysis; every claim below is tagged
**CONFIRMED** (code that uses the data was traced and the data was checked/decoded) or
**LIKELY** (heuristic, pattern match, or a single-sided trace). Addresses are SNES addresses
(`$85:C49E`); file offsets are given as `0x05C49E` where useful (HiROM: offset = addr & $3FFFFF).

All scripts live in `/home/claude/work/scripts/mk2/` and are run with `python3 -I <script>`.
All PNG evidence lives in `/home/claude/work/out/mk2/`.

## 0. Tooling notes (read first)

* `snes.disasm`/`snes.show` in the shared lib **crash when both M and X are 8-bit**
  (capstone 5 rejects `CS_MODE_MOS65XX_65816` without a LONG flag: `CsError: Invalid mode`).
  I wrote a pure-python table-driven 65816 disassembler, `scripts/mk2/d65.py`
  (`python3 -I d65.py <addr> <count> [rom]`). Note also `python3 -I` does not put the script
  directory on `sys.path`; scripts insert it explicitly.
* Main modules:
  * `mk2gfx.py` – character headers, frame decoder, tile decoder, renderer, palettes (sections 3-5, 7).
  * `mk2lz.py` – port of the general LZ decompressor $85:B9FC (section 10).
  * `stages.py`, `stage_report.py` – stage records, decompression, rendering, sizes (section 9).
  * `anims.py`, `anim_catalog.py` – animation tables/scripts (section 5).
  * `sizes.py`, `coverage.py`, `validate_tiles.py`, `donor_sizes.py` – sizes and validation (section 6).
  * `palettes.py`, `pal_frames.py` – palettes (section 7); `overview.py` – per-set contact sheets.
  * `specials.py` – special-move input dispatch (section 8).
  * `xref.py`, `fid_users.py`, `fid_tables.py`, `stage_users.py`, `jumptables.py` – cross-reference helpers.
  * `crosscheck_umk3.py` – quick code-pattern comparison with MK3/UMK3 (section 12).

## 1. Executive summary

* **Fighter IDs (0-16)**: 0 Kung Lao, 1 Liu Kang, 2 Johnny Cage, 3 Baraka, 4 Kitana, 5 Mileena,
  6 Shang Tsung, 7 Raiden, 8 Sub-Zero, 9 Reptile, 10 Scorpion, 11 Jax, 12 Kintaro, 13 Shao Kahn,
  14 Smoke, 15 Noob Saibot, 16 Jade. **CONFIRMED** (section 2).
* Graphics are organised in **17 sprite sets**, not per fighter: 11 fighter sets (palette-swap
  fighters share one) + 6 shared effect/UI sets. Fighter → set: `[0,1,2,3,4,4,5,6,7,7,7,8,9,10,7,7,4]`.
  **CONFIRMED**.
* **Sprite format fully decoded** (frames + bucketed zero-mask tile compression). Python decoder
  `mk2gfx.py` renders every frame of every set; Baraka, Johnny Cage, Raiden and Kintaro render
  correctly with their own palettes (`out/mk2/donors_decoded.png`). 62,767 compressed-tile
  references were checked and all satisfy the format invariant. **CONFIRMED**.
* **Stage format decoded** (LZ decompressor ported, all 10 stages render: `out/mk2/stages_all.png`).
  **CONFIRMED**.
* **Donor byte budgets** (graphics + frames + tables + anim scripts + palettes, excluding move code):
  Baraka ≈ 159 KB, Johnny Cage ≈ 167 KB, Raiden ≈ 192 KB, Kintaro ≈ 140 KB, i.e. ≈ 658 KB for the
  four, plus projectile/effect frames and move code (estimated tens of KB; sound not measured)
  (section 6). Every MK2 stage is 13-32 KB compressed (section 9).
* The MK2 **general LZ decompressor is also present in MK3 and UMK3** (same code shape), but the MK2
  **sprite tile codec was not found** in MK3/UMK3 (section 12) – fighter graphics will need
  converting, stages may not.

## 2. Fighter roster and fighter-ID variables

| ID | Fighter | sprite set | ID | Fighter | sprite set |
|---|---|---|---|---|---|
| 0 | Kung Lao | 0 | 9 | Reptile | 7 |
| 1 | Liu Kang | 1 | 10 | Scorpion | 7 |
| 2 | Johnny Cage | 2 | 11 | Jax | 8 |
| 3 | Baraka | 3 | 12 | Kintaro | 9 |
| 4 | Kitana | 4 | 13 | Shao Kahn | 10 |
| 5 | Mileena | 4 | 14 | Smoke | 7 |
| 6 | Shang Tsung | 5 | 15 | Noob Saibot | 7 |
| 7 | Raiden | 6 | 16 | Jade | 4 |
| 8 | Sub-Zero | 7 | | | |

* **CONFIRMED** – ID order: 17-entry pointer table $83:D7B8 → "KUNG LAO WINS", "LIU KANG WINS",
  "CAGE WINS", "BARAKA WINS", "KITANA WINS", "MILEENA WINS", "SHANG TSUNG WINS", "RAYDEN WINS",
  "ZERO WINS" (Sub-), "REPTILE WINS", "SCORPION WINS", "JAX WINS", "KINTARO WINS",
  "SHAO KAHN WINS", "SMOKE WINS", "NOOB SAIBOT WINS", "JADE WINS" (strings at 0x03D7DA..).
  Read by $83:D126 (`lda $83D7B8,x` with x = 2*A); caller $83:A877 gets A from $83:AEF1, which
  returns `$7E:2EF8` or `$7E:30A6`. Every per-fighter table below follows this order and its
  contents match it (e.g. the sprite renders).
* **CONFIRMED** – `$7E:2EF8` = P1 fighter ID, `$7E:30A6` = P2 fighter ID: $85:C3DA / $85:C409 build
  the P1/P2 fighter objects from them and call $85:C629, which stores the ID into the per-object
  array `$7E:4C10,x` (`$85:C671-C675`). Almost all per-fighter lookups use `$4C10,x`, usually
  through `$84:90CA` (`ldx $26; lda $4C10,x; asl; tax; rtl`).
* Other P1/P2 player-struct fields are $1AE apart (e.g. `$2F08`/`$30B6`, `$2EFC`/`$30AA`). LIKELY.

## 3. Per-fighter tables (all indexed by fighter ID)

| Table | Entry | Meaning | Used by | Tag |
|---|---|---|---|---|
| $83:D7B8 | 2 B ptr (bank 83) | "X WINS" string | $83:D126 | CONFIRMED |
| $85:C49E | 4 B (lo, bank) | common animation table = sprite-set header + $10 | $85:C47D (A=anim) | CONFIRMED |
| $85:C4E2 | 4 B (lo, bank) | fighter-specific animation table | $85:C45C (A=anim) | CONFIRMED |
| $85:D547 | 1 B | main palette ID | $85:C629 | CONFIRMED |
| $85:D558 | 1 B | alternate palette ID (P2 when P1 picked the same fighter, `$2EE4`≠4) | $85:C629/$85:C64E | CONFIRMED |
| $85:D569 | 1 B | 2nd palette (projectile/effect) | $84:FD2B → $83:F8CE | CONFIRMED use; meaning LIKELY |
| $85:D57A | 1 B | 2nd palette variant (00 = none for Baraka/Mileena) | $84:FD3D | CONFIRMED use; meaning LIKELY |
| $85:D58B | 1 B ×12 | Shang Tsung morph palette for target fighter | $84:ED51 (inside Shang's code, next to his table $84:D976) | LIKELY |
| $85:D5B7 | 1 B | frozen palette (all cyan monochrome) | $85:C784 → $85:C6A8 | LIKELY (visual: `out/mk2/pal_*`) |
| $81:A989, $81:A9A1, $81:A9B9, $81:AA88, $81:AAA0 | 2 B ×12 (bank 81) | special-move input-check routine per button event ($AACD = none) | $81:A943 (`jml [$1900]`) | CONFIRMED dispatch; section 8 |
| $81:CD42 | 2 B (bank 81) | list of bank-81 handlers indexed by attack/reaction id ($32 high byte) | $84:9CC5 | CONFIRMED use; meaning LIKELY (hit reactions) |
| $83:DCC1 | 2 B (bank 83) | move routines indexed by a move number (stubs $81:B51C-B55D pass n=0..$D) | $83:DCB4 | CONFIRMED |
| $80:CA39, $80:CA99, $80:D3C8, $80:DCA5, $80:DF53, $80:E093, $85:AC98 | 2 B jump tables | per-fighter variants of shared actions (`jsl $8490CA; jmp (tbl,x)`) | listed addresses | CONFIRMED dispatch, purpose unknown |
| $80:F2CE | 2 B (bank 80) | per-fighter AI/behaviour data block (ninjas share $F4A0) | $80:F2B5 | LIKELY |
| $82:D059, $82:E104 | 2 B | select-screen / portrait object + palette IDs ($88-$93 for the 12) | $82:D1C2, $82:E0B4 | LIKELY |
| $85:C543, $85:C5A1, $85:C5E5, $85:C723 | 1-4 B | per-fighter size/offset constants (C723 = height-like, subtracted from floor `$2EDC`) | $85:C534.. | LIKELY |
| $81:BBFC, $81:C02E, $81:C124, $81:C22E, $81:C23F, $81:C583, $82:8829, $82:99E4, $83:D76A, $80:952A, $80:CF55, $80:D683 | 1-8 B | misc per-fighter constants | `scripts/mk2/fid_tables.py` lists each user | CONFIRMED indexed by fighter ID, meaning not traced |

Evidence for the whole table: `python3 -I fid_tables.py` (prints table + using instruction) and
`fid_users.py`.

## 4. Sprite sets and the 16-byte character header

Sprite-set ID = bits 9-15 of an animation frame word (`$7E:4C3C,x`); frame = bits 0-8 (1-based).
**CONFIRMED**: $85:BF66 does `lda $4C3C,y; xba; and #$00FE` → index into
**$84:CDCC (bank words) / $84:CDEE (low words)**, 17 entries; $85:C0DD uses `($4C3C & $1FF) - 1`.

| set | contents | header | frames |
|---|---|---|---|
| 0 | Kung Lao | $85:96BA | 211 |
| 1 | Liu Kang | $84:F109 | 222 |
| 2 | Johnny Cage | $85:8000 | 226 |
| 3 | Baraka | $85:87B6 | 214 |
| 4 | Kitana / Mileena / Jade | $84:B4EE | 262 |
| 5 | Shang Tsung | $84:D8E2 | 247 |
| 6 | Raiden | $85:8F48 | 189 |
| 7 | male ninjas (Sub-Zero, Reptile, Scorpion, Smoke, Noob) | $84:A067 | 271 |
| 8 | Jax | $84:E158 | 229 |
| 9 | Kintaro | $82:FE13 | 67 |
| 10 | Shao Kahn | $85:D9E7 | 98 |
| 11-14 | shared effects (projectiles, blood, fans, lightning...) | $80:8957, $84:CF84, $84:CF94, $84:CFA4 | 150/125/162/226 |
| 15 | black silhouettes (battle plan?) | $84:CF74 | 10 |
| 16 | select screen / UI pieces | $84:CFB4 | 30 |

Identification is **CONFIRMED** by rendering every ~n/20-th frame of each set with the main
palette of its first fighter (`python3 -I overview.py` → `out/mk2/overview_setNN.png`,
`overview_part0..2.png`; greyscale check `id_sets5to10_gray.png`) and by $85:C49E pointing each fighter at `<its set header>+$10`.
Frame counts are **CONFIRMED** self-consistent: the frame-pointer table is directly followed by the
frame-bank table and the bank table length equals ceil(n/64) for all 17 sets (`sizes.py`).

Header layout (read by $85:BF85-$85:BFC3 into per-object arrays, then into DP by $85:BFC6):

| off | size | meaning | DP/array |
|---|---|---|---|
| +0 | 2 | frame-bank table low word (bank = byte +7) – 1 byte per 64 frames | $5A ($2032) |
| +2 | 3 | tile-group table (4-byte entries) | $4E/$50 ($2C96/$2CAC) |
| +5 | 3 | frame-pointer table: 16-bit low word per frame (bank from frame-bank table) | $3E/$40 ($2CC2/$2CD8) |
| +8 | 1 | bank of the shadow table and box table | $60 ($2CEE) |
| +9 | 2 | shadow table low word ($FFFF = none), 2 B per frame | $2D04 |
| +B | 1 | bank of position table | $54 ($2D30) |
| +C | 2 | position table low word (32 bytes) | $52 ($2D1A) |
| +E | 2 | body-box table low word ($FFFF = default $84:CFC6), 4 B per frame | $5E ($2D46) |

All **CONFIRMED** by the code above; meanings of +9 and +E are explained in section 4.3.
Headers +$10.. hold the common animation table (section 5). Smaller per-fighter blocks are packed
back to back: bank 85 = Cage $8000, Baraka $87B6, Raiden $8F48, Kung Lao $96BA; bank 84 = ninjas
$A067, Kitana set $B4EE, Shang $D8E2, Jax $E158, Liu Kang $F109.

### 4.1 Frame format (builder $81:8000, entry $85:C0AA → `jsl $81:8000`)

Frame address = `bank_tbl[(f-1)>>6] : ptr_tbl[f-1]`. Frame bytes:

* byte 0 = piece count; byte 1 = number of leading 16×16 pieces (rest are 8×8). (If byte 1 = 0,
  `$0E` becomes $FFFF and only the 8×8 path is used.)
* per piece: one position byte `XY`: high nibble X, low nibble Y. Nibble 0 → an explicit byte
  follows (X first, then Y); nibble n≠0 → coordinate += pos_tbl delta. Positions are cumulative
  8-bit values, starting from pos_tbl[0] (X) and pos_tbl[1] (Y) for every frame
  ($85:BFFC-C012). pos_tbl[1+n] = X delta for n, pos_tbl[16+n] = Y delta for n.
  Final coordinate = sign-extended byte relative to the object (`sbc #$80; eor #$FF80`).
* then 4 tile words (16×16: TL, TR, BL, BR, written to VRAM-buffer offsets +0, +$20, +$200,
  +$220) or 1 tile word (8×8).
* tile word: bits 0-1 = H/V flip for the piece (first word only, $81:811D-8123, XORed with the
  object flip from `$2048`/`$205E`); bits 2-7 = tile-group number ×4; bits 8-15 = tile index in group.
* flipped X: `-x-1-6` (8×8) or `-x-1-14` (16×16).

**CONFIRMED** (code $81:8000-$81:81F7 traced; decoder renders every frame of every set;
example: Baraka frame $64 at $DE:0E5C, 115 bytes, 19 pieces of which 8 are 16×16 –
`python3 -I baraka_example.py`).

### 4.2 Tile format (fetch $81:834B, mask expansion jump table $81:A451)

Tile-group entry (4 bytes) = 24-bit address + flag byte:

* flag $20 (bit 7 clear): raw 4bpp tiles, tile = base + idx×32. (98 groups)
* flag $80|s (s = 5..31): compressed, **fixed-stride records of s bytes**: tile record =
  base + idx×s (multiplied with the hardware multiplier $4202/$4203). Record = 4 mask bytes then
  the non-zero bytes. Mask byte q covers output bytes 8q..8q+7, bit 7 = first byte; a set bit takes
  the next literal, a clear bit writes 0. Tiles are therefore **bucketed by their number of non-zero
  bytes** (stride = 4 + popcount); tiles with 28+ non-zero bytes are stored raw.

**CONFIRMED**: handler code traced for mask values $00, $01, $02, $03, $40, $80, $81, $C0, $FF
(`$81:8451`, `$81:8460`, ... `$81:A432`); `validate_tiles.py` walked all 94,126 tile references of
all 17 sets: 62,767 compressed references all have 4 + popcount(masks) == stride exactly, 31,359
raw. Flag bytes seen: only $20 and $85-$9F. The 256 handlers + table occupy $81:8451-$81:A650
(~8.7 KB of unrolled code).

Python decoder: `mk2gfx.tile_bytes()`, `mk2gfx.decode_frame()`, `mk2gfx.render()`,
`mk2gfx.sheet()`. Evidence PNGs: `donors_decoded.png` (Baraka f$64, Cage f$61, Raiden f$61,
Kintaro f$27 with their main palettes), `test_c3_f24.png`, `anims_baraka.png`,
`anims_johnny_cage.png`, `anims_raiden.png`, `anims_kintaro.png`.

### 4.3 Per-frame tables

* **Body box**, 4 B/frame at header+$E (bank +8): read by $85:C165 (called on every frame build
  from $85:BFF9) into `$44E4`, `$487A`, `$414E`, `$3DB8` (signed, flip-aware via $85:C1AB/$C1CD).
  Baraka frame $64 = (-16, 19, -51, 49). CONFIRMED read path; "collision/body box" meaning LIKELY.
  Kintaro/Kahn/effects without a table use the default at $84:CFC6.
* **Shadow table**, 2 B/frame at header+9 (bank +8), $FFFF = none, followed immediately by the box
  table (gap = 2×frames for all 11 fighter sets). Drawn by $81:A71A only when `$2ED8` ≠ 0;
  `$83:EE57` sets `$2ED8 = 1` unless stage ID = 6 (The Pit II). $81:A71A emits a strip of 8-px
  sprites → LIKELY floor shadows. Data lives just before the table (e.g. Baraka $C0:6F17-$C0:7ACF).
* Attack/hit boxes were **not** found as frame data; hit checks appear to be done in move code
  (reaction handlers $81:CD42, $84:9C90). Open question.

## 5. Animation tables, scripts and timing (Baraka as the worked example)

* $85:C47D (A = anim#) → common table from $85:C49E[fighter]; $85:C45C → specific table from
  $85:C4E2[fighter]. Both return the script address in `$2A/$2C`. **CONFIRMED**.
* Common tables have **66 entries** for the 12 playable fighters (table length = specific − common
  = $84 for all), 24 for Kintaro ($82:FE23), 26 for Shao Kahn ($85:D9F7). Specific tables:
  Kung Lao 6, Liu Kang 5, Cage 7, Baraka 4, Shang 14, Raiden 6, Jax 7. Shared sets overlap:
  Reptile's specific table = Sub-Zero's +5 entries, Scorpion/Smoke/Noob = Sub-Zero's +13;
  Mileena = Kitana's +9; Jade's "specific" pointer equals the common table. **CONFIRMED**
  (`python3 -I anims.py`).
* Script interpreter **$83:F28E** (word stream, same bank as the table). **CONFIRMED**:
  `0000` end; `0001..FFF5` frame word → `$4C3C,x` via $83:EF0C (one frame per call);
  `FFFF a` jump; `FFFE` jsl $83:F1E4; `FFFD a` / `FFFC a b` jsl $83:F4D8 with X/Y (LIKELY
  position offsets); `FFFB f` frame without waiting; `FFFA lo bank` call $85:DF88;
  `FFF9 a` jsl $85:E0C5 (LIKELY sound); `FFF8 b a` conditional jump via $84:A05C; `FFF7` jsl
  $83:F1F5. Dispatch table $83:F32C.
* **Timing is in the code, not the data**: `A = delay<<8 | anim` → $83:F347 (common) / $83:F356
  (specific) → $83:F39C pushes the delay and sleeps `delay` ticks ($85:DDF9) after each frame word.
  $83:F365/$83:F36F start at an offset; $83:F3E2 plays backwards. **CONFIRMED**.
* Baraka: header $85:87B6, common table $85:87C6, specific table $85:884A (4 entries), scripts to
  $85:8F47. Anim 0 (stance) at $85:8852 = frames $664,$665,$666,$667,$666,$665 then jump to
  $8852. 67 scripts reachable from the tables reference 134 distinct frames (sets 3 and 12).
  Catalog: `out/mk2/anims_baraka.png` (c0 stance, c1-c4 walk, c5 duck, c7/c8 jump, c38 blade,
  s0-s3 blade specials) – labels LIKELY, script decoding CONFIRMED.
* Some scripts are reached only from code (not from the tables), so per-set script coverage from
  the tables is ~1.0-1.5 KB while the blocks are ~1.9-2.6 KB.

## 6. Donor size budgets

`python3 -I donor_sizes.py` (tile bytes = sum over referenced groups of (max index+1)×stride;
frame bytes = union of decoded frame byte ranges; ftbls = header + frame-ptr + bank + group table
+ position + box + shadow tables; shadow = pointed shadow data; anim = header-to-next-header
block; pals = 32 B × palette IDs referenced from the fighter's tables).

| set | frames | tiles | frame data | tables | shadow | anim block | palettes | **total** |
|---|---|---|---|---|---|---|---|---|
| Johnny Cage | 226 | 138,766 | 21,062 | 2,008 | 2,774 | 1,974 | 160 | **166,744** |
| Baraka | 214 | 131,895 | 20,472 | 1,900 | 3,001 | 1,938 | 160 | **159,366** |
| Raiden | 189 | 164,985 | 20,261 | 1,731 | 2,818 | 1,906 | 160 | **191,861** |
| Kintaro | 67 | 123,795 | 13,255 | 738 | 2,019 | 446 | 96 | **140,349** |
| (others for reference) Kung Lao 186,337; Liu Kang 175,919; Kitana set 186,037; Shang 180,082; ninjas 221,151; Jax 200,921; Kahn 91,636 | | | | | | | | |

* Four donors together ≈ **658 KB** of graphics/frames/tables. CONFIRMED as measured; it is the
  *packed* MK2 size – if UMK3 needs a different sprite codec the converted size will differ.
* No tile group is shared between sets (`sizes.py` prints none), and decoded regions never
  overlap; together they cover 2,003,360 of 3,145,728 ROM bytes (`coverage.py`). CONFIRMED.
* Data is scattered: Baraka's tile groups live in 20 banks ($05, $C9-$EF; one group at
  $05:E67B = free space of code bank 5), frames in $DE, $E1, $E2, $ED. Cage frames $E0, $E3, $EB;
  Raiden frames $DB, $DE, $E3; Kintaro frames $C8 and $EF (one 35-byte group at $00:FF9C).
* Effect frames referenced *directly* from scripts (lower bound): Cage 2 frames of set 12, Baraka 2
  of set 12, Raiden 16 of set 13 (278 tiles, ~9 KB decoded – lightning), Kintaro none.
  Projectiles spawned by code (Cage's green bolt, Baraka's blade sparks, Raiden's lightning bolt,
  Kintaro's fireball) use effect sets 11-14 through other objects and are not yet attributed.
  LIKELY 10-40 KB extra.
* Move code is small by comparison: special-move checks for all 12 fighters are in
  $81:A9D1-$81:B50C (~3 KB), move routines sit in banks 81/83 (e.g. $83:DD10-$83:EE31 for the
  table $83:DCC1 is ~4.4 KB for 14 routines). MK2 code will not run in UMK3's engine anyway; it is
  mainly a behaviour reference. LIKELY estimate: < 5 KB per donor.

## 7. Palettes

* Global palette table **$85:D33D**: 174 (=$AE) 24-bit pointers to 16-colour BGR555 palettes; it
  ends exactly where $85:D547 begins. Loader $83:F8CC (A = ID): copies 32 bytes to the CGRAM
  shadow chosen by `$84:CE52` + mode offset `$84:CEA4[$2EE4]`. **CONFIRMED**.
* Per-fighter palette IDs (main / alt / effect1 / effect2 / morph / frozen; `python3 -I palettes.py`):

| fighter | main | alt | eff1 | eff2 | morph | frozen |
|---|---|---|---|---|---|---|
| Kung Lao | 11 | 12 | 98 | 98 | 52 | 13 |
| Liu Kang | 44 | 43 | 99 | 99 | 54 | 45 |
| Johnny Cage | 00 | 01 | 9B | 9B | 51 | 04 |
| Baraka | 39 | 3A | A1 | (00) | 5A | 3C |
| Kitana | 27 | 28 | 9C | 9D | 50 | 2C |
| Mileena | 29 | 2A | 9E | (00) | 55 | 2C |
| Shang Tsung | 4B | 4C | 4E | 4E | 4B | 4F |
| Raiden | 32 | 33 | AA | AA | 56 | 35 |
| Sub-Zero | 17 | 1A | A3 | A3 | 59 | 1D |
| Reptile | 18 | 1B | A4 | A2 | 57 | 1D |
| Scorpion | 19 | 1C | A7 | A7 | 58 | 1D |
| Jax | 0C | 0B | AC | AC | 53 | 0D |
| Kintaro | 40 | 40 | 41 | 41 | – | 42 |
| Shao Kahn | 5E | 5E | 60 | 60 | – | 61 |
| Smoke | 1F | 1F | A7 | A7 | – | 1D |
| Noob Saibot | 1E | 1E | A7 | A7 | – | 1D |
| Jade | 2B | 2B | 9C | 9C | – | 2C |

* Ninja palettes (render `out/mk2/pal_ninja_set7.png`, set 7 frame 40): $17 Sub-Zero blue,
  $18 Reptile green, $19 Scorpion yellow, $1A/$1B/$1C mirror-match alternates, $1D frozen cyan,
  $1E Noob Saibot (all black), $1F Smoke (grey), $20-$25 red-streaked variants of the six,
  $26 dark/olive variant. Main/alt IDs CONFIRMED from tables; $20-$26 purposes LIKELY (gore/
  fatality variants). Female set (`pal_female_set4.png`): $27 Kitana blue, $28 alt, $29 Mileena
  purple, $2A alt, $2B Jade green, $2C frozen, $2D-$31 red-streaked variants.
* Donor palettes (`pal_baraka_set3.png`, `pal_cage_set2.png`, `pal_raiden_set6.png`,
  `pal_kintaro_set9.png`): Baraka $39-$3F block at $EF:CAD4 (7 palettes), Cage $00-$0A at
  $EF:88BE, Raiden $32-$38 at $EF:CBB4, Kintaro $40-$42 at $EF:F32B. All palette data sits in bank
  $EF except Shang Tsung's block $4B-$5D (bank $CE:7D9F) and IDs $64/$65 ($85:FFBF/$85:FFDF).
* Palette ID $A8 points into $85:D597 (inside the ID tables) – probably unused. LIKELY.

## 8. Special-move input dispatch (move code entry points)

* $81:A943: `[$0A]` = per-button-event table, `lda [$0A],y` with y = fighter×2, `jml [$1900]`
  (bank 81). Event tables (12 entries, $AACD = nothing): $81:A989, $81:A9A1, $81:A9B9 (selected by
  $81:A97A/$A97F/$A984), $81:AA88 (after `$330A`), $81:AAA0 (after `$330E`). Selected through
  the jump table $81:A901. **CONFIRMED**.
* Check routines call **$81:C8CB** (X = time window, A = input-sequence address in bank 81,
  sequences at ~$81:C9E8-$81:CD35) and on success `lda #routine; jmp $81:C83F` (bank-81 move),
  `$81:C852` (bank-85 move) or `$81:C7C6/$C7D5/$C78F` (distance-checked, used with $C763/$C75D,
  LIKELY fatality range checks under `$327E == 3`). 64 calls to $81:C8CB in $81:A9F1-$81:C7A8.
* Donor entries (`python3 -I specials.py`, linear walk, so lists may be incomplete – LIKELY):
  * Baraka: $81:B054 (sequences $CC65, $CC58, $CB20, $CC4B; moves $81:C250, $81:BAF4, + range
    checks $C763/$C75D, $CD0E).
  * Johnny Cage: $81:B0C3, $81:B0E0, $81:B38D (moves $81:BB2F, $81:B53A, $81:C346, $81:B544, ...).
  * Raiden: $81:AA0F, $81:AA2D, $81:AB0A (move $81:B558 → $83:DCB4 index $D).
  * Kintaro, Shao Kahn, Smoke, Noob, Jade: no entries (tables have 12 entries) – they are CPU-only.
* $81:B51C-$81:B55D are stubs `lda #n; jml $83:DCB4` → `jmp ($83DCC1,x)`; the table is in
  ascending address order $83:DD10..$83:ED27 (14 routines) plus $83:DCBE default. CONFIRMED.

## 9. Stages

Stage ID = `$7E:3270`. **CONFIRMED**: $82:D7B3 prints the name from **$82:DD76** (16-bit pointers
in bank 82); $83:AEBD advances `inc; cmp #9; bcc` and wraps to 0, so stages 0-8 rotate; stage 9 is
special-cased ($83:9DDE resets it to 0 afterwards, $84:AFA3).

| ID | name ($82:DD76) | tiles (packed→raw, type) | metatiles | unique map blocks | palette | packed total |
|---|---|---|---|---|---|---|
| 0 | The Dead Pool | $C3:0000 23,737→26,432 (t2) | $E6:BA5F 4,170 | 8 / 1,061 B | $EF:D310 | 29,160 |
| 1 | Kombat Tomb | $C7:98B1 17,863→25,312 (t1) | $EC:CDB1 1,916 | 6 / 656 B | $EF:D250 | 20,627 |
| 2 | Wasteland | $C6:5637 21,785→28,736 (t1) | $EC:528C 2,030 | 5 / 423 B | $EF:D910 | 24,430 |
| 3 | The Tower | $CE:0000 23,041→27,168 (t1) | $E8:888C 3,375 | 7 / 1,006 B | $EF:D610 | 27,614 |
| 4 | Living Forest | $C0:0000 28,439→30,944 (t2) | $E9:BECD 2,919 | 6 / 866 B | $EF:D790 | 32,416 |
| 5 | The Armory | $C6:0000 22,071→26,784 (t2) | $E9:A7E6 2,942 | 7 / 833 B | $EF:DA90 | 26,038 |
| 6 | The Pit II | $C9:2CB8 11,313→15,680 (t1) | $ED:C357 1,299 | 7 / 675 B | $EF:D9D0 | 13,479 |
| 7 | The Portal | $C8:0000 17,480→24,224 (t1) | $ED:06B5 1,686 | 5 / 332 B | $EF:D6D0 | 19,690 |
| 8 | Kahn's Arena | $D4:6E73 22,158→26,624 (t1) | $EB:1D03 2,428 | 8 / 782 B | $EF:D3D0 | 25,560 |
| 9 | (no name entry) | $C8:4448 17,029→18,336 (t1) | $EC:0882 2,148 | 5 / 669 B | $EF:D490 | 20,038 |

* Loader **$82:F04F** (called from the fight setup $85:B447): record = **$82:EDFC +
  $82:EF50[stage]** (34 B each): +0..+3 banks (tiles, metatiles, maps, palette), +4 tiles lo,
  +6 metatiles lo, +8 palette lo (192 B = 6 palettes → `$7E:B91C`), +$A..+$20 12 map-block lows.
  Tiles: decompress to `$7F:0000`, DMA to VRAM. Metatiles = 4 tilemap words (TL, TR, BL, BR).
  Each map block = 16×16 metatile words (512 B) expanded by $82:F1AB into a 32×32 tilemap
  (bit 15 of the map word → tilemap bit 13); destinations $82:EF64 build two 5-screen-wide bands
  (blocks 0-4, 5-9) and one 2-screen band (10-11). **CONFIRMED**: decompression ends exactly at the
  buffer start for all 84 blocks (`lz_validate.py`), and all 10 stages render recognisably
  (`out/mk2/stage0..9.png`, `stages_all.png`; my band placement is approximate).
* Stage 9 shows stone arches with a carved figure → LIKELY **Goro's Lair** (the task's tenth stage).
  The arena names list has 9 entries, so it has no name.
* Other per-stage tables: $80:860E/$80:8622/$80:8636 (words → `$332C`, `$3272`, `$3274`),
  $82:E6BE (scroll/parallax descriptors), $82:E732 (4 B), $82:EF8C (10 B: `$C8A0`, floor-ish
  `$2ECE`, `$2EE0`, `$2EE2`, `$2EDC`), $82:EFF0, $82:FD66 (per-stage init code jump table),
  $83:A77E/$83:A788/$83:A792/$83:A79C (1 B → $84:8939, LIKELY music). CONFIRMED indexed by stage;
  meanings LIKELY. Animated stage props (e.g. Kombat Tomb spikes, Dead Pool acid) were not mapped.
* Budget: all ten stages = 239,052 B packed (+ the small tables above).

## 10. General LZ decompressor $85:B9FC (used for stages; port `mk2lz.py`)

Header: u16 uncompressed size, u8 type. Output is written **backwards** from the end. Commands
(first byte c): `1LLLLooo oooooooo` copy L+3 bytes from distance ((c&7)<<8|o)+1;
`01nnnnnn` n+1 literals; `001kkkkk` copy 1 byte from distance k+1; `000kkkkk bb` fill k+2 bytes
(k = 0 ends). Type 2 decodes into a virtual buffer [even bytes | odd bytes] (de-interleaved
bitplanes/tilemap halves) with byte copies, and `001kkkkk bb` there means a descending run of k+3
bytes (ascending in memory – tilemap index runs). Return value = size. **CONFIRMED** by the
end-of-stream check on 30+ stage blocks. Not used for fighter sprites.

## 11. ROM layout overview

* $80:8000-$85:FFFF (upper halves of file banks 00-05): code. Lower halves $C0:0000-$C5:7FFF hold
  data (e.g. Living Forest tiles $C0:0000, Dead Pool tiles $C3:0000, Baraka shadow/box tables $C0:6F17).
* $C6-$C9, $CE, $D4: stage tiles; $CA-$EF: fighter sprite groups/frames/tables; $EF: palettes,
  tile-group tables, frame tables, position tables.
* $CE:7D9F-$D4:FFFF (~426 KB) not covered by sprite/stage data; sound init $84:8279 reads an index
  at $CE:9900 → LIKELY music/SFX; also fonts, portraits, intro/ending art (not mapped).
* Coverage: `python3 -I coverage.py` (banks $CA-$CD, $D5-$DA, $DC, $DE, $DF, $E3, $E4 are 100%
  sprite data).

## 12. Cross-check with MK3/UMK3 (quick, outside this topic)

`python3 -I crosscheck_umk3.py`: a wildcard byte pattern of the LZ back-reference decoder is found
twice in each game at the same distance ($158): MK2 $C5:BA8D/$C5:BBE5, MK3 $C6:E4AB/$C6:E603,
UMK3 $C8:ADC1/$C8:AF19 → LIKELY UMK3 has the same general decompressor (stage data may be
transplantable as is). The MK2 tile mask-expansion handler pattern and the animation-command check
were **not** found in MK3/UMK3 → LIKELY a different sprite codec/animation engine; donor sprites
will need re-encoding. Needs confirmation by the UMK3 mapper.

## 13. Useful RAM (bank $7E)

| addr | meaning | tag |
|---|---|---|
| $2EF8 / $30A6 | P1 / P2 fighter ID | CONFIRMED |
| $3270 | stage ID | CONFIRMED |
| $4C10,x | object fighter ID | CONFIRMED |
| $4C3C,x | frame word (set<<9 \| frame); $4C26,x cached set×2 | CONFIRMED |
| $2006,x / $201C,x | frame pointer low / bank | CONFIRMED |
| $2048,x / $205E,x | object H / V flip ($FFFF = flipped) | CONFIRMED |
| $76BC.. | decoded tile buffer, DMA'd per object (base $84:C768,x) | CONFIRMED |
| $2ED8 | shadow enable (0 on stage 6) | LIKELY |
| $2EE4 | game mode (palette slot offsets, 4/5/$D used) | LIKELY |
| $327E | round/fight phase (3 = finishing-move window) | LIKELY |

## 14. Open questions / next steps

1. Attribute effect-set frames (sets 11-14) to each donor's projectiles (follow the process spawns
   `$85:DF5D` from Baraka/Cage/Raiden/Kintaro move code).
2. Full call-graph size of each donor's move code (special moves, fatalities, friendship/babality,
   Kintaro's AI) – a recursive-descent walk from the entry points in section 8.
3. Hit/attack box data (not found as per-frame data).
4. Sound: per-fighter sample/SFX IDs (`FFF9` script command, $84:8855 calls) and the $CE:9900 index.
5. Portraits / select-screen and battle-plan graphics (sets 15/16, $82:D059, $82:E104).
6. Exact meaning of the per-fighter jump tables $80:CA99..$85:AC98 and the $83:DCC1 routines.
