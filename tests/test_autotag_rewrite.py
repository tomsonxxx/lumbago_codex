from types import SimpleNamespace

from lumbago_app.core.models import Track
from lumbago_app.services.autotag_rewrite import (
    Candidate,
    UnifiedAutoTagger,
    _clean_text,
    _discogs_result_score,
    _itunes_result_score,
    _musicbrainz_recording_score,
    _track_with_filename_identity,
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
    monkeypatch.setattr(service, "_search_itunes", lambda _track: None)
    monkeypatch.setattr(service, "_search_deezer", lambda _track: None)
    monkeypatch.setattr(service, "_search_discogs", lambda _track: Candidate(source="Discogs", score=81, title="Take Me Away", artist="4 Strings"))
    monkeypatch.setattr(service, "_search_lrclib", lambda _track: None)
    monkeypatch.setattr(service, "_search_lyrics_ovh", lambda _track: None)
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


def test_apply_best_match_applies_full_ai_metadata_fields():
    service = UnifiedAutoTagger(_settings())
    track = Track(path="x.mp3", title="Old", artist="Old Artist")
    ai_candidate = Candidate(
        source="AI",
        score=88,
        albumartist="Album Artist",
        tracknumber="7",
        discnumber="1",
        composer="Composer X",
        rating=4,
        comment="Peak-time festival edit",
        lyrics="Some lyrics",
        isrc="USABC0100001",
        publisher="Label Y",
        grouping="Main Set",
        copyright="Copyright Z",
        remixer="Remixer Q",
    )
    result = type("R", (), {"candidates": [ai_candidate], "best_match": ai_candidate})()

    changed = service.apply_best_match(track, result)

    assert changed is True
    assert track.albumartist == "Album Artist"
    assert track.tracknumber == "7"
    assert track.discnumber == "1"
    assert track.composer == "Composer X"
    assert track.rating == 4
    assert track.comment == "Peak-time festival edit"
    assert track.lyrics == "Some lyrics"
    assert track.isrc == "USABC0100001"
    assert track.publisher == "Label Y"
    assert track.grouping == "Main Set"
    assert track.copyright == "Copyright Z"
    assert track.remixer == "Remixer Q"


def test_lookup_identity_repairs_bitrate_title_from_filename():
    track = Track(
        path=r"E:\music\Poylow, ATHYN - Good In Goodbye - 320.mp3",
        title="320",
        artist="Poylow ATHYN",
    )

    lookup = _track_with_filename_identity(track)

    assert lookup.artist == "Poylow, ATHYN"
    assert lookup.title == "Good In Goodbye"


def test_lookup_identity_uses_single_filename_title_when_bitrate_was_title():
    track = Track(
        path=r"E:\music\Diamond Heart - 320.mp3",
        title="320",
        artist="Diamond Heart",
    )

    lookup = _track_with_filename_identity(track)

    assert lookup.artist is None
    assert lookup.title == "Diamond Heart"


def test_lookup_identity_removes_artist_when_it_is_really_single_title():
    track = Track(
        path=r"E:\music\Diamond Heart - 320.mp3",
        title="Diamond Heart",
        artist="Diamond Heart",
    )

    lookup = _track_with_filename_identity(track)

    assert lookup.artist is None
    assert lookup.title == "Diamond Heart"


def test_lookup_identity_strips_bitrate_suffix_from_existing_title():
    track = Track(
        path=r"E:\music\Poylow, ATHYN - Good In Goodbye - 320.mp3",
        title="Good In Goodbye - 320",
        artist="Poylow, ATHYN",
    )

    lookup = _track_with_filename_identity(track)

    assert lookup.artist == "Poylow, ATHYN"
    assert lookup.title == "Good In Goodbye"


def test_lookup_identity_restores_single_title_from_filename_after_bad_online_match():
    track = Track(
        path=r"E:\music\Frequency - 320.mp3",
        title="Frequency Express",
        artist=None,
    )

    lookup = _track_with_filename_identity(track)

    assert lookup.artist is None
    assert lookup.title == "Frequency"


def test_apply_best_match_does_not_replace_identity_from_online_candidate():
    service = UnifiedAutoTagger(_settings())
    track = Track(path=r"E:\music\Diamond Heart - 320.mp3", title="Diamond Heart", artist=None)
    candidate = Candidate(
        source="Apple Music",
        score=72,
        title="Diamond Heart",
        artist="Alan Walker & Sophia Somajo",
        album="Diamond Heart - Single",
        year="2018",
        genre="Dance",
    )
    result = type("R", (), {"candidates": [candidate], "best_match": candidate})()

    changed = service.apply_best_match(track, result)

    assert changed is True
    assert track.title == "Diamond Heart"
    assert track.artist is None
    assert track.album == "Diamond Heart - Single"
    assert track.year == "2018"
    assert track.genre == "Dance"


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


def test_itunes_ranking_prefers_metadata_complete_candidate():
    track = Track(path="x.mp3", title="Song", artist="Artist")
    weak = {"trackName": "Song", "artistName": "Artist"}
    strong = {
        "trackName": "Song",
        "artistName": "Artist",
        "collectionName": "Album",
        "releaseDate": "2001-01-01T00:00:00Z",
        "primaryGenreName": "Dance",
    }

    assert _itunes_result_score(track, strong) > _itunes_result_score(track, weak)


def test_search_ai_returns_error_candidate_when_providers_fail(monkeypatch):
    service = UnifiedAutoTagger(_settings(cloud_ai_api_key="key"))
    track = Track(path="x.mp3", title="Song", artist="Artist")

    class _FailingTagger:
        def analyze(self, _track):
            from lumbago_app.core.models import AnalysisResult

            return AnalysisResult(description="provider failed", confidence=0.0)

    monkeypatch.setattr(service, "_build_multi_ai_tagger", lambda: _FailingTagger())

    candidate = service._search_ai(track)

    assert candidate is not None
    assert candidate.score == 0
    assert candidate.error == "provider failed"


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
