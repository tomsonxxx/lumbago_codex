from __future__ import annotations

from core.process_log_pl import (
    build_colored_log_html,
    color_for_source_key,
    detect_log_source_key,
    format_queue_status,
    humanize_process_log,
)


def test_humanize_bg_service_queue_message():
    raw = "[bg-service] Zakończono zadanie #23 (kolejka: pending=5, running=1)"
    out = humanize_process_log(raw)
    assert out.startswith("» Uzupełnianie w tle:")
    assert "utwór #23" in out or "zadanie #23" in out
    assert "5 oczekuje" in out
    assert "1 w trakcie" in out


def test_humanize_autotag_provider_hit():
    raw = "[autotag] source=_search_musicbrainz stage=done elapsed_ms=450 status=hit score=85 file=song.mp3"
    out = humanize_process_log(raw)
    assert "MusicBrainz" in out
    assert "dopasowanie 85 pkt" in out
    assert "song.mp3" in out


def test_humanize_autotag_start_summary():
    raw = "[autotag] start | tracks=12 mode=uzupełnianie"
    out = humanize_process_log(raw)
    assert out.startswith("» Autotag:")
    assert "utworów: 12" in out


def test_format_queue_status_polish():
    assert format_queue_status(3, 1) == "3 oczekuje, 1 w trakcie"
    assert format_queue_status(0, 0) == "kolejka pusta"


def test_detect_log_source_key_for_providers():
    assert detect_log_source_key("   · YouTube: wyszukiwanie — song.mp3") == "youtube"
    assert detect_log_source_key("   · SoundCloud: brak wyniku") == "soundcloud"
    assert detect_log_source_key("   · MusicBrainz: dopasowanie 85 pkt") == "musicbrainz"


def test_detect_log_source_key_for_categories():
    assert detect_log_source_key("» Uzupełnianie w tle: Zadanie #3 ukończone") == "bg_enrichment"
    assert detect_log_source_key("» Autotag: Rozpoczęto — utworów: 5") == "autotag"


def test_colored_log_html_uses_source_color():
    line = "2026-06-15 10:00:00    · YouTube: wyszukiwanie"
    html_out = build_colored_log_html(line)
    assert color_for_source_key("youtube") in html_out
    assert "YouTube" in html_out