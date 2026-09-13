"""Netflix's official Top 10 data, published as a TSV at top10.netflix.com."""

import logging
import requests

logger = logging.getLogger(__name__)

TSV_URL = "https://top10.netflix.com/data/all-weeks-countries.tsv"

# country_name, country_iso2, week, category, weekly_rank, show_title,
# season_title, cumulative_weeks_in_top_10
COL_ISO2 = 1
COL_WEEK = 2
COL_CATEGORY = 3
COL_RANK = 4
COL_TITLE = 5
COL_WEEKS = 7

CATEGORY_TO_TYPE = {"Films": "movie", "TV": "series"}


class TudumError(RuntimeError):
    pass


def parse_rows(lines, country_iso2: str) -> tuple[str, dict[str, list[dict]]]:
    """Pick out the most recent week for one country. Netflix ships every week
    back to 2021 in one file, so this filters while streaming rather than
    holding 30MB+ of unrelated countries in memory."""
    rows = []
    latest_week = None

    for index, line in enumerate(lines):
        if index == 0:
            continue
        fields = line.rstrip("\n").split("\t")
        if len(fields) <= COL_WEEKS or fields[COL_ISO2] != country_iso2:
            continue
        week = fields[COL_WEEK]
        if latest_week is None or week > latest_week:
            latest_week = week
        rows.append(fields)

    if latest_week is None:
        raise TudumError(f"No rows found for country {country_iso2}")

    by_type: dict[str, list[dict]] = {}
    for fields in rows:
        if fields[COL_WEEK] != latest_week:
            continue
        media_type = CATEGORY_TO_TYPE.get(fields[COL_CATEGORY])
        if media_type is None:
            continue
        by_type.setdefault(media_type, []).append(
            {
                "rank": int(fields[COL_RANK]),
                "title": fields[COL_TITLE],
                "weeks_in_top10": int(fields[COL_WEEKS] or 0),
            }
        )

    for items in by_type.values():
        items.sort(key=lambda item: item["rank"])

    return latest_week, by_type


def fetch_top10(country_iso2: str) -> tuple[str, dict[str, list[dict]]]:
    with requests.get(TSV_URL, timeout=180, stream=True) as response:
        response.raise_for_status()
        response.encoding = "utf-8"
        week, by_type = parse_rows(
            response.iter_lines(decode_unicode=True), country_iso2
        )
    logger.info("Netflix week %s: %s", week, {k: len(v) for k, v in by_type.items()})
    return week, by_type
