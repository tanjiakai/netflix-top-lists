"""Resolve a Netflix title to an IMDb ID.

Netflix's Top 10 feed gives titles only, but Stremio needs IMDb IDs for other
add-ons to find streams. Two keyless sources are tried, and a title is left
unresolved rather than guessed - a wrong ID shows the wrong film and pulls the
wrong streams, which is worse than no ID at all.
"""

import logging
import re
import urllib.parse
from difflib import SequenceMatcher

import requests

logger = logging.getLogger(__name__)

CINEMETA_URL = "https://v3-cinemeta.strem.io"
JUSTWATCH_URL = "https://apis.justwatch.com/graphql"
METAHUB_URL = "https://images.metahub.space"
IMAGE_BASE = "https://images.justwatch.com"
POSTER_PROFILE = "s718"
POSTER_FORMAT = "jpg"
TIMEOUT = 30

# JustWatch rejects the default python-requests agent with a 403.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

OBJECT_TYPES = {"movie": "MOVIE", "series": "SHOW"}

# Netflix's feed carries the occasional wrong word - it lists the Indonesian film
# "The Thorn: One Sacred Night" as "...One Sacred Light" - so a near-identical
# title is accepted when it is the only close one. Kept high deliberately: this
# is the step most likely to attach a wrong ID.
FUZZY_THRESHOLD = 0.90

# packages: ["nfx"] restricts the search to titles actually on Netflix in this
# country, which is what disambiguates common titles - without it "The
# Magnificent Seven" matches the 1960 original rather than the 2016 remake
# that is the one actually charting.
SEARCH_QUERY = """
query Search($country: Country!, $query: String!, $types: [ObjectType!]) {
  popularTitles(
    country: $country
    first: 5
    filter: { searchQuery: $query, objectTypes: $types, packages: ["nfx"] }
  ) {
    edges {
      node {
        content(country: $country, language: "en") {
          title
          originalReleaseYear
          posterUrl
          externalIds { imdbId }
        }
      }
    }
  }
}
"""


def normalize(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def poster_url(poster_path: str | None) -> str:
    if not poster_path:
        return ""
    resolved = poster_path.replace("{profile}", POSTER_PROFILE).replace(
        "{format}", POSTER_FORMAT
    )
    return f"{IMAGE_BASE}{resolved}"


def _justwatch(title: str, media_type: str, country: str):
    """Returns (imdb_id, year, poster) for the Netflix title matching by name."""
    payload = {
        "query": SEARCH_QUERY,
        "variables": {
            "country": country,
            "query": title,
            "types": [OBJECT_TYPES[media_type]],
        },
    }
    try:
        response = requests.post(
            JUSTWATCH_URL, json=payload, timeout=TIMEOUT, headers=HEADERS
        )
        response.raise_for_status()
        body = response.json()
        edges = (body.get("data") or {}).get("popularTitles", {}).get("edges") or []
    except (requests.RequestException, ValueError) as exc:
        logger.warning("JustWatch lookup failed for %r: %s", title, exc)
        return None, None, None

    for edge in edges:
        content = (edge.get("node") or {}).get("content") or {}
        if normalize(content.get("title")) == normalize(title):
            return (
                (content.get("externalIds") or {}).get("imdbId"),
                content.get("originalReleaseYear"),
                poster_url(content.get("posterUrl")),
            )
    return None, None, None


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _cinemeta_search(title: str, media_type: str) -> list[dict]:
    url = f"{CINEMETA_URL}/catalog/{media_type}/top/search={urllib.parse.quote(title)}.json"
    try:
        response = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        response.raise_for_status()
        return response.json().get("metas") or []
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Cinemeta lookup failed for %r: %s", title, exc)
        return []


def metahub_poster(imdb_id: str) -> str:
    return f"{METAHUB_URL}/poster/medium/{imdb_id}/img"


def resolve(title: str, media_type: str, country: str = "MY") -> tuple[str | None, str]:
    """Returns (imdb_id or None, poster_url).

    Every item needs its own poster: Stremio renders catalog rows from the
    poster in the catalog response and does not merge Cinemeta artwork into
    them, so an item without one shows a blank placeholder.
    """
    imdb_id, year, poster = _justwatch(title, media_type, country)
    if imdb_id:
        return imdb_id, poster or metahub_poster(imdb_id)

    metas = _cinemeta_search(title, media_type)
    exact = [m for m in metas if normalize(m.get("name")) == normalize(title)]

    matches = [m for m in exact if year and str(year) in (m.get("releaseInfo") or "")]
    if not matches and len(exact) == 1:
        matches = exact

    if not matches and not exact:
        close = [
            m for m in metas
            if similarity(normalize(m.get("name")), normalize(title)) >= FUZZY_THRESHOLD
        ]
        if len(close) == 1:
            logger.info("Fuzzy match: %r -> %r", title, close[0].get("name"))
            matches = close

    if matches:
        meta = matches[0]
        return meta["id"], meta.get("poster") or poster or metahub_poster(meta["id"])

    if len(exact) > 1:
        logger.info("Ambiguous match for %r (%d candidates), leaving unresolved",
                    title, len(exact))

    return None, poster or ""
