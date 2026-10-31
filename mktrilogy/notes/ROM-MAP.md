# ROM-MAP: consolidated reference for the mktrilogy hack (UMK3 base, MK3 and MK2 donors)

This is the one-stop reference. It condenses:
- `umk3-map.md`, `mk2-map.md` and `compat.md` (analyst maps);
- `verify-umk3.md` and `verify-mk2-compat.md` (independent verification);
- the planning checks in `PLAN.md` section 10.

The full evidence and longer explanations stay in those files. No raw ROM byte runs are reproduced here.

## Status legend

| mark | meaning |
|---|---|
| **verified** | The claim was re-derived by an independent verifier with their own code and held, or is a detail that verifier established. |
| **verified\*** | The verifier corrected the original claim. The corrected version is the one given here. |
| **open (single)** | One analyst traced and checked it (tagged CONFIRMED in their notes), but no verifier re-checked it. Treat as good but unconfirmed. |
| **open (LIKELY)** | A heuristic or inference. It also covers claims the verifiers marked "unverifiable". |
| **open (?)** | Unknown. Listed so the gap is visible. |

Address conventions:
- SNES addresses are written `$BB:AAAA`. HiROM file offset = `addr & $3FFFFF`, so `$88:9984` and
  `$C8:9984` are the same byte.
- `$80`-`$88` are code-bank views; `$C0`-`$FF` are data views.
- Scripts named below live in `/home/claude/work/scripts/<topic>/`; outputs in `/home/claude/work/out/<topic>/`.

Tooling caveat (**verified**, C23 / mk2:C21): the shared `lib/snes.py` has two bugs.
- `to_off` returns `None` for banks `$FE`/`$FF`. UMK3 keeps palettes, sprite tables and screen data there.
- `disasm` fails in 8-bit-M + 8-bit-X mode.

Use a fixed mapper (`scripts/compat/c.py`, `scripts/umk3/u.py`) and a capstone-free disassembler
(`scripts/umk3/d65.py`, `scripts/verify-umk3/v.py`, `scripts/verify-mk2-compat/d.py`).

---

## 0. ROM identities

| ROM | size | title | map / size byte | checksum | SHA-1 | status |
|---|---|---|---|---|---|---|
| UMK3 | 4 MB, no copier header | "Ultimate Kombat 3" | `$31` / `$0C` | `$64E9` (complement `$9B16`) = plain byte sum | `09c094ca1114bcb6d5917e989686ca79b96cf9ea` | verified (C1) |
| MK3 | 4 MB | "Mortal Kombat 3 R2.1" | `$31` / `$0C` | `$7149` = plain sum | `58e4e1259a86faaadbc982176e569cb2038dbac5` | open (single: `plan/checksum.py`) |
| MK2 | 3 MB | "Mortal Kombat II" | `$31` / `$0C` | `$7221` = sum(2 MB) + 2 × sum(last 1 MB), mirrored convention | `f6aa5291759e982ea249c4b76f729ca2f4ab1cf4` | open (single: `plan/checksum.py`) |

---

## 1. UMK3 (base ROM)

### 1.1 Vectors and bank-`$00` code

