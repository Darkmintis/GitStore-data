#!/usr/bin/env python3
"""
Git Store discovery. Runs daily (midnight UTC) and writes, all in the same schema:

  catalog/apps.json   every APK-verified repo we know about (app searches this locally)
  trending/apps.json  biggest star GAIN since the previous run (falls back to recent+stars on day 1)
  new/apps.json       repos created in the last 30 days, newest first
  popular/apps.json   most-starred repos pushed in the last 30 days
  catalog/state.json  verification memory so we never re-check the same repo daily

Verification = latest non-draft release has an .apk (stable preferred, prerelease accepted;
same rule as the app's search). Each run verifies at most MAX_VERIFY new repos, so the
catalog grows over several days instead of blowing the API budget.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("ERROR: GITHUB_TOKEN is not set")

API = "https://api.github.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
TOPICS = ["android", "android-app"]
# GitHub search returns max 1000 hits per query, so slice by star bands to go deeper.
STAR_BANDS = [">5000", "1000..5000", "500..999", "200..499", "100..199", "50..99", "20..49"]
MAX_VERIFY = int(os.environ.get("MAX_VERIFY", 600))         # new release checks per run (budget: 1000 core req/hr)
HIT_RECHECK_DAYS = 14     # re-verify a known app this often
MISS_RECHECK_DAYS = 14    # retry a known non-app this often
LIST_SIZE = 50
BAND_PAGES = int(os.environ.get("BAND_PAGES", 10))  # GitHub caps a query at 10 pages
OUT = Path(os.environ.get("DISCOVERY_ROOT", "."))

NOW = datetime.now(timezone.utc)
TODAY = NOW.date().isoformat()


def day(n: int) -> str:
    return (NOW - timedelta(days=n)).strftime("%Y-%m-%d")


def get(url, params=None):
    """GET with minimal retry; sleeps through rate limits. Returns Response or None."""
    for attempt in range(5):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        except requests.RequestException as e:
            print(f"  network error: {e}")
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 200:
            return r
        limited = r.status_code == 429 or (r.status_code == 403 and "rate limit" in r.text.lower())
        if limited:
            reset = int(r.headers.get("X-RateLimit-Reset", 0))
            wait = int(r.headers.get("Retry-After", 0)) or max(reset - int(time.time()), 1)
            if wait > 120:  # out of budget: stop instead of hanging the job
                print(f"  rate limited for {wait}s, giving up on {url}")
                return None
            print(f"  rate limited, sleeping {wait}s")
            time.sleep(wait + 1)
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        print(f"  {r.status_code} for {url}")
        return None
    return None


def has_apk(full_name: str):
    """True/False, or None when the check itself failed (don't remember failures)."""
    r = get(f"{API}/repos/{full_name}/releases", {"per_page": 10})
    if r is None:
        return None
    rels = [x for x in r.json() if not x.get("draft")]
    def apk(x):
        return any(a["name"].lower().endswith(".apk") for a in x.get("assets", []))
    return any(apk(x) for x in rels if not x.get("prerelease")) or any(apk(x) for x in rels)


def search(query: str, sort: str, pages: int):
    for page in range(1, pages + 1):
        r = get(f"{API}/search/repositories",
                {"q": query, "sort": sort, "order": "desc", "per_page": 100, "page": page})
        if r is None:
            return
        items = r.json().get("items", [])
        yield from items
        if len(items) < 100:
            return
        time.sleep(2)  # search API: 30 req/min


def summarize(repo: dict) -> dict:
    return {
        "id": repo["id"],
        "name": repo["name"],
        "fullName": repo["full_name"],
        "owner": {"login": repo["owner"]["login"], "avatarUrl": repo["owner"]["avatar_url"]},
        "description": repo.get("description"),
        "defaultBranch": repo.get("default_branch", "main"),
        "htmlUrl": repo["html_url"],
        "stargazersCount": repo["stargazers_count"],
        "forksCount": repo["forks_count"],
        "language": repo.get("language"),
        "topics": repo.get("topics", []),
        "releasesUrl": repo["releases_url"],
        "updatedAt": repo["updated_at"],
        "createdAt": repo["created_at"],
        "pushedAt": repo["pushed_at"],
    }


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write(folder: str, repos: list):
    path = OUT / folder / "apps.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"lastUpdated": NOW.isoformat().replace("+00:00", "Z"), "totalCount": len(repos),
               "repositories": repos}
    # Small lists are meant to be read (and diffed); the catalog grows to thousands, so keep it compact.
    fmt = {"separators": (",", ":")} if folder == "catalog" else {"indent": 2}
    path.write_text(json.dumps(payload, ensure_ascii=False, **fmt), encoding="utf-8")
    print(f"wrote {folder}/apps.json: {len(repos)} repos")


