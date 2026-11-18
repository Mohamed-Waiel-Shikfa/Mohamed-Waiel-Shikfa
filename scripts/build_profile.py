#!/usr/bin/env python3
"""Render the GitHub profile's original SVG artwork using Python and Node built-ins."""

import json
import math
import subprocess
import textwrap
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path

from mechanical_scenes import swarm, magnetics, jackal_blueprint, formation, dodecahedron, SWARM_COLORS
from additional_scenes import scene as additional_scene
from notebook_cards import build_notes

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
BG, PANEL, LINE = '#090e1b', '#121c2e', '#2a3a50'
WHITE, MUTED, MINT, AMBER, LILAC = '#edf5f1', '#a8bcc8', '#91f2cc', '#ffc183', '#b5a4ff'
SANS, MONO = 'DejaVu Sans, Arial, sans-serif', 'DejaVu Sans Mono, monospace'

STYLE = '''
.type-reveal{transform-origin:42px 0;animation:type-reveal 7s steps(30,end) infinite}@keyframes type-reveal{0%,8%{transform:scaleX(0)}52%,90%{transform:scaleX(1)}100%{transform:scaleX(0)}}
.flow{stroke-dasharray:5 10;animation:flow 8s linear infinite}
.float{animation:float 6s ease-in-out infinite}
.spin{animation:spin .65s linear infinite}
.scan{animation:scan 7s ease-in-out infinite}
.pulse{animation:pulse 4s ease-in-out infinite}
.eq{transform-box:fill-box;transform-origin:center bottom;animation:eq 1.6s ease-in-out infinite alternate}
.game-ball{animation:game-ball 6s ease-in-out infinite}
@keyframes flow{to{stroke-dashoffset:-120}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes scan{0%,100%{transform:translateY(-48px);opacity:.25}50%{transform:translateY(48px);opacity:.85}}
@keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}
@keyframes eq{from{transform:scaleY(.35)}to{transform:scaleY(1)}}
@keyframes game-ball{0%,100%{transform:translate(0,0)}30%{transform:translate(43px,-22px)}65%{transform:translate(73px,12px)}}
@media(prefers-reduced-motion:reduce){.anim{animation:none!important}}
'''



def text(x, y, value, size=20, color=WHITE, weight=400, mono=False, extra=''):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{MONO if mono else SANS}" '
            f'font-size="{size}" font-weight="{weight}" {extra}>{escape(str(value))}</text>')


def path(d, color=LINE, width=1, extra=''):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def circle(x, y, r, color=MINT, extra=''):
    return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{color}" {extra}/>'


