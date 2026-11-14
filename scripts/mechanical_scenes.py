"""Original SVG motion studies; mechanical references are documented in data/."""

import itertools
import colorsys
import json
import math
import xml.etree.ElementTree as ET
from functools import lru_cache
from html import escape
from pathlib import Path

BG, PANEL, LINE = '#090e1b', '#121c2e', '#2a3a50'
WHITE, MUTED, MINT, AMBER, LILAC = '#edf5f1', '#a8bcc8', '#91f2cc', '#ffc183', '#b5a4ff'


def line(d, color=MINT, width=1, extra=''):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def label(x, y, value, size=12, color=MUTED, extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="DejaVu Sans Mono,monospace" font-size="{size}" {extra}>{escape(value)}</text>'


def poly(pts, color=MINT, fill=PANEL, width=1, extra=''):
    coords=' '.join(f'{x:.3f},{y:.3f}' for x,y in pts)
    return f'<polygon points="{coords}" fill="{fill}" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" {extra}/>'


def dot(x, y, r, color=MINT, extra=''):
    return f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r}" fill="{color}" {extra}/>'


PHI=(1+math.sqrt(5))/2


def module_frame(v):
    x,y,z=v
    return ((x-y)/math.sqrt(2),(x+y-2*z)/math.sqrt(6),(x+y+z)/math.sqrt(3))


VERTICES=[module_frame(v) for v in itertools.product((-1,1),repeat=3)]
for a,b in itertools.product((-1,1),repeat=2):
    v=(0,a/PHI,b*PHI)
    VERTICES.extend(module_frame(v[k:]+v[:k]) for k in range(3))
EDGES=[(i,j) for i,j in itertools.combinations(range(20),2)
       if abs(math.dist(VERTICES[i],VERTICES[j])-2/PHI)<1e-8]


def view(v):
    x,y,z=v
    return .5*x+.8660254*y,.45*x-.2598076*y-.8544*z


def dodecahedron(color=MINT):
    """The public simulator's vertex-up regular dodecahedral frame, with six rotor glyphs."""
    p=[view(v) for v in VERTICES]
    body=''
    for i,j in EDGES:
        a,b=p[i],p[j]
        body+=line(f'M{a[0]:.3f} {a[1]:.3f}L{b[0]:.3f} {b[1]:.3f}',color,.032,extra='opacity=".24"')
    # A compact hexarotor, simplified enough to remain readable in a moving formation.
    for i in range(6):
        a=math.tau*i/6;x,y=.68*math.cos(a),.68*math.sin(a)
        cx,cy=view((x,y,0))
        body+=line(f'M0 0L{cx:.3f} {cy:.3f}',MUTED,.065)
        body+=f'<ellipse cx="{cx:.3f}" cy="{cy:.3f}" rx=".27" ry=".12" fill="{BG}" stroke="{color}" stroke-width=".035"/>'
        body+=f'<g transform="translate({cx:.3f} {cy:.3f}) scale(1 .44)"><g class="anim spin">'+line('M-.23 0H.23M0 -.23V.23',WHITE,.025)+'</g></g>'
    for i,j in EDGES:
        a,b=VERTICES[i],VERTICES[j]
        depth=sum((a[k]+b[k])*(.74,-.43,.52)[k] for k in range(3))
        if depth>0:
            u,v=p[i],p[j]
            body+=line(f'M{u[0]:.3f} {u[1]:.3f}L{v[0]:.3f} {v[1]:.3f}',color,.042,extra='opacity=".9"')
    body+=dot(0,0,.09,AMBER)
    return body


N1,N2,N3=map(module_frame,[(2,0,-2),(0,2,-2),(2,2,0)])


def formation(kind):
    if kind=='delta':slots=[(i,j,0) for j in range(4) for i in range(4-j)]
    elif kind=='spine':slots=[(i,j,0) for j in range(2) for i in range(5)]
    else:slots=[(i,j,k) for k in range(3) for j in range(3-k) for i in range(3-k-j)]
    pts=[tuple(i*N1[a]+j*N2[a]+k*N3[a] for a in range(3)) for i,j,k in slots]
    projected=[view(v) for v in pts]
    center=[(min(p[a] for p in projected)+max(p[a] for p in projected))/2 for a in range(2)]
    return [(x-center[0],y-center[1]) for x,y in projected]


SWARM_COLORS=['#85f2cb','#7fd8ff','#95a7ff','#c39bff','#f0a0e3','#ff9eb1','#ffc082','#f6df8c','#c0e58c','#7ce4df']

def flight_points(i,forms):
    a,b,c=[f[i] for f in forms];angle=math.tau*i/10
    q=(9.4*math.cos(angle),3.2*math.sin(angle));r=(q[0]*.88,-q[1]*.8);d=(i%5)*.38
    return [(0,a),(18,a),(21+d,q),(24+d,r),(28+d,b),(31,b),(47,b),(50+d,r),(54+d,q),(58+d,c),(61,c),(77,c),(80+d,q),(84+d,r),(88+d,a),(91,a),(100,a)]

