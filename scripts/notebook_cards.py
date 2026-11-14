"""Draw the six linked notebook covers, including a dedicated phone composition."""

import math
from functools import lru_cache
from html import escape
from pathlib import Path

BG, PANEL, LINE = '#090e1b', '#121c2e', '#2a3a50'
WHITE, MUTED, MINT, AMBER, LILAC = '#edf5f1', '#a8bcc8', '#91f2cc', '#ffc183', '#b5a4ff'

NOTES = [
    ('calculus', 'Integration & approximation', ['Integration &', 'approximation'],
     ['Integration', 'approximation'], 'MY NOTES / TEX', MINT),
    ('ml', 'Machine learning in a nutshell', ['Machine learning', 'in a nutshell'],
     ['Machine learning', 'in a nutshell'], 'MY NOTES / TEX', LILAC),
    ('networking', 'Networking & the Internet', ['Networking &', 'the Internet'],
     ['Networking', '& the Internet'], 'MY NOTES / TEX', MINT),
    ('security', 'Security & privacy / 15-316', ['Security & privacy', '15-316'],
     ['Security', '& privacy', '15-316'], 'MY NOTES / TEX', AMBER),
    ('collective', 'Collective intelligence', ['Collective', 'intelligence'],
     ['Collective', 'intelligence'], 'SHARED / FORK', LILAC),
    ('matrices', 'Matrices & linear transformations', ['Matrices & linear', 'transformations'],
     ['Matrices &', 'linear', 'transformations'], 'SHARED / FORK', AMBER),
]


def txt(x, y, value, size=24, color=WHITE, weight=600, mono=False):
    family = 'DejaVu Sans Mono,monospace' if mono else 'DejaVu Sans,Arial,sans-serif'
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{family}" font-size="{size}" font-weight="{weight}">{escape(value)}</text>'


def path(d, color=MINT, width=1.4, extra=''):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def circle(x, y, radius=4, color=MINT, extra=''):
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{BG}" stroke="{color}" stroke-width="1.4" {extra}/>'


@lru_cache(maxsize=1)
def lorenz_orbit():
    """An original RK4 orbit for the Collective Intelligence cover.

    Model and parameters follow Gianni A. Di Caro's 15-382 attractor demo,
    2018–2025 (course source permits reuse with acknowledgment). No plotting
    code or trajectory data from the course materials is copied here.
    """
    def derivative(v):
        x, y, z = v
        return 10*(y-x), x*(28-z)-y, x*y-(8/3)*z

    def step(v, dt):
        a = derivative(v)
        b = derivative(tuple(v[i]+dt*a[i]/2 for i in range(3)))
        c = derivative(tuple(v[i]+dt*b[i]/2 for i in range(3)))
        d = derivative(tuple(v[i]+dt*c[i] for i in range(3)))
        return tuple(v[i]+dt*(a[i]+2*b[i]+2*c[i]+d[i])/6 for i in range(3))

    state, dt = (1.0, 1.0, 1.0), 1/240
    samples = []
    # Discard the initial approach to the attractor, then retain 24 seconds.
    for i in range(32*240+1):
        state = step(state, dt)
        if i >= 8*240 and i % 3 == 0:
            x, y, z = state
            samples.append((.94*x+.34*y, z+.12*y))
    xmin, xmax = min(p[0] for p in samples), max(p[0] for p in samples)
    ymin, ymax = min(p[1] for p in samples), max(p[1] for p in samples)
    # An oblique phase portrait fits the cover's wide illustration window.
    points = [(62+176*(x-xmin)/(xmax-xmin), 131-87*(y-ymin)/(ymax-ymin))
              for x, y in samples]
    d = 'M'+'L'.join(f'{x:.2f},{y:.2f}' for x, y in points)
    length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
    return d, length


