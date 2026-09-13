"""Horror catalogues from Shudder, via JustWatch.

Shudder's own site is geo-locked (403 outside its markets) and TMDB's
availability data is licensed from JustWatch a day in arrears, so JustWatch is
queried directly. Its US catalogue is used because Shudder is not sold in
Malaysia - that only decides which catalogue is read, not what can be played,
since the add-on serves IMDb IDs and other add-ons supply the streams.
"""

import logging

import requests

from .models import ScrapedItem
from .resolver import HEADERS, poster_url

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://apis.justwatch.com/graphql"
COUNTRY = "US"
PACKAGE = "shd"
HORROR_GENRE = "hrr"

# JustWatch has no "recently added" sort - NEWEST, NEW and DATE_ADDED are all
# rejected - so "new" means most recently released.
SORTS = {"popular": "POPULAR", "new": "RELEASE_YEAR"}

OBJECT_TYPES = {"movie": "MOVIE", "series": "SHOW"}

QUERY = """
query ShudderHorror {
  popularTitles(
    country: %(country)s
    first: %(limit)d
    sortBy: %(sort)s
    filter: {
      objectTypes: [%(object_type)s]
      packages: ["%(package)s"]
      genres: ["%(genre)s"]
    }
  ) {
    edges {
      node {
        id
        content(country: %(country)s, language: "en") {
          title
          originalReleaseYear
          shortDescription
          fullPath
          posterUrl
          externalIds { imdbId }
        }
      }
    }
  }
}
"""


class ShudderError(RuntimeError):
    pass


def _query(sort: str, object_type: str, limit: int) -> list[dict]:
    payload = {
        "query": QUERY
        % {
            "country": COUNTRY,
            "limit": limit,
            "sort": SORTS[sort],
            "object_type": OBJECT_TYPES[object_type],
            "package": PACKAGE,
            "genre": HORROR_GENRE,
        }
    }
    try:
        response = requests.post(
            GRAPHQL_URL, json=payload, timeout=30, headers=HEADERS
        )
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ShudderError(f"JustWatch request failed: {exc}") from exc

    if body.get("errors"):
        raise ShudderError(f"GraphQL errors: {body['errors']}")

    titles = (body.get("data") or {}).get("popularTitles")
    if not titles:
        raise ShudderError("Response contained no popularTitles data")

    return titles.get("edges") or []


def fetch_horror(sort: str, media_type: str, limit: int = 10) -> list[ScrapedItem]:
    edges = _query(sort, media_type, limit)
    items = []

    for position, edge in enumerate(edges, start=1):
        node = edge.get("node") or {}
        content = node.get("content") or {}
        title = content.get("title")
        if not title:
            continue

        imdb_id = (content.get("externalIds") or {}).get("imdbId")
        year = content.get("originalReleaseYear")
        full_path = content.get("fullPath") or ""

        items.append(
            ScrapedItem(
                id=imdb_id or node.get("id") or f"shudder-{sort}-{media_type}-{position}",
                title=title,
                poster=poster_url(content.get("posterUrl")),
                rank=position,
                type=media_type,
                region="shudder",
                url=f"https://www.justwatch.com{full_path}" if full_path else "",
                description=content.get("shortDescription")
                or (f"{title} ({year})" if year else title),
                imdb_id=imdb_id,
            )
        )

    logger.info("Shudder %s %s: %d items", sort, media_type, len(items))
    return items
