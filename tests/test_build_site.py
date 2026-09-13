import json

import build_site


def write_catalog(tmp_path, items):
    payload = {
        "updated_at": "2026-09-13T08:00:00+00:00",
        "catalogs": {"malaysia_movies": items, "malaysia_tv": []},
    }
    (tmp_path / "catalog.json").write_text(json.dumps(payload), encoding="utf-8")


def sample_item(**overrides):
    item = {
        "id": "tt0120791",
        "title": "Practical Magic",
        "poster": "https://images.justwatch.com/poster/1/s718/x.jpg",
        "rank": 1,
        "type": "movie",
        "region": "malaysia",
        "url": "https://www.justwatch.com/my/movie/x",
        "description": "Two sisters.",
        "imdb_id": "tt0120791",
        "year": 1998,
    }
    item.update(overrides)
    return item


def test_build_writes_stremio_tree(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item()])

    assert build_site.main() == 0

    manifest = json.loads((tmp_path / "dist" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["id"] == "org.stremio.netflix_top_lists"

    catalog = json.loads(
        (tmp_path / "dist" / "catalog" / "movie" / "malaysia_movies.json").read_text(
            encoding="utf-8"
        )
    )
    assert catalog["metas"][0]["id"] == "tt0120791"
    assert catalog["metas"][0]["name"] == "Practical Magic"

    meta = json.loads(
        (tmp_path / "dist" / "meta" / "movie" / "tt0120791.json").read_text(encoding="utf-8")
    )
    assert meta["meta"]["releaseInfo"] == "1998"
    assert meta["meta"]["background"]


def test_meta_uses_fallback_id_when_imdb_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item(id="tm999", imdb_id=None)])

    assert build_site.main() == 0
    assert (tmp_path / "dist" / "meta" / "movie" / "tm999.json").exists()


def test_catalog_preview_omits_missing_poster(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item(poster="")])

    assert build_site.main() == 0
    catalog = json.loads(
        (tmp_path / "dist" / "catalog" / "movie" / "malaysia_movies.json").read_text(
            encoding="utf-8"
        )
    )
    assert "poster" not in catalog["metas"][0]


def test_missing_catalog_file_fails(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert build_site.main() == 1


def test_index_page_carries_install_link(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    write_catalog(tmp_path, [sample_item()])

    assert build_site.main() == 0
    html = (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")
    assert "stremio://" in html
    assert "2026-09-13" in html
