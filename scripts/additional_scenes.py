"""Original, script-free illustrations for the profile's classroom and team projects.

Each fragment fits the 640-wide project card's illustration area. The parent SVG
provides the palette background and reduced-motion rule for all ``anim`` classes.
"""

from html import escape

BG, PANEL, LINE = '#090e1b', '#121c2e', '#2a3a50'
WHITE, MUTED, MINT, AMBER, LILAC = '#edf5f1', '#a8bcc8', '#91f2cc', '#ffc183', '#b5a4ff'


def _path(d, color=LINE, width=1, extra=''):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def _text(x, y, text, size=11, color=MUTED, extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-family="DejaVu Sans Mono,monospace" {extra}>{escape(text)}</text>'


def _circle(x, y, r, fill=MINT, extra=''):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" {extra}/>'


def _polygon(points, fill=PANEL, stroke=LINE, extra=''):
    return f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-linejoin="round" {extra}/>'


def arcade(accent):
    """Symmetric cabinet front elevation, with all hardware centered on x=320."""
    body=f'<ellipse cx="320" cy="237" rx="91" ry="3" fill="{BG}" opacity=".6"/>'
    # A shallow side gives the cabinet depth while retaining a centered front. The
    # rectangular upper cabinet and pedestal meet at a projecting control shelf.
    body+=_polygon('382,58 407,69 407,153 419,164 419,190 403,187 399,243 378,234 378,175 394,175 394,145 382,145',BG,LINE,extra='stroke-width="1.2"')
    body+=_path('M382 58l25 11M382 145l25 8M394 175l25 15M378 234l21 9',LINE,.9)
    body+=f'<path d="M258 58H382V145H394V175H378V234H262V175H246V145H258Z" fill="{PANEL}" stroke="{accent}" stroke-width="1.5" stroke-linejoin="round"/>'
    body+=_path('M263 63V142M377 63V142M267 178V229M373 178V229',LINE,.9)
    body+=f'<rect x="266" y="65" width="108" height="19" rx="1" fill="{BG}" stroke="{LINE}"/>'
    body+=_text(320,78,'15-112',10,accent,'text-anchor="middle" letter-spacing="1.2"')
    # The bezel and display are true rectangles with a shared centerline.
    body+=f'<rect x="269" y="90" width="102" height="51" rx="2" fill="{BG}" stroke="{MUTED}" stroke-width="1.1"/>'
    body+=f'<rect x="274" y="95" width="92" height="41" rx="1" fill="{PANEL}" stroke="{LINE}"/>'
    body+=_path('M280 128h14v-8h17v8h18v-14h30',MINT,1.4)
    body+=_circle(302,106,2.5,AMBER)
    body+=_path('M279 99h5M356 99h5',LINE,.7)
    # Two small speaker grilles sit between the marquee and bezel.
    for x in [279,356]:body+=_path(f'M{x} 87h5',MUTED,.7)
    body+=f'<rect x="248" y="147" width="144" height="25" rx="1" fill="{BG}" stroke="{LINE}"/>'
    body+=_path('M247 174H393',accent,.9)
    # Including the buttons, the two control stations span 272.5..367.5,
    # exactly centered under the 269..371 screen at x=320.
    for x in [280.5,342.5]:
        body+=f'<ellipse cx="{x}" cy="165" rx="8" ry="2.4" fill="{PANEL}" stroke="{MUTED}" stroke-width=".8"/>'
        body+=_path(f'M{x} 163v-10',MUTED,2)
        body+=_circle(x,152,3.5,AMBER if x<320 else LILAC)
        for dx,dy in [(14,0),(22,1),(18,7)]:
            body+=_circle(x+dx,158+dy,3,accent)
    # Coin/access door, lock, fasteners, ventilation, and toe kick.
    body+=f'<rect x="290" y="183" width="60" height="36" rx="2" fill="{BG}" stroke="{LINE}"/>'
    body+=f'<rect x="302" y="190" width="15" height="2" rx=".6" fill="{MUTED}"/>'
    body+=_circle(338,197,2.6,BG,extra=f'stroke="{AMBER}" stroke-width=".8"')
    body+=_path('M338 196v2M297 206h31m-31 4h31m-31 4h31M267 226H373',MUTED,.7)
    for x,y in [(262,62),(378,62),(262,141),(378,141),(252,151),(388,151),(252,169),(388,169),(294,187),(346,187),(294,215),(346,215)]:
        body+=_circle(x,y,.8,MUTED)
    # Input controller board and cable routing connect hardware to the cabinet.
    body+=f'<rect x="133" y="111" width="66" height="49" rx="4" fill="{PANEL}" stroke="{LINE}"/>'
    body+=f'<rect x="154" y="123" width="24" height="23" rx="2" fill="{BG}" stroke="{accent}"/>'
    for x in [145,151,157,163,169,175,181,187]:
        body+=_path(f'M{x} 107v4M{x} 160v4',MUTED,.8)
    for y in [119,126,133,140,147,154]:
        body+=_path(f'M129 {y}h4M199 {y}h4',MUTED,.8)
    body+=_path('M204 134C224 134 224 159 246 159',accent,1.1,extra='class="anim flow"')
    body+=_text(70,84,'INPUT THROUGH',9,MUTED)+_text(70,99,'RASPBERRY PI PICO RP2040',9,MUTED)
    body+=_path('M414 114H379',LINE,.8)+_text(420,117,'SCREEN',10,MUTED)
    body+=_path('M414 159H398',LINE,.8)+_text(420,162,'CONTROLS',10,MUTED)
    return body


def logic(accent):
    """A conventional XOR symbol with all four consistent input/output states."""
    body='<style>'
    for i in range(4):
        start=i*25;end=(i+1)*25
        frames=(f'0%,{start}%{{opacity:0}}' if start else '0%{opacity:1}')
        if start:frames+=f'{start+.001}%{{opacity:1}}'
        frames+=f'{end}%{{opacity:0}}100%{{opacity:{1 if i==0 else 0}}}'
        body+=f'.logic-state-{i}{{animation:logic-state-{i} 8s steps(1,end) infinite}}@keyframes logic-state-{i}{{{frames}}}'
    body+='</style>'
    body+=_path('M262 95Q312 141 262 187Q339 189 381 141Q339 93 262 95Z',accent,1.8)
    body+=_path('M250 95Q300 141 250 187',accent,1.6)
    body+=_text(320,148,'XOR',17,WHITE,'text-anchor="middle"')
    for i,(a,b) in enumerate([(0,0),(0,1),(1,0),(1,1)]):
        q=a^b
        body+=f'<g class="anim logic-state-{i}" opacity="{1 if i==0 else 0}">'
        for y,v in [(113,a),(169,b)]:
            col=accent if v else MUTED
            body+=_path(f'M176 {y}H269',col,1.7,extra='stroke-dasharray="4 4"' if v else '')
            body+=_circle(169,y,14,BG,extra=f'stroke="{col}" stroke-width="1.2"')
            body+=_text(169,y+5,str(v),16,col,'text-anchor="middle"')
        col=MINT if q else MUTED
        body+=_path('M381 141H455',col,1.8,extra='stroke-dasharray="4 4"' if q else '')
        body+=_circle(468,141,17,BG,extra=f'stroke="{col}" stroke-width="1.5"')
        body+=_text(468,147,str(q),19,col,'text-anchor="middle"')
        body+=_text(320,224,f'{a} ⊕ {b} = {q}',15,col,'text-anchor="middle"')
        body+='</g>'
    body+=_text(141,81,'INPUTS',10,MUTED)+_text(442,81,'OUTPUT',10,MUTED)
    return body


def salem(accent):
    """An original time-travel storyboard, rather than copied game imagery."""
    body='''<style>
.salem-clock{transform-origin:320px 143px;animation:salem-clock 12s linear infinite}
@keyframes salem-clock{to{transform:rotate(-360deg)}}
.salem-page{animation:salem-page 8s ease-in-out infinite}
@keyframes salem-page{0%,100%{opacity:.45}40%,65%{opacity:1}}
</style>'''
    body+=_path('M132 214H507',LINE,.8)
    # Two manuscript panels frame the portal. The left is a contemporary city;
    # the right an original traditional Gulf courtyard elevation.
    body+=f'<rect x="139" y="84" width="111" height="116" rx="3" fill="{BG}" stroke="{LINE}"/>'
    body+=_path('M147 184h95M151 184v-38l12-16 12 16v38m7 0v-66l9-10 9 10v66m9 0v-45h21v45',MUTED,1.1)
    for x in [156,163,170,187,194,216,223]:
        for y in [153,162,171]:body+=_path(f'M{x} {y}h2',accent,.8)
    body+=_text(194,220,'PRESENT',10,MUTED,'text-anchor="middle"')
    body+=f'<rect x="390" y="84" width="111" height="116" rx="3" fill="{BG}" stroke="{LINE}"/>'
    body+=_path('M398 184h95M401 184v-52h88v52M405 132v-18h8v18m5 0v-18h8v18m5 0v-18h8v18m5 0v-18h8v18m5 0v-18h8v18m5 0v-18h8v18',AMBER,1.1)
    body+=_path('M433 184v-27q12-21 24 0v27M407 146h12v16h-12zM471 146h12v16h-12z',MUTED,1.1)
    body+=_text(445,220,'PAST',10,MUTED,'text-anchor="middle"')
    # The arch and mechanical clock refer to the story's time-travel premise.
    body+=f'<path d="M271 199V117Q271 79 320 58Q369 79 369 117V199Z" fill="{PANEL}" stroke="{accent}" stroke-width="1.4"/>'
    body+=_path('M280 192V118Q280 87 320 68Q360 87 360 118V192',LINE,1)
    body+=f'<circle cx="320" cy="143" r="34" fill="{BG}" stroke="{AMBER}" stroke-width="1.2"/>'
    body+=f'<circle cx="320" cy="143" r="29" fill="none" stroke="{LINE}" stroke-dasharray="1 5"/>'
    body+='<g class="anim salem-clock">'+_path('M320 143V120M320 143l15 10',AMBER,1.7)+'</g>'
    body+=_circle(320,143,2.5,WHITE)
    body+=_path('M252 154h14m-6-4 6 4-6 4M374 154h14m-6-4 6 4-6 4',accent,1.1,extra='class="anim salem-page"')
    body+=_text(320,221,'A STORY THROUGH TIME',10,accent,'text-anchor="middle"')
    return body


def opencode(accent):
    """A course-fork diff and review diagram, not a fabricated product screenshot."""
    body='''<style>
.review-flow{stroke-dasharray:3 7;animation:review-flow 3s linear infinite}
@keyframes review-flow{to{stroke-dashoffset:-50}}
.review-cursor{animation:review-cursor 1.6s steps(1) infinite}
@keyframes review-cursor{0%,49%{opacity:1}50%,100%{opacity:0}}
</style>'''
    body+=f'<rect x="124" y="65" width="309" height="162" rx="8" fill="{BG}" stroke="{LINE}"/>'
    body+=_path('M124 93H433',LINE)
    for i,c in enumerate([AMBER,LILAC,MINT]):body+=_circle(140+i*13,79,2.5,c)
    body+=_text(203,83,'opencode / course fork',10,MUTED)
    body+=_text(141,114,'diff',11,accent)
    for y,sign,col,lengths in [(134,'−',AMBER,[88,62]),(159,'+',MINT,[116,77]),(184,'+',MINT,[66,109])]:
        body+=_text(141,y,sign,14,col)
        body+=f'<rect x="158" y="{y-7}" width="{lengths[0]}" height="3" rx="1.5" fill="{col}" opacity=".65"/>'
        body+=f'<rect x="{166+lengths[0]}" y="{y-7}" width="{lengths[1]}" height="3" rx="1.5" fill="{MUTED}" opacity=".25"/>'
    body+=_path('M141 211h11',MINT,1.4)
    body+=f'<rect x="157" y="202" width="5" height="12" fill="{MINT}" class="anim review-cursor"/>'
    body+=_path('M433 147H461V118h36M461 147v30h36',accent,1.4,extra='class="anim review-flow"')
    for x,y,c in [(461,147,accent),(497,118,MINT),(497,177,LILAC)]:
        body+=_circle(x,y,8,BG,extra=f'stroke="{c}" stroke-width="1.4"')
        body+=_circle(x,y,2,c)
    body+=_text(453,89,'REVIEW',10,MUTED)
    body+=_text(474,216,'17-313',12,accent)
    return body


def scene(key, accent=MINT):
    """Return the requested project's SVG illustration fragment."""
    renderers={'arcade':arcade,'logic':logic,'salem':salem,'opencode':opencode}
    return renderers[key](accent) if key in renderers else ''
