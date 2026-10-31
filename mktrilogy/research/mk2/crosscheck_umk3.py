"""Quick cross-check (not a full analysis): do MK3/UMK3 contain the same code byte sequences as MK2's
tile fetch ($81:834B), mask-expansion handlers ($81:8451) and LZ decompressor ($85:B9FC)?"""
import sys; sys.path.insert(0,'/home/claude/work/lib')
import snes
mk2=snes.load('mk2')
probes={'tile_fetch_81834B':(0x81834B,24),'mask_handler_818460':(0x818460,22),'lz_85B9FC':(0x85B9FC,24),
        'lz_split_85BB49':(0x85BB49,20),'frame_build_818050':(0x818050,24),'anim_interp_83F28E':(0x83F28E,16)}
for rn in ('mk3','umk3'):
    r=snes.load(rn)
    for k,(a,n) in probes.items():
        o=snes.to_off(a,len(mk2)); pat=mk2[o:o+n]
        hits=[]; i=r.find(pat)
        while i!=-1 and len(hits)<4: hits.append(i); i=r.find(pat,i+1)
        print(rn, k, 'len',n, 'hits', ['%06X (=$%06X)'%(h,0xC00000|h) for h in hits])
import re
print('--- wildcard probes')
pats={'mask_handler_code01': rb'\xA6.\x9E..\x9E..\x9E..\xB7.\xC8\x29\xFF\x00\xEB\x9D..\x60',
      'lz_backref_decode': rb'\xEB\x29\xFF\x07.{0,3}\x85.\x8A\x29\x78\x00\x4A\x4A\xAA',
      'anim_cmd_check_FFF6': rb'\xC9\xF6\xFF\xB0.\x22...\xA9\x01\x00\x18\x6B'}
for rn in ('mk2','mk3','umk3'):
    r=snes.load(rn)
    for k,p in pats.items():
        hs=[m.start() for m in re.finditer(p,r,re.S)][:5]
        print(rn,k,len(hs),['$%06X'%(0xC00000|h) for h in hs])