def flight_position(keys,percent):
    """C1-continuous Hermite flights, settling to zero velocity at docked holds."""
    percent%=100
    def tangent(i):
        if i==0 or i==len(keys)-1:return (0.,0.)
        t,a=keys[i-1];_,b=keys[i];tt,c=keys[i+1]
        if a==b or b==c:return (0.,0.)
        return tuple(.85*(c[k]-a[k])/(tt-t) for k in range(2))
    for i,((t0,a),(t1,b)) in enumerate(zip(keys,keys[1:])):
        if t0<=percent<=t1:
            u=(percent-t0)/(t1-t0);m,n=tangent(i),tangent(i+1)
            return tuple((2*u**3-3*u*u+1)*a[k]+(u**3-2*u*u+u)*(t1-t0)*m[k]+(-2*u**3+3*u*u)*b[k]+(u**3-u*u)*(t1-t0)*n[k] for k in range(2))
    return keys[-1][1]


def flight_state(i,percent,forms):
    keys=flight_points(i,forms);percent%=100
    p=flight_position(keys,percent)
    active=next(((percent-t)/(tt-t)) for (t,a),(tt,b) in zip(keys,keys[1:]) if t<=percent<=tt and a!=b) if any(t<=percent<=tt and a!=b for (t,a),(tt,b) in zip(keys,keys[1:])) else None
    gate=math.sin(math.pi*active)**2 if active is not None else 0
    phase=math.tau*percent/100
    noise=(.11*gate*math.sin(phase*19+i*1.7),.085*gate*math.sin(phase*23+i*.9))
    common=(.018*math.sin(phase*3),.025*math.sin(phase*5))
    p=tuple(p[k]+noise[k]+common[k] for k in range(2))
    before=flight_position(keys,percent-.06);after=flight_position(keys,percent+.06)
    roll=max(-18,min(18,(after[0]-before[0])/.12*5))
    return p,roll,1-.13*gate

@lru_cache(maxsize=1)
def flight_trails():
    forms=[formation(k) for k in ['delta','spine','pyramid']]
    css='';art=''
    for i,color in enumerate(SWARM_COLORS):
        keys=flight_points(i,forms)
        for j,opacity in enumerate([.6,.28,.1]):
            name=f'flight-trail-{i}-{j}'
            css+=f'.{name}{{animation:{name} 15s linear infinite}}@keyframes {name}'+'{'
            for f in range(221):
                t=f/220*15
                pts=[flight_state(i,(t-.035-j*.26-k*.26/3)/15*100,forms)[0] for k in range(4)]
                pts=list(reversed(pts));a,b,c,d=pts
                control1=(a[0]+(b[0]-a[0])*1.5,a[1]+(b[1]-a[1])*1.5)
                control2=(d[0]-(d[0]-c[0])*1.5,d[1]-(d[1]-c[1])*1.5)
                d=f'M{a[0]:.3f},{a[1]:.3f}C{control1[0]:.3f},{control1[1]:.3f} {control2[0]:.3f},{control2[1]:.3f} {d[0]:.3f},{d[1]:.3f}' 
                css+=f'{f/220*100:.3f}%{{d:path("{d}")}}'
            css+='}'
            art+=line('M0 0C0 0 0 0 0 0',color,.06 if j==0 else .045,extra=f'class="anim {name}" opacity="{opacity}"')
    return css,art


@lru_cache(maxsize=1)
def thrust_animation():
    """An aesthetic speed cue: per-module normalized speed, not a thrust solver."""
    forms=[formation(k) for k in ['delta','spine','pyramid']]
    styles=[]
    for i,color in enumerate(SWARM_COLORS):
        speeds=[]
        for frame in range(221):
            percent=frame/220*100
            a=flight_state(i,percent-.025,forms)[0];b=flight_state(i,percent+.025,forms)[0]
            speeds.append(math.dist(a,b)/.05)
        peak=max(speeds) or 1
        hue,light,_=colorsys.rgb_to_hls(*(int(color[k:k+2],16)/255 for k in [1,3,5]))
        intense=colorsys.hls_to_rgb(hue,min(.68,light),.98)
        styles.append(f'.thrust-{i}'+f'{{animation:thrust-{i} 15s linear infinite}}@keyframes thrust-{i}'+'{')
        for frame,speed in enumerate(speeds):
            strength=min(1,speed/peak)
            opacity=.005+.695*strength
            end=2.0+.8*strength
            shade='#'+''.join(f'{round(105+(v*255-105)*strength):02x}' for v in intense)
            d=f'M-.38 1.65L-.38 {end:.3f}M.38 1.65L.38 {end:.3f}'
            styles.append(f'{frame/220*100:.3f}%{{opacity:{opacity:.5f};stroke:{shade};stroke-width:{.025+.05*strength:.4f};d:path("{d}")}}')
        styles.append('}')
    return ''.join(styles)


