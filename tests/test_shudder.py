import pytest

from scraper import shudder


def edge(title="The Terror", imdb_id="tt6109106", poster="/poster/1/{profile}/x.{format}",
         year=2018, description="A ship becomes trapped in ice."):
    return {
        "node": {
            "id": "ts12345",
            "content": {
                "title": title,
                "originalReleaseYear": year,
                "shortDescription": description,
                "fullPath": "/us/tv-show/the-terror",
                "posterUrl": poster,
                "externalIds": {"imdbId": imdb_id},
            },
        }
    }


def test_maps_edges_to_items(monkeypatch):
    monkeypatch.setattr(shudder, "_query", lambda *a: [edge()])
    item = shudder.fetch_horror("popular", "series")[0]
    assert item.title == "The Terror"
    assert item.imdb_id == "tt6109106"
    assert item.type == "series"
    assert item.poster == "https://images.justwatch.com/poster/1/s718/x.jpg"
    assert item.url == "https://www.justwatch.com/us/tv-show/the-terror"


def test_rank_comes_from_position(monkeypatch):
    monkeypatch.setattr(
        shudder, "_query", lambda *a: [edge(title="A"), edge(title="B"), edge(title="C")]
    )
    assert [i.rank for i in shudder.fetch_horror("new", "movie")] == [1, 2, 3]


def test_falls_back_to_justwatch_id_without_imdb(monkeypatch):
    monkeypatch.setattr(shudder, "_query", lambda *a: [edge(imdb_id=None)])
    item = shudder.fetch_horror("popular", "movie")[0]
    assert item.imdb_id is None
    assert item.id == "ts12345"


def test_description_falls_back_to_title_and_year(monkeypatch):
    monkeypatch.setattr(shudder, "_query", lambda *a: [edge(description=None)])
    assert shudder.fetch_horror("popular", "movie")[0].description == "The Terror (2018)"


def test_skips_entries_without_a_title(monkeypatch):
    monkeypatch.setattr(shudder, "_query", lambda *a: [edge(title=None), edge()])
    assert len(shudder.fetch_horror("popular", "series")) == 1


def test_graphql_errors_raise(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"errors": [{"message": "boom"}]}

    monkeypatch.setattr(shudder.requests, "post", lambda *a, **k: FakeResponse())
    with pytest.raises(shudder.ShudderError):
        shudder._query("popular", "movie", 20)


def test_missing_data_raises(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": {"popularTitles": None}}

    monkeypatch.setattr(shudder.requests, "post", lambda *a, **k: FakeResponse())
    with pytest.raises(shudder.ShudderError):
        shudder._query("popular", "movie", 20)


def test_sorts_cover_both_catalogues():
    assert set(shudder.SORTS) == {"popular", "new"}
    assert shudder.SORTS["new"] == "RELEASE_YEAR"
