"""Poster lookup of last resort, for titles absent from IMDb-backed indexes.

Optional: without TMDB_API_KEY set, every lookup returns "" and the build falls
back to a generated tile. Used for artwork only, never for IMDb IDs - TMDB is
the weakest identity signal of the three sources, and a wrong ID is worse than
a missing one.
"""

import logging
import os

import requests

from .resolver import normalize, similarity, FUZZY_THRESHOLD

logger = logging.getLogger(__name__)

API_URL = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TIMEOUT = 30

SEARCH_PATHS = {"movie": "search/movie", "series": "search/tv"}
# TMDB names the title field differently per media type.
TITLE_FIELDS = {"movie": "title", "series": "name"}


def api_key() -> str:
    return os.environ.get("TMDB_API_KEY", "").strip()


def search_poster(title: str, media_type: str) -> str:
    key = api_key()
    if not key:
        return ""

    try:
        response = requests.get(
            f"{API_URL}/{SEARCH_PATHS[media_type]}",
            params={"api_key": key, "query": title, "include_adult": "false"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        results = response.json().get("results") or []
    except (requests.RequestException, ValueError) as exc:
        logger.warning("TMDB lookup failed for %r: %s", title, exc)
        return ""

    field = TITLE_FIELDS[media_type]
    wanted = normalize(title)

    for result in results:
        if not result.get("poster_path"):
            continue
        if normalize(result.get(field)) == wanted:
            logger.info("TMDB poster for %r", title)
            return f"{IMAGE_BASE}{result['poster_path']}"

    for result in results:
        if not result.get("poster_path"):
            continue
        if similarity(normalize(result.get(field)), wanted) >= FUZZY_THRESHOLD:
            logger.info("TMDB poster for %r (via %r)", title, result.get(field))
            return f"{IMAGE_BASE}{result['poster_path']}"

    return ""
