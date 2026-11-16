# Discovery scripts

`discover.py` finds Android repos with APK releases and writes `trending/apps.json`.

```bash
export GITHUB_TOKEN=...   # or rely on Actions
python discover.py
```

Optional: `DISCOVERY_OUTPUT_DIR` (default `trending`).
