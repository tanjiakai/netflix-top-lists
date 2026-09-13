import json

import pytest

from scraper import scraper
from scraper.models import ScrapedItem

NETFLIX_CATALOGS = {"malaysia_movies", "malaysia_tv"}
SHUDDER_CATALOGS = set(scraper.SHUDDER_CATALOGS)


def fake_rows():
    return "2026-09-06", {
        "movie": [{"rank": 1, "title": "A Film", "weeks_in_top10": 2}],
        "series": [{"rank": 1, "title": "A Show", "weeks_in_top10": 13}],
    }


def horror_item(media_type="movie"):
    return ScrapedItem(
        id="tt9", title="A Horror", poster="https://p.jpg", rank=1,
        type=media_type, region="shudder", url="", imdb_id="tt9",
    )


@pytest.fixture(autouse=True)
def stub_network(monkeypatch):
    """Every scraper.main() test must stay offline."""
    # A developer with a real key exported would otherwise hit TMDB here.
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    monkeypatch.setattr(scraper, "fetch_top10", lambda country: fake_rows())
    monkeypatch.setattr(scraper, "resolve", lambda *a, **k: ("tt1", "https://p.jpg"))
    monkeypatch.setattr(
        scraper, "fetch_horror", lambda sort, media_type: [horror_item(media_type)]
    )


def test_slug_handles_punctuation():
    assert scraper.slug("Nar'Sata: Sekutu Setan") == "nar-sata-sekutu-setan"


def test_writes_every_catalogue_with_the_week(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    assert scraper.main() == 0
    written = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))
    assert written["week"] == "2026-09-06"
    assert set(written["catalogs"]) == NETFLIX_CATALOGS | SHUDDER_CATALOGS
    assert written["catalogs"]["malaysia_movies"][0]["imdb_id"] == "tt1"
    assert written["catalogs"]["shudder_horror_new_series"][0]["type"] == "series"


def test_unresolved_title_falls_back_to_slug_id(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(scraper, "resolve", lambda *a, **k: (None, "https://poster"))

    assert scraper.main() == 0
    written = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))
    item = written["catalogs"]["malaysia_movies"][0]
    assert item["imdb_id"] is None
    assert item["id"] == "a-film"
    assert item["poster"] == "https://poster"


def test_description_includes_rank_and_weeks(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    scraper.main()
    written = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))
    assert "13 week(s)" in written["catalogs"]["malaysia_tv"][0]["description"]


def test_empty_netflix_catalogue_does_not_overwrite(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    existing = {"week": "old", "catalogs": {"a": [1]}}
    (tmp_path / "catalog.json").write_text(json.dumps(existing), encoding="utf-8")
    monkeypatch.setattr(scraper, "fetch_top10", lambda country: ("2026-09-06", {}))

    assert scraper.main() == 1
    assert json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8")) == existing


def test_empty_shudder_catalogue_does_not_overwrite(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    existing = {"week": "old", "catalogs": {"a": [1]}}
    (tmp_path / "catalog.json").write_text(json.dumps(existing), encoding="utf-8")
    monkeypatch.setattr(scraper, "fetch_horror", lambda sort, media_type: [])

    assert scraper.main() == 1
    assert json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8")) == existing


def test_fetch_failure_does_not_overwrite_catalog(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "catalog.json").write_text('{"kept": true}', encoding="utf-8")

    def boom(country):
        raise RuntimeError("upstream down")

    monkeypatch.setattr(scraper, "fetch_top10", boom)

    assert scraper.main() == 1
    assert (tmp_path / "catalog.json").read_text(encoding="utf-8") == '{"kept": true}'
