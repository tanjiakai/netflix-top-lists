import json

import build_site


def write_catalog(tmp_path, items):
    payload = {
        "updated_at": "2026-09-13T08:00:00+00:00",
        "week": "2026-09-06",
        "catalogs": {"malaysia_movies": items, "malaysia_tv": []},
    }
    (tmp_path / "catalog.json").write_text(json.dumps(payload), encoding="utf-8")


def sample_item(**overrides):
    item = {
        "id": "tt0120791",
        "title": "Practical Magic",
        "poster": "",
        "rank": 1,
        "type": "movie",
        "region": "malaysia",
        "url": "https://www.netflix.com/tudum/top10/malaysia",
        "description": "#1 on Netflix Malaysia - 2 week(s) in the Top 10",
        "imdb_id": "tt0120791",
        "weeks_in_top10": 2,
    }
    item.update(overrides)
    return item


def read(tmp_path, *parts):
    return json.loads(tmp_path.joinpath("dist", *parts).read_text(encoding="utf-8"))


def test_build_writes_stremio_tree(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item()])

    assert build_site.main() == 0

    manifest = read(tmp_path, "manifest.json")
    assert manifest["id"] == "org.stremio.netflix_top_lists"

    catalog = read(tmp_path, "catalog", "movie", "malaysia_movies.json")
    assert catalog["metas"][0]["id"] == "tt0120791"
    assert catalog["metas"][0]["name"] == "Practical Magic"

    meta = read(tmp_path, "meta", "movie", "tt0120791.json")
    assert "Netflix Malaysia" in meta["meta"]["description"]


def test_manifest_description_names_the_week(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item()])

    assert build_site.main() == 0
    assert "2026-09-06" in read(tmp_path, "manifest.json")["description"]


def test_meta_uses_fallback_id_when_imdb_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item(id="a-film", imdb_id=None)])

    assert build_site.main() == 0
    assert (tmp_path / "dist" / "meta" / "movie" / "a-film.json").exists()


def test_catalog_preview_keeps_poster_when_present(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item(poster="https://img/x.jpg")])

    assert build_site.main() == 0
    catalog = read(tmp_path, "catalog", "movie", "malaysia_movies.json")
    assert catalog["metas"][0]["poster"] == "https://img/x.jpg"


def test_wrap_breaks_long_titles():
    assert build_site.wrap("The Thorn: One Sacred Light") == [
        "The Thorn: One", "Sacred Light"
    ]
    assert build_site.wrap("Mousetrap") == ["Mousetrap"]
    assert build_site.wrap("") == []


def test_placeholder_escapes_xml():
    svg = build_site.placeholder_svg("Upin&Ipin")
    assert "Upin&amp;Ipin" in svg
    assert "Upin&Ipin" not in svg


def test_item_without_poster_gets_a_generated_one(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item(id="a-film", imdb_id=None, poster="")])

    assert build_site.main() == 0

    svg = tmp_path / "dist" / "poster" / "a-film.svg"
    assert svg.exists()
    assert svg.read_text(encoding="utf-8").startswith("<svg")

    catalog = read(tmp_path, "catalog", "movie", "malaysia_movies.json")
    assert catalog["metas"][0]["poster"].endswith("/poster/a-film.svg")


def test_real_poster_is_not_replaced(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item(poster="https://real/poster.jpg")])

    assert build_site.main() == 0
    assert not (tmp_path / "dist" / "poster").exists()


def test_missing_catalog_file_fails(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert build_site.main() == 1


def test_index_page_carries_install_link_and_week(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item()])

    assert build_site.main() == 0
    html = (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")
    assert "stremio://" in html
    assert "2026-09-06" in html
