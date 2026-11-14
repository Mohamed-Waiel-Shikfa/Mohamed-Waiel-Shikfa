#!/usr/bin/env python3
"""Refresh public metadata; a failed API request preserves the old snapshot."""

import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from build_profile import ROOT, build

USER = "Mohamed-Waiel-Shikfa"
SNAPSHOT = ROOT / "data/public-activity.json"


def fetch_repos():
    headers = {"User-Agent": f"{USER}-profile", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    repos = []
    for page in range(1, 101):
        url = f"https://api.github.com/users/{USER}/repos?type=owner&sort=pushed&per_page=100&page={page}"
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("Expected a repository list")
        repos.extend(batch)
        if len(batch) < 100:
            return repos
    raise ValueError("Pagination exceeded its safety limit")


def summarize(repos):
    clean = []
    for repo in repos:
        if (repo["private"] or repo["fork"] or repo["archived"]
                or repo["name"].lower() == USER.lower()
                or repo["owner"]["login"].lower() != USER.lower()):
            continue
        name, pushed = repo["name"], repo["pushed_at"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
            raise ValueError("Unexpected repository name")
        if pushed is None:
            continue
        datetime.strptime(pushed, "%Y-%m-%dT%H:%M:%SZ")
        language = repo["language"]
        if language is not None and not isinstance(language, str):
            raise ValueError("Unexpected language value")
        clean.append({"name": name, "language": language, "pushed_at": pushed})
    return sorted(clean, key=lambda repo: (repo["pushed_at"], repo["name"]), reverse=True)


def refresh(include_extras=False):
    fetched = fetch_repos()
    repos = summarize(fetched)
    if include_extras:
        target = ROOT/'data/public-extras.json'
        previous = json.loads(target.read_text()) if target.exists() else []
        old_profile = next ( (r for r in previous if r['name'].lower() == USER.lower()), None)
        generated_profile = False
        if old_profile and os.environ.get('GITHUB_ACTIONS') == 'true':
            from refresh_code_metrics import public_heads
            generated_profile = public_heads([USER])[USER]['generated_head']
        extras = []
        for repo in fetched:
            if repo['private'] or repo['owner']['login'].lower() != USER.lower():
                continue
            if not (repo['fork'] or repo['archived'] or repo['name'].lower() == USER.lower()):
                continue
            name, pushed, language = repo['name'], repo['pushed_at'], repo['language']
            if name.lower() == USER.lower() and generated_profile:
                pushed = old_profile['pushed_at']
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or (language is not None and not isinstance(language, str)):
                raise ValueError('Invalid public repository metadata')
            if pushed is None:
                continue
            datetime.strptime(pushed, '%Y-%m-%dT%H:%M:%SZ')
            extras.append({'name': name, 'language': language, 'pushed_at': pushed, 'fork': bool(repo['fork'])})
        extras.sort(key=lambda repo: (repo['pushed_at'], repo['name']), reverse=True)
        if not target.exists() or json.loads(target.read_text()) != extras:
            temporary = target.with_suffix('.tmp')
            temporary.write_text(json.dumps(extras, indent=2)+'\n', encoding='utf-8')
            temporary.replace(target)
    old = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else None
    if old is None or old["repos"] != repos:
        data = {"snapshot_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "repos": repos}
        SNAPSHOT.parent.mkdir(exist_ok=True)
        temp = SNAPSHOT.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        temp.replace(SNAPSHOT)
        print(f"Updated snapshot: {len(repos)} original public repositories")
    else:
        print("Public repository metadata unchanged; retaining snapshot date")
    build()


if __name__ == "__main__":
    try:
        refresh(include_extras=True)
    except Exception as error:
        print(f"Refresh failed: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)
