# Netflix Top Lists — Stremio Add-on

A Stremio add-on serving the daily Netflix Top 10 (movies and TV) for Malaysia.

It is a **static add-on**: a GitHub Action fetches the charts once a day, renders the
Stremio Add-on Protocol responses as plain JSON files, and publishes them to GitHub
Pages. There is no server to run, keep warm, or pay for.

## Install

Open <https://tanjiakai.github.io/netflix-top-lists/> and click **Install in Stremio**,
or paste this into Stremio's add-on search:

```
https://tanjiakai.github.io/netflix-top-lists/manifest.json
```

## How it works

```
JustWatch GraphQL  ->  scraper/  ->  catalog.json  ->  build_site.py  ->  dist/  ->  GitHub Pages
```

- **Data source**: JustWatch's `streamingCharts` GraphQL field, using the
  `DAILY_POPULARITY_SAME_CONTENT_TYPE` chart filtered to Netflix (`nfx`) in Malaysia.
  It returns IMDb IDs directly, so no TMDB lookup is needed and no API key is required.
- **Ranking**: the API reports each title's position in the country-wide chart across
  *all* providers, so Netflix-only results come back non-contiguous (1, 5, 6, …). Rank
  is assigned from list position instead.
- **Freshness guard**: if either chart comes back empty or the fetch fails, the scraper
  exits non-zero and leaves `catalog.json` untouched, so a bad upstream day fails the
  workflow loudly instead of silently blanking the add-on.

## Local development

```bash
pip install -r requirements.txt
python -m scraper.scraper   # refresh catalog.json
python build_site.py        # render dist/
python -m pytest            # run tests
```

To preview the built add-on:

```bash
python -m http.server 8765 --directory dist
```

Then point Stremio at `http://127.0.0.1:8765/manifest.json`.

`build_site.py` reads `ADDON_BASE_URL` to build the install link; it defaults to the
GitHub Pages URL and the workflow sets it from the repository name.

## Deployment

The `Update catalog and deploy` workflow runs daily at 02:00 UTC, on every push to
`master`, and on manual dispatch. It runs the tests, scrapes, builds, commits the
refreshed `catalog.json`, and deploys `dist/` to GitHub Pages.

**One-time setup:** in the repository settings, under *Pages*, set the source to
**GitHub Actions**.
