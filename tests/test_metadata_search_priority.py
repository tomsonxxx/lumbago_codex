from lumbago_app.core.models import Track
from lumbago_app.services.metadata_enricher import (
    LOCAL_SOURCE_LABELS,
    _build_portal_consensus,
    _build_portal_queries,
    _select_recording_id,
)


def test_portal_catalog_contains_added_top_sources():
    expected = {
        "portal_search_apple_music",
        "portal_search_deezer",
        "portal_search_bandcamp",
        "portal_search_beatport",
        "portal_search_tidal",
        "portal_search_amazon_music",
        "portal_search_lastfm",
        "portal_search_traxsource",
        "portal_search_junodownload",
        "portal_search_audiomack",
        "portal_consensus",
    }
    assert expected <= set(LOCAL_SOURCE_LABELS)


def test_portal_queries_are_compact_and_deduplicated():
    track = Track(
        path="Artist__Song_Name_(Official_Video)_Remastered_2024.mp3",
        artist="Artist Name",
        title="Song Name (Official Video) [4K] Remastered 2024",
        albumartist="Artist Name",
        genre="House",
        tracknumber="3",
        discnumber="1",
        composer="Composer X",
        bpm=128.0,
        key="8A",
        rating=5,
        comment="Festival edit",
        lyrics="Some lyrics here",
        isrc="USABC1234567",
        publisher="Label Y",
        grouping="Main Set",
        copyright="Label Y",
        remixer="Remixer Z",
        mood="energetic",
    )

    queries = _build_portal_queries(track)

    assert 1 <= len(queries) <= 3
    assert len(set(queries)) == len(queries)
    assert all(len(query) <= 90 for query in queries)


def test_portal_consensus_prefers_repeated_candidate():
    track = Track(path="demo.mp3", artist="Artist", title="Song")
    hits = [
        ("portal_search_spotify", {"artist": "Artist", "title": "Song"}, "q1", 10),
        ("portal_search_apple_music", {"artist": "Artist", "title": "Song"}, "q1", 7),
        ("portal_search_youtube", {"artist": "Other", "title": "Different"}, "q2", 9),
    ]

    candidate, detail = _build_portal_consensus(track, hits)

    assert candidate is not None
    assert candidate.get("artist") == "Artist"
    assert candidate.get("title") == "Song"
    assert "Glosowanie" in detail


def test_select_recording_id_uses_similarity_not_only_first_hit():
    payload = {
        "results": [
            {
                "score": 0.70,
                "recordings": [
                    {
                        "id": "mismatch",
                        "title": "Completely Different",
                        "artist-credit": [{"name": "Unknown Artist"}],
                    }
                ],
            },
            {
                "score": 0.55,
                "recordings": [
                    {
                        "id": "best-match",
                        "title": "Around The World",
                        "artist-credit": [{"name": "Daft Punk"}],
                    }
                ],
            },
        ]
    }

    recording_id = _select_recording_id(payload, preferred_title="Around The World", preferred_artist="Daft Punk")

    assert recording_id == "best-match"
