from scraper import resolver


def stub_lookups(monkeypatch, justwatch=(None, None, None), cinemeta=None):
    monkeypatch.setattr(resolver, "_justwatch", lambda *a, **k: justwatch)
    monkeypatch.setattr(resolver, "_cinemeta_exact", lambda *a, **k: cinemeta or [])


def test_normalize_ignores_punctuation_and_case():
    assert resolver.normalize("Nar'Sata: Sekutu Setan") == "nar sata sekutu setan"
    assert resolver.normalize("Upin&Ipin") == "upin ipin"


def test_poster_url_substitutes_placeholders():
    assert resolver.poster_url("/poster/1/{profile}/x.{format}") == (
        "https://images.justwatch.com/poster/1/s718/x.jpg"
    )
    assert resolver.poster_url(None) == ""


def test_prefers_justwatch_imdb_id(monkeypatch):
    stub_lookups(monkeypatch, justwatch=("tt123", 2026, "poster"))
    assert resolver.resolve("A Film", "movie") == ("tt123", "")


def test_falls_back_to_cinemeta_matching_year(monkeypatch):
    stub_lookups(
        monkeypatch,
        justwatch=(None, 2016, ""),
        cinemeta=[
            {"name": "The Magnificent Seven", "releaseInfo": "1960", "id": "tt0054047"},
            {"name": "The Magnificent Seven", "releaseInfo": "2016", "id": "tt2404435"},
        ],
    )
    assert resolver.resolve("The Magnificent Seven", "movie") == ("tt2404435", "")


def test_accepts_unique_cinemeta_match(monkeypatch):
    stub_lookups(
        monkeypatch,
        cinemeta=[{"name": "Mousetrap", "releaseInfo": "2026", "id": "tt36996011"}],
    )
    assert resolver.resolve("Mousetrap", "series") == ("tt36996011", "")


def test_ambiguous_match_is_left_unresolved(monkeypatch):
    """A wrong ID shows the wrong title and pulls the wrong streams."""
    stub_lookups(
        monkeypatch,
        justwatch=(None, None, "https://poster"),
        cinemeta=[
            {"name": "Gandhari", "releaseInfo": "2025", "id": "tt33354945"},
            {"name": "Gandhari", "releaseInfo": "1993", "id": "tt0353478"},
        ],
    )
    assert resolver.resolve("Gandhari", "movie") == (None, "https://poster")


def test_unmatched_title_keeps_justwatch_poster(monkeypatch):
    stub_lookups(monkeypatch, justwatch=(None, None, "https://poster"), cinemeta=[])
    assert resolver.resolve("Unknown Title", "movie") == (None, "https://poster")


def test_cinemeta_only_matches_exact_names(monkeypatch):
    stub_lookups(
        monkeypatch,
        cinemeta=[],  # _cinemeta_exact already filters; nothing exact means nothing
    )
    assert resolver.resolve("Something", "movie") == (None, "")
