# GitStore-data

Free static “backend” for [Git Store](https://github.com/Darkmintis/GitStore): pre-verified Android repos on jsDelivr. No Cloudflare.

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

The app repo’s `auto-discovery` workflow still runs `scripts/discover.py`, commits to **GitStore** `cached-data/` (legacy clients), then mirrors `trending/` here when secret `GITSTORE_DATA_TOKEN` is set.

Phones never write to this repo.


## License

MIT — see `LICENSE`. The JSON is metadata about public GitHub repos (links, stars, APK presence). It is not the apps themselves; install/download still goes through GitHub.

## Public use / abuse

Anyone can hit the jsDelivr URLs (same as any public GitHub file). That is fine for other FOSS clients. There is **no API key** and **no per-user quota we control**.

Limits that actually apply:
- **jsDelivr** — public CDN fair use; very high for small JSON; they may throttle extreme abuse
- **GitHub** — raw/API limits only if someone bypasses jsDelivr; our Actions PAT is separate and not exposed
- **Us** — cost is Actions minutes + repo size, not per CDN request

Misuse (scraping the CDN hard) mostly burns *their* bandwidth via jsDelivr, not your GitHub anonymous quota. If a client hammers GitHub *releases* after reading our catalog, that hits GitHub’s limits on *their* IP/token, not yours.

To stay polite for third-party apps: document the endpoints, ask for caching, and keep files small. No auth wall is possible on a public jsDelivr+GitHub setup without adding a real backend.
