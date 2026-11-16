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
| `trending/` | Daily trending seed (`apps.json`) |
| `catalog/` | Searchable APK-verified catalog (filled by discovery later) |

## How it updates

The app repo’s `auto-discovery` workflow runs `scripts/discover.py`, commits to **GitStore** `cached-data/` (legacy ≤1.4.x clients), then mirrors `trending/` here when secret `GITSTORE_DATA_TOKEN` is set.

Phones never write to this repo.

## License

MIT — see `LICENSE`. The JSON is metadata about public GitHub repos (links, stars, APK presence). It is not the apps themselves; install/download still goes through GitHub.

## Public use

Anyone can hit the jsDelivr URLs (same as any public GitHub file). That is fine for other FOSS clients. There is **no API key** and **no per-user quota we control**.

Limits that apply:
- **jsDelivr** — public CDN fair use; very high for small JSON; extreme abuse may be throttled
- **GitHub** — raw/API limits only if someone bypasses jsDelivr; our Actions PAT is separate and not exposed
- **Us** — cost is Actions minutes + repo size, not per CDN request

If a client hammers GitHub *releases* after reading this catalog, that hits GitHub’s limits on *their* IP/token, not ours. Please cache responses and keep polling polite.