def swarm(ox,oy,scale=25,caption=False):
    """Ten dodecahedral modules reconfigure on the simulator's FCC neighbour lattice."""
    forms=[formation(k) for k in ['delta','spine','pyramid']]
    css,trails=flight_trails();css+=thrust_animation();body=''
    for i in range(10):
        a,b,c=[f[i] for f in forms]
        angle=math.tau*i/10
        scatter=(9.4*math.cos(angle),3.2*math.sin(angle))
        sweep=(scatter[0]*.88,-scatter[1]*.8)
        def pose(p,roll=0,s=1):return f'transform:translate({p[0]:.3f}px,{p[1]:.3f}px) rotate({roll}deg) scale({s})'
        css+=f'.swarm-{i}'+f'{{animation:swarm-{i} 15s linear infinite}}@keyframes swarm-{i}'+'{'
        for frame in range(221):
            percent=frame/220*100;p,roll,zoom=flight_state(i,percent,forms)
            css+=f'{percent:.3f}%{{{pose(p,round(roll,3),round(zoom,4))}}}'
        css+='}'
        color=SWARM_COLORS[i]
        streak=line('M-.38 1.65L-.38 2M.38 1.65L.38 2',color,.025,extra=f'class="anim thrust-{i}" opacity=".005"')
        body+=f'<g class="anim swarm-{i}" style="{pose(a)}">{streak}{dodecahedron(color)}</g>'
    css+='''
.swarm-streak{animation:swarm-streak 15s linear infinite;opacity:0}
@keyframes swarm-streak{0%,18%,31%,47%,61%,77%,91%,100%{opacity:0}22%,25%,52%,55%,82%,85%{opacity:.65}}
.shape-delta{animation:shape-delta 15s steps(1) infinite}.shape-spine{animation:shape-spine 15s steps(1) infinite;opacity:0}.shape-pyramid{animation:shape-pyramid 15s steps(1) infinite;opacity:0}
@keyframes shape-delta{0%,91%{opacity:1}19%{opacity:0}100%{opacity:1}}
@keyframes shape-spine{0%,48%,100%{opacity:0}31%{opacity:1}}
@keyframes shape-pyramid{0%,78%,100%{opacity:0}61%{opacity:1}}
'''
    result=f'<style>{css}</style><g transform="translate({ox} {oy}) scale({scale})">{trails}{body}</g>'
    if caption:
        for name,cls in [('DELTA','delta'),('SPINE','spine'),('PYRAMID','pyramid')]:
            result+=f'<g class="anim shape-{cls}">'+label(ox,oy+scale*5.6,'10 MODULES / '+name,12,AMBER,extra='text-anchor="middle"')+'</g>'
    return result


def magnetics():
    css='''
.epm-on{animation:epm-on 12s steps(1) infinite;opacity:0}.epm-off{animation:epm-off 12s steps(1) infinite}
@keyframes epm-on{0%,59%,100%{opacity:0}18%{opacity:1}}
@keyframes epm-off{0%,59%,100%{opacity:1}18%{opacity:0}}
.epm-plus{animation:epm-plus 12s linear infinite;opacity:0}.epm-minus{animation:epm-minus 12s linear infinite;opacity:0}
@keyframes epm-plus{0%,9%,25%,100%{opacity:0}11%,23%{opacity:1}}
@keyframes epm-minus{0%,51%,66%,100%{opacity:0}53%,64%{opacity:1}}
.epm-current-plus{stroke-dasharray:2 9;animation:epm-current-plus 12s linear infinite;opacity:0}
.epm-current-minus{stroke-dasharray:2 9;animation:epm-current-minus 12s linear infinite;opacity:0}
@keyframes epm-current-plus{0%,9%{opacity:0;stroke-dashoffset:0}11%{opacity:1}23%{opacity:1;stroke-dashoffset:-180}25%,100%{opacity:0;stroke-dashoffset:-200}}
@keyframes epm-current-minus{0%,51%{opacity:0;stroke-dashoffset:0}53%{opacity:1}64%{opacity:1;stroke-dashoffset:180}66%,100%{opacity:0;stroke-dashoffset:200}}
.epm-hold{animation:epm-hold 12s linear infinite}
@keyframes epm-hold{0%,8%,27%,49%,68%,100%{opacity:1}10%,24%,52%,65%{opacity:0}}
'''
    body=f'<style>{css}</style>'
    body+=label(127,65,'CURRENT → FIELD → REMANENCE',11,LILAC)
    body+='<g class="anim epm-on">'
    for i in range(4):
        body+=line(f'M262 {85-i*2}C{132-i*18} {37-i*5} {132-i*18} {231+i*3} 263 205',MINT,1,extra='class="anim flow" opacity=".6"')
        body+=line(f'M375 {85-i*2}C{501+i*18} {37-i*5} {501+i*18} {231+i*3} 375 205',MINT,1,extra='class="anim flow" opacity=".6"')
    body+='</g>'
    for y in [79,195]:body+=f'<rect x="238" y="{y}" width="158" height="11" rx="2" fill="{PANEL}" stroke="{MUTED}"/>'
    for x in [250,353]:
        body+=f'<rect x="{x}" y="90" width="32" height="105" fill="{PANEL}" stroke="{MINT if x==250 else LILAC}" stroke-width="1.3"/>'
    body+=line('M266 172V112m-5 8 5-8 5 8',MINT,2)
    body+=label(261,104,'N',10,MINT)+label(261,189,'S',10,LILAC)
    for cls,top,bottom in [('epm-on','N','S'),('epm-off','S','N')]:
        top_color=MINT if top=='N' else LILAC
        bottom_color=MINT if bottom=='N' else LILAC
        arrow='M369 168V116m-5 8 5-8 5 8' if top=='N' else 'M369 116V168m-5-8 5 8 5-8'
        body+=f'<g class="anim {cls}"><rect x="354" y="91" width="30" height="17" fill="{top_color}" opacity=".13"/><rect x="354" y="177" width="30" height="17" fill="{bottom_color}" opacity=".13"/>'
        body+=label(364,104,top,10,top_color)+label(364,189,bottom,10,bottom_color)+line(arrow,LILAC,2)+'</g>'
    winding='M413 214L402 189'
    for y in range(185,100,-14):
        winding+=f'C{402} {y-16} 328 {y-16} 330 {y-3}C332 {y+9} 402 {y+7} 402 {y-8}'
    winding+='L410 86'
    body+=line(winding,AMBER,1.1,extra='opacity=".6"')
    for cls in ['epm-current-plus','epm-current-minus']:body+=line(winding,WHITE,2,extra=f'class="anim {cls}"')
    body+='<g class="anim epm-off">'+line('M267 191V85H369V200H267',LILAC,1.1,extra='class="anim flow" opacity=".55"')+'</g>'
    for cls,arrow,txt in [('epm-plus','M391 174V110m-4 7 4-7 4 7','PULSE +'),('epm-minus','M391 110V174m-4-7 4 7 4-7','PULSE −')]:
        body+=f'<g class="anim {cls}">'
        for i in range(3):
            body+=line(f'M{363+i*4} 193V91C{444+i*8} 65 {444+i*8} 219 {363+i*4} 193',AMBER,.8,
                       extra='class="anim flow" opacity=".35"'+(' style="animation-direction:reverse"' if cls=='epm-minus' else ''))
        body+=line(arrow,AMBER,1.7)+label(55,144,txt,12,AMBER)+label(419,145,'H',14,AMBER)+'</g>'
    body+='<g class="anim epm-hold">'+label(55,144,'I = 0',15,MUTED)+label(55,163,'LATCHED',10,MUTED)+'</g>'
    body+=label(243,229,'NdFeB',11,MUTED)+label(344,229,'Alnico',11,MUTED)
    for cls,txt,col in [('epm-on','FLUX ON',MINT),('epm-off','FLUX OFF',LILAC)]:
        body+=f'<g class="anim {cls}">'+label(467,219,txt,11,col)+'</g>'
    return body


