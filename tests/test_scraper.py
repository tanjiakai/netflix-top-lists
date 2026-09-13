import json

import pytest

from scraper import justwatch, scraper
from scraper.models import ScrapedItem


def make_edge(title, imdb_id="tt1234567", poster="/poster/1/{profile}/x.{format}"):
    return {
        "node": {
            "id": "tm999",
            "content": {
                "title": title,
                "originalReleaseYear": 2026,
                "shortDescription": "A description.",
                "fullPath": "/my/movie/x",
                "posterUrl": poster,
                "externalIds": {"imdbId": imdb_id},
            },
        }
    }


def test_poster_url_substitutes_placeholders():
    url = justwatch._poster_url("/poster/123/{profile}/some-title.{format}")
    assert url == "https://images.justwatch.com/poster/123/s718/some-title.jpg"


def test_poster_url_handles_missing_poster():
    assert justwatch._poster_url(None) == ""


def test_rank_comes_from_position_not_api_rank(monkeypatch):
    monkeypatch.setattr(
        justwatch, "_query", lambda *a, **k: [make_edge("A"), make_edge("B")]
    )
    items = justwatch.fetch_top10("MY", "MOVIE", "movie", "malaysia")
    assert [item.rank for item in items] == [1, 2]


def test_falls_back_to_justwatch_id_when_imdb_missing(monkeypatch):
    monkeypatch.setattr(
        justwatch, "_query", lambda *a, **k: [make_edge("A", imdb_id=None)]
    )
    item = justwatch.fetch_top10("MY", "MOVIE", "movie", "malaysia")[0]
    assert item.imdb_id is None
    assert item.id == "tm999"


def test_graphql_errors_raise(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"errors": [{"message": "boom"}]}

    monkeypatch.setattr(justwatch.requests, "post", lambda *a, **k: FakeResponse())
    with pytest.raises(justwatch.JustWatchError):
        justwatch._query("MY", "MOVIE", 10)


def test_empty_result_does_not_overwrite_catalog(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    existing = {"updated_at": "2026-01-01T00:00:00+00:00", "catalogs": {"a": [1]}}
    (tmp_path / "catalog.json").write_text(json.dumps(existing), encoding="utf-8")

    monkeypatch.setattr(justwatch, "_query", lambda *a, **k: [])
    monkeypatch.setattr(scraper, "fetch_top10", lambda **k: [])

    assert scraper.main() == 1
    assert json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8")) == existing


def test_fetch_failure_does_not_overwrite_catalog(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "catalog.json").write_text('{"kept": true}', encoding="utf-8")

    def boom(**kwargs):
        raise justwatch.JustWatchError("upstream down")

    monkeypatch.setattr(scraper, "fetch_top10", boom)

    assert scraper.main() == 1
    assert (tmp_path / "catalog.json").read_text(encoding="utf-8") == '{"kept": true}'


def test_successful_scrape_writes_catalog(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    item = ScrapedItem(
        id="tt1",
        title="A",
        poster="",
        rank=1,
        type="movie",
        region="malaysia",
        url="",
    )
    monkeypatch.setattr(scraper, "fetch_top10", lambda **k: [item])

    assert scraper.main() == 0
    written = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))
    assert set(written["catalogs"]) == {"malaysia_movies", "malaysia_tv"}
    assert written["updated_at"]
