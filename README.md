# GitStore-data

Free static “backend” for [Git Store](https://github.com/Darkmintis/GitStore): pre-verified Android repos served over jsDelivr. No Cloudflare.

## CDN

```
https://cdn.jsdelivr.net/gh/Darkmintis/GitStore-data@main/trending/
https://cdn.jsdelivr.net/gh/Darkmintis/GitStore-data@main/catalog/
```

## Layout

| Path | Purpose |
|------|---------|
| `trending/` | Daily trending / New / Popular seed lists (moved from the app repo) |
| `catalog/` | Searchable APK-verified catalog (built by Actions) |

The Android app should prefer this CDN, then fall back to live GitHub if needed.

## Updating

GitHub Actions (with a PAT secret) crawls GitHub, verifies `.apk` releases, and commits JSON here. Phones never write to this repo.
