#!/usr/bin/env python3
"""Measure filtered source LOC at verified public default-branch commits.

Repository code is read as data and is never executed. A failed refresh leaves
the committed metric snapshot unchanged. Existing public SHAs are cached.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
USER = 'Mohamed-Waiel-Shikfa'
SNAPSHOT = ROOT/'data/public-activity.json'
METRICS = ROOT/'data/repo-code-metrics.json'
POLICY_VERSION = 2
EXCLUDED_DIRS = {
    '.git', '.hg', '.svn', '.venv', 'venv', 'env', 'site-packages',
    '__pycache__', 'node_modules', 'bower_components', 'vendor', 'vendors',
    'third_party', 'third-party', 'external', 'extern', 'submodules',
    'build', 'dist', 'out', 'target', '.next', '.nuxt', 'coverage', '.cache',
    '.pytest_cache', '.mypy_cache', '.tox', '.idea', '.vscode', 'htmlcov',
    'generated', 'generated-src', 'generated_sources', '.ipynb_checkpoints',
    'cmake-build-debug', 'cmake-build-release', 'cmu_graphics',
}
EXCLUDED_FILES = {
    'cmu_graphics.py', 'cmu_112_graphics.py', 'cmu_graphics_loader.py',
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'cargo.lock',
    'poetry.lock', 'uv.lock', 'pipfile.lock', 'composer.lock', 'go.sum',
    'gemfile.lock', 'ieeetran.cls', 'ieeetran.bst',
}
# Recognized maintained source/configuration formats. Prose, datasets, media,
# lockfiles, notebook outputs, and LaTeX build products do not enter the count.
SOURCE_EXTENSIONS = {
    '.py', '.pyw', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.c', '.h', '.cc', '.hh', '.cpp', '.hpp', '.cxx', '.hxx', '.rs', '.go',
    '.java', '.kt', '.kts', '.cs', '.swift', '.m', '.mm', '.r', '.jl',
    '.sml', '.sig', '.fun', '.ml', '.mli', '.hs', '.lhs', '.rkt', '.scm',
    '.clj', '.cljs', '.lisp', '.ex', '.exs', '.erl', '.hrl', '.lua', '.rb',
    '.php', '.pl', '.pm', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.sql',
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
    '.tex', '.sty', '.bib', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.xml', '.urdf', '.xacro', '.sdf', '.cmake', '.scad', '.glsl', '.vert',
    '.frag', '.geom', '.proto', '.qbs', '.qml', '.qrc', '.pro', '.gradle',
    '.v', '.sv', '.vhd', '.vhdl', '.ipynb',
}
SOURCE_NAMES = {'makefile', 'dockerfile', 'cmakelists.txt', 'justfile'}
MAX_ARCHIVE_BYTES = 300*1024*1024
MAX_SOURCE_BYTES = 32*1024*1024
MAX_NOTEBOOK_BYTES = 256*1024*1024


def eligible_source(path):
    path = PurePosixPath(path)
    if path.is_absolute() or '..' in path.parts:
        return False
    if any(part.lower() in EXCLUDED_DIRS for part in path.parts[:-1]):
        return False
    name = path.name.lower()
    if name in EXCLUDED_FILES or name.endswith(('.lock', '.min.js', '.min.css', '.bundle.js', '.map')):
        return False
    return path.suffix.lower() in SOURCE_EXTENSIONS or name in SOURCE_NAMES


def policy():
    return {
        'version': POLICY_VERSION,
        'excluded_directories': sorted(EXCLUDED_DIRS),
        'excluded_files': sorted(EXCLUDED_FILES),
        'included_extensions': sorted(SOURCE_EXTENSIONS),
        'included_names': sorted(SOURCE_NAMES),
        'notebooks': 'Code cells only; markdown, metadata, execution counts, and outputs omitted.',
        'extra_exclusions': ['*.lock', '*.min.js', '*.min.css', '*.bundle.js', '*.map'],
        'repository_exclusions': {'ML_in_a_Nutshell_notes': ['*.ipynb (source material)']},
    }


def public_heads(names):
    """Query only the explicit public-snapshot allowlist, then verify visibility."""
    for name in names:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
            raise ValueError('Invalid public repository name')
    fields = 'name isPrivate isFork isArchived owner{login} defaultBranchRef{name target{oid ... on Commit{author{email user{login}}}}}'
    query = 'query{'+''.join(f'r{i}:repository(owner:"{USER}",name:"{name}"){{{fields}}}'
                            for i, name in enumerate(names))+'}'
    if shutil.which('gh'):
        result = subprocess.run(['gh', 'api', '--hostname', 'github.com', 'graphql', '--input', '-'],
                                input=json.dumps({'query': query}), text=True, capture_output=True, check=True)
        result = json.loads(result.stdout)
    else:
        headers = {'User-Agent': USER+'-profile-metrics', 'Content-Type': 'application/json'}
        if os.environ.get('GH_TOKEN'):
            headers['Authorization'] = 'Bearer '+os.environ['GH_TOKEN']
        request = Request('https://api.github.com/graphql', json.dumps({'query': query}).encode(), headers)
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    if result.get('errors'):
        raise ValueError('Public repository query failed')
    heads = {}
    for i, name in enumerate(names):
        repo = result['data'][f'r{i}']
        if (not repo or repo['name'] != name or repo['isPrivate']
                or repo['owner']['login'].lower() != USER.lower()):
            raise ValueError('Repository no longer matches public original-repository policy')
        branch = repo['defaultBranchRef']
        if not branch or not re.fullmatch(r'[a-f0-9]{40}', branch['target']['oid']):
            raise ValueError('Missing public default-branch commit')
        author = branch['target'].get('author') or {}
        generated = ((author.get('user') or {}).get('login') == 'github-actions[bot]'
                     or author.get('email') == '41898282+github-actions[bot]@users.noreply.github.com')
        heads[name] = {'head_sha': branch['target']['oid'], 'default_branch': branch['name'], 'is_fork': repo['isFork'], 'generated_head': generated}
    return heads


def notebook_source(data):
    notebook = json.loads(data)
    language = notebook.get('metadata', {}).get('language_info', {}).get('name', 'python').lower()
    extension = {'python': '.py', 'r': '.r', 'julia': '.jl', 'javascript': '.js', 'typescript': '.ts'}.get(language)
    if not extension:
        raise ValueError('Unsupported notebook kernel language')
    cells = []
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'code':
            source = cell.get('source', [])
            cells.append(''.join(source) if isinstance(source, list) else source)
    return '\n\n'.join(cells), extension


def extract_sources(archive, target, repo_name=''):
    selected = 0
    with tarfile.open(archive, 'r:gz') as bundle:
        for member in bundle:
            if not member.isfile():
                continue  # Never materialize archive links or devices.
            raw = PurePosixPath(member.name)
            if raw.is_absolute() or '..' in raw.parts:
                raise ValueError('Unsafe archive path')
            if len(raw.parts) < 2:
                continue
            path = PurePosixPath(*raw.parts[1:])
            if not eligible_source(path):
                continue
            if repo_name == 'ML_in_a_Nutshell_notes' and path.suffix.lower() == '.ipynb':
                continue
            limit = MAX_NOTEBOOK_BYTES if path.suffix.lower() == '.ipynb' else MAX_SOURCE_BYTES
            if member.size > limit:
                raise ValueError(f'Source file exceeds measurement limit: {path} ({member.size} bytes)')
            with bundle.extractfile(member) as source:
                data = source.read(limit+1)
            if len(data) > limit:
                raise ValueError('Source file exceeds measurement limit')
            if path.suffix.lower() == '.ipynb':
                code, extension = notebook_source(data)
                data = code.encode('utf-8')
                path = PurePosixPath(str(path)+extension)
            output = target.joinpath(*path.parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
            selected += 1
    return selected


def extract_tree_sources(name, head, target):
    """Fetch only source blobs when a public archive is too large."""
    base = f'repos/{USER}/{name}/git'
    commit = json.loads(subprocess.run(['gh','api',f'{base}/commits/{head["head_sha"]}'],
                                       text=True,capture_output=True,check=True,timeout=60).stdout)
    tree_sha = commit['tree']['sha']
    tree = json.loads(subprocess.run(['gh','api',f'{base}/trees/{tree_sha}?recursive=1'],
                                     text=True,capture_output=True,check=True,timeout=60).stdout)
    if tree.get('truncated'):
        raise ValueError('Public source tree is truncated')
    candidates=[]
    for item in tree['tree']:
        path=PurePosixPath(item['path'])
        if item.get('type')!='blob' or item.get('mode')=='120000' or not eligible_source(path):
            continue
        if name=='ML_in_a_Nutshell_notes' and path.suffix.lower()=='.ipynb':
            continue
        limit=MAX_NOTEBOOK_BYTES if path.suffix.lower()=='.ipynb' else MAX_SOURCE_BYTES
        if item.get('size',0)>limit:
            raise ValueError('Source file exceeds measurement limit')
        candidates.append((path,limit))
    def fetch(item):
        path,limit=item
        url=f'https://raw.githubusercontent.com/{USER}/{name}/{head["head_sha"]}/{quote(str(path),safe="/")}'
        with urlopen(Request(url,headers={'User-Agent':USER+'-profile-metrics'}),timeout=60) as response:
            data=response.read(limit+1)
        if len(data)>limit:raise ValueError('Source file exceeds measurement limit')
        if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
            return None
        if path.suffix.lower()=='.ipynb':
            code,extension=notebook_source(data);data=code.encode('utf-8');path=PurePosixPath(str(path)+extension)
        output=target.joinpath(*path.parts);output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data)
        return str(path)
    with ThreadPoolExecutor(max_workers=6) as executor:
        return sum(result is not None for result in executor.map(fetch,candidates))


def measure_repository(name, head):
    """Download an immutable public archive; count filtered files with cloc."""
    with tempfile.TemporaryDirectory(prefix='profile-loc-') as temp:
        temp = Path(temp); archive = temp/'source.tar.gz'; sources = temp/'source'
        sources.mkdir()
        url = f'https://codeload.github.com/{USER}/{name}/tar.gz/{head["head_sha"]}'
        archive_hash=None
        if name in {'Term-project', 'ML_in_a_Nutshell_notes'} or head.get('is_fork'):
            selected=extract_tree_sources(name,head,sources)
        else:
            try:
                with urlopen(Request(url, headers={'User-Agent': USER+'-profile-metrics'}), timeout=60) as response:
                    if int(response.headers.get('Content-Length','0'))>MAX_ARCHIVE_BYTES:
                        raise ValueError('Public archive exceeds measurement limit')
                    size = 0
                    with archive.open('wb') as output:
                        while chunk := response.read(1024*1024):
                            size += len(chunk)
                            if size > MAX_ARCHIVE_BYTES:
                                raise ValueError('Public archive exceeds measurement limit')
                            output.write(chunk)
                archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
                selected = extract_sources(archive, sources, name)
            except ValueError as error:
                if str(error)!='Public archive exceeds measurement limit':raise
                selected=extract_tree_sources(name,head,sources)
        command = ['cloc', str(sources), '--json', '--quiet', '--timeout=30',
                   '--force-lang=XML,urdf', '--force-lang=XML,xacro', '--force-lang=XML,sdf']
        result = subprocess.run(command, text=True, capture_output=True, check=True, timeout=120)
        counts = json.loads(result.stdout) if result.stdout.strip() else {'SUM': {'code': 0, 'comment': 0, 'blank': 0, 'nFiles': 0}}
        total = counts.get('SUM')
        if total is None:
            if selected:
                raise ValueError('cloc returned no totals for selected source files')
            total = {'code': 0, 'comment': 0, 'blank': 0, 'nFiles': 0}
        for key in ['code', 'comment', 'blank', 'nFiles']:
            if not isinstance(total.get(key), int) or total[key] < 0:
                raise ValueError('Invalid cloc totals')
        return {
            **head,
            'measured_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'archive_sha256': archive_hash,
            'source_lines': total['code'], 'comment_lines': total['comment'],
            'blank_lines': total['blank'], 'source_files': total['nFiles'],
            'languages': {language: {'files': row['nFiles'], 'source_lines': row['code']}
                          for language, row in counts.items() if language not in ['header', 'SUM']},
        }


def refresh_metrics(snapshot_path=SNAPSHOT, target=METRICS):
    snapshot = json.loads(snapshot_path.read_text())
    extras_path = ROOT/'data/public-extras.json'
    extras = json.loads(extras_path.read_text()) if extras_path.exists() else []
    repos = snapshot['repos'] + extras
    names = [repo['name'] for repo in repos]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate public repository names')
    tool = subprocess.run(['cloc', '--version'], text=True, capture_output=True, check=True).stdout.strip()
    current_policy = policy()
    old = json.loads(target.read_text()) if target.exists() else None
    reusable = bool(old and old.get('policy') == current_policy and old.get('tool') == {'name': 'cloc', 'version': tool})
    heads = public_heads(names)
    measured = {}
    pending = []
    for repo in repos:
        previous = old.get('repos', {}).get(repo['name']) if reusable else None
        if previous and (previous.get('head_sha') == heads[repo['name']]['head_sha'] or
                         (repo['name'].lower() == USER.lower() and heads[repo['name']]['generated_head'])):
            measured[repo['name']] = {**previous, 'pushed_at': repo['pushed_at']}
        else:
            pending.append(repo)
    def measure(repo):
        result = measure_repository(repo['name'], heads[repo['name']])
        result['pushed_at'] = repo['pushed_at']
        return repo['name'], result
    failures=[]
    def save_partial():
        result={'schema_version':1,'metric':'filtered_nonblank_noncomment_source_lines',
                'measured_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'tool':{'name':'cloc','version':tool},'policy':current_policy,
                'repos':{name:measured[name] for name in sorted(measured)}}
        target.parent.mkdir(exist_ok=True)
        temporary=target.with_suffix('.tmp');temporary.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');temporary.replace(target)
    with ThreadPoolExecutor(max_workers=3) as executor:
        jobs={executor.submit(measure,repo):repo['name'] for repo in pending}
        for job in as_completed(jobs):
            try:
                name,result=job.result();measured[name]=result;save_partial()
                print(f'{name}: {result["source_lines"]:,} source LOC at {result["head_sha"][:12]}',flush=True)
            except Exception as error:
                failures.append((jobs[job],str(error)))
                print(f'{jobs[job]}: measurement failed: {error}',file=sys.stderr,flush=True)
    if failures:
        raise ValueError(f'{len(failures)} public repository measurements failed; successful measurements were saved')
    ordered = {name: measured[name] for name in sorted(measured)}
    if old and old.get('repos') == ordered and reusable:
        print('Public commit SHAs unchanged; retaining code metrics', flush=True)
        return False
    result = {
        'schema_version': 1,
        'metric': 'filtered_nonblank_noncomment_source_lines',
        'measured_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'tool': {'name': 'cloc', 'version': tool}, 'policy': current_policy, 'repos': ordered,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    temporary.replace(target)
    print(f'Updated source-volume metrics for {len(ordered)} public repositories', flush=True)
    return True


if __name__ == '__main__':
    try:
        refresh_metrics()
        from build_profile import build
        build()
    except Exception as error:
        print(f'Code metric refresh failed: {type(error).__name__}: {error}', file=sys.stderr)
        sys.exit(1)
