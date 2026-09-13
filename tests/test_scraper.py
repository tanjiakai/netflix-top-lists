import json

from scraper import scraper


def fake_rows():
    return "2026-09-06", {
        "movie": [{"rank": 1, "title": "A Film", "weeks_in_top10": 2}],
        "series": [{"rank": 1, "title": "A Show", "weeks_in_top10": 13}],
    }


def test_slug_handles_punctuation():
    assert scraper.slug("Nar'Sata: Sekutu Setan") == "nar-sata-sekutu-setan"


def test_successful_scrape_writes_catalog_with_week(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(scraper, "fetch_top10", lambda country: fake_rows())
    monkeypatch.setattr(scraper, "resolve", lambda *a, **k: ("tt1", ""))

    assert scraper.main() == 0
    written = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))
    assert written["week"] == "2026-09-06"
    assert set(written["catalogs"]) == {"malaysia_movies", "malaysia_tv"}
    assert written["catalogs"]["malaysia_movies"][0]["imdb_id"] == "tt1"


def test_unresolved_title_falls_back_to_slug_id(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(scraper, "fetch_top10", lambda country: fake_rows())
    monkeypatch.setattr(scraper, "resolve", lambda *a, **k: (None, "https://poster"))

    assert scraper.main() == 0
    written = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))
    item = written["catalogs"]["malaysia_movies"][0]
    assert item["imdb_id"] is None
    assert item["id"] == "a-film"
    assert item["poster"] == "https://poster"


def test_description_includes_rank_and_weeks(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(scraper, "fetch_top10", lambda country: fake_rows())
    monkeypatch.setattr(scraper, "resolve", lambda *a, **k: ("tt1", ""))

    scraper.main()
    written = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))
    assert "13 week(s)" in written["catalogs"]["malaysia_tv"][0]["description"]


def test_empty_result_does_not_overwrite_catalog(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    existing = {"week": "old", "catalogs": {"a": [1]}}
    (tmp_path / "catalog.json").write_text(json.dumps(existing), encoding="utf-8")

    monkeypatch.setattr(scraper, "fetch_top10", lambda country: ("2026-09-06", {}))

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