def svg(w, h, title, body, description=''):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description or title)}</desc>
<style>{STYLE}</style>
<defs>
 <radialGradient id="glow"><stop stop-color="{MINT}" stop-opacity=".14"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
 <radialGradient id="violet"><stop stop-color="{LILAC}" stop-opacity=".13"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
 <linearGradient id="silk" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#11182c"/><stop offset=".48" stop-color="{BG}"/><stop offset="1" stop-color="#0b1b25"/></linearGradient>
 <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".72" numOctaves="3" stitchTiles="stitch" seed="7"/><feColorMatrix type="saturate" values="0"/></filter>
 <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="{MUTED}" opacity=".13"/></pattern>
 <filter id="bloom" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>
{body}
</svg>\n'''


def frame(w, h):
    body=(f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20" fill="url(#silk)" stroke="{LINE}"/>'
          f'<ellipse cx="{w*.83}" cy="{h*.26}" rx="{w*.42}" ry="{h*.72}" fill="url(#violet)"/>'
          f'<ellipse cx="{w*.75}" cy="{h*.9}" rx="{w*.43}" ry="{h*.61}" fill="url(#glow)"/>')
    for i in range(7):
        d=f'M{w*(.45+i*.034):.2f} {h-2}C{w*(.72+i*.02):.2f} {h*.65:.2f} {w*(.5+i*.035):.2f} {h*.34:.2f} {w-2} {h*(.05+i*.055):.2f}'
        body+=path(d,LILAC,.7,extra='opacity=".07"')
    body+=f'<rect x="2" y="2" width="{w-4}" height="{h-4}" rx="19" fill="{WHITE}" filter="url(#grain)" opacity=".025"/>'
    return (f'<defs><clipPath id="panel-clip"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="20"/></clipPath></defs>'
            f'<g clip-path="url(#panel-clip)">{body}</g>')


def project3(x, y, z, ox=0, oy=0, scale=1):
    return ox+(x-y)*.866*scale, oy+(x+y)*.4*scale-z*.9*scale


def points(values):
    return ' '.join(f'{x:.2f},{y:.2f}' for x, y in values)


def hero(mobile=False):
    if mobile:
        body=frame(600,720)
        body+=text(30,46,'MWS / RESEARCH & CODE',18,MINT,mono=True,extra='letter-spacing="2"')
        body+='<defs><clipPath id="typing-name"><rect class="anim type-reveal" x="30" y="65" width="540" height="43" style="transform-origin:30px 0"/></clipPath></defs>'
        body+='<g clip-path="url(#typing-name)">'+text(30,98,'Mohamed Waiel Shikfa',31,WHITE,600)+'</g>'
        body+=text(25,183,'Build things',65,WHITE,700,extra='letter-spacing="-2"')
        body+=text(25,255,'that move.',65,MINT,700,extra='letter-spacing="-2"')
        body+=text(30,306,'Robotics × systems × curiosity',24,MUTED)
        body+=path('M63 543L282 417 537 543 318 659Z',LINE,1)
        body+='<ellipse cx="300" cy="563" rx="155" ry="50" fill="url(#violet)"/>'
        body+=swarm(300,465,22)
        body+=text(30,622,'ASSEMBLE → RECONFIGURE → REPEAT',18,AMBER,mono=True)
        body+=path('M30 650H570',LINE)
        body+=text(30,691,"CMU-Q / CS '27 / DOHA",20,MUTED,mono=True)
        return svg(600,720,'Mohamed Waiel Shikfa — build things that move',body,
                   'Ten dodecahedral flight modules sweep into delta, spine, and pyramid configurations in a repeating concept animation. Computer Science at CMU-Q, Class of 2027.')
    body=frame(1200,520)
    body+='<ellipse cx="876" cy="366" rx="300" ry="185" fill="url(#violet)"/>'
    body+=text(42,48,'MWS / RESEARCH & CODE',16,MINT,mono=True,extra='letter-spacing="2"')
    body+=text(42,112,'Mohamed Waiel Shikfa',31,WHITE,600)
    body+=text(36,218,'Build things',73,WHITE,700,extra='letter-spacing="-3"')
    body+=text(36,300,'that move.',73,MINT,700,extra='letter-spacing="-3"')
    body+=text(42,352,'Robotics × systems × curiosity',24,MUTED)
    body+=text(42,418,"CMU-Q / CS '27 / DOHA",18,MUTED,mono=True)
    body+=path('M42 446H554',LINE)
    body+='<defs><clipPath id="typing"><rect class="anim type-reveal" x="42" y="460" width="510" height="36"/></clipPath></defs>'
    body+='<g clip-path="url(#typing)">'+text(42,485,'> code. build. understand. repeat_',17,MINT,mono=True)+'</g>'
    body+=path('M628 381L870 240 1157 388 915 529Z',LINE,1.2)
    for i in range(1,6):
        x=628+i*48;y=381-i*28
        body+=path(f'M{x} {y}l287 148',LINE,1,extra='opacity=".4"')
        body+=path(f'M{628+i*57} {381+i*29.6}l242 -141',LINE,1,extra='opacity=".4"')
    body+='<ellipse cx="887" cy="388" rx="160" ry="43" fill="none" stroke="#91f2cc" stroke-opacity=".15"/>'
    body+=path('M667 339Q879 430 1109 310',MINT,1.5,extra='class="anim flow" opacity=".45"')
    body+=swarm(889,257,25)
    body+=text(756,78,'MODULAR FLIGHT / CONCEPT STUDY',13,MUTED,mono=True)
    body+=text(704,470,'ASSEMBLE → RECONFIGURE → REPEAT',16,AMBER,mono=True)
    body+=path('M1148 94h18v18M1148 446h18v-18',MINT,1,extra='opacity=".5"')
    return svg(1200,520,'Mohamed Waiel Shikfa — build things that move',body,
               'A 15-second concept loop: ten dodecahedral flight modules swoop, dock into delta, spine, and pyramid structures, detach, and reconfigure on the public simulator’s lattice. Robotics, systems, and curiosity. This is concept artwork, not experimental flight footage.')


# key, number, category, title, short description, stack, accent
PROJECTS = [
 ('uav','01','RESEARCH / MODULAR FLIGHT','Modular Multi-UAV',['Idealized aerial docking and coordinated flight.','Configurable experiments in two physics engines.'],'PYTHON / PYBULLET + MUJOCO',MINT),
 ('magsim','03','RESEARCH / MAGNETIC ACTUATION','magsim',['Permanent-magnet forces. EPM switching.','Parameter sweeps, verification, and a web UI.'],'PYTHON / MAGNETICS + CIRCUITS',LILAC),
 ('ugv','02','RESEARCH / ACTIVE PERCEPTION','Vertical perception',['A Jackal, a camera mast, and a greenhouse.','A Gazebo test bed for choosing a better view.'],'PYTHON / ROS 2 + GAZEBO',MINT),
 ('review','04','RESEARCH / MANUSCRIPT IN PREPARATION','Electropermanent magnets',['A review of physics, models, devices, and uses.','The literature behind the magnetic mechanisms.'],'TEX / REVIEW IN PREPARATION',AMBER),
 ('graphics','05','GRAPHICS / UPSTREAM CONTRIBUTOR','CMU Graphics',['Rebuilt the sound engine. Fixed resizing.','Contributions merged into the upstream library.'],'PYTHON / OPEN SOURCE',MINT),
 ('r36s','07','GRAPHICS / HANDHELD HARDWARE','CMU Graphics on R36S',['CMU 15-112 games ported to the R36S.','Porting, input mapping, and rendering optimizations.'],'PYTHON / DARKOS',LILAC),
 ('arcade','06','GRAPHICS / CAMPUS HARDWARE','Campus arcade',['Software and controls for the campus arcade.','Contributed to and helped maintain the machine.'],'PYTHON / CONTROLS + HARDWARE',AMBER),
 ('logic','08','GRAPHICS / LEARNING BY BUILDING','Logic Gate Simulator',['Wire a circuit. Toggle the inputs.','Make digital logic visible.'],'PYTHON / PYGAME',MINT),
 ('dim3','09','COURSEWORK / 3D DATA','Dim3',['Meshes → points → voxels → graphs.','Preprocessing 3D data for machine learning.'],'PYTHON / 3D PREPROCESSING',LILAC),
 ('ironic','12','COURSEWORK / SUMMER OF CODE','OpenStack Ironic',['Real-world infrastructure, built together.','Bare-metal provisioning and the OpenStack SDK.'],'PYTHON / OPEN SOURCE',AMBER),
 ('salem','10','COURSEWORK / INTERACTIVE STORY',"Salem’s Adventure",['A first CS course project, built in Python.','Later ported to arcade and handheld.'],'PYTHON / CMU GRAPHICS',LILAC),
 ('opencode','11','COURSEWORK / TEAM ENGINEERING','17-313 team project',['Applied Software Engineering in a real codebase.','An OpenCode-based team project.'],'TYPESCRIPT / COLLABORATIVE DEVELOPMENT',MINT),
]


def project_scene(key,accent):
    body=''
    if key=='uav':
        body+=swarm(320,145,18)
        body+=text(320,233,'DELTA → SPINE → PYRAMID',11,MUTED,mono=True,extra='text-anchor="middle"')
    elif key=='magsim':
        body+=magnetics()
    elif key in ['arcade','logic','salem','opencode']:
        body+=additional_scene(key,accent)
    elif key=='review':
        for i in [2,1,0]:
            body+=f'<rect x="{252+i*10}" y="{63+i*8}" width="130" height="154" rx="5" fill="{PANEL}" stroke="{LINE if i else accent}"/>'
        body+=text(266,91,'EPM',18,accent,600,mono=True)
        body+=path('M266 103h99M266 112h99M266 121h66M266 182h99M266 191h87',MUTED,2,extra='opacity=".45"')
        body+=path('M282 159C300 124 340 124 356 159M282 159C300 174 340 174 356 159',MINT,1.4,extra='class="anim flow"')
        for x,y,label in [(122,100,'PHYSICS'),(122,190,'MODELS'),(435,100,'DEVICES'),(435,190,'USES')]:
            body+=text(x,y,label,12,MUTED,mono=True)
            body+=path(f'M{208 if x<300 else 410} {y-4}h{28 if x<300 else 17}',LINE)
    elif key=='r36s':
        body+=f'<rect x="225" y="53" width="190" height="185" rx="20" fill="{PANEL}" stroke="{accent}" stroke-width="1.6"/>'
        body+=f'<rect x="246" y="68" width="148" height="91" rx="6" fill="{BG}" stroke="{LINE}"/>'
        body+=path('M254 144h27v-15h28v15h37v-25h40',MINT,2)
        body+='<g class="anim game-ball">'+circle(275,109,5,AMBER)+'</g>'
        body+=path('M265 175v29M250 190h30',MUTED,9)
        for x,y,c in [(371,178,MINT),(386,192,AMBER),(355,192,LILAC),(371,206,MUTED)]:body+=circle(x,y,5,c)
        body+=f'<rect x="303" y="197" width="11" height="4" rx="2" fill="{MUTED}"/><rect x="323" y="197" width="11" height="4" rx="2" fill="{MUTED}"/>'
        body+=text(115,131,'PYTHON',11,MUTED,mono=True)+path('M159 141h43m-7-5 7 5-7 5',accent,1.5,extra='class="anim pulse"')
        body+=text(444,131,'PLAY',11,MUTED,mono=True)+path('M426 141h43m-7-5 7 5-7 5',MINT,1.5,extra='class="anim pulse"')
    elif key=='dim3':
        # A procedural point-cloud sculpture; illustrative, never represented as a trained model result.
        cloud=[]
        for i in range(19):
            theta=math.pi*(i+.5)/19
            for j in range(25):
                phi=2*math.pi*j/25
                r=43*(1+.17*math.cos(3*theta))
                x=r*math.sin(theta)*math.cos(phi)
                y=r*math.sin(theta)*math.sin(phi)
                z=67*math.cos(theta)
                px,py=project3(x,y,z,321,147,1.05)
                cloud.append((y,px,py))
        for depth,x,y in sorted(cloud):
            body+=circle(x,y,1.6,accent,extra=f'opacity="{.35+(depth+50)/160:.2f}"')
        body+=f'<g class="anim scan">{path("M239 146L321 108 404 146 321 184Z",MINT,1.2)}<ellipse cx="321" cy="146" rx="82" ry="38" fill="{MINT}" opacity=".035"/></g>'
        for side in [-1,1]:
            body+=path(f'M{321+side*128} 93v103M{321+side*119} 93h{-side*9}M{321+side*119} 196h{-side*9}',LINE)
        body+=text(142,225,'MESH',12,MUTED,mono=True)+text(441,225,'FEATURES',12,MUTED,mono=True)
        body+=path('M181 138h50m182 0h50',MUTED,1,extra='class="anim flow"')
    elif key=='graphics':
        body+=f'<rect x="136" y="65" width="370" height="163" rx="9" fill="{BG}" stroke="{LINE}"/>'
        body+=path('M136 92H506',LINE)
        for i,c in enumerate([AMBER,LILAC,MINT]):body+=circle(151+i*14,79,3,c)
        body+=text(345,83,'sound.py',11,MUTED,mono=True)
        for i in range(37):
            height=13+54*abs(math.sin(i*.35)*math.cos(i*.13))
            body+=f'<rect class="anim eq" x="{158+i*9}" y="{191-height:.2f}" width="4" height="{height:.2f}" rx="2" fill="{MINT if i<25 else LILAC}" style="animation-delay:-{(i%7)*.23:.2f}s"/>'
        body+=text(158,214,'♫  audio engine / merged upstream',12,MUTED,mono=True)
    elif key=='ironic':
        # Original animated line-art interpretation of Ironic’s Pixie Boots mascot.
        body+='''<style>
