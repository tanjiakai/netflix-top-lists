import json
import logging
import sys
from datetime import datetime, timezone

from .justwatch import fetch_top10

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CATALOG_FILE = "catalog.json"

SCRAPE_TARGETS = {
    "malaysia_movies": {
        "country": "MY",
        "object_type": "MOVIE",
        "media_type": "movie",
        "region": "malaysia",
    },
    "malaysia_tv": {
        "country": "MY",
        "object_type": "SHOW",
        "media_type": "series",
        "region": "malaysia",
    },
}


def scrape_all() -> dict[str, list[dict]]:
    results = {}

    for key, config in SCRAPE_TARGETS.items():
        logger.info("Fetching %s", key)
        items = fetch_top10(
            country=config["country"],
            object_type=config["object_type"],
            media_type=config["media_type"],
            region=config["region"],
        )
        missing_imdb = [item.title for item in items if not item.imdb_id]
        if missing_imdb:
            logger.warning("No IMDb ID for: %s", ", ".join(missing_imdb))
        logger.info("Got %d items for %s", len(items), key)
        results[key] = [item.model_dump() for item in items]

    return results


def main() -> int:
    try:
        catalogs = scrape_all()
    except Exception as exc:
        logger.error("Scrape failed, leaving %s untouched: %s", CATALOG_FILE, exc)
        return 1

    # A partial scrape must never overwrite a good catalog — an empty write would
    # silently blank the add-on until someone noticed.
    empty = sorted(key for key, items in catalogs.items() if not items)
    if empty:
        logger.error(
            "Empty results for %s, leaving %s untouched", ", ".join(empty), CATALOG_FILE
        )
        return 1

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "catalogs": catalogs,
    }

    with open(CATALOG_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    logger.info("Wrote %s", CATALOG_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
