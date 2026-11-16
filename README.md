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