.bear-left{animation:bear-left 4.8s ease-in-out infinite;transform-origin:286px 136px}
.bear-right{animation:bear-right 4.8s ease-in-out infinite;transform-origin:354px 136px}
@keyframes bear-left{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(12deg)}}
@keyframes bear-right{0%,100%{transform:rotate(5deg)}50%{transform:rotate(-12deg)}}
</style>'''
        body+=f'<ellipse cx="320" cy="198" rx="77" ry="9" fill="{LILAC}" opacity=".07"/>'
        for x in [291,349]:body+=circle(x,83,10,PANEL,extra=f'stroke="{AMBER}" stroke-width="1.8"')+circle(x,83,4,AMBER)
        body+=f'<path d="M289 124C277 132 278 169 286 187Q290 200 306 199H334Q350 200 354 187C362 169 363 132 351 124Z" fill="{PANEL}" stroke="{MINT}" stroke-width="2"/>'
        body+=f'<ellipse cx="320" cy="158" rx="17" ry="25" fill="{BG}" stroke="{AMBER}" stroke-width="1.7"/>'
        body+=f'<path d="M281 103Q281 72 320 73Q359 72 359 103V116Q356 132 340 136H300Q284 132 281 116Z" fill="{PANEL}" stroke="{MINT}" stroke-width="2"/>'
        for x in [306,334]:
            body+=f'<rect x="{x-7}" y="94" width="14" height="18" rx="5" fill="{WHITE}" stroke="{BG}" stroke-width="1.4"/>'+circle(x,103,3,BG)
        body+=path('M296 92l16 -4M344 92l-16 -4',AMBER,2)
        body+=f'<ellipse cx="320" cy="117" rx="13" ry="10" fill="{AMBER}" stroke="{BG}" stroke-width="1.5"/>'+circle(320,114,3,BG)
        body+=path('M320 117v5m-6 0q6 5 12 0',BG,1.5)
        body+=f'<g class="anim bear-left">{path("M287 136q-14 3-20 15l-10-4",MINT,3)}{circle(257,147,5,PANEL,extra=f"stroke={chr(34)}{AMBER}{chr(34)} stroke-width={chr(34)}2{chr(34)}")}{path("M254 144l-8-13",AMBER,2)}{circle(244,128,3,AMBER)}</g>'
        body+=f'<g class="anim bear-right">{path("M353 136q14 3 20 15l10-4",MINT,3)}{circle(383,147,5,PANEL,extra=f"stroke={chr(34)}{AMBER}{chr(34)} stroke-width={chr(34)}2{chr(34)}")}{path("M386 144l8-13",AMBER,2)}{circle(396,128,3,AMBER)}</g>'
        for x in [303,337]:body+=f'<ellipse cx="{x}" cy="194" rx="12" ry="6" fill="{PANEL}" stroke="{AMBER}" stroke-width="1.5"/>'
        body+=text(115,148,'OPENSTACK',12,MUTED,mono=True)+path('M195 145h25',LINE)
        body+=text(434,148,'BARE METAL',12,MUTED,mono=True)+path('M419 145h10',LINE)
    elif key=='cofactor':
        for x in [178,320,462]:
            body+=path(f'M320 102L{x} 155M{x} 172l-29 40M{x} 172l29 40',accent,1.2,extra='class="anim flow" opacity=".6"')
            for dx in [-29,29]:body+=circle(x+dx,218,4,accent)
        for x,y,label,w in [(320,85,'3 × 3',108),(178,162,'2 × 2',88),(320,162,'2 × 2',88),(462,162,'2 × 2',88)]:
            body+=f'<rect x="{x-w/2}" y="{y-23}" width="{w}" height="46" rx="7" fill="{PANEL}" stroke="{LINE}"/>'
            body+=text(x,y+7,label,20,accent,600,mono=True,extra='text-anchor="middle"')
        body+=text(501,102,'O(n!)',17,MUTED,mono=True)
    return body


def project_card(project,mobile=False):
    key,number,category,title,lines,stack,accent=project
    if key in ['uav','magsim']:
        w,h=(600,720) if mobile else (1200,600 if key=='uav' else 540)
        body=frame(w,h)
        body+=text(28 if mobile else 34,41,number+' / '+category,16 if mobile else 15,accent,mono=True)
        body+=text(28 if mobile else 32,99,title,38 if mobile else 42,WHITE,700)
        body+=text(28 if mobile else 34,142,'Ten modules. Three structures. Reconfigure.' if key=='uav' else 'Pulse the coil. Switch the core. Keep the state.',23 if mobile else 22,MUTED)
        if key=='uav':
            body+=swarm(300 if mobile else 422,340 if mobile else 330,23 if mobile else 28)
            for idx,kind in enumerate(['delta','spine','pyramid']):
                ox=100+idx*200 if mobile else 1000
                oy=582 if mobile else 220+idx*125
                sc=6 if mobile else 10
                body+=f'<g transform="translate({ox} {oy}) scale({sc})">'
                for i,(x,y) in enumerate(formation(kind)):
                    glyph=dodecahedron(SWARM_COLORS[i]).replace('class="anim spin"','')
                    body+=f'<g transform="translate({x} {y})">{glyph}</g>'
                body+='</g>'+text(ox,oy+42 if mobile else oy+48,kind.upper(),17 if mobile else 13,MUTED,mono=True,extra='text-anchor="middle"')
            body+=path('M28 520H572' if mobile else 'M818 160V530',LINE)
        else:
            body+=f'<g transform="translate({-14 if mobile else 350} {180 if mobile else 145}) scale({.95 if mobile else 1.3})">{magnetics()}</g>'
            steps=[('01 / DRIVE A PULSE','Coil current creates a field.'),('02 / SWITCH THE CORE','Reverse the Alnico magnetization.'),('03 / HOLD THE STATE','Current returns to zero; the state stays.')]
            for i,(heading,description) in enumerate(steps):
                y=490+i*52 if mobile else 230+i*95
                body+=text(28 if mobile else 34,y,heading,19,accent,mono=True)
                body+=text(28 if mobile else 34,y+27,description,21 if mobile else 17,MUTED)
        body+=path(f'M28 {h-54}H{w-28}',LINE)
        body+=text(28,h-25,stack,16 if mobile else 14,accent,mono=True)+text(w-52,h-24,'↗',24,accent)
        return svg(w,h,title,body,' '.join([category,*lines,stack]))
    if key=='ugv':
        w,h=(600,1080) if mobile else (1200,720)
        body=frame(w,h)
        body+=text(28 if mobile else 34,41,number+' / RESEARCH / ACTIVE PERCEPTION',16 if mobile else 15,MINT,mono=True)
        if mobile:
            body+=text(28,99,'Active vertical',38,WHITE,700)+text(28,144,'perception',38,WHITE,700)
            body+=text(28,187,'A Jackal. A 1.5 m lift. Two gimbals.',23,MUTED)
        else:
            body+=text(32,97,'Active vertical perception',42,WHITE,700)
            body+=text(34,132,'A Jackal, a vertical stage, and two three-axis camera gimbals.',21,MUTED)
        body+=jackal_blueprint(mobile)
        y=1035 if mobile else 640
        body+=path(f'M28 {y}H{w-28}',LINE)
        body+=text(28,y+29,'ROS 2 / GAZEBO' if mobile else 'PYTHON / ROS 2 + GAZEBO',17 if mobile else 14,MINT,mono=True)
        body+=text(w-52,y+30,'↗',24,MINT)
        return svg(w,h,'Active vertical perception — mechanical blueprint',body,
                   'An exploded orthographic study based on the official Clearpath J100 chassis mesh, the project’s actual rear-deck bracket CAD, and its FPB30 and C-200T joint definitions. The full system, three-axis camera gimbal, and deck interface are shown. Simulation geometry, not a manufacturing drawing.')
    if key=='review':
        w,h=(600,470) if mobile else (1200,300)
        body=frame(w,h)
        body+=text(28 if mobile else 34,41,number+' / RESEARCH / REVIEW IN PREPARATION',15 if mobile else 14,AMBER,mono=True)
        if mobile:
            body+=text(28,94,'Electropermanent',36,WHITE,700)+text(28,135,'magnets',36,WHITE,700)
            body+=text(28,177,'Physics. Models. Devices. Applications.',23,MUTED)
            body+=f'<g transform="translate(-18 200) scale(.82)">{project_scene(key,accent)}</g>'
            body+=text(28,440,'TEX / REVIEW IN PREPARATION',17,AMBER,mono=True)
        else:
            body+=text(30,108,'Electropermanent magnets',39,WHITE,700)
            body+=text(34,156,'Physics. Models. Devices. Applications.',22,MUTED)
            body+=text(34,194,'A review of the literature behind magnetic mechanisms.',20,MUTED)
            body+=text(34,263,'TEX / MANUSCRIPT IN PREPARATION',14,AMBER,mono=True)
            body+=f'<g transform="translate(700 21) scale(.9)">{project_scene(key,accent)}</g>'
        body+=text(w-52,h-30,'↗',24,AMBER)
        return svg(w,h,title,body,'LaTeX review of electropermanent magnets: physics, modeling, devices, and applications. Manuscript in preparation, not peer reviewed.')
    if mobile:
        body=frame(300,470)
        body+=text(18,35,number+' / '+category.split(' / ')[0].replace('SENIOR HONORS THESIS','THESIS').replace('UPSTREAM CONTRIBUTOR','UPSTREAM'),12,accent,mono=True)
        body+=f'<g transform="translate(-10 25) scale(.50)">{project_scene(key,accent)}</g>'
        mobile_title={'uav':'Modular Multi-UAV','review':'EPM review','r36s':'CMU games on R36S','arcade':'Campus arcade','logic':'Logic gates','salem':'Salem’s Adventure','opencode':'17-313 project','ironic':'OpenStack Ironic'}.get(key,title)
        for i,line in enumerate(textwrap.wrap(mobile_title,15,break_on_hyphens=False)):
            body+=text(18,225+i*37,line,32,WHITE,700,extra='letter-spacing="-1"')
        short={
            'uav':['Aerial docking.','Shared flight.','Two simulators.'],
            'magsim':['Magnet forces.','EPM switching.','A web interface.'],
            'ugv':['A camera mast.','A greenhouse.','A better view.'],
            'review':['Physics. Models.','Devices. Uses.','Review in prep.'],
            'dim3':['3D geometry.','Many forms.','One pipeline.'],
            'graphics':['Audio rewrite.','Resizing fixes.','Merged upstream.'],
            'r36s':['Python games.','Real buttons.','Handheld play.'],
            'arcade':['Real controls.','Campus games.','Kept running.'],
            'logic':['Wire a circuit.','Flip the inputs.','See the logic.'],
            'salem':['Qatar, two eras.','A time portal.','An arcade story.'],
            'opencode':['A team project.','A real codebase.','17-313.'],
            'ironic':['Real servers.','Bare-metal APIs.','Summer of Code.'],
            'cofactor':['Small matrices.','Big recursion.','Algorithm costs.']}
        for i,line in enumerate(short[key]):body+=text(18,323+i*33,line,26,MUTED)
        body+=path('M18 420H282',LINE)
        body+=text(18,450,{'cofactor':'SML / PYTHON','review':'TEX','opencode':'TYPESCRIPT'}.get(key,'PYTHON'),17,accent,mono=True)
        body+=text(256,451,'↗',25,accent)
        return svg(300,470,title,body,' '.join([category,*lines,stack]))
    body=frame(640,405)
    body+=text(26,35,number+' / '+category,13,accent,mono=True)
    body+=project_scene(key,accent)
    body+=path('M26 247H614',LINE)
    body+=text(26,289,title,32,WHITE,700,extra='letter-spacing="-.8"')
    for i,line in enumerate(lines):body+=text(26,324+i*27,line,19,MUTED)
    body+=text(26,385,stack,13,accent,mono=True)
    body+=text(587,386,'↗',25,accent)
    return svg(640,405,title,body,' '.join([category,*lines,stack]))


def activity(data,mobile=False):
    from orbital_activity import category, category_totals, CATEGORIES, render_orbits
    extras_path=ROOT/'data/public-extras.json'
    extras=json.loads(extras_path.read_text()) if extras_path.exists() else []
    repos=sorted(data['repos']+extras,key=lambda r:(r['pushed_at'],r['name']),reverse=True); palette=dict(CATEGORIES)
    recent_names={
        'epm-review':'epm-review', 'magsim':'magsim',
        'Active_Vertical_Perception_System_UGV':'Active vertical perception',
        'Modular_Multi_UAV_Systems':'Modular Multi-UAV Systems',
        'r36s_handheld_console':'R36S handheld console',
    }
    description=(f"{len(repos)} public repositories. One orbiting satellite per repo; rings indicate original repositories, moons indicate forks, and marker count encodes authored commits on the default branch. "
                 'Colors show curated project categories: research, graphics, coursework, notes, and other. '
                 'More recent pushes have smaller orbital radii, measured at the saved snapshot. '
                 'The three most recently pushed repositories stay named in a separate ledger. '
                 f"Snapshot {data['snapshot_at'][:10]}. Reduced motion shows fixed satellite positions.")
    def mark_example(x, y, count):
        result=circle(x,y,5,MINT)
        for i in range(count):
            result+=f'<ellipse cx="{x}" cy="{y}" rx="{9+i*3}" ry="{4+i*1.5}" fill="none" stroke="{MINT}" stroke-width=".8" transform="rotate(-25 {x} {y})"/>'
        result+=circle(x+42,y,5,LILAC)
        for i in range(count):
            angle=2*math.pi*i/count
            result+=circle(x+42+10*math.cos(angle),y+10*math.sin(angle),1.8,LILAC)
        return result

    if mobile:
        body=frame(600,1170)
        body+=text(28,48,'REPOSITORY CONSTELLATION',20,MINT,mono=True)
        body+=text(28,119,str(len(repos)).zfill(2),64,WHITE,700)
        body+=text(144,92,'public repositories',24,WHITE,600)
        body+=text(144,128,'originals + forks',20,MUTED)
        body+=render_orbits(repos,data['snapshot_at'],300,296,98,225,.49,True)
        body+=path('M28 427H572',LINE)
        body+=text(28,458,'RECENTLY PUSHED',15,MUTED,mono=True)
        for i,repo in enumerate(repos[:3]):
            y=496+i*72
            name=recent_names.get(repo['name'],repo['name'].replace('_',' ').replace('-',' '))
            body+=circle(35,y-7,4,palette[category(repo)])
            body+=text(52,y,textwrap.shorten(name,32,placeholder='…'),24,WHITE,600)
            body+=text(52,y+29,repo['pushed_at'][:10],18,MUTED,mono=True)
        body+=path('M28 689H572',LINE)
        body+=text(28,725,'CONSTELLATION KEY',18,MINT,mono=True)
        for i,(name,count,color) in enumerate(category_totals(repos)):
            x=[28,205,392][i%3]; y=758+(i//3)*30
            body+=circle(x+4,y-5,4,color)+text(x+17,y,f'{name} {count}',16,WHITE,mono=True)
        x=31
        for radius in [3,4.3,5.6,6.9,8.2,9.5,10.8,12]:
            x+=radius
            body+=circle(x,829,radius,MUTED)
            x+=radius+13
        body+=text(28,865,'LARGER PLANET = MORE SOURCE CODE',15,MUTED,mono=True)
        body+=circle(40,907,5,MINT)+f'<ellipse cx="40" cy="907" rx="10" ry="5" fill="none" stroke="{MINT}"/>'
        body+=text(59,913,'ORIGINALS HAVE RINGS',15,MUTED,mono=True)
        body+=circle(325,907,5,LILAC)+circle(335,902,1.8,LILAC)
        body+=text(345,913,'FORKS HAVE MOONS',15,MUTED,mono=True)
        body+=text(28,957,'RINGS OR MOONS / COMMITS',15,MUTED,mono=True)
        body+=text(28,980,'ON THE DEFAULT BRANCH',14,MUTED,mono=True)
        for x,count,label in [(70,1,'1–4'),(250,2,'5–19'),(430,3,'20+')]:
            body+=mark_example(x,1020,count)
            body+=path(f'M{x+21} 1040V1053',LINE)
            body+=text(x+21,1075,label,16,WHITE,mono=True,extra='text-anchor="middle"')
        body+=text(28,1110,'MORE RECENT ACTIVITY = SMALLER ORBIT',14,MUTED,mono=True)
        body+=text(28,1140,'SNAPSHOT / '+data['snapshot_at'][:10]+' UTC',14,MUTED,mono=True)
        return svg(600,1170,'Public repository constellation — orbital activity',body,description)
    body=frame(1200,550)
    body+=text(34,46,'REPOSITORY CONSTELLATION',17,MINT,mono=True,extra='letter-spacing="1"')
    body+=text(34,119,str(len(repos)).zfill(2),62,WHITE,700)
    body+=text(131,91,'public repositories',23,WHITE,600)
    body+=text(131,124,'originals + forks',17,MUTED)
    body+=text(34,173,'RECENTLY PUSHED',13,MUTED,mono=True)
    for i,repo in enumerate(repos[:3]):
        y=211+i*55
        name=recent_names.get(repo['name'],repo['name'].replace('_',' ').replace('-',' '))
        body+=circle(40,y-6,3.5,palette[category(repo)])
        body+=text(54,y,textwrap.shorten(name,31,placeholder='…'),18,WHITE,600)
        body+=text(54,y+22,repo['pushed_at'][:10],12,MUTED,mono=True)
    body+=path('M475 82V350',LINE)
    body+=render_orbits(repos,data['snapshot_at'],837,200,110,270,.48)
    body+=path('M34 370H1166',LINE)
    body+=text(34,400,'CONSTELLATION KEY',14,MINT,mono=True)
    body+=text(1166,400,'SNAPSHOT / '+data['snapshot_at'][:10]+' UTC',11,MUTED,mono=True,extra='text-anchor="end"')
    x=34
    for name,count,color in category_totals(repos):
        body+=circle(x,430,4,color)
        value=f'{name} {count}'
        body+=text(x+12,435,value,13,WHITE,mono=True)
        x+=len(value)*7.85+38
    x=34
    for radius in [3,4.3,5.6,6.9,8.2,9.5,10.8,12]:
        x+=radius
        body+=circle(x,480,radius,MUTED)
        x+=radius+13
    body+=text(34,518,'LARGER PLANET = MORE SOURCE CODE',11,MUTED,mono=True)
    body+=circle(345,480,5,MINT)+f'<ellipse cx="345" cy="480" rx="10" ry="5" fill="none" stroke="{MINT}"/>'
    body+=text(362,484,'ORIGINALS HAVE RINGS',11,MUTED,mono=True)
    body+=circle(345,515,5,LILAC)+circle(355,510,1.8,LILAC)
    body+=text(362,519,'FORKS HAVE MOONS',11,MUTED,mono=True)
    body+=text(610,435,'RINGS OR MOONS / COMMITS ON THE DEFAULT BRANCH',10,MUTED,mono=True)
    for x,count,label in [(625,1,'1–4'),(720,2,'5–19'),(815,3,'20+')]:
        body+=mark_example(x,476,count)
        body+=path(f'M{x+21} 495V500',LINE)
        body+=text(x+21,518,label,13,WHITE,mono=True,extra='text-anchor="middle"')
    body+=f'<ellipse cx="1035" cy="478" rx="68" ry="26" fill="none" stroke="{MUTED}" stroke-width=".8" opacity=".35"/>'
    body+=f'<ellipse cx="1035" cy="478" rx="36" ry="14" fill="none" stroke="{MINT}" stroke-width=".9" opacity=".65"/>'
    body+=circle(1035,478,3,MUTED)+circle(1071,478,4,MINT)+circle(967,478,3,MUTED)
    body+=text(1035,518,'MORE RECENT ACTIVITY = SMALLER ORBIT',9,MUTED,mono=True,extra='text-anchor="middle"')
    return svg(1200,550,'Public repository constellation — orbital activity',body,description)



def footer(mobile=False):
    w,h=(600,170) if mobile else (1200,135)
    body=frame(w,h)
    body+=text(28,52,'STILL CURIOUS. STILL BUILDING.',20 if mobile else 24,MINT,600,mono=True)
    body+=text(28,93,'Robots, open source, games, and good food.',19 if mobile else 22,MUTED)
    if not mobile:
        body+=path('M851 75h46l16-22 21 44 25-49 20 27h175',MINT,2,extra='class="anim flow"')
    else:body+=path('M28 137h160l12-15 16 28 17-32 16 19h319',MINT,1.5,extra='class="anim flow"')
    return svg(w,h,'Still curious. Still building.',body)


def chaos_shell(mobile=False, quiet=False):
    w,h=(600,510) if mobile else (1200,330)
    body=frame(w,h)
    if mobile:
        body+=text(28,43,'A SMALL CHAOS EXPERIMENT',18,LILAC,mono=True)
        body+=text(26,97,'Almost the same.',40,WHITE,700,extra='letter-spacing="-1"')
        body+=text(26,146,'Until it isn’t.',40,MINT,700,extra='letter-spacing="-1"')
        ox,oy,scale=300,320,70
        body+=text(28,488,'GENTLE RELEASE / 18°' if quiet else 'NEARBY STARTS / 120°',18,MUTED,mono=True)
    else:
        body+=text(35,43,'CHAOS / A SMALL PHYSICS DETOUR',15,LILAC,mono=True)
        body+=text(31,116,'Almost the same.',43,WHITE,700,extra='letter-spacing="-1"')
        body+=text(31,169,'Until it isn’t.',43,MINT,700,extra='letter-spacing="-1"')
        body+=text(35,219,'Same equations. Different futures.',20,MUTED)
        body+=text(35,289,'GENTLE RELEASE / 18°' if quiet else 'NEARBY STARTS / 120°',14,MUTED,mono=True)
        ox,oy,scale=920,165,68
    body+=f'<g transform="translate({ox} {oy}) scale({scale})"><!-- PENDULUM_ART --></g>'
    return svg(w,h,'Double pendulum: tiny differences, different futures',body,
               'Original numerical double-pendulum animation. Equal masses and lengths, released from rest with lower-arm angles spread across one millionth of a degree. Real RK4 trajectories. Motion freezes to a representative frame with reduced-motion preference.')


def build():
    ASSETS.mkdir(exist_ok=True)
    build_notes(ASSETS)
    for mobile in [False,True]:
        suffix='-mobile' if mobile else ''
        (ASSETS/f'hero{suffix}.svg').write_text(hero(mobile),encoding='utf-8')
        for project in PROJECTS:
            (ASSETS/f'project-{project[0]}{suffix}.svg').write_text(project_card(project,mobile),encoding='utf-8')
        (ASSETS/f'footer{suffix}.svg').write_text(footer(mobile),encoding='utf-8')
        snapshot=ROOT/'data/public-activity.json'
        if snapshot.exists():
            (ASSETS/f'activity{suffix}.svg').write_text(activity(json.loads(snapshot.read_text()),mobile),encoding='utf-8')


if __name__=='__main__':
    build()
