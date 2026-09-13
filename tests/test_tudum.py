import pytest

from scraper import tudum

HEADER = "country_name\tcountry_iso2\tweek\tcategory\tweekly_rank\tshow_title\tseason_title\tcumulative_weeks_in_top_10"


def row(iso2, week, category, rank, title, weeks="1"):
    return f"Name\t{iso2}\t{week}\t{category}\t{rank}\t{title}\tN/A\t{weeks}"


def test_picks_latest_week_only():
    lines = [
        HEADER,
        row("MY", "2026-08-30", "Films", 1, "Old Film"),
        row("MY", "2026-09-06", "Films", 1, "New Film"),
    ]
    week, by_type = tudum.parse_rows(lines, "MY")
    assert week == "2026-09-06"
    assert [i["title"] for i in by_type["movie"]] == ["New Film"]


def test_filters_by_country():
    lines = [
        HEADER,
        row("SG", "2026-09-06", "Films", 1, "Singapore Film"),
        row("MY", "2026-09-06", "Films", 1, "Malaysia Film"),
    ]
    _, by_type = tudum.parse_rows(lines, "MY")
    assert [i["title"] for i in by_type["movie"]] == ["Malaysia Film"]


def test_maps_categories_to_stremio_types():
    lines = [
        HEADER,
        row("MY", "2026-09-06", "Films", 1, "A Film"),
        row("MY", "2026-09-06", "TV", 1, "A Show"),
    ]
    _, by_type = tudum.parse_rows(lines, "MY")
    assert by_type["movie"][0]["title"] == "A Film"
    assert by_type["series"][0]["title"] == "A Show"


def test_sorts_by_rank():
    lines = [
        HEADER,
        row("MY", "2026-09-06", "Films", 3, "Third"),
        row("MY", "2026-09-06", "Films", 1, "First"),
        row("MY", "2026-09-06", "Films", 2, "Second"),
    ]
    _, by_type = tudum.parse_rows(lines, "MY")
    assert [i["title"] for i in by_type["movie"]] == ["First", "Second", "Third"]


def test_carries_weeks_in_top10():
    lines = [HEADER, row("MY", "2026-09-06", "TV", 1, "Long Runner", weeks="13")]
    _, by_type = tudum.parse_rows(lines, "MY")
    assert by_type["series"][0]["weeks_in_top10"] == 13


def test_unknown_country_raises():
    lines = [HEADER, row("SG", "2026-09-06", "Films", 1, "Nope")]
    with pytest.raises(tudum.TudumError):
        tudum.parse_rows(lines, "MY")


def test_ignores_short_and_unknown_category_rows():
    lines = [
        HEADER,
        "truncated\trow",
        row("MY", "2026-09-06", "Games", 1, "A Game"),
        row("MY", "2026-09-06", "Films", 1, "A Film"),
    ]
    _, by_type = tudum.parse_rows(lines, "MY")
    assert set(by_type) == {"movie"}
