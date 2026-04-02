from __future__ import annotations

from dataclasses import dataclass

from lumbago_app.services.free_music_portals import FreeMusicPortalSearch


@dataclass
class _FakeResponse:
    status_code: int = 200
    text: str = ""
    json_data: dict | list | None = None
    headers: dict[str, str] | None = None

    def json(self):
        if self.json_data is None:
            raise ValueError("No JSON")
        return self.json_data


class _StubSession:
    def __init__(self, routes: dict[str, _FakeResponse]):
        self.routes = routes

    def get(self, url, **_kwargs):
        for key, response in self.routes.items():
            if key in url:
                return response
        raise AssertionError(f"Unexpected URL: {url}")


def test_youtube_provider_parses_result():
    html = (
        '"videoRenderer":{"videoId":"ABCDEFG1234","title":{"runs":[{"text":"Fade to Black"}]},'
        '"longBylineText":{"runs":[{"text":"Metallica"}]}}'
    )
    search = FreeMusicPortalSearch()
    search.session = _StubSession({"youtube.com/results": _FakeResponse(text=html)})
    probe = search._search_youtube("metallica fade to black")
    assert probe.candidate is not None
    assert probe.candidate.title == "Fade to Black"
    assert probe.candidate.artist == "Metallica"


def test_soundcloud_provider_parses_result():
    home = '<script src="https://a-v2.sndcdn.com/assets/54-test.js"></script>'
    script = 'var cfg = {"client_id":"abcdef1234567890abcdef1234"};'
    payload = {
        "collection": [
            {
                "title": "Fade to Black",
                "genre": "Rock",
                "release_date": "2024-01-10T00:00:00Z",
                "permalink_url": "https://soundcloud.com/test/fade-to-black",
                "user": {"username": "Metallica"},
            }
        ]
    }
    search = FreeMusicPortalSearch()
    search.session = _StubSession(
        {
            "https://soundcloud.com": _FakeResponse(text=home),
            "sndcdn.com/assets/54-test.js": _FakeResponse(text=script),
            "api-v2.soundcloud.com/search/tracks": _FakeResponse(json_data=payload),
        }
    )
    probe = search._search_soundcloud("metallica fade to black")
    assert probe.candidate is not None
    assert probe.candidate.artist == "Metallica"
    assert probe.candidate.year == "2024"


def test_bandcamp_provider_parses_result():
    html = (
        '<li class="searchresult data-search">'
        '<a class="artcont" href="https://example.bandcamp.com/track/fade"></a>'
        '<div class="result-info"><div class="heading"><a href="#">Fade to Black</a></div>'
        '<div class="subhead">by Metallica Tribute</div></div></li>'
    )
    search = FreeMusicPortalSearch()
    search.session = _StubSession({"bandcamp.com/search": _FakeResponse(text=html)})
    probe = search._search_bandcamp("metallica fade to black")
    assert probe.candidate is not None
    assert probe.candidate.title == "Fade to Black"
    assert probe.candidate.artist == "Metallica Tribute"


def test_deezer_provider_parses_result():
    payload = {"data": [{"title_short": "Fade to Black", "artist": {"name": "Metallica"}, "album": {"title": "Ride"}, "link": "https://deezer.com/track/1"}]}
    search = FreeMusicPortalSearch()
    search.session = _StubSession({"api.deezer.com/search": _FakeResponse(json_data=payload)})
    probe = search._search_deezer("metallica fade to black")
    assert probe.candidate is not None
    assert probe.candidate.album == "Ride"


def test_itunes_provider_parses_result():
    payload = {"results": [{"trackName": "Fade to Black", "artistName": "Metallica", "collectionName": "Ride", "primaryGenreName": "Metal", "releaseDate": "1984-07-27T00:00:00Z"}]}
    search = FreeMusicPortalSearch()
    search.session = _StubSession({"itunes.apple.com/search": _FakeResponse(json_data=payload)})
    probe = search._search_itunes("metallica fade to black")
    assert probe.candidate is not None
    assert probe.candidate.year == "1984"


def test_audius_provider_parses_result():
    payload = {"data": [{"title": "Fade to Black", "genre": "Rock", "release_date": "2023-01-01T00:00:00Z", "user": {"name": "Artist"}, "permalink": "https://audius.co/artist/fade"}]}
    search = FreeMusicPortalSearch()
    search.session = _StubSession({"discoveryprovider.audius.co/v1/tracks/search": _FakeResponse(json_data=payload)})
    probe = search._search_audius("metallica fade to black")
    assert probe.candidate is not None
    assert probe.candidate.artist == "Artist"


def test_archiveorg_provider_parses_result():
    payload = {"response": {"docs": [{"title": "Fade to Black", "creator": ["Metallica"], "date": "1984-07-27", "identifier": "fade_to_black"}]}}
    search = FreeMusicPortalSearch()
    search.session = _StubSession({"archive.org/advancedsearch.php": _FakeResponse(json_data=payload)})
    probe = search._search_archiveorg("metallica fade to black")
    assert probe.candidate is not None
    assert probe.candidate.url == "https://archive.org/details/fade_to_black"


def test_jiosaavn_provider_parses_result():
    payload = {"results": [{"id": "57CrrdjC", "song": "Fade to Black", "album": "Ride", "year": "1984", "music": "Metallica", "primary_artists": "Metallica"}]}
    search = FreeMusicPortalSearch()
    search.session = _StubSession({"jiosaavn.com/api.php": _FakeResponse(json_data=payload)})
    probe = search._search_jiosaavn("Metallica - Fade to Black")
    assert probe.candidate is not None
    assert probe.candidate.album == "Ride"


def test_musicbrainz_provider_parses_result():
    payload = {"recordings": [{"id": "mb-1", "title": "Fade to Black", "artist-credit": [{"name": "Metallica"}]}]}
    search = FreeMusicPortalSearch()
    search.session = _StubSession({"musicbrainz.org/ws/2/recording": _FakeResponse(json_data=payload)})
    probe = search._search_musicbrainz("recording:\"fade to black\"")
    assert probe.candidate is not None
    assert probe.candidate.url == "https://musicbrainz.org/recording/mb-1"


def test_discogs_provider_parses_result():
    payload = {"results": [{"title": "Metallica - Fade to Black", "genre": ["Metal"], "year": 1984, "label": ["Elektra"], "uri": "https://discogs.com/release/1"}]}
    search = FreeMusicPortalSearch(discogs_token="token")
    search.session = _StubSession({"api.discogs.com/database/search": _FakeResponse(json_data=payload)})
    probe = search._search_discogs("metallica fade to black")
    assert probe.candidate is not None
    assert probe.candidate.artist == "Metallica"
    assert probe.candidate.title == "Fade to Black"