def lorenz_illustration():
    d, length = lorenz_orbit()
    duration = 24
    body = f'''<defs>
<path id="lorenz-orbit" d="{d}" pathLength="{length:.3f}"/>
<linearGradient id="lorenz-ink" x1="0" y1="1" x2="1" y2="0"><stop stop-color="{LILAC}"/><stop offset=".5" stop-color="{MINT}"/><stop offset="1" stop-color="{AMBER}"/></linearGradient>
<filter id="lorenz-halo" x="-15%" y="-35%" width="130%" height="170%"><feGaussianBlur stdDeviation=".8"/></filter>
</defs>
<style>
.lorenz-flow{{animation:lorenz-flow {duration}s linear infinite}}
.lorenz-lap{{animation:lorenz-lap {duration}s linear infinite}}
@keyframes lorenz-flow{{from{{stroke-dashoffset:0}}to{{stroke-dashoffset:-{length:.3f}}}}}
@keyframes lorenz-lap{{0%,100%{{opacity:0}}2%,98%{{opacity:1}}}}
@media(prefers-reduced-motion:reduce){{.lorenz-flow,.lorenz-lap{{animation:none!important}}}}
</style>
<use href="#lorenz-orbit" fill="none" stroke="url(#lorenz-ink)" stroke-width="1.2" opacity=".16" filter="url(#lorenz-halo)"/>
<use href="#lorenz-orbit" fill="none" stroke="url(#lorenz-ink)" stroke-width=".55" opacity=".32"/>
'''
    speed = length/duration
    for color, phase in [(MINT, 3.4), (LILAC, 10.1), (AMBER, 18.3)]:
        body += f'<g class="lorenz-lap" style="animation-delay:-{phase}s">'
        # Overlapping short dashes form a tail that fades over eighteen pixels.
        for i in reversed(range(8)):
            delay = phase-(i+1)*2.15/speed
            opacity = .68*(1-i/8)**1.6
            body += (f'<use href="#lorenz-orbit" fill="none" stroke="{color}" '
                     f'stroke-width="1.45" stroke-linecap="round" '
                     f'stroke-dasharray="2.8 {length-2.8:.3f}" opacity="{opacity:.3f}" '
                     f'class="lorenz-flow" style="animation-delay:-{delay:.5f}s;stroke-dashoffset:-{speed*delay:.3f}"/>')
        body += (f'<use href="#lorenz-orbit" fill="none" stroke="{WHITE}" '
                 f'stroke-width="2.4" stroke-linecap="round" '
                 f'stroke-dasharray=".08 {length-.08:.3f}" class="lorenz-flow" '
                 f'style="animation-delay:-{phase}s;stroke-dashoffset:-{speed*phase:.3f}"/>')
        body += '</g>'
    return body


def illustration(key, accent):
    body = ''
    if key == 'calculus':
        body += path('M47 119H253M57 125V43', LINE, 1)
        heights = [23, 38, 50, 57, 55, 44, 30, 19]
        for i, h in enumerate(heights):
            body += f'<rect x="{66+i*21}" y="{119-h}" width="20" height="{h}" fill="{accent}" fill-opacity=".055" stroke="{accent}" stroke-opacity=".35"/>'
        body += path('M66 99C102 37 148 47 178 68S211 112 238 96', accent, 2.4)
        body += path('M66 99C102 37 148 47 178 68S211 112 238 96', WHITE, 1.2, 'class="trace"')
    elif key == 'ml':
        layers = [(81, [64, 88, 112]), (151, [55, 79, 103, 127]), (221, [72, 109])]
        for left, right in zip(layers, layers[1:]):
            for y1 in left[1]:
                for y2 in right[1]:
                    body += path(f'M{left[0]} {y1}L{right[0]} {y2}', accent, 1, 'opacity=".3"')
        for x, ys in layers:
            for y in ys:
                body += circle(x, y, 5, accent)
        body += circle(151, 79, 9, MINT, 'class="breathe"')
    elif key == 'networking':
        coords = [(66, 65), (67, 116), (144, 89), (231, 58), (232, 119)]
        for i, j in [(0, 2), (1, 2), (2, 3), (2, 4)]:
            a, b = coords[i], coords[j]
            body += path(f'M{a[0]} {a[1]}L{b[0]} {b[1]}', accent, 1.8, 'class="packet"')
        for i, (x, y) in enumerate(coords):
            if i == 2:
                body += f'<rect x="{x-17}" y="{y-12}" width="34" height="24" rx="5" fill="{PANEL}" stroke="{accent}"/>'
                body += path(f'M{x-10} {y}h20m-5-4 5 4-5 4', WHITE, 1.3)
            else:
                body += f'<rect x="{x-12}" y="{y-8}" width="24" height="16" rx="3" fill="{PANEL}" stroke="{MUTED}"/>'
                body += path(f'M{x-6} {y+12}h12M{x} {y+8}v4', MUTED, 1)
    elif key == 'security':
        body += f'<path d="M151 46L191 60V86Q190 116 151 131Q112 116 111 86V60Z" fill="{accent}" fill-opacity=".04" stroke="{accent}" stroke-width="1.7"/>'
        body += path('M138 85V76a13 13 0 0 1 26 0v9', MUTED, 1.6)
        body += f'<rect x="132" y="84" width="38" height="26" rx="4" fill="{PANEL}" stroke="{MINT}" stroke-width="1.5"/>'
        body += circle(151, 96, 3, MINT) + path('M151 99v5', MINT, 1.8)
        body += path('M68 89h29m110 0h28', LINE, 1.4)
        body += circle(68, 89, 4, LILAC) + circle(235, 89, 4, MINT)
    elif key == 'collective':
        body += lorenz_illustration()
    elif key == 'matrices':
        for i in range(5):
            body += path(f'M{64+i*21} 120L{94+i*21} 52M64 {120-i*17}l84 -0', LINE, 1)
        body += path('M64 120l84 0m-8-5 8 5-8 5M64 120l30-68m-7 6 7-6 0 10', accent, 2)
        body += path('M187 75h8m-4-4 4 4-4 4', MUTED, 1.4)
        body += path('M216 66h-7v48h7M247 66h7v48h-7', accent, 1.4)
        body += txt(221, 85, 'a b', 12, MUTED, 400, True)
        body += txt(221, 106, 'c d', 12, MUTED, 400, True)
    return body