class Blueprint:
    """Orthographic solid primitives and crease lines in the robot's metre frame."""
    def __init__(self,ox,oy,scale):self.ox,self.oy,self.scale=ox,oy,scale

    def p(self,v):
        x,y,z=v
        return self.ox+self.scale*(.818*x-.574*y),self.oy+self.scale*(.25*x+.36*y-.90*z)

    def wire(self,vertices,color=MINT,width=.8,extra='',closed=False):
        pts=[self.p(v) for v in vertices]
        return line('M'+'L'.join(f'{x:.2f} {y:.2f}' for x,y in pts)+('Z' if closed else ''),color,width,extra)

    def facing(self,vertices):
        """Visibility from projected winding, including inherited joint rotations."""
        pts=[self.p(v) for v in vertices]
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))
        return 1 if area>1e-8 else 0

    def box(self,center,size,color=MINT,holes=False):
        x,y,z=center;dx,dy,dz=[v/2 for v in size]
        vertices=[(x+a*dx,y+b*dy,z+c*dz) for a,b,c in itertools.product((-1,1),repeat=3)]
        faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
        # Opaque closed surfaces are separate from the visible-edge pass. Every
        # pose has all six faces, so an edge-visibility transition cannot open a
        # hole or change the path topology during SVG interpolation.
        result=''.join(poly([self.p(vertices[i]) for i in face],'none',PANEL,0) for face in faces)
        for face in faces:
            points=[vertices[i] for i in face]
            result+=poly([self.p(v) for v in points],color,'none',.75,
                         extra=f'opacity="{self.facing(points)}"')
        if holes:
            visible=self.facing([vertices[i] for i in faces[-1]])
            for a,b in itertools.product([-.3,.3],repeat=2):
                px,py=self.p((x+a*size[0],y+b*size[1],z+dz))
                result+=dot(px,py,1.3,BG,extra=f'stroke="{color}" stroke-width=".6" opacity="{visible}"')
        return result

    def cylinder(self,center,radius,length,axis='y',color=MUTED,treads=False):
        a='xyz'.index(axis);others=[k for k in range(3) if k!=a];segments=24
        rings=[]
        for side in [-1,1]:
            ring=[]
            for i in range(segments):
                v=list(center);v[a]+=side*length/2
                v[others[0]]+=radius*math.cos(math.tau*i/segments)
                v[others[1]]+=radius*math.sin(math.tau*i/segments)
                ring.append(v)
            rings.append(ring)
        caps=[list(reversed(rings[0])),rings[1]] if axis!='y' else [rings[0],list(reversed(rings[1]))]
        sides=[]
        for i in range(segments):
            j=(i+1)%segments;face=[rings[0][i],rings[0][j],rings[1][j],rings[1][i]]
            sides.append(face if axis!='y' else list(reversed(face)))
        result=''.join(poly([self.p(v) for v in face],'none',PANEL,0) for face in sides+caps)
        for cap in caps:
            result+=poly([self.p(v) for v in cap],color,'none',.8,
                         extra=f'opacity="{self.facing(cap)}"')
        # Two exact projected silhouette generators close the shaft between its
        # caps, without a distracting web of side-facet edges.
        c0,c1=[self.p(tuple(center[k]+(side*length/2 if k==a else 0) for k in range(3))) for side in [-1,1]]
        u=list(center);v=list(center);u[others[0]]+=radius;v[others[1]]+=radius
        cp=self.p(center);up=self.p(u);vp=self.p(v)
        normal=(-(c1[1]-c0[1]),c1[0]-c0[0])
        if abs(normal[0])+abs(normal[1])<1e-10:normal=(1,0)
        theta=math.atan2(sum((vp[k]-cp[k])*normal[k] for k in range(2)),
                         sum((up[k]-cp[k])*normal[k] for k in range(2)))
        for angle in [theta,theta+math.pi]:
            points=[]
            for side in [-1,1]:
                point=list(center);point[a]+=side*length/2
                point[others[0]]+=radius*math.cos(angle);point[others[1]]+=radius*math.sin(angle)
                points.append(point)
            result+=self.wire(points,color,.75)
        if treads:
            for i in range(0,segments,2):
                result+=self.wire([rings[0][i],rings[1][i]],color,.6,
                                 extra=f'opacity="{.55*self.facing(sides[i])}"')
        return result

    def mesh(self,name,offset=(0,0,0),color=MINT):
        data=json.loads((Path(__file__).resolve().parents[1]/'data/mechanical-geometry.json').read_text())[name]
        paths={0:[],1:[]}
        for a,b,visible in data['edges']:
            a,b=[self.p(tuple(v[k]+offset[k] for k in range(3))) for v in [a,b]]
            paths[visible].append(f'M{a[0]:.2f} {a[1]:.2f}L{b[0]:.2f} {b[1]:.2f}')
        return line(''.join(paths[0]),color,.6,extra='opacity=".13"')+line(''.join(paths[1]),color,.8,extra='opacity=".8"')


