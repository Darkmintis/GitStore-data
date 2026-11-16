# Search catalog

`apps.json` uses the same shape as `../trending/apps.json`:

```json
{
  "lastUpdated": "ISO-8601",
  "totalCount": 0,
  "repositories": [ /* GithubRepoSummary-compatible objects */ ]
}
```

Empty until the search-index job lands. Clients should treat `totalCount == 0` as “not ready” and fall back to live GitHub search.
