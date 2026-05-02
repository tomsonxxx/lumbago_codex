from types import SimpleNamespace

from lumbago_app.core.models import Track
from lumbago_app.services.autotag_rewrite import (
    Candidate,
    UnifiedAutoTagger,
    _clean_text,
    _discogs_result_score,
    _musicbrainz_recording_score,
)


def _settings(**kwargs):
    defaults = {
        "musicbrainz_app_name": "LumbagoMusicAI",
        "discogs_token": "",
        "cloud_ai_api_key": None,
        "gemini_api_key": None,
        "openai_api_key": None,
        "grok_api_key": None,
        "deepseek_api_key": None,
        "gemini_base_url": None,
        "gemini_model": None,
        "openai_base_url": None,
        "openai_model": None,
        "grok_base_url": None,
        "grok_model": None,
        "deepseek_base_url": None,
        "deepseek_model": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_clean_text_removes_noise_tokens():
    raw = "Artist - Track Name (Official Video) [HD]"
    assert _clean_text(raw) == "Artist - Track Name"


def test_unified_autotagger_picks_best_candidate(monkeypatch):
    service = UnifiedAutoTagger(_settings())
    track = Track(path="x.mp3", title="Take Me Away", artist="4 Strings")

    monkeypatch.setattr(service, "_search_musicbrainz", lambda _track: Candidate(source="MusicBrainz", score=74, title="Take Me Away", artist="4 Strings"))
    monkeypatch.setattr(service, "_search_discogs", lambda _track: Candidate(source="Discogs", score=81, title="Take Me Away", artist="4 Strings"))
    monkeypatch.setattr(service, "_search_ai", lambda _track: Candidate(source="AI", score=69, title="Take Me Away", artist="4 Strings"))

    result = service.enrich_track(track)

    assert result.best_match is not None
    assert result.best_match.source == "Discogs"
    assert result.best_match.score == 81


def test_apply_best_match_updates_track():
    service = UnifiedAutoTagger(_settings())
    track = Track(path="x.mp3", title="Old", artist="Old Artist", album=None, genre=None, bpm=None, key=None)
    result = type("R", (), {"best_match": Candidate(source="MusicBrainz", score=90, title="New Title", artist="New Artist", album="New Album", genre="Trance", bpm=128.0, key="8A", mood="energetic", energy=0.8)})()

    changed = service.apply_best_match(track, result)

    assert changed is True
    assert track.title == "New Title"
    assert track.artist == "New Artist"
    assert track.album == "New Album"
    assert track.genre == "Trance"
    assert track.bpm == 128.0
    assert track.key == "8A"


def test_apply_best_match_uses_secondary_candidates_for_missing_fields():
    service = UnifiedAutoTagger(_settings())
    track = Track(path="x.mp3", title="Old", artist="Old Artist", album=None, year=None, genre=None)
    primary = Candidate(source="MusicBrainz", score=90, title="New Title", artist="New Artist")
    secondary = Candidate(source="Discogs", score=80, album="New Album", year="1999", genre="Trance")
    result = type("R", (), {"candidates": [primary, secondary], "best_match": primary})()

    changed = service.apply_best_match(track, result)

    assert changed is True
    assert track.title == "New Title"
    assert track.artist == "New Artist"
    assert track.album == "New Album"
    assert track.year == "1999"
    assert track.genre == "Trance"


def test_musicbrainz_ranking_prefers_more_complete_candidate():
    track = Track(path="x.mp3", title="Song", artist="Artist")
    weak = {"title": "Song", "artist-credit": [{"name": "Artist"}]}
    strong = {
        "title": "Song",
        "artist-credit": [{"name": "Artist"}],
        "releases": [{"date": "2001-01-01", "title": "Album"}],
        "isrcs": ["USABC0100001"],
    }

    assert _musicbrainz_recording_score(track, strong) > _musicbrainz_recording_score(track, weak)


def test_discogs_ranking_prefers_candidate_with_year_and_genre():
    track = Track(path="x.mp3", title="Song", artist="Artist")
    weak = {"title": "Artist - Song"}
    strong = {"title": "Artist - Song", "year": 2001, "genre": ["Trance"], "style": ["Uplifting"]}

    assert _discogs_result_score(track, strong) > _discogs_result_score(track, weak)


def test_musicbrainz_search_uses_release_group_genre_fallback(monkeypatch):
    service = UnifiedAutoTagger(_settings())
    track = Track(path="x.mp3", title="Song", artist="Artist")

    monkeypatch.setattr(
        service,
        "_musicbrainz_detail",
        lambda _mbid: {"tags": [], "genres": []},
    )
    monkeypatch.setattr(
        service,
        "_musicbrainz_release_group_detail",
        lambda _rgid: {"tags": ["trance"], "genres": []},
    )
    monkeypatch.setattr(
        "lumbago_app.services.autotag_rewrite.requests.get",
        lambda *args, **kwargs: type(
            "Resp",
            (),
            {
                "raise_for_status": lambda self: None,
                "json": lambda self: {
                    "recordings": [
                        {
                            "id": "rec1",
                            "title": "Song",
                            "artist-credit": [{"name": "Artist"}],
                            "releases": [
                                {
                                    "title": "Album",
                                    "date": "2001-01-01",
                                    "release-group": {"id": "rg1"},
                                }
                            ],
                        }
                    ]
                },
            },
        )(),
    )

    candidate = service._search_musicbrainz(track)

    assert candidate is not None
    assert candidate.genre == "trance"