class CameraBlueprint(Blueprint):
    """A slightly more frontal view of the camera, without changing the robot view."""
    def p(self,v):
        x,y,z=v
        return self.ox+self.scale*(.55*x-.83*y),self.oy+self.scale*(.34*x+.23*y-.90*z)


class YawBlueprint(Blueprint):
    def __init__(self,base,pivot,yaw):
        super().__init__(base.ox,base.oy,base.scale)
        self.pivot,self.yaw=pivot,yaw
    def p(self,v):
        x,y,z=[v[k]-self.pivot[k] for k in range(3)]
        c,s=math.cos(self.yaw),math.sin(self.yaw)
        return super().p((self.pivot[0]+c*x-s*y,self.pivot[1]+s*x+c*y,self.pivot[2]+z))


class JointBlueprint(Blueprint):
    def __init__(self,base,origin,angles,depth):
        super().__init__(base.ox,base.oy,base.scale)
        self.base,self.origin,self.angles,self.depth=base,origin,angles,depth
    def p(self,v):
        point=[v[k]-self.origin[k] for k in range(3)]
        def rotate(point,pivot,axis,angle):
            q=[point[k]-pivot[k] for k in range(3)];c,s=math.cos(angle),math.sin(angle)
            i,j=[k for k in range(3) if k!=axis]
            if axis==1:angle=-angle;c,s=math.cos(angle),math.sin(angle)
            q[i],q[j]=c*q[i]-s*q[j],s*q[i]+c*q[j]
            return [q[k]+pivot[k] for k in range(3)]
        yaw,roll,pitch=self.angles
        if self.depth>=3:point=rotate(point,(0,0,-.059),1,pitch)
        if self.depth>=2:point=rotate(point,(-.04,0,-.059),0,roll)
        if self.depth>=1:point=rotate(point,(0,0,-.014),2,yaw)
        return self.base.p(tuple(point[k]+self.origin[k] for k in range(3)))


def exploded(name,dx,dy,content,delay=0):
    # Explicit inline pose remains an informative exploded view with reduced motion.
    css=f'''<style>.{name}{{animation:{name} 5s cubic-bezier(.76,0,.24,1) infinite}}
@keyframes {name}{{0%,10%,90%,100%{{transform:translate(0,0)}}28%,72%{{transform:translate({dx}px,{dy}px)}}}}</style>'''
    return css+f'<g class="anim {name}" style="transform:translate({dx}px,{dy}px)">{content}</g>'


