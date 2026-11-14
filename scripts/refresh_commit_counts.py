#!/usr/bin/env python3
"""Count the account's commits on public repositories' default branches."""
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from refresh_code_metrics import ROOT, USER, public_heads

TARGET=ROOT/'data/repo-contributions.json'


def parse_count(response):
    headers,body=re.split(r'\r?\n\r?\n',response,maxsplit=1)
    count=int(body.strip())
    if count not in (0,1):raise ValueError('Unexpected commit response')
    links=re.findall(r'<([^>]+)>;\s*rel="last"',headers,re.I)
    return int(parse_qs(urlparse(links[-1]).query)['page'][0]) if links else count


def fetch_count(name):
    route=f'repos/{USER}/{name}/commits?author={USER}&per_page=1'
    result=subprocess.run(['gh','api','--include',route,'--jq','length'],capture_output=True,text=True,check=True,timeout=90)
    return parse_count(result.stdout)


def refresh():
    main=json.loads((ROOT/'data/public-activity.json').read_text())['repos']
    extras=json.loads((ROOT/'data/public-extras.json').read_text())
    repos=main+extras;names=[r['name'] for r in repos]
    if len(names)!=len(set(names)):raise ValueError('Duplicate repository')
    heads=public_heads(names)
    old=json.loads(TARGET.read_text()) if TARGET.exists() else {}
    previous=old.get('repos',{});records={};pending=[]
    for repo in repos:
        head=heads[repo['name']]['head_sha'];entry=previous.get(repo['name'],{})
        unchanged = entry.get('head_sha') == head or (repo['name'].lower() == USER.lower() and heads[repo['name']]['generated_head'])
        if unchanged and type(entry.get('commits')) is int and entry['commits']>=0:
            records[repo['name']]={**entry,'pushed_at':repo['pushed_at']}
        else:pending.append(repo)
    def save():
        result={'schema_version':1,'metric':'github_authored_commits_on_default_branch',
                'measured_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                'repos':{name:records[name] for name in sorted(records)}}
        temp=TARGET.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(TARGET)
    failures=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs={pool.submit(fetch_count,r['name']):r for r in pending}
        for job in as_completed(jobs):
            repo=jobs[job];name=repo['name']
            try:
                count=job.result()
                records[name]={'head_sha':heads[name]['head_sha'],'pushed_at':repo['pushed_at'],'commits':count}
                save();print(f'{name}: {count} authored commits',flush=True)
            except Exception as error:
                failures.append(name);print(f'{name}: commit count unavailable: {error}',file=sys.stderr,flush=True)
    # Reuse the original timestamp and bytes when the cache has not changed.
    if records!=previous:save()
    if failures:raise ValueError(f'{len(failures)} public commit counts unavailable; successful counts retained')
    print(f'Authored commit counts ready for {len(records)} public repositories')


if __name__=='__main__':
    try:
        refresh()
        from build_profile import build
        build()
    except Exception as error:
        print(f'Commit count refresh failed: {error}',file=sys.stderr)
        sys.exit(1)
