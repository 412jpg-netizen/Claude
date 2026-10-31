# Ultimate Mortal Kombat 3 (SNES, USA): base-ROM map for the "mktrilogy" hack

ROM: `/home/claude/work/roms/umk3.sfc` (read-only).
- Size: 4 MB (4,194,304 bytes), no copier header.
- Header title: "ULTIMATE KOMBAT 3".
- Map mode `$FFD5 = $31` (HiROM + FastROM). ROM size byte `$FFD7 = $0C` (4 MB).
- Checksum `$64E9`, complement `$9B16`. The byte sum of the file equals `$64E9`, so the ROM is an unmodified dump.

Addresses are SNES addresses written `$BB:AAAA`. HiROM file offset = `addr & $3FFFFF`, so `$C8:9984` and `$88:9984` are both file `0x089984`. Code banks are addressed as `$80`-`$88`; data banks as `$C9`-`$FF`.

Every claim is tagged:
- **CONFIRMED**: I traced the code that uses the data, then decoded or rendered the data and checked it.
- **LIKELY**: based on a heuristic, a pattern match, or only one side of the trace.

All work is static analysis. Nothing was emulated or executed except my own Python scripts.

Locations:
- Scripts: `/home/claude/work/scripts/umk3/`. Run them as `python3 -I <script>` from that directory, because each script inserts its own directory into `sys.path`.
- PNG evidence: `/home/claude/work/out/umk3/`.

---

## 0. Tooling notes (read first)

* **Shared-lib bug 1.** The capstone wrapper in `/home/claude/work/lib/snes.py` cannot disassemble the 8-bit-M / 8-bit-X mode (capstone raises `CS_ERR_MODE`). I wrote `d65.py`, a self-contained table-driven 65816 disassembler that tracks REP/SEP. Its API is `dis1`, `lst` and `show`.
* **Shared-lib bug 2.** `snes.to_off` treats banks `$FE`/`$FF` as WRAM, so it returns `None` for valid ROM data in `$FE:xxxx`/`$FF:xxxx`. UMK3 keeps palettes and screen data there. `u.py` monkey-patches `snes.to_off` so that only `$7E`/`$7F` count as WRAM. **The shared lib itself was not modified**, so any other agent using `snes.to_off` on `$FE`/`$FF` addresses will hit the same bug.
* `trace.py` + `run_trace.py` form a recursive-descent tracer over banks `$80`-`$88`.
  - Seeds: the vectors plus 292 process entry points found from `LDA #lo / LDX #bank / JSL creator` patterns.
  - Output: `out/umk3/trace.pkl`.
  - Helpers that read it: `refs.py ADDR` (traced instructions whose operand equals ADDR) and `xref.py ADDR` (raw byte-pattern xref; it has false positives in data banks).
  - The tracer also decodes some ASCII as code (e.g. "EOR $415452"), so treat hits in banks `$01`-`$3F`/`$40`-`$7D` as noise.
* Main decoders:
  - `sprite.py`: fighter sprite sets, frames, tiles, palettes, renderer.
  - `lz.py`: general LZ decompressor, both modes.
  - `render_screen.py`: screen/stage layers.
  - `render_vs.py`: VS portraits.
  - `pals.py`: palette table.
  - `dumptab.py` / `ftabs.py`: per-fighter tables.
  - `free.py`: free space.

---

## 1. Executive summary

* **Roster.** 28 fighter IDs (0-27). Rain (24) and Noob Saibot (23) are already full fighters in the SNES base game: they have grid cells, select-screen portraits, VS portraits, palettes and animation tables. **CONFIRMED** (sections 2, 4, 7, 8).
  - **Consequence for the hack:** the "palette-swap Rain/Noob" quick win is already in the base ROM. Nothing needs adding for those two.
