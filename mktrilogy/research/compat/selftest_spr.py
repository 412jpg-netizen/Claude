"""Self-test: spr.py must give byte-identical tiles/pieces to the per-game decoders written by the
UMK3 analyst (scripts/umk3/sprite.py) and the MK2 analyst (scripts/mk2/mk2gfx.py)."""
import sys
sys.path.insert(0, '/home/claude/work/scripts/compat')
import spr
sys.path.insert(0, '/home/claude/work/scripts/umk3')
import sprite as US
sys.path.insert(0, '/home/claude/work/scripts/mk2')
import mk2gfx as MG
bad = n = 0
for s in range(28):
    H = US.set_header(s)
    if H is None: continue
    S = spr.Set('umk3', s)
    nf = S.nframes() or 0
    for f in range(1, min(nf, 400) + 1, 7):
        try:
            fp, pcs = US.frame_pieces(H, f)
        except Exception:
            continue
        mp, a, _ = S.pieces(f)
        n += 1
        if [(x, y, sz, r) for x, y, sz, r in pcs] != mp:
            bad += 1; continue
        for (_, _, _, refs) in pcs:
            for r in refs:
                if US.tile_data(H, r) != S.tile(r):
                    bad += 1
print('umk3 frames compared', n, 'mismatches', bad)
bad = n = 0
for s in range(17):
    hd = MG.header(s); S = spr.Set('mk2', s)
    for f in range(1, MG.nframes(hd) + 1, 5):
        fr = MG.decode_frame(hd, f); mp, a, _ = S.pieces(f); n += 1
        if [(p['x'], p['y'], p['size'], p['words']) for p in fr['pieces']] != mp:
            bad += 1; continue
        for p in fr['pieces']:
            for w in p['words']:
                if MG.tile_bytes(hd, w)[0] != S.tile(w): bad += 1
print('mk2 frames compared', n, 'mismatches', bad)
