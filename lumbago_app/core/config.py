from __future__ import annotations

import os
import json
import sys
from dataclasses import dataclass
from pathlib import Path


def app_data_dir() -> Path:
    base = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    path = Path(base) / "LumbagoMusicAI"
    try:
        path.mkdir(parents=True, exist_ok=True)
        # Validate write access to avoid later DB/cache failures
        test_file = path / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        try:
            test_file.unlink()
        except Exception:
            pass
        return path
    except (PermissionError, OSError):
        fallback = Path.cwd() / ".lumbago_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def cache_dir() -> Path:
    base = app_data_dir()
    path = base / "cache"
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except PermissionError:
        fallback = Path.cwd() / ".lumbago_data" / "cache"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def settings_path() -> Path:
    base = app_data_dir()
    path = base / "settings.json"
    try:
        # Touch to validate write access without overwriting
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
        return path
    except PermissionError:
        fallback = Path.cwd() / ".lumbago_data" / "settings.json"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        if not fallback.exists():
            fallback.touch(exist_ok=True)
        return fallback


@dataclass(frozen=True)
class Settings:
    db_path: Path
    cache_path: Path
    settings_file: Path
    acoustid_api_key: str | None
    musicbrainz_app_name: str | None
    discogs_token: str | None
    cloud_ai_provider: str | None
    cloud_ai_api_key: str | None
    grok_api_key: str | None
    deepseek_api_key: str | None
    openai_api_key: str | None
    openai_base_url: str | None
    openai_model: str | None
    grok_base_url: str | None
    grok_model: str | None
    deepseek_base_url: str | None
    deepseek_model: str | None
    filename_patterns: list[str]
    validation_policy: str | None
    metadata_cache_ttl_days: int
    ui_theme: str


def load_settings() -> Settings:
    data_dir = app_data_dir()
    file_path = settings_path()
    payload: dict[str, str] = {}
    try:
        if file_path.exists():
            payload = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    auto = _discover_windows_keys()
    return Settings(
        db_path=data_dir / "lumbago.db",
        cache_path=cache_dir(),
        settings_file=file_path,
        acoustid_api_key=_first_value(
            payload.get("ACOUSTID_API_KEY"),
            os.getenv("ACOUSTID_API_KEY"),
            auto.get("ACOUSTID_API_KEY"),
        ),
        musicbrainz_app_name=_first_value(
            payload.get("MUSICBRAINZ_APP_NAME"),
            os.getenv("MUSICBRAINZ_APP_NAME"),
            auto.get("MUSICBRAINZ_APP_NAME"),
        ),
        discogs_token=_first_value(
            payload.get("DISCOGS_TOKEN"),
            os.getenv("DISCOGS_TOKEN"),
            auto.get("DISCOGS_TOKEN"),
        ),
        cloud_ai_provider=_first_value(
            payload.get("CLOUD_AI_PROVIDER"),
            os.getenv("CLOUD_AI_PROVIDER"),
            auto.get("CLOUD_AI_PROVIDER"),
        ),
        cloud_ai_api_key=_first_value(
            payload.get("CLOUD_AI_API_KEY"),
            payload.get("GEMINI_API_KEY"),
            os.getenv("CLOUD_AI_API_KEY"),
            os.getenv("GEMINI_API_KEY"),
            auto.get("CLOUD_AI_API_KEY"),
        ),
        grok_api_key=_first_value(
            payload.get("GROK_API_KEY"),
            os.getenv("GROK_API_KEY"),
            auto.get("GROK_API_KEY"),
        ),
        deepseek_api_key=_first_value(
            payload.get("DEEPSEEK_API_KEY"),
            os.getenv("DEEPSEEK_API_KEY"),
            auto.get("DEEPSEEK_API_KEY"),
        ),
        openai_api_key=_first_value(
            payload.get("OPENAI_API_KEY"),
            os.getenv("OPENAI_API_KEY"),
            auto.get("OPENAI_API_KEY"),
        ),
        openai_base_url=_first_value(
            payload.get("OPENAI_BASE_URL"),
            os.getenv("OPENAI_BASE_URL"),
        )
        or "https://api.openai.com/v1",
        openai_model=_first_value(
            payload.get("OPENAI_MODEL"),
            os.getenv("OPENAI_MODEL"),
        )
        or "gpt-4.1-mini",
        grok_base_url=_first_value(
            payload.get("GROK_BASE_URL"),
            os.getenv("GROK_BASE_URL"),
        )
        or "https://api.x.ai/v1",
        grok_model=_first_value(
            payload.get("GROK_MODEL"),
            os.getenv("GROK_MODEL"),
        )
        or "grok-2-latest",
        deepseek_base_url=_first_value(
            payload.get("DEEPSEEK_BASE_URL"),
            os.getenv("DEEPSEEK_BASE_URL"),
        )
        or "https://api.deepseek.com/v1",
        deepseek_model=_first_value(
            payload.get("DEEPSEEK_MODEL"),
            os.getenv("DEEPSEEK_MODEL"),
        )
        or "deepseek-chat",
        filename_patterns=_parse_patterns(payload.get("FILENAME_PATTERNS")),
        validation_policy=_first_value(
            payload.get("VALIDATION_POLICY"),
            os.getenv("VALIDATION_POLICY"),
        )
        or "balanced",
        metadata_cache_ttl_days=_to_int(
            _first_value(
                payload.get("METADATA_CACHE_TTL_DAYS"),
                os.getenv("METADATA_CACHE_TTL_DAYS"),
            ),
            default=30,
        ),
        ui_theme=_first_value(payload.get("UI_THEME"), os.getenv("UI_THEME")) or "cyber",
    )


def save_settings(values: dict[str, str]) -> None:
    file_path = settings_path()
    existing: dict[str, str] = {}
    if file_path.exists():
        try:
            existing = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    merged = {**existing, **values}
    file_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")


def _first_value(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _to_int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _discover_windows_keys() -> dict[str, str]:
    if not sys.platform.startswith("win"):
        return {}
    discovered: dict[str, str] = {}
    discovered.update(_read_registry_keys())
    discovered.update(_read_optional_key_file())
    return discovered


def _read_registry_keys() -> dict[str, str]:
    try:
        import winreg
    except Exception:
        return {}
    keys: dict[str, str] = {}
    paths = [
        r"SOFTWARE\\LumbagoMusicAI",
        r"SOFTWARE\\LumbagoAI",
    ]
    for path in paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
        except Exception:
            continue
        for name in [
            "ACOUSTID_API_KEY",
            "MUSICBRAINZ_APP_NAME",
            "DISCOGS_TOKEN",
            "CLOUD_AI_PROVIDER",
            "CLOUD_AI_API_KEY",
            "GROK_API_KEY",
            "DEEPSEEK_API_KEY",
            "OPENAI_API_KEY",
        ]:
            try:
                value, _ = winreg.QueryValueEx(key, name)
                if value:
                    keys[name] = value
            except Exception:
                continue
        try:
            winreg.CloseKey(key)
        except Exception:
            pass
    return keys


def _read_optional_key_file() -> dict[str, str]:
    # Optional JSON file: %APPDATA%\\LumbagoMusicAI\\api_keys.json
    path = app_data_dir() / "api_keys.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: str(v) for k, v in data.items() if isinstance(k, str)}
    except Exception:
        return {}


def _parse_patterns(value: str | list | None) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return []
