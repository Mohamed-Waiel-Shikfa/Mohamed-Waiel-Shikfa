"""Public repository satellites: curated categories and snapshot-relative orbits."""

import math
import random
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

MINT, CYAN, AMBER, LILAC, ROSE = '#91f2cc', '#76c7ef', '#ffc183', '#b5a4ff', '#ef9fb9'
CATEGORIES = [
    ('Research', MINT), ('Graphics', CYAN), ('Coursework', AMBER),
    ('Notes', LILAC), ('Other', ROSE),
]
CATEGORY_BY_NAME = {
    'Modular_Multi_UAV_Systems': 'Research',
    'magsim': 'Research',
    'epm-review': 'Research',
    'Active_Vertical_Perception_System_UGV': 'Research',
    'r36s_handheld_console': 'Graphics',
    'Edge-project': 'Graphics',
    'desktop-cmu-graphics': 'Graphics',
    'Dim3': 'Coursework',
    'arcade-box-15112': 'Coursework',
    'Term-project': 'Coursework',
    'Cofactor-Expansion-Research': 'Coursework',
    'Freshmen-Immigration-leetcode-problems': 'Coursework',
    'Integration_And_Approximation_notes': 'Notes',
    'ML_in_a_Nutshell_notes': 'Notes',
    'Networking_and_the_Internet_notes': 'Notes',
    '15316-Notes': 'Notes',
    'collective_intelligence_notes': 'Notes',
    'matrices-notes': 'Notes',
}


def category(repo):
    return CATEGORY_BY_NAME.get(repo['name'], 'Other')


def category_totals(repos):
    counts = Counter(category(repo) for repo in repos)
    return [(name, counts[name], color) for name, color in CATEGORIES if counts[name]]