def older_than(date_str: str, days: int) -> bool:
    return date_str <= day(days)


def main():
    old_catalog = {r["fullName"]: r for r in load(OUT / "catalog/apps.json", {}).get("repositories", [])}
    # state: fullName -> {"checked": date, "apk": bool}; stars: fullName -> stars at last run
    state = load(OUT / "catalog/state.json", {"checked": {}, "stars": {}})
    checked, prev_stars = state["checked"], state["stars"]

    # 1. gather candidates (fresh metadata straight from search)
    candidates = {}
    def add(items):
        for it in items:
            candidates[it["full_name"]] = it

    print("collecting: new / popular / star bands")
    for topic in TOPICS:  # GitHub search can't OR topics, so one pass per topic
        base = f"archived:false topic:{topic}"
        add(search(f"{base} stars:>=3 created:>={day(30)}", "created", 3))
        add(search(f"{base} stars:>=50 pushed:>={day(30)}", "stars", 3))
        for band in STAR_BANDS:
            add(search(f"{base} stars:{band}", "updated", BAND_PAGES))
    print(f"{len(candidates)} candidates")

    # 2. verify: known hits stay (until recheck), unknown ones are checked, newest/most-starred first
    verified, budget = {}, MAX_VERIFY
    # new repos first so the New list is never starved by the star-sorted backlog
    todo = sorted(candidates.values(),
                  key=lambda r: (r["created_at"][:10] < day(30), -r["stargazers_count"]))
    for repo in todo:
        name = repo["full_name"]
        info = checked.get(name)
        fresh = info and not older_than(info["checked"], HIT_RECHECK_DAYS if info["apk"] else MISS_RECHECK_DAYS)
        if fresh:
            if info["apk"]:
                verified[name] = summarize(repo)
            continue
        if budget <= 0:
            if info and info["apk"]:  # out of budget: keep the stale hit rather than dropping it
                verified[name] = summarize(repo)
            continue
        budget -= 1
        result = has_apk(name)
        if result is None:
            continue
        checked[name] = {"checked": TODAY, "apk": result}
        if result:
            verified[name] = summarize(repo)
    print(f"verified {len(verified)} apps ({MAX_VERIFY - budget} release checks)")

    # keep catalog entries that weren't in this run's search window (don't shrink on a bad day)
    for name, repo in old_catalog.items():
        verified.setdefault(name, repo)

    if not verified:
        sys.exit("ERROR: nothing verified, refusing to overwrite data")

    catalog = sorted(verified.values(), key=lambda r: -r["stargazersCount"])

    # 3. lists
    def pushed_since(r, n):
        return (r.get("pushedAt") or r["updatedAt"])[:10] >= day(n)

    new = sorted((r for r in catalog if r.get("createdAt", "")[:10] >= day(30)),
                 key=lambda r: r["createdAt"], reverse=True)[:LIST_SIZE]
    popular = [r for r in catalog if pushed_since(r, 30)][:LIST_SIZE]

    def gain(r):  # real trending: stars gained since last run; unseen repos get no gain
        return r["stargazersCount"] - prev_stars.get(r["fullName"], r["stargazersCount"])
    active = [r for r in catalog if pushed_since(r, 14)]
    if prev_stars:
        trending = sorted(active, key=lambda r: (-gain(r), -r["stargazersCount"]))[:LIST_SIZE]
    else:  # day 1, no history yet
        trending = active[:LIST_SIZE]

    write("catalog", catalog)
    write("trending", trending)
    write("new", new)
    write("popular", popular)

    state = {"checked": checked, "stars": {r["fullName"]: r["stargazersCount"] for r in catalog}}
    (OUT / "catalog/state.json").write_text(json.dumps(state, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
