from scraper import resolver


def stub_lookups(monkeypatch, justwatch=(None, None, None), cinemeta=None):
    monkeypatch.setattr(resolver, "_justwatch", lambda *a, **k: justwatch)
    monkeypatch.setattr(resolver, "_cinemeta_search", lambda *a, **k: cinemeta or [])


def test_normalize_ignores_punctuation_and_case():
    assert resolver.normalize("Nar'Sata: Sekutu Setan") == "nar sata sekutu setan"
    assert resolver.normalize("Upin&Ipin") == "upin ipin"


def test_poster_url_substitutes_placeholders():
    assert resolver.poster_url("/poster/1/{profile}/x.{format}") == (
        "https://images.justwatch.com/poster/1/s718/x.jpg"
    )
    assert resolver.poster_url(None) == ""


def test_prefers_justwatch_imdb_id_and_keeps_its_poster(monkeypatch):
    stub_lookups(monkeypatch, justwatch=("tt123", 2026, "https://jw/poster.jpg"))
    assert resolver.resolve("A Film", "movie") == ("tt123", "https://jw/poster.jpg")


def test_falls_back_to_metahub_when_no_poster_available(monkeypatch):
    stub_lookups(monkeypatch, justwatch=("tt123", 2026, ""))
    imdb_id, poster = resolver.resolve("A Film", "movie")
    assert imdb_id == "tt123"
    assert poster == "https://images.metahub.space/poster/medium/tt123/img"


def test_falls_back_to_cinemeta_matching_year(monkeypatch):
    stub_lookups(
        monkeypatch,
        justwatch=(None, 2016, ""),
        cinemeta=[
            {"name": "The Magnificent Seven", "releaseInfo": "1960",
             "id": "tt0054047", "poster": "https://old.jpg"},
            {"name": "The Magnificent Seven", "releaseInfo": "2016",
             "id": "tt2404435", "poster": "https://new.jpg"},
        ],
    )
    assert resolver.resolve("The Magnificent Seven", "movie") == (
        "tt2404435", "https://new.jpg"
    )


def test_accepts_unique_cinemeta_match_with_its_poster(monkeypatch):
    stub_lookups(
        monkeypatch,
        cinemeta=[{"name": "Mousetrap", "releaseInfo": "2026",
                   "id": "tt36996011", "poster": "https://cm/poster.jpg"}],
    )
    assert resolver.resolve("Mousetrap", "series") == (
        "tt36996011", "https://cm/poster.jpg"
    )


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


def test_every_resolved_item_gets_a_poster(monkeypatch):
    """Stremio shows a blank placeholder for any catalog item without a poster."""
    cases = [
        (("tt1", 2026, ""), []),
        (("tt2", 2026, "https://jw.jpg"), []),
        ((None, 2026, ""), [{"name": "X", "releaseInfo": "2026", "id": "tt3"}]),
        ((None, None, ""), [{"name": "X", "releaseInfo": "2026", "id": "tt4",
                             "poster": "https://cm.jpg"}]),
    ]
    for justwatch, cinemeta in cases:
        stub_lookups(monkeypatch, justwatch=justwatch, cinemeta=cinemeta)
        imdb_id, poster = resolver.resolve("X", "movie")
        assert imdb_id and poster, f"{justwatch} / {cinemeta} produced {imdb_id!r}, {poster!r}"


def test_unrelated_results_are_ignored(monkeypatch):
    stub_lookups(
        monkeypatch,
        cinemeta=[{"name": "Something Else Entirely", "releaseInfo": "2020",
                   "id": "tt999", "poster": "https://x.jpg"}],
    )
    assert resolver.resolve("Something", "movie") == (None, "")


def test_accepts_near_identical_title(monkeypatch):
    """Netflix lists this film with 'Light' where the real title says 'Night'."""
    stub_lookups(
        monkeypatch,
        cinemeta=[
            {"name": "The Thorn: One Sacred Night", "releaseInfo": "2024",
             "id": "tt29795485", "poster": "https://real.jpg"},
            {"name": "One Night with the King", "releaseInfo": "2006", "id": "tt0430431"},
        ],
    )
    assert resolver.resolve("The Thorn: One Sacred Light", "movie") == (
        "tt29795485", "https://real.jpg"
    )


def test_rejects_fuzzy_match_when_several_are_close(monkeypatch):
    stub_lookups(
        monkeypatch,
        cinemeta=[
            {"name": "The Thorn: One Sacred Night", "id": "tt1"},
            {"name": "The Thorn: One Sacred Fight", "id": "tt2"},
        ],
    )
    assert resolver.resolve("The Thorn: One Sacred Light", "movie") == (None, "")


def test_rejects_fuzzy_match_below_threshold(monkeypatch):
    stub_lookups(
        monkeypatch,
        cinemeta=[{"name": "Safe House", "releaseInfo": "2012", "id": "tt1599348"}],
    )
    assert resolver.resolve("Safe", "movie") == (None, "")


def test_similarity_scores_one_word_difference_highly():
    a = resolver.normalize("The Thorn: One Sacred Light")
    b = resolver.normalize("The Thorn: One Sacred Night")
    assert resolver.similarity(a, b) >= resolver.FUZZY_THRESHOLD
    assert resolver.similarity(
        resolver.normalize("Safe"), resolver.normalize("Safe House")
    ) < resolver.FUZZY_THRESHOLD
