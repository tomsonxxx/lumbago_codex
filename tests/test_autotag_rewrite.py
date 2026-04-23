from types import SimpleNamespace

from lumbago_app.core.models import Track
from lumbago_app.services.autotag_rewrite import Candidate, UnifiedAutoTagger, _clean_text


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