def note_svg(note, mobile=False):
    key, title, desktop_lines, phone_lines, credit, accent = note
    h = 360 if mobile else 250
    lines = phone_lines if mobile else desktop_lines
    size = 32 if mobile else 24
    if mobile and key == 'ml':
        lines = ['Machine', 'learning', 'in a nutshell']
    if mobile and key == 'matrices':
        size = 29
    y = 196 if mobile else 163
    leading = 38 if mobile else 29
    body = f'<rect x="1" y="1" width="298" height="{h-2}" rx="16" fill="url(#silk)" stroke="{LINE}"/>'
    body += f'<g clip-path="url(#clip)"><ellipse cx="281" cy="{h*.75}" rx="215" ry="185" fill="url(#aura)"/>'
    for i in range(5):
        body += path(f'M{90+i*24} {h}C{240+i*18} {h*.62} {170+i*22} {h*.37} 300 {26+i*18}', accent, .65, 'opacity=".065"')
    body += f'<rect x="1" y="1" width="298" height="{h-2}" fill="{WHITE}" filter="url(#grain)" opacity=".02"/></g>'
    body += txt(18, 29, 'SHARED NOTEBOOK' if credit.startswith('SHARED') else 'COURSE NOTES', 12 if not mobile else 14, accent, 400, True)
    body += illustration(key, accent)
    for i, value in enumerate(lines):
        body += txt(18, y+i*leading, value, size)
    body += path(f'M18 {h-48}H282', LINE, 1)
    body += txt(18, h-21, credit, 12 if not mobile else 17, accent, 400, True)
    body += txt(263, h-20, '↗', 20 if not mobile else 24, accent)
    description = title+'. '+('Collaborative notebook fork.' if credit.startswith('SHARED') else 'My course notes.')
    if key == 'collective':
        description += (' Original numerical Lorenz attractor with short fading tracers. '
                        'Sigma 10, rho 28, beta 8/3. Model and parameters follow '
                        'Gianni A. Di Caro’s 15-382 course demonstration, 2018–2025.')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="{h}" viewBox="0 0 300 {h}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<style>.trace{{stroke-dasharray:8 180;animation:trace 7s linear infinite}}.packet{{stroke-dasharray:3 7;animation:packet 5s linear infinite}}.breathe{{animation:breathe 5s ease-in-out infinite}}@keyframes trace{{to{{stroke-dashoffset:-188}}}}@keyframes packet{{to{{stroke-dashoffset:-100}}}}@keyframes breathe{{0%,100%{{opacity:.35}}50%{{opacity:.9}}}}@media(prefers-reduced-motion:reduce){{.trace,.packet,.breathe{{animation:none!important}}}}</style>
<defs>
<linearGradient id="silk" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#11182c"/><stop offset=".5" stop-color="{BG}"/><stop offset="1" stop-color="#0b1b25"/></linearGradient>
<radialGradient id="aura"><stop stop-color="{accent}" stop-opacity=".1"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
<clipPath id="clip"><rect x="1" y="1" width="298" height="{h-2}" rx="16"/></clipPath>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".72" numOctaves="3" stitchTiles="stitch" seed="7"/><feColorMatrix type="saturate" values="0"/></filter>
</defs>{body}</svg>\n'''


def build_notes(assets: Path):
    assets.mkdir(exist_ok=True)
    for note in NOTES:
        for mobile in [False, True]:
            suffix = '-mobile' if mobile else ''
            (assets/f'note-{note[0]}{suffix}.svg').write_text(note_svg(note, mobile), encoding='utf-8')


if __name__ == '__main__':
    build_notes(Path(__file__).resolve().parents[1]/'assets')