def gimbal(b,origin=(0,0,0),prefix='gimbal',explode=True,angles=None):
    def add(v):return tuple(origin[k]+v[k] for k in range(3))
    parts=[
        ('mount',(0,0,-.007),(.050,.050,.014),MUTED,(0,0)),
        ('yaw',(-.012,0,-.026),(.034,.034,.018),AMBER,(0,13)),
        ('roll',(-.020,-.031,-.059),(.050,.012,.030),MUTED,(-24,28)),
        ('camera',(0,0,-.059),(.040,.045,.035),MINT,(27,44))]
    result='';base_b=b;mount=''
    for i,(name,pos,size,col,move) in enumerate(parts):
        b=JointBlueprint(base_b,origin,angles,i) if angles is not None else base_b
        chunk=b.box(add(pos),size,col,holes=name=='mount')
        if name=='yaw':chunk+=b.cylinder(add((0,0,-.014)),.013,.009,'z',AMBER)
        if name=='roll':chunk+=b.cylinder(add((-.040,0,-.059)),.013,.012,'x',MUTED)
        if name=='camera':
            chunk=b.cylinder(add((0,-.024,-.059)),.012,.009,'y',MUTED)+chunk
            chunk+=b.cylinder(add((.028,0,-.059)),.016,.016,'x',WHITE)
            chunk+=b.cylinder(add((.038,0,-.059)),.011,.004,'x',MINT)
        drawn=exploded(prefix+'-'+name,*move,chunk,i*2) if explode else chunk
        if name=='mount':mount=drawn
        else:result+=drawn
    result+=mount
    if explode:
        result+=b.wire([(0,0,0),(0,0,-.028),(-.04,0,-.059),(0,0,-.059)],MUTED,.75,extra='stroke-dasharray="3 5" opacity=".5"')
    return result


# Continuous periodic sweep with no stationary holds.
CAMERA_SCAN_SECONDS = 12


def camera_scan_angles(seconds):
    phase=math.tau*(seconds % CAMERA_SCAN_SECONDS)/CAMERA_SCAN_SECONDS
    return .42*math.sin(phase), 0., .24*math.sin(2*phase)


class ScanJointBlueprint(JointBlueprint):
    """Smooth cylinders using their exact silhouette, without hidden facets."""
    def cylinder(self, center, radius, length, axis='y', color=MUTED, treads=False):
        a='xyz'.index(axis)
        other=[k for k in range(3) if k!=a]
        def point(side, angle):
            v=list(center)
            v[a]+=side*length/2
            v[other[0]]+=radius*math.cos(angle)
            v[other[1]]+=radius*math.sin(angle)
            return tuple(v)
        c0,c1=[self.p(point(side,0)) for side in [-1,1]]
        normal=(-(c1[1]-c0[1]), c1[0]-c0[0])
        cp=self.p(center)
        u=list(center);u[other[0]]+=radius
        v=list(center);v[other[1]]+=radius
        up,vp=self.p(u),self.p(v)
        theta=math.atan2(sum((vp[k]-cp[k])*normal[k] for k in range(2)),
                         sum((up[k]-cp[k])*normal[k] for k in range(2)))
        sides=[[point(side, angle) for side in [-1,1]] for angle in [theta,theta+math.pi]]
        body=[sides[0][0],sides[0][1],sides[1][1],sides[1][0]]
        result=poly([self.p(v) for v in body], 'none', PANEL, 0)
        rings=[[point(side,math.tau*i/32) for i in range(32)] for side in [-1,1]]
        caps=[list(reversed(rings[0])),rings[1]] if axis!='y' else [rings[0],list(reversed(rings[1]))]
        for cap in caps:
            result+=poly([self.p(v) for v in cap], 'none', PANEL, 0)
        for cap in caps:
            result+=poly([self.p(v) for v in cap],color,'none',.8,
                         extra=f'opacity="{self.facing(cap)}"')
        for side in sides:
            result+=self.wire(side,color,.75)
        return result


def scan_gimbal(b, angles):
    """Connected camera detail; each solid belongs to one physical joint.

    The yaw neck feeds a rear roll bearing. A U-shaped yoke connects that
    bearing to the two pitch trunnions; only the camera and lens pitch.
    Roll stays locked. The fixed mounting plate never inherits a joint pose.
    """
    yaw = ScanJointBlueprint(b, (0, 0, 0), angles, 1)
    yoke = ScanJointBlueprint(b, (0, 0, 0), angles, 2)
    camera = ScanJointBlueprint(b, (0, 0, 0), angles, 3)
    # Far pitch arm first, then the camera, then the near arm. This preserves
    # occlusion throughout the deliberately limited scan envelope.
    def hidden_edges(fragment):
        root=ET.fromstring('<svg>'+fragment+'</svg>')
        for el in root:
            el.set('stroke', 'none')
        return ''.join(ET.tostring(el, encoding='unicode') for el in root)
    result = yaw.cylinder((0, 0, -.025), .010, .024, 'z', MUTED)
    # One continuous extruded L bracket avoids overlapping box seams at the
    # rear elbow. Every face shares the same vertices and joint transform.
    profile=[(.006,-.033),(-.046,-.033),(-.046,-.062),
             (-.034,-.062),(-.034,-.043),(.006,-.043)]
    rings=[[(x,y,z) for x,z in profile] for y in [-.010,.010]]
    faces=[list(reversed(rings[0])),rings[1]]
    for i in range(len(profile)):
        j=(i+1)%len(profile)
        faces.append([rings[0][i],rings[0][j],rings[1][j],rings[1][i]])
    for face in faces:
        result += poly([yaw.p(v) for v in face], 'none', PANEL, 0)
    for face in faces:
        result += poly([yaw.p(v) for v in face], MUTED, 'none', .75,
                       extra=f'opacity="{yaw.facing(face)}"')
    result += yaw.cylinder((-.040, 0, -.059), .011, .014, 'x', MUTED)
    result += hidden_edges(yoke.box((-.030, 0, -.059), (.010, .072, .010), MUTED))
    result += yoke.box((-.013, -.032, -.059), (.044, .008, .012), MUTED)
    result += yoke.cylinder((0, -.026, -.059), .009, .012, 'y', MUTED)
    result += camera.box((0, 0, -.059), (.040, .044, .032), MINT)
    result += camera.cylinder((.027, 0, -.059), .013, .014, 'x', WHITE)
    result += camera.cylinder((.036, 0, -.059), .009, .004, 'x', MINT)
    result += yoke.box((-.013, .032, -.059), (.044, .008, .012), MUTED)
    result += yoke.cylinder((0, .026, -.059), .009, .012, 'y', MUTED)
    # Plate is above the neck and stays bolted to the same screen position.
    result += b.box((0, 0, -.007), (.050, .050, .014), MUTED, holes=True)
    return result


