# Top Lists — Stremio Add-on

A Stremio add-on serving curated top lists from streaming services. Currently
**Netflix's official Top 10** (movies and TV) for Malaysia.

The manifest `id` stays `org.stremio.netflix_top_lists` and the repository keeps its
name: Stremio keys installs off the id, and the repository name is part of the GitHub
Pages URL, so changing either would break existing installs.

It is a **static add-on**: a GitHub Action fetches the chart once a day, renders the
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
top10.netflix.com TSV  ->  scraper/  ->  catalog.json  ->  build_site.py  ->  dist/  ->  GitHub Pages
```

### Data source

Netflix publishes its own Top 10 as a TSV at
`https://top10.netflix.com/data/all-weeks-countries.tsv` — every country, every week
back to 2021. This is Netflix's own data, so the rankings are correct by definition.
The scraper streams the file and keeps only the latest week for Malaysia.

**Cadence:** Netflix publishes weekly, on Tuesdays, for the week ending the previous
Sunday. So the chart is between 2 and 9 days old. Netflix only publishes the *daily*
Top 10 inside the app itself; no public source exposes it.

This was measured, not assumed. An earlier version of this add-on used JustWatch's
`streamingCharts`, which is daily — but it ranks by JustWatch's own user activity, not
Netflix viewing. Compared against Netflix's official Malaysia chart it matched on
**1 title out of 20**: it returned Western catalog filler (*Rick and Morty*, *The
Terminator*) where the real chart is dominated by Malaysian titles (*Bulan Henti
Bicara*, *Upin&Ipin*, *Gandhari*). Accurate-but-weekly beat fresh-but-unrelated.

### IMDb resolution

The TSV gives titles only, but Stremio needs IMDb IDs for other add-ons to find
streams. Two keyless sources are tried, in [scraper/resolver.py](scraper/resolver.py):

1. **JustWatch search**, restricted to titles on Netflix in the country. That
   restriction is what disambiguates common titles — without it *The Magnificent
   Seven* resolves to the 1960 original rather than the 2016 remake that is actually
   charting.
2. **Cinemeta** (Stremio's own catalog), matched on exact title, preferring the year
   JustWatch reported.
3. If nothing matches exactly, a **near-identical title** is accepted, but only when
   exactly one candidate clears a 0.90 similarity score. Netflix's feed carries the odd
   wrong word or spacing: it lists the Indonesian film *The Thorn: One Sacred **Night***
   as *"...One Sacred **Light**"*, and *Gate 24: The Border* as *"GATE24:The Border"*.
   Both were unresolvable on exact match alone.

A title with several equally plausible matches is left **unresolved rather than
guessed** — a wrong ID displays the wrong film and pulls the wrong streams, which is
worse than no ID. Currently 18 of 20 resolve. The rest still appear in the catalog,
just without streams.

### Shudder horror

Four extra catalogues, 10 titles each: popular and new, for films and series.
Source is JustWatch's `popularTitles`, filtered to the horror genre (`hrr`) on Shudder
(`shd`), in [scraper/shudder.py](scraper/shudder.py).

- **"New" means most recently released, not recently added.** JustWatch has no
  added-date sort — `NEWEST`, `NEW` and `DATE_ADDED` are all rejected by the schema.
- **The US catalogue is queried**, because Shudder is not sold in Malaysia. That only
  decides which catalogue is read; it does not affect playback, since the add-on serves
  IMDb IDs and other add-ons supply the streams.
- **"Popular" is JustWatch's own popularity signal**, not a Shudder ranking — the same
  class of number that matched Netflix on 1 title in 20. There is no official Shudder
  chart to check it against, so it is labelled "Popular on Shudder" rather than implying
  it is Shudder's own list.

Why not another source: Shudder's own site returns `403 — not available in your
country`, and TMDB licenses its availability data *from* JustWatch, delivered once per
24 hours, so it is the same data a day later.

These entries carry IMDb IDs and posters inline, so they skip the resolver entirely.

### Posters

Every item carries its own poster. Stremio renders catalog rows from the poster in the
catalog response and does **not** merge Cinemeta artwork into them, so an item without
one shows a blank placeholder. Whichever source resolved the title supplies the
artwork, falling back to `images.metahub.space` for any IMDb ID that arrives without
one.

Titles that resolve to no ID *and* that JustWatch has never heard of have no artwork
anywhere, so `build_site.py` generates a 2:3 SVG tile carrying the title — currently
1 of 20.

Netflix cannot fill that gap despite these being Netflix titles: neither the Tudum
chart nor its public title pages expose portrait art. Every artwork type they publish
is landscape (1200x675, 1280x720) or square (750x750).

### Freshness guard

If either catalog comes back empty or the fetch fails, the scraper exits non-zero and
leaves `catalog.json` untouched, so a bad upstream day fails the workflow loudly
instead of silently blanking the add-on.

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

The daily run is deliberate even though Netflix publishes weekly — it picks up the new
chart the day it appears without needing to track Netflix's schedule.