def orbital_parameters(repos, snapshot_at, inner=87, outer=205):
    """Return radius/period pairs, monotone in age at the committed snapshot.

    Log scaling distinguishes the latest pushes while keeping old repositories
    in view. Periods and radii are a visual encoding, not measured dynamics.
    """
    observed = datetime.fromisoformat(snapshot_at.replace('Z', '+00:00'))
    ages = [max(0, (observed-datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00'))).total_seconds()/86400)
            for repo in repos]
    denominator = math.log1p(max(ages, default=0))
    normalized = [math.log1p(age)/denominator if denominator else 0 for age in ages]
    return [(inner+(outer-inner)*fraction, 48.0) for fraction in normalized]


def source_line_counts(repos, metrics=None):
    """Return measured public source volumes; absent/stale measurements stay unknown."""
    if metrics is None:
        path = Path(__file__).resolve().parents[1]/'data/repo-code-metrics.json'
        metrics = json.loads(path.read_text()) if path.exists() else {}
    if metrics.get('metric') != 'filtered_nonblank_noncomment_source_lines':
        return [None for _ in repos]
    records = metrics.get('repos', {})
    counts = []
    for repo in repos:
        record = records.get(repo['name'], {})
        count = record.get('source_lines')
        valid = (type(count) is int and count >= 0 and record.get('pushed_at') == repo['pushed_at']
                 and isinstance(record.get('head_sha'), str) and len(record['head_sha']) == 40)
        counts.append(count if valid else None)
    return counts


def contributed_commits(repos):
    path=Path(__file__).resolve().parents[1]/'data/repo-contributions.json'
    data=json.loads(path.read_text()) if path.exists() else {}
    if data.get('metric')!='github_authored_commits_on_default_branch':return [None]*len(repos)
    records=data.get('repos',{});out=[]
    for repo in repos:
        item=records.get(repo['name'],{});value=item.get('commits')
        valid=type(value) is int and value>=0 and item.get('pushed_at')==repo['pushed_at'] and len(item.get('head_sha',''))==40
        out.append(value if valid else None)
    return out


def contribution_marks(count):
    if count is None or count==0:return 0
    if count<5:return 1
    if count<20:return 2
    return 3


def satellite_sizes(repos, metrics=None, mobile=False):
    """Area is proportional to source LOC above a 2.8 px visibility floor.

    The largest measured repository has radius 12 px. A hollow 4 px satellite
    indicates an unknown measurement and carries no source-volume claim.
    """
    counts = source_line_counts(repos, metrics)
    maximum = max((count for count in counts if count is not None), default=0)
    scale = 1.15 if mobile else 1
    return [(max(2.8, 12*math.sqrt(count/maximum)) if maximum else 2.8)*scale
            if count is not None else 4*scale for count in counts]


def separated_phases(repos, parameters, sizes, flatten):
    """Pack phase offsets using a conservative bound valid throughout an orbit."""
    radii=[x[0] for x in parameters]
    extents=[size+8.5 for size in sizes]
    phases=[-2.36+i*2.3999632297 for i in range(len(repos))]
    rng=random.Random(28471)
    def pair(i,phase,j):
        d=math.sqrt(radii[i]**2+radii[j]**2-2*radii[i]*radii[j]*math.cos(phase-phases[j]))
        return max(0,extents[i]+extents[j]+1-flatten*d)**2
    for iteration in range(120000):
        i=rng.randrange(len(phases));old=phases[i];new=old+rng.uniform(-.65,.65)
        before=sum(pair(i,old,j) for j in range(len(phases)) if j!=i)
        after=sum(pair(i,new,j) for j in range(len(phases)) if j!=i)
        temp=max(.002,1.8*(1-iteration/120000)**3)
        if after<before or rng.random()<math.exp(min(0,(before-after)/temp)):phases[i]=new
    if any(pair(i,phases[i],j)>1e-7 for i in range(len(phases)) for j in range(i)):
        raise ValueError('Could not place satellites: '+str(max(pair(i,phases[i],j) for i in range(len(phases)) for j in range(i))))
    return phases


def render_orbits(repos, snapshot_at, cx, cy, inner=87, outer=205, flatten=.52, mobile=False):
    """Sample ellipse translations so satellites keep circular, unwarped shapes."""
    counts = source_line_counts(repos)
    sizes = satellite_sizes(repos, mobile=mobile)
    contributions = contributed_commits(repos)
    # Keep the symbols clear of the center as well as one another. If a future
    # source-size distribution is unusually dense, scale all bodies together;
    # their relative areas remain unchanged.
    phases = []
    if repos:
        for factor in (1, .88, .75, .6):
            candidate = [size*factor for size in sizes]
            extent = max(size+8.5 for size in candidate)
            safe_inner = max(inner, (32+extent)/flatten)
            parameters = orbital_parameters(repos, snapshot_at, safe_inner, outer)
            try:
                phases = separated_phases(repos, parameters, candidate, flatten)
                sizes = candidate
                break
            except ValueError:
                continue
        else:
            raise ValueError('Could not find a collision-free constellation layout')
    else:
        parameters = []
    palette = dict(CATEGORIES)
    css = ['.moon-orbit{animation:moon-orbit 8s linear infinite;transform-origin:0 0}@keyframes moon-orbit{to{transform:rotate(360deg)}}@media(prefers-reduced-motion:reduce){.repo-orbiter,.moon-orbit{animation:none!important}}']
    drawing = ''
    # Quiet tracks make individual radii legible without implying dependencies.
    for repo, (radius, _) in zip(repos, parameters):
        drawing += (f'<ellipse cx="0" cy="0" rx="{radius:.3f}" ry="{radius*flatten:.3f}" '
                    f'fill="none" stroke="{palette[category(repo)]}" stroke-width=".7" opacity=".095"/>')
    for fraction in [0, .34, .67, 1]:
        radius = inner+(outer-inner)*fraction
        drawing += (f'<ellipse cx="0" cy="0" rx="{radius:.3f}" ry="{radius*flatten:.3f}" '
                    'fill="none" stroke="#6b8199" stroke-width=".6" opacity=".18"/>')
    for i, (repo, (radius, period)) in enumerate(zip(repos, parameters)):
        phase = phases[i]
        poses = []
        for frame in range(73):
            angle = phase+math.tau*frame/72
            x, y = radius*math.cos(angle), radius*flatten*math.sin(angle)
            poses.append(f'{frame*100/72:.4f}%{{transform:translate({x:.3f}px,{y:.3f}px)}}')
        css.append(f'.repo-orbit-{i}{{animation:repo-orbit-{i} {period:.3f}s linear infinite}}'
                   f'@keyframes repo-orbit-{i}{{'+''.join(poses)+'}')
        x, y = radius*math.cos(phase), radius*flatten*math.sin(phase)
        color = palette[category(repo)]
        size = sizes[i]
        measured = counts[i] is not None
        marks=contribution_marks(contributions[i])
        if repo.get('fork'):
            distance=size+6
            moons=''.join(f'<circle cx="{distance*math.cos(math.tau*j/marks):.2f}" cy="{distance*math.sin(math.tau*j/marks):.2f}" r="1.7" fill="{color}"/>' for j in range(marks)) if marks else ''
            symbol=f'<g class="moon-orbit">{moons}</g>' if moons else ''
        else:
            symbol=''.join(f'<ellipse rx="{size+3+2.2*j:.2f}" ry="{size*.48+2+1.1*j:.2f}" fill="none" stroke="{color}" stroke-width=".65" transform="rotate(-25)"/>' for j in range(marks))
        drawing += (f'<g class="repo-orbiter repo-orbit-{i}" style="transform:translate({x:.3f}px,{y:.3f}px)">'
                    f'<circle r="{size*2.4:.2f}" fill="{color}" opacity=".065"/>'
                    f'<circle r="{size:.2f}" fill="{color if measured else "#090e1b"}" stroke="{color}" stroke-width=".9"/>'+
                    (f'<circle r="{max(.8,size*.19):.2f}" fill="#edf5f1" opacity=".6"/>' if measured else '')+
                    symbol+'</g>')
    drawing += ('<circle r="43" fill="#91f2cc" opacity=".025"/>'
                '<circle r="25" fill="#090e1b" stroke="#91f2cc" stroke-width="1.2"/>'
                '<circle r="31" fill="none" stroke="#91f2cc" stroke-width=".6" opacity=".2"/>'
                '<text x="0" y="5" fill="#91f2cc" font-family="DejaVu Sans Mono,monospace" '
                'font-size="13" font-weight="600" text-anchor="middle">MWS</text>')
    return '<style>'+''.join(css)+f'</style><g transform="translate({cx} {cy})">'+drawing+'</g>'
