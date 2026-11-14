"""Extract creases and silhouette edges from the publicly credited reference STLs.

Usage: python scripts/extract_blueprint.py JACKAL.stl BRACKET.stl
The generated linework is an illustration, not a manufacturing drawing.
"""
import hashlib
import json
import math
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VIEW=(.52,.74,.44)


def extract(source,kind):
    data=Path(source).read_bytes();n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*n
    def point(v):
        if kind=='jackal':return tuple(round(x,6) for x in (v[2],v[0],v[1]-.0655))
        return tuple(round(x/1000,6) for x in v)
    edges=defaultdict(list)
    for i in range(n):
        vals=struct.unpack_from('<12fH',data,84+i*50)
        a,b,c=[point(vals[k:k+3]) for k in [3,6,9]]
        u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
        normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        norm=math.sqrt(sum(x*x for x in normal))
        if norm<1e-12:continue
        normal=tuple(x/norm for x in normal)
        for x,y in [(a,b),(b,c),(c,a)]:edges[tuple(sorted([x,y]))].append(normal)
    out=[]
    for (a,b),normals in edges.items():
        facing=[sum(n[k]*VIEW[k] for k in range(3)) for n in normals]
        crease=len(normals)!=2 or sum(normals[0][k]*normals[1][k] for k in range(3))<math.cos(math.radians(28))
        silhouette=min(facing)<0<max(facing)
        if (crease or silhouette) and math.dist(a,b)>.0005:
            out.append([a,b,1 if max(facing)>0 else 0])
    return {'source_sha256':hashlib.sha256(data).hexdigest(),'triangles':n,'edges':out}


if __name__=='__main__':
    result={k:extract(p,k) for k,p in zip(['jackal','bracket'],sys.argv[1:])}
    assert set(result)=={'jackal','bracket'}
    target=ROOT/'data/mechanical-geometry.json'
    target.write_text(json.dumps(result,separators=(',',':'))+'\n')
    for k,v in result.items():print(k,len(v['edges']),'reference edges')
