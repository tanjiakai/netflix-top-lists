from scraper import tmdb


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def stub_results(monkeypatch, results, key="testkey"):
    monkeypatch.setenv("TMDB_API_KEY", key)
    monkeypatch.setattr(
        tmdb.requests, "get", lambda *a, **k: FakeResponse({"results": results})
    )


def test_returns_nothing_without_an_api_key(monkeypatch):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)

    def fail(*a, **k):
        raise AssertionError("must not call TMDB without a key")

    monkeypatch.setattr(tmdb.requests, "get", fail)
    assert tmdb.search_poster("Anything", "movie") == ""


def test_blank_api_key_is_treated_as_absent(monkeypatch):
    monkeypatch.setenv("TMDB_API_KEY", "   ")
    monkeypatch.setattr(
        tmdb.requests, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError())
    )
    assert tmdb.search_poster("Anything", "movie") == ""


def test_exact_title_match_returns_poster(monkeypatch):
    stub_results(monkeypatch, [
        {"name": "Something Else", "poster_path": "/wrong.jpg"},
        {"name": "Bulan Henti Bicara", "poster_path": "/right.jpg"},
    ])
    assert tmdb.search_poster("Bulan Henti Bicara", "series") == (
        "https://image.tmdb.org/t/p/w500/right.jpg"
    )


def test_uses_title_field_for_movies(monkeypatch):
    stub_results(monkeypatch, [{"title": "A Film", "poster_path": "/f.jpg"}])
    assert tmdb.search_poster("A Film", "movie").endswith("/f.jpg")


def test_skips_results_without_a_poster(monkeypatch):
    stub_results(monkeypatch, [
        {"name": "A Show", "poster_path": None},
        {"name": "A Show", "poster_path": "/has.jpg"},
    ])
    assert tmdb.search_poster("A Show", "series").endswith("/has.jpg")


def test_falls_back_to_near_identical_title(monkeypatch):
    stub_results(monkeypatch, [
        {"title": "The Thorn: One Sacred Night", "poster_path": "/close.jpg"},
    ])
    assert tmdb.search_poster("The Thorn: One Sacred Light", "movie").endswith(
        "/close.jpg"
    )


def test_ignores_unrelated_results(monkeypatch):
    stub_results(monkeypatch, [
        {"title": "Something Completely Different", "poster_path": "/no.jpg"},
    ])
    assert tmdb.search_poster("A Film", "movie") == ""


def test_request_failure_returns_empty(monkeypatch):
    monkeypatch.setenv("TMDB_API_KEY", "testkey")

    def boom(*a, **k):
        raise tmdb.requests.RequestException("down")

    monkeypatch.setattr(tmdb.requests, "get", boom)
    assert tmdb.search_poster("A Film", "movie") == ""
