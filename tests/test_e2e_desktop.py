"""E2E smoke tests for desktop app (subprocess, no GUI interaction).

Per NOWA_LISTA 2026-07-14 item 27 + Faza2/Faza4: placeholder dla pełnego E2E (AI→DL→library→DJ).
Aktualnie smoke + SAFE. Rozbudowa: subprocess z prefill, checkpoint check, waveform color sim, smart rules.
Per SZPIEG research 2026-07-14 plan rozbudowy Faza0/Faza1/Faza2/Faza3/Faza4/Faza5 + 'dalej az do ukonczenia wszystkich faz' ... must document identical.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_main(extra_env: dict[str, str] | None = None, seconds: str = "2") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["LUMBAGO_SAFE_MODE"] = "1"
    env["LUMBAGO_SMOKE_SECONDS"] = seconds
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", "import main; raise SystemExit(main.main())"],
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.e2e
def test_e2e_main_smoke_exit_zero():
    result = _run_main()
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.e2e
def test_e2e_autotag_best_candidate_logic():
    code = """
from types import SimpleNamespace
from core.models import Track
from services.autotag_rewrite import UnifiedAutoTagger, Candidate

settings = SimpleNamespace(
    musicbrainz_app_name='LumbagoMusicAI', discogs_token='',
    cloud_ai_api_key=None, gemini_api_key=None, openai_api_key=None,
    grok_api_key=None, deepseek_api_key=None, gemini_base_url=None,
    gemini_model=None, openai_base_url=None, openai_model=None,
    grok_base_url=None, grok_model=None, deepseek_base_url=None,
    deepseek_model=None, cloud_ai_provider=None,
    autotag_sequential=True,
)
service = UnifiedAutoTagger(settings)
track = Track(path='x.mp3', title='Take Me Away', artist='4 Strings')
service._search_musicbrainz = lambda _t: Candidate(source='MusicBrainz', score=74, title='Take Me Away', artist='4 Strings')
service._search_itunes = lambda _t: None
service._search_deezer = lambda _t: None
service._search_discogs = lambda _t: Candidate(source='Discogs', score=81, title='Take Me Away', artist='4 Strings')
service._search_theaudiodb = lambda _t: None
service._search_listenbrainz = lambda _t: None
service._search_lrclib = lambda _t: None
service._search_lyrics_ovh = lambda _t: None
service._search_ai = lambda _t: Candidate(source='AI', score=69, title='Take Me Away', artist='4 Strings')
result = service.enrich_track(track)
assert result.best_match is not None
assert result.best_match.source == 'Discogs'
assert result.best_match.score == 81
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=PROJECT_ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.e2e
def test_e2e_hotcue_manager_crud():
    code = """
from ui.dj.hotcue_manager import HotcueManager
mgr = HotcueManager(max_cues=8)
mgr.set(0, 1000)
mgr.set(3, 5000)
assert mgr.get(0) == 1000
mgr.clear(0)
assert mgr.get(0) is None
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=PROJECT_ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout