"""Render all MK2 stages and print per-stage compressed/decompressed sizes."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import stages
tot=0
for s in range(10):
    R=stages.record(s)
    z=stages.sizes(s)
    t=z['tiles'][0]+z['meta'][0]+z['maps'][0]+z['pal']
    tot+=t
    print(f"{s} {stages.STAGE_NAMES[s]:34s} tiles@{R['tiles']:06X} {z['tiles'][0]:6d}->{z['tiles'][1]:6d} (t{z['tiles'][2]})  meta@{R['meta']:06X} {z['meta'][0]:5d}->{z['meta'][1]:5d} (t{z['meta'][2]})  maps {z['maps'][1]:2d} unique {z['maps'][0]:5d}B  pal@{R['pal']:06X}  total packed {t:6d}B")
    stages.render_stage(s, '/home/claude/work/out/mk2/stage%d.png'%s)
print('all stages packed total', tot)
