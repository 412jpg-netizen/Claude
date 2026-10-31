"""Check that every stage block decompresses with the write pointer ending exactly at 0."""
import sys; sys.path.insert(0,'/home/claude/work/scripts/mk2')
import stages, mk2lz
n=0; bad=[]
for s in range(10):
    R=stages.record(s)
    for a in [R['tiles'],R['meta']]+sorted(set(R['maps'])):
        d,i=mk2lz.decompress(a); n+=1
        if i['end_y']!=0: bad.append((s,hex(a),i))
print('blocks checked',n,'bad',bad)