| item | value | status |
|---|---|---|
| RESET (emulation) | `$00:83D7`: SEI, CLD, native mode, `REP #$30`, S=`$1FFF`, D=`$1800`, DB=`$7E`, `JSL $88:C7E4`, `JML $80:83F2` | verified (C2) |
| IRQ | `$00:8738`: `REP #$30`, push A/X/Y/D/B, `JML $80:8743` | verified (C2) |
| NMI | `$00:8765` = RTI | verified (C2) |
| COP / BRK / ABORT | `$00:83D6` = RTI | verified (C2) |
| Bank-`$00` code ever executed | only `$83D6`-`$83EE`, `$8738`-`$873F`, `$8765` | verified (C22, code side) |
| Per-frame work runs in a V-IRQ set through `$4209` from `$1A28` | – | open (single) |
| Process system: create `$88:C6E7` (Y=id, A=addr, X=bank), sleep `$88:C637`, push frame `$88:C7B6`, end step `$88:C7CC`, kill `$88:C66C` | – | open (single) |
| VRAM DMA queue: enqueue `$88:BA4A`, flush `$88:BA79` | – | open (single) |
| CGRAM shadow `$7E:C0A8` (full image, DMA'd by `$87:FECB`); `$C1A8` = colour 128 (first OBJ palette) | – | open (LIKELY, verifier C11 extra) |

### 1.2 Fighter IDs and RAM

| ID | fighter | ID | fighter | ID | fighter | ID | fighter |
|---|---|---|---|---|---|---|---|
| 0 | Kano | 7 | Sektor | 14 | Smoke (robot) | 21 | Classic Sub-Zero |
| 1 | Sonya | 8 | Cyrax | 15 | Kitana | 22 | Human Smoke |
| 2 | Jax | 9 | Kung Lao | 16 | Jade | 23 | Noob Saibot |
| 3 | Nightwolf | 10 | Kabal | 17 | Mileena | 24 | Rain |
| 4 | Sub-Zero (unmasked) | 11 | **empty** | 18 | Scorpion | 25 | **spare male ninja** |
| 5 | Stryker | 12 | Shang Tsung | 19 | Reptile | 26 | Motaro |
| 6 | Sindel | 13 | Liu Kang | 20 | Ermac | 27 | Shao Kahn |

Status of the roster: **verified** (C3: own renders, name table, kode messages).
- ID 11 is empty in every table; MK3's ID 11 is Sheeva (**verified**, C6).
- ID 25 is a male ninja with Scorpion's palettes and VS art, no name and no grid cell (**verified**, C7).
- ID 11 is not 100% empty: `$83:F29D`[11] = `$83:FC9E`, a leftover routine (**verified**, C-U3).

| RAM (`$7E`) | meaning | status |
|---|---|---|
| `$52C8,X` | fighter ID of player object (X=0 P1, 2 P2), copied from `$36D0`/`$3894` at `$88:93C0` | verified |
| `$52F8,X` | current frame ID (stored by `$88:8798`/`$88:87A2`) | verified (C-U2 path) |
| `$36D0` / `$3894` | P1 / P2 selected fighter | verified |
| `$3A50` / `$3A52` | P1 / P2 select-cursor cell | verified (C5) |
| `$36CA` / `$388E` | P1 / P2 object offsets (0 / 2) | verified (C9) |
| `$5538,X` | object flags: bit `$40` = alternate palette | verified (C9) |
| `$5538,X` bit `$20` | set at `$85:C656` when the SHADOW FIGHTING flag `$3C22` is non-zero | open (single: `plan/dis_flagreaders.txt`; meaning LIKELY) |
| `$3BEE`, `$F5A6` | alternate-palette rule inputs; `$3BEE` incremented by kodes 6/37 | verified use; meaning open (LIKELY) |

### 1.3 Per-fighter tables (index = fighter ID)

| table | entries × size | contents | reader | status |
|---|---|---|---|---|
| `$88:95C3` | 28 × 4 (ptr24 + pad) | common animation table | `$88:95A0` | verified\* (C-U1: the umk3-map had the readers swapped) |
| `$88:9633` | 28 × 4 | second animation table = first + `$98` (76 words per fighter); Kahn has both equal | `$88:9576` | verified\* (C-U1) |
| `$88:9D23` | 28 × 1 | primary palette ID | `$88:9874` path | verified (C9, C10) |
| `$88:9D3F` | 28 × 1 | alternate (mirror-match) palette ID | `$88:9874` path | verified (C9, C10) |
| `$83:E544` | words, bank `$83` | name strings ("-SONYA" …); entries 11 and 25 null; 21 shares 4's string, 22 shares 14's | `$83:E363` | verified (C3) |
| `$83:F29D` | 2 B | per-fighter jump table (`LDA $83F29D,X` / `BEQ` / `JMP ($F29D,X)` at `$83:F2E7`) | `$83:F2E7` | verified (C-U3) |
| `$86:EAEC` / `$86:EB24` | 28 words each | sprite-set header bank / address (section 1.5) | `$88:A483` / `$88:A489` | verified (C8) |
| `$83:EE92` | 26 × 2 | VS tile count | `$83:E808` | verified\* (C16) |
| `$83:EEC6` / `$83:EEFA` / `$83:EF2E` / `$83:EF62` | 26 × 2 | VS bank / tile stream / map stream / 64-colour palette | `$83:E730`, `$83:E808` | verified\* (C16) |
| `$83:EFE6` | 26 × 2 | VS mirror-match palette offset | – | verified\* (C16) |
| `$88:9E19` | 1 B, IDs 0-14 only | palette IDs used by `$82:9D59` for IDs < 15 (IDs ≥ 15 use `$9D23`/`$9D3F`) | `$82:9D59` | verified (C9 extra) |
| `$82:9E72` | 4 B | x/y offsets used by `$82:9D85` | – | open (single) |
| `$88:9D5B`, `$88:9D77`, `$88:9D93`, `$88:9DAF`, `$88:9DC9` | 1 B | further palette IDs, use unknown | – | open (single) |
| `$85:AEBA` / `$88:9DE5` | 2 B | babality frame ID / its palette | – | open (LIKELY) |
| `$88:9E28`, `$80:986C`, `$84:D11B`, `$86:FDA1`, `$87:E73A`, `$82:A5A6`, `$82:C071`, `$81:C1EF`, `$86:FC28`, `$88:96C0`, `$88:9955`, `$88:9729`, `$88:9799`, `$80:F7E4`, `$81:AB7D`, `$80:D1F7`, `$87:E436` | various | meaning unknown | (see umk3-map 4.3) | open (single; meanings ?) |
| `$81:B104`, `$81:B190` | 2 B | `$FFFF` for Noob, Rain, id25 and bosses | – | open (LIKELY "feature absent") |
| `$86:8E15` | 2 B jump table | Smoke and Human Smoke → `$8E4D`, Motaro → `$8E9A` | – | open (single) |

Fighter-ID compare sites, heuristic list of 42 (**open (LIKELY)**; `plan/idchecks.py` →
`out/plan/idchecks.txt`). Most relevant to new IDs:

| site | test | meaning |
|---|---|---|
| `$85:9ADE`, `$85:9C5E`, `$85:9F99`, `$85:E6D7`, `$88:AB0B` | `CMP #$001A ; BCS` | ID ≥ 26 = boss |
| `$80:9945` | `CMP #$000F ; BMI` | ID < 15 |
| `$85:99D2` | `CMP #$001E ; BMI` on `$36D0` | ? |
| several | `CMP #$1A` / `#$1B` with BEQ/BNE | Motaro / Kahn special cases |
| `$80:9004`, `$80:9047`, `$82:91A2` | `CMP #$07` / `#$08` / `#$0E` | robot checks |

Tables are only known as far as the trace reached. **A complete inventory is open (?)**.

### 1.4 Palettes

| item | value | status |
|---|---|---|
| Palette table | `$88:9984`: 309 × ptr24 to 16-colour BGR555 palettes; it ends exactly at `$88:9D23` (no room to grow in place). Banks used: `$88`, `$CA`-`$CD`, `$D5`, `$FD`-`$FF` | verified (C11) |
| Loader | `$85:CD8B` (via `$85:CD14`; `$88:9842`). Input: `$0A` = palette ID, X = slot byte offset. Copies colours 1-15 (not 0) via `$85:CC74` to `$C1A8 + 16 × X` | verified\* (C11 wording) |
| Long references | only `$85:CDA2` and `$85:CDA8` | verified (C11) |
| Male-ninja palette IDs | primary/alt: Scorpion `$70`/`$82`, Reptile `$76`/`$87`, Ermac `$71`/`$83`, Classic Sub-Zero `$72`/`$84`, Human Smoke `$73`/`$85`, Noob `$74`/`$88`, Rain `$75`/`$86`, id25 `$70`/`$82`; Motaro `$94`, Kahn `$97`. Alternates `$82`-`$88` stored at `$88:C42D`-`$88:C4ED` | verified (C10) |
| Palette choice | `$88:9874`: `JSL $88:98BE`. Carry set → primary (`$5538` bit `$40` cleared); clear → alternate (bit set). `$88:98BE`: if `$3BEE` ≠ 0 or `$F5A6` = 1, object `$2A` = 0 gets primary; otherwise mirror match → P2 gets alternate. Shang Tsung morph rule at `$88:991C` | verified (C9) |

### 1.5 Sprite format

| item | value | status |
|---|---|---|
| Frame ID | `(set << 9) \| frame`, frame 1-based. `$88:A471`: `XBA ; AND #$00FE` → set × 2 | verified (C12) |
| Set tables | `$86:EAEC` (bank) / `$86:EB24` (address), 28 sets. Sets 0-14 = fighters 0-14; 11 null; 7, 8 and 14 share header `$86:C9AB`. 15 = Motaro `$88:C017`; 16 = Kahn `$88:BB87`; 17 `$80:8F7C`; 18-25 = `$86:EBBC`-`$86:EC2C` (effects/UI, not catalogued); 26 = female ninjas `$85:CE30`; 27 = male ninjas `$85:8000` | verified (C8, C12); set 17-25 contents open (?) |
| Set header (16 B) | +0 word / +7 bank = bank table (1 byte per 64 frames); +2 word / +4 bank = tile directory; +5 word / +7 bank = frame-pointer table (word per frame); +8 bank / +E word = 4-byte-per-frame box table (`$FFFF` → default `$86:EC3C`; reader `$88:A6A6`, adds a flip-aware X offset from `$2DE4,X`); +9 word written at `$88:A4BA`, never read (LIKELY unused); +B bank / +C word = 32-byte delta block | verified (C12, T2-2, T2-4); +9 open (LIKELY) |
| Frame count | `(banktab - frametab) / 2`, because the bank table directly follows the frame table (set 0: 255 frames, set 27: 380) | verified (C12 extra) |
| Frame lookup | `$88:A5A8`: `f0 = (id & $1FF) - 1`; bank = byte `[banktab + (f0 >> 6)]`; addr = word `[frametab + 2 × f0]` | verified (C12) |
| Frame bytes | parsed by `$83:8000`. Byte N = piece count; byte B = leading 16×16 pieces. Per piece, a control byte: high nibble k → `x += delta[1+k]`, k = 0 → explicit x byte follows; low nibble likewise for y with `delta[16+k]`; start (`delta[0]`, `delta[1]`), signed bytes. 16×16 piece: 4 tile refs TL/TR/BL/BR (VRAM +0/+`$20`/+`$200`/+`$220`); 8×8 piece: 1 ref | verified (C12) |
| Tile ref | bits 0-1 flip (H, V). **A 16×16 piece takes its flip from its first ref only.** Bits 2-7 = directory byte offset (entry × 4); bits 8-15 = tile number | verified (C12) |
| Directory entry | word address, byte bank, byte flags. Bit 7 = mask-compressed; bit 6 = 2bpp/16-byte tiles; bits 0-5 = record size | verified (C12, T2-2) |
| Codec | `$83:8362`, `$83:8474`, `$83:850F` (2-mask variant); mask routines in the `$83:85AA` table. Raw: 32 B per 4bpp tile, 16 B per 2bpp tile. Compressed block: byte T, then record n at `base + 1 + n × size`; records n ≥ T start with a fill byte; then 4 (or 2) mask bytes MSB-first (1 = literal, 0 = fill). The fill byte is read via the Mode-7 multiply result `$2135` | verified (C12, T2-3) |
| Tile fetch | DB-relative: `PHA`/`PLB` then `LDA $0000,Y`. Raw path `$83:83F5`/`$8401`/`$8402`; 16-byte path `$83:8382`/`$838F`/`$8390`; compressed path `$83:8491`/`$84C5`/`$84C6`. New tile data must not be addressed through `$00`-`$3F` | verified (T4-3) |
| Runtime buffers | tiles assembled from `$7E:80A8` (slot offsets `$86:E322`), DMA'd by `$88:B920`/`$88:B990` to VRAM per `$86:E33A` | open (single/LIKELY) |
| Observed per-frame maxima | 133 tiles (set 22), 62 pieces (set 15); fighter sets max 108 tiles (set 10) | verified (T2-8, values); hard engine limit open (?) |

Decoders that agree with each other: `scripts/umk3/sprite.py`, `scripts/verify-umk3/spr.py` and
`scripts/compat/spr.py` (0 mismatches over 761 UMK3 and 595 MK2 frames).

### 1.6 Animation scripts

| item | value | status |
|---|---|---|
| Interpreter | `$88:87DD`. A word below `$FFEA` is a frame ID; otherwise `CMP #$FFEA` then `JMP ($89E2,X)` with X = `(word EOR $FFFF) × 2`. 22 entries `$FFFF`..`$FFEA` (`$FFE9` is garbage) | verified (T2-6) |
| `$FFFF` addr | jump (`$88:883C`), same bank | verified |
| `$FFF8` | byte fighter ID + word target: per-fighter branch (`$88:8804`). **Not word-aligned**: a naive word scan misreads the scripts | verified |
| `$FFFE`..`$FFF7` | same argument layouts as MK2: none; X; X,Y (flip-aware offsets); frame + SEC; ptr24 → JML; sound word; fid + target; none | verified (T2-6) |
| `$FFF6`..`$FFEA` | UMK3-only commands | open (?) |
| Shared tables | male ninjas 18-25 `$85:8010`; female 15-17 `$85:CE40`; robots `$86:CA27`; Motaro `$88:C027`; Kahn `$88:BB97` | verified (C8) |
| Animation numbering | 76 slots per fighter. Indices 0-52 agree with MK3 for the 13 shared fighters; 53+ differ | open (single: `plan/sheeva_check.txt`, numbers measured) |

### 1.7 General LZ decompressor

| item | value | status |
|---|---|---|
| Routine | `$88:AD30` (normal) / `$88:AE7D` (mode 2). Header: word output size, byte mode. Output is written **backwards** | verified (C13) |
| Commands | `c ≥ $80`: back-reference, len `((c>>3)&$F)+3`, offset `((c&7)<<8)\|next`, word-wise, highest word first. `$40`-`$7F`: `(c&$3F)+1` literals. `$20`-`$3F`: copy 1 byte (mode 2: descending run of `(c&$1F)+3`). `$01`-`$1F`: fill `c+2` bytes. `$00`: end | verified (C13) |
| Mode 2 | stride-2: odd bytes first, then even; back-references wrap | verified (C13) |
| Coverage | 83 of 85 streams named by the VS and layer tables decode exactly. The 2 failures are record 7's maps `$F0:A95D`/`$F0:AB2B` | verified |
| Traced callers | `$83:C067`, `$83:C081`, `$84:943E`, `$84:98B0` (wrapper: dst `$76`/`$78`, src `$7A`/`$7C`), `$84:A4B8`, `$86:DD7F`, `$87:EEE4`; more untraced | open (single) |
| Equivalence | identical to MK2 `$85:B9FC` apart from DP/scratch operands | verified (T2-1) |

### 1.8 Select screen (screen record 13; `$3A7E = 13` set at `$86:9F57`)

| item | value | status |
|---|---|---|
| Grid `$86:A207` | 24 bytes, cell → ID; `$FF` = hidden cell 10. Read at `$86:A1F7` inside `$86:A1F6`, which writes `$36D0`/`$3894` | verified (C14) |
| Row 0 (cells 0-6) | Rain, Reptile, Stryker, Jax, Nightwolf, Jade, Noob | verified (C14) |
| Row 1 (cells 7-13) | Sonya, Kano, Mileena, [hidden], Classic Sub-Zero, Sub-Zero, Kung Lao | verified (C14) |
| Row 2 (cells 14-18) | Sektor, Kitana, Ermac, Scorpion, Cyrax | verified (C14) |
| Row 3 (cells 19-23) | Kabal, Sindel, Smoke, Liu Kang, Shang Tsung | verified (C14) |
| Direction tables | `$86:A6C6` up, `$86:A6DE` down, `$86:A6F6` left, `$86:A70E` right (24 B each). Joypad bits `$0800`/`$0400`/`$0200`/`$0100` at `$86:A387`-`$86:A3EE` | verified (C14) |
| Blocked lists | `$86:A677` (7 B per direction, padded `$1B`), checked by `$86:A661`. Up: 0-6; down: 7, 19-23, 13; left: 0, 7, 14, 19; right: 6, 13, 18, 23 | verified (C14) |
| Movement | `$86:A726`. Cell 10 is entered only if `$1C57 == 1`, `$F5A6 == 0` and the other cursor is not on 10; otherwise it is skipped. Cursor steps x ±50, y ±64 | verified (C5, C14) |
| Cursor start | P1 cell 0 (Rain), P2 cell 6 (Noob) | verified (C5) |
| Confirm | `$86:A3FA` → `$86:A1F6`, no ID filter | verified (C5) |
| Hidden cell | `$84:A2A3`-`$84:A42B`. Opens only when `$36C6` and `$388A` are both non-zero. `$1C59 = $1B` (Kahn) if `$3BAE`, `$1A` (Motaro) if `$3BB0`; alternates if both. `$1C57`: 0 closed, 1 open, 2 closing. `$86:A203` returns `$1C59` for grid `$FF`. Portraits at select-map rows 28-33 (Motaro columns 0-3, Kahn 4-7), copied 4×6 via `$84:A750` | verified (C15) |
| Boss unlock flags | `$3BAE`/`$3BB0`: only traced stores are `STZ` at `$80:86B1`/`$80:86B4`, inside init `$80:8653` (called from `$80:8469`). Menu variable list `$83:D742`-`$83:D76E` | verified (stores); menu link open (LIKELY) |
| Random select | `$86:A91F`/`$86:A953` → `$86:A987` | open (single) |
| BG layer 0 | descriptor `$84:8299`, type 1, 8bpp (descriptor +1 = `$FF`). Tiles `$C3:0000` (LZ mode 2, `$9C80` B = 626 tiles). Map `$F9:FACF` (32 wide; portraits 4×6 tiles). Palette block `$FF:7BC2`: 96 colours loaded at CGRAM 48; `$84:9703` adds +48 to non-zero pixels (A = descriptor +2) | verified (C16, select part) |
| BG layer 1 | descriptor `$84:82C6`: tiles `$F2:BAAA`, map `$F9:FCB9`, palette `$FF:7B5E` | open (single; streams decode) |

### 1.9 VS screen portraits (IDs 0-25; none for 26/27)

| item | value | status |
|---|---|---|
| Tables | see 1.3 (`$83:EE92`/`$EEC6`/`$EEFA`/`$EF2E`/`$EF62`/`$EFE6`, 26 entries each, `$34` B apart) | verified\* |
| Loaders | tiles by `$83:E808` (count from `$83:EE92`); map and palette by `$83:E730`; map window 16×22 copied by `$83:E87C` | verified\* (C16) |
| Format | 6bpp at 48 B per tile (`$83:E97E` pads to 8bpp). **Tile index = map value & `$3FF`** (no −1; tile 0 blank). `out/umk3/vs_portraits.png` is off by one; use `out/verify-umk3/vs_portraits_shift0.png` | verified\* (C16) |
| Ninjas | Rain `$D4:86B5`, Noob `$D4:85F5`; ID 25 entries are byte-identical to Scorpion's (bank `$D4`, tiles `$63A2`, map `$838F`, palette `$8475`) | verified (C4, C7) |

### 1.10 Screen and stage records

| item | value | status |
|---|---|---|
| Record table | `$84:8A22`: 29 × `$22` bytes, index = `$3A7E` (multiplied via `$4202`/`$4203` at `$84:8FC8`). Highest immediate stored to `$3A7E` is `$1C` (`$83:D838`) | verified (C17) |
| Record fields | +0 BG mode; +2 TM; +8..+F = 4 layer-descriptor **words in bank `$84`** (`$FFFF` none, `$8000` special; loop `$84:9081`); +`$10`..+`$20` ground and other parameters (not decoded) | verified (C17); +3..+7 and +`$10` meanings open (single/?) |
| Type-0 descriptor | loader `$84:913E`: palette +17/+18, tiles +1A/+1B (traced to `$84:9425`), map +1F/+20, second map +28 | tiles offset verified (T1-4); rest open (single) |
| Type-1 descriptor | loader `$84:920C`: +1 = `$FF` → 8bpp; palette +15; tiles +18; count +1B; map +1D | verified (C16) |
| Palette block | word count, word first CGRAM index, colours (loader `$84:961C`) | verified (C16) |
| Fight-stage metatiles | `$84:9AB8`, `$84:9C87` | **open (?)**: not decoded; a plain-tilemap render is noise (PLAN P9) |
| Zone → record | `$80:84B8`: `$3A84 = 0` → record 5; `$70` → record 0 (and clears `$3A84`); other values unchanged | verified (C17) |
| Stage names | `$85:EE32` (read at `$85:E908`, `$85:EA00`), 7 entries: 0 ROOFTOP, 1 THE DESERT, 2 HADES, 3 THE KAVE, 4 THE WATERFRONT, 5 LOST, 6 THE PIT 3 | verified (C17) |
| Fight records | 0-10 and 23. Records 1-6 = names 1-6 | open (LIKELY, C18) |
| Shared layers | rec 6 and 9 share all layers; `$84:87FD` is shared by recs 6, 9 and 23; `$84:83BB` by recs 10, 17 and 20 | open (single: `plan/rec78.txt`) |
| Dead records | **rec 7**: tiles point at `$C0:0000` (Pit 3 L1 stream); maps `$F0:A95D`/`$F0:9D74`/`$F0:AB2B` do not decompress; private descriptors `$84:8946` (type 0) and `$84:89B6` (type 1). **rec 8**: all data pointers `$00:0001`; private descriptors `$84:8752`, `$84:8786` (type 0) and `$84:87B0` (type 1) | dead: verified (T1-5); descriptors open (single: `plan/rec78.txt`) |
| Kept from MK3 | UMK3 rec 0 = MK3 rec 3 (Rooftop); rec 6 = MK3 rec 9 (Pit 3). All UMK3 tiles are found in MK3; MK3 has an extra layer `$F6:0000` | verified (T1-4, from the UMK3 side) |
| Boss stages | Motaro → rec 0; Kahn → rec 6, or `$17` if `$36C0 == $15` | open (LIKELY) |
| Attract cycle | `$85:A987`: 5, 1, 2, 3, 4 | open (LIKELY) |

### 1.11 Kombat kodes

| item | value | status |
|---|---|---|
| Kode table | `$85:DFF5`: 45 × 8 B (6 icon values, 0 = wildcard, then 2 zero bytes); terminator `$FF` at `$85:E15D` | verified (C19) |
| Matcher | `$85:E1B3` (called from `$83:E6BA`) compares with `$7E:52F8 + $18 + 2k`; index + 1 → `$3C2E`/`$3C30` | verified (C19) |
| Dispatch | `$85:DF1F`: `$3A90 == 1` → `JMP ($DF3D,X)`, else `JMP ($DF99,X)`; the tables differ at kodes 10, 29, 36 (→ `$E209`, no-op) | verified (C19) |
| Battle kodes | 11 Motaro (`$1A`, message `$85:EB7F`), 12 Kahn (`$1B`, `$85:EB58`), 13 Noob (`$17`, `$85:EB2F`), 20 Smoke (`$0E`, `$85:EB0C`); via `$85:E721`-`$85:E730` | verified (C19) |
| Zone kodes | 38-43 → `$3A84` = 6, 4, 2, 3, 1, `$70` (`$85:E237`-`$85:E255`) | verified (C19) |
| Icon value | = arcade digit + 1 (9 arcade kodes match) | open (LIKELY, C20) |
| Banner frames | `$80:C794`: one word per kode = set-21 frame ID of the kode banner (`$2A17`-`$2A29`, `$FFFF` none); read at `$80:C733` | verified\* (C-U2; the umk3-map called these sound IDs) |
| Message table | `$85:EA3E`: 6-B entries (pointer to RAM variable, compare value, message pointer in bank `$85`), 22 entries, read at `$85:E819`/`$85:E8AB` | open (single: `plan/dis_85E805.txt`, `plan/kodemsgs.txt`) |
| Flag pairs | the kode flags are word pairs cleared by the `$80:8653` loop (X = 2, 0); the handlers `INC` the base word. Readers found by raw search: `$85:C656` (SHADOW `$3C22` → `$5538,X` bit `$20`); `$84:E829`-`$84:E84A` (damage in DP `$32`: halved if `$3BD6`, doubled if `$3BDA`, quartered if `$3C16`, minimum 1); one-button-fatalities flag `$3BE2` at `$85:99F7`/`$88:ABA0`; BACKGROUND BLAST `$3C1E` at `$81:8F6B`. HYPER `$3BF2`: no reader found | open (single: `plan/flagraw2.txt`, `plan/dis_flagreaders.txt`; meanings LIKELY) |
| Other text | menus and cheats `$83:D000`-`$83:D720` (ENABLE MOTARO `$83:D515`, ENABLE SHAO KAHN `$83:D523`); credits `$83:BBD9`-`$83:BD74`; kode messages `$85:EAC4`+ | open (single) |

### 1.12 Free space and ExHiROM facts

| item | value | status |
|---|---|---|
| Largest free run | 9,106 B of `$FF` at `$FF:DC6E`-`$FF:FFFF` (file `0x3FDC6E`) | verified (C21) |
| Code-bank `$FF` runs | `$C0:FF1F` 103, `$C1:FF72` 98, `$C2:FF0B` 102, `$C3:FF8E` 100, `$C4:FF83` 87, `$C5:FEE1` 92, `$C6:FF79` 100, `$C7:FF58` 90 bytes | verified (C21) |
| **Bank tails are not free** | each `$FF` run is followed by a compressed tile group up to the bank end | verified (C-U5) |
| Maybe free | `$C8:CAE6` (100 × `$FF`). The zero run at `$C8:C22B` is not free (it overlaps palette `$82`) | open (?) |
| Low-bank tile groups | 9 frame-referenced directory entries have bank bytes `$00`-`$07` (see table below). Patch the bank byte at each file offset to `$C0`-`$C7` before ExHiROM | verified (T4-2, C22) |
| No header/checksum reads | none in traced code | verified (C22 code side; T4-1 unverifiable as a whole) |
| No ROM reads via `$00`-`$7D`; no bank masking | in traced code | open (T4-1 unverifiable; spot checks agree) |
| ExHiROM recipe | `PLAN.md` section 4 | open (LIKELY until run) |

| set | dir entry | group address | bank-byte file offset |
|---|---|---|---|
| 0 (Kano) | +`$34` | `$05:FF3D` | `0x3FB3F5` |
| 0 (Kano) | +`$6C` | `$04:FFDA` | `0x3FB42D` |
| 13 (Liu Kang, incl. stance) | +`$00` | `$07:FFFB` | `0x3FB832` |
| 17 | +`$44` | `$00:FF86` | `0x3FC68F` |
| 18 | +`$44` | `$02:FF71` | `0x3FC52F` |
| 20 | +`$24` | `$01:FFD4` | `0x3FCAD3` |
| 21 | +`$38` | `$03:FFF2` | `0x3FD4ED` |
| 24 | +`$68` | `$06:FFDD` | `0x3FC727` |
| 25 | +`$2C` | `$07:FFB2` | `0x3FC841` |

### 1.13 UMK3 unknowns (summary; details and cheapest checks in `PLAN.md` section 7)

All **open (?)**:
- special-move dispatch, move routines, attack boxes, combos, finisher framework, AI;
- sound driver and sample directory;
- fight-stage metatile format and per-stage code;
- win banner and names, ending and bio text, ladder data;
- HUD and run-meter rendering;
- Human Smoke selection path;
- meanings of animation slots 53-75 and of commands `$FFF6`-`$FFEA`;
- contents of sets 17-25;
- a complete per-fighter table inventory;
- VRAM and CPU budgets per player.

---

## 2. MK3 (donor for Sheeva, stages, animalities)

| item | value | status |
|---|---|---|
| Fighter IDs | 0-14 as UMK3 with **11 = Sheeva**; 15 Motaro, 16 Shao Kahn, 17 Noob Saibot (= set 0, Kano, with palette 3) | 0-14 verified (C6 cross-check); 15-17 open (single, compat render) |
| Set tables | `$85:ABAA` (bank) / `$85:ABDE` (address), 26 sets; read from `$86:E9AC`/`$86:E9B9`/`$86:E9BF` | verified (C6, T1-2) |
| Sprite format | same as UMK3, including the tile codec (one decoder renders both) | verified (C6, C12) |
| Animation tables | `$86:DC53` (first) / `$86:DC9B` (second), readers `$86:DC13`/`$86:DC34`. The second table = first + `$82` (65 words) for every fighter except 16 (+0) | tables verified (C6); `+$82` open (single: `plan/sheeva_check.txt`) |
| Palette table | `$86:F0FC` (read at `$83:F7E9`), 230 entries; primary IDs `$86:F3AE` (read at `$86:DE70`); alternate `$86:F3C0` | table and primary verified (C6); 230 entries and alternate open (single) |
| VS tables | bank `$80:F414`, tiles `$80:F432` (15 entries); map `$80:F450`; palette `$80:F46E` | bank/tiles verified (T1-2); map/palette open (single) |
| Stage/screen records | `$82:B888`, 26 records, same type-0/1 descriptor layout as UMK3 | verified (T1-4 parse) |
| LZ decompressor | head at `$86:E41A`, same routine as UMK3 | open (LIKELY, mk2:C20) |
| **Sheeva** | set 11 header `$86:9B3F`, 204 frames, 25,345 frame bytes, 7,413 distinct tiles (28 also in UMK3), about 210 KB footprint; renders four-armed. Tile-directory banks all ≥ `$C9` | verified (T1-2); banks open (single: `plan/sheeva_check.txt`) |
| Sheeva palettes | `$4A` / `$4B` (via `$86:F3AE`/`$86:F3C0`[11]) | open (single) |
| Sheeva VS portrait | tiles `$C9:0000` (clean 10,817-B LZ stream, 0 bytes in UMK3); map `$C9:2A41`; palette `$C9:2B1C` | tiles verified (T1-2); map/palette open (single) |
| Sheeva code | not located (inside the 172 KB of MK3-only code-bank bytes) | open (?) |
| Set 21 | frames about 1-115 animal sprites (absent in UMK3); 139-157 kode banners; 158-166 actor credits | verified\* (T1-3) |
| Set 19 | ANIMALITY (frames 1-11), **all** MK3 stage-name banners (45-56; UMK3 has none), MK3 FIGHT!/FATALITY variants | verified\* (T1-3) |
| Set 18 | MERCY banner frames 206-212 absent from UMK3; the static frame 213 is present | verified\* (T1-3) |
| Set 22 | 21 frames partly differ (2-30% of their tiles) from UMK3. They are variants, not absent frames | verified\* (T1-3) |

MK3 stage and screen records (0-1.4% tile overlap with UMK3 unless noted). Tile overlap is
**verified** (T1-4). The record → name mapping is **open (single)**.

| MK3 rec | stage / screen | in UMK3? |
|---|---|---|
| 0 | The Subway | no |
| 1 | The Street | no |
| 2 | The Bank | no (only the skyline L0 `$C5:0000` is shared) |
| 3 | Rooftop | yes, UMK3 rec 0 |
| 4 | The Balcony | no |
| 5 | The Bridge | no |
| 6 | Soul Chamber | no |
| 7 | Shao Kahn's Tower | no |
| 8 | The Temple | no |
| 9 | The Pit 3 | yes, UMK3 rec 6 |
| 10 | The Vortex | L0 = Pit 3 tiles (kept); L1 sky `$C6:0000` absent |
| 13 | MK3 select screen | no |
| 15 | MK3 logo screen | no |
| 12, 14/16/19 | unidentified screens (`$D5:1678`, `$C8:3FFF`) | no; purpose open (?) |

Other MK3 notes:
- MK3-only BRR-like data: about 55-66 KB, mostly in `$CF:B800`-`$D4:4FFF`. **open (LIKELY**, T1-6).
- Code: 67.6% of traced UMK3 instructions have an MK3 skeleton match. **open (LIKELY**; T1-7
  unverifiable).
- Object-RAM equality between MK3 and UMK3 is not checked. **open (?)**.

---

## 3. MK2 (donor for Baraka, Johnny Cage, Raiden, Kintaro, MK2 Jax/Kung Lao, stages)

### 3.1 Basics and RAM

| item | value | status |
|---|---|---|
| Vectors | reset `$80:8000`, NMI `$80:86D9`, IRQ `$80:86B1` | open (single) |
| Fighter IDs | 0 Kung Lao, 1 Liu Kang, 2 Johnny Cage, 3 Baraka, 4 Kitana, 5 Mileena, 6 Shang Tsung, 7 Raiden, 8 Sub-Zero, 9 Reptile, 10 Scorpion, 11 Jax, 12 Kintaro, 13 Shao Kahn, 14 Smoke, 15 Noob Saibot, 16 Jade. "X WINS" table `$83:D7B8` (17 entries, read at `$83:D126`) | verified (mk2:C1) |
| `$2EF8` / `$30A6` | P1 / P2 fighter ID | verified (mk2:C2) |
| `$4C10,X` | object fighter ID (stored at `$85:C671`; X = 0 P1, 2 P2) | verified (mk2:C2) |
| `$4C3C,X` | frame word `set<<9 \| frame` | verified (mk2:C3) |
| `$3270` | stage ID | verified (mk2:C16) |
| `$2ED8` | shadow enable: set to 1 by `$83:EE57` unless stage 6; cleared by `STZ` at `$80:BB54`, `$81:F01D`, `$82:A11F`, `$83:ABF3`, `$85:A64B` | verified\* (mk2:C11) |
| `$2EE4` / `$327E` | game mode / fight phase (3 = finishing window) | open (LIKELY) |
| Object RAM layout | 11 slots, word arrays `$16` apart (header copies to `$2C96`…`$2D46`; loop `LDX #$16` at `$85:C017`). UMK3: 12 slots, `$18` apart (`$3474`…`$3534`; `LDX #$18` at `$88:A523`) | verified (T2-5) |

### 3.2 Sprites

| item | value | status |
|---|---|---|
| Set tables | `$84:CDCC` (bank words) / `$84:CDEE` (low words), 17 sets, via `$85:BF66` | verified (mk2:C3) |
| Set → content | 0 Kung Lao, 1 Liu Kang, 2 Cage, 3 Baraka, 4 Kitana/Mileena/Jade, 5 Shang, 6 Raiden, 7 male ninjas, 8 Jax, 9 Kintaro, 10 Kahn, 11-16 effects/UI. Fighter → set: `[0,1,2,3,4,4,5,6,7,7,7,8,9,10,7,7,4]` | verified (mk2:C3) |
| Headers and frame counts | Cage `$85:8000` (226 frames), Baraka `$85:87B6` (214), Raiden `$85:8F48` (189), Kintaro `$82:FE13` (67), Kung Lao `$85:96BA` (211), Jax `$84:E158` (229); others in mk2-map 4 | open (single; common anim table = header + `$10` verified) |
| Header layout | same as UMK3. +0/+7 frame-bank table; +2 tile-group table ptr24; +5 frame-pointer table ptr24; +8 bank for shadow and box tables; +9 shadow table (2 B per frame, `$FFFF` none); +B/+C 32-B position table; +E box table (4 B per frame, `$FFFF` → `$84:CFC6`) | verified (mk2:C4, T2-2) |
| Frame format | same as UMK3 (nibble X/Y deltas from `pos[1+n]` / `pos[16+n]`, start `pos[0]`/`pos[1]`; 4 words per 16×16 piece, flip from the first only). Builder `$81:8000`-`$81:81F7` | verified (mk2:C5) |
| Tile codec | `$81:834B`. Group entry = ptr24 + flag. Flag `$20` = raw 32 B per tile; flag `$80\|s` = records of s bytes at `base + idx × s` (hardware multiply), 4 mask bytes MSB-first + literals, fill 0; s = 5..31. 62,767 compressed refs (all `4 + popcount == s`), 31,359 raw. Handlers `$81:8451`-`$81:A650`, jump table `$81:A451` | verified (mk2:C6) |
| **Conversion to UMK3** | per group: prepend `T = max_index + 1`; if index 255 is used, `T = 255` plus a `$00` fill byte before record 255; re-point the directory entry. Raw groups unchanged. 0 mismatches over 45,347 distinct tiles in all 17 sets | verified (T2-3) |
| Box table | same reader logic as UMK3 (`$85:C165` vs `$88:A6A6`). Baraka frame `$64` box (−16, 19, −51, 49). "Body/collision" meaning LIKELY | verified (format, mk2:C10, T2-4) |
| Shadow table | precedes the box table (gap = 2 × frames); drawn by `$81:A71A` when `$2ED8` ≠ 0 | open (LIKELY, mk2:C11) |
| Attack/hit boxes | not found as frame data | open (?) |

### 3.3 Animation

| item | value | status |
|---|---|---|
| Tables | common `$85:C49E` (read at `$85:C47D`), specific `$85:C4E2` (read at `$85:C45C`), index `$4C10,X` × 4. Common has 66 entries for the 12 playable fighters, 24 for Kintaro (`$82:FE23`), 26 for Kahn (`$85:D9F7`). Counts come from table adjacency; entry 64 is null for playable fighters | verified (mk2:C8) |
| Interpreter | `$83:F28E`, dispatch `$83:F32C`. `0000` = end; words < `$FFF6` are frames (`$83:EF0C`). Commands `FFFF`..`FFF7` are valid; `FFF6` slot is garbage. `FFF8` = byte fid + target (`$84:A05C`); `FFF9` = sound word (`$85:E0C5`, LIKELY) | verified (mk2:C8, T2-6) |
| Timing | supplied by code: A = delay<<8 \| anim → `$83:F347` (common) / `$83:F356` (specific) → `$83:F39C`, sleeping via `$85:DDF9`. `FFFB` frames get no sleep | verified (mk2:C9) |
| Remap to UMK3 | 66 → 76 slots; only about the first 5-6 indices agree | open (LIKELY, T2-7) |

### 3.4 Palettes

| item | value | status |
|---|---|---|
| Palette table | `$85:D33D`: 174 × ptr24 (ends at `$85:D547`). Entries 100/101 point through bank `$05` (`$05:FFBF`, `$05:FFDF`) | verified (mk2:C12) |
| Loader | `$83:F8CC` copies **30 bytes (colours 1-15)**, like UMK3 | verified\* (C-M1) |
| Per-fighter IDs | main `$85:D547`; alternate `$85:D558` (P2 in a mirror match, when `$2EE4` ≠ 4) | verified (mk2:C12) |
| Other palette tables | effect `$85:D569` / `$85:D57A`; Shang morph `$85:D58B`; frozen `$85:D5B7` (read at `$85:C784`; all cyan) | D5B7 verified (LIKELY meaning, mk2:C13); others open (single) |
| Donor palette IDs | main/alt: Cage `$00`/`$01`, Baraka `$39`/`$3A`, Raiden `$32`/`$33`, Kintaro `$40`/`$40`, Jax `$0C`/`$0B`, Kung Lao `$11`/`$12`. Blocks in bank `$EF` (Baraka `$EF:CAD4`, Cage `$EF:88BE`, Raiden `$EF:CBB4`, Kintaro `$EF:F32B`) | open (single) |
| Ninja palettes | `$17` Sub-Zero, `$18` Reptile, `$19` Scorpion, `$1A`-`$1C` alternates, `$1D` frozen, `$1E` Noob (black), `$1F` Smoke (grey), `$20`-`$26` variants | verified (LIKELY by nature, mk2:C13) |

### 3.5 Special moves and move code (behaviour reference only; the code cannot run in UMK3)

| item | value | status |
|---|---|---|
| Dispatch | `$81:A943`: `[$0A]` = per-event table in bank `$81`, Y = `$4C10,X` × 2, `JML [$1900]`. **8 tables**: `$81:A989`, `$A9A1`, `$A9B9`, `$AA40`, `$AA58`, `$AA70`, `$AA88`, `$AAA0` (12 entries; `$81:AACD` = RTL = none) | verified\* (mk2:C19) |
| Check pattern | `$81:C8CB` (X = window, A = sequence in bank `$81`) → on success `$81:C83F` (bank-81 move) / `$81:C852` (bank-85 move) | open (single) |
| Baraka | input checks `$81:B094` (AA40), `$81:B065` (AA58); `$81:B054` (AA88) → `$81:C78F`, LIKELY a stage-fatality check | verified\* (mk2:C19) |
| Johnny Cage | A989 `$B0C3`, AA40 `$B0F1`, AA58 `$B2AA`, AA70 `$B115`, AA88 `$B0E0`, AAA0 `$B38D` | verified\* (mk2:C19) |
| Raiden | A989 `$AA0F`, A9B9 `$AA2D`, AA40 `$B311`, AA58 `$B2FF`, AA88 `$AB0A` | verified\* (mk2:C19) |
| Kintaro, Kahn, Smoke, Noob, Jade | outside the 12-entry tables (CPU-only) | verified (consistent, mk2:C19) |
| Move routines | `$83:DCC1` jump table (14 routines `$83:DD10`..`$83:ED27`), stubs `$81:B51C`-`$81:B55D` | open (single) |
| Effect frames per donor | Raiden uses 16 frames of set 13 directly; Cage and Baraka 2 of set 12; code-spawned projectiles not attributed | open (single / ?) |

### 3.6 Donor budgets (graphics, frames, tables, scripts, palettes; no move code, no effect sets)

Totals **verified** (mk2:C14; caveats: the header is counted twice, the shadow extent is assumed):

| donor | total | tiles | frames |
|---|---|---|---|
| Johnny Cage | 166,744 | 138,766 | 21,062 |
| Baraka | 159,366 | 131,895 | 20,472 |
| Raiden | 191,861 | 164,985 | 20,261 |
| Kintaro | 140,349 | 123,795 | 13,255 |

- Sum: 658,320 bytes.
- Converter overhead is only 1-2 bytes per compressed group (the T byte, plus a fill byte when
  index 255 is used). The "added bytes" figures in `compat/convert_test.txt` (46-90 KB per donor) are
  the re-emitted compressed groups, not overhead (single; read from `convert_test.py` line 132).
- Reference (single): Kung Lao 186,337; Jax 200,921.
- No tile group is shared between sets; decoded sprite data covers 2,003,360 B (**verified**, mk2:C15).

### 3.7 Stages

| item | value | status |
|---|---|---|
| Names | `$82:DD76` (9 entries; printed at `$82:D7B3`); `$83:AEBD` wraps at 9 | verified (mk2:C16) |
| Stage list | 0 Dead Pool, 1 Kombat Tomb, 2 Wasteland, 3 Tower, 4 Living Forest, 5 Armory, 6 Pit II, 7 Portal, 8 Kahn's Arena, 9 unnamed. Stage 9 is LIKELY Goro's Lair: two MK2 secret-fighter messages (near `$C3:DA34`, `$C3:DC44`) name "GORO'S LAIR" as the next fight's place | verified (0-8); 9 open (LIKELY) |
| Record | `$82:EDFC + $82:EF50[stage]`, 34 B, 10 records; loader `$82:F04F`. +0..+3 banks (tiles, metatiles, maps, palette); +4 tiles LZ (→ `$7F:0000`); +6 metatiles LZ; +8 192-B palette (→ `$7E:B91C`); +`$A`..+`$21` 12 map blocks of 16×16 metatile words (512 B, expanded by `$82:F1AB`, metatile = w & `$3FF`, 8 B each). Blocks 0-9 form a 5×2 layer; 10-11 a 2×1 layer | verified (mk2:C17) |
| Sizes | 13,479-32,416 B packed per stage; 239,052 total | verified (mk2:C17) |
| LZ | `$85:B9FC`. Types 0/1 copy 16-bit descending pairs; type 2 is split odd/even, and its `001` command is a decrementing run. 84 streams decode exactly | verified (mk2:C18) |
| Per-stage tables | `$80:860E`/`$8622`/`$8636`, `$82:E6BE` (scroll), `$82:E732`, `$82:EF8C` (floor-ish), `$82:EFF0`, `$82:FD66` (per-stage init jump table), `$83:A77E`.. (LIKELY music) | open (single/LIKELY) |
| Props and animations | not mapped | open (?) |

---

## 4. Cross-game equivalences (what can be reused as is)

| layer | MK2 → UMK3 | MK3 → UMK3 | status |
|---|---|---|---|
| General LZ | identical routine; streams usable as is | same routine (LIKELY) | verified (T2-1) / open (LIKELY) |
| Sprite set header, frame bytes, delta table, tile-ref layout, raw tiles | same | same | verified (T2-2, C6) |
| Compressed tile groups | add T byte (+ fill for index 255) | same codec | verified (T2-3) / verified (C6 renders) |
| Box table | same reader logic (UMK3 adds a flip offset) | – | verified (T2-4) |
| Palette format and loader (colours 1-15) | same | same | verified (C11, C-M1) |
| Animation command encoding `FFFF`..`FFF7` | same layouts; remap sets, targets, fighter IDs, sound IDs, code pointers | numbering 0-52 matches; 53+ differs | verified (T2-6) / open (single, P2) |
| Animation numbering | 66 → 76, only about 6 agree | 65 → 76 | open (LIKELY) |
| Object RAM and move code | different (11 × `$16` vs 12 × `$18`); rewrite | unknown; skeleton similarity high | verified (T2-5) / open (?) |
| Stage container | converter needed (MK2 record → type-0/1 descriptors) | same record and descriptor types | open (LIKELY) / verified (T1-4 parse) |
| MK2 data already inside UMK3 | about 37 KB: engine tables (MK2 `$C4:C7A9`-`$C4:CDCB` → UMK3 `$C6:E369`-`$C6:EAEC`), sound region `$CE:8E00`-`$CF:5000`, padding; no fighter, stage or palette asset | – | verified (T3-1) |

---

## 5. Corrections applied relative to the analyst notes

| ref | correction |
|---|---|
| C-U1 | `$88:9576` reads `$88:9633`; `$88:95A0` reads `$88:95C3` (umk3-map had them reversed) |
| C-U2 | `$80:C794` holds set-21 kode-banner frame IDs, not sound IDs |
| C-U3 | ID 11 is not fully empty: `$83:F29D`[11] = `$83:FC9E` |
| C-U5 | the bytes after the `$FF` runs at the ends of banks `$C0`-`$C7` are tile data, not free space |
| C16 | VS tile index = map value & `$3FF` (no −1); VS tiles are loaded by `$83:E808` with count `$83:EE92`; `$83:EFE6` = mirror-match palette offset |
| C22 | the ExHiROM recipe also needs the 9 low-bank tile-directory patches |
| C-M1 / mk2:C12 | MK2 palette loader copies 30 bytes (colours 1-15) |
| C-M2 | the MK2 sprite codec is the same family as UMK3's (byte insertion, not a re-encode) |
| mk2:C11 | `$83:EE57` sets `$2ED8 = 1` unless stage 6; the clears are elsewhere |
| mk2:C19 | 8 special-move event tables, not 5; Baraka's real checks are `$81:B094`/`$81:B065` |
| T1-3 | MK3 set 21 also holds kode banners and credits; set 19 holds all MK3 stage names; set 22 frames are variants, not absent |
| T1-4 | Rooftop/Pit 3 are 100% contained only from the UMK3 side (MK3 has the extra `$F6:0000` layer) |
| umk3-map side remark | `$C1A8` is CGRAM colour 128 (first OBJ palette), not colour 0 (LIKELY) |
