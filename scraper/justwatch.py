import logging
import requests

from .models import ScrapedItem

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://apis.justwatch.com/graphql"
IMAGE_BASE = "https://images.justwatch.com"
POSTER_PROFILE = "s718"
POSTER_FORMAT = "jpg"
NETFLIX_PACKAGE = "nfx"

# streamingCharts returns each title's position in the country-wide chart across all
# providers, so filtering to Netflix yields non-contiguous ranks (1, 5, 6, ...).
# Rank is therefore assigned from list position rather than read off the response.
CHART_QUERY = """
query NetflixTop10 {
  streamingCharts(
    country: %(country)s
    first: %(limit)d
    filter: {
      category: DAILY_POPULARITY_SAME_CONTENT_TYPE
      objectType: %(object_type)s
      packages: ["%(package)s"]
      nextTitles: 0
      previousTitles: 0
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
          externalIds {
            imdbId
          }
        }
      }
    }
  }
}
"""


class JustWatchError(RuntimeError):
    pass


def _poster_url(poster_path: str | None) -> str:
    if not poster_path:
        return ""
    resolved = poster_path.replace("{profile}", POSTER_PROFILE).replace(
        "{format}", POSTER_FORMAT
    )
    return f"{IMAGE_BASE}{resolved}"


def _query(country: str, object_type: str, limit: int) -> list[dict]:
    payload = {
        "query": CHART_QUERY
        % {
            "country": country,
            "object_type": object_type,
            "limit": limit,
            "package": NETFLIX_PACKAGE,
        }
    }
    response = requests.post(
        GRAPHQL_URL,
        json=payload,
        timeout=30,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "netflix-top-lists (+https://github.com/tanjiakai/netflix-top-lists)",
        },
    )
    response.raise_for_status()
    body = response.json()

    if body.get("errors"):
        raise JustWatchError(f"GraphQL errors: {body['errors']}")

    charts = (body.get("data") or {}).get("streamingCharts")
    if not charts:
        raise JustWatchError("Response contained no streamingCharts data")

    return charts.get("edges") or []


def fetch_top10(country: str, object_type: str, media_type: str, region: str,
                limit: int = 10) -> list[ScrapedItem]:
    edges = _query(country, object_type, limit)
    items = []

    for position, edge in enumerate(edges, start=1):
        node = edge.get("node") or {}
        content = node.get("content") or {}
        title = content.get("title")
        if not title:
            logger.warning("Skipping chart entry at position %d with no title", position)
            continue

        imdb_id = (content.get("externalIds") or {}).get("imdbId")
        full_path = content.get("fullPath") or ""

        items.append(
            ScrapedItem(
                id=imdb_id or node.get("id") or f"{region}-{media_type}-{position}",
                title=title,
                poster=_poster_url(content.get("posterUrl")),
                rank=position,
                type=media_type,
                region=region,
                url=f"https://www.justwatch.com{full_path}" if full_path else "",
                description=content.get("shortDescription"),
                imdb_id=imdb_id,
                year=content.get("originalReleaseYear"),
            )
        )

    return items