* **Free slots.**
  - ID 11 (Sheeva's slot in arcade MK3 order) is completely empty: null animation pointer, null name, palette 0, not on the grid. **CONFIRMED** empty; that it was Sheeva is **LIKELY**.
  - ID 25 is a spare male ninja: male-ninja animation table, Scorpion palettes, a VS portrait, but no name and no grid cell. **CONFIRMED**.
  - Both are ready-made slots for new fighters.
* **Male ninjas.** All 8 (IDs 18-25) share one sprite set (set 27, header `$85:8000`) and one animation table (`$85:8010`). They differ only by palette ID:
  - Primary palettes: table `$88:9D23`.
  - Alternate (mirror-match) palettes: table `$88:9D3F`.
  - The palette table itself is at `$88:9984`.
  - **CONFIRMED**; the renders match (`ninja_palettes_on_sprite.png`).
* **Sprite format fully decoded:** set header → bank table / frame table / tile directory / delta table; frames made of 16x16 and 8x8 pieces; tiles raw 4bpp, raw 2bpp, or "mask-compressed". **CONFIRMED** (`sprite.py`, `roster_stance.png`).
* **General LZ decompressor `$88:AD30` ported, both modes.** Every stream tried decodes exactly. **CONFIRMED** (`lz.py`).
* **Select screen.**
  - 24 cells, mapped to fighters by `$86:A207`.
  - Direction tables at `$86:A6C6`/`A6DE`/`A6F6`/`A70E`.
  - Hidden center cell 10 is used for Kahn/Motaro.
  - The BG is a mode-3 8bpp layer; its portrait art has been decoded and rendered.
  - **CONFIRMED** (`screen13_L0.png`).
* **The ROM is full.** Only about 9.1 KB of contiguous free space exists (`$FF:DC6E-$FF:FFFF`). Adding Trilogy fighters means expanding to ExHiROM. The code style (24-bit `[dp]` pointers with bank bytes taken from tables) makes that look feasible. **LIKELY** (section 11).

---

## 2. Header, vectors, main loop, process system

| item | value | tag |
|---|---|---|
| Native NMI | `$00:8765` | CONFIRMED (vector) |
| Native IRQ | `$00:8738` (JMLs to `$80:8743`) | CONFIRMED |
| Native/emulation RESET | `$00:83D7` | CONFIRMED |
| COP / BRK / ABORT | `$00:83D6` | CONFIRMED (vector value) |

Reset sequence (CONFIRMED, `d65.py` at `$00:83D7`):
- `SEI`, `CLD`, native mode, `REP #$30`, S = `$1FFF`, D = `$1800`, DB = `$7E` (`PEA $7E7E`, `PLB` x2).
- `JSL $88:C7E4`, then `JML $80:83F2` at `$00:83EE`, so the game runs in the FastROM mirror. The stub occupies `$00:83D6`-`$00:83F1`.
- The IRQ stub `$00:8738`-`$00:8742` saves registers, then `JML $80:8743`.

Interrupts:
- The per-frame work is done in the IRQ, a V-IRQ programmed through `$4209` from `$1A28`. **CONFIRMED** (`dis_808000.txt`).
- The NMI vector target `$00:8765` is a bare RTI, and so is `$00:83D6` (COP/BRK/ABORT). **CONFIRMED**.

Process system (Williams-style cooperative scheduler). CONFIRMED by many call sites (`run_trace.py` seeds):

| routine | role |
|---|---|
| `$88:C6E7` | create process: Y = process id, A = entry address, X = bank |
| `$88:C637` | sleep A frames |
| `$88:C7B6` | push a call frame (used as `PEA bank / PEA addr / PHA / JSL $88C7B6`) |
| `$88:C7CC` | return / end of script step |
| `$88:C66C` | kill process |

Other process creators: `$88:90F8`, `$80:F482`, `$85:C6CC`, `$85:C6F7`, `$85:C93B`, `$85:C911`.

Other plumbing:
- OAM is built at `$80:8000` (**LIKELY**).
- VRAM DMA queue (**CONFIRMED** from code shape, `dis_87E800.txt`):
  - Enqueue at `$88:BA4A`: A = source, X = VRAM address, Y = size, bank on the stack.
  - Flush at `$88:BA79`.
- Palette shadow:
  - Base `$7E:C1A8`; `$85:CD8B` writes a 16-color slot there.
  - The sprite half is DMA'd from `$7E:C2A8` by `$87:FE15`.
  - **LIKELY**: `$C1A8` is CGRAM color 0 and `$C2A8` is color 128.

---

## 3. Roster and fighter-ID variables

Fighter-ID variables (CONFIRMED, `refs.py 52C8`, `out/umk3/refs_52C8.txt`):

| variable | meaning |
|---|---|
| `$52C8,X` | fighter ID of the player object (X = 0 for P1, 2 for P2) |
| `$52F8,X` | current frame ID |
| `$36D0` | P1 selected fighter |
| `$3894` | P2 selected fighter |
| `$3A50` / `$3A52` | P1 / P2 select-cursor cell |

| ID | fighter | sprite set | ID | fighter | sprite set |
|---|---|---|---|---|---|
| 0 | Kano | 0 | 14 | Smoke (robot) | 14 |
| 1 | Sonya | 1 | 15 | Kitana | 26 (female ninja) |
| 2 | Jax | 2 | 16 | Jade | 26 |
| 3 | Nightwolf | 3 | 17 | Mileena | 26 |
| 4 | Sub-Zero (unmasked) | 4 | 18 | Scorpion | 27 (male ninja) |
| 5 | Stryker | 5 | 19 | Reptile | 27 |
| 6 | Sindel | 6 | 20 | Ermac | 27 |
| 7 | Sektor | 7 | 21 | Classic Sub-Zero | 27 |
| 8 | Cyrax | 8 | 22 | Human Smoke | 27 |
| 9 | Kung Lao | 9 | 23 | Noob Saibot | 27 |
| 10 | Kabal | 10 | 24 | Rain | 27 |
| 11 | **empty** (null pointers) | none | 25 | **spare ninja** (Scorpion palette) | 27 |
| 12 | Shang Tsung | 12 | 26 | Motaro | 15 |
| 13 | Liu Kang | 13 | 27 | Shao Kahn | 16 |

* **CONFIRMED.** Each ID was rendered from its own animation table (frame of animation 0) and its own primary palette: `render_roster.py` → `out/umk3/roster_stance.png`. 26 = Motaro and 27 = Shao Kahn were checked visually.
* Fighter → sprite set comes from the frame IDs in each fighter's animation scripts: set = `frameID >> 9`. **CONFIRMED**. Sets 7, 8 and 14 share one header (`$86:C9AB`), so the three robots use the same graphics (section 6.1).
* The IDs 0-14 follow arcade MK3 order with Sheeva at 11, so ID 11 was probably Sheeva. **LIKELY**.
* Name strings:
  - Word-pointer table at `$83:E544` (bank `$83`). The strings carry a `-` prefix (e.g. `-SONYA` at `$83:E490`).
  - It is used by the tournament screen code around `$83:E363` with `$F548,X`.
  - Entries run through 24 (Rain). Entries 11 and 25 are null; 26 is `? ? ? ? ?`.
  - **CONFIRMED** (`xref.py C3E544`, `out/umk3/ascii_strings.txt`).

---

## 4. Per-fighter tables (indexed by the fighter ID from `$52C8`)

### 4.1 Animation tables (CONFIRMED)

* `$88:95C3`: 28 x 4 bytes, 24-bit pointer plus a pad byte, pointing to the fighter's **animation-script word table**. Loaded by `$88:9576`.
  - `$88:9633` is a second 4-byte table loaded by `$88:95A0`. Its pointers equal the first table's plus `$98`. **LIKELY** meaning: the second half of the animation table (76 words = `$98` bytes).
* Shared animation tables:

  | fighters | table |
  |---|---|
  | male ninjas 18-25 | `$85:8010` |
  | female ninjas 15-17 | `$85:CE40` |
  | robots 7, 8, 14 | `$86:CA27` |
  | Motaro (26) | `$88:C027` |
  | Kahn (27) | `$88:BB97` |
  | ID 11 | 0 (null) |

* Animation scripts:
  - Each script is a list of words. A word is either a frame ID or a command.
  - `$FFFF` followed by a word is a jump.
  - Commands `$FFEA`-`$FFFF` are dispatched through the jump table at `$88:89E2`.
  - Command `$FFF8` is the per-fighter branch: `byte fighterID, word target`, handled by `$88:8804`. This is how the shared ninja scripts diverge per ninja.
  - The player animation loop is `$88:87DD`; the frame is stored into `$52F8,X` by `$88:87A2`.
* **Frame ID** = `(set << 9) | frame`, with frame 1-based and 9 bits wide. `$88:A471` does `XBA ; AND #$00FE` to index the set tables. **CONFIRMED**.

### 4.2 Palette selection (CONFIRMED)

Primary/alternate palette IDs (byte tables, values are indices into the palette table at `$88:9984`). Decimal, with hex in brackets:

| fighter | primary `$88:9D23` | alt `$88:9D3F` |
|---|---|---|
| Kano | 1 | 0 |
| Sonya | 8 | 9 |
| Jax | 16 | 17 |
| Nightwolf | 21 | 22 |
| Sub-Zero | 26 | 27 |
| Stryker | 39 | 40 |
| Sindel | 33 | 34 |
| Sektor | 51 | 52 |
| Cyrax | 53 | 54 |
| Kung Lao | 46 | 47 |
| Kabal | 82 | 83 |
| id11 | 0 | 0 |
| Shang Tsung | 74 | 75 |
| Liu Kang | 68 | 69 |
| Smoke (robot) | 56 | 57 |
| Kitana | 90 ($5A) | 93 ($5D) |
| Jade | 89 ($59) | 92 ($5C) |
| Mileena | 88 ($58) | 91 ($5B) |
| **Scorpion** | 112 ($70) | 130 ($82) |
| **Reptile** | 118 ($76) | 135 ($87) |
| **Ermac** | 113 ($71) | 131 ($83) |
| **Classic Sub-Zero** | 114 ($72) | 132 ($84) |
| **Human Smoke** | 115 ($73) | 133 ($85) |
| **Noob Saibot** | 116 ($74) | 136 ($88) |
| **Rain** | 117 ($75) | 134 ($86) |
| **id25** | 112 ($70) | 130 ($82) |
| Motaro | 148 ($94) | 148 |
| Shao Kahn | 151 ($97) | 151 |

Where the choice is made:
- At `$88:9874`-`$88:98BD`:
  1. `JSL $88:98BE` returns a carry bit.
  2. Carry set → clear bit `$40` of `$5538,X` and use `$88:9D23[id]`.
  3. Carry clear → set bit `$40` and use `$88:9D3F[id]`.
  4. In both cases `JSL $88:9842` → `$85:CD14` loads the palette.
- `$88:98BE`:
  - If `$3BEE != 0` or `$F5A6 == 1`, P1 gets the primary palette and P2 the alternate. `$3BEE` is incremented by kombat-kode handlers 6 and 37.
  - Otherwise it compares `$36D0`/`$3894` (same fighter on both sides → the second player gets the alternate).
  - Shang Tsung (ID `$0C`) is special-cased via `$388E` because of morphing.
  - **CONFIRMED** code path; the exact meaning of `$3BEE`/`$F5A6` is **LIKELY** (random-character / attract modes).
- `$82:9D59` (second user):
  - Fighters ID >= 15 use `$9D3F`/`$9D23` according to the same `$5538` bit `$40`.
  - Fighters < 15 use a byte from `$88:9E19 + id`.
  - Then `JSL $85:C72B`, and per-fighter x/y offsets are read from `$82:9E72` (4 bytes per ID).
  - `$86:C90E` also reads `$88:9D23`; its purpose is unknown.

**To recolor a fighter:** change its byte in `$88:9D23`/`$88:9D3F` (pick another palette ID), or edit the 16 colors the palette table points to. See section 5.

### 4.3 Other per-fighter tables

Found by scanning traced `LDA long,X` / `abs,X` users of `$52C8`-derived indices (`ftabs.py`, `dumptab.py ADDR WIDTH`). All are **CONFIRMED** to be indexed by fighter ID (traced users); every meaning is **LIKELY** unless stated.

| table | width | notes |
|---|---|---|
| `$82:9E72` | 4 | x/y offset pair used by `$82:9D85`. Ninjas -5,-2; bosses `$100` |
| `$88:9D5B`, `$88:9D77`, `$88:9D93` | 1 | more palette IDs; use unknown |
| `$88:9DAF` | 1 | palette ID used at `$85:C59D` |
| `$88:9DC9` | 1 | palette ID (Noob = `$60`) |
| `$88:9DE5` | 2 | palette ID for the frame in `$85:AEBA`. Rain `$8E`, Noob `$74`. **LIKELY** babality palette (`render_misc.py` → `tab_85AEBA_frames.png` shows baby frames) |
| `$85:AEBA` | 2 | frame ID per fighter (baby/babality frame, see above) |
| `$88:9E19` | 1 | palette IDs for fighters 0-14 only (`$82:9D75`) |
| `$88:9E28` | 2 | Noob `$74`, Rain `$130`; meaning unknown |
| `$80:986C`, `$84:D11B`, `$86:FDA1`, `$87:E73A`, `$82:A5A6`, `$82:C071`, `$81:C1EF` | 2 | meaning unknown |
| `$81:B104`, `$81:B190` | 2 | `$FFFF` for Noob, Rain, id25 and the bosses; **LIKELY** "feature not available" (finisher-related?) |
| `$83:F29D` | 2 | jump table, per fighter |
| `$86:8E15` | 2 | jump table. Smoke and Human Smoke → `$8E4D`, Motaro → `$8E9A`. **LIKELY** involved in the Human Smoke / Motaro special cases |
| `$86:FC28`, `$88:96C0`, `$88:9955` | 1 | meaning unknown |
| `$87:E436` | 2 | non-zero for robots only |
| `$88:9729`, `$88:9799` | 4 | meaning unknown |
| `$80:F7E4`, `$81:AB7D`, `$80:D1F7` | 2 | all entries equal |
| VS-screen tables `$83:EE92`, `$83:EEC6`, `$83:EEFA`, `$83:EF2E`, `$83:EF62`, `$83:EFE6` | 2 | 26 entries (IDs 0-25), see section 8 |

---

## 5. Palettes (CONFIRMED)

* **Palette table `$88:9984`.** 309 entries of 24-bit pointers to 16-color BGR555 palettes (32 bytes).
  - `$88:9984 + 309*3 = $88:9D23`, so the table ends exactly where the primary-palette table starts. It cannot be extended in place.
  - Found with `ptrruns.py`; rendered with `pals.py` → `paltable_000.png`, `paltable_080.png`, `paltable_160.png`, `paltable_240.png`, and `fighter_palettes.png` (primary and alt per fighter).
* **Loader `$85:CD8B`.**
  - Input: A = palette ID (in `$0A`), X = slot.
  - It computes `X = ID*3`, then `LDA $889984,X` / `LDA $889986,X` → `$4A`/`$4C`.
  - It copies words Y = `$1E` down to `$02` (**colors 1-15; color 0 is not copied**) through `JSL $85:CC74` (per-color transform, **LIKELY** fade/brightness) into `($52),Y` with `$52 = $C1A8 + slot*16`.
  - The only long-mode xrefs to `$88:9984`/`$88:9986` are the two at `$85:CDA2` and `$85:CDA8` (`xref.py 889984`). Relocating or enlarging the table should therefore need only those two operands patched. **LIKELY**: abs-mode users with DB = `$88` were not found, but cannot be ruled out.
* **Male-ninja palettes.** Primary IDs `$70`-`$76`, alternates `$82`-`$88` (table in 4.2). `render_ninjas.py` → `ninja_palettes_on_sprite.png` renders male-ninja frame `$7F` of set 27 in every one of them.
  - Noob's primary palette is all-black; his alternate is dark grey.
* **Adding a new ninja color** (e.g. Chameleon or Tremor style) means:
  1. Add a 32-byte palette anywhere.
  2. Add a palette-table entry (the table must be relocated first, see above).
  3. Point `$9D23`/`$9D3F` for the slot at it.
  - Chameleon-style palette cycling would need new code. **LIKELY**.

---

## 6. Sprite graphics format (CONFIRMED, `sprite.py`; renders: `roster_stance.png`, `kano_f36.png`, `scorpion_f7F.png`)

### 6.1 Sprite sets

* `$86:EAEC`: 28 words, bank of each set header (low byte).
* `$86:EB24`: 28 words, address of each set header.
* Sets 0-14 = fighters 0-14.
  - Set 11 is null (bank 0, address 0), matching the empty ID 11.
  - Sets 7, 8 and 14 (Sektor, Cyrax, Smoke) all point at the same header, `$86:C9AB`: one shared robot set.
* Set 15 = Motaro (header `$88:C017`), set 16 = Kahn (`$88:BB87`).
* Set 17 is at `$80:8F7C`. Sets 18-25 are consecutive 16-byte headers at `$86:EBBC`-`$86:EC2C`. These are miscellaneous / effect sets (not catalogued).
* Set 26 = female ninjas (`$85:CE30`), set 27 = male ninjas (`$85:8000`).
* The 16-byte set header sits directly before the fighter's animation table (e.g. `$85:8000` + 16 = `$85:8010`).

### 6.2 Set header (16 bytes, read by `$88:A471`)

| offset | meaning |
|---|---|
| +0 word, +7 bank | bank table: one bank byte per 64 frames (`[$6A]`) |
| +2 word, +4 bank | tile-bank directory (`[$5E]`) |
| +5 word, +7 bank | frame-pointer table, one word per frame (`[$4E]`) |
| +8 word | unknown |
| +B bank, +C word | delta block (`[$62]`): x0, y0, 15 x-deltas, 15 y-deltas (signed bytes) |
| +E word | unknown |

### 6.3 Locating a frame (`$88:A5A8`)

```
f0   = (frameID & $1FF) - 1
bank = byte [banktab + (f0 >> 6)]
addr = word [frametab + 2*f0]
```

### 6.4 Frame data (parsed by `$83:8000`)

* Header: `byte N` (number of pieces), `byte B` (how many of those are 16x16; the 16x16 pieces come first).
* For each piece:
  - A control byte. High nibble k ≠ 0 → `x += delta[1+k]`; k = 0 → an explicit absolute x byte follows. The low nibble does the same for y using the y-deltas at `delta[16+k]`.
  - Starting position: (x0, y0). Coordinates are signed bytes.
  - A 16x16 piece is followed by 4 tile-reference words (TL, TR, BL, BR); an 8x8 piece by 1.
* Tile reference word:
  - Bits 0-1: flips (bit 0 = H, bit 1 = V).
  - Bits 2-7: byte offset into the tile-bank directory (entry index * 4).
  - Bits 8-15: tile number inside that bank.

### 6.5 Tile-bank directory entry (4 bytes) and tile codec (`$83:8362`)

* Entry: `word addr, byte bank, byte flags`.
* Flags:
  - bit 7 = mask-compressed.
  - bit 6 = 2bpp (planes 2-3 zero).
  - bits 0-5 = record size, for compressed banks.
* Raw: 32 bytes per 4bpp tile; 16 bytes per 2bpp tile (padded with 16 zero bytes).
* Mask-compressed block:
  - First byte = threshold T.
  - Record n starts at `base + 1 + n*recsize`.
  - If n >= T, the record starts with a fill byte (otherwise fill = 0).
  - Then 4 mask bytes (2 for 2bpp), then literal bytes.
  - Each mask bit, MSB first: 1 = take the next literal, 0 = fill byte.
  - The ROM reads the fill byte through the Mode-7 multiply registers (`$211B`/`$2135`). This is a trick only; the format is as above.

### 6.6 Runtime

* Tiles are assembled in WRAM from `$7E:80A8`, using slot offsets at `$86:E322`.
* They are DMA'd by `$88:B920`/`$88:B990` to VRAM addresses from `$86:E33A`.
* **LIKELY**: details beyond what was needed for the renderer were not followed.

### 6.7 Decoder usage

`python3 -I sprite.py SET FRAME PALID out.png`.
- Functions: `set_header`, `frame_ptr`, `tile_data`, `frame_pieces`, `palette_rgb`, `render`.
- `render_ninjas.render_fit()` crops a frame to its bounding box.

---

## 7. General LZ decompressor `$88:AD30` (CONFIRMED, `lz.py`, `dis_88AD30.txt`)

Stream layout: `word out_size, byte mode`, then commands.

### 7.1 Normal mode (mode ≠ 2)

Output is written **backwards** from `dst+size` down to `dst`. Y below is the current output position after decrementing.

| command c | effect |
|---|---|
| `c >= $80` | back-reference: `len = ((c>>3)&$F)+3`, `off = ((c&7)<<8) \| next byte`. Source = Y+off+1; copied word-wise, highest word first |
| `$40-$7F` | literal: n = (c&$3F)+1 bytes, in stream order, placed at [Y-n, Y) |
| `$20-$3F` | copy 1 byte from Y + (c&$1F) + 1 |
| `$01-$1F` | fill c+2 bytes with the next byte |
| `$00` | end |

### 7.2 Mode 2 (`$88:AE7D`; `lz.decompress2`)

The same command set with these differences:
- Every write steps by 2. The odd (high) bytes are produced first, top-down, then the stream wraps to the even bytes.
- A back-reference reaching past the end wraps by `- size + (size even ? 1 : 0)`.
- `$20-$3F` becomes a descending-value run: count (c&$1F)+3, starting at the next byte.
- Fill writes c+2 bytes.

Validation: `$C3:0000` (select-screen tiles, mode 2, `$9C80` bytes) ends with final Y = 0, i.e. exact. So do `$F9:FACF` (`$870`), `$F2:BAAA` (`$16C0`) and `$F9:FCB9` (`$1000`).

### 7.3 Callers

- Traced: `$83:C067`, `$83:C081`, `$84:943E`, `$84:98B0`, `$84:A4B8`, `$86:DD7F`, `$87:EEE4`.
- `$84:98B0` is a wrapper: destination in `$76`/`$78`, source in `$7A`/`$7C`.
- More call sites exist in banks `$81`/`$83`/`$86`/`$87` that the tracer did not reach (`dis_decomp_candidates.txt`). **LIKELY**.

### 7.4 Other decoders

- The mode-2 fill helpers dispatched through `$88:B19C` were not each verified individually. All streams still decode exactly, so the port is right for the data seen.
- The `mk2-map` notes record that this decompressor has the same shape as MK2's `$85:B9FC`. MK2 stage data may therefore be reusable without re-encoding. **LIKELY**.

---

## 8. Select screen, VS screen, unlocks (CONFIRMED unless tagged)

### 8.1 Screen record and grid

* The select screen is screen/stage record **13** (set at `$86:9F57`).
* **Grid table `$86:A207`**: 24 bytes, cell → fighter ID. `$FF` = hidden slot. Read by `$86:A1F7`, inside `$86:A1F6`, which writes `$36D0`/`$3894`.

| row | cells | fighters |
|---|---|---|
| 0 | 0-6 | Rain(24), Reptile(19), Stryker(5), Jax(2), Nightwolf(3), Jade(16), Noob(23) |
| 1 | 7-13 | Sonya(1), Kano(0), Mileena(17), **[hidden, $FF]**, Classic Sub-Zero(21), Sub-Zero(4), Kung Lao(9) |
| 2 | 14-18 | Sektor(7), Kitana(15), Ermac(20), Scorpion(18), Cyrax(8) |
| 3 | 19-23 | Kabal(10), Sindel(6), Smoke(14), Liu Kang(13), Shang Tsung(12) |

* Not on the grid: Human Smoke (22), id25, id11, Motaro and Kahn (except through the hidden cell).

### 8.2 Navigation

* Next-cell tables, 24 bytes each: `$86:A6C6` up, `$86:A6DE` down, `$86:A6F6` left, `$86:A70E` right.
* Blocked-cell lists: `$86:A677`, 7 bytes per direction, checked by `$86:A661`.
* The movement handler `$86:A726` skips cell 10 unless `$1C57 == 1`.
* The cursor coordinate steps seen in the handler are ±50 (x) and ±64 (y). **LIKELY**: units not verified.
* Nothing else gates cells 0 and 6, so Rain and Noob are selectable without a code. **LIKELY** (static only).

### 8.3 Cursors, selection, random select

* Cursor init: P1 at `$86:A27C` (cell 0, process `$86:A14C`); P2 at `$86:A222` (cell 6, process `$86:A0EE`).
* Selection: `$86:A3FA` → `$86:A1F6`.
* Random-select scripts: `$86:A91F`/`$86:A953` → `$86:A987`.

### 8.4 Hidden slot (`$84:A2A3`-`$84:A42B`)

* `$1C59 = $1B` (Kahn) if `$3BAE` is set; `$1C59 = $1A` (Motaro) if `$3BB0` is set.
* `$1C57` = slot state.
* Strings `ENABLE MOTARO` (`$83:D515`) and `ENABLE SHAO KAHN` (`$83:D523`) are in the "LOST TREASURES OF SHAO KAHN" reward menu. **LIKELY**: those menu items set `$3BB0`/`$3BAE`.

### 8.5 Select BG (record 13)

* **Layer 0**: descriptor `$84:8299`, type 1.
  - Tiles `$C3:0000` (LZ mode 2, `$9C80` bytes, 8bpp, i.e. 625 tiles).
  - Map `$F9:FACF`.
  - Palette block `$FF:7BC2` (96 colors). Pixel values 0-95 index this block.
  - `render_screen.py 13 0 8 own` → `screen13_L0.png` shows every portrait correctly, including Rain and Noob in the top corners.
  - The off-screen Kahn and Motaro portraits are at map rows 28-33.
* **Layer 1**: descriptor `$84:82C6`. Tiles `$F2:BAAA`, map `$F9:FCB9`, palette `$FF:7B5E`.

**Free portrait slots for the hack:**
- Cell 10 (hidden) is the only unused grid cell.
- Adding cells means rewriting:
  - the grid table (24 bytes);
  - the 4 next-cell tables;
  - the blocked lists;
  - the cursor position logic;
  - the 8bpp BG art.
- **LIKELY** effort: moderate. The tables are small and self-contained in bank `$86`.

### 8.6 VS portraits

* Loader `$83:E730`. Per fighter ID 0-25:
  - bank = `$83:EEC6[id]`;
  - tiles = LZ(`$83:EEFA[id]`), **6bpp, 48 bytes per tile** (`$83:E97E` pads each tile to 64 bytes / 8bpp);
  - map = LZ(`$83:EF2E[id]`): 32x32 words, portrait in the left 16x22, tile index = map value - 1;
  - palette = 64 colors at `$83:EF62[id]`.
* `$83:EE92` and `$83:EFE6` are adjacent 26-entry tables; meaning unknown.
* `render_vs.py` → `vs_portraits.png`: all 26 render, including Rain (purple), Noob (black) and id25 (yellow ninja).
* `vs_portraits_test.png` and `kano_vs_tiles_raw.png` are earlier debug renders (wrong 4bpp guess); ignore them.
* There is no VS portrait for IDs 26/27.

---

## 9. Stages and screens

### 9.1 Record table

Screen/stage record table `$84:8A22`: 29 records x `$22` bytes, indexed by `$3A7E * $22` in `$84:8FC8`. **CONFIRMED**.

| offset | meaning |
|---|---|
| +0 | BG mode (3 = 8bpp for select/VS) |
| +2 | TM |
| +3 | → `$EADC` |
| +4..+7 | → `$EAF2`-`$EAF8` |
| +8..+F | 4 layer-descriptor pointers in bank `$84` (`$FFFF` = none, `$8000` = special) |
| +$10..+$20 | ground line and other parameters (not decoded) |

* Fight stages: records 0-10 and 23. Records 6 and 9 share layers.
* Records 11-22 and 24-28 are menu/screens (13 = select). **CONFIRMED** for 13; the split for the others is **LIKELY**.

### 9.2 Layer descriptors

* Type 0 (`$84:913E`): palette +17/+18, tiles +1A/+1B, map +1F/+20, second map +28.
* Type 1 (`$84:920C`): palette +15/+16, tiles +18/+19, map +1D/+1E.
* Palette block = `word count, word first CGRAM index, colors` (`$84:961C`).
* Stage BGs use 16x16 metatiles (`$84:9AB8`, `$84:9C87`). **LIKELY**: the metatile format was not decoded, and fight stages were not rendered.

### 9.3 Choosing a stage

* `$80:84B8`: `$3A84` (kombat-zone choice) → record. 0 → record 5, `$70` → record 0 (and `$3A84` is cleared), anything else → the same number. **CONFIRMED**.
* Bosses:
  - Motaro → record 0.
  - Kahn → record 6, or `$17` if `$36C0 == $15`.
  - **LIKELY**: read from the boss setup; exact branch conditions not re-verified.
* Attract stage cycle at `$85:A987`: 5, 1, 2, 3, 4. **LIKELY**.
* Stage-name pointer table `$85:EE32`, indexed by `$3A84` (`$85:E903`-`$85:E908` and `$85:E9FB`-`$85:EA00`): 0 ROOFTOP, 1 THE DESERT, 2 HADES, 3 THE KAVE, 4 THE WATERFRONT, 5 LOST, 6 THE PIT 3. **CONFIRMED** (table and indexing).
  - So record N for N = 1-6 is probably the named stage. **LIKELY**.
  - The remaining fight records (0, 7-10, 23) are not named.

---

## 10. Kombat kodes, messages, win text (CONFIRMED unless tagged; dump: `out/umk3/kodes.txt`)

### 10.1 Kode table and matching

* Kode table `$85:DFF5`: 45 entries x 8 bytes, then an `$FF` terminator.
  - Each entry is 6 icon values (1-based; 0 = wildcard) and 2 zero bytes.
* Matcher `$85:E1B3` compares against the entered icons at `$7E:52F8+$18`.
* The match index+1 goes to `$3C2E`/`$3C30`. Dispatch is `JMP ($85:DF3D,X)` if `$3A90 == 1`, else `JMP ($85:DF99,X)`. The second table disables kodes 10, 29 and 36.
* The value is the arcade icon digit + 1. **LIKELY**: four published arcade kodes match their handlers exactly — 769-342 Noob = entry 13, 205-205 Smoke = 20, 969-141 Motaro = 11, 033-564 Kahn = 12. Value 11 (kode 27) is unexplained.

### 10.2 Handlers

| # | icons | handler effect |
|---|---|---|
| 1 | 2 1 1 2 1 1 | `STZ $3BC2` (**LIKELY** throws off) |
| 2 | 1 3 1 1 3 1 | `STZ $3BC6` (**LIKELY** blocks off) |
| 3 / 4 | 1 4 4 1 1 1 / 1 1 1 1 4 4 | message PLAYER 1 / PLAYER 2 HALF POWER |
| 8 / 9 | 8 1 8 1 1 1 / 1 1 1 8 1 8 | PLAYER 1 / 2 QUARTER POWER |
| 5 | 7 9 9 5 3 3 | process `$85:E554`, `INC $3BEA` |
| 6, 37 | 5 7 1 5 7 1 / 5 5 5 5 5 5 | process `$85:E675`, `INC $3BEE` (affects palette choice, 4.2) |
| 11 | 10 7 10 2 5 2 | battle **Motaro** (ID `$1A`), message `$85:EB7F` |
| 12 | 1 4 4 6 7 5 | battle **Shao Kahn** (`$1B`), message `$85:EB58` |
| 13 | 8 7 10 4 5 3 | battle **Noob Saibot** (`$17`), message `$85:EB2F` |
| 20 | 3 1 6 3 1 6 | battle **Smoke** (`$0E`), message `$85:EB0C` |
| 36 | 4 1 1 4 1 1 | `$3A78 = 1`, message SILENT KOMBAT |
| 38-43 | e.g. 9 3 1 1 3 9 | kombat zone: `$3A84` = 6, 4, 2, 3, 1, `$70` |
| 44 | 1 2 1 1 2 1 | `$3A78 \|= 2`, THROWING ENCOURAGED |
| 45 | 1 2 3 4 5 6 | `$3A78 \|= 8`, ONE BUTTON BRUTALITIES |

* The battle-X handlers go through `$85:E721`-`$85:E730`.
* The messages are plain ASCII in `$85:EAC4` onward (e.g. "WINNER OF THIS ROUND BATTLES NOOB SAIBOT").
* Message table `$85:EA3E`: 6-byte entries (flag variable, value, message pointer).
* `$80:C794`: one word per kode, `$2A17`-`$2A29` for kodes 1-20 and 37, `$FFFF` otherwise. Meaning unknown; **LIKELY** a sound or speech call ID.
* **Win text:** no ASCII "WINS" string was found. **LIKELY**: the win banner is graphics or font-tile based. Not located.
* Other text:
  - Menus and cheats in `$83:D000`-`$83:D720` (e.g. CHEATS, KOMBAT ZONE, ENABLE POWER KODE).
  - Credits in `$83:BBD9`-`$83:BD74` (Williams 1996, Sculptured Software 1995, Midway, Avalanche Software).
  - Build stamp "FRI=AUG=04== 1:49PM" at `$80:FDAF`.
  - Ending/bio text appears only as readable fragments inside banks `$E5`/`$F6` etc. **LIKELY**: LZ-compressed, with the literals visible.
  - "WELCOME TO SCOTT'S SECRET SLOT ROOM" at `$86:E07F`.
  - (`ascii_strings.txt`)

---

## 11. Free space and ExHiROM (for adding Trilogy fighters)

### 11.1 Free space today (CONFIRMED, `free.py`)

* `$FF:DC6E`-`$FF:FFFF` (file `0x3FDC6E`-`0x3FFFFF`): 9,106 bytes of `$FF`.
* Each code bank `$C0`-`$C7` (`$80`-`$87`) ends with a run of about 87-103 `$FF` bytes near `$xx:FF00` (e.g. `$C0:FF1F` 103 bytes, `$C5:FEE1` 92 bytes). Good for small hooks only.
* Data banks have no meaningful free space.
* The `mk2-map` notes estimate 140-190 KB per MK2 donor fighter, so expansion is required.

### 11.2 ExHiROM layout

* Today, bank-`$00` code is reached through the vectors: reset at `$00:83D7`, IRQ at `$00:8738`, NMI at `$00:8765`, COP/BRK at `$00:83D6`. The reset and IRQ stubs JML into bank `$80` almost immediately. **CONFIRMED**.
* In ExHiROM, banks `$00`-`$3F` (`$8000`-`$FFFF`) and `$40`-`$7D` map to file `0x400000`+. So the vectors and header are read from file `0x40FFC0`-`0x40FFFF`, and bank `$00`'s code from file `0x408000`-`0x40FFFF`.
* Conversion recipe (**LIKELY**; standard ExHiROM practice applied to these addresses):
  1. Keep file `0x000000`-`0x3FFFFF` as is. Banks `$80`-`$FF` keep mapping there, so every existing 24-bit pointer stays valid.
  2. Copy file `0x008000`-`0x00FFFF` to `0x408000`-`0x40FFFF`. At minimum this must cover the header, the vectors, and the stubs at `$83D6`-`$83F1`, `$8738`-`$8742` and `$8765`. All three were disassembled; each does at most one JSL/JML into `$80`/`$88`.
  3. Set map mode `$35` and ROM size `$0D` in the new header, then recompute the checksum.
  4. Put new data in banks `$41`-`$7D` (all of `$0000`-`$FFFF`) and `$40:0000`-`$7FFF`. `$40:8000`-`$FFFF` is the bank-`$00` mirror.
  5. Keep new code in `$80`-`$BF`/`$C0`-`$FF`. Free space there is tiny, so new code must also live in the new region and run from `$40`-`$7D` (SlowROM speed). **LIKELY** acceptable.

### 11.3 Code compatibility evidence

* Bank bytes come from tables and are used directly through `[dp]` long pointers:
  - sprite frames `$88:A5C1` `LDA [$6A],Y` → `$24A2,X`;
  - palettes `$85:CDA2`/`$85:CDB1`;
  - set headers `$88:A471`;
  - the LZ wrapper `$84:98B0` with source bank in `$7C`.
* No `ORA #$C0`-style forcing of bank bytes was seen in these paths.
* Long operands in the traced code use only banks `$80`-`$BF`, `$C0`-`$FF` and `$7E`/`$7F`, plus I/O. Apparent `$01`-`$3F`/`$40`-`$7D` operands were ASCII false positives.
* **LIKELY** compatible. Not every loader was audited.

### 11.4 Checksum checks

No traced code reads the header (`$FFC0`-`$FFDF`) or compares a checksum. The only `$FFDx` matches are immediates such as `LDX #$FFD0`. **LIKELY**: there is no anti-tamper check.

### 11.5 Risks to check when converting

* Code that sets DB from a data bank and then uses absolute addressing for WRAM or I/O. This is already impossible with DB = `$C0`+, so probably absent.
* The palette table cannot grow in place (section 5).
* VRAM budget: the select screen already uses a 625-tile 8bpp BG. **LIKELY** tight.

---

## 12. Hack-relevant conclusions (advice; tags as stated)

1. **The Rain/Noob palette-swap quick win already exists** in the base ROM. It is not needed. **CONFIRMED**.
2. Cheapest new fighters are **new male-ninja palette variants in slot 25 or 11**. They reuse set 27 and the `$85:8010` scripts; per-ninja moves branch via script command `$FFF8` (fighter ID). Work needed:
   - a palette;
   - `$9D23`/`$9D3F` bytes;
   - a name pointer (`$83:E544`);
   - a VS portrait (`$83:EE92`-`$83:EFE6` tables);
   - a grid cell.

   Slot 25 already has a working VS portrait and animation pointer. **LIKELY**: move and special-move tables for slot 25 were not audited.
3. **Grid space is the main UI constraint**: 24 cells plus one hidden cell. **CONFIRMED**.
4. **New non-ninja fighters** (Johnny Cage, Baraka, Raiden, Kintaro, Goro, MK2 Kung Lao, etc.) need, at least:
   - a new sprite set. `$86:EAEC`/`$86:EB24` hold 28 entries; only set 11 is null and reusable as-is, so more fighters mean relocating the tables (where `$88:A471` indexes them) or reusing set 17-25 entries;
   - an animation table;
   - every per-fighter table in 4.3 extended past 28 entries, or slot 11/25 reused;
   - move code.

   **LIKELY**.

---

## 13. Open questions

* Map stage records 0, 7-10 and 23 to names and art. The fight-stage metatile format (`$84:9AB8`/`$84:9C87`) is undecoded, and no fight stage was rendered.
* Meanings of most per-fighter tables in 4.3, particularly `$86:8E15` (Smoke / Human Smoke / Motaro jump table) and `$81:B104`/`$81:B190`.
* The Human Smoke selection path. ID 22 is not on the grid; the `$86:8E15` → `$8E4D` handler was not followed.
* `$80:C794` per-kode words (`$2A17`-`$2A29`).
* Whether Rain and Noob have unique special moves, or only shared ninja moves with palette changes. The `$FFF8` per-fighter branches in `$85:8010` were not enumerated per ID.
* Purpose of ID 25 (a leftover? a test slot?) and whether its move code is complete.
* Sets 17-25 contents (effects, projectiles, fatality pieces?) and per-set byte sizes. A donor/size budget like the one in `mk2-map` was not computed.
* The individual `$88:B19C` mode-2 helper routines. All tested streams decode exactly anyway.
* Win banner text / graphics location; how the ending text is stored.
* Unknown header words +8 and +E in the sprite-set header.

---

## 14. Evidence index

Scripts (`/home/claude/work/scripts/umk3/`):

| script | purpose |
|---|---|
| `d65.py` | 65816 disassembler |
| `u.py` | `to_off` fix |
| `xref.py` | byte-pattern xref |
| `refs.py` | traced-operand xref |
| `trace.py` / `run_trace.py` | tracer |
| `banks.py` | code vs data banks: `$80`-`$88` code, `$09`-`$3F` data |
| `ptrruns.py` | 24-bit pointer runs; found `$C8:9984` |
| `pals.py` | palette sheets |
| `sprite.py` | sprite decoder |
| `render_ninjas.py` | ninja palettes |
| `render_roster.py` | stance of every ID |
| `render_misc.py` | `$85:AEBA` frames |
| `dumptab.py` / `ftabs.py` | per-fighter tables |
| `findgrid.py` | found `$86:A207` |
| `lz.py` | decompressor, both modes |
| `scan_desc.py` | LZ sources in layer descriptors |
| `render_screen.py` | screen layers |
| `render_vs.py` | VS portraits |
| `free.py` | free space |

Outputs (`/home/claude/work/out/umk3/`):

| file | contents |
|---|---|
| `roster_stance.png` | stance frame of every fighter ID |
| `fighter_palettes.png` | primary and alt palette per fighter |
| `paltable_000.png`, `paltable_080.png`, `paltable_160.png`, `paltable_240.png` | the palette table |
| `ninja_palettes_on_sprite.png` | male-ninja frame in every ninja palette |
| `kano_f36.png`, `scorpion_f7F.png` | sample frames |
| `tab_85AEBA_frames.png` | `$85:AEBA` frames |
| `screen13_L0.png` | select-screen portraits |
| `vs_portraits.png` | VS portraits |
| `vs_portraits_test.png`, `kano_vs_tiles_raw.png` | superseded debug renders |
| `dis_*.txt` | disassembly listings |
| `refs_52C8.txt`, `refs_52F8.txt`, `refs_3A50.txt` | traced-operand xrefs |
| `kodes.txt` | kode table, handlers, `$80:C794` |
| `ascii_strings.txt` | ASCII strings |
| `trace.pkl` | tracer output |