def moving_gimbal(b):
    """Project rigid 3D poses, then interpolate densely sampled SVG geometry."""
    frames=[]
    times=[CAMERA_SCAN_SECONDS*i/180 for i in range(181)]
    for seconds in times:
        angles=camera_scan_angles(seconds)
        root=ET.fromstring('<svg>'+scan_gimbal(b,angles)+'</svg>')
        paths=[]
        for el in root:
            attrs=dict(el.attrib)
            if el.tag=='polygon':
                pts=attrs.pop('points').split();d='M'+'L'.join(pts)+'Z'
            elif el.tag=='circle':
                x,y,r=[float(attrs.pop(k)) for k in ['cx','cy','r']]
                d=f'M{x-r:.3f} {y:.3f}a{r} {r} 0 1 0 {2*r} 0a{r} {r} 0 1 0 {-2*r} 0'
            else:d=attrs.pop('d')
            paths.append((d,attrs))
        frames.append(paths)
    css='';art=''
    for i,(d,attrs) in enumerate(frames[0]):
        # Fixed plate surfaces need no animation at all.
        fixed=all(paths[i]==frames[0][i] for paths in frames)
        name=f'gimbal-scan-{i}'
        if not fixed:
            css+=f'.{name}'+f'{{animation:{name} {CAMERA_SCAN_SECONDS}s linear infinite}}@keyframes {name}'+'{'
            for f,paths in enumerate(frames):
                d_frame,frame_attrs=paths[i]
                css+=f'{times[f]/CAMERA_SCAN_SECONDS*100:.3f}%'+f'{{d:path("{d_frame}");opacity:{frame_attrs.get("opacity","1")}}}'
            css+='}'
        attr=' '.join(f'{k}="{v}"' for k,v in attrs.items())
        cls='' if fixed else f' class="anim {name}"'
        art+=f'<path d="{d}" {attr}{cls}/>'
    return '<style>'+css+'</style>'+art


def joint_axis(b,point,axis,color):
    px,py=b.p(point)
    return dot(px,py,1.7,BG,extra=f'stroke="{color}" stroke-width=".7" opacity=".55"')


