# GitStore-data

Static discovery data for [Git Store](https://github.com/Darkmintis/GitStore): pre-verified Android repos served over jsDelivr.

**Primary CDN for app v1.5+.** Older clients still read `Darkmintis/GitStore/cached-data/` until that path is retired (see the app repo `TODO.md`).

## CDN

```
https://cdn.jsdelivr.net/gh/Darkmintis/GitStore-data@main/trending/apps.json
https://cdn.jsdelivr.net/gh/Darkmintis/GitStore-data@main/catalog/apps.json
```

## Layout

| Path | Purpose |
|------|---------|
| `trending/` | Biggest star gain since the previous daily run |
| `new/` | Repos created in the last 30 days, newest first |
| `popular/` | Most-starred repos pushed in the last 30 days |
| `catalog/` | Every APK-verified repo found so far (the app searches it locally); `state.json` remembers which repos were already checked |
| `scripts/` | Discovery (`discover.py`) — this is the source of truth |

## How it updates

Daily Actions (`auto-discovery.yml`) runs `scripts/discover.py` with the workflow `GITHUB_TOKEN` and commits `trending/`.

The app repo **mirrors** that file into `cached-data/` for ≤1.4.x clients only. No cross-repo PAT required.

## License

MIT — see `LICENSE`. The JSON is metadata about public GitHub repos (links, stars, APK presence). It is not the apps themselves; install/download still goes through GitHub.

## Public use

Anyone can hit the jsDelivr URLs. Fine for other FOSS clients. No API key; no per-user quota we control.

Limits: jsDelivr fair use; GitHub API only if someone bypasses the CDN; our cost is Actions minutes + repo size. Please cache and poll politely.
