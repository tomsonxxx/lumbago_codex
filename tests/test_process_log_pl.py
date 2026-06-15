from __future__ import annotations

from core.process_log_pl import format_queue_status, humanize_process_log


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