def jackal_blueprint(mobile=False):
    result=''
    if mobile:
        bx,by,s=230,610,225
        result+=label(29,244,'A / SYSTEM',17,MINT)
    else:
        bx,by,s=303,563,218
        result+=label(47,176,'A / SYSTEM ASSEMBLY',14,MINT)
    b=Blueprint(bx,by,s)
    # Source J100 chassis creases, accurate axle spacing, solid tyres with hubs and tread.
    for i,(x,y) in enumerate(itertools.product([-.131,.131],[-.187795,.187795])):
        wheel=b.cylinder((x,y,.0345),.1,.04,'y',MUTED,True)
        wheel+=b.cylinder((x,y+(.023 if y>0 else -.023),.0345),.038,.004,'y',MINT)
        for j in range(6):
            a=math.tau*j/6
            px,py=b.p((x+.025*math.cos(a),y+(.026 if y>0 else -.026),.0345+.025*math.sin(a)))
            wheel+=dot(px,py,.8,WHITE)
        dx,dy=s*(-.574)*(.10 if y>0 else -.10),s*.36*(.10 if y>0 else -.10)
        result+=exploded(f'jackal-wheel-{i}',dx,dy,wheel,0)
    result+=b.mesh('jackal',color=MUTED)
    # Sensor deck and its real four M5 mounting locations (120 mm pitch).
    deck=b.box((-.045,0,.19),(.15,.15,.008),MINT)
    for x,y in itertools.product([-.06,.06],repeat=2):
        px,py=b.p((x-.045,y,.199));deck+=dot(px,py,1,BG,extra=f'stroke="{WHITE}" stroke-width=".7"')
    result+=exploded('jackal-deck',0,-13,deck,3)
    result+=exploded('jackal-bracket',0,-25,b.mesh('bracket',(-.045,0,.184),MINT),6)
    rail=b.box((-.075,0,.196+1.677/2),(.030,.030,1.677),MINT)
    rail+=b.box((-.075,0,1.859),(.036,.034,.028),MUTED)
    rail+=b.box((-.101,0,.226),(.047,.042,.042),AMBER)
    # Two extruded guide edges and the drive belt, not an invented hydraulic ram.
    rail+=b.wire([(-.058,-.008,.25),(-.058,-.008,1.83)],AMBER,.7,extra='stroke-dasharray="3 4"')
    rail+=b.wire([(-.058,.008,.25),(-.058,.008,1.83)],MUTED,.6)
    result+=exploded('jackal-rail',0,-28,rail,7)
    carriage=b.box((-.0545,0,1.04),(.011,.065,.084),LILAC,True)
    carriage+=b.box((.001,0,1.079),(.10,.22,.006),MINT,True)
    carriage+=gimbal(YawBlueprint(b,(.016,.065,1.076),math.pi/2),(.016,.065,1.076),'full-left',False)
    carriage+=gimbal(YawBlueprint(b,(.016,-.065,1.076),-math.pi/2),(.016,-.065,1.076),'full-right',False)
    result+=exploded('jackal-carriage',37,-12,carriage,10)
    # Alignment axes retain the attachment locations while components separate.
    for height in [.196,1.04]:
        px,py=b.p((-.0545,0,height))
        result+=line(f'M{px:.2f} {py:.2f}l37 -12',LILAC,.7,extra='stroke-dasharray="3 5" opacity=".6"')
        result+=dot(px,py,2,BG,extra=f'stroke="{LILAC}" stroke-width=".8"')
    px,py=b.p((-.045,0,.184))
    result+=line(f'M{px:.2f} {py+5:.2f}v-44',MUTED,.7,extra='stroke-dasharray="3 5" opacity=".6"')
    # Small, dimensioned lidar housing and its circular scan plane.
    result+=b.box((.12,0,.227),(.06,.06,.086),MUTED)
    if mobile:
        dx=394;y0=b.p((-.0545,0,1.782))[1];y1=b.p((-.0545,0,.282))[1]
        result+=line(f'M{dx} {y0}V{y1}m-5-7 5 7 5-7M{dx-5} {y0+7}l5-7 5 7',MUTED,.9)
        center=(y0+y1)/2
        result+=label(420,center,'1.5 m',20,MUTED,extra=f'transform="rotate(90 420 {center})" text-anchor="middle"')
        result+=label(42,661,'J100 / FPB30 / 2 × C-200T',19,MUTED)
        result+=line('M28 687H572',LINE)
        result+=label(28,725,'B / CAMERA SCAN',19,MINT)
        inset=CameraBlueprint(224,773,1700)
        result+=moving_gimbal(inset)
        result+=label(414,797,'YAW / Z',16,MUTED)+label(414,831,'PITCH / Y',16,MUTED)+label(414,865,'ROLL LOCKED',14,MUTED)
        result+=label(28,1013,'1 PRISMATIC + 6 REVOLUTE AXES',18,MUTED)
    else:
        y0=b.p((-.0545,0,1.782))[1];y1=b.p((-.0545,0,.282))[1];center=(y0+y1)/2
        result+=line(f'M450 {y0}V{y1}m-5-7 5 7 5-7M445 {y0+7}l5-7 5 7M437 {y0}h19M437 {y1}h19',MUTED,.8)
        result+=label(473,center,'1.5 m STROKE',13,MUTED,extra=f'transform="rotate(90 473 {center})" text-anchor="middle"')
        result+=label(49,626,'J100 · FPB30 / B42 · DUAL C-200T',13,MUTED)
        result+=line('M610 164V612',LINE)
        result+=label(646,177,'B / CAMERA SCAN',14,MINT)
        inset=CameraBlueprint(848,221,1700)
        result+=moving_gimbal(inset)
        result+=label(1000,248,'YAW / Z',11,MUTED)+label(1000,276,'PITCH / Y',11,MUTED)+label(1000,304,'ROLL LOCKED',10,MUTED)
        result+=label(660,383,'YAW + PITCH / ROLL LOCKED',11,MUTED)
        result+=line('M646 403H1154',LINE)
        result+=label(646,433,'C / DECK INTERFACE',14,MINT)
        mount=Blueprint(831,570,650)
        result+=mount.box((0,0,-.006),(.19,.19,.012),MUTED,True)
        result+=mount.mesh('bracket',color=MINT)
        for x,y in itertools.product([-.06,.06],repeat=2):
            result+=mount.cylinder((x,y,-.002),.003,.023,'z',WHITE)
        result+=label(994,489,'4 × M5',13,MUTED)+label(994,513,'120 mm PITCH',12,MUTED)
        result+=label(994,561,'PRISMATIC Z',12,LILAC)+label(994,586,'2 × 3-AXIS',12,LILAC)
    return result
