import json
import logging
import re
import sys
from datetime import datetime, timezone

from .models import ScrapedItem
from .resolver import resolve
from .tudum import fetch_top10

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CATALOG_FILE = "catalog.json"
COUNTRY = "MY"
REGION = "malaysia"
TUDUM_URL = "https://www.netflix.com/tudum/top10/malaysia"

CATALOG_IDS = {"movie": "malaysia_movies", "series": "malaysia_tv"}


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def build_items(media_type: str, rows: list[dict]) -> list[ScrapedItem]:
    items = []
    for row in rows:
        title = row["title"]
        imdb_id, poster = resolve(title, media_type, COUNTRY)
        if imdb_id:
            logger.info("%s -> %s", title, imdb_id)
        else:
            logger.warning("Unresolved: %s", title)

        weeks = row["weeks_in_top10"]
        items.append(
            ScrapedItem(
                id=imdb_id or slug(title),
                title=title,
                poster=poster,
                rank=row["rank"],
                type=media_type,
                region=REGION,
                url=TUDUM_URL if media_type == "movie" else f"{TUDUM_URL}/tv",
                description=f"#{row['rank']} on Netflix Malaysia"
                + (f" - {weeks} week(s) in the Top 10" if weeks else ""),
                imdb_id=imdb_id,
                weeks_in_top10=weeks or None,
            )
        )
    return items


def scrape_all() -> tuple[str, dict[str, list[dict]]]:
    week, by_type = fetch_top10(COUNTRY)

    catalogs = {}
    for media_type, catalog_id in CATALOG_IDS.items():
        rows = by_type.get(media_type) or []
        logger.info("Building %s from %d rows", catalog_id, len(rows))
        catalogs[catalog_id] = [item.model_dump() for item in build_items(media_type, rows)]

    return week, catalogs


def main() -> int:
    try:
        week, catalogs = scrape_all()
    except Exception as exc:
        logger.error("Scrape failed, leaving %s untouched: %s", CATALOG_FILE, exc)
        return 1

    # A partial scrape must never overwrite a good catalog - an empty write would
    # silently blank the add-on until someone noticed.
    empty = sorted(key for key, items in catalogs.items() if not items)
    if empty:
        logger.error(
            "Empty results for %s, leaving %s untouched", ", ".join(empty), CATALOG_FILE
        )
        return 1

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "week": week,
        "catalogs": catalogs,
    }

    with open(CATALOG_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    logger.info("Wrote %s for Netflix week %s", CATALOG_FILE, week)
    return 0


if __name__ == "__main__":
    sys.exit(main())